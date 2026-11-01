#!/usr/bin/env python3
"""A461-MECH-M13 R1: CPU freeze of shift-location arms at the author and block lines and of a tilt of the pooled
round contrast relative to the 16-dim common subspace, with random-tilt nulls (zero model forwards; tokenizer only).

M12 (b72a451): weak P30_OPPOSES; SHIFT_FIELDS_NEEDED:BLOCK with AUTH on the edge (per host 4bcbaf15 needs AUTH and
BLOCK); SHIFT_FIELDS_SUFFICE:NONE; SUBSPACE_BELOW_COSINE (264c458d: cpar16_sm 1 vs its cosine nulls 5-10). M13 asks:
  L  shift at positions 0-12 (AUTH + BLOCK) plus 29-30, with c and with c_29 only, at s = 1 and 1/2; the complement
     13-30; location controls KIND+RECV and RECV+RKEY (each plus 29-30)
  T  r = the part of P c (P = projector on the 16-dim common subspace) orthogonal to c, per row and position;
     contrast c + lam r with lam in -1, +1, +2 at s = 1, 1/2, 3/8 (r is orthogonal to c, so c's component along c
     is unchanged)
  N  nulls c + q, q orthogonal to c with ||q|| = ||r|| per row and position, random direction, 5 seeds per cell
     shared across s = 1/2 and 3/8 and by main and round
Anchors: full (M3, bitwise, 51), meanD_host (M6, bitwise, 39), cs1 / cs_s05 / cs_s025 / cpar16_sm / sh_fBLOCK /
sh_xAUTH / sh_xBLOCK (M12 rows, same patch fields, bitwise; S 39 / 38 / 13 / 27 / 18 / 26 / 20).
44 captures + 104 x 34 x 2 = 7116 calls in 55 x 128 + 76.
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
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
N_HEADS, N_KV = 16, 4
SOURCES = ("new", "ROUND")
BASE = ("PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT")
BULK = ["OTHER_ITEMS", "CONTEXT"]
SPAN_W = 31
C_POS = [29, 30]      # the span positions where c != 0 in all M9-M11 captures (ROUND changes the token at 29)
SPLIT_K = 16
NULL_SEEDS = list(range(1, 6))
ALPHA_CAP = 10.0
# the appended item's fields (span-relative positions; the decoded markers are checked for every capture)
FIELDS = {"AUTH": list(range(0, 7)), "BLOCK": list(range(7, 13)), "KIND": list(range(13, 18)),
          "RECV": list(range(18, 25)), "RKEY": list(range(25, 29))}
FIELD_MARKS = {2: " author", 6: "\n", 8: " block", 12: "\n", 14: " kind", 17: "\n", 19: " received", 24: "\n",
               26: " round", 30: "\n"}
AB = FIELDS["AUTH"] + FIELDS["BLOCK"]      # 0-12: the author and block lines of the appended item
M12_REPLAY = ("full", "meanD_host", "cs1", "cs_s05", "cs_s025", "cpar16_sm", "sh_fBLOCK", "sh_xAUTH", "sh_xBLOCK")
CS = {"t": 1.0, "s": 1.0}
S38 = 0.375
TILT_S = ((1.0, ""), (0.5, "_s05"), (S38, "_s0375"))
NULL_S = ((0.5, "_s05"), (S38, "_s0375"))

# (name, op, classes, extra)
ARMS = ([("full", "full", [], {}),
         ("meanD_host", "pool", BULK, {"base": "target", "pool": "donors"}),
         ("cs1", "cshift", BULK, dict(CS)),
         ("cs_s05", "cshift", BULK, dict(CS, s=0.5)),
         ("cs_s025", "cshift", BULK, dict(CS, s=0.25)),
         ("cpar16_sm", "cshift", BULK, dict(CS, proj="par", seed=0)),
         ("sh_fBLOCK", "cshift", BULK, dict(CS, shpos=sorted(FIELDS["BLOCK"] + C_POS))),
         ("sh_xAUTH", "cshift", BULK, dict(CS, shpos=[i for i in range(SPAN_W) if i not in FIELDS["AUTH"]])),
         ("sh_xBLOCK", "cshift", BULK, dict(CS, shpos=[i for i in range(SPAN_W) if i not in FIELDS["BLOCK"]]))]
        + [("sh_fAB", "cshift", BULK, dict(CS, shpos=AB + C_POS)),
           ("sh_fAB_c29", "cshift", BULK, dict(CS, shpos=AB + C_POS, cw=0.0)),
           ("sh_fAB_s05", "cshift", BULK, dict(CS, s=0.5, shpos=AB + C_POS)),
           ("sh_xAB", "cshift", BULK, dict(CS, shpos=[i for i in range(SPAN_W) if i not in AB])),
           ("sh_fKR", "cshift", BULK, dict(CS, shpos=FIELDS["KIND"] + FIELDS["RECV"] + C_POS)),
           ("sh_fRR", "cshift", BULK, dict(CS, shpos=FIELDS["RECV"] + FIELDS["RKEY"] + C_POS)),
           ("cs_s0375", "cshift", BULK, dict(CS, s=S38))]
        + [(f"rem_{tg}{sfx}", "cshift", BULK, dict(CS, s=s_, rem=lam)) for s_, sfx in TILT_S
           for tg, lam in (("p1", 1.0), ("m1", -1.0), ("p2", 2.0)) if not (s_ == S38 and lam == 2.0)]
        + [(f"rnull{sfx}_{i}", "cshift", BULK, dict(CS, s=s_, rem=1.0, nullseed=i)) for s_, sfx in NULL_S
           for i in NULL_SEEDS])
PLAN = [128] * 55 + [76]

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
                        "checked in the run); cs1 / cs_s05 / cs_s025 / cpar16_sm / sh_fBLOCK / sh_xAUTH / sh_xBLOCK = "
                        "the M12 arms (same patch fields): their 7 x 208 rows equal M12's bitwise and S = 39 / 38 / 13 "
                        "/ 27 / 18 / 26 / 20; otherwise every verdict is INCONSISTENT_WITH_M3_M6_M12 and no claim",
    "C": "C(arm) = median over cells of dM_main - dM_round",
    "responsive_host": "a host where S(cs1) on its cells exceeds half its cells",
    "ab_verdicts": "AB = span positions 0-12. SHIFT_AB_SUFFICES iff SUF(sh_fAB) else SHIFT_AB_INSUFFICIENT; "
                   "SHIFT_AB_C29_SUFFICES iff SUF(sh_fAB_c29) else SHIFT_AB_C29_INSUFFICIENT; SHIFT_AB_S05_SUFFICES "
                   "iff SUF(sh_fAB_s05) else SHIFT_AB_S05_INSUFFICIENT; SHIFT_AB_NEEDED iff not SUF(sh_xAB) else "
                   "SHIFT_AB_NOT_NEEDED; AB_LOCATION_SPECIFIC iff SUF(sh_fAB), neither sh_fKR nor sh_fRR is SUF and "
                   "S(sh_fAB) > max(S(sh_fKR), S(sh_fRR)); AB_LOCATION_NOT_SPECIFIC iff SUF(sh_fAB) and sh_fKR or "
                   "sh_fRR is SUF; else AB_LOCATION_UNRESOLVED. AB_BY_HOST:<host8>=<S(sh_fAB)>/<S(cs1)>,... over the "
                   "responsive hosts",
    "tilt_verdicts": "r = P c - (P c . c^) c^ per question row and span position (P = projector on the first 16 "
                     "right singular vectors of the cell's same-arm pairs basis, as cpar16_sm); arm rem_<lam> = c + "
                     "lam r, main -s/2, round +s/2. Per s in 1, 1/2, 3/8 with S_m = S(rem_m1..), S_0 = S(cs1 / cs_s05 / "
                     "cs_s0375), S_p = S(rem_p1..): TILT_OPPOSES iff S_m >= S_0 >= S_p and S_m > S_p; TILT_SUPPORTS "
                     "iff S_m <= S_0 <= S_p and S_m < S_p; TILT_NO_EFFECT iff S_m = S_0 = S_p; TILT_MIXED otherwise. "
                     "Pooled: REM_OPPOSES iff some s is TILT_OPPOSES and every s is TILT_OPPOSES or TILT_NO_EFFECT; "
                     "REM_SUPPORTS likewise; REM_NO_EFFECT iff all TILT_NO_EFFECT; else REM_MIXED. S and C of rem_p2 "
                     "and rem_p2_s05 are reported",
    "tilt_null_verdicts": "rnull_<s>_<i> = c + q with q orthogonal to c, ||q|| = ||r|| per row and position, its "
                          "direction drawn at random (seed per cell and i, the same at both s and for main and round). "
                          "Per responsive host and s in 1/2, 3/8, with the host S of the 5 nulls N: add = the host S of "
                          "rem_p1 at s: HARM_BEYOND_NULL iff add < min N, LESS_HARM_THAN_NULL iff add > max N, else AT; "
                          "remove = the host S of rem_m1 at s: REMOVAL_BEYOND_NULL iff remove > max N, "
                          "REMOVAL_BELOW_NULL iff remove < min N, else AT. REM_NULL_BY_HOST:<host8>=s05:<add>/<remove>,"
                          "s0375:<add>/<remove>,...; pooled: REM_DIRECTION_SPECIFIC iff some HARM_BEYOND_NULL or "
                          "REMOVAL_BEYOND_NULL and no LESS_HARM_THAN_NULL or REMOVAL_BELOW_NULL; "
                          "REM_DIRECTION_NOT_SPECIFIC iff all AT; REM_DIRECTION_REVERSED iff some LESS_HARM_THAN_NULL or "
                          "REMOVAL_BELOW_NULL and no BEYOND; else REM_DIRECTION_MIXED",
    "size_gate": "cpar16_sm has ||c|| per row and position within 1e-3 relative where not capped (fail-closed, as "
                 "M9-M12); every tilt arm and null keeps c's component along c and has tilt norm |lam| ||r|| within "
                 "1e-6 relative to ||c|| (fail-closed); sh_fAB_c29 sets c_30 to 0 exactly",
    "interpretation_fixed_in_advance": "SHIFT_AB_SUFFICES with AB_LOCATION_SPECIFIC: the common shift's role sits at "
        "the author and block lines of the appended item; with SHIFT_AB_C29_SUFFICES the repair needs only that shift "
        "and c at the round value. REM_OPPOSES with REM_DIRECTION_SPECIFIC: tilting c towards the common subspace "
        "works against the round-specific repair beyond a random tilt of the same size, which locates M12's "
        "SUBSPACE_BELOW_COSINE in the in-subspace remainder r; REM_OPPOSES with REM_DIRECTION_NOT_SPECIFIC: any "
        "orthogonal push of that size does the same, so r is not special. All M13 arms except full are pooled-donor "
        "arms (effectively 8 host replicates, 3 responding in M9-M12); per-host S is the honest unit; a host at its "
        "ceiling or floor for an arm and all its nulls reads AT",
    "always_reported": "S, SPEC, J_main, J_round, median dM and C per arm; per host; leave-one-donor-group-out of "
                       "every verdict; energy shares, remainder shares, tilt errors; the S of each null, pooled and per "
                       "host; change norm of every arm relative to full",
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
       and file_blob(a.m12_design) == BLOB_M12_DESIGN and file_blob(a.m12_raw) == BLOB_M12_RAW, "pins")
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
                    ck(patch["span"][1] - patch["span"][0] == SPAN_W, "span width")
                    same_pairs = [[f"{a_}:{t[:12]}", f"{a_}:{h[:12]}"] for t in pool_d for a_ in SOURCES]
                    if op == "cshift":    # common pooled shift, -+ s/2 of the pooled contrast
                        patch["base"] = "target"
                        patch["pool_new"] = [f"new:{t[:12]}" for t in pool_d]
                        patch["pool_round"] = [f"ROUND:{t[:12]}" for t in pool_d]
                        patch["scale"] = 0.0 if ex["s"] == 0 else (-ex["s"] / 2 if sk == "main" else ex["s"] / 2)
                        ck(ex["t"] == 1.0, "t = 1 in every M13 arm")
                        if "cpos" in ex:
                            patch["contrast_positions"] = ex["cpos"]
                        if "cw" in ex:
                            patch["contrast_pos_weight"] = [[30, ex["cw"]]]
                        if "shpos" in ex:
                            patch["shift_positions"] = ex["shpos"]
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
                                tag_ = f"A461_M13_RNULL|{SPLIT_K}|{d}|{h}|{ex['nullseed']}"
                                crm["null_seed"] = int(hashlib.sha256(tag_.encode()).hexdigest()[:8], 16)
                            patch["contrast_rem"] = crm
                    if arm in M12_REPLAY:   # M12 replays: identical patch fields
                        m12p = m12_rows[(arm, d, h, sk)]["patch"]
                        ck(all(m12p.get(k_) == v_ for k_, v_ in patch.items())
                           and all(patch.get(k_) == v_ for k_, v_ in m12p.items() if v_ is not None), f"M12 {arm} wiring")
                    add(phase="patch", condition=f"patch_m13_{arm}_{sk}", direction="repair", scope="all",
                        source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                        target_arm="new", patch=patch,
                        bitwise_vs_m3=m3_all[(d, h, sk)] if op == "full" else None,
                        bitwise_vs_m6=m6_md[(d, h, sk)]["forward_index"] if op == "pool" else None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * len(ARMS) * 2 == 7072, "104 x 34 x 2 patches")
    ck(len({r["condition"] for r in rows if r["phase"] == "patch"}) == 68, "68 patch conditions")
    seeds = collections.defaultdict(set)
    for r in rows:
        if r["phase"] == "patch" and "null_seed" in (r["patch"].get("contrast_rem") or {}):
            seeds[(r["donor"], r["host"])].add((r["patch"]["arm"].rsplit("_", 1)[1], r["patch"]["contrast_rem"]["null_seed"]))
    ck(len(seeds) == 104 and all(len(v) == len(NULL_SEEDS) and len({s_ for _i, s_ in v}) == len(NULL_SEEDS)
                                 for v in seeds.values()),
       "5 distinct null seeds per cell, the same at both s and for the main and round patch")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m3")) == 208, "208 M3 bitwise anchors")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m6")) == 208, "208 M6 bitwise anchors")
    design = {"schema": "JEV_A461_MECH_M13_AB_SHIFT_TILT_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M13_FORWARD",
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
                         "g10_counterfactuals_blob": BLOB_G10_CF, "g5v2_questions_blob": g5_full,
                         "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV, "base_classes": list(BASE),
              "arms": [[n, op, cl, ex] for n, op, cl, ex in ARMS], "c_positions": C_POS, "fields": FIELDS,
              "field_marks": FIELD_MARKS, "ab_positions": AB, "span_width": SPAN_W, "null_seeds": NULL_SEEDS, "split_k": SPLIT_K,
              "alpha_cap": ALPHA_CAP, "m12_replay": list(M12_REPLAY), "bulk": BULK,
              "pools": pools,
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "key_classes": key_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M13 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m13_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m13_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m13_design.json", "m13_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 7072,
                      "class_sizes": {t: {k: sum(hi - lo for lo, hi in v) for k, v in c["classes"].items()}
                                      for t, c in list(key_classes.items())[:3]},
                      "manifest_blob": file_blob(out / "m13_manifest.jsonl"),
                      "design_blob": file_blob(out / "m13_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
