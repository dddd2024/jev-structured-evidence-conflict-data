#!/usr/bin/env python3
"""A461-G5-G2 Stage-E preregistered analysis (frozen with the design before any Stage-E forward).

Implements stage_e_design.json (blob af68448c) "preregistered_analysis":
  A = logit(reject_conflict) - max(logit(accept), logit(wait)); REJECT iff A > 0; dA vs the Stage-A host new baseline.
  cell (donor, host, setting): SPECIFIC_REJECT iff main REJECT and neither SA-sham nor dose-random REJECT;
  DOSE_SPECIFIC_A iff dA_main > dA_dose. Action-level correction is claimed iff in some setting SPECIFIC_REJECT
  cells involve >= 2 donor groups and >= 2 host groups.
  Reachability: scope action -> every non-action row bitwise == baseline.
"""
import argparse, collections, json, statistics as st, sys
from pathlib import Path

SETTINGS = [(11, "action"), (11, "all"), (12, "all")]


def logits(qs, qid):
    q = next(q for q in qs if q["id"] == qid)
    return dict(zip(q["keys"], q["logits"]))


def A(qs):
    d = logits(qs, "certificate_action")
    return d["reject_conflict"] - max(d["accept"], d["wait"])


def M(qs):
    d = logits(qs, "conflicting_vote")
    return d["true"] - d["false"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = [json.loads(x) for x in (a.run_dir / "raw_native_logits_stage_e.jsonl").read_text("utf8").splitlines() if x.strip()]
    assert len(rows) == 304 and [r["forward_index"] for r in rows] == list(range(1, 305))
    design = json.loads(a.design.read_text("utf8"))
    sa = {(r["scene_sha256"], r["arm"]): r for r in
          (json.loads(x) for x in a.stage_a_raw.read_text("utf8").splitlines() if x.strip()) if r["kind"] == "primary"}
    dgroup = {x["scene_sha256"]: x["source_group"] for x in design["donors"]}
    hgroup = {x["scene_sha256"]: x["source_group"] for x in design["hosts"]}
    cross_row = {r["target_scene"][:12] + ":" + r["target_arm"]: r.get("cross_row_max_absdiff") for r in rows
                 if r["condition"].startswith("capture_")}
    # baselines = the in-run capture forwards of the host new arm (the runner asserts these are bitwise equal to the
    # Stage-A rows on the GPU backend); equality to Stage-A is also reported here
    inrun = {(r["target_scene"], r["target_arm"]): r for r in rows if r["condition"].startswith("capture_")}
    baseline_equals_stage_a = all(r["questions"] == sa[k]["questions"] for k, r in inrun.items())
    sa = {k: {"questions": r["questions"]} for k, r in inrun.items()}
    cells = collections.defaultdict(dict)
    for r in rows:
        if r.get("direction") == "repair":
            arm = r["condition"].split("_")[2]          # main / sasham / doserand
            cells[(r["donor"], r["host"], r["layer"], r["scope"])][arm] = r
    reach_bad = 0
    out_cells = []
    for (d, h, L, scope), cs in sorted(cells.items()):
        b = sa[(h, "new")]["questions"]
        if scope == "action":
            for r in cs.values():
                # only the certificate_action row was patched: every other row must equal the baseline bitwise
                reach_bad += any(logits(r["questions"], q) != logits(b, q)
                                 for q in ("conflicting_vote", "evidence_level", "quorum"))
        Ab, Mb = A(b), M(b)
        Ax = {k: A(v["questions"]) for k, v in cs.items()}
        Mx = {k: M(v["questions"]) for k, v in cs.items()}
        rej = {k: v > 0 for k, v in Ax.items()}
        out_cells.append({"donor": d[:12], "host": h[:12], "layer": L, "scope": scope, "donor_group": dgroup[d],
                          "host_group": hgroup[h], "baseline_A": round(Ab, 6), "baseline_M": round(Mb, 6),
                          "A": {k: round(v, 6) for k, v in Ax.items()}, "dA": {k: round(v - Ab, 6) for k, v in Ax.items()},
                          "M": {k: round(v, 6) for k, v in Mx.items()}, "reject": rej,
                          "specific_reject": rej["main"] and not rej["sasham"] and not rej["doserand"],
                          "dose_specific_A": Ax["main"] > Ax["doserand"],
                          "c_flip_main": Mx["main"] > 0})
    assert len(out_cells) == 96
    summary = {}
    for L, scope in SETTINGS:
        cs = [c for c in out_cells if c["layer"] == L and c["scope"] == scope]
        sr = [c for c in cs if c["specific_reject"]]
        s = {"cells": len(cs), "specific_reject": len(sr),
             "rejects": {k: sum(c["reject"][k] for c in cs) for k in ("main", "sasham", "doserand")},
             "dose_specific_A": sum(c["dose_specific_A"] for c in cs),
             "median_dA": {k: round(st.median(c["dA"][k] for c in cs), 4) for k in ("main", "sasham", "doserand")},
             "c_flips_main": sum(c["c_flip_main"] for c in cs),
             "specific_reject_donor_groups": sorted({c["donor_group"] for c in sr}),
             "specific_reject_host_groups": sorted({c["host_group"] for c in sr})}
        s["action_level_correction"] = len(s["specific_reject_donor_groups"]) >= 2 and len(s["specific_reject_host_groups"]) >= 2
        summary[f"L{L}_{scope}"] = s
    verdict = "ACTION_LEVEL_CORRECTION" if any(v["action_level_correction"] for v in summary.values()) else "NO_ACTION_LEVEL_CORRECTION"
    res = {"schema": "JEV_A461_G5_G2_STAGE_E_ANALYSIS_V1", "verdict": verdict, "summary": summary,
           "baseline_capture_rows_equal_stage_a": baseline_equals_stage_a,
           "reachability_violations_scope_action": reach_bad, "cross_row_max_absdiff": cross_row, "cells": out_cells}
    a.out.mkdir(mode=0o700, exist_ok=False)
    (a.out / "stage_e_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"verdict": verdict, "summary": summary, "reachability_violations_scope_action": reach_bad,
                      "baseline_capture_rows_equal_stage_a": baseline_equals_stage_a,
                      "cross_row_max_absdiff_max": max(v for v in cross_row.values() if v is not None)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
