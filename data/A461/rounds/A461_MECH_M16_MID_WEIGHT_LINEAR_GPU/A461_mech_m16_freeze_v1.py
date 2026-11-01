#!/usr/bin/env python3
"""A461-MECH-M16 R1: CPU freeze grading the common shift at the middle span positions 13-28 (the KIND, RECV and RKEY
lines of the appended item, between the author/block lines and the round line) by a weight w, to test whether M14's
lower AB contrast threshold is the linear readout consequence of that shift (zero model forwards; tokenizer only).

M15 (0e3339a): the AB shift lowers SMIN against the all-position shift on 264c458d and 4bcbaf15 whether or not c is
kept at 30 (Q1_GAIN_LOC_ONLY), while its C is lower at every s. The two arms differ only by the common shift at
13-28, the same tensor for the main and the round source. M16 asks, with c at 29 only:
  W  mw<tag>_<s>: the common shift at 13-28 times w in -1, -1/2, +1/2, +3/2 (1 at every other span position), at
     s = 1/4, 3/8, 1/2. w = 0 is M14's abc_<s>, w = 1 is M15's csc29_<s> (pinned rows).
  L  the per-cell, per-source linear predictions M(w), A(w) = (1 - w) x (w = 0 row) + w x (w = 1 row), computed here
     from the pinned M14 / M15 rows before any M16 forward and frozen in the design.
Anchors: full (M3, bitwise, 51) and meanD_host (M6, bitwise, 39) on all 208 rows; M14's abc_s0375 and M15's
csc29_s0375 replayed bitwise on the 6 subset cells; mw0_s0375 (the new shift_pos_weight field with weight 0 at 13-28)
on the same 6 cells must equal abc_s0375 bitwise (the GPU check of the new code path).
44 captures + 104 x 14 x 2 + 6 x 3 x 2 = 2992 calls in 23 x 128 + 48.
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
BLOB_M8_DESIGN = "14cee4c2cffe30d78338de8063c72110f223f0bb"
BLOB_M8_RAW = "997c9b71054ee2adec472a5410705068511650aa"
BLOB_M9_DESIGN = "fe91481e42e5cf33f20cd7c98dba16caf177268c"
BLOB_M9_RAW = "c74e5117da511f7d0be1503746b752f1a41c62b8"
BLOB_M10_DESIGN = "f127d850223174f8ef10997c8539a2c348102b89"
BLOB_M10_RAW = "755c74e1d722cdd0429916a13608fd60c647bb53"
BLOB_M11_DESIGN = "53d2bc8d89098c8e3434be9f11851bc459e1389a"
BLOB_M11_RAW = "393f0d6e7d4a698db15f9217202039c52ad663a8"
BLOB_M12_DESIGN = "3b2ef50f3f45274249b1ed05dcc578d67807f173"
BLOB_M12_RAW = "cc79f23a0dc6d80ec17bdad0fed54f710291dbe4"
BLOB_M13_DESIGN = "900b1f0595ab30f45cc07264a14280bf2f8c222a"
BLOB_M13_RAW = "cdbf677bd2b89d487045b104af040f2e39fcf5a3"
BLOB_M14_DESIGN = "87905a3c4d0a5786a25bbd974ef13c40f3f3c06b"
BLOB_M14_RAW = "d2ac9f4221728d309300cbf617385ad79925eb0b"
BLOB_M15_DESIGN = "4288440cb835cb1e36211c949878428a2dba2ad2"
BLOB_M15_RAW = "b6807b136acd3a00944705fae50b5d910946cf16"
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
N_HEADS, N_KV = 16, 4
SOURCES = ("new", "ROUND")
BASE = ("PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT")
BULK = ["OTHER_ITEMS", "CONTEXT"]
SPAN_W = 31
C_POS = [29, 30]      # the span positions where c != 0 in all M9-M11 captures (ROUND changes the token at 29)
SPLIT_K = 16
ALPHA_CAP = 10.0
# the appended item's fields (span-relative positions; the decoded markers are checked for every capture)
FIELDS = {"AUTH": list(range(0, 7)), "BLOCK": list(range(7, 13)), "KIND": list(range(13, 18)),
          "RECV": list(range(18, 25)), "RKEY": list(range(25, 29))}
FIELD_MARKS = {2: " author", 6: "\n", 8: " block", 12: "\n", 14: " kind", 17: "\n", 19: " received", 24: "\n",
               26: " round", 30: "\n"}
AB = FIELDS["AUTH"] + FIELDS["BLOCK"]      # 0-12: the author and block lines of the appended item
MID = list(range(13, 29))   # KIND, RECV, RKEY: the span positions where the AB arm has no common shift
RESP = ("1fb5651c", "264c458d", "4bcbaf15")   # the hosts with S(cs1) > half their cells in M9-M15
M15_REPLAY = ("full", "meanD_host", "abc_s0375", "csc29_s0375")   # identical patch fields to the M15 rows
SUBSET = ("abc_s0375", "csc29_s0375", "mw0_s0375")
W = ((-1.0, "m1"), (-0.5, "m05"), (0.5, "p05"), (1.5, "p15"))
CS = {"t": 1.0, "s": 1.0}
ABC = dict(CS, shpos=AB + C_POS, cw=0.0)
Q1_S = ((0.5, "_s05"), (0.375, "_s0375"), (0.25, "_s025"))


# (name, op, classes, extra)
ARMS = ([("full", "full", [], {}),
         ("meanD_host", "pool", BULK, {"base": "target", "pool": "donors"}),
         ("abc_s0375", "cshift", BULK, dict(ABC, s=0.375, sub=True)),
         ("csc29_s0375", "cshift", BULK, dict(CS, cw=0.0, s=0.375, sub=True)),
         ("mw0_s0375", "cshift", BULK, dict(CS, cw=0.0, s=0.375, mw=0.0, sub=True))]
        + [(f"mw{tg}{sfx}", "cshift", BULK, dict(CS, cw=0.0, s=s_, mw=w_)) for s_, sfx in Q1_S for w_, tg in W])
PLAN = [128] * 23 + [48]

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
                        "checked in the run); abc_s0375 = M14's AB arm and csc29_s0375 = M15's all-position c-29 arm "
                        "(same patch fields) on the 6 subset cells: their 2 x 12 rows equal M14's / M15's bitwise; "
                        "mw0_s0375 (shift_pos_weight 0 at 13-28) on the same 12 rows equals abc_s0375 bitwise; "
                        "otherwise every verdict is INCONSISTENT_WITH_M3_M6_M14_M15 and no claim",
    "C": "C(arm) = median over cells of dM_main - dM_round; C_h the same over host h's cells",
    "responsive_host": "a host where S(cs1) on its cells exceeds half its cells, with cs1 read from the pinned M13 "
                       "raw rows (1fb5651c, 264c458d, 4bcbaf15 in M13-M15)",
    "w_family": "for s in 1/4, 3/8, 1/2 and w in -1, -1/2, 0, 1/2, 1, 3/2: the common shift (t = 1) at all 31 span "
                "positions with the positions 13-28 multiplied by w, contrast -+ s/2 c with c_30 weight 0. w = 0 is "
                "M14 abc_<s> (pinned M14 rows), w = 1 is M15 csc29_<s> (pinned M15 rows), the other w are M16 "
                "mw<tag>_<s>",
    "linear_prediction": "for every M16 dose arm, cell and source, M_pred and A_pred = (1 - w) x the w = 0 row + w x "
                         "the w = 1 row (M = conflict margin, A = action margin), computed in the freeze from the "
                         "pinned rows and stored under linear_predictions; JOINT_pred = M_pred > 0 and A_pred > 0; "
                         "S_pred as S. Per responsive host: AGREE = share of the 13 x 2 x 3 x 4 = 312 (cell, source, "
                         "s, w) JOINT decisions where observed = predicted; dS = S_obs - S_pred per (s, w). "
                         "LINEAR_HOLDS iff AGREE >= 0.95 and max |dS| <= 1; LINEAR_FAILS iff AGREE < 0.90 or max "
                         "|dS| >= 3; else LINEAR_APPROX. LIN_BY_HOST lists the three hosts; pooled W_LINEAR: HOLDS "
                         "iff every responsive host HOLDS, FAILS iff any FAILS, else APPROX. Reported as well, not "
                         "verdicts: AGREE and max |dS| for w = 1/2 alone (interpolation) and for w = -1, -1/2, 3/2 "
                         "(extrapolation); R^2 and median |error| of M and A against the prediction per host",
    "w_trend": "per responsive host and s, over the 6 w in increasing order, of host S and of host C: NO_EFFECT iff "
               "all equal; OPPOSES iff non-increasing and first > last; SUPPORTS iff non-decreasing and first < "
               "last; PEAKED iff non-decreasing up to the first maximum, non-increasing after it, and both ends "
               "below the maximum; else MIXED (prefix WS_ for S, WC_ for C). DISSOC_BY_HOST: over the s where "
               "WS is not NO_EFFECT, S_C_DISSOCIATE iff at every such s WC = SUPPORTS and WS in {OPPOSES, "
               "PEAKED}; S_C_ALIGNED iff at every such s WS = WC in {SUPPORTS, OPPOSES}; UNINFORMATIVE iff no such "
               "s; else S_C_MIXED",
    "attribution": "always reported per responsive host, s and w: main JOINT count, round JOINT count among the "
                   "main-JOINT cells, round A > 0 and M > 0 counts, main and round median A and M, observed and "
                   "predicted",
    "size_gate": "every dose arm records shift weight min / max = min(w, 1) / max(w, 1) and the listed weight w; "
                 "abc_s0375, csc29_s0375, mw0 and every mw arm set c_30 to 0 exactly",
    "interpretation_fixed_in_advance": "W_LINEAR HOLDS: within w in [-1, 3/2] each cell's M and A move linearly in "
        "the weight of the common shift at 13-28, so the AB / all-position difference in S, and M14's lower AB "
        "threshold, is the threshold readout of a linear per-cell, per-source effect of that shift on M and A; "
        "it is not evidence of a contrast component carried by the author and block lines. FAILS: the middle "
        "shift interacts non-linearly with the rest of the patch, and the two endpoints do not describe the "
        "intermediate patches. S_C_DISSOCIATE on a host: lowering the middle weight raises S while it lowers C, so "
        "on that host S at a fixed s ranks arms opposite to the contrast they carry; ALIGNED: they agree. All arms "
        "except full are pooled-donor arms (effectively 8 host replicates, 3 responding); per-host S is the honest "
        "unit; comparisons with M14 / M15 rows are valid because the replay arms are bitwise equal",
    "always_reported": "S, SPEC, J_main, J_round, median dM and C per arm; S and C per host; observed and predicted "
                       "S per host, s and w; leave-one-donor-group-out of every verdict; shift weight stats; change "
                       "norm of every arm relative to full",
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
    ap.add_argument("--m8-design", required=True, type=Path)
    ap.add_argument("--m8-raw", required=True, type=Path)
    ap.add_argument("--m9-design", required=True, type=Path)
    ap.add_argument("--m9-raw", required=True, type=Path)
    ap.add_argument("--m10-design", required=True, type=Path)
    ap.add_argument("--m10-raw", required=True, type=Path)
    ap.add_argument("--m11-design", required=True, type=Path)
    ap.add_argument("--m11-raw", required=True, type=Path)
    ap.add_argument("--m12-design", required=True, type=Path)
    ap.add_argument("--m12-raw", required=True, type=Path)
    ap.add_argument("--m13-design", required=True, type=Path)
    ap.add_argument("--m13-raw", required=True, type=Path)
    ap.add_argument("--m14-design", required=True, type=Path)
    ap.add_argument("--m14-raw", required=True, type=Path)
    ap.add_argument("--m15-design", required=True, type=Path)
    ap.add_argument("--m15-raw", required=True, type=Path)
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.m1_design) == BLOB_M1_DESIGN
       and file_blob(a.m1_raw) == BLOB_M1_RAW and file_blob(a.m3_design) == BLOB_M3_DESIGN
       and file_blob(a.m3_raw) == BLOB_M3_RAW and file_blob(a.m4_design) == BLOB_M4_DESIGN and file_blob(a.g10_counterfactuals) == BLOB_G10_CF
       and file_blob(a.m6_design) == BLOB_M6_DESIGN and file_blob(a.m6_raw) == BLOB_M6_RAW
       and file_blob(a.m7_design) == BLOB_M7_DESIGN and file_blob(a.m7_raw) == BLOB_M7_RAW
       and file_blob(a.m8_design) == BLOB_M8_DESIGN and file_blob(a.m8_raw) == BLOB_M8_RAW
       and file_blob(a.m9_design) == BLOB_M9_DESIGN and file_blob(a.m9_raw) == BLOB_M9_RAW
       and file_blob(a.m10_design) == BLOB_M10_DESIGN and file_blob(a.m10_raw) == BLOB_M10_RAW
       and file_blob(a.m11_design) == BLOB_M11_DESIGN and file_blob(a.m11_raw) == BLOB_M11_RAW
       and file_blob(a.m12_design) == BLOB_M12_DESIGN and file_blob(a.m12_raw) == BLOB_M12_RAW
       and file_blob(a.m13_design) == BLOB_M13_DESIGN and file_blob(a.m13_raw) == BLOB_M13_RAW
       and file_blob(a.m14_design) == BLOB_M14_DESIGN and file_blob(a.m14_raw) == BLOB_M14_RAW
       and file_blob(a.m15_design) == BLOB_M15_DESIGN and file_blob(a.m15_raw) == BLOB_M15_RAW, "pins")
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
    m8 = json.loads(a.m8_design.read_text("utf8"))
    m9 = json.loads(a.m9_design.read_text("utf8"))
    m10 = json.loads(a.m10_design.read_text("utf8"))
    m11 = json.loads(a.m11_design.read_text("utf8"))
    m12 = json.loads(a.m12_design.read_text("utf8"))
    m13 = json.loads(a.m13_design.read_text("utf8"))
    m14 = json.loads(a.m14_design.read_text("utf8"))
    m15 = json.loads(a.m15_design.read_text("utf8"))
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    m3raw = [json.loads(x) for x in a.m3_raw.read_text("utf8").splitlines() if x.strip()]
    m6raw = [json.loads(x) for x in a.m6_raw.read_text("utf8").splitlines() if x.strip()]
    m7raw = [json.loads(x) for x in a.m7_raw.read_text("utf8").splitlines() if x.strip()]
    m8raw = [json.loads(x) for x in a.m8_raw.read_text("utf8").splitlines() if x.strip()]
    m9raw = [json.loads(x) for x in a.m9_raw.read_text("utf8").splitlines() if x.strip()]
    m10raw = [json.loads(x) for x in a.m10_raw.read_text("utf8").splitlines() if x.strip()]
    m11raw = [json.loads(x) for x in a.m11_raw.read_text("utf8").splitlines() if x.strip()]
    m12raw = [json.loads(x) for x in a.m12_raw.read_text("utf8").splitlines() if x.strip()]
    m13raw = [json.loads(x) for x in a.m13_raw.read_text("utf8").splitlines() if x.strip()]
    m14raw = [json.loads(x) for x in a.m14_raw.read_text("utf8").splitlines() if x.strip()]
    m15raw = [json.loads(x) for x in a.m15_raw.read_text("utf8").splitlines() if x.strip()]
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
    m8_rows = {(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"]): x for x in m8raw if x["patch"]}
    ck(len(m8_rows) == 15 * 208 and m8["selection"] == m3["selection"] and m8["pools"] == m6["pools"], "M8 rows")
    m9_rows = {(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"]): x for x in m9raw if x["patch"]}
    ck(len(m9_rows) == 23 * 208 and m9["selection"] == m3["selection"] and m9["pools"] == m6["pools"], "M9 rows")
    m10_rows = {(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"]): x for x in m10raw if x["patch"]}
    ck(len(m10_rows) == 25 * 208 and m10["selection"] == m3["selection"] and m10["pools"] == m6["pools"], "M10 rows")
    m10_seeds = collections.defaultdict(set)
    for (_a, d_, h_, sk_), x in m10_rows.items():
        if (x["patch"].get("contrast_proj") or {}).get("basis") == "random":
            m10_seeds[(d_, h_, sk_)].add(x["patch"]["contrast_proj"]["seed"])
    ck(len(m10_seeds) == 208 and all(len(v) == 5 for v in m10_seeds.values()), "M10 random frames")
    m11_rows = {(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"]): x for x in m11raw if x["patch"]}
    ck(len(m11_rows) == 25 * 208 and m11["selection"] == m3["selection"] and m11["pools"] == m6["pools"], "M11 rows")
    m12_rows = {(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"]): x for x in m12raw if x["patch"]}
    ck(len(m12_rows) == 37 * 208 and m12["selection"] == m3["selection"] and m12["pools"] == m6["pools"], "M12 rows")
    m13_rows = {(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"]): x for x in m13raw if x["patch"]}
    ck(len(m13_rows) == 34 * 208 and m13["selection"] == m3["selection"] and m13["pools"] == m6["pools"], "M13 rows")
    m14_rows = {(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"]): x for x in m14raw if x["patch"]}
    ck(len(m14_rows) == 33 * 208 + 4 * 12 and m14["selection"] == m3["selection"] and m14["pools"] == m6["pools"],
       "M14 rows")
    m15_rows = {(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"]): x for x in m15raw if x["patch"]}
    ck(len(m15_rows) == 26 * 208 + 4 * 12 and m15["selection"] == m3["selection"] and m15["pools"] == m6["pools"],
       "M15 rows")
    sub_cells = set()
    for hp in RESP:   # the subset cells of the M14 replays (the M14 rule): each responsive host's first 2 cells in donor order
        h_ = [h for h, _ in hosts if h.startswith(hp)]
        ck(len(h_) == 1, f"responsive host {hp}")
        sub_cells |= {(d, h_[0]) for d in [d for d, _ in donors if gd[d] != gh[h_[0]]][:2]}
    ck(len(sub_cells) == 6 and sorted([d[:12], h[:12]] for d, h in sub_cells) == m14["subset_cells"]
       == m15["subset_cells"], "6 subset cells = M14's = M15's")

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
        sd = dec[s0:s1]
        ck(len(sd) == SPAN_W and all(sd[i_] == t_ for i_, t_ in FIELD_MARKS.items()),
           f"span field layout at {s[:8]}:{arm}")
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
        ck(m8["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M8 key classes differ at {s[:8]}:{arm}")
        ck(m9["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M9 key classes differ at {s[:8]}:{arm}")
        ck(m10["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M10 key classes differ at {s[:8]}:{arm}")
        ck(m11["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M11 key classes differ at {s[:8]}:{arm}")
        ck(m12["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M12 key classes differ at {s[:8]}:{arm}")
        ck(m13["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M13 key classes differ at {s[:8]}:{arm}")
        ck(m14["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M14 key classes differ at {s[:8]}:{arm}")
        ck(m15["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M15 key classes differ at {s[:8]}:{arm}")
        return {"span": [s0, s1], "classes": cls, "state_len": len(ids), "token_ids_sha256": tid,
                "partner_token_ids": ids[partner[0][0]:partner[0][1]], "partner_message": pmsg, "author": A}

    key_classes = {}
    rows = []
    built = {}

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
                if ex.get("sub") and (d, h) not in sub_cells:
                    continue
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
                    ck(patch["span"][1] - patch["span"][0] == SPAN_W, "span width")
                    same_pairs = [[f"{a_}:{t[:12]}", f"{a_}:{h[:12]}"] for t in pool_d for a_ in SOURCES]
                    if op == "cshift":    # common pooled shift, -+ s/2 of the pooled contrast
                        patch["base"] = "target"
                        patch["pool_new"] = [f"new:{t[:12]}" for t in pool_d]
                        patch["pool_round"] = [f"ROUND:{t[:12]}" for t in pool_d]
                        patch["scale"] = 0.0 if ex["s"] == 0 else (-ex["s"] / 2 if sk == "main" else ex["s"] / 2)
                        ck(ex["t"] == 1.0, "t = 1 in every M16 arm")
                        if "cpos" in ex:
                            patch["contrast_positions"] = ex["cpos"]
                        if "cw" in ex:
                            patch["contrast_pos_weight"] = [[30, ex["cw"]]]
                        if "shpos" in ex:
                            patch["shift_positions"] = ex["shpos"]
                        if "mw" in ex:   # the common shift at 13-28 times w, 1 elsewhere
                            patch["shift_pos_weight"] = [[i_, ex["mw"]] for i_ in MID]
                        if "shscale" in ex:
                            patch["shift_scale"] = ex["shscale"]
                        if "proj" in ex:
                            cpj = {"k": SPLIT_K, "part": ex["proj"], "rescale": "contrast"}
                            m7p = m7_rows[(f"dlr{SPLIT_K}_sm", d, h, "main")]["patch"]
                            ck(m7p["basis_pairs"] == same_pairs and m7p["k"] == SPLIT_K, "M7 dlr16_sm basis")
                            cpj.update(basis="pairs", cap=ALPHA_CAP, basis_pairs=same_pairs)
                            patch["contrast_proj"] = cpj
                        if "rem" in ex:   # c + lam r, r = the part of the 16-dim projection of c orthogonal to c
                            m7p = m7_rows[(f"dlr{SPLIT_K}_sm", d, h, "main")]["patch"]
                            ck(m7p["basis_pairs"] == same_pairs and m7p["k"] == SPLIT_K, "M7 dlr16_sm basis")
                            crm = {"k": SPLIT_K, "lam": ex["rem"], "basis_pairs": same_pairs}
                            if "nullseed" in ex:   # one seed per cell and i: the same q at both s, main and round
                                tag_ = f"A461_{ex['ntag']}_RNULL|{SPLIT_K}|{d}|{h}|{ex['nullseed']}"
                                crm["null_seed"] = int(hashlib.sha256(tag_.encode()).hexdigest()[:8], 16)
                            patch["contrast_rem"] = crm
                    if arm in M15_REPLAY:   # M14 / M15 replays: identical patch fields to the M15 rows
                        m15p = m15_rows[(arm, d, h, sk)]["patch"]
                        ck(all(m15p.get(k_) == v_ for k_, v_ in patch.items())
                           and all(patch.get(k_) == v_ for k_, v_ in m15p.items() if v_ is not None), f"M15 {arm} wiring")
                    built[(arm, d, h, sk)] = patch
                    add(phase="patch", condition=f"patch_m16_{arm}_{sk}", direction="repair", scope="all",
                        source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                        target_arm="new", patch=patch,
                        bitwise_vs_m3=m3_all[(d, h, sk)] if op == "full" else None,
                        bitwise_vs_m6=m6_md[(d, h, sk)]["forward_index"] if op == "pool" else None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * 14 * 2 + 6 * 3 * 2 == 2948, "104 x 14 x 2 + 6 x 3 x 2 patches")
    ck(len(ARMS) == 17 and len({r["condition"] for r in rows if r["phase"] == "patch"}) == 34, "34 patch conditions")
    ck(collections.Counter(r["patch"]["arm"] for r in rows if r["phase"] == "patch")
       == {n: (12 if ex.get("sub") else 208) for n, _o, _c, ex in ARMS}, "rows per arm")
    # mw0_s0375 = abc_s0375 with the 0/1 shift mask written as weights (same cells, sources, pools, contrast)
    n_mw0 = 0
    for (arm, d, h, sk), p in built.items():
        if arm == "mw0_s0375":
            q = built[("abc_s0375", d, h, sk)]
            ck({k_: v_ for k_, v_ in p.items() if k_ not in ("arm", "shift_pos_weight")}
               == {k_: v_ for k_, v_ in q.items() if k_ not in ("arm", "shift_positions")}
               and sorted(set(range(SPAN_W)) - {i_ for i_, _w in p["shift_pos_weight"]}) == q["shift_positions"]
               and {w_ for _i, w_ in p["shift_pos_weight"]} == {0.0}, "mw0 = abc as weights")
            n_mw0 += 1
    ck(n_mw0 == 12, "12 mw0 rows")
    # the linear predictions from the pinned endpoints: w = 0 = M14 abc_<s>, w = 1 = M15 csc29_<s>
    def ma(qs):
        q = {x["id"]: x for x in qs}
        c, ac = q["conflicting_vote"], q["certificate_action"]
        M = c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]
        L = dict(zip(ac["keys"], ac["logits"]))
        return M, L["reject_conflict"] - max(L["accept"], L["wait"])
    preds, pred_S = {}, {}
    for n, _op, _cl, ex in ARMS:
        if "mw" not in ex or ex.get("sub"):
            continue
        sfx = n[n.index("_s"):]
        w_ = ex["mw"]
        preds[n] = {}
        for (a_, d, h, sk) in built:
            if a_ != n:
                continue
            ck(m14_rows[(f"abc{sfx}", d, h, sk)]["patch"]["scale"] == m15_rows[(f"csc29{sfx}", d, h, sk)]["patch"]["scale"]
               == built[(n, d, h, sk)]["scale"], "endpoint scales")
            v0, v1 = ma(m14_rows[(f"abc{sfx}", d, h, sk)]["questions"]), ma(m15_rows[(f"csc29{sfx}", d, h, sk)]["questions"])
            preds[n][f"{d[:12]}|{h[:12]}|{sk}"] = [(1 - w_) * v0[0] + w_ * v1[0], (1 - w_) * v0[1] + w_ * v1[1]]
        J = lambda v: v[0] > 0 and v[1] > 0
        pred_S[n] = {hp: sum(J(preds[n][f"{d[:12]}|{h[:12]}|main"]) and not J(preds[n][f"{d[:12]}|{h[:12]}|round"])
                             for (a_, d, h, sk) in built if a_ == n and sk == "main" and h.startswith(hp))
                     for hp in RESP}
    ck(len(preds) == 12 and all(len(v) == 208 for v in preds.values()), "208 predictions per dose arm")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m3")) == 208, "208 M3 bitwise anchors")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m6")) == 208, "208 M6 bitwise anchors")
    design = {"schema": "JEV_A461_MECH_M16_MID_WEIGHT_LINEAR_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M16_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader); L11 = Qwen3.5 full attention, "
                       "16 query heads x 256 in 4 KV groups, output gate, o_proj without bias",
              "inputs": {"roster_blob": BLOB_ROSTER, "m1_design_blob": BLOB_M1_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                         "m3_design_blob": BLOB_M3_DESIGN, "m3_raw_blob": BLOB_M3_RAW, "m4_design_blob": BLOB_M4_DESIGN,
                         "m6_design_blob": BLOB_M6_DESIGN, "m6_raw_blob": BLOB_M6_RAW,
                         "m7_design_blob": BLOB_M7_DESIGN, "m7_raw_blob": BLOB_M7_RAW,
                         "m8_design_blob": BLOB_M8_DESIGN, "m8_raw_blob": BLOB_M8_RAW,
                         "m9_design_blob": BLOB_M9_DESIGN, "m9_raw_blob": BLOB_M9_RAW,
                         "m10_design_blob": BLOB_M10_DESIGN, "m10_raw_blob": BLOB_M10_RAW,
                         "m11_design_blob": BLOB_M11_DESIGN, "m11_raw_blob": BLOB_M11_RAW,
                         "m12_design_blob": BLOB_M12_DESIGN, "m12_raw_blob": BLOB_M12_RAW,
                         "m13_design_blob": BLOB_M13_DESIGN, "m13_raw_blob": BLOB_M13_RAW,
                         "m14_design_blob": BLOB_M14_DESIGN, "m14_raw_blob": BLOB_M14_RAW,
                         "m15_design_blob": BLOB_M15_DESIGN, "m15_raw_blob": BLOB_M15_RAW,
                         "g10_counterfactuals_blob": BLOB_G10_CF, "g5v2_questions_blob": g5_full,
                         "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV, "base_classes": list(BASE),
              "arms": [[n, op, cl, ex] for n, op, cl, ex in ARMS], "c_positions": C_POS, "fields": FIELDS,
              "field_marks": FIELD_MARKS, "ab_positions": AB, "mid_positions": MID, "span_width": SPAN_W,
              "alpha_cap": ALPHA_CAP, "m15_replay": list(M15_REPLAY), "subset": list(SUBSET),
              "responsive_hosts": list(RESP), "subset_cells": sorted([d[:12], h[:12]] for d, h in sub_cells),
              "sizes": [x for x, _ in Q1_S], "weights": [w_ for w_, _t in W], "bulk": BULK,
              "linear_predictions": preds, "predicted_S_by_host": pred_S,
              "pools": pools,
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "key_classes": key_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M16 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m16_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m16_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m16_design.json", "m16_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 2948, "predicted_S_by_host": pred_S,
                      "class_sizes": {t: {k: sum(hi - lo for lo, hi in v) for k, v in c["classes"].items()}
                                      for t, c in list(key_classes.items())[:3]},
                      "manifest_blob": file_blob(out / "m16_manifest.jsonl"),
                      "design_blob": file_blob(out / "m16_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
