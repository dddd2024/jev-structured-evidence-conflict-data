#!/usr/bin/env python3
"""A461-G5-G2 Stage-B preregistered analysis (frozen with the design, before any Stage-B forward).

Implements stage_b_design.json (blob fd2a48b3) "preregistered_analysis" exactly:
  M = logit(true) - logit(false) on the C row.
  restoration cell (donor, host, layer): dM_x = M(host SA patched by x) - M(host SA baseline of that batch);
    SUPPORTIVE iff dM_main > max(dM_sasham, dM_permuted, dM_normrand); FLIP iff M(main) > 0.
  suppression cell: dM_x = M(donor new patched by x) - M(donor new baseline);
    SUPPORTIVE iff dM_main < min(dM_donorside_sasham, dM_permuted, dM_normrand); FLIP iff M(main) < 0.
  confirmatory = layer 11 both directions: supportive cells /16, flips /16, and the specificity claim needs
    supportive cells in all 3 donor groups and all 4 host groups in BOTH directions and no control with as many
    flips as the main arm. Layers 7/15, certificate_action changes and span statistics are exploratory.
"""
import argparse, collections, json, statistics, sys
from pathlib import Path

ARMS = {"restoration": {"main": "patch_restoration_donor_new_to_host_sa", "sasham": "patch_sasham_donor_sa_to_host_sa",
                        "permuted": "patch_permuted_donor_new_to_host_sa", "normrand": "patch_normrand_donor_new_to_host_sa"},
        "suppression": {"main": "patch_suppression_host_new_to_donor_new",
                        "sasham": "patch_donorside_sasham_host_sa_to_donor_new",
                        "permuted": "patch_permuted_host_new_to_donor_new",
                        "normrand": "patch_normrand_host_new_to_donor_new"}}


def action(row):
    a = next(q for q in row["questions"] if q["id"] == "certificate_action")
    return a["keys"][max(range(len(a["logits"])), key=lambda i: a["logits"][i])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = [json.loads(x) for x in a.raw.read_text("utf8").splitlines() if x.strip()]
    design = json.loads(a.design.read_text("utf8"))
    assert len(rows) == 464 and [r["forward_index"] for r in rows] == list(range(1, 465))
    group = {x["scene_sha256"]: x["source_group"] for x in design["donors"] + design["hosts"]}
    base = {}
    for r in rows:
        if r["condition"] in ("baseline_host_sa_unpatched", "baseline_donor_new_unpatched"):
            base[(r["run"], r["target_scene"])] = r
    idx = collections.defaultdict(dict)
    for r in rows:
        if r.get("direction"):
            idx[(r["direction"], r["donor"], r["host"], r["layer"])][r["condition"]] = r
    cells = []
    for (direction, donor, host, layer), conds in sorted(idx.items()):
        tgt = host if direction == "restoration" else donor
        b = base[(next(iter(conds.values()))["run"], tgt)]
        dM = {k: conds[c]["M"] - b["M"] for k, c in ARMS[direction].items()}
        Mx = {k: conds[c]["M"] for k, c in ARMS[direction].items()}
        ctrl = [dM[k] for k in ("sasham", "permuted", "normrand")]
        supportive = dM["main"] > max(ctrl) if direction == "restoration" else dM["main"] < min(ctrl)
        flip = {k: (Mx[k] > 0) if direction == "restoration" else (Mx[k] < 0) for k in Mx}
        cells.append({"direction": direction, "donor": donor[:12], "host": host[:12], "layer": layer,
                      "donor_group": group[donor], "host_group": group[host], "baseline_M": round(b["M"], 6),
                      "dM": {k: round(v, 6) for k, v in dM.items()}, "M": {k: round(v, 6) for k, v in Mx.items()},
                      "supportive": supportive, "flip": flip,
                      "action_baseline": action(b), "action": {k: action(conds[c]) for k, c in ARMS[direction].items()},
                      "span_stats_main": conds[ARMS[direction]["main"]]["span_stats"]})
    assert len(cells) == 2 * 4 * 4 * 3
    summary = {}
    for direction in ("restoration", "suppression"):
        for layer in (7, 11, 15):
            cs = [c for c in cells if c["direction"] == direction and c["layer"] == layer]
            flips = {k: sum(c["flip"][k] for c in cs) for k in ("main", "sasham", "permuted", "normrand")}
            summary[f"{direction}_L{layer}"] = {
                "supportive": sum(c["supportive"] for c in cs), "cells": len(cs), "flips": flips,
                "median_dM": {k: round(statistics.median(c["dM"][k] for c in cs), 4)
                              for k in ("main", "sasham", "permuted", "normrand")},
                "supportive_donor_groups": sorted({c["donor_group"] for c in cs if c["supportive"]}),
                "supportive_host_groups": sorted({c["host_group"] for c in cs if c["supportive"]}),
                "action_changes_main": sum(c["action"]["main"] != c["action_baseline"] for c in cs)}
    n_dg = len({x["source_group"] for x in design["donors"]})
    n_hg = len({x["source_group"] for x in design["hosts"]})

    def specific(direction):
        s = summary[f"{direction}_L11"]
        return (len(s["supportive_donor_groups"]) == n_dg and len(s["supportive_host_groups"]) == n_hg
                and all(s["flips"][k] < s["flips"]["main"] or s["flips"]["main"] == 0 and s["flips"][k] == 0
                        for k in ("sasham", "permuted", "normrand")))
    confirm = {d: specific(d) for d in ("restoration", "suppression")}
    verdict = ("SPECIFIC_CARRIER_L11_BOTH_DIRECTIONS" if all(confirm.values())
               else "ONE_DIRECTION_ONLY_" + [d for d, v in confirm.items() if v][0].upper() if any(confirm.values())
               else "NO_CROSS_GROUP_SPECIFICITY_AT_L11")
    res = {"schema": "JEV_A461_G5_G2_STAGE_B_ANALYSIS_V1", "design_rule_source": "stage_b_design.json",
           "confirmatory_L11": confirm, "verdict": verdict, "summary": summary, "cells": cells}
    a.out.mkdir(mode=0o700, exist_ok=False)
    (a.out / "stage_b_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"verdict": verdict, "confirmatory_L11": confirm,
                      "summary": {k: {kk: v[kk] for kk in ("supportive", "flips", "median_dM")} for k, v in summary.items()}},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
