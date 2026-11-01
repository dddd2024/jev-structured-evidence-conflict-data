#!/usr/bin/env python3
"""A461-MECH-M17 R1: CPU freeze of the false-veto control (zero model forwards; tokenizer only).

Every M1-M16 patch targeted host new, the conflicting scene, so whether the repairing patches also push benign hosts
to reject_conflict (false veto) was never measured. M17 applies four of them, unchanged, to the same 8 hosts' three
benign variants, which carry a 31-token appended vote at the same span position as host new and whose source-internal
Gold is accept or wait (never reject_conflict; conflicting_vote false):
  SA        the roster's SHAM_same_author_duplicate (an existing vote sent again; Stage-A screen arm)
  ROUND     host new's message with the round changed to a non-candidate round (G1.0 counterfactual)
  OUTSIDER  host new's message with the author changed to a non-validator (G1.0 counterfactual)
Arms (each on all 104 cross-group cells of M1-M16, per benign target T; sources donor new = main, donor ROUND = round):
  full@T     the M3 all-heads L11 o_proj-input span patch (the donor's own write)
  meanD@T    the M6 pooled-donor BULK arm (base = T's own capture)
  cs0@T      the M8 common shift alone (contrast scale 0; main == round by construction, so main rows only)
  abc05@T    the M14 AB arm at s 1/2 (shift at 0-12 + 29-30, c at 29 only)
Anchors on host new, on M14's 6 subset cells, both sources: full (bitwise M3), meanD_host (bitwise M6), cs0 (bitwise
M8), abc_s05 (bitwise M14); their fields are checked here to equal the pinned rows'. Benign captures use host new's key
classes: the benign state differs from host new only inside the span, so every key before the span is token-identical
(checked), and the field layout of the span is checked against the M12 field marks.
60 captures + 6 x 4 x 2 + 3 x 104 x 7 = 2292 calls in 17 x 128 + 116.
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
BLOB_M6_DESIGN = "43967513c3dbcad74dd7b024b67a16463f456ffc"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M8_DESIGN = "14cee4c2cffe30d78338de8063c72110f223f0bb"
BLOB_M8_RAW = "997c9b71054ee2adec472a5410705068511650aa"
BLOB_M14_DESIGN = "87905a3c4d0a5786a25bbd974ef13c40f3f3c06b"
BLOB_M14_RAW = "d2ac9f4221728d309300cbf617385ad79925eb0b"
BLOB_M16_DESIGN = "c061686a5a3271e2b06f418f213bce81fa3ff05a"
BLOB_M16_RAW = "1d74b63ba7e24fa47f6fe2cac1b967a9f141706e"
BLOB_G5V2 = "66c1f95e"   # resolved to the full blob via the repo below; full sha recorded in the design
HEAD_LAYER = 11
SOURCES = ("new", "ROUND")
TARGETS = ("SA", "ROUND", "OUTSIDER")
BULK = ["OTHER_ITEMS", "CONTEXT"]
SPAN_W = 31
C_POS = [29, 30]
AB = list(range(0, 13))
FIELD_MARKS = {2: " author", 6: "\n", 8: " block", 12: "\n", 14: " kind", 17: "\n", 19: " received", 24: "\n",
               26: " round", 30: "\n"}
RESP = ("1fb5651c", "264c458d", "4bcbaf15")
# (name, op, classes, extra); the anchor names are the pinned stages' arm names
ARMS = (("full", "full", [], {}),
        ("meanD", "pool", BULK, {"base": "target"}),
        ("cs0", "cshift", BULK, {"s": 0.0, "main_only": True}),
        ("abc05", "cshift", BULK, {"s": 0.5, "shpos": AB + C_POS, "cw": 0.0}))
ANCHOR_NAME = {"full": "full", "meanD": "meanD_host", "cs0": "cs0", "abc05": "abc_s05"}
PLAN = [128] * 17 + [116]

PREREG = {
    "readouts": "M = logit(conflicting_vote=true) - logit(false); A = logit(reject_conflict) - max(accept, wait); "
                "JOINT = M > 0 and A > 0; action = argmax over (accept, reject_conflict, wait)",
    "gold": "source-internal executable rule: every benign target T in {SA, ROUND, OUTSIDER} of every host has Gold "
            "action accept (6 hosts) or wait (1fb5651c, 1c7158b6) and conflicting_vote false (roster oracle_sa; G1.0 "
            "counterfactual gold); reject_conflict is never correct on a benign target",
    "units": "104 cross-group cells (14 donors x 8 hosts minus same-group pairs), shared donors and hosts; the "
             "pooled arms vary with the donor only through the pool exclusion (effectively 8 host replicates); counts "
             "are descriptive decision rules, not independent tests; per-host counts are always reported",
    "false_veto": "FV(arm, T) = #cells where the main-source patch of T has action reject_conflict and T's in-run "
                  "unpatched capture does not; FV_round the same for the round source; FVJ = #cells JOINT after the "
                  "main-source patch and not JOINT unpatched; FV_h per host (of its cells)",
    "repair_reference": "R(arm) = #cells where the same arm's main-source patch of host new has action "
                        "reject_conflict and host new's unpatched capture does not, read from the pinned rows on all "
                        "104 cells: full = M3 'all', meanD = M6 meanD_host, cs0 = M8 cs0, abc05 = M14 abc_s05 (their "
                        "6-cell subsets are replayed bitwise here); R_h per host",
    "fv_verdict": "per arm and T: FV_NONE iff FV <= 5 and no host has FV_h >= 7; FV_AS_REPAIR iff FV >= R(arm) / 2; "
                  "else FV_PARTIAL. Per arm: SELECTIVE iff FV_NONE on all three T; NONSELECTIVE iff FV_AS_REPAIR on "
                  ">= 2 of 3 T; else MIXED",
    "host_selectivity": "per responsive host (1fb5651c, 264c458d, 4bcbaf15) and arm: R_h on host new and FV_h on each "
                        "T; HOST_SELECTIVE iff R_h >= 7 and every FV_h <= 1; HOST_NONSELECTIVE iff R_h >= 7 and some "
                        "FV_h >= R_h / 2; else HOST_MIXED (R_h < 7: HOST_UNINFORMATIVE)",
    "source_contrast_on_benign": "per arm (not cs0) and T: share of cells with A_main > A_round after the patch, and "
                                 "FV_round; reported, not a verdict",
    "consistency_gate": "the 36 M1 capture readouts bitwise (runner); full / meanD_host anchors 12 rows each bitwise "
                        "== M3 / M6 (runner and analysis); cs0 12 rows bitwise == M8 and abc_s05 12 rows bitwise == "
                        "M14 (analysis); every benign capture's token ids equal the roster / G1.0 sha and its unpatched "
                        "action is reported against Gold; otherwise every verdict is INCONSISTENT and no claim",
    "interpretation_fixed_in_advance": (
        "full NONSELECTIVE: the donor's L11 span state is applied downstream to whatever vote sits at the span, "
        "without a re-check against the host's context, so the M1-M3 repair is the injection of a carried verdict, "
        "not the enabling of the host's own relation check; such a patch cannot serve as a defence without a "
        "false-veto cost of the same order. full SELECTIVE: downstream still checks the vote against the context, and "
        "the injected evaluation acts only where the host's context supports a conflict. cs0 NONSELECTIVE is the "
        "standard's par. 3.6 threshold push (expected: M8 cs0 flips main and round alike). meanD / abc05 decide "
        "whether the pooled repairs of M6-M16 are conditional on a real conflict. ROUND (conflict-shaped, wrong "
        "round) and OUTSIDER (non-validator author) are near misses; SA is a plain duplicate. Level S1-S2: an "
        "artificial intervention scored on the native action against source-internal Gold; no deployment claim"),
    "always_reported": "unpatched benign action vs Gold per host and T; FV, FV_round, FVJ, R per arm and T; FV_h, R_h "
                       "per host; median dM and dA vs unpatched; off-Gold changes of any kind (accept <-> wait); "
                       "leave-one-donor-group-out of every verdict",
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
    for n in ("m1", "m3", "m6", "m8", "m14"):
        ap.add_argument(f"--{n}-design", required=True, type=Path)
        ap.add_argument(f"--{n}-raw", required=True, type=Path)
    ap.add_argument("--m16-design", required=True, type=Path)
    ap.add_argument("--m16-raw", required=True, type=Path)
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    pins = {"roster": (a.roster, BLOB_ROSTER), "m1_design": (a.m1_design, BLOB_M1_DESIGN),
            "m1_raw": (a.m1_raw, BLOB_M1_RAW), "m3_design": (a.m3_design, BLOB_M3_DESIGN),
            "m3_raw": (a.m3_raw, BLOB_M3_RAW), "m6_design": (a.m6_design, BLOB_M6_DESIGN),
            "m6_raw": (a.m6_raw, BLOB_M6_RAW), "m8_design": (a.m8_design, BLOB_M8_DESIGN),
            "m8_raw": (a.m8_raw, BLOB_M8_RAW), "m14_design": (a.m14_design, BLOB_M14_DESIGN),
            "m14_raw": (a.m14_raw, BLOB_M14_RAW), "m16_design": (a.m16_design, BLOB_M16_DESIGN), "m16_raw": (a.m16_raw, BLOB_M16_RAW),
            "g10": (a.g10_counterfactuals, BLOB_G10_CF)}
    for k, (p, b) in pins.items():
        ck(file_blob(p) == b, f"pin {k}")
    spec = importlib.util.spec_from_file_location("sa", WORK / "A461_g5_g2_stage_a_cpu_freeze_v1.py")
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    ck(sha_file(sa.CORPUS) == sa.CORPUS_SHA, "corpus pin")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    J = lambda p: json.loads(Path(p).read_text("utf8"))
    L = lambda p: [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]
    m1, m3, m6, m8, m14, m16 = (J(p) for p in (a.m1_design, a.m3_design, a.m6_design, a.m8_design, a.m14_design,
                                               a.m16_design))
    cf = J(a.g10_counterfactuals)
    m1raw, m3raw, m6raw, m8raw, m14raw, m16raw = (L(p) for p in (a.m1_raw, a.m3_raw, a.m6_raw, a.m8_raw, a.m14_raw,
                                                                 a.m16_raw))
    donors, hosts = m1["selection"]["donors"], m1["selection"]["hosts"]
    ck(len(donors) == 14 and len(hosts) == 8, "selection")
    for d_ in (m3, m6, m8, m14, m16):
        ck(d_["selection"] == {"donors": donors, "hosts": hosts}, "selection differs from M1")
    ck(m8["pools"] == m6["pools"] == m14["pools"] == m16["pools"], "pools differ across M6 / M8 / M14 / M16")
    gd, gh = dict(donors), dict(hosts)
    m1_cap = {(x["target_scene"], x["target_arm"]): x["forward_index"] for x in m1raw if x["capture"]}
    pinned = {}
    for tag, rr, arm in (("M3", m3raw, "all"), ("M6", m6raw, "meanD_host"), ("M8", m8raw, "cs0"),
                         ("M14", m14raw, "abc_s05")):
        pinned[tag] = {(x["donor"], x["host"], x["source_kind"]): x for x in rr if x["patch"] and x["patch"]["arm"] == arm}
        ck(len(pinned[tag]) == 208, f"208 {tag} {arm} rows")
    # wiring templates in the current patch schema: M16's full / meanD_host rows (bitwise == M3 / M6 in M16), M8's cs0
    # and M14's abc_s05 rows (already in this schema)
    wire = {"full": {(x["donor"], x["host"], x["source_kind"]): x for x in m16raw if x["patch"] and x["patch"]["arm"] == "full"},
            "meanD": {(x["donor"], x["host"], x["source_kind"]): x for x in m16raw
                      if x["patch"] and x["patch"]["arm"] == "meanD_host"},
            "cs0": pinned["M8"], "abc05": pinned["M14"]}
    ck(all(len(v) == 208 for v in wire.values()), "208 wiring rows per arm")
    sub_cells = {tuple(c) for c in m14["subset_cells"]}
    ck(len(sub_cells) == 6 and m16["subset_cells"] == m14["subset_cells"], "6 subset cells = M14's = M16's")

    # ---------- benign spans (tokenizer only) ----------
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
    hset = set(gh)
    scenes = {}
    for line in gzip.open(sa.CORPUS, "rt", encoding="utf8"):
        if line.strip():
            rec = json.loads(line)
            if rec["_meta"].get("source") == "twins_streamlet":
                sh = hashlib.sha256(sa.canon(rec["state"]).encode("utf8")).hexdigest()
                if sh in hset:
                    scenes[sh] = rec["state"]
    ck(set(scenes) == hset, "host scene recovery")

    def message(h, arm):
        return {"new": roster[h]["declared_edit_new"]["message"], "SA": roster[h]["declared_edit_sa"]["message"]
                }.get(arm) or cf[h][arm]["message"]

    def want_sha(h, arm):
        return roster[h]["token_ids_sha256"][arm] if arm in ("new", "SA") else cf[h][arm]["token_ids_sha256"]

    def ids_of(h, arm):
        st = json.loads(sa.canon(scenes[h]))
        st["received_messages"].append(dict(message(h, arm)))
        rendered, _ = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(sa.canon(st))}))
        e = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
        ck(not e["state_truncated"], "truncated")
        ck(sa.hids(e["ids"]) == want_sha(h, arm), f"token gate {h[:8]}:{arm}")
        return e["ids"][:e["seg"].count(0)], sa.hids(e["ids"])

    gold, benign = {}, {}
    for h, _g in hosts:
        nid, _ = ids_of(h, "new")
        s0, s1 = roster[h]["appended_span_in_state"]["new"]
        ck(s1 - s0 == SPAN_W and roster[h]["frozen_width"] == SPAN_W, f"span width {h[:8]}")
        newc = m16["key_classes"][f"new:{h[:12]}"]
        ck(newc["span"] == [s0, s1], f"M16 host new span {h[:8]}")
        for T in TARGETS:
            ids, tid = ids_of(h, T)
            span = roster[h]["appended_span_in_state"]["SA"] if T == "SA" else cf[h][T]["span"]
            ck(span == [s0, s1] and len(ids) == len(nid) and ids[:s0] == nid[:s0] and ids[s1:] == nid[s1:],
               f"benign {T} differs from host new outside the span at {h[:8]}")
            dec = [tok.decode([t]) for t in ids[s0:s1]]
            ck(all(dec[i_] == t_ for i_, t_ in FIELD_MARKS.items()), f"span field layout at {h[:8]}:{T}")
            g_ = roster[h]["oracle_sa"] if T == "SA" else cf[h][T]["gold"]
            ck(cf[h].get(T, {"ok": True}).get("ok", True) and g_["certificate_action"] in ("accept", "wait")
               and g_["conflicting_vote"] is False, f"benign Gold {h[:8]}:{T}")
            ck(g_["certificate_action"] == roster[h]["oracle_old"]["certificate_action"], f"Gold = old {h[:8]}:{T}")
            gold[f"{T}:{h[:12]}"] = g_
            benign[f"{T}:{h[:12]}"] = {"span": [s0, s1], "classes": newc["classes"], "token_ids_sha256": tid,
                                       "state_len": len(ids), "message": message(h, T)}

    rows = []

    def add(**kw):
        n = len(rows)
        rows.append(dict(forward_index=n + 1, run=n // 128 + 1, **kw))

    for kind, sel in (("donor", donors), ("host", hosts)):
        for s, _g in sel:
            for arm in SOURCES:
                tag = f"{arm}:{s[:12]}"
                kc = m16["key_classes"][tag]
                add(phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm,
                    source_kind=kind,
                    capture={"tag": tag, "span": kc["span"], "rows": "all", "save": True, "layer": HEAD_LAYER,
                             "classes": kc["classes"], "partner": kc["classes"]["PARTNER"][0]},
                    bitwise_vs_m1=m1_cap.get((s, arm)))
    ck(sum(1 for r in rows if r["bitwise_vs_m1"]) == 36, "36 M1 bitwise anchors")
    for h, _g in hosts:
        for T in ("SA", "OUTSIDER"):     # host ROUND is captured above (a source kind of M1-M16)
            tag = f"{T}:{h[:12]}"
            b = benign[tag]
            add(phase="capture", condition=f"capture_{T}_all_rows", target_scene=h, target_arm=T, source_kind="host",
                capture={"tag": tag, "span": b["span"], "rows": "all", "save": True, "layer": HEAD_LAYER,
                         "classes": b["classes"], "partner": b["classes"]["PARTNER"][0]}, bitwise_vs_m1=None)
    for h, _g in hosts:
        ck(m16["key_classes"][f"ROUND:{h[:12]}"]["span"] == benign[f"ROUND:{h[:12]}"]["span"]
           and m16["key_classes"][f"ROUND:{h[:12]}"]["classes"] == benign[f"ROUND:{h[:12]}"]["classes"],
           f"host ROUND capture classes = host new's at {h[:8]}")
    ck(len(rows) == 60, "60 captures")

    dlist = [d for d, _ in donors]
    cells = [(d, h) for d, _ in donors for h, _ in hosts if gd[d] != gh[h]]
    ck(len(cells) == 104, "104 cells")
    built = {}

    def patch_for(arm, op, cl, ex, d, h, T, src):
        sk = "main" if src == "new" else "round"
        pool_d = [t for t in dlist if gd[t] not in (gd[d], gh[h])]
        ck(len(pool_d) == 12 and m6["pools"][f"{d[:12]}|{h[:12]}"]["donors"] == [t[:12] for t in pool_d], "pools")
        name = ANCHOR_NAME[arm] if T == "new" else f"{arm}@{T}"
        p = {"layer": HEAD_LAYER, "arm": name, "op": op, "classes": cl, "span": benign[f"SA:{h[:12]}"]["span"],
             "source": f"{src}:{d[:12]}", "target": f"{T}:{h[:12]}", "rows": "all"}
        if op == "pool":
            p["base"] = "target"
            p["pool"] = [f"{src}:{t[:12]}" for t in pool_d]
        if op == "cshift":
            p["base"] = "target"
            p["pool_new"] = [f"new:{t[:12]}" for t in pool_d]
            p["pool_round"] = [f"ROUND:{t[:12]}" for t in pool_d]
            p["scale"] = 0.0 if ex["s"] == 0 else (-ex["s"] / 2 if sk == "main" else ex["s"] / 2)
            if "shpos" in ex:
                p["shift_positions"] = ex["shpos"]
            if "cw" in ex:
                p["contrast_pos_weight"] = [[30, ex["cw"]]]
        return name, sk, p

    # anchors on host new: the pinned arms on the 6 subset cells, both sources, identical fields to the pinned rows
    for d, h in cells:
        if (d[:12], h[:12]) not in sub_cells:
            continue
        for arm, op, cl, ex in ARMS:
            for src in SOURCES:
                name, sk, p = patch_for(arm, op, cl, ex, d, h, "new", src)
                pt = {"full": "M3", "meanD": "M6", "cs0": "M8", "abc05": "M14"}[arm]
                pr = pinned[pt][(d, h, sk)]
                pp = {k_: v_ for k_, v_ in wire[arm][(d, h, sk)]["patch"].items() if v_ is not None}
                want = dict(p, arm=pp["arm"])
                ck(pp == want, f"{pt} anchor wiring {arm} {d[:8]} {h[:8]} {sk}: {sorted(set(pp) ^ set(want))}")
                built[(name, d, h, sk)] = p
                add(phase="patch", condition=f"patch_m17_anchor_{name}_{sk}", direction="anchor", scope="all",
                    source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                    target_arm="new", patch=dict(p, arm=pp["arm"]), anchor_of={"stage": pt, "forward_index": pr["forward_index"]},
                    bitwise_vs_m3=pr["forward_index"] if pt == "M3" else None,
                    bitwise_vs_m6=pr["forward_index"] if pt == "M6" else None)
    ck(sum(1 for r in rows if r["phase"] == "patch") == 48, "48 anchor rows")
    for T in TARGETS:
        for d, h in cells:
            for arm, op, cl, ex in ARMS:
                for src in (("new",) if ex.get("main_only") else SOURCES):
                    name, sk, p = patch_for(arm, op, cl, ex, d, h, T, src)
                    # the same patch fields as the host-new arm, except the target (and the arm name)
                    pt = {"full": "M3", "meanD": "M6", "cs0": "M8", "abc05": "M14"}[arm]
                    pp = {k_: v_ for k_, v_ in wire[arm][(d, h, sk)]["patch"].items() if v_ is not None}
                    ck(dict(p, arm=pp["arm"], target=pp["target"]) == pp, f"benign {name} = {pt} fields but target")
                    built[(name, d, h, sk)] = p
                    add(phase="patch", condition=f"patch_m17_{name}_{sk}", direction="false_veto", scope="all",
                        source_kind=sk, donor=d, host=h, layer=HEAD_LAYER, cross_group=True, target_scene=h,
                        target_arm=T, patch=p, anchor_of=None, bitwise_vs_m3=None, bitwise_vs_m6=None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN) == 2292, f"plan {dict(per_run)}")
    cnt = collections.Counter(r["patch"]["arm"] for r in rows if r["phase"] == "patch")
    ck(cnt == dict({n: 12 for n in ANCHOR_NAME.values()},
                   **{f"{arm}@{T}": (104 if ex.get("main_only") else 208) for T in TARGETS for arm, _o, _c, ex in ARMS}),
       f"rows per arm {dict(cnt)}")
    # repair reference on host new from the pinned rows (all 104 cells), computed here before any M17 forward
    def act(qs):
        q = {x["id"]: x for x in qs}["certificate_action"]
        return q["keys"][max(range(len(q["keys"])), key=lambda i: q["logits"][i])]
    base_new = {x["target_scene"]: act(x["questions"]) for x in m1raw if x["capture"] and x["target_arm"] == "new"
                and x["target_scene"] in gh}
    ck(len(base_new) == 8, "8 host-new baselines in M1")
    rep = {}
    for arm, pt in (("full", "M3"), ("meanD", "M6"), ("cs0", "M8"), ("abc05", "M14")):
        rr = [(d, h) for (d, h, sk), x in pinned[pt].items()
              if sk == "main" and act(x["questions"]) == "reject_conflict" and base_new[h] != "reject_conflict"]
        rep[arm] = {"R": len(rr), "R_h": {hp[:8]: sum(1 for _d, h in rr if h == hp) for hp, _g in hosts}}
    design = {"schema": "JEV_A461_MECH_M17_FALSE_VETO_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M17_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader); L11 = Qwen3.5 full attention",
              "inputs": {k: b for k, (_p, b) in pins.items()} | {"g5v2_questions_blob": g5_full,
                                                                 "corpus_sha256": sa.CORPUS_SHA},
              "selection": {"donors": donors, "hosts": hosts}, "targets": list(TARGETS),
              "arms": [[n, op, cl, ex] for n, op, cl, ex in ARMS], "anchor_names": ANCHOR_NAME,
              "subset_cells": sorted([list(c) for c in sub_cells]), "responsive_hosts": list(RESP),
              "benign_gold": gold, "benign_spans": benign, "host_new_baseline_action": {h[:12]: v for h, v in base_new.items()},
              "repair_reference": rep, "field_marks": FIELD_MARKS, "ab_positions": AB, "c_positions": C_POS,
              "pools": m6["pools"], "plan": PLAN, "total": len(rows), "preregistered_analysis": PREREG,
              "gpu_status": f"0 M17 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m17_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m17_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m17_design.json", "m17_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "repair_reference": rep, "benign_gold":
                      collections.Counter(g_["certificate_action"] for g_ in gold.values()),
                      "manifest_blob": file_blob(out / "m17_manifest.jsonl"),
                      "design_blob": file_blob(out / "m17_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
