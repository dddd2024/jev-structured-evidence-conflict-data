#!/usr/bin/env python3
"""A461-G5-G2 Stage-D preregistered analysis (frozen with the design before any Stage-D forward).

Implements stage_d_design.json (blob 13516502) "preregistered_analysis":
  D1: strict donors (C old=F, new=T, SA=F) per frozen width; groups; patterns.
  D2 cell (donor, host, layer): C_FLIP_x iff M_x > 0; ACTION_x = argmax certificate_action;
      SPECIFIC_FLIP iff main flips and neither SA-sham nor dose-random flips;
      SPECIFIC_REJECT iff main action == reject_conflict and neither control's action is.
      Behavioural correction claimed iff at some layer SPECIFIC_FLIP cells involve >= 2 donor groups and
      >= 2 host groups AND >= 1 SPECIFIC_REJECT exists. Secondary: dose specificity dM_main > dM_dose,
      dM_main - dM_sasham, flip vs baseline M_new.
dM is measured against the Stage-A host new baseline (bitwise-replayed by the host capture forward).
"""
import argparse, collections, json, statistics as st, sys
from pathlib import Path

ARMS = {"main": "patch_repair_donor_new_to_host_new", "sasham": "patch_sasham_donor_sa_to_host_new",
        "dose": "patch_doserand_to_host_new"}


def margin(qs):
    c = next(q for q in qs if q["id"] == "conflicting_vote")
    return c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]


def action(qs):
    a = next(q for q in qs if q["id"] == "certificate_action")
    return a["keys"][max(range(len(a["logits"])), key=lambda i: a["logits"][i])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = [json.loads(x) for x in (a.run_dir / "raw_native_logits_stage_d.jsonl").read_text("utf8").splitlines() if x.strip()]
    assert len(rows) == 349 and [r["forward_index"] for r in rows] == list(range(1, 350))
    design = json.loads(a.design.read_text("utf8"))
    sa = [json.loads(x) for x in a.stage_a_raw.read_text("utf8").splitlines() if x.strip()]
    base = {(r["scene_sha256"], r["arm"]): r for r in sa if r["kind"] == "primary"}

    # ---- D1 screen ----
    meta = {x["scene_sha256"]: x for x in design["D1_screen"]["scenes"]}
    scr = collections.defaultdict(dict)
    for r in rows:
        if r["condition"].startswith("screen_"):
            scr[r["target_scene"]][r["target_arm"]] = r
    assert len(scr) == 47 and all(set(v) == {"old", "new", "SA"} for v in scr.values())
    d1 = []
    for s, arms in sorted(scr.items()):
        M = {k: margin(v["questions"]) for k, v in arms.items()}
        pat = "".join("T" if M[k] > 0 else "F" for k in ("old", "new", "SA"))
        d1.append({"scene_sha256": s, "frozen_width": meta[s]["frozen_width"], "source_group": meta[s]["source_group"],
                   "cell": meta[s]["cell"], "pattern": pat, "M": {k: round(v, 6) for k, v in M.items()},
                   "action": {k: action(v["questions"]) for k, v in arms.items()}, "strict_qualified": pat == "FTF"})
    d1_sum = {"by_width": {w: {"scenes": sum(x["frozen_width"] == w for x in d1),
                               "strict": sum(x["strict_qualified"] and x["frozen_width"] == w for x in d1),
                               "patterns": dict(collections.Counter(x["pattern"] for x in d1 if x["frozen_width"] == w))}
                           for w in (31, 34)},
              "new_donors": [{k: x[k] for k in ("scene_sha256", "frozen_width", "source_group", "cell", "M", "action")}
                             for x in d1 if x["strict_qualified"]]}

    # ---- D2 repair ----
    donor_group = {x["scene_sha256"]: x["source_group"] for x in design["D2_repair"]["donors"]}
    host_group = {x["scene_sha256"]: x["source_group"] for x in design["D2_repair"]["hosts"]}
    # capture forwards are bitwise replays of Stage-A rows; the runner enforces that on the GPU backend
    cells = collections.defaultdict(dict)
    for r in rows:
        if r.get("direction") == "repair":
            cells[(r["donor"], r["host"], r["layer"])][r["condition"]] = r
    out_cells = []
    for (d, h, L), cs in sorted(cells.items()):
        b = base[(h, "new")]
        bM = margin(b["questions"])
        M = {k: margin(cs[c]["questions"]) for k, c in ARMS.items()}
        act = {k: action(cs[c]["questions"]) for k, c in ARMS.items()}
        flip = {k: M[k] > 0 for k in M}
        out_cells.append({"donor": d[:12], "host": h[:12], "layer": L, "donor_group": donor_group[d],
                          "host_group": host_group[h], "baseline_M": round(bM, 6), "baseline_action": action(b["questions"]),
                          "M": {k: round(v, 6) for k, v in M.items()}, "dM": {k: round(M[k] - bM, 6) for k in M},
                          "action": act, "flip": flip,
                          "specific_flip": flip["main"] and not flip["sasham"] and not flip["dose"],
                          "specific_reject": act["main"] == "reject_conflict" and act["sasham"] != "reject_conflict"
                          and act["dose"] != "reject_conflict",
                          "dose_specific": M["main"] > M["dose"]})
    assert len(out_cells) == 64
    layers = {}
    for L in (11, 12):
        cs = [c for c in out_cells if c["layer"] == L]
        sf = [c for c in cs if c["specific_flip"]]
        layers[L] = {"cells": len(cs), "specific_flip": len(sf), "specific_reject": sum(c["specific_reject"] for c in cs),
                     "flips": {k: sum(c["flip"][k] for c in cs) for k in ARMS},
                     "reject_actions": {k: sum(c["action"][k] == "reject_conflict" for c in cs) for k in ARMS},
                     "dose_specific": sum(c["dose_specific"] for c in cs),
                     "median_dM": {k: round(st.median(c["dM"][k] for c in cs), 4) for k in ARMS},
                     "specific_flip_donor_groups": sorted({c["donor_group"] for c in sf}),
                     "specific_flip_host_groups": sorted({c["host_group"] for c in sf})}
        layers[L]["behavioural_correction"] = (len(layers[L]["specific_flip_donor_groups"]) >= 2
                                               and len(layers[L]["specific_flip_host_groups"]) >= 2
                                               and layers[L]["specific_reject"] >= 1)
    per_host = {}
    for h in sorted({c["host"] for c in out_cells}):
        cs = [c for c in out_cells if c["host"] == h]
        per_host[h] = {"baseline_M": cs[0]["baseline_M"], "group": cs[0]["host_group"],
                       "specific_flip_L11": sum(c["specific_flip"] for c in cs if c["layer"] == 11),
                       "specific_flip_L12": sum(c["specific_flip"] for c in cs if c["layer"] == 12),
                       "max_M_main": max(c["M"]["main"] for c in cs)}
    verdict = "BEHAVIOURAL_CORRECTION" if any(v["behavioural_correction"] for v in layers.values()) else "NO_BEHAVIOURAL_CORRECTION"
    res = {"schema": "JEV_A461_G5_G2_STAGE_D_ANALYSIS_V1", "D1": d1_sum, "D1_scenes": d1, "D2_layers": layers,
           "D2_per_host": per_host, "D2_verdict": verdict, "D2_cells": out_cells}
    a.out.mkdir(mode=0o700, exist_ok=False)
    (a.out / "stage_d_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"D1": d1_sum, "D2_verdict": verdict, "D2_layers": layers, "D2_per_host": per_host}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
