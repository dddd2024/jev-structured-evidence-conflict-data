#!/usr/bin/env python3
"""kev-4B K-B layer-scan analysis (frozen with the K-B design before any kev-4B patch forward).

Window rule (k4b_kb_design.json): L* = argmax over the scanned layers of the median, over cross-group cells,
of dM_main - dM_dose on the conflict margin; ties -> lower layer. Also reports per layer: median dM_main,
dM_dose, dA_main, dA_dose, share of cells with dM_main > dM_dose, and flips (C, R, joint) per arm.
Baselines are the in-run host capture rows (bitwise == kev-4B screen rows on the GPU backend).
"""
import argparse, json, statistics as st, sys
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = [json.loads(x) for x in (a.run_dir / "raw_native_logits_k4b_kb.jsonl").read_text("utf8").splitlines() if x.strip()]
    assert len(rows) == 346
    base = {r["target_scene"]: r["questions"] for r in rows if r["condition"] == "capture_new_all_rows" and r.get("source_kind") == "host"}
    assert len(base) == 4
    cells = {}
    for r in rows:
        if r["condition"].startswith("patch_kb_"):
            arm = "main" if "main" in r["condition"] else "dose"
            cells.setdefault((r["donor"], r["host"], r["layer"], r["cross_group"]), {})[arm] = r["questions"]
    prof = {}
    for L in sorted({k[2] for k in cells}):
        cs = [(k, v) for k, v in cells.items() if k[2] == L and k[3]]
        dm = {arm: [M(v[arm]) - M(base[k[1]]) for k, v in cs] for arm in ("main", "dose")}
        da = {arm: [A(v[arm]) - A(base[k[1]]) for k, v in cs] for arm in ("main", "dose")}
        gap = [x - y for x, y in zip(dm["main"], dm["dose"])]
        prof[str(L)] = {"cells": len(cs), "median_gap": round(st.median(gap), 4),
                        "share_main_gt_dose": round(sum(g > 0 for g in gap) / len(gap), 4),
                        "median_dM": {k: round(st.median(v), 4) for k, v in dm.items()},
                        "median_dA": {k: round(st.median(v), 4) for k, v in da.items()},
                        "C_flips": {arm: sum(M(v[arm]) > 0 for k, v in cs) for arm in ("main", "dose")},
                        "R_flips": {arm: sum(A(v[arm]) > 0 for k, v in cs) for arm in ("main", "dose")},
                        "joint": {arm: sum(M(v[arm]) > 0 and A(v[arm]) > 0 for k, v in cs) for arm in ("main", "dose")}}
    window = min(prof, key=lambda L: (-prof[L]["median_gap"], int(L)))
    res = {"schema": "JEV_A461_G5_G2_K4B_KB_ANALYSIS_V1", "window_layer": int(window),
           "rule": "argmax median(dM_main - dM_dose) over cross-group cells; ties -> lower layer",
           "host_baselines": {h[:12]: {"M": round(M(q), 4), "A": round(A(q), 4)} for h, q in base.items()},
           "profile": prof}
    a.out.mkdir(mode=0o700, exist_ok=False)
    (a.out / "k4b_kb_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"window_layer": res["window_layer"],
                      "profile": {L: {k: v[k] for k in ("median_gap", "share_main_gt_dose", "median_dM", "joint")} for L, v in prof.items()}},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
