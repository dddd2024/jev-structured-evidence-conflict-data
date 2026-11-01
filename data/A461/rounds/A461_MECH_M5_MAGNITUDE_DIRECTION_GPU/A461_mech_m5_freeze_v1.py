#!/usr/bin/env python3
"""A461-MECH-M5 R1: CPU freeze of the magnitude / direction / content controls of the L11 span write of kev-4B
(zero model forwards; tokenizer only, for the key classes).

M4 (f5bbf87): the donor's L11 span write (the M3 all-heads patch, 51/104 repairs) splits exactly into key-class
contributions; dropping the partner's part keeps 41/51, the partner part alone repairs 1, and the host's own
attention reading the donor's partner values repairs 0 (V_NONE); dropping OTHER_ITEMS (-> 8) or CONTEXT (-> 23)
loses the repair, but these are also the largest contributions. A class contribution is a vector at the span
positions [W, 4096], so it can be rescaled and moved across scenes. M5 asks
  B  BULK = OTHER_ITEMS + CONTEXT together: only_BULK (host - host_B + donor_B), drop_BULK (donor - donor_B + host_B)
  D  direction at matched size: dir_C = host + alpha_C * (donor_C - host_C), alpha_C chosen per row and span
     position so that ||alpha_C * delta_C|| = ||donor - host|| (the full patch's change); C in PARTNER,
     ROUND_PEERS, OTHER_ITEMS, CONTEXT, SELF, ROUNDVOTES, BULK
  R  null: dir_RAND = host + ||donor - host|| * u (u a seeded unit-Gaussian direction per span position, fixed
     per cell and shared by the main and round sources)
  X  content: xdonor_BULK = donor - donor_B + third_B, third = a third donor from neither the donor's nor the
     host's group, taken from the same arm (new / ROUND) as the source
`full` = the M3 all-heads patch (bitwise anchor). Captures as M4: donor new / ROUND (14 + 14), host new / ROUND
(8 + 8). 44 captures + 104 x 12 x 2 = 2540 calls in 19 x 128 + 108.
"""
import argparse, collections, gzip, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
WORK = ROOT / "a461-g5-minimal-patch-pilot-20261025-v1"
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_M1_DESIGN = "f3852efc21e7b55fdc1b7370a867454730422913"
BLOB_M1_RAW = "298c7cdfab634cd6a6a9122fac90d41c87219c21"
BLOB_G10_CF = "06ee06d7942b9f1a5f09c35777d5da1149655e4d"
BLOB_M3_DESIGN = "7445c13bc36c45324b54c3b4ea2fcbee0c37fe77"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M4_DESIGN = "7ec989c0f70d3fcead4b64b035a32b6655110575"
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
N_HEADS, N_KV = 16, 4
SOURCES = ("new", "ROUND")
BASE = ("PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT")
BULK = ["OTHER_ITEMS", "CONTEXT"]
ARMS = ([("full", "full", []), ("only_BULK", "only", BULK), ("drop_BULK", "drop", BULK)]
        + [(f"dir_{c}", "dir", cl) for c, cl in (("PARTNER", ["PARTNER"]), ("ROUND_PEERS", ["ROUND_PEERS"]),
                                                   ("OTHER_ITEMS", ["OTHER_ITEMS"]), ("CONTEXT", ["CONTEXT"]),
                                                   ("SELF", ["SELF"]), ("ROUNDVOTES", ["PARTNER", "ROUND_PEERS"]),
                                                   ("BULK", BULK))]
        + [("dir_RAND", "rand", []), ("xdonor_BULK", "xdonor", BULK)])
DIR_CLASSES = ["PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "CONTEXT", "SELF", "ROUNDVOTES", "BULK"]
PLAN = [128] * 19 + [108]

PREREG = {
    "readouts": "M = conflict margin; A = logit(reject_conflict) - max(accept, wait); JOINT = M > 0 and A > 0; "
                "dM = M(patch) - M(in-run capture of host new)",
    "units": "the 104 cross-group cells of M1-M4; cells share donors and hosts, counts are descriptive decision "
             "rules, not independent tests",
    "S": "S(arm) = #cells where the donor-new-source patch is JOINT and the donor-ROUND-source patch of the same arm "
         "is not (target host new)",
    "SPEC": "SPEC iff dM_main > dM_round in >= 75% of cells AND in a majority of cells for >= 10 of 14 donor groups",
    "consistency_gate": "the full arm is the M3 all-heads patch: its 208 rows must equal M3's bitwise (GPU, checked in "
                        "the run) and S(full) = 51; otherwise verdict INCONSISTENT_WITH_M3 and no claim",
    "matched_size_gate": "for every dir_* and dir_RAND row, the patch's change ||patch - host|| per row and span "
                         "position equals ||donor - host|| within 1e-3 relative (fail-closed in the runner)",
    "bulk_rules": "BULK_SUF iff S(only_BULK) >= 1/2 S(full) and SPEC(only_BULK); BULK_NEC iff S(drop_BULK) <= "
                  "1/2 S(full)",
    "direction_rules": "DIR_SUF(C) iff S(dir_C) >= 1/2 S(full) and SPEC(dir_C), for C in PARTNER, ROUND_PEERS, "
                       "OTHER_ITEMS, CONTEXT, SELF, ROUNDVOTES, BULK. RAND_NULL iff S(dir_RAND) <= 5 and not "
                       "SPEC(dir_RAND)",
    "verdict": "if not RAND_NULL: MAGNITUDE_SUFFICES (a random direction at the full patch's size repairs; no "
               "direction claim). Else D = {C : DIR_SUF(C)}: PARTNER_DIRECTION if PARTNER or ROUNDVOTES in D and no "
               "BULK-side class (OTHER_ITEMS, CONTEXT, BULK) in D; BULK_DIRECTION if a BULK-side class in D and "
               "neither PARTNER nor ROUNDVOTES in D; BOTH_DIRECTIONS if both kinds in D; SELF_DIRECTION if D = "
               "{SELF}; NO_SINGLE_DIRECTION if D is empty (the repair needs the donor's write as a whole)",
    "content_rule": "XD_HOLDS iff S(xdonor_BULK) >= 1/2 S(full) and SPEC(xdonor_BULK): the BULK part need not come "
                    "from the same scene as the rest of the donor's write; else XD_FAILS",
    "interpretation_fixed_in_advance": "M4's necessity of OTHER_ITEMS / CONTEXT is a size effect if RAND_NULL holds "
        "and BULK_DIRECTION does not, or if a non-BULK class repairs at matched size (PARTNER_DIRECTION: the partner "
        "direction carries the evaluation and was only too small in M4). BULK_DIRECTION with RAND_NULL: the "
        "context-wide read carries the round-specific evaluation in its direction, not only its size. "
        "NO_SINGLE_DIRECTION: the evaluation is a combination across classes. dir_C rescales a direction by a "
        "position-wise factor alpha_C that can be large; alpha statistics are always reported. All keys before the "
        "span are identical in a scene's new and ROUND arms, so round-specificity of pre-span classes comes from "
        "the donor's span-side queries and gates (the round token is at the span end)",
    "always_reported": "S, SPEC, J_main, J_round and median dM per arm; alpha statistics per dir arm; per-cell "
                       "||delta_C|| and cos(delta_C, delta_full) from the capture files; leave-one-donor-group-out "
                       "of every verdict; per host; all nulls",
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


def ranges(idx):
    """sorted index list -> [[lo, hi), ...]"""
    out = []
    for i in idx:
        if out and out[-1][1] == i:
            out[-1][1] = i + 1
        else:
            out.append([i, i + 1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--roster", required=True, type=Path)
    ap.add_argument("--m1-design", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--m3-design", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m4-design", required=True, type=Path)
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.m1_design) == BLOB_M1_DESIGN
       and file_blob(a.m1_raw) == BLOB_M1_RAW and file_blob(a.m3_design) == BLOB_M3_DESIGN
       and file_blob(a.m3_raw) == BLOB_M3_RAW and file_blob(a.m4_design) == BLOB_M4_DESIGN and file_blob(a.g10_counterfactuals) == BLOB_G10_CF, "pins")
    spec = importlib.util.spec_from_file_location("sa", WORK / "A461_g5_g2_stage_a_cpu_freeze_v1.py")
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    ck(sha_file(sa.CORPUS) == sa.CORPUS_SHA, "corpus pin")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    m1 = json.loads(a.m1_design.read_text("utf8"))
    m3 = json.loads(a.m3_design.read_text("utf8"))
    m4 = json.loads(a.m4_design.read_text("utf8"))
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    m3raw = [json.loads(x) for x in a.m3_raw.read_text("utf8").splitlines() if x.strip()]
    donors, hosts = m1["selection"]["donors"], m1["selection"]["hosts"]
    ck(len(donors) == 14 and len(hosts) == 8 and m3["selection"] == {"donors": donors, "hosts": hosts}, "selection")
    gd, gh = dict(donors), dict(hosts)
    m1_cap = {(x["target_scene"], x["target_arm"]): x["forward_index"] for x in m1raw if x["capture"]}
    m3_all = {(x["donor"], x["host"], x["source_kind"]): x["forward_index"] for x in m3raw
              if x["patch"] and x["patch"]["arm"] == "all"}
    ck(len(m3_all) == 208, "208 M3 all-heads rows")

    # ---------- key classes (tokenizer only) ----------
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
        items = list(zip(starts, starts[1:] + [s1]))
        for (p, q), m in zip(items, msgs):
            txt = "".join(dec[p:q])
            ck(all(f"{k}: {m[k]}" in txt for k in ("author", "block", "kind")), f"item text at {s[:8]}:{arm}:{p}")
        rnd, A = st["candidate_round"], msg["author"]
        allowed = set(st["validator_set"])
        base = roster[s]["declared_edit_new"]["message"]
        partner, peers, other, pmsg = [], [], [], None
        for (p, q), m in zip(items[:-1], msgs[:-1]):
            if (m.get("kind") == "vote" and m.get("round") == rnd and m.get("author") == A
                    and m.get("block") != base["block"] and m.get("author") in allowed
                    and isinstance(m.get("received"), (int, float)) and m["received"] <= st["decision_time"]):
                partner.append([p, q])
                pmsg = m
            elif m.get("kind") == "vote" and m.get("round") == rnd and m.get("author") != A:
                peers.append([p, q])
            else:
                other.append([p, q])
        ck(len(partner) == 1 and partner[0][1] - partner[0][0] == 33, f"partner at {s[:8]}:{arm}")
        ck(other, f"no OTHER_ITEMS at {s[:8]}:{arm}")
        used = {k for lo, hi in partner + peers + other + [[s0, s1]] for k in range(lo, hi)}
        cls = {"PARTNER": partner, "ROUND_PEERS": peers, "OTHER_ITEMS": other, "SELF": [[s0, s1]],
               "CONTEXT": ranges([k for k in range(s1) if k not in used])}
        cover = sorted(k for v in cls.values() for lo, hi in v for k in range(lo, hi))
        ck(cover == list(range(s1)), f"classes do not partition the keys < span end at {s[:8]}:{arm}")
        mk = m4["key_classes"][f"{arm}:{s[:12]}"]
        ck(mk["classes"] == cls and mk["token_ids_sha256"] == tid, f"M4 key classes differ at {s[:8]}:{arm}")
        mc = m3["token_classes"][f"{arm}:{s[:12]}"]
        ck(mc["partner"] == partner and mc["round_peers"] == peers and mc["span"] == [s0, s1]
           and mc["token_ids_sha256"] == tid, f"M3 token classes differ at {s[:8]}:{arm}")
        return {"span": [s0, s1], "classes": cls, "state_len": len(ids), "token_ids_sha256": tid,
                "partner_token_ids": ids[partner[0][0]:partner[0][1]], "partner_message": pmsg, "author": A}

    key_classes = {}
    rows = []

    def add(**kw):
        n = len(rows)
        rows.append(dict(forward_index=n + 1, run=n // 128 + 1, **kw))

    for kind, sel in (("donor", donors), ("host", hosts)):
        for s, _g in sel:
            for arm in SOURCES:
                tag = f"{arm}:{s[:12]}"
                key_classes[tag] = classes(s, arm)
                add(phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm,
                    source_kind=kind,
                    capture={"tag": tag, "span": span(s, arm), "rows": "all", "save": True, "layer": HEAD_LAYER,
                             "classes": key_classes[tag]["classes"], "partner": key_classes[tag]["classes"]["PARTNER"][0]},
                    bitwise_vs_m1=m1_cap.get((s, arm)))
    ck(sum(1 for r in rows if r["bitwise_vs_m1"]) == 36, "36 M1 bitwise anchors")
    dlist = [d for d, _ in donors]
    third_of = {}
    for d, _ in donors:
        for h, _ in hosts:
            if gd[d] == gh[h]:
                continue
            k = dlist.index(d)
            third = next(t for t in dlist[k + 1:] + dlist[:k] if gd[t] not in (gd[d], gh[h]))
            third_of[f"{d[:12]}|{h[:12]}"] = third
            seed = int(hashlib.sha256(f"A461_M5_RAND|{d}|{h}".encode()).hexdigest()[:8], 16)
            for arm, op, cl in ARMS:
                for src in SOURCES:
                    sk = "main" if src == "new" else "round"
                    patch = {"layer": HEAD_LAYER, "arm": arm, "op": op, "classes": cl, "span": span(h, "new"),
                             "source": f"{src}:{d[:12]}", "target": f"new:{h[:12]}", "rows": "all"}
                    if op == "rand":
                        patch["seed"] = seed
                    if op == "xdonor":
                        patch["third"] = f"{src}:{third[:12]}"
                    add(phase="patch", condition=f"patch_m5_{arm}_{sk}", direction="repair", scope="all",
                        source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                        target_arm="new", patch=patch,
                        bitwise_vs_m3=m3_all[(d, h, sk)] if op == "full" else None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * len(ARMS) * 2 == 2496, "104 x 12 x 2 patches")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m3")) == 208, "208 M3 bitwise anchors")
    design = {"schema": "JEV_A461_MECH_M5_MAGNITUDE_DIRECTION_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M5_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader); L11 = Qwen3.5 full attention, "
                       "16 query heads x 256 in 4 KV groups, output gate, o_proj without bias",
              "inputs": {"roster_blob": BLOB_ROSTER, "m1_design_blob": BLOB_M1_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                         "m3_design_blob": BLOB_M3_DESIGN, "m3_raw_blob": BLOB_M3_RAW, "m4_design_blob": BLOB_M4_DESIGN,
                         "g10_counterfactuals_blob": BLOB_G10_CF, "g5v2_questions_blob": g5_full,
                         "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV, "base_classes": list(BASE),
              "arms": [[n, op, cl] for n, op, cl in ARMS], "dir_classes": DIR_CLASSES, "bulk": BULK,
              "third_donor": third_of,
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "key_classes": key_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M5 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m5_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m5_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m5_design.json", "m5_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 2496,
                      "class_sizes": {t: {k: sum(hi - lo for lo, hi in v) for k, v in c["classes"].items()}
                                      for t, c in list(key_classes.items())[:3]},
                      "manifest_blob": file_blob(out / "m5_manifest.jsonl"),
                      "design_blob": file_blob(out / "m5_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
