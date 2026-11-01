#!/usr/bin/env python3
"""A461-MECH-M1 R1 analysis: applies the rules frozen in m1_design.json (written before the GPU run)."""
import argparse, collections, json, statistics, sys
from pathlib import Path


def ra(qs):
    q = {x["id"]: x for x in qs}
    c, a = q["conflicting_vote"], q["certificate_action"]
    M = c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]
    L = dict(zip(a["keys"], a["logits"]))
    A = L["reject_conflict"] - max(L["accept"], L["wait"])
    return M, A, (M > 0 and A > 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    design = json.loads(a.design.read_text("utf8"))
    raw = [json.loads(x) for x in a.raw.read_text("utf8").splitlines() if x.strip()]
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    grp = dict(design["selection"]["donors"]) | dict(design["selection"]["hosts"])
    cap = {(x["target_scene"], x["target_arm"]): ra(x["questions"]) for x in raw if x["capture"]}
    by = collections.defaultdict(dict)
    for x in raw:
        if x["patch"]:
            by[(x["donor"], x["host"])][x["source_kind"]] = ra(x["questions"])
    cells = []
    for (d, h), arms in sorted(by.items()):
        base_M = cap[(h, "new")][0]
        cells.append({"donor": d, "host": h, "dg": grp[d], "hg": grp[h], "cross": grp[d] != grp[h],
                      **{f"J_{k}": v[2] for k, v in arms.items()},
                      **{f"dM_{k}": v[0] - base_M for k, v in arms.items()},
                      **{f"A_{k}": v[1] for k, v in arms.items()}})
    X = [c for c in cells if c["cross"]]
    assert len(X) == 104, len(X)

    def count(cs, k):
        return sum(c[f"J_{k}"] for c in cs)

    def frac_gt(cs, k1, k2):
        return sum(c[f"dM_{k1}"] > c[f"dM_{k2}"] for c in cs) / len(cs)

    def groups_majority(cs, k1, k2):
        g = collections.defaultdict(list)
        for c in cs:
            g[c["dg"]].append(c[f"dM_{k1}"] > c[f"dM_{k2}"])
        return sum(sum(v) * 2 > len(v) for v in g.values())

    def summary(cs):
        Jm, Jr, Jo, Jd = (count(cs, k) for k in ("main", "round", "okalt", "doserand_r"))
        return {"cells": len(cs), "J_main": Jm, "J_round": Jr, "J_okalt": Jo, "J_doserand_r": Jd,
                "J_round_not_dose": sum(c["J_round"] and not c["J_doserand_r"] for c in cs),
                "frac_dM_main_gt_round": round(frac_gt(cs, "main", "round"), 4),
                "groups_majority_main_gt_round": groups_majority(cs, "main", "round"),
                "frac_dM_round_gt_dose": round(frac_gt(cs, "round", "doserand_r"), 4),
                "frac_dM_okalt_gt_round": round(frac_gt(cs, "okalt", "round"), 4),
                "median_dM": {k: round(statistics.median(c[f"dM_{k}"] for c in cs), 4)
                              for k in ("main", "round", "okalt", "doserand_r")}}
    S = summary(X)
    h_rel = S["J_round"] <= S["J_main"] / 4 and S["frac_dM_main_gt_round"] >= 0.75 and S["groups_majority_main_gt_round"] >= 10
    h_cls = S["J_round"] >= S["J_main"] / 2 and S["frac_dM_main_gt_round"] < 0.60
    verdict = "REL_SUPPORTED" if h_rel else ("CLS_SUPPORTED" if h_cls else "GRADED_INTERMEDIATE")
    role = ("ROLE_ABSTRACT" if S["J_okalt"] >= S["J_main"] / 2 else
            "AUTHOR_IDENTITY_SPECIFIC" if S["J_okalt"] <= S["J_main"] / 4 else "INTERMEDIATE")
    donors = [d for d, _ in design["selection"]["donors"]]
    recog = {d[:12]: {"group": grp[d], **{arm: {"M": round(cap[(d, arm)][0], 4), "A": round(cap[(d, arm)][1], 4),
                                                "JOINT": cap[(d, arm)][2]} for arm in ("new", "ROUND", "OKALT")}}
             for d in donors}
    rd_flag = {d: cap[(d, "ROUND")][0] > 0 for d in donors}
    strat = {"donor_ROUND_flags_conflict": summary([c for c in X if rd_flag[c["donor"]]]) if any(rd_flag[c["donor"]] for c in X) else None,
             "donor_ROUND_no_conflict": summary([c for c in X if not rd_flag[c["donor"]]]) if any(not rd_flag[c["donor"]] for c in X) else None}
    logo = {g: summary([c for c in X if c["dg"] != g]) for g in sorted({c["dg"] for c in X})}
    per_host = {h[:12]: summary([c for c in X if c["host"] == h]) for h in sorted({c["host"] for c in X})}
    res = {"schema": "JEV_A461_MECH_M1_ANALYSIS_V1", "cross_group": S, "H_REL": h_rel, "H_CLS": h_cls,
           "verdict_round": verdict, "verdict_role": role, "donor_self_readouts": recog,
           "stratified_by_donor_ROUND_self_recognition": strat,
           "leave_one_donor_group_out": {g: {k: v[k] for k in ("J_main", "J_round", "J_okalt", "frac_dM_main_gt_round")}
                                         for g, v in logo.items()},
           "per_host": {h: {k: v[k] for k in ("cells", "J_main", "J_round", "J_okalt", "J_doserand_r")} for h, v in per_host.items()},
           "same_group_cells": summary([c for c in cells if not c["cross"]]),
           "rules": design["preregistered_analysis"]}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m1_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    (a.out / "m1_cells.jsonl").write_text("".join(json.dumps(c, sort_keys=True) + "\n" for c in cells), encoding="utf8")
    print(json.dumps({k: res[k] for k in ("cross_group", "verdict_round", "verdict_role")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
