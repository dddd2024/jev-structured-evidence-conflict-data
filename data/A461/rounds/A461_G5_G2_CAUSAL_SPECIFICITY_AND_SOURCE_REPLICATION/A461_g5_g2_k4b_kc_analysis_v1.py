#!/usr/bin/env python3
"""kev-4B K-C replication analysis (written before any K-B or K-C result was seen; rules from k4b_kc design).

Readouts: M = conflict margin, A = logit(reject_conflict) - max(accept, wait); C = M > 0; R = A > 0;
JOINT = C and R; dM, dA vs the in-run host capture (bitwise == kev-4B screen row on the GPU backend).
Only cross-group cells (donor group != host group) enter the preregistered counts.
  K-C1 dose specificity: dM_main > dM_dose in >= 75% of cross-group cells AND in a majority of cells for
       >= 10 of the 14 donor groups.
  K-C2 sham specificity: dM_main > dM_sasham in >= 75% of cross-group cells.
  K-C3 joint generality: SPECIFIC_JOINT = main JOINT and neither SA-sham nor dose JOINT; generality iff
       SPECIFIC_JOINT cells come from >= 7 donor groups and no donor group supplies > 30% of them.
  K-C4 recognition: JOINT rate of unrecognized sources <= one quarter of the main-arm JOINT rate.
Always reported: leave-one-donor-group-out for K-C1..K-C3, per-host results, flip rates of every arm.
"""
import argparse, collections, json, statistics as st, sys
from pathlib import Path


def lg(qs, q):
    d = next(x for x in qs if x["id"] == q)
    return dict(zip(d["keys"], d["logits"]))


def M(qs):
    d = lg(qs, "conflicting_vote")
    return d["true"] - d["false"]


def A(qs):
    d = lg(qs, "certificate_action")
    return d["reject_conflict"] - max(d["accept"], d["wait"])


def evaluate(cells, n_groups_total):
    """cells: list of dicts with donor_group, dM{main,sasham,doserand}, joint{...}. Returns K-C1..K-C3."""
    share_dose = sum(c["dM"]["main"] > c["dM"]["doserand"] for c in cells) / len(cells)
    share_sham = sum(c["dM"]["main"] > c["dM"]["sasham"] for c in cells) / len(cells)
    per_g = collections.defaultdict(list)
    for c in cells:
        per_g[c["donor_group"]].append(c["dM"]["main"] > c["dM"]["doserand"])
    groups_majority = sum(sum(v) > len(v) / 2 for v in per_g.values())
    spec = [c for c in cells if c["joint"]["main"] and not c["joint"]["sasham"] and not c["joint"]["doserand"]]
    by_g = collections.Counter(c["donor_group"] for c in spec)
    top = max(by_g.values()) / len(spec) if spec else 0.0
    return {"cells": len(cells), "share_main_gt_dose": round(share_dose, 4), "groups_majority_main_gt_dose": groups_majority,
            "share_main_gt_sham": round(share_sham, 4), "specific_joint": len(spec), "specific_joint_groups": len(by_g),
            "specific_joint_top_group_share": round(top, 4), "specific_joint_by_group": dict(by_g),
            "K_C1": share_dose >= 0.75 and groups_majority >= 10 if n_groups_total == 14 else None,
            "K_C2": share_sham >= 0.75,
            "K_C3": len(by_g) >= 7 and top <= 0.30 if spec else False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = [json.loads(x) for x in (a.run_dir / "raw_native_logits_k4b_kc.jsonl").read_text("utf8").splitlines() if x.strip()]
    assert len(rows) == 417
    des = json.loads(a.design.read_text("utf8"))
    sel = des["selection"]
    group = {s: g for s, g in sel["replication_donors"]}
    group.update({s: g for s, g, _m in sel["replication_hosts"]})
    group.update({s: g for s, g in sel["unrecognized_sources"]})
    base = {r["target_scene"]: r["questions"] for r in rows if r["condition"] == "capture_new_all_rows" and r.get("source_kind") == "host"}
    assert len(base) == 8
    raw = collections.defaultdict(dict)
    unrec = []
    for r in rows:
        if not r["condition"].startswith("patch_kc_"):
            continue
        q, b = r["questions"], base[r["host"]]
        rec = {"dM": M(q) - M(b), "dA": A(q) - A(b), "C": M(q) > 0, "R": A(q) > 0}
        rec["J"] = rec["C"] and rec["R"]
        if r["source_kind"] == "unrecognized":
            unrec.append(dict(rec, cross=r["cross_group"], host=r["host"]))
        else:
            raw[(r["donor"], r["host"], r["cross_group"])][r["source_kind"]] = rec
    cells = []
    for (d, h, cross), arms in raw.items():
        assert set(arms) == {"main", "sasham", "doserand"}
        cells.append({"donor": d[:12], "donor_group": group[d], "host": h[:12], "host_group": group[h], "cross_group": cross,
                      "dM": {k: v["dM"] for k, v in arms.items()}, "dA": {k: v["dA"] for k, v in arms.items()},
                      "joint": {k: v["J"] for k, v in arms.items()}, "C": {k: v["C"] for k, v in arms.items()},
                      "R": {k: v["R"] for k, v in arms.items()}})
    xc = [c for c in cells if c["cross_group"]]
    n_groups = len({c["donor_group"] for c in xc})
    main_eval = evaluate(xc, n_groups)
    main_joint_rate = sum(c["joint"]["main"] for c in xc) / len(xc)
    unrec_x = [u for u in unrec if u["cross"]]
    unrec_rate = sum(u["J"] for u in unrec_x) / len(unrec_x)
    k_c4 = unrec_rate <= main_joint_rate / 4
    logo = {}
    for g in sorted({c["donor_group"] for c in xc}):
        e = evaluate([c for c in xc if c["donor_group"] != g], n_groups - 1)
        logo[g] = {k: e[k] for k in ("share_main_gt_dose", "share_main_gt_sham", "specific_joint", "specific_joint_groups",
                                     "specific_joint_top_group_share")}
    flips = {arm: {"C": sum(c["C"][arm] for c in xc), "R": sum(c["R"][arm] for c in xc), "JOINT": sum(c["joint"][arm] for c in xc)}
             for arm in ("main", "sasham", "doserand")}
    flips["unrecognized"] = {"C": sum(u["C"] for u in unrec_x), "R": sum(u["R"] for u in unrec_x), "JOINT": sum(u["J"] for u in unrec_x),
                             "cells": len(unrec_x)}
    medians = {arm: {"dM": round(st.median(c["dM"][arm] for c in xc), 4), "dA": round(st.median(c["dA"][arm] for c in xc), 4)}
               for arm in ("main", "sasham", "doserand")}
    res = {"schema": "JEV_A461_G5_G2_K4B_KC_ANALYSIS_V1", "layer": des["layers"][0], "cross_group_cells": len(xc),
           "same_group_cells": len(cells) - len(xc), "donor_groups": n_groups,
           "K_C1_dose_specificity": main_eval["K_C1"], "K_C2_sham_specificity": main_eval["K_C2"],
           "K_C3_joint_generality": main_eval["K_C3"], "K_C4_recognition": k_c4,
           "main_eval": main_eval, "joint_rate_main": round(main_joint_rate, 4), "joint_rate_unrecognized": round(unrec_rate, 4),
           "flips_cross_group": flips, "medians_cross_group": medians, "leave_one_donor_group_out": logo,
           "per_host": {h: {"specific_joint": sum(1 for c in xc if c["host"] == h and c["joint"]["main"] and not c["joint"]["sasham"]
                                                  and not c["joint"]["doserand"]),
                            "main_gt_dose": sum(1 for c in xc if c["host"] == h and c["dM"]["main"] > c["dM"]["doserand"])}
                        for h in sorted({c["host"] for c in xc})},
           "cells": cells}
    a.out.mkdir(mode=0o700, exist_ok=False)
    (a.out / "k4b_kc_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("layer", "cross_group_cells", "donor_groups", "K_C1_dose_specificity",
                                         "K_C2_sham_specificity", "K_C3_joint_generality", "K_C4_recognition",
                                         "joint_rate_main", "joint_rate_unrecognized", "flips_cross_group", "medians_cross_group")}
                     | {"main_eval": {k: v for k, v in main_eval.items() if k != "specific_joint_by_group"}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
