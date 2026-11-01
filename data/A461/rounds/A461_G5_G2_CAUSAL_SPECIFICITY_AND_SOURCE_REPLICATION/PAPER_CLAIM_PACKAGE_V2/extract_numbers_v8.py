#!/usr/bin/env python3
"""Single source of every G2 number quoted in manuscript v6 and the claim package.

Reads only archived artifacts in the jev repository (analysis JSONs, execution receipts,
quota ledgers) and writes numbers_v6.json with the source file for each block. The v6
generator reads numbers_v6.json and nothing else for G2 values.
"""
import collections, json, statistics as st, sys
from pathlib import Path

REPO = Path(sys.argv[1])
RD = REPO / "research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION"


def J(p):
    return json.loads((RD / p).read_text("utf8"))


def L(p):
    return [json.loads(x) for x in (RD / p).read_text("utf8").splitlines() if x.strip()]


def r2(x):
    return round(x, 2)


out = {"sources": {}}

# ---------- Stage A ----------
pA = "G2_STAGE_A_GPU_R1/G2_STAGE_A_ANALYSIS_R1/stage_a_analysis.json"
a = J(pA)
recA = J("G2_STAGE_A_GPU_R1/G2_STAGE_A_GPU_RUNS/ATTEMPT_R1/execution_receipt.json")
out["sources"]["A"] = pA
out["A"] = {"scenes": a["scenes"], "strict": a["strict_qualified"], "groups": a["qualified_source_groups"],
            "patterns": a["pattern_counts_old_new_SA"], "C_rate": a["C_rate"],
            "median_dM_new_old": a["median_delta_new_minus_old"], "physical": recA["physical_forwards"],
            "batches": [b["physical"] for b in recA["batch_receipts"]],
            "donors": [{"scene": q["scene_sha256"][:12], "group": q["source_group"],
                        "M": {k: r2(v) for k, v in q["M"].items()}, "action": q["action"]} for q in a["qualified"]],
            "n_groups_screened": len(a["groups"])}
out["A"]["missed_rate_new"] = r2(100 * (1 - a["C_rate"]["new"]))

# ---------- Stage B ----------
pB = "G2_STAGE_B_GPU_R1/G2_STAGE_B_ANALYSIS_R1/stage_b_analysis.json"
b = J(pB)
recB = J("G2_STAGE_B_GPU_R1/G2_STAGE_B_GPU_RUNS/ATTEMPT_R1/execution_receipt.json")
out["sources"]["B"] = pB
cellsB = b["cells"]


def beats(cells, d, L_, ctrl):
    cs = [c for c in cells if c["direction"] == d and c["layer"] == L_]
    sgn = 1 if d == "restoration" else -1
    return sum(sgn * (c["dM"]["main"] - c["dM"][ctrl]) > 0 for c in cs)
out["B"] = {"verdict": b["verdict"], "physical": recB["physical_forwards"],
            "summary": {k: {"supportive": v["supportive"], "flips_main": v["flips"]["main"], "flips": v["flips"],
                            "median_dM": {kk: r2(vv) for kk, vv in v["median_dM"].items()}}
                        for k, v in b["summary"].items()},
            "rest_L11_beats": {c: beats(cellsB, "restoration", 11, c) for c in ("sasham", "permuted", "normrand")},
            "supp_L11_beats": {c: beats(cellsB, "suppression", 11, c) for c in ("sasham", "permuted", "normrand")},
            "span_cos_L11_median": r2(st.median(c["span_stats_main"]["cos_mean"] for c in cellsB
                                                if c["direction"] == "restoration" and c["layer"] == 11))}

# ---------- Stage C ----------
pC = "G2_STAGE_C_GPU_R1/G2_STAGE_C_ANALYSIS_R1/stage_c_analysis.json"
c = J(pC)
recC = J("G2_STAGE_C_GPU_R1/G2_STAGE_C_GPU_RUNS/ATTEMPT_R1/execution_receipt.json")
out["sources"]["C"] = pC
h1, h1b, h2, h3 = c["H1_dose_matched_restoration_L11"], c["H1b_dose_matched_suppression_L11"], c["H2_layers"], c["H3_encoding"]
out["C"] = {"physical": recC["physical_forwards"],
            "H1": {"supportive": h1["supportive"], "cells": h1["cells"], "content_specific": h1["content_specific"],
                   "median_gap": r2(h1["median_main_minus_max_dose"]),
                   "median_dM": {k: r2(v) for k, v in h1["median_dM"].items()}},
            "H1b": {"supportive": h1b["supportive"], "main_beats_sasham": h1b["main_beats_sasham"],
                    "median_dM": {k: r2(v) for k, v in h1b["median_dM"].items()}},
            "H2": {d: {str(L_): r2(h2[d][str(L_)]["median_dM_main"]) for L_ in (11, 12, 13, 14)}
                   for d in ("restoration", "suppression")},
            "H2_boundary": h2["boundary_layer"],
            "H3": {"auc_L11": r2(h3["L11"]["auc_FTF_vs_FFF"]), "auc_L12": r2(h3["profile"]["12"]["auc_FTF_vs_FFF"]),
                   "prediction_holds_L11": h3["prediction_holds_L11"],
                   "median_p_FFF_L11": r2(h3["L11"]["median_p"]["FFF"]),
                   "donor_p_L11": [r2(x) for x in h3["L11"]["donor_p_lodo"]],
                   "auc_peak_layer": max(h3["profile"], key=lambda k: h3["profile"][k]["auc_FTF_vs_FFF"]),
                   "auc_peak": r2(max(v["auc_FTF_vs_FFF"] for v in h3["profile"].values()))}}

rawC = L("G2_STAGE_C_GPU_R1/G2_STAGE_C_GPU_RUNS/ATTEMPT_R1/raw_native_logits_stage_c.jsonl")
out["C"]["restoration_L11_flips"] = {arm: sum(1 for r in rawC if r.get("direction") == "restoration" and r["layer"] == 11
                                             and r["condition"] == cond and r["M"] > 0)
                                     for arm, cond in (("main", "patch_restoration_donor_new_to_host_sa"),
                                                       ("dose1", "patch_doserand_s1_to_host_sa"),
                                                       ("dose2", "patch_doserand_s2_to_host_sa"))}

# ---------- Stage D ----------
pD = "G2_STAGE_D_GPU_R1/G2_STAGE_D_ANALYSIS_R1/stage_d_analysis.json"
d = J(pD)
recD = J("G2_STAGE_D_GPU_R1/G2_STAGE_D_GPU_RUNS/ATTEMPT_R1/execution_receipt.json")
out["sources"]["D"] = pD
out["D"] = {"physical": recD["physical_forwards"],
            "D1": {w: {"scenes": v["scenes"], "strict": v["strict"], "patterns": v["patterns"]}
                   for w, v in d["D1"]["by_width"].items()},
            "verdict": d["D2_verdict"],
            "layers": {L_: {"specific_flip": v["specific_flip"], "cells": v["cells"], "flips": v["flips"],
                            "dose_specific": v["dose_specific"],
                            "median_dM": {k: r2(x) for k, x in v["median_dM"].items()},
                            "donor_groups": len(v["specific_flip_donor_groups"]),
                            "host_groups": len(v["specific_flip_host_groups"])} for L_, v in d["D2_layers"].items()},
            "hosts_M_new_range": [r2(min(h["baseline_M"] for h in d["D2_per_host"].values())),
                                  r2(max(h["baseline_M"] for h in d["D2_per_host"].values()))],
            "n_hosts": len(d["D2_per_host"]),
            "n_host_groups": len({h["group"] for h in d["D2_per_host"].values()})}

# ---------- Stage E ----------
pE = "G2_STAGE_E_GPU_R1/G2_STAGE_E_ANALYSIS_R1/stage_e_analysis.json"
e = J(pE)
recE = J("G2_STAGE_E_GPU_R1/G2_STAGE_E_GPU_RUNS/ATTEMPT_R1/execution_receipt.json")
out["sources"]["E"] = pE
cellsE = e["cells"]
hosts_with_spec = sorted({x["host"] for x in cellsE if x["layer"] == 11 and x["scope"] == "action" and x["specific_reject"]})
out["E"] = {"physical": recE["physical_forwards"], "verdict": e["verdict"],
            "reachability_violations": e["reachability_violations_scope_action"],
            "baseline_equals_stage_a": e["baseline_capture_rows_equal_stage_a"],
            "cross_row_max": max(v for v in e["cross_row_max_absdiff"].values() if v is not None),
            "summary": {k: {"specific_reject": v["specific_reject"], "cells": v["cells"], "rejects": v["rejects"],
                            "median_dA": {kk: r2(vv) for kk, vv in v["median_dA"].items()},
                            "c_flips_main": v["c_flips_main"], "dose_specific_A": v["dose_specific_A"],
                            "donor_groups": len(v["specific_reject_donor_groups"]),
                            "host_groups": len(v["specific_reject_host_groups"])} for k, v in e["summary"].items()},
            "hosts_with_specific_reject_L11_action": len(hosts_with_spec),
            "host_A_range": [r2(min(x["baseline_A"] for x in cellsE)), r2(max(x["baseline_A"] for x in cellsE))]}

# ---------- exploratory robustness (not preregistered): leave-one-donor-out, donor concentration ----------
cellsD = d["D2_cells"]
eA = [x for x in cellsE if x["layer"] == 11 and x["scope"] == "action"]
dA11 = [x for x in cellsD if x["layer"] == 11]
cC = [x for x in c["cells"] if x["direction"] == "restoration" and x["layer"] == 11]


def lodo(cells, key):
    res = {}
    for dn in sorted({x["donor"] for x in cells}):
        cs = [x for x in cells if x["donor"] != dn]
        sp = [x for x in cs if x[key]]
        res[dn] = {"specific": len(sp), "cells": len(cs), "donor_groups": len({x["donor_group"] for x in sp}),
                   "host_groups": len({x["host_group"] for x in sp})}
    return res
top = max({x["donor"] for x in eA}, key=lambda dn: sum(x["specific_reject"] for x in eA if x["donor"] == dn))
out["robust"] = {
    "E_lodo": lodo(eA, "specific_reject"), "D_lodo": lodo(dA11, "specific_flip"),
    "C_lodo_min": min(sum(x["supportive_dose"] for x in cC if x["donor"] != dn) for dn in {x["donor"] for x in cC}),
    "top_donor": top, "top_donor_group": next(x["donor_group"] for x in eA if x["donor"] == top),
    "top_donor_E_rejects": sum(x["specific_reject"] for x in eA if x["donor"] == top),
    "top_donor_D_flips": sum(x["specific_flip"] for x in dA11 if x["donor"] == top),
    "median_A_flipped": r2(st.median(x["baseline_A"] for x in eA if x["specific_reject"])),
    "median_A_not_flipped": r2(st.median(x["baseline_A"] for x in eA if not x["specific_reject"]))}
out["robust"]["E_without_top"] = out["robust"]["E_lodo"][top]
out["robust"]["D_without_top"] = out["robust"]["D_lodo"][top]
bdes = J("G2_STAGE_B_FREEZE_R1/stage_b_design.json")
ddes = J("G2_STAGE_D_FREEZE_R1/stage_d_design.json")
out["host_groups_union"] = len({x["source_group"] for x in bdes["hosts"]} | {x["source_group"] for x in ddes["D2_repair"]["hosts"]})
out["screened_total"] = out["A"]["scenes"] + sum(v["scenes"] for v in out["D"]["D1"].values())

# ---------- joint C-and-A repair in the same forward (paper audit 64faaee P0-2) ----------
rawE = L("G2_STAGE_E_GPU_R1/G2_STAGE_E_GPU_RUNS/ATTEMPT_R1/raw_native_logits_stage_e.jsonl")
desE = J("G2_STAGE_E_FREEZE_R1/stage_e_design.json")
dgE = {x["scene_sha256"]: x["source_group"] for x in desE["donors"]}


def lgq(r, q):
    d = next(x for x in r["questions"] if x["id"] == q)
    return dict(zip(d["keys"], d["logits"]))


def Cq(r):
    d = lgq(r, "conflicting_vote")
    return d["true"] > d["false"]


def Rq(r):
    d = lgq(r, "certificate_action")
    return d["reject_conflict"] > max(d["accept"], d["wait"])
joint = {}
for L_ in (11, 12):
    for arm in ("main", "sasham", "doserand"):
        cs = [r for r in rawE if r.get("scope") == "all" and r.get("layer") == L_ and r["condition"] == f"patch_repair_{arm}_all"]
        jj = [r for r in cs if Cq(r) and Rq(r)]
        joint[f"L{L_}_{arm}"] = {"cells": len(cs), "C": sum(map(Cq, cs)), "R": sum(map(Rq, cs)), "JOINT": len(jj),
                                 "by_donor_group": dict(collections.Counter(dgE[r["donor"]].replace("twins_streamlet:", "") for r in jj)),
                                 "host_groups": len({x["source_group"] for x in desE["hosts"] if x["scene_sha256"] in {r["host"] for r in jj}})}
mainL11 = [r for r in rawE if r.get("scope") == "all" and r.get("layer") == 11 and r["condition"] == "patch_repair_main_all"]
joint["L11_main_lodo"] = {dgE[d].replace("twins_streamlet:", "") + ":" + d[:8]: sum(1 for r in mainL11 if r["donor"] != d and Cq(r) and Rq(r))
                          for d in sorted({r["donor"] for r in mainL11})}
out["joint"] = joint

# ---------- Stage F: semantic controls (SecJev) ----------
f = J("G2_STAGE_F_GPU_R1/G2_STAGE_F_ANALYSIS_R1/stage_f_analysis.json")
recF = J("G2_STAGE_F_GPU_R1/G2_STAGE_F_GPU_RUNS/ATTEMPT_R1/execution_receipt.json")
out["F"] = {"physical": recF["physical_forwards"], "joint": f["joint"],
            "cells": {k: v["cells"] for k, v in f["by_kind"].items()},
            "by_kind": {k: {kk: v[kk] for kk in ("C", "R", "JOINT")} for k, v in f["by_kind"].items()},
            "H_F1": f["H_F1_content_beyond_class"], "H_F2": f["H_F2_recognition_matters"], "H_F3": f["H_F3_source_diversity"],
            "n_ttt_groups": len(f["by_source_group"]["ttt_new"]), "n_fff_groups": len(f["by_source_group"]["fff_new"]),
            "host_baselines_ok": f["host_baselines_neither_C_nor_R"]}

# ---------- kev-4B screen, K-B, K-C ----------
k4 = J("G2_K4B_STAGE_A_GPU_R1/G2_K4B_STAGE_A_ANALYSIS_R1/stage_a_analysis.json")
rec4 = J("G2_K4B_STAGE_A_GPU_R1/G2_K4B_STAGE_A_GPU_RUNS/ATTEMPT_R1/execution_receipt.json")
k4per = {x["scene_sha256"]: x for x in L("G2_K4B_STAGE_A_GPU_R1/G2_K4B_STAGE_A_ANALYSIS_R1/stage_a_per_scene.jsonl")}
saper = {x["scene_sha256"]: x for x in L("G2_STAGE_A_GPU_R1/G2_STAGE_A_ANALYSIS_R1/stage_a_per_scene.jsonl")}
out["K4"] = {"physical": rec4["physical_forwards"], "strict": k4["strict_qualified"], "groups": len(k4["qualified_source_groups"]),
             "C_rate": k4["C_rate"], "median_dM_new_old": r2(k4["median_delta_new_minus_old"]),
             "median_dM_SA_old": r2(st.median(x["M"]["SA"] - x["M"]["old"] for x in k4per.values())),
             "patterns": k4["pattern_counts_old_new_SA"], "reject_new": k4["action_counts"]["new"].get("reject_conflict", 0),
             "missed_rate_new": r2(100 * (1 - k4["C_rate"]["new"])),
             "load_gb": round(rec4["kev4b_load"]["cuda_max_memory_allocated_after_load"] / 1e9, 1),
             "secjev_missed_now_donor": sum(1 for s in saper if saper[s]["pattern"] == "FFF" and k4per[s]["strict_qualified"]),
             "secjev_donors_also_k4b": sum(1 for s in saper if saper[s]["strict_qualified"] and k4per[s]["strict_qualified"])}
kb = J("G2_K4B_KB_GPU_R1/G2_K4B_KB_ANALYSIS_R1/k4b_kb_analysis.json")
recKB = J("G2_K4B_KB_GPU_R1/G2_K4B_KB_GPU_RUNS/ATTEMPT_R1/execution_receipt.json")
out["KB"] = {"physical": recKB["physical_forwards"], "window": kb["window_layer"],
             "profile": {L_: {"gap": r2(v["median_gap"]), "share": round(100 * v["share_main_gt_dose"])} for L_, v in kb["profile"].items()}}
kc = J("G2_K4B_KC_GPU_R1/G2_K4B_KC_ANALYSIS_R1/k4b_kc_analysis.json")
recKC = J("G2_K4B_KC_GPU_R1/G2_K4B_KC_GPU_RUNS/ATTEMPT_R1/execution_receipt.json")
me = kc["main_eval"]
logo = kc["leave_one_donor_group_out"]
out["KC"] = {"physical": recKC["physical_forwards"], "layer": kc["layer"], "cells": kc["cross_group_cells"], "groups": kc["donor_groups"],
             "K1": kc["K_C1_dose_specificity"], "K2": kc["K_C2_sham_specificity"], "K3": kc["K_C3_joint_generality"], "K4": kc["K_C4_recognition"],
             "share_dose": round(100 * me["share_main_gt_dose"], 1), "groups_majority": me["groups_majority_main_gt_dose"],
             "share_sham": round(100 * me["share_main_gt_sham"], 1), "spec_joint": me["specific_joint"],
             "spec_joint_groups": me["specific_joint_groups"], "top_share": round(100 * me["specific_joint_top_group_share"], 1),
             "joint_rate_main": round(100 * kc["joint_rate_main"], 1), "unrec": kc["flips_cross_group"]["unrecognized"],
             "flips": kc["flips_cross_group"], "medians": kc["medians_cross_group"],
             "logo_min": min(v["specific_joint"] for v in logo.values()), "logo_max": max(v["specific_joint"] for v in logo.values()),
             "logo_min_groups": min(v["specific_joint_groups"] for v in logo.values()),
             "hosts_repaired": sum(1 for v in kc["per_host"].values() if v["specific_joint"] > 0), "hosts": len(kc["per_host"])}

# ---------- GPU ledger across G2 (quota ledgers are the authority) ----------
led = {}
for stage, path in (("A", "G2_STAGE_A_GPU_R1/G2_STAGE_A_QUOTA_LEDGER/A461_G5_G2_STAGE_A_GPU_20261027_R1/ledger.jsonl"),
                    ("B", "G2_STAGE_B_GPU_R1/G2_STAGE_B_QUOTA_LEDGER/A461_G5_G2_STAGE_B_GPU_20261027_R1/ledger.jsonl"),
                    ("C", "G2_STAGE_C_GPU_R1/G2_STAGE_C_QUOTA_LEDGER/A461_G5_G2_STAGE_C_GPU_20261027_R1/ledger.jsonl"),
                    ("D", "G2_STAGE_D_GPU_R1/G2_STAGE_D_QUOTA_LEDGER/A461_G5_G2_STAGE_D_GPU_20261027_R1/ledger.jsonl"),
                    ("E", "G2_STAGE_E_GPU_R1/G2_STAGE_E_QUOTA_LEDGER/A461_G5_G2_STAGE_E_GPU_20261027_R1/ledger.jsonl"),
                    ("F", "G2_STAGE_F_GPU_R1/G2_STAGE_F_QUOTA_LEDGER/A461_G5_G2_STAGE_F_GPU_20261027_R1/ledger.jsonl"),
                    ("K4", "G2_K4B_STAGE_A_GPU_R1/G2_K4B_STAGE_A_QUOTA_LEDGER/A461_G5_G2_K4B_STAGE_A_GPU_20261027_R1/ledger.jsonl"),
                    ("KB", "G2_K4B_KB_GPU_R1/G2_K4B_KB_QUOTA_LEDGER/A461_G5_G2_K4B_KB_GPU_20261027_R1/ledger.jsonl"),
                    ("KC", "G2_K4B_KC_GPU_R1/G2_K4B_KC_QUOTA_LEDGER/A461_G5_G2_K4B_KC_GPU_20261027_R1/ledger.jsonl")):
    ev = L(path)
    led[stage] = {"reserved": sum(1 for x in ev if x["event"] == "reserve"),
                  "unreserved": sum(int(x["count"]) for x in ev if x["event"] == "unreserved_physical"),
                  "attempts": sum(1 for x in ev if x["event"] == "attempt_open")}
out["ledger"] = led
out["ledger_total_g2"] = sum(v["reserved"] + v["unreserved"] for v in led.values())
out["ledger_prior_line"] = 409  # v5.1/v5.2 Section 7: G1 103 + G3 109 + G4 56 + G5 112 + pilot 28 + 1 fail-closed
assert all(led[s]["reserved"] == out[s]["physical"] for s in ("A", "B", "C", "D", "E", "F", "K4", "KB", "KC"))
out["ledger_total_secjev_g2"] = sum(led[s]["reserved"] + led[s]["unreserved"] for s in ("A", "B", "C", "D", "E", "F"))
out["ledger_total_k4b"] = sum(led[s]["reserved"] + led[s]["unreserved"] for s in ("K4", "KB", "KC"))
(Path(sys.argv[2])).write_text(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf8")
print(json.dumps({"A": {k: out["A"][k] for k in ("strict", "scenes", "missed_rate_new")}, "B": out["B"]["verdict"],
                  "C_H1": out["C"]["H1"], "D_L11": out["D"]["layers"]["11"], "E_L11a": out["E"]["summary"]["L11_action"],
                  "ledger_g2": out["ledger_total_g2"]}, indent=1))
