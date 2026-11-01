#!/usr/bin/env python3
"""A461-MECH-M10 R1: CPU freeze of size-matched head slices, span positions and a multi-seed null for the pooled
round contrast on the common BULK shift of the L11 write of kev-4B (zero model forwards; tokenizer only).

M9 (da03730): the contrast c = mean_D B(ROUND) - mean_D B(new) is read only on the (nearly) full common shift
(GAIN_MIXED, GAIN_TMIN:1.0), through the o_proj-input slice of the writer heads 8-14 (chW S 39, chR 0, ch10 25 not
SPEC; not size-matched), and at matched size its active part lies outside the 16-dim common subspace (cperp16_sm
S 39, cpar16_sm 27 not SPEC) with a marginal one-seed null (crand16_sm S 7 > 5). In every M9 capture c is nonzero
only at span positions 29 and 30 (ROUND changes the token at 29). M10 asks:
  H  size-matched head slices: cs1 with c restricted to heads 8-14, head 10, the other 9 heads, or heads 8-14
     without 10, each slice rescaled to ||c|| per row and span position (cap 10)
  P  position: cs1 with c kept only at span position 29 or only at 30 (not size-matched)
  L  location of the common shift: the common shift only at positions 29-30, or only at 0-28, with the full c
  N  null: four more seeded random 16-frames for the size-matched split (5 seeds with M9's)
  T  finer gain: t in 0.6, 0.7, 0.8, 0.9 at s = 1
Anchors: full (M3, bitwise, 51), meanD_host (M6, bitwise, 39), cs1 / chW / ch10 / chR / cpar16_sm / cperp16_sm /
crand16_sm (M9 rows, same patch fields, bitwise; S 39 / 39 / 25 / 0 / 27 / 39 / 7). 44 captures + 104 x 25 x 2 =
5244 calls in 40 x 128 + 124.
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
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
N_HEADS, N_KV = 16, 4
SOURCES = ("new", "ROUND")
BASE = ("PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT")
BULK = ["OTHER_ITEMS", "CONTEXT"]
T_FINE = [("06", 0.6), ("07", 0.7), ("08", 0.8), ("09", 0.9)]   # common-shift scale t at s = 1
WRITER_HEADS = list(range(8, 15))                              # M3: heads 8-14 write the evaluation, head 10 core
REST_HEADS = [h for h in range(N_HEADS) if h not in WRITER_HEADS]
HEAD_SETS = [("chW", WRITER_HEADS), ("ch10", [10]), ("chR", REST_HEADS)]
HEAD_SETS_SM = [("chW_sm", WRITER_HEADS), ("ch10_sm", [10]), ("chR_sm", REST_HEADS),
                ("chWx10_sm", [h for h in WRITER_HEADS if h != 10])]
SPAN_W = 31
C_POS = [29, 30]      # the span positions where c != 0 in all 22 M9 captures (ROUND changes the token at 29)
CPOS = [("cpos29", [29]), ("cpos30", [30])]
SHPOS = [("sh2930", C_POS), ("sh0_28", list(range(29)))]
SPLIT_K = 16
N_SEEDS = 4
ALPHA_CAP = 10.0
M9_REPLAY = ("full", "meanD_host", "cs1", "chW", "ch10", "chR", "cpar16_sm", "cperp16_sm", "crand16_sm")
CS = {"t": 1.0, "s": 1.0}

# (name, op, classes, extra)
ARMS = ([("full", "full", [], {}),
         ("meanD_host", "pool", BULK, {"base": "target", "pool": "donors"}),
         ("cs1", "cshift", BULK, dict(CS))]
        + [(n, "cshift", BULK, dict(CS, heads=hs)) for n, hs in HEAD_SETS]
        + [(f"c{part}{SPLIT_K}_sm", "cshift", BULK, dict(CS, proj=part, seed=0)) for part in ("par", "perp", "rand")]
        + [(n, "cshift", BULK, dict(CS, heads=hs, rescale=True)) for n, hs in HEAD_SETS_SM]
        + [(n, "cshift", BULK, dict(CS, cpos=ps)) for n, ps in CPOS]
        + [(n, "cshift", BULK, dict(CS, shpos=ps)) for n, ps in SHPOS]
        + [(f"crand{SPLIT_K}_sm_s{i}", "cshift", BULK, dict(CS, proj="rand", seed=i)) for i in range(1, N_SEEDS + 1)]
        + [(f"g{tn}_1", "cshift", BULK, {"t": tv, "s": 1.0}) for tn, tv in T_FINE])
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
                        "checked in the run); cs1 / chW / ch10 / chR / cpar16_sm / cperp16_sm / crand16_sm = the M9 "
                        "arms (same patch fields): their 7 x 208 rows equal M9's bitwise and S = 39 / 39 / 25 / 0 / 27 / "
                        "39 / 7; otherwise every verdict is INCONSISTENT_WITH_M3_M6_M9 and no claim",
    "C": "C(arm) = median over cells of dM_main - dM_round",
    "heads_sm_verdict": "on cs1 with c restricted to a head slice and rescaled to ||c|| per row and span position: "
                        "CONTRAST_SM_IN_WRITER_HEADS iff SUF(chW_sm) and not SUF(chR_sm); CONTRAST_SM_OUTSIDE_WRITER_HEADS "
                        "iff SUF(chR_sm) and not SUF(chW_sm); CONTRAST_SM_EITHER_HEAD_SET iff both; "
                        "CONTRAST_SM_NEEDS_ALL_HEADS iff neither. Suffix +H10 iff SUF(ch10_sm); suffix +WX10 iff "
                        "SUF(chWx10_sm) (the writer heads without head 10)",
    "position_verdict": "on cs1 with c kept only at one span position (not size-matched; energy shares reported): "
                        "CONTRAST_AT_P29 iff SUF(cpos29) and not SUF(cpos30); CONTRAST_AT_P30 iff SUF(cpos30) and not "
                        "SUF(cpos29); CONTRAST_AT_EITHER_POSITION iff both; CONTRAST_NEEDS_BOTH_POSITIONS iff neither",
    "shift_location_verdict": "the common shift (t = 1) applied only at span positions 29-30 (sh2930) or only at 0-28 "
                              "(sh0_28), with the full c: SHIFT_AT_CONTRAST_POSITIONS iff SUF(sh2930) and not "
                              "SUF(sh0_28); SHIFT_AT_OTHER_POSITIONS iff SUF(sh0_28) and not SUF(sh2930); "
                              "SHIFT_AT_EITHER iff both; SHIFT_NEEDS_ALL_POSITIONS iff neither",
    "split_null_multi": "SPLIT_NULL5 holds iff the median S over the 5 random frames (crand16_sm = M9's seed and "
                        "crand16_sm_s1 .. s4) is <= 5 and none of them is SPEC; each S and the maximum are reported",
    "contrast_subspace_verdict": "on the M9 rows cpar16_sm / cperp16_sm (replayed bitwise): CONTRAST_IN_COMMON_SUBSPACE "
                                 "iff SUF(cpar16_sm) and not SUF(cperp16_sm); CONTRAST_OUTSIDE_COMMON_SUBSPACE iff "
                                 "SUF(cperp16_sm) and not SUF(cpar16_sm); CONTRAST_BOTH_PARTS iff both; "
                                 "CONTRAST_NOT_SPLITTABLE iff neither; suffix _UNRESOLVED on the first three iff "
                                 "SPLIT_NULL5 fails. The M9 one-seed verdict stays as reported in M9",
    "gain_tfine_verdict": "t* = the smallest t in 0.6, 0.7, 0.8, 0.9, 1 with SUF(g{t}_1) (cs1 at t = 1); "
                          "GAIN_TFINE:t*, or GAIN_TFINE_NONE; S, C and J per t and per host reported",
    "size_gate": "head-slice arms _sm: per row and span position where the slice is nonzero and alpha < cap, the "
                 "rescaled slice has norm ||c|| within 1e-3 relative (fail-closed in the runner); alpha = "
                 "min(||c|| / ||slice||, 10); the pre-rescale slice energy share, alpha and the capped share are "
                 "recorded. Random frames: as M9 (no cap)",
    "interpretation_fixed_in_advance": "CONTRAST_SM_IN_WRITER_HEADS: at the size of c, the writer heads' slice "
        "carries the contrast's effect and the other heads' slice does not, so the M9 head result is not an energy "
        "effect; +H10: head 10's slice alone suffices at matched size; +WX10: the writer heads without head 10 "
        "suffice. CONTRAST_AT_P29: the contrast acts at the position whose token ROUND changes; CONTRAST_AT_P30: at "
        "the next position. SHIFT_AT_CONTRAST_POSITIONS: the common shift is needed only where the contrast is "
        "(a local gate); SHIFT_AT_OTHER_POSITIONS: the shift acts through the earlier positions (context read by later "
        "layers); SHIFT_NEEDS_ALL_POSITIONS: neither part suffices alone. SPLIT_NULL5 failing means a contrast-sized "
        "push in a random 16-dim direction often repairs, and the M9 split verdict stays unresolved. GAIN_TFINE:t: "
        "the smallest common shift on the 0.1 grid at which the contrast at s = 1 repairs. All M10 arms except full "
        "are pooled-donor arms (effectively 8 host replicates, 3 responding in M9); per-host S is the honest unit. "
        "The position arms are not size-matched (position 29 holds most of c's energy)",
    "always_reported": "S, SPEC, J_main, J_round, median dM and C per arm; per host; leave-one-donor-group-out of "
                       "every verdict; energy shares, alpha, capped and zero-part shares of the head slices, positions "
                       "and contrast parts; the S of each random frame; change norm of every arm relative to full",
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
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.m1_design) == BLOB_M1_DESIGN
       and file_blob(a.m1_raw) == BLOB_M1_RAW and file_blob(a.m3_design) == BLOB_M3_DESIGN
       and file_blob(a.m3_raw) == BLOB_M3_RAW and file_blob(a.m4_design) == BLOB_M4_DESIGN and file_blob(a.g10_counterfactuals) == BLOB_G10_CF
       and file_blob(a.m6_design) == BLOB_M6_DESIGN and file_blob(a.m6_raw) == BLOB_M6_RAW
       and file_blob(a.m7_design) == BLOB_M7_DESIGN and file_blob(a.m7_raw) == BLOB_M7_RAW
       and file_blob(a.m8_design) == BLOB_M8_DESIGN and file_blob(a.m8_raw) == BLOB_M8_RAW
       and file_blob(a.m9_design) == BLOB_M9_DESIGN and file_blob(a.m9_raw) == BLOB_M9_RAW, "pins")
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
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    m3raw = [json.loads(x) for x in a.m3_raw.read_text("utf8").splitlines() if x.strip()]
    m6raw = [json.loads(x) for x in a.m6_raw.read_text("utf8").splitlines() if x.strip()]
    m7raw = [json.loads(x) for x in a.m7_raw.read_text("utf8").splitlines() if x.strip()]
    m8raw = [json.loads(x) for x in a.m8_raw.read_text("utf8").splitlines() if x.strip()]
    m9raw = [json.loads(x) for x in a.m9_raw.read_text("utf8").splitlines() if x.strip()]
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
                    if op == "cshift":    # common pooled shift (scale t), -+ s/2 of the pooled contrast
                        patch["base"] = "target"
                        patch["pool_new"] = [f"new:{t[:12]}" for t in pool_d]
                        patch["pool_round"] = [f"ROUND:{t[:12]}" for t in pool_d]
                        patch["scale"] = 0.0 if ex["s"] == 0 else (-ex["s"] / 2 if sk == "main" else ex["s"] / 2)
                        if ex["t"] != 1.0:    # t = 1: no field, the M8 cs code path (bitwise replay)
                            patch["t"] = ex["t"]
                        if "heads" in ex:
                            patch["contrast_heads"] = ex["heads"]
                        if ex.get("rescale"):
                            patch["contrast_rescale"] = "contrast"
                        if "cpos" in ex:
                            patch["contrast_positions"] = ex["cpos"]
                        if "shpos" in ex:
                            patch["shift_positions"] = ex["shpos"]
                        if "proj" in ex:
                            cpj = {"k": SPLIT_K, "part": "perp" if ex["proj"] == "perp" else "par", "rescale": "contrast"}
                            if ex["proj"] == "rand":
                                tag_ = (f"A461_M9_CRAND|{SPLIT_K}|{d}|{h}" if ex["seed"] == 0
                                        else f"A461_M10_CRAND|{SPLIT_K}|{d}|{h}|{ex['seed']}")
                                cpj.update(basis="random", cap=None,
                                           seed=int(hashlib.sha256(tag_.encode()).hexdigest()[:8], 16))
                            else:
                                m7p = m7_rows[(f"dlr{SPLIT_K}_sm", d, h, "main")]["patch"]
                                ck(m7p["basis_pairs"] == same_pairs and m7p["k"] == SPLIT_K, "M7 dlr16_sm basis")
                                cpj.update(basis="pairs", cap=ALPHA_CAP, basis_pairs=same_pairs)
                            patch["contrast_proj"] = cpj
                    if arm in M9_REPLAY:   # M9 replays: identical patch fields
                        m9p = m9_rows[(arm, d, h, sk)]["patch"]
                        ck(all(m9p.get(k_) == v_ for k_, v_ in patch.items())
                           and all(patch.get(k_) == v_ for k_, v_ in m9p.items() if v_ is not None), f"M9 {arm} wiring")
                    add(phase="patch", condition=f"patch_m10_{arm}_{sk}", direction="repair", scope="all",
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
    ck(len(seeds) == 208 and all(len(v) == 1 + N_SEEDS for v in seeds.values()), "5 distinct random frames per row")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m3")) == 208, "208 M3 bitwise anchors")
    ck(sum(1 for r in rows if r.get("bitwise_vs_m6")) == 208, "208 M6 bitwise anchors")
    design = {"schema": "JEV_A461_MECH_M10_HEADS_POSITIONS_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M10_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader); L11 = Qwen3.5 full attention, "
                       "16 query heads x 256 in 4 KV groups, output gate, o_proj without bias",
              "inputs": {"roster_blob": BLOB_ROSTER, "m1_design_blob": BLOB_M1_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                         "m3_design_blob": BLOB_M3_DESIGN, "m3_raw_blob": BLOB_M3_RAW, "m4_design_blob": BLOB_M4_DESIGN,
                         "m6_design_blob": BLOB_M6_DESIGN, "m6_raw_blob": BLOB_M6_RAW,
                         "m7_design_blob": BLOB_M7_DESIGN, "m7_raw_blob": BLOB_M7_RAW,
                         "m8_design_blob": BLOB_M8_DESIGN, "m8_raw_blob": BLOB_M8_RAW,
                         "m9_design_blob": BLOB_M9_DESIGN, "m9_raw_blob": BLOB_M9_RAW,
                         "g10_counterfactuals_blob": BLOB_G10_CF, "g5v2_questions_blob": g5_full,
                         "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts},
              "head_layer": HEAD_LAYER, "n_heads": N_HEADS, "n_kv_groups": N_KV, "base_classes": list(BASE),
              "arms": [[n, op, cl, ex] for n, op, cl, ex in ARMS], "t_fine": T_FINE, "head_sets": HEAD_SETS, "head_sets_sm": HEAD_SETS_SM, "c_positions": C_POS,
              "cpos": CPOS, "shpos": SHPOS, "span_width": SPAN_W, "n_seeds": N_SEEDS, "split_k": SPLIT_K,
              "alpha_cap": ALPHA_CAP, "bulk": BULK,
              "pools": pools,
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "key_classes": key_classes,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M10 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m10_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m10_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m10_design.json", "m10_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 5200,
                      "class_sizes": {t: {k: sum(hi - lo for lo, hi in v) for k, v in c["classes"].items()}
                                      for t, c in list(key_classes.items())[:3]},
                      "manifest_blob": file_blob(out / "m10_manifest.jsonl"),
                      "design_blob": file_blob(out / "m10_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
