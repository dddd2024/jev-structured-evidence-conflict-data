#!/usr/bin/env python3
"""A461-MECH-M11 R1: CPU freeze of size-matched span-position and shift-location arms, and a per-host split null,
for the pooled round contrast on the common BULK shift of the L11 write of kev-4B (zero model forwards; tokenizer only).

M10 (c4c4aeb): CONTRAST_AT_P29 (cpos29 S 39, cpos30 S 3) but position 29 holds 89 % of c's energy (not size-matched;
A573: a pure amplitude threshold reproduces it); SHIFT_NEEDS_ALL_POSITIONS (sh2930 J 0 / 0, sh0_28 S 13), but the shift
at 29-30 is 5 % of the shift's change norm; SPLIT_NULL5 fails (S 7 / 11 / 4 / 7 / 4, 27 of 33 hits on host 1fb5651c).
M11 asks:
  P  size-matched position: c kept only at 29 rescaled to the norm of c at 30, and c kept only at 30 rescaled to the
     norm of c at 29 (per row, cap 10), plus a dose: c at 29 with s = 1/4, 1/2 and c at 30 with s = 2, 4
  L  size-matched shift location: the common shift only at 29-30, rescaled so that its total norm equals the norm of
     the shift at 0-28 (tm), or its per-token norm equals the mean per-token norm at 0-28 (pt), per row, cap 10; plus a
     dose u = 2, 4 on the shift at 29-30
  N  per-host split null: five more seeded random 16-frames (M10's five are read from the pinned M10 raw); the split is
     decided per responsive host against the maximum null over 10 frames
Anchors: full (M3, bitwise, 51), meanD_host (M6, bitwise, 39), cs1 / chR_sm / cpar16_sm / cperp16_sm / cpos29 / cpos30 /
sh2930 / sh0_28 (M10 rows, same patch fields, bitwise; S 39 / 0 / 27 / 39 / 39 / 3 / 0 / 13). 44 captures +
104 x 25 x 2 = 5244 calls in 40 x 128 + 124.
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
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
N_HEADS, N_KV = 16, 4
SOURCES = ("new", "ROUND")
BASE = ("PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT")
BULK = ["OTHER_ITEMS", "CONTEXT"]
REST_HEADS = [h for h in range(N_HEADS) if h not in range(8, 15)]   # M3 writer heads are 8-14
SPAN_W = 31
C_POS = [29, 30]      # the span positions where c != 0 in all M9 / M10 captures (ROUND changes the token at 29)
SPLIT_K = 16
SEEDS = list(range(5, 10))   # M10 used seed 0 (M9's frame) and 1-4
ALPHA_CAP = 10.0
M10_REPLAY = ("full", "meanD_host", "cs1", "chR_sm", "cpar16_sm", "cperp16_sm", "cpos29", "cpos30", "sh2930", "sh0_28")
CS = {"t": 1.0, "s": 1.0}

# (name, op, classes, extra)
ARMS = ([("full", "full", [], {}),
         ("meanD_host", "pool", BULK, {"base": "target", "pool": "donors"}),
         ("cs1", "cshift", BULK, dict(CS)),
         ("chR_sm", "cshift", BULK, dict(CS, heads=REST_HEADS, rescale=True))]
        + [(f"c{part}{SPLIT_K}_sm", "cshift", BULK, dict(CS, proj=part, seed=0)) for part in ("par", "perp")]
        + [("cpos29", "cshift", BULK, dict(CS, cpos=[29])), ("cpos30", "cshift", BULK, dict(CS, cpos=[30])),
           ("sh2930", "cshift", BULK, dict(CS, shpos=C_POS)), ("sh0_28", "cshift", BULK, dict(CS, shpos=list(range(29))))]
        + [("cpos29_n30", "cshift", BULK, dict(CS, cpos=[29], cnorm=30)),
           ("cpos30_n29", "cshift", BULK, dict(CS, cpos=[30], cnorm=29))]
        + [(f"cpos29_s{sn}", "cshift", BULK, dict(CS, s=sv, cpos=[29])) for sn, sv in (("025", 0.25), ("05", 0.5))]
        + [(f"cpos30_s{sn}", "cshift", BULK, dict(CS, s=sv, cpos=[30])) for sn, sv in (("2", 2.0), ("4", 4.0))]
        + [("sh2930_tm", "cshift", BULK, dict(CS, shpos=C_POS, shresc="complement_total")),
           ("sh2930_pt", "cshift", BULK, dict(CS, shpos=C_POS, shresc="complement_token"))]
        + [(f"sh2930_u{un}", "cshift", BULK, dict(CS, shpos=C_POS, shscale=uv)) for un, uv in (("2", 2.0), ("4", 4.0))]
        + [(f"crand{SPLIT_K}_sm_s{i}", "cshift", BULK, dict(CS, proj="rand", seed=i)) for i in SEEDS])
PLAN = [128] * 40 + [124]

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
                        "checked in the run); cs1 / chR_sm / cpar16_sm / cperp16_sm / cpos29 / cpos30 / sh2930 / sh0_28 = "
                        "the M10 arms (same patch fields): their 8 x 208 rows equal M10's bitwise and S = 39 / 0 / 27 / "
                        "39 / 39 / 3 / 0 / 13; otherwise every verdict is INCONSISTENT_WITH_M3_M6_M10 and no claim",
    "C": "C(arm) = median over cells of dM_main - dM_round",
    "position_sm_verdict": "c kept at one span position and rescaled per row to the norm c has at the other position "
                           "(cap 10): POSITION29_SPECIFIC iff SUF(cpos29_n30) and not SUF(cpos30_n29); AMPLITUDE_DRIVEN iff "
                           "SUF(cpos30_n29) and not SUF(cpos29_n30); BOTH_POSITIONS_ACT_AT_SWAPPED_NORM iff both; "
                           "P30_INERT_AT_P29_NORM iff neither. AMPLITUDE_ONLY_EXCLUDED iff not SUF(cpos30_n29)",
    "position_dose": "POS29_SMIN = the smallest s in 0.25, 0.5, 1 with SUF (cpos29_s025, cpos29_s05, cpos29); POS30_SMIN "
                     "= the smallest s in 1, 2, 4 with SUF (cpos30, cpos30_s2, cpos30_s4); NONE if no s; the per-row "
                     "norm ratio ||c_29|| / ||c_30|| is reported",
    "shift_sm_verdict": "the common shift (t = 1) only at span positions 29-30, rescaled per row so that its total norm "
                        "equals that of the shift at 0-28 (sh2930_tm) or its per-token norm equals the mean per-token "
                        "norm at 0-28 (sh2930_pt), cap 10, with the full c: SHIFT_LOCAL_AT_TOTAL_NORM iff SUF(sh2930_tm) "
                        "and not SUF(sh2930_pt); SHIFT_LOCAL_AT_TOKEN_NORM iff the reverse; SHIFT_LOCAL_SUFFICES iff "
                        "both; SHIFT_NEEDS_CONTEXT_POSITIONS iff neither",
    "shift_dose": "SHIFT2930_UMIN = the smallest u in 1, 2, 4 with SUF (sh2930, sh2930_u2, sh2930_u4), or NONE; the "
                  "per-row total and per-token norm ratios of the shift at 29-30 vs 0-28 and the applied factors are "
                  "reported",
    "split_by_host": "responsive host = a host where S(cs1) on its cells exceeds half its cells. Per responsive host: "
                     "null_max = the maximum over the 10 random frames (crand16_sm and crand16_sm_s1 .. s4 from the "
                     "pinned M10 raw, crand16_sm_s5 .. s9 here) of the host's S; OUTSIDE iff S(cperp16_sm) > null_max "
                     "and S(cpar16_sm) <= null_max; INSIDE iff the reverse; BOTH iff both exceed; NEITHER iff neither. "
                     "Verdict SPLIT_BY_HOST:<host8>=<v>,... over the responsive hosts",
    "split_null10": "SPLIT_NULL10 holds iff the median pooled S over the 10 random frames is <= 5 and none is SPEC; the "
                    "pooled subspace verdict is re-applied with the M9 / M10 categories and the _UNRESOLVED suffix iff "
                    "SPLIT_NULL10 fails",
    "size_gate": "rescaled rows: where not capped, the rescaled part has the target norm within 1e-3 relative "
                 "(fail-closed in the runner): the kept position's c (target ||c|| at the other position), the shift at "
                 "29-30 (target the total or per-token-scaled norm at 0-28, or u times its own norm); the factors, the "
                 "capped share and the pre-rescale shares are recorded",
    "interpretation_fixed_in_advance": "A pure amplitude threshold (A573) predicts SUF(cpos30_n29); AMPLITUDE_ONLY_EXCLUDED "
        "means c at position 30, given the size c has at 29, does not act, so the M10 P29 effect is not size alone. "
        "This separates position and direction together from size, not position from direction (c's direction at 30 "
        "differs from that at 29). AMPLITUDE_DRIVEN: the M10 P29 verdict reflects size. SHIFT_LOCAL_AT_TOTAL_NORM: with "
        "the same total shift norm, the shift at 29-30 alone suffices, so M10's SHIFT_NEEDS_ALL_POSITIONS was an amount "
        "effect; SHIFT_NEEDS_CONTEXT_POSITIONS: even the norm-matched local shift fails, so the shift must reach the "
        "context positions. SPLIT_BY_HOST: per responsive host, whether the part of c outside (or inside) the 16-dim "
        "common subspace repairs more cells than any of 10 contrast-sized random frames. All M11 arms except full are "
        "pooled-donor arms (effectively 8 host replicates, 3 responding in M9-M10); per-host S is the honest unit",
    "always_reported": "S, SPEC, J_main, J_round, median dM and C per arm; per host; leave-one-donor-group-out of "
                       "every verdict; energy shares, factors, capped shares; the S of each random frame, pooled and per "
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
       and file_blob(a.m10_design) == BLOB_M10_DESIGN and file_blob(a.m10_raw) == BLOB_M10_RAW, "pins")
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
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    m3raw = [json.loads(x) for x in a.m3_raw.read_text("utf8").splitlines() if x.strip()]
    m6raw = [json.loads(x) for x in a.m6_raw.read_text("utf8").splitlines() if x.strip()]
    m7raw = [json.loads(x) for x in a.m7_raw.read_text("utf8").splitlines() if x.strip()]
    m8raw = [json.loads(x) for x in a.m8_raw.read_text("utf8").splitlines() if x.strip()]
    m9raw = [json.loads(x) for x in a.m9_raw.read_text("utf8").splitlines() if x.strip()]
    m10raw = [json.loads(x) for x in a.m10_raw.read_text("utf8").splitlines() if x.strip()]
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
        ck(m8["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M8 key classes differ at {s[:8]}:{arm}")
        ck(m9["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M9 key classes differ at {s[:8]}:{arm}")
        ck(m10["key_classes"][f"{arm}:{s[:12]}"]["classes"] == cls, f"M10 key classes differ at {s[:8]}:{arm}")
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
                        ck(ex["t"] == 1.0, "t = 1 in every M11 arm")
                        if "heads" in ex:
                            patch["contrast_heads"] = ex["heads"]
                        if ex.get("rescale"):
                            patch["contrast_rescale"] = "contrast"
                        if "cpos" in ex:
                            patch["contrast_positions"] = ex["cpos"]
                        if "cnorm" in ex:
                            patch["contrast_pos_norm_from"] = ex["cnorm"]
                        if "shpos" in ex:
                            patch["shift_positions"] = ex["shpos"]
                        if "shresc" in ex:
                            patch["shift_rescale"] = ex["shresc"]
                        if "shscale" in ex:
                            patch["shift_scale"] = ex["shscale"]
                        if "proj" in ex:
                            cpj = {"k": SPLIT_K, "part": "perp" if ex["proj"] == "perp" else "par", "rescale": "contrast"}
                            if ex["proj"] == "rand":
                                tag_ = f"A461_M10_CRAND|{SPLIT_K}|{d}|{h}|{ex['seed']}"   # the M10 seed family, seeds 5-9
                                cpj.update(basis="random", cap=None,
                                           seed=int(hashlib.sha256(tag_.encode()).hexdigest()[:8], 16))
                            else:
                                m7p = m7_rows[(f"dlr{SPLIT_K}_sm", d, h, "main")]["patch"]
                                ck(m7p["basis_pairs"] == same_pairs and m7p["k"] == SPLIT_K, "M7 dlr16_sm basis")
                                cpj.update(basis="pairs", cap=ALPHA_CAP, basis_pairs=same_pairs)
                            patch["contrast_proj"] = cpj
                    if arm in M10_REPLAY:   # M10 replays: identical patch fields
                        m10p = m10_rows[(arm, d, h, sk)]["patch"]
                        ck(all(m10p.get(k_) == v_ for k_, v_ in patch.items())
                           and all(patch.get(k_) == v_ for k_, v_ in m10p.items() if v_ is not None), f"M10 {arm} wiring")
                    add(phase="patch", condition=f"patch_m11_{arm}_{sk}", direction="repair", scope="all",
                        source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                        target_arm="new", patch=patch,
                        bitwise_vs_m3=m3_all[(d, h, sk)] if op == "full" else None,
                        bitwise_vs_m6=m6_md[(d, h, sk)]["forward_index"] if op == "pool" else None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * len(ARMS) * 2 == 5200, "104 x 25 x 2 patches")
    ck(len({r["condition"] for r in rows if r["phase"] == "patch"}) == 50, "50 patch conditions")
    seeds = collections.defaultdict(set)
    for r in rows:
        if r["phase"] == "patch" and (r["patch"].get("contrast_proj") or {}).get("basis") == "random":
            seeds[(r["donor"], r["host"], r["source_kind"])].add(r["patch"]["contrast_proj"]["seed"])
    ck(len(seeds) == 208 and all(len(v) == len(SEEDS) and not (v & m10_seeds[k_]) for k_, v in seeds.items()),
       "5 distinct random frames per row, disjoint from the M10 frames")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m3")) == 208, "208 M3 bitwise anchors")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m6")) == 208, "208 M6 bitwise anchors")
    design = {"schema": "JEV_A461_MECH_M11_MATCHED_POSITION_SHIFT_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M11_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader); L11 = Qwen3.5 full attention, "
                       "16 query heads x 256 in 4 KV groups, output gate, o_proj without bias",
              "inputs": {"roster_blob": BLOB_ROSTER, "m1_design_blob": BLOB_M1_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                         "m3_design_blob": BLOB_M3_DESIGN, "m3_raw_blob": BLOB_M3_RAW, "m4_design_blob": BLOB_M4_DESIGN,
                         "m6_design_blob": BLOB_M6_DESIGN, "m6_raw_blob": BLOB_M6_RAW,
                         "m7_design_blob": BLOB_M7_DESIGN, "m7_raw_blob": BLOB_M7_RAW,
                         "m8_design_blob": BLOB_M8_DESIGN, "m8_raw_blob": BLOB_M8_RAW,
                         "m9_design_blob": BLOB_M9_DESIGN, "m9_raw_blob": BLOB_M9_RAW,
                         "m10_design_blob": BLOB_M10_DESIGN, "m10_raw_blob": BLOB_M10_RAW,
                         "g10_counterfactuals_blob": BLOB_G10_CF, "g5v2_questions_blob": g5_full,
                         "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV, "base_classes": list(BASE),
              "arms": [[n, op, cl, ex] for n, op, cl, ex in ARMS], "rest_heads": REST_HEADS, "c_positions": C_POS,
              "span_width": SPAN_W, "seeds": SEEDS, "split_k": SPLIT_K, "alpha_cap": ALPHA_CAP,
              "m10_replay": list(M10_REPLAY), "bulk": BULK,
              "pools": pools,
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "key_classes": key_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M11 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m11_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m11_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m11_design.json", "m11_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 5200,
                      "class_sizes": {t: {k: sum(hi - lo for lo, hi in v) for k, v in c["classes"].items()}
                                      for t, c in list(key_classes.items())[:3]},
                      "manifest_blob": file_blob(out / "m11_manifest.jsonl"),
                      "design_blob": file_blob(out / "m11_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
