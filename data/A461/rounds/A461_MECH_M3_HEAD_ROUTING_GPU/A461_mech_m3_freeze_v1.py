#!/usr/bin/env python3
"""A461-MECH-M3 R1: CPU freeze of the head-level routing test at the L11 full-attention layer of kev-4B
(zero model forwards; tokenizer only, for the attention-readout token classes).

M2 (ca949e7) found MIXER_WRITER at L11: replacing only the L11 self_attn output at the host's append span
with the donor's repairs 51/104 cells round-specifically, and the MLP is never a sufficient writer. M3 asks
WHICH heads write it and WHERE they read from:
  P  head patches: the input of L11 self_attn.o_proj (gated per-head attention output, 16 heads x 256) at
     the span positions, replaced for a head subset with the donor's own: all 16 heads, each single head,
     all-but-one head, each KV group (4 query heads sharing one key/value head); source donor new (main)
     and donor ROUND (round), the rest of the forward recomputed in host context
  R  attention readout: in every capture forward, the L11 attention probabilities from each span query
     to every earlier key (recomputed from the module's own q/k at the hook, checked against the forward's
     own o_proj input), summarised by token class: PARTNER (the vote by the same author in the candidate
     round that makes the appended vote a conflict), ROUND_PEERS (other authors' candidate-round votes),
     SELF (the span itself), REST
Captures: donor new / ROUND (14 + 14), host new / ROUND (8 + 8). 44 captures + 104 x 37 x 2 patches = 7740
calls in 60 x 128 + 60.
"""
import argparse, collections, gzip, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
WORK = ROOT / "a461-g5-minimal-patch-pilot-20261025-v1"
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_M1_DESIGN = "f3852efc21e7b55fdc1b7370a867454730422913"
BLOB_M1_RAW = "298c7cdfab634cd6a6a9122fac90d41c87219c21"
BLOB_G10_CF = "06ee06d7942b9f1a5f09c35777d5da1149655e4d"
BLOB_M2_RAW = "e1c4b34fcef9221a98e8209f6bbff3f6536b15d4"
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
N_HEADS, N_KV = 16, 4
SOURCES = ("new", "ROUND")
ARMS = ([("all", list(range(N_HEADS)))] + [(f"head{h}", [h]) for h in range(N_HEADS)]
        + [(f"drop{h}", [k for k in range(N_HEADS) if k != h]) for h in range(N_HEADS)]
        + [(f"group{g}", list(range(g * N_HEADS // N_KV, (g + 1) * N_HEADS // N_KV))) for g in range(N_KV)])
PLAN = [128] * 60 + [60]

PREREG = {
    "readouts": "M = conflict margin; A = logit(reject_conflict) - max(accept, wait); JOINT = M > 0 and A > 0; "
                "dM = M(patch) - M(in-run host new capture)",
    "units": "the 104 cross-group cells of M1/M2; cells share donors and hosts, counts are descriptive decision "
             "rules, not independent tests",
    "S": "S(arm) = #cells where the main-source patch is JOINT and the ROUND-source patch of the same arm is not",
    "SPEC": "SPEC(arm) iff dM_main > dM_round in >= 75% of cells AND in a majority of cells for >= 10 of 14 donor groups",
    "consistency_gate": "the all-heads arm reproduces M2 mixer_L11 (o_proj is linear without bias, so the all-heads "
                        "o_proj-input patch equals the mixer-output patch up to GEMM rounding): |S(all) - "
                        "S_M2(mixer, 11)| <= 5 AND main-source JOINT agrees with M2 mixer_L11 main in >= 98/104 "
                        "cells; otherwise verdict INCONSISTENT_WITH_M2 and no head claim is made",
    "head_rules": "SUF(h): S(head h) >= 1/2 S(all) and SPEC(head h). NEC(h): S(drop h) <= 1/2 S(all) "
                  "(within-patch necessity: removing head h from the donor patch loses at least half the repairs). "
                  "GSUF(g): S(group g) >= 1/2 S(all) and SPEC(group g)",
    "verdict": "SPARSE_HEADS if 1 <= |SUF u NEC| <= 3; BROAD_HEADS if |SUF u NEC| > 3; else KV_GROUP_LOCAL if some "
               "GSUF(g); else DISTRIBUTED",
    "implicated_heads": "H* = SUF u NEC; if empty, the heads of the GSUF groups; if still empty, the 3 heads with the "
                        "largest S(head h) (ties: larger median dM_main - dM_round), labelled exploratory",
    "attention_readout": "per capture, head and span query: probability mass on PARTNER / ROUND_PEERS / SELF / REST "
                         "keys (question row 0; the span is in the shared state prefix, cross-row equality is "
                         "recorded); mP(scene, arm) = mean over span queries and over h in H* of the PARTNER mass",
    "A1_round_gated_partner_attention": "within scene, D(s) = mP(s, new) - mP(s, ROUND). DONOR_GATED iff D > 0 for "
                                        ">= 11/14 donors; HOST_GATED iff D > 0 for >= 6/8 hosts",
    "A2_donor_vs_host": "mP(new) of donors vs hosts: medians, and #hosts below the donor minimum; descriptive only",
    "interpretation_fixed_in_advance": "DONOR_GATED and HOST_GATED: the host's L11 heads find the partner vote in a "
        "round-dependent way just as donors do, so the failing host's deficit is in what those heads carry (the "
        "partner's value representation built upstream), not where they look. DONOR_GATED and not HOST_GATED: the "
        "host's heads do not route attention to the partner by round, an attention-pattern (routing) failure. Not "
        "DONOR_GATED: the round-specific evaluation is not explained by span-to-partner attention at L11. Head "
        "patches show sufficiency (SUF) and within-patch necessity (NEC), not necessity in the unpatched host",
    "always_reported": "S, SPEC, J_main, J_round and median dM per arm; per-head class masses for every capture; "
                       "leave-one-donor-group-out of the verdict and of H*; per host; all nulls",
}


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--roster", required=True, type=Path)
    ap.add_argument("--m1-design", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--m2-raw", required=True, type=Path)
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.m1_design) == BLOB_M1_DESIGN
       and file_blob(a.m1_raw) == BLOB_M1_RAW and file_blob(a.m2_raw) == BLOB_M2_RAW
       and file_blob(a.g10_counterfactuals) == BLOB_G10_CF, "pins")
    spec = importlib.util.spec_from_file_location("sa", WORK / "A461_g5_g2_stage_a_cpu_freeze_v1.py")
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    ck(sha_file(sa.CORPUS) == sa.CORPUS_SHA, "corpus pin")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    m1 = json.loads(a.m1_design.read_text("utf8"))
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    donors, hosts = m1["selection"]["donors"], m1["selection"]["hosts"]
    ck(len(donors) == 14 and len(hosts) == 8, "selection")
    gd, gh = dict(donors), dict(hosts)
    m1_cap = {(x["target_scene"], x["target_arm"]): x["forward_index"] for x in m1raw if x["capture"]}
    ck(all(cf[s]["ROUND"]["ok"] for s in list(gd) + list(gh)), "ROUND variant for every donor and host")

    # ---------- token classes for the attention readout (tokenizer only) ----------
    repo = a.repo_root.expanduser().resolve(strict=True)
    g5_full = subprocess.run(["git", "-C", str(repo), "rev-parse", BLOB_G5V2], capture_output=True, text=True,
                             check=True).stdout.strip()
    q_tw = json.loads(subprocess.run(["git", "-C", str(repo), "cat-file", "blob", g5_full], capture_output=True,
                                     text=True, check=True).stdout.splitlines()[0])["native_request"]["questions"]
    sys.path.insert(0, str(ROOT / "kev08b-smoke-20261001-153041/code"))
    from transformers import AutoTokenizer
    from kev.api import SystemOneRequest, to_record
    from kev.model import encode
    tok = AutoTokenizer.from_pretrained(str(ROOT / "kev4b-assets-20261002/base"))
    need = set(gd) | set(gh)
    scenes = {}
    for line in gzip.open(sa.CORPUS, "rt", encoding="utf8"):
        if line.strip():
            rec = json.loads(line)
            if rec["_meta"].get("source") == "twins_streamlet":
                sh = hashlib.sha256(sa.canon(rec["state"]).encode("utf8")).hexdigest()
                if sh in need:
                    scenes[sh] = rec["state"]
    ck(set(scenes) == need, "scene recovery")

    def span(s, arm):
        return roster[s]["appended_span_in_state"]["new"] if arm == "new" else cf[s]["ROUND"]["span"]

    def classes(s, arm):
        msg = roster[s]["declared_edit_new"]["message"] if arm == "new" else cf[s]["ROUND"]["message"]
        st = json.loads(sa.canon(scenes[s]))
        st["received_messages"].append(dict(msg))
        rendered, _ = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(sa.canon(st))}))
        e = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
        ck(not e["state_truncated"], "truncated")
        tid = sa.hids(e["ids"])
        want = roster[s]["token_ids_sha256"]["new"] if arm == "new" else cf[s]["ROUND"]["token_ids_sha256"]
        ck(tid == want, f"token gate {s[:8]}:{arm}")
        ids = e["ids"][:e["seg"].count(0)]
        dec = [tok.decode([t]) for t in ids]
        starts = [p for p in range(len(ids) - 2) if dec[p] == " " and dec[p + 1] == " -" and dec[p + 2] == " author"]
        msgs = st["received_messages"]
        ck(len(starts) == len(msgs), f"item starts {len(starts)} != messages {len(msgs)} at {s[:8]}:{arm}")
        s0, s1 = span(s, arm)
        ck(starts[-1] == s0, f"last item != span at {s[:8]}:{arm}")
        ends = starts[1:] + [s1]
        items = list(zip(starts, ends))
        for (p, q), m in zip(items, msgs):
            txt = "".join(dec[p:q])
            ck(all(f"{k}: {m[k]}" in txt for k in ("author", "block", "kind")), f"item text at {s[:8]}:{arm}:{p}")
        rnd, A = st["candidate_round"], msg["author"]
        allowed = set(st["validator_set"])
        base = roster[s]["declared_edit_new"]["message"]
        partner, peers = [], []
        for (p, q), m in zip(items[:-1], msgs[:-1]):
            if m.get("kind") != "vote" or m.get("round") != rnd:
                continue
            if (m.get("author") == A and m.get("block") != base["block"] and m.get("author") in allowed
                    and isinstance(m.get("received"), (int, float)) and m["received"] <= st["decision_time"]):
                partner.append([p, q])
            elif m.get("author") != A:
                peers.append([p, q])
        ck(len(partner) == 1, f"partner count {len(partner)} at {s[:8]}:{arm}")
        return {"span": [s0, s1], "partner": partner, "round_peers": peers, "state_len": len(ids),
                "token_ids_sha256": tid}

    token_classes = {}
    rows = []

    def add(**kw):
        n = len(rows)
        rows.append(dict(forward_index=n + 1, run=n // 128 + 1, **kw))

    for kind, sel in (("donor", donors), ("host", hosts)):
        for s, _g in sel:
            for arm in SOURCES:
                tag = f"{arm}:{s[:12]}"
                token_classes[tag] = classes(s, arm)
                add(phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm,
                    source_kind=kind,
                    capture={"tag": tag, "span": span(s, arm), "rows": "all", "save": True, "layer": HEAD_LAYER,
                             "oproj_input": True, "attention": True},
                    bitwise_vs_m1=m1_cap.get((s, arm)))
    ck(sum(1 for r in rows if r["bitwise_vs_m1"]) == 36, "36 M1 bitwise anchors (hosts' ROUND is new in M3)")
    for d, _ in donors:
        for h, _ in hosts:
            if gd[d] == gh[h]:
                continue
            for arm, heads in ARMS:
                for src in SOURCES:
                    add(phase="patch", condition=f"patch_m3_{arm}_{'main' if src == 'new' else 'round'}",
                        direction="repair", scope="all", source_kind="main" if src == "new" else "round",
                        donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h, target_arm="new",
                        patch={"layer": HEAD_LAYER, "arm": arm, "heads": heads, "span": span(h, "new"),
                               "source": f"{src}:{d[:12]}", "rows": "all"})
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * len(ARMS) * 2 == 7696, "104 x 37 x 2 patches")
    design = {"schema": "JEV_A461_MECH_M3_HEAD_ROUTING_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M3_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader); L11 = Qwen3.5 full attention, "
                       "16 query heads x 256 in 4 KV groups, output gate, o_proj without bias",
              "inputs": {"roster_blob": BLOB_ROSTER, "m1_design_blob": BLOB_M1_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                         "m2_raw_blob": BLOB_M2_RAW, "g10_counterfactuals_blob": BLOB_G10_CF,
                         "g5v2_questions_blob": g5_full, "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV,
              "arms": [[n, hs] for n, hs in ARMS], "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "token_classes": token_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M3 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m3_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m3_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m3_design.json", "m3_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 7696,
                      "partner_spans": {t: c["partner"][0] for t, c in token_classes.items()},
                      "manifest_blob": file_blob(out / "m3_manifest.jsonl"),
                      "design_blob": file_blob(out / "m3_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
