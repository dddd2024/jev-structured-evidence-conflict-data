#!/usr/bin/env python3
"""A461-MECH-M7 R1: CPU freeze of the delta-basis, mean-difference and round-contrast tests of the L11 BULK write of
kev-4B (zero model forwards; tokenizer only, for the key classes).

M6 (18aae99): the BULK part (OTHER_ITEMS + CONTEXT key-class contributions of the L11 span write) pooled over 12
other donors repairs hosts round-specifically (meanD_host 39, SHARED_DONOR_COMPONENT); the pooled BULK of other
hosts gives 17 (SPEC, below SUF); the cell's delta_B projected on the top-64 directions of the other donors' RAW BULK
contributions gives 10 (NOT_LOWRANK_LE64), with that basis uncentred and the projection not rescaled. M7 asks:
  D  delta basis: dlr{k}_sm = host + alpha * U_k U_k^T delta_B, U_k = top-k right singular vectors of the other
     donors' differences to the same host, {p_B(a) - h_B(a) : p in Pool_D, a in new, ROUND} (744 vectors), and
     alpha = min(||delta_B|| / ||U_k U_k^T delta_B||, 10) per row and span position (size-matched to delta_B);
     k in 1, 4, 16, 64; dlr64 = the same without rescaling
  S  size of the M6 negative: lr64_sm = M6's raw-basis lr64 projection, rescaled as above
  N  null: rand64_sm = host + Q Q^T delta_B rescaled to ||delta_B|| (seeded random 64-frame per cell)
  M  mean difference: mdir{s} = host + s * (mean_{Pool_D} p_B(src) - mean_{Pool_H} h'_B(src)), s in 1, 2
  R  round contrast without the donor: rc{H,D} = host + sign * (mean_pool B(ROUND) - mean_pool B(new)) with
     sign = -1 for the main source, +1 for the round source; pool = Pool_H (rcH) or Pool_D (rcD)
`full` = the M3 all-heads patch (bitwise anchor, 51); `meanD_host` = the M6 pooled-donor arm (bitwise anchor of
the M6 rows, 39). 44 captures + 104 x 13 x 2 = 2748 calls in 21 x 128 + 60.
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
BLOB_M6_DESIGN = "43967513c3dbcad74dd7b024b67a16463f456ffc"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
N_HEADS, N_KV = 16, 4
SOURCES = ("new", "ROUND")
BASE = ("PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT")
BULK = ["OTHER_ITEMS", "CONTEXT"]
KS = [1, 4, 16, 64]
ALPHA_CAP = 10.0
# (name, op, classes, extra)
ARMS = ([("full", "full", [], {}),
         ("meanD_host", "pool", BULK, {"base": "target", "pool": "donors"})]
        + [(f"dlr{k}_sm", "dlowrank", BULK, {"k": k, "rescale": "delta"}) for k in KS]
        + [("dlr64", "dlowrank", BULK, {"k": 64, "rescale": None}),
           ("lr64_sm", "lowrank", BULK, {"k": 64, "rescale": "delta"}),
           ("rand64_sm", "randsub", BULK, {"k": 64, "rescale": "delta"}),
           ("mdir1", "meandiff", BULK, {"plus": "donors", "minus": "hosts", "scale": 1.0}),
           ("mdir2", "meandiff", BULK, {"plus": "donors", "minus": "hosts", "scale": 2.0}),
           ("rcH", "meandiff", BULK, {"plus": "hosts@ROUND", "minus": "hosts@new", "scale": "signed"}),
           ("rcD", "meandiff", BULK, {"plus": "donors@ROUND", "minus": "donors@new", "scale": "signed"})])
PLAN = [128] * 21 + [60]

PREREG = {
    "readouts": "M = conflict margin; A = logit(reject_conflict) - max(accept, wait); JOINT = M > 0 and A > 0; "
                "dM = M(patch) - M(in-run capture of host new)",
    "units": "the 104 cross-group cells of M1-M6; cells share donors and hosts, and the pooled-mean arms vary with "
             "the donor only through the pool exclusion (effectively 8 hosts), so counts are descriptive decision "
             "rules, not independent tests; per-host S is always reported",
    "S": "S(arm) = #cells where the donor-new-source patch is JOINT and the donor-ROUND-source patch of the same arm "
         "is not (target host new)",
    "SPEC": "SPEC iff dM_main > dM_round in >= 75% of cells AND in a majority of cells for >= 10 of 14 donor groups",
    "SUF": "SUF(arm) iff S(arm) >= 1/2 S(full) and SPEC(arm)",
    "consistency_gate": "full = the M3 all-heads patch: its 208 rows equal M3's bitwise and S(full) = 51; "
                        "meanD_host = the M6 pooled-donor arm: its 208 rows equal M6's bitwise and S = 39 (GPU, "
                        "checked in the run); otherwise every verdict is INCONSISTENT_WITH_M3_M6 and no claim",
    "size_gate": "per row and span position, the change of a rescaled arm equals min(||delta_B||, 10 ||U_k U_k^T "
                 "delta_B||) (dlr*_sm, lr64_sm) or ||delta_B|| (rand64_sm) within 1e-3 relative (fail-closed in the "
                 "runner); energy ||U_k U_k^T delta_B|| / ||delta_B||, alpha and the capped share are recorded",
    "delta_lowrank_verdict": "k* = the smallest k in 1, 4, 16, 64 with SUF(dlr{k}_sm); NULL holds iff S(rand64_sm) "
                             "<= 5 and not SPEC(rand64_sm). DELTA_LOWRANK:k* if k* exists and NULL holds; "
                             "DELTA_LOWRANK_UNRESOLVED:k* if k* exists and NULL fails; NOT_DELTA_LOWRANK_LE64 if no k*",
    "m6_lr64_size": "LR64_SIZE_LIMITED if SUF(lr64_sm), else LR64_BASIS_LIMITED",
    "meandiff_verdict": "s* = the smallest s in 1, 2 with SUF(mdir{s}); MEANDIFF_DIRECTION:s* if s* exists and NULL "
                        "holds; MEANDIFF_UNRESOLVED:s* if s* exists and NULL fails; NOT_MEANDIFF otherwise",
    "round_contrast_verdict": "RC_GENERIC if SUF(rcH); RC_DONOR_POOL_ONLY if SUF(rcD) and not SUF(rcH); "
                              "RC_INSUFFICIENT otherwise; the median dM of the round source (+contrast) and of the "
                              "main source (-contrast) of rcH and rcD are always reported",
    "interpretation_fixed_in_advance": "DELTA_LOWRANK:k: the repairing part of the cell's donor-minus-host BULK "
        "difference lies in a k-dimensional subspace of OTHER donors' differences to the same host, at matched size, "
        "and a random subspace at that size does not repair. NOT_DELTA_LOWRANK_LE64: not even a 64-dimensional "
        "difference subspace carries it. LR64_SIZE_LIMITED: M6's lr64 failure (S 10) was a size effect of the "
        "unrescaled projection; LR64_BASIS_LIMITED: it was the raw basis. MEANDIFF_DIRECTION:s: one fixed "
        "position-wise vector per source kind, the pooled donor BULK minus the pooled host BULK, added to the host "
        "repairs it round-specifically: the shared component is a donor-vs-host difference, not the donor's absolute "
        "BULK. RC_GENERIC: the new-vs-ROUND contrast of other hosts' BULK alone, subtracted (main) or added (round), "
        "produces the round-specific JOINT pattern: the round contrast needs no repairing donor. RC_DONOR_POOL_ONLY: "
        "only the donors' contrast does. RC_INSUFFICIENT: the contrast alone is not enough. The mdir and rc arms vary "
        "with the donor only through the pool exclusion (effectively 8 hosts); per-host S is the honest unit there. "
        "The mdir and rc arms are not size-matched; their change norms relative to full are reported. A rescaled "
        "arm at large alpha (capped at 10) is off-distribution; alpha and the capped share are reported",
    "always_reported": "S, SPEC, J_main, J_round and median dM per arm; per host; leave-one-donor-group-out of "
                       "every verdict; energy, alpha and capped share of the subspace arms; change norm of every "
                       "arm relative to the full patch; all nulls",
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
    ap.add_argument("--m6-design", required=True, type=Path)
    ap.add_argument("--m6-raw", required=True, type=Path)
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.m1_design) == BLOB_M1_DESIGN
       and file_blob(a.m1_raw) == BLOB_M1_RAW and file_blob(a.m3_design) == BLOB_M3_DESIGN
       and file_blob(a.m3_raw) == BLOB_M3_RAW and file_blob(a.m4_design) == BLOB_M4_DESIGN and file_blob(a.g10_counterfactuals) == BLOB_G10_CF
       and file_blob(a.m6_design) == BLOB_M6_DESIGN and file_blob(a.m6_raw) == BLOB_M6_RAW, "pins")
    spec = importlib.util.spec_from_file_location("sa", WORK / "A461_g5_g2_stage_a_cpu_freeze_v1.py")
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    ck(sha_file(sa.CORPUS) == sa.CORPUS_SHA, "corpus pin")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    m1 = json.loads(a.m1_design.read_text("utf8"))
    m3 = json.loads(a.m3_design.read_text("utf8"))
    m4 = json.loads(a.m4_design.read_text("utf8"))
    m6 = json.loads(a.m6_design.read_text("utf8"))
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    m3raw = [json.loads(x) for x in a.m3_raw.read_text("utf8").splitlines() if x.strip()]
    m6raw = [json.loads(x) for x in a.m6_raw.read_text("utf8").splitlines() if x.strip()]
    donors, hosts = m1["selection"]["donors"], m1["selection"]["hosts"]
    ck(len(donors) == 14 and len(hosts) == 8 and m3["selection"] == {"donors": donors, "hosts": hosts}, "selection")
    gd, gh = dict(donors), dict(hosts)
    m1_cap = {(x["target_scene"], x["target_arm"]): x["forward_index"] for x in m1raw if x["capture"]}
    m3_all = {(x["donor"], x["host"], x["source_kind"]): x["forward_index"] for x in m3raw
              if x["patch"] and x["patch"]["arm"] == "all"}
    ck(len(m3_all) == 208, "208 M3 all-heads rows")
    m6_md = {(x["donor"], x["host"], x["source_kind"]): x for x in m6raw
             if x["patch"] and x["patch"]["arm"] == "meanD_host"}
    ck(len(m6_md) == 208 and m6["selection"] == m3["selection"], "208 M6 meanD_host rows")

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
        ck(m6["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M6 key classes differ at {s[:8]}:{arm}")
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
    pools = {}
    hlist = [h for h, _ in hosts]
    for d, _ in donors:
        for h, _ in hosts:
            if gd[d] == gh[h]:
                continue
            pool_d = [t for t in dlist if gd[t] not in (gd[d], gh[h])]
            pool_h = [t for t in hlist if t != h and gh[t] != gd[d]]
            ck(len(pool_d) == 12 and d not in pool_d and pool_h and h not in pool_h, "pools")
            pools[f"{d[:12]}|{h[:12]}"] = {"donors": [t[:12] for t in pool_d], "hosts": [t[:12] for t in pool_h]}
            ck(m6["pools"][f"{d[:12]}|{h[:12]}"] == pools[f"{d[:12]}|{h[:12]}"], "pools != M6")
            for arm, op, cl, ex in ARMS:
                for src in SOURCES:
                    sk = "main" if src == "new" else "round"
                    patch = {"layer": HEAD_LAYER, "arm": arm, "op": op, "classes": cl, "span": span(h, "new"),
                             "source": f"{src}:{d[:12]}", "target": f"new:{h[:12]}", "rows": "all"}
                    if op == "pool":
                        patch["base"] = ex["base"]
                        patch["pool"] = [f"{src}:{t[:12]}" for t in (pool_d if ex["pool"] == "donors" else pool_h)]
                        mx = m6_md[(d, h, sk)]["patch"]
                        ck(all(mx[k_] == patch[k_] for k_ in ("base", "pool", "source", "target", "span", "classes")),
                           "M6 meanD_host wiring")
                    if op in ("lowrank", "dlowrank", "randsub"):
                        patch["k"] = ex["k"]
                        patch["rescale"] = ex["rescale"]
                    if op == "lowrank":   # the M6 raw basis (same tags, same order as M6 lr_k)
                        patch["basis_pool"] = [f"{a_}:{t[:12]}" for t in pool_d for a_ in SOURCES]
                    if op == "dlowrank":  # other donors' differences to the same host, same arm
                        patch["basis_pairs"] = [[f"{a_}:{t[:12]}", f"{a_}:{h[:12]}"] for t in pool_d for a_ in SOURCES]
                    if op == "randsub":
                        patch["seed"] = int(hashlib.sha256(f"A461_M7_RANDSUB|{ex['k']}|{d}|{h}".encode()).hexdigest()[:8], 16)
                    if op == "meandiff":
                        grp = lambda w: pool_d if w == "donors" else pool_h
                        if ex["scale"] == "signed":
                            (pw, pa), (mw, ma) = ex["plus"].split("@"), ex["minus"].split("@")
                            patch["plus"] = [f"{pa}:{t[:12]}" for t in grp(pw)]
                            patch["minus"] = [f"{ma}:{t[:12]}" for t in grp(mw)]
                            patch["scale"] = -1.0 if sk == "main" else 1.0
                        else:
                            patch["plus"] = [f"{src}:{t[:12]}" for t in grp(ex["plus"])]
                            patch["minus"] = [f"{src}:{t[:12]}" for t in grp(ex["minus"])]
                            patch["scale"] = ex["scale"]
                    add(phase="patch", condition=f"patch_m7_{arm}_{sk}", direction="repair", scope="all",
                        source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                        target_arm="new", patch=patch,
                        bitwise_vs_m3=m3_all[(d, h, sk)] if op == "full" else None,
                        bitwise_vs_m6=m6_md[(d, h, sk)]["forward_index"] if op == "pool" else None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * len(ARMS) * 2 == 2704, "104 x 13 x 2 patches")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m3")) == 208, "208 M3 bitwise anchors")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m6")) == 208, "208 M6 bitwise anchors")
    design = {"schema": "JEV_A461_MECH_M7_DELTA_MEANDIFF_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M7_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader); L11 = Qwen3.5 full attention, "
                       "16 query heads x 256 in 4 KV groups, output gate, o_proj without bias",
              "inputs": {"roster_blob": BLOB_ROSTER, "m1_design_blob": BLOB_M1_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                         "m3_design_blob": BLOB_M3_DESIGN, "m3_raw_blob": BLOB_M3_RAW, "m4_design_blob": BLOB_M4_DESIGN,
                         "m6_design_blob": BLOB_M6_DESIGN, "m6_raw_blob": BLOB_M6_RAW,
                         "g10_counterfactuals_blob": BLOB_G10_CF, "g5v2_questions_blob": g5_full,
                         "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV, "base_classes": list(BASE),
              "arms": [[n, op, cl, ex] for n, op, cl, ex in ARMS], "ks": KS, "alpha_cap": ALPHA_CAP, "bulk": BULK,
              "pools": pools,
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "key_classes": key_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M7 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m7_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m7_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m7_design.json", "m7_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 2704,
                      "class_sizes": {t: {k: sum(hi - lo for lo, hi in v) for k, v in c["classes"].items()}
                                      for t, c in list(key_classes.items())[:3]},
                      "manifest_blob": file_blob(out / "m7_manifest.jsonl"),
                      "design_blob": file_blob(out / "m7_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
