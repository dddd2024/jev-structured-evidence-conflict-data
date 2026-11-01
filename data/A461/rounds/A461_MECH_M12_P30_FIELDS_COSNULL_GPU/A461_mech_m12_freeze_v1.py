#!/usr/bin/env python3
"""A461-MECH-M12 R1: CPU freeze of a position-30 weight ladder, field-wise shift-location arms and a cosine-matched
null for the subspace split, for the pooled round contrast on the common BULK shift of the L11 write of kev-4B (zero
model forwards; tokenizer only).

M11 (76e6537): AMPLITUDE_ONLY_EXCLUDED (c at 30 at c_29's norm S 1; larger c_30 suppresses the main flip, J_main
30 -> 1 at s 4); POS29_SMIN:0.5 with per-host thresholds; SHIFT_NEEDS_CONTEXT_POSITIONS (the shift at 29-30 alone flips
nothing at any size); SPLIT_BY_HOST BOTH x 3, with 264c458d substantively OUTSIDE (cperp 13, cpar 1, null 0) and
SPLIT_NULL10 failing (59 of 69 null repairs on 1fb5651c). M12 asks:
  W  is c at 30 a counter-signal? c_29 + w c_30 with w = -1, 0, +1, +2 at s = 1/4, 1/2, 1 (w = 0 and the w = +1 s = 1
     arm are M11 replays)
  F  which fields of the appended item must carry the common shift? The 31-token span is the item
     " - author / block / kind / received / round" (fields 0-6, 7-12, 13-17, 18-24, round key 25-28, round value 29,
     newline 30; checked per capture). Shift at one field + 29-30 (sh_f*) and everywhere except one field (sh_x*)
  N  is the part of c inside / outside the 16-dim common subspace special beyond its cosine with c? Per row and
     position a null with the same norm and the same cosine to c as cpar16_sm / cperp16_sm, its remainder orthogonal
     to c drawn at random (5 seeds per part)
Anchors: full (M3, bitwise, 51), meanD_host (M6, bitwise, 39), cs1 / cpos29 / cpos29_s05 / cpos29_s025 / cpar16_sm /
cperp16_sm / sh2930 / sh0_28 (M11 rows, same patch fields, bitwise; S 39 / 39 / 38 / 13 / 27 / 39 / 0 / 13).
44 captures + 104 x 37 x 2 = 7740 calls in 60 x 128 + 60.
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
M11_REPLAY = ("full", "meanD_host", "cs1", "cpos29", "cpos29_s05", "cpos29_s025", "cpar16_sm", "cperp16_sm", "sh2930",
              "sh0_28")
CS = {"t": 1.0, "s": 1.0}

# (name, op, classes, extra)
ARMS = ([("full", "full", [], {}),
         ("meanD_host", "pool", BULK, {"base": "target", "pool": "donors"}),
         ("cs1", "cshift", BULK, dict(CS)),
         ("cpos29", "cshift", BULK, dict(CS, cpos=[29])),
         ("cpos29_s05", "cshift", BULK, dict(CS, s=0.5, cpos=[29])),
         ("cpos29_s025", "cshift", BULK, dict(CS, s=0.25, cpos=[29]))]
        + [(f"c{part}{SPLIT_K}_sm", "cshift", BULK, dict(CS, proj=part, seed=0)) for part in ("par", "perp")]
        + [("sh2930", "cshift", BULK, dict(CS, shpos=C_POS)), ("sh0_28", "cshift", BULK, dict(CS, shpos=list(range(29))))]
        + [("cw30_m1", "cshift", BULK, dict(CS, cw=-1.0)), ("cw30_p2", "cshift", BULK, dict(CS, cw=2.0)),
           ("cs_s05", "cshift", BULK, dict(CS, s=0.5)), ("cw30_m1_s05", "cshift", BULK, dict(CS, s=0.5, cw=-1.0)),
           ("cw30_p2_s05", "cshift", BULK, dict(CS, s=0.5, cw=2.0)),
           ("cs_s025", "cshift", BULK, dict(CS, s=0.25)), ("cw30_m1_s025", "cshift", BULK, dict(CS, s=0.25, cw=-1.0))]
        + [(f"sh_f{f}", "cshift", BULK, dict(CS, shpos=sorted(v + C_POS))) for f, v in FIELDS.items()]
        + [(f"sh_x{f}", "cshift", BULK, dict(CS, shpos=[i for i in range(SPAN_W) if i not in v])) for f, v in FIELDS.items()]
        + [(f"ccos_{part}_s{i}", "cshift", BULK, dict(CS, proj=part, seed=0, nullseed=i))
           for part in ("par", "perp") for i in NULL_SEEDS])
PLAN = [128] * 60 + [60]

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
                        "checked in the run); cs1 / cpos29 / cpos29_s05 / cpos29_s025 / cpar16_sm / cperp16_sm / sh2930 / "
                        "sh0_28 = the M11 arms (same patch fields): their 8 x 208 rows equal M11's bitwise and S = 39 / "
                        "39 / 38 / 13 / 27 / 39 / 0 / 13; otherwise every verdict is INCONSISTENT_WITH_M3_M6_M11 and no "
                        "claim",
    "C": "C(arm) = median over cells of dM_main - dM_round",
    "p30_weight_verdict": "the contrast c_29 + w c_30 (c at the other span positions is 0), main -s/2, round +s/2. At "
                          "s = 1/4 (the most sensitive dose: S 13 at w = 0 in M11) with S_m = S(cw30_m1_s025), S_0 = "
                          "S(cpos29_s025), S_p = S(cs_s025): P30_OPPOSES iff S_m > S_0 >= S_p and S_m > S_p; "
                          "P30_SUPPORTS iff S_p > S_0 >= S_m and S_p > S_m; P30_NO_EFFECT iff S_m = S_0 = S_p; "
                          "P30_MIXED otherwise",
    "p30_weight_dose": "WSMIN(w) = the smallest s in 1/4, 1/2, 1 with SUF for w = -1 (cw30_m1_s025, cw30_m1_s05, "
                       "cw30_m1), w = 0 (cpos29_s025, cpos29_s05, cpos29), w = +1 (cs_s025, cs_s05, cs1), and in 1/2, 1 for "
                       "w = +2 (cw30_p2_s05, cw30_p2); NONE if no s. FLIP_LOWERS_THRESHOLD iff WSMIN(-1) < WSMIN(0). "
                       "C, frac and J per (w, s) are reported",
    "shift_fields_verdict": "fields AUTH 0-6, BLOCK 7-12, KIND 13-17, RECV 18-24, RKEY 25-28 (span-relative); the common "
                            "shift (t = 1) at a field plus 29-30 (sh_f<F>) or at every span position except the field "
                            "(sh_x<F>), with the full c (s = 1). NEEDED(F) iff not SUF(sh_x<F>); SUFFICES(F) iff "
                            "SUF(sh_f<F>). Verdicts SHIFT_FIELDS_NEEDED:<F,...|NONE> and SHIFT_FIELDS_SUFFICE:<F,...|NONE> "
                            "(cs1 is the all-fields arm, SUF in M9-M11); per-host S of every field arm is reported",
    "cos_null_verdict": "cosine-matched null: per question row and span position, ccos_<part>_s<i> has the norm and the "
                        "cosine to c of the c<part>16_sm patch (same pairs basis, rescale and cap) and a remainder "
                        "orthogonal to c drawn at random (seeded per cell and seed, the same vector for the main and "
                        "round patch). Responsive host = a host where S(cs1) on its cells exceeds half its cells. Per "
                        "responsive host and part: BEYOND iff S(c<part>16_sm) > the maximum host S over the 5 nulls; "
                        "BELOW iff < the minimum; AT otherwise. COS_SPLIT_BY_HOST:<host8>=par:<v>/perp:<v>,...; pooled: "
                        "SUBSPACE_EXPLAINED_BY_COSINE iff every responsive host is AT for both parts, else "
                        "SUBSPACE_BEYOND_COSINE iff some part is BEYOND on some host and none is BELOW, else "
                        "SUBSPACE_BELOW_COSINE iff some part is BELOW and none BEYOND, else SUBSPACE_COSINE_MIXED",
    "size_gate": "the c<part>16_sm parts have ||c|| per row and position within 1e-3 relative where not capped "
                 "(fail-closed, as M9-M11); the cosine nulls have the part's norm and cosine to c within 1e-6 (fail-"
                 "closed); the weighted contrast keeps c_29 unchanged and scales c_30 exactly",
    "interpretation_fixed_in_advance": "P30_OPPOSES: c at the newline after the round value works against the round-"
        "specific repair that c at the round value drives (as cpos30_s4 suggested in M11), so the pooled contrast is "
        "c_29 minus a counter-signal; P30_SUPPORTS: c_30 helps once c_29 is present, even though it does nothing alone. "
        "SHIFT_FIELDS_NEEDED lists the fields whose shift cannot be dropped; SHIFT_FIELDS_SUFFICE the fields whose "
        "shift alone (with 29-30) suffices; NONE / NONE means the shift's role is spread over fields, each "
        "dispensable and none sufficient. SUBSPACE_EXPLAINED_BY_COSINE: the parts of c inside and outside the 16-dim "
        "common subspace act as any direction with the same cosine to c would, so the M9-M11 split reading reduces to "
        "'closer to c works better' (cperp keeps about 67 % of c's energy, cpar 33 %). BEYOND: the subspace part acts "
        "beyond its cosine; BELOW: it acts less than a random direction of the same cosine. All M12 arms except full "
        "are pooled-donor arms (effectively 8 host replicates, 3 responding in M9-M11); per-host S is the honest unit",
    "always_reported": "S, SPEC, J_main, J_round, median dM and C per arm; per host; leave-one-donor-group-out of "
                       "every verdict; energy shares, factors, capped shares, cosines; the S of each null, pooled and "
                       "per host; change norm of every arm relative to full",
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
       and file_blob(a.m11_design) == BLOB_M11_DESIGN and file_blob(a.m11_raw) == BLOB_M11_RAW, "pins")
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
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    m3raw = [json.loads(x) for x in a.m3_raw.read_text("utf8").splitlines() if x.strip()]
    m6raw = [json.loads(x) for x in a.m6_raw.read_text("utf8").splitlines() if x.strip()]
    m7raw = [json.loads(x) for x in a.m7_raw.read_text("utf8").splitlines() if x.strip()]
    m8raw = [json.loads(x) for x in a.m8_raw.read_text("utf8").splitlines() if x.strip()]
    m9raw = [json.loads(x) for x in a.m9_raw.read_text("utf8").splitlines() if x.strip()]
    m10raw = [json.loads(x) for x in a.m10_raw.read_text("utf8").splitlines() if x.strip()]
    m11raw = [json.loads(x) for x in a.m11_raw.read_text("utf8").splitlines() if x.strip()]
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
                        ck(ex["t"] == 1.0, "t = 1 in every M12 arm")
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
                            if "nullseed" in ex:   # one seed per cell and null: the same vector for main and round
                                tag_ = f"A461_M12_CCOS|{ex['proj']}|{SPLIT_K}|{d}|{h}|{ex['nullseed']}"
                                cpj["null_seed"] = int(hashlib.sha256(tag_.encode()).hexdigest()[:8], 16)
                            patch["contrast_proj"] = cpj
                    if arm in M11_REPLAY:   # M11 replays: identical patch fields
                        m11p = m11_rows[(arm, d, h, sk)]["patch"]
                        ck(all(m11p.get(k_) == v_ for k_, v_ in patch.items())
                           and all(patch.get(k_) == v_ for k_, v_ in m11p.items() if v_ is not None), f"M11 {arm} wiring")
                    add(phase="patch", condition=f"patch_m12_{arm}_{sk}", direction="repair", scope="all",
                        source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                        target_arm="new", patch=patch,
                        bitwise_vs_m3=m3_all[(d, h, sk)] if op == "full" else None,
                        bitwise_vs_m6=m6_md[(d, h, sk)]["forward_index"] if op == "pool" else None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * len(ARMS) * 2 == 7696, "104 x 37 x 2 patches")
    ck(len({r["condition"] for r in rows if r["phase"] == "patch"}) == 74, "74 patch conditions")
    seeds = collections.defaultdict(set)
    for r in rows:
        if r["phase"] == "patch" and "null_seed" in (r["patch"].get("contrast_proj") or {}):
            seeds[(r["donor"], r["host"], r["patch"]["contrast_proj"]["part"])].add(
                (r["patch"]["arm"], r["patch"]["contrast_proj"]["null_seed"]))
    ck(len(seeds) == 208 and all(len(v) == len(NULL_SEEDS) and len({s_ for _a, s_ in v}) == len(NULL_SEEDS)
                                 for v in seeds.values()),
       "5 distinct null seeds per cell and part, the same for the main and round patch")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m3")) == 208, "208 M3 bitwise anchors")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m6")) == 208, "208 M6 bitwise anchors")
    design = {"schema": "JEV_A461_MECH_M12_P30_FIELDS_COSNULL_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M12_FORWARD",
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
                         "g10_counterfactuals_blob": BLOB_G10_CF, "g5v2_questions_blob": g5_full,
                         "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV, "base_classes": list(BASE),
              "arms": [[n, op, cl, ex] for n, op, cl, ex in ARMS], "c_positions": C_POS, "fields": FIELDS,
              "field_marks": FIELD_MARKS, "span_width": SPAN_W, "null_seeds": NULL_SEEDS, "split_k": SPLIT_K,
              "alpha_cap": ALPHA_CAP, "m11_replay": list(M11_REPLAY), "bulk": BULK,
              "pools": pools,
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "key_classes": key_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M12 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m12_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m12_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m12_design.json", "m12_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 7696,
                      "class_sizes": {t: {k: sum(hi - lo for lo, hi in v) for k, v in c["classes"].items()}
                                      for t, c in list(key_classes.items())[:3]},
                      "manifest_blob": file_blob(out / "m12_manifest.jsonl"),
                      "design_blob": file_blob(out / "m12_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
