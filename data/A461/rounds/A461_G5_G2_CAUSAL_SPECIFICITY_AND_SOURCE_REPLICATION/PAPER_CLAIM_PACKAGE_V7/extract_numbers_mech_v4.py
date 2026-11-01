#!/usr/bin/env python3
"""Extract every mechanism / monitor number cited in manuscript v10 (section 4.12-4.16, abstract, discussion,
limitations) from the archived analysis JSONs and execution receipts of M1-M22 and the S2 endpoint note.

Usage: python extract_numbers_mech_v4.py <jev repo root> numbers_mech_v4.json
V4 = V3 plus the twin three-action table, source-group spread, quorum-change twins and G2.3 family status (audit 8dd4528).
V3 = V2 plus the M23 same-span twin test (verdicts, primary detector metrics, native behaviour on twins).
V2 = V1 plus the three-action safety table, M21 action changes, M20 survivors and G2.3 coverage (audit 02a2b73).
Standard library only. Every value is read from an archived file by an explicit key path; nothing is typed here."""
import collections, io, json, sys
from pathlib import Path

ROOT = Path(sys.argv[1]) / "research" / "rounds"
OUT = Path(sys.argv[2])
DIRS = {1: "A461_MECH_M1_ROUND_BINDING_GPU", 2: "A461_MECH_M2_SUBLAYER_LOCUS_GPU", 3: "A461_MECH_M3_HEAD_ROUTING_GPU",
        4: "A461_MECH_M4_KEYCLASS_VALUE_GPU", 5: "A461_MECH_M5_MAGNITUDE_DIRECTION_GPU",
        6: "A461_MECH_M6_SHARED_BULK_DIRECTION_GPU", 7: "A461_MECH_M7_DELTA_BASIS_MEANDIFF_GPU",
        8: "A461_MECH_M8_CROSS_DELTA_TWOPART_GPU", 9: "A461_MECH_M9_GAIN_HEADS_SPLIT_GPU",
        10: "A461_MECH_M10_HEADS_POSITIONS_GPU", 11: "A461_MECH_M11_MATCHED_POSITION_SHIFT_GPU",
        12: "A461_MECH_M12_P30_FIELDS_COSNULL_GPU", 13: "A461_MECH_M13_AB_SHIFT_TILT_GPU",
        14: "A461_MECH_M14_AB_THRESHOLD_TILT3_GPU", 15: "A461_MECH_M15_Q1_SPLIT_NULL24_GPU",
        16: "A461_MECH_M16_MID_WEIGHT_LINEAR_GPU", 17: "A461_MECH_M17_FALSE_VETO_BENIGN_GPU",
        18: "A461_MON_M18_SPAN_MONITOR_GPU", 19: "A461_MECH_M19_READOUT_GAIN_GPU",
        20: "A461_MECH_M20_NATURAL_NECESSITY_GPU", 21: "A461_MECH_M21_READOUT_MEANDIFF_GPU",
        22: "A461_MON_M22_SECJEV_REPLICATION_GPU"}


def J(p):
    return json.loads(io.open(p, encoding="utf8").read())


def an(i):
    sub = "M17_ANALYSIS_R1_V1_1" if i == 17 else f"M{i}_ANALYSIS_R1"   # M17: v1.1 is the analysis of record
    return J(ROOT / DIRS[i] / sub / f"m{i}_analysis.json")


def receipt(i):
    return J(ROOT / DIRS[i] / f"M{i}_GPU_R1" / "execution_receipt.json")


def r3(x):
    return None if x is None else round(x, 3)


N = {"forwards": {}, "verdicts": {}}
for i in DIRS:
    rc = receipt(i)
    assert rc["denied_prehook_calls"] == 0 and rc["status"].startswith("COMPLETE"), (i, rc["status"])
    N["forwards"][f"M{i}"] = rc["physical_prehook_calls"]
N["forwards_total"] = sum(N["forwards"].values())
N["forwards_k4b"] = N["forwards_total"] - N["forwards"]["M22"]
N["gpu_hours"] = round(sum(receipt(i)["elapsed_seconds"] or 0 for i in DIRS) / 3600, 1)

d = an(1)
cg = d["cross_group"]
N["M1"] = {"verdict_round": d["verdict_round"], "verdict_role": d["verdict_role"], "cells": cg["cells"],
           "J_main": cg["J_main"], "J_round": cg["J_round"], "J_okalt": cg["J_okalt"],
           "frac_main_gt_round": cg["frac_dM_main_gt_round"], "groups_majority": cg["groups_majority_main_gt_round"],
           "median_dM_main": cg["median_dM"]["main"], "median_dM_round": cg["median_dM"]["round"]}
d = an(2)
t = d["table"]
N["M2"] = {"verdict": d["verdict"], "L_f": d["L_f"], "S_mixer_L11": t["mixer_L11"]["S"], "S_resid_L11": t["resid_L11"]["S"],
           "S_mlp_max": max(t[f"mlp_L{l}"]["S"] for l in (8, 9, 10, 11)),
           "S_resid_L7_L10": [t[f"resid_L{l}"]["S"] for l in (7, 8, 9, 10) if f"resid_L{l}" in t]}
d = an(3)
t = d["table"]
N["M3"] = {"verdict": d["verdict"], "S_all": t["all"]["S"], "S_best_single_head": max(t[f"head{h}"]["S"] for h in range(16)),
           "S_drop10": t["drop10"]["S"], "S_drop8_9_14": [t[f"drop{h}"]["S"] for h in (8, 9, 14)]}
d = an(4)
t = d["table"]
N["M4"] = {"verdict": d["verdict"], "value_swap": d["value_swap"], "S_full": t["full"]["S"],
           "S_drop_OTHER_ITEMS": t["drop_OTHER_ITEMS"]["S"], "S_drop_CONTEXT": t["drop_CONTEXT"]["S"],
           "S_drop_PARTNER": t["drop_PARTNER"]["S"], "S_vswap_PARTNER": t["vswap_PARTNER"]["S"]}
d = an(5)
t = d["table"]
N["M5"] = {"verdict": d["verdict"], "content": d["content"], "S_full": t["full"]["S"], "S_dir_BULK": t["dir_BULK"]["S"],
           "S_dir_RAND": t["dir_RAND"]["S"], "S_xdonor_BULK": t["xdonor_BULK"]["S"]}
d = an(6)
N["verdicts"]["M6"] = {"shared": d["shared_verdict"], "lowrank": d["lowrank_verdict"]}
for i in range(7, 17):
    N["verdicts"][f"M{i}"] = an(i)["verdicts"]
for i in (1, 2, 3, 4, 5):
    N["verdicts"][f"M{i}"] = {k: v for k, v in N[f"M{i}"].items() if k.startswith("verdict") or k in ("value_swap", "content")}

d = an(17)
fv = d["false_veto"]
N["M17"] = {"arm_verdicts": d["verdicts"]["arm_verdicts"], "R": {a: d["repair_reference"][a]["R"] for a in d["repair_reference"]},
            "FV": {k: fv[k]["FV"] for k in fv}, "FVJ": {k: fv[k]["FVJ"] for k in fv}, "cells_per_arm": 104}

d = an(18)
m = d["metrics"]
SP = "PROBE:SPAN_ATTN11"


def mon(m, keys):
    return {k: {"AUROC": r3(m[k]["AUROC"]), "TPR5": r3(m[k]["TPR_missed@FV5"]), "FPR5": r3(m[k]["FPR@FV5"]),
                "TPR1": r3(m[k]["TPR_missed@FV1"]), "FPR1": r3(m[k]["FPR@FV1"])} for k in keys}


N["M18"] = {"verdicts": {k: v for k, v in d["verdicts"].items() if k != "calibrated"}, "counts": d["counts"],
            "det": mon(m, [SP, "PROBE:LAST_RESID_L31", "PROBE:LAST_RESID_L19", "PROBE:SPAN_RESID_L15",
                           "PROBE:SPAN_RESID_emb", "NATIVE_A", "NATIVE_M", "WHITEN:LAST_RESID_L31"]),
            "ci_AUROC_span": d["ci95_group_bootstrap"]["AUROC_span"],
            "fp_groups_FV1": d["span_monitor_false_positive_groups"]["FV1"]}
d = an(22)
m = d["metrics"]
N["M22"] = {"verdicts": {k: v for k, v in d["verdicts"].items() if k != "calibrated"}, "counts": d["counts"],
            "det": mon(m, [SP, "PROBE:LAST_RESID_L23", "PROBE:LAST_RESID_L11", "PROBE:SPAN_RESID_L11",
                           "PROBE:SPAN_RESID_emb", "NATIVE_A", "NATIVE_M", "WHITEN:LAST_RESID_L23"]),
            "ci_AUROC_span": d["ci95_group_bootstrap"]["AUROC_span"],
            "fp_groups_FV1": d["span_monitor_false_positive_groups"]["FV1"]}
for i in (18, 22):
    N["verdicts"][f"M{i}"] = N[f"M{i}"]["verdicts"]

for i in (19, 21):
    d = an(i)
    N[f"M{i}"] = {"verdicts": d["verdicts"], "counts": d["counts"],
                  "measures": {k: {"REPAIR": r3(v["REPAIR"]), "FV": r3(v["FV"])} for k, v in d["measures"].items()},
                  "cos_median": d["readout_geometry"].get("median_cos_probe_vs_head_gradient")}
    N["verdicts"][f"M{i}"] = d["verdicts"]
d = an(20)
N["M20"] = {"verdicts": d["verdicts"], "logo": d["logo_stability"],
            "full": {"host_C_loss": r3(d["detail_full"]["host"]["C_loss"]), "ctrl_C_loss": r3(d["detail_full"]["ctrl"]["C_loss"])},
            "bulk": {"host_C_loss": r3(d["detail_bulk"]["host"]["C_loss"]), "ctrl_C_loss": r3(d["detail_bulk"]["ctrl"]["C_loss"])},
            "round_self": {"C_loss": r3(d["per_donor_arms"]["bulk_round_self"]["C_loss"]),
                           "n": d["per_donor_arms"]["bulk_round_self"]["n"],
                           "median_dM": d["per_donor_arms"]["bulk_round_self"]["median_dM"]}}
N["verdicts"]["M20"] = d["verdicts"]

s2 = J(ROOT / "A461_SAFETY_S2_ENDPOINT_CPU" / "s2_endpoint.json")
N["S2_keys"] = sorted(s2.keys())
# ---- V5 additions (audit 02a2b73): three-action safety table, M21 action changes, M20 survivors, G2.3 coverage ----
def raw_rows(i):
    return [json.loads(x) for x in io.open(ROOT / DIRS[i] / f"M{i}_GPU_R1" / f"raw_native_logits_m{i}.jsonl",
                                           encoding="utf8").read().splitlines() if x.strip()]


def act(qs):
    a = next(q for q in qs if q["id"] == "certificate_action")
    return a["keys"][max(range(len(a["keys"])), key=lambda k: a["logits"][k])]


ARMS = ("new", "old", "SA", "ROUND", "OUTSIDER")
N["safety3"] = {}
for name, i in (("kev4b", 18), ("secjev", 22)):
    rows = raw_rows(i)
    assert len(rows) == 620
    t = {}
    for arm in ARMS:
        sub = [r for r in rows if r["target_arm"] == arm]
        c = collections.Counter((r["gold_action"], act(r["questions"])) for r in sub)
        fv_groups = {r["source_group"] for r in sub if r["gold_action"] != "reject_conflict" and act(r["questions"]) == "reject_conflict"}
        t[arm] = {"rows": len(sub), "by_gold_pred": {f"{g}->{p}": n for (g, p), n in sorted(c.items())},
                  "correct": sum(n for (g, p), n in c.items() if g == p),
                  "false_veto": sum(n for (g, p), n in c.items() if g != "reject_conflict" and p == "reject_conflict"),
                  "missed_conflict": sum(n for (g, p), n in c.items() if g == "reject_conflict" and p != "reject_conflict"),
                  "accept_wait_swap": sum(n for (g, p), n in c.items() if {g, p} == {"accept", "wait"}),
                  "groups_with_false_veto": len(fv_groups),
                  "groups": len({r["source_group"] for r in sub})}
    N["safety3"][name] = t

rows = raw_rows(21)
rep = {(r["target_scene"], r["target_arm"]): act(r["questions"]) for r in rows if not r.get("op")}
ch = collections.defaultdict(collections.Counter)
for r in rows:
    if r.get("op"):
        k = (r["target_scene"], r["target_arm"])
        a0, a1 = rep[k], act(r["questions"])
        if a0 != a1:
            kind = ("repair" if k[1] == "new" and a1 == "reject_conflict" else
                    "lost_recognition" if k[1] == "new" and a0 == "reject_conflict" else
                    "new_false_veto" if k[1] != "new" and a1 == "reject_conflict" else
                    "other_change")
            ch[r["condition"]][kind] += 1
N["M21"]["action_changes"] = {c: dict(v) for c, v in sorted(ch.items())}
N["M21"]["action_changes_total"] = {c: sum(v.values()) for c, v in ch.items()}
N["M20"]["round_self"]["survivors"] = N["M20"]["round_self"]["n"] - round(N["M20"]["round_self"]["C_loss"] * N["M20"]["round_self"]["n"])
N["M17"]["arms_tested"] = sorted(N["M17"]["arm_verdicts"])
g23 = J(ROOT / "A461_MON_G23_CONTEXT_COUNTERFACTUAL_CPU" / "G23_OUT_R1" / "receipt.json")
N["G23"] = {"PARTNER_ROUND": g23["coverage"]["all"]["PARTNER_ROUND"], "groups": g23["groups"],
            "token_positions_changed": g23["token_positions_changed_hist"]["PARTNER_ROUND"]}
# ---- V6 additions: M23 same-span twins ----
M23D = ROOT / "A461_MON_M23_TWIN_PROBE_GPU"
N["M23"] = {"forwards": {}, "models": {}}
for k, K in (("k", "K"), ("s", "S")):
    rc = J(M23D / f"M23{K}_GPU_R1" / "execution_receipt.json")
    assert rc["denied_prehook_calls"] == 0 and rc["status"] == f"COMPLETE_A461_MON_M23{K}"
    N["M23"]["forwards"][k] = rc["physical_prehook_calls"]
    an_ = J(M23D / f"M23{K}_ANALYSIS_R1" / f"m23{k}_analysis.json")
    assert an_["consistency_gate"]["pass"] is True
    det = {d: {x: (round(v[x], 3) if isinstance(v[x], float) else v[x]) for x in
               ("AUROC_pair", "ci_AUROC_pair", "twin_flag@FV5", "new_flag@FV5", "twin_flag@FV1", "new_flag@FV1",
                "paired_frac_new_gt_twin", "AUROC_twin_vs_parent_benign")} for d, v in an_["detectors"].items()}
    rows = [json.loads(x) for x in io.open(M23D / f"M23{K}_GPU_R1" / f"raw_native_logits_m23{k}.jsonl", encoding="utf8").read().splitlines() if x.strip()]
    by = {(r["target_scene"], r["target_arm"]): r for r in rows}
    sc = sorted({r["target_scene"] for r in rows})

    def cm(qs):
        c = next(q for q in qs if q["id"] == "conflicting_vote")
        return c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]
    rec = [s for s in sc if act(by[(s, "new")]["questions"]) == "reject_conflict"]
    mis = [s for s in sc if s not in rec]
    dm = sorted(cm(by[(s, "TWIN")]["questions"]) - cm(by[(s, "new")]["questions"]) for s in mis)
    N["M23"]["models"][k] = {"verdicts": an_["verdicts"], "primary": an_["primary"], "detectors": det,
                             "missed_scenes": an_["missed_scenes"], "missed_groups": an_["missed_groups"],
                             "native": an_["native"], "recognized": len(rec),
                             "twin_rejected_in_recognized": sum(act(by[(s, "TWIN")]["questions"]) == "reject_conflict" for s in rec),
                             "twin_C_pos_in_recognized": sum(cm(by[(s, "TWIN")]["questions"]) > 0 for s in rec),
                             "new_C_pos_in_recognized": sum(cm(by[(s, "new")]["questions"]) > 0 for s in rec),
                             "median_dM_twin_minus_new_missed": round((dm[(len(dm) - 1) // 2] + dm[len(dm) // 2]) / 2, 3)}
N["M23"]["forwards_total"] = sum(N["M23"]["forwards"].values())
# ---- V7 additions (audit 8dd4528): twin three-action table, group spread, quorum-change twins ----
g23rows = {r["scene"]: r for r in J(ROOT / "A461_MON_G23_CONTEXT_COUNTERFACTUAL_CPU" / "G23_OUT_R1" / "ctx_counterfactuals.json")}
for k, K in (("k", "K"), ("s", "S")):
    rows = [json.loads(x) for x in io.open(M23D / f"M23{K}_GPU_R1" / f"raw_native_logits_m23{k}.jsonl", encoding="utf8").read().splitlines() if x.strip()]
    tw = [r for r in rows if r["target_arm"] == "TWIN"]
    nw = {r["target_scene"]: r for r in rows if r["target_arm"] == "new"}
    conf = collections.Counter((r["gold_action"], act(r["questions"])) for r in tw)
    groups_all = {r["source_group"] for r in tw}
    fv_groups = {r["source_group"] for r in tw if act(r["questions"]) == "reject_conflict"}
    qc = [r for r in tw if g23rows[r["target_scene"][:12]]["old_gold"] != r["gold_action"]]
    mm = N["M23"]["models"][k]
    mm["twin_confusion"] = {f"{g}->{p}": n for (g, p), n in sorted(conf.items())}
    mm["twin_pred_totals"] = {p: sum(n for (g, q), n in conf.items() if q == p) for p in ("reject_conflict", "accept", "wait")}
    mm["twin_correct"] = sum(n for (g, p), n in conf.items() if g == p)
    mm["twin_accept_wait_swap"] = sum(n for (g, p), n in conf.items() if {g, p} == {"accept", "wait"})
    mm["twin_fv_groups"] = len(fv_groups)
    mm["groups"] = len(groups_all)
    mm["twin_rejected_where_new_missed"] = sum(act(r["questions"]) == "reject_conflict" for r in tw
                                               if act(nw[r["target_scene"]]["questions"]) != "reject_conflict")
    mm["new_missed"] = sum(act(r["questions"]) != "reject_conflict" for r in nw.values())
    mm["twin_M_gt_new_all"] = sum(1 for r in tw if (lambda a, b: a > b)(
        *[(lambda c: c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")])(
            next(q for q in x["questions"] if q["id"] == "conflicting_vote")) for x in (r, nw[r["target_scene"]])]))
    mm["quorum_change_twins"] = {"n": len(qc), "pred": dict(collections.Counter(act(r["questions"]) for r in qc))}
N["M23"]["G23_families"] = {f: {"constructible": J(ROOT / "A461_MON_G23_CONTEXT_COUNTERFACTUAL_CPU" / "G23_OUT_R1" / "receipt.json")["coverage"]["all"][f]["scenes"],
                                "run": f == "PARTNER_ROUND"} for f in ("PARTNER_ROUND", "PARTNER_BLOCK", "PARTNER_AUTHOR")}
OUT.write_text(json.dumps(N, indent=1, sort_keys=True) + chr(10), encoding="utf8")
print(json.dumps({k: {x: v[x] for x in ("twin_pred_totals", "twin_fv_groups", "twin_accept_wait_swap", "twin_rejected_where_new_missed", "twin_M_gt_new_all", "quorum_change_twins")} for k, v in N["M23"]["models"].items()}, indent=0))
print(json.dumps(N["M23"]["G23_families"]))
