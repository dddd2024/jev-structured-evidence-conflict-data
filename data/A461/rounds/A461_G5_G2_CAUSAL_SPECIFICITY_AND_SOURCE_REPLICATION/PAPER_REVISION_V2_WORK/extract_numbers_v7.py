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

# ---------- GPU ledger across G2 (quota ledgers are the authority) ----------
led = {}
for stage, path in (("A", "G2_STAGE_A_GPU_R1/G2_STAGE_A_QUOTA_LEDGER/A461_G5_G2_STAGE_A_GPU_20261027_R1/ledger.jsonl"),
                    ("B", "G2_STAGE_B_GPU_R1/G2_STAGE_B_QUOTA_LEDGER/A461_G5_G2_STAGE_B_GPU_20261027_R1/ledger.jsonl"),
                    ("C", "G2_STAGE_C_GPU_R1/G2_STAGE_C_QUOTA_LEDGER/A461_G5_G2_STAGE_C_GPU_20261027_R1/ledger.jsonl"),
                    ("D", "G2_STAGE_D_GPU_R1/G2_STAGE_D_QUOTA_LEDGER/A461_G5_G2_STAGE_D_GPU_20261027_R1/ledger.jsonl"),
                    ("E", "G2_STAGE_E_GPU_R1/G2_STAGE_E_QUOTA_LEDGER/A461_G5_G2_STAGE_E_GPU_20261027_R1/ledger.jsonl")):
    ev = L(path)
    led[stage] = {"reserved": sum(1 for x in ev if x["event"] == "reserve"),
                  "unreserved": sum(int(x["count"]) for x in ev if x["event"] == "unreserved_physical"),
                  "attempts": sum(1 for x in ev if x["event"] == "attempt_open")}
out["ledger"] = led
out["ledger_total_g2"] = sum(v["reserved"] + v["unreserved"] for v in led.values())
out["ledger_prior_line"] = 409  # v5.1/v5.2 Section 7: G1 103 + G3 109 + G4 56 + G5 112 + pilot 28 + 1 fail-closed
assert all(led[s]["reserved"] == out[s]["physical"] for s in "ABCDE")
(Path(sys.argv[2])).write_text(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf8")
print(json.dumps({"A": {k: out["A"][k] for k in ("strict", "scenes", "missed_rate_new")}, "B": out["B"]["verdict"],
                  "C_H1": out["C"]["H1"], "D_L11": out["D"]["layers"]["11"], "E_L11a": out["E"]["summary"]["L11_action"],
                  "ledger_g2": out["ledger_total_g2"]}, indent=1))
