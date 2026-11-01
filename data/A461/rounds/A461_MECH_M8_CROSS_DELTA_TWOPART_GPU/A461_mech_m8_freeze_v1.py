#!/usr/bin/env python3
"""A461-MECH-M8 R1: CPU freeze of the cross-kind delta-basis, two-part and contrast-scaling tests of the L11 BULK write
of kev-4B (zero model forwards; tokenizer only, for the key classes).

M7 (edc49cb): a basis of other donors' SAME-KIND differences to the host, {p_B(a) - h_B(a)}, recovers the main repair
but not the round-specificity (dlr64_sm S 24, J_round 18, frac 0.72); M6's raw basis rescaled keeps the round
contrast but not the main push (lr64_sm 19, SPEC); the pooled round contrast c = mean_D B(ROUND) - mean_D B(new) is
inert alone (rcD 0) but separates J 39 from J 0 inside meanD_host. M8 asks:
  X  cross-kind delta basis: xdlr{k}_sm = host + alpha U_k U_k^T delta_B with U_k from {p_B(a) - h_B(new) : p in
     Pool_D, a in new, ROUND} (the cell's delta_B is formed the same way), alpha as M7 (size-matched, cap 10);
     k in 4, 16, 64; xdlr64 = the same without rescaling
  T  two-part: tp{k} = host + alpha U_k U_k^T delta_B(new) [M7 same-kind basis] + [round source] c_own, c_own =
     d_B(ROUND) - d_B(new) (the cell's donor); k in 16, 64; tpD64 = the same with the pooled-donor contrast
  C  contrast scaling on the common shift: cs{s} = host - h_B + (mean_D B(new) + mean_D B(ROUND)) / 2 -+ (s/2) c
     (- main, + round), s in 0, 0.5, 1, 2 (s = 1 is meanD_host up to float rounding)
Anchors: full (M3 all-heads, bitwise, 51), meanD_host (M6 rows, bitwise, 39), dlr64_sm and rand64_sm (M7 rows
replayed; S 24 and 1). 44 captures + 104 x 15 x 2 = 3164 calls in 24 x 128 + 92.
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
BLOB_M7_DESIGN = "f7d5318c1bfe24521831cc322be08bd6ed08fa17"
BLOB_M7_RAW = "0383fccf01ad027ae14c59c8fc9830f1d398219e"
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
N_HEADS, N_KV = 16, 4
SOURCES = ("new", "ROUND")
BASE = ("PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT")
BULK = ["OTHER_ITEMS", "CONTEXT"]
KS = [4, 16, 64]          # cross-kind basis ranks
TP_KS = [16, 64]          # two-part ranks
CS = [("0", 0.0), ("05", 0.5), ("1", 1.0), ("2", 2.0)]
ALPHA_CAP = 10.0
# (name, op, classes, extra)
ARMS = ([("full", "full", [], {}),
         ("meanD_host", "pool", BULK, {"base": "target", "pool": "donors"}),
         ("dlr64_sm", "dlowrank", BULK, {"k": 64, "rescale": "delta", "pairs": "same"}),
         ("rand64_sm", "randsub", BULK, {"k": 64, "rescale": "delta"})]
        + [(f"xdlr{k}_sm", "dlowrank", BULK, {"k": k, "rescale": "delta", "pairs": "cross"}) for k in KS]
        + [("xdlr64", "dlowrank", BULK, {"k": 64, "rescale": None, "pairs": "cross"})]
        + [(f"tp{k}", "twopart", BULK, {"k": k, "contrast": "own"}) for k in TP_KS]
        + [("tpD64", "twopart", BULK, {"k": 64, "contrast": "donors"})]
        + [(f"cs{n}", "cshift", BULK, {"s": s}) for n, s in CS])
PLAN = [128] * 24 + [92]

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
                        "checked in the run); the M7 replays dlr64_sm and rand64_sm give S = 24 and S = 1 as in M7; "
                        "otherwise every verdict is INCONSISTENT_WITH_M3_M6_M7 and no claim. The bitwise equality of "
                        "the M7 replay rows (dlr64_sm, rand64_sm; the main rows of tp16 / tp64 / tpD64 against M7 "
                        "dlr16_sm / dlr64_sm) is reported, not gated (CPU SVD / QR reproducibility)",
    "size_gate": "per row and span position, the change of a rescaled arm (xdlr*_sm, dlr64_sm, rand64_sm, and the "
                 "low-rank part of tp*) equals alpha ||U_k U_k^T delta_B|| within 1e-3 relative (fail-closed in the "
                 "runner), alpha = min(||delta_B|| / ||U_k U_k^T delta_B||, 10) (rand64_sm: no cap); energy, alpha and "
                 "the capped share are recorded",
    "null": "NULL holds iff S(rand64_sm) <= 5 and not SPEC(rand64_sm)",
    "xdelta_verdict": "k* = the smallest k in 4, 16, 64 with SUF(xdlr{k}_sm). XDELTA_LOWRANK:k* if k* exists and NULL "
                      "holds; XDELTA_LOWRANK_UNRESOLVED:k* if k* exists and NULL fails; NOT_XDELTA_LOWRANK_LE64 if no k*",
    "twopart_verdict": "k* = the smallest k in 16, 64 with SUF(tp{k}). TWOPART:k* if k* exists and NULL holds; "
                       "TWOPART_UNRESOLVED:k* if k* exists and NULL fails; NOT_TWOPART if no k*",
    "contrast_source_verdict": "POOLED_CONTRAST_SUFFICES if SUF(tpD64); OWN_CONTRAST_NEEDED if SUF(tp64) and not "
                               "SUF(tpD64); CONTRAST_SOURCE_NA otherwise",
    "cshift_verdict": "s* = the smallest s in 0.5, 1, 2 with SUF(cs{s}); CS_SUFFICIENT:s* if s* exists, else CS_NONE. "
                      "cs0 has identical main and round patches (S = 0 by construction); its J count is reported as "
                      "the common shift alone",
    "nonadditivity_verdict": "C(arm) = median over cells of dM_main - dM_round. CONTRAST_NONADDITIVE iff C(cs2) > 0 and "
                             "C(cs2) >= 3 |C(rcD)|, with rcD taken from the M7 raw rows (the same contrast -+ c on the "
                             "plain host); otherwise CONTRAST_ADDITIVE_OR_WEAK",
    "interpretation_fixed_in_advance": "XDELTA_LOWRANK:k: the repairing part of delta_B, round contrast included, lies in "
        "a k-dimensional subspace of other donors' differences to the host's new BULK, at matched size; a random "
        "subspace at that size does not repair. NOT_XDELTA_LOWRANK_LE64: adding the round kind to the basis does not "
        "make delta_B low-rank. TWOPART:k: a k-dimensional common part of the donor-new difference plus the donor's own "
        "new-vs-ROUND contrast suffices. POOLED_CONTRAST_SUFFICES: the contrast need not be the cell's own; "
        "OWN_CONTRAST_NEEDED: it must. CS_SUFFICIENT:s: on top of the pooled common BULK shift, the pooled contrast at "
        "scale s gives the round-specific repair. CONTRAST_NONADDITIVE: the same contrast moves the round-vs-main "
        "margin at least 3 times more on the common shift than on the plain host. The pooled arms (cs*, tpD64 "
        "contrast) vary with the donor only through the pool exclusion (effectively 8 hosts); per-host S is the honest "
        "unit there. The cs arms are not size-matched; change norms relative to full are reported",
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
    ap.add_argument("--m7-design", required=True, type=Path)
    ap.add_argument("--m7-raw", required=True, type=Path)
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.m1_design) == BLOB_M1_DESIGN
       and file_blob(a.m1_raw) == BLOB_M1_RAW and file_blob(a.m3_design) == BLOB_M3_DESIGN
       and file_blob(a.m3_raw) == BLOB_M3_RAW and file_blob(a.m4_design) == BLOB_M4_DESIGN and file_blob(a.g10_counterfactuals) == BLOB_G10_CF
       and file_blob(a.m6_design) == BLOB_M6_DESIGN and file_blob(a.m6_raw) == BLOB_M6_RAW
       and file_blob(a.m7_design) == BLOB_M7_DESIGN and file_blob(a.m7_raw) == BLOB_M7_RAW, "pins")
    spec = importlib.util.spec_from_file_location("sa", WORK / "A461_g5_g2_stage_a_cpu_freeze_v1.py")
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    ck(sha_file(sa.CORPUS) == sa.CORPUS_SHA, "corpus pin")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    m1 = json.loads(a.m1_design.read_text("utf8"))
    m3 = json.loads(a.m3_design.read_text("utf8"))
    m4 = json.loads(a.m4_design.read_text("utf8"))
    m6 = json.loads(a.m6_design.read_text("utf8"))
    m7 = json.loads(a.m7_design.read_text("utf8"))
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    m3raw = [json.loads(x) for x in a.m3_raw.read_text("utf8").splitlines() if x.strip()]
    m6raw = [json.loads(x) for x in a.m6_raw.read_text("utf8").splitlines() if x.strip()]
    m7raw = [json.loads(x) for x in a.m7_raw.read_text("utf8").splitlines() if x.strip()]
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
    m7_rows = {(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"]): x for x in m7raw if x["patch"]}
    ck(len(m7_rows) == 13 * 208 and m7["selection"] == m3["selection"] and m7["pools"] == m6["pools"], "M7 rows")

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
        ck(m7["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M7 key classes differ at {s[:8]}:{arm}")
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
                    same_pairs = [[f"{a_}:{t[:12]}", f"{a_}:{h[:12]}"] for t in pool_d for a_ in SOURCES]
                    if op in ("dlowrank", "randsub", "twopart"):
                        patch["k"] = ex["k"]
                        patch["rescale"] = ex.get("rescale", "delta")
                    if op == "dlowrank":  # M7 same-kind pairs, or cross-kind pairs against the host's new BULK
                        patch["basis_pairs"] = (same_pairs if ex["pairs"] == "same" else
                                                [[f"{a_}:{t[:12]}", f"new:{h[:12]}"] for t in pool_d for a_ in SOURCES])
                    if op == "randsub":   # the M7 seed (same frame per cell)
                        patch["seed"] = int(hashlib.sha256(f"A461_M7_RANDSUB|{ex['k']}|{d}|{h}".encode()).hexdigest()[:8], 16)
                    if op == "twopart":   # low-rank part of the donor-NEW difference, plus a round contrast on the round source
                        patch["basis_pairs"] = same_pairs
                        patch["lowpart_source"] = f"new:{d[:12]}"
                        cp = [d] if ex["contrast"] == "own" else pool_d
                        patch["plus"] = [f"ROUND:{t[:12]}" for t in cp]
                        patch["minus"] = [f"new:{t[:12]}" for t in cp]
                        patch["scale"] = 0.0 if sk == "main" else 1.0
                    if op == "cshift":    # common pooled shift, -+ s/2 of the pooled contrast
                        patch["base"] = "target"
                        patch["pool_new"] = [f"new:{t[:12]}" for t in pool_d]
                        patch["pool_round"] = [f"ROUND:{t[:12]}" for t in pool_d]
                        patch["scale"] = 0.0 if ex["s"] == 0 else (-ex["s"] / 2 if sk == "main" else ex["s"] / 2)
                    if arm in ("dlr64_sm", "rand64_sm"):   # M7 replays: identical patch fields
                        m7p = m7_rows[(arm, d, h, sk)]["patch"]
                        ck(all(m7p.get(k_) == v_ for k_, v_ in patch.items()), f"M7 {arm} wiring")
                    if op == "twopart":   # its main patch is the M7 dlr{k}_sm main patch
                        m7p = m7_rows[(f"dlr{ex['k']}_sm", d, h, "main")]["patch"]
                        ck(all(m7p[k_] == patch[k_] for k_ in ("k", "rescale", "basis_pairs", "target", "span", "classes"))
                           and m7p["source"] == patch["lowpart_source"], f"M7 dlr{ex['k']}_sm wiring")
                    add(phase="patch", condition=f"patch_m8_{arm}_{sk}", direction="repair", scope="all",
                        source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                        target_arm="new", patch=patch,
                        bitwise_vs_m3=m3_all[(d, h, sk)] if op == "full" else None,
                        bitwise_vs_m6=m6_md[(d, h, sk)]["forward_index"] if op == "pool" else None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * len(ARMS) * 2 == 3120, "104 x 15 x 2 patches")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m3")) == 208, "208 M3 bitwise anchors")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m6")) == 208, "208 M6 bitwise anchors")
    design = {"schema": "JEV_A461_MECH_M8_XDELTA_TWOPART_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M8_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader); L11 = Qwen3.5 full attention, "
                       "16 query heads x 256 in 4 KV groups, output gate, o_proj without bias",
              "inputs": {"roster_blob": BLOB_ROSTER, "m1_design_blob": BLOB_M1_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                         "m3_design_blob": BLOB_M3_DESIGN, "m3_raw_blob": BLOB_M3_RAW, "m4_design_blob": BLOB_M4_DESIGN,
                         "m6_design_blob": BLOB_M6_DESIGN, "m6_raw_blob": BLOB_M6_RAW,
                         "m7_design_blob": BLOB_M7_DESIGN, "m7_raw_blob": BLOB_M7_RAW,
                         "g10_counterfactuals_blob": BLOB_G10_CF, "g5v2_questions_blob": g5_full,
                         "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV, "base_classes": list(BASE),
              "arms": [[n, op, cl, ex] for n, op, cl, ex in ARMS], "ks": KS, "tp_ks": TP_KS, "cs": CS, "alpha_cap": ALPHA_CAP, "bulk": BULK,
              "pools": pools,
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "key_classes": key_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M8 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m8_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m8_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m8_design.json", "m8_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 3120,
                      "class_sizes": {t: {k: sum(hi - lo for lo, hi in v) for k, v in c["classes"].items()}
                                      for t, c in list(key_classes.items())[:3]},
                      "manifest_blob": file_blob(out / "m8_manifest.jsonl"),
                      "design_blob": file_blob(out / "m8_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
