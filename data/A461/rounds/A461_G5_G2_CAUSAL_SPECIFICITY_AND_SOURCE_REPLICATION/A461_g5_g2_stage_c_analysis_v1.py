#!/usr/bin/env python3
"""A461-G5-G2 Stage-C preregistered analysis (frozen with the design before any Stage-C forward).

Implements stage_c_design.json (blob 985d7cce) "preregistered_analysis":
  H1  dose-matched restoration at L11: cell SUPPORTIVE iff dM_main > max(dM_doserand_s1, dM_doserand_s2);
      content-specific iff >= 10/16 supportive AND every donor group has one AND median(dM_main - max doserand) > 0.
  H1b dose-matched suppression at L11: cell SUPPORTIVE iff dM_main < dM_doserand_s1; plus main vs donor-side SA-sham.
  H2  layer localization 11..14: median dM_main per direction; boundary = first layer with |median| < 10% of L11
      in both directions.
  H3  encoding: delta_s(L) = mean over span positions of h_new - h_SA; u(L) = normalised mean delta of donors
      (leave-one-donor-out for donor scores); p_s(L) = delta_s(L) . u(L). Prediction at L11: median p(FFF) < every
      held-out donor p, and AUC(FTF vs FFF) >= 0.9. 24-layer profile descriptive.
dM is measured against the Stage-A raw baseline of the patched arm.
"""
import argparse, collections, json, statistics as st, sys
from pathlib import Path

REST = {"main": "patch_restoration_donor_new_to_host_sa", "sasham": "patch_sasham_donor_sa_to_host_sa",
        "dose1": "patch_doserand_s1_to_host_sa", "dose2": "patch_doserand_s2_to_host_sa"}
SUPP = {"main": "patch_suppression_host_new_to_donor_new", "sasham": "patch_donorside_sasham_host_sa_to_donor_new",
        "dose1": "patch_doserand_s1_to_donor_new"}


def margin(qs):
    c = next(q for q in qs if q["id"] == "conflicting_vote")
    return c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]


def auc(pos, neg):
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--stage-a-per-scene", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    import torch
    rows = [json.loads(x) for x in (a.run_dir / "raw_native_logits_stage_c.jsonl").read_text("utf8").splitlines() if x.strip()]
    assert len(rows) == 696
    sa = [json.loads(x) for x in a.stage_a_raw.read_text("utf8").splitlines() if x.strip()]
    per = {json.loads(x)["scene_sha256"]: json.loads(x) for x in a.stage_a_per_scene.read_text("utf8").splitlines() if x.strip()}
    design = json.loads(a.design.read_text("utf8"))
    base = {(r["scene_sha256"], r["arm"]): margin(r["questions"]) for r in sa if r["kind"] == "primary"}
    group = {x["scene_sha256"]: x["source_group"] for x in design["donors"] + design["hosts"]}

    cells = collections.defaultdict(dict)
    for r in rows:
        if r.get("direction"):
            cells[(r["direction"], r["donor"], r["host"], r["layer"])][r["condition"]] = r
    res = {"schema": "JEV_A461_G5_G2_STAGE_C_ANALYSIS_V1", "cells": []}
    for (d, dn, hs, L), cs in sorted(cells.items()):
        arms = REST if d == "restoration" else SUPP
        tgt = (hs, "SA") if d == "restoration" else (dn, "new")
        dM = {k: cs[c]["M"] - base[tgt] for k, c in arms.items()}
        if d == "restoration":
            sup = dM["main"] > max(dM["dose1"], dM["dose2"])
        else:
            sup = dM["main"] < dM["dose1"]
        res["cells"].append({"direction": d, "donor": dn[:12], "host": hs[:12], "layer": L, "donor_group": group[dn],
                             "host_group": group[hs], "dM": {k: round(v, 6) for k, v in dM.items()},
                             "supportive_dose": sup,
                             "pert_norm_main": cs[arms["main"]]["span_stats"]["delta_norm_mean"]})
    C = res["cells"]

    def sel(d, L):
        return [c for c in C if c["direction"] == d and c["layer"] == L]
    r11 = sel("restoration", 11)
    gap = [c["dM"]["main"] - max(c["dM"]["dose1"], c["dM"]["dose2"]) for c in r11]
    n_dg = len({x["source_group"] for x in design["donors"]})
    h1 = {"supportive": sum(c["supportive_dose"] for c in r11), "cells": len(r11),
          "donor_groups_with_support": sorted({c["donor_group"] for c in r11 if c["supportive_dose"]}),
          "median_main_minus_max_dose": round(st.median(gap), 4),
          "median_dM": {k: round(st.median(c["dM"][k] for c in r11), 4) for k in REST}}
    h1["content_specific"] = (h1["supportive"] >= 10 and len(h1["donor_groups_with_support"]) == n_dg
                              and h1["median_main_minus_max_dose"] > 0)
    s11 = sel("suppression", 11)
    h1b = {"supportive": sum(c["supportive_dose"] for c in s11), "cells": len(s11),
           "median_dM": {k: round(st.median(c["dM"][k] for c in s11), 4) for k in SUPP},
           "median_main_minus_sasham": round(st.median(c["dM"]["main"] - c["dM"]["sasham"] for c in s11), 4),
           "main_beats_sasham": sum(c["dM"]["main"] < c["dM"]["sasham"] for c in s11)}
    h2 = {d: {L: {"median_dM_main": round(st.median(c["dM"]["main"] for c in sel(d, L)), 4),
                  "median_dM_sasham": round(st.median(c["dM"]["sasham"] for c in sel(d, L)), 4),
                  "dose_supportive": sum(c["supportive_dose"] for c in sel(d, L))} for L in (11, 12, 13, 14)}
          for d in ("restoration", "suppression")}
    boundary = None
    for L in (12, 13, 14):
        if all(abs(h2[d][L]["median_dM_main"]) < 0.1 * abs(h2[d][11]["median_dM_main"]) for d in h2):
            boundary = L
            break
    h2["boundary_layer"] = boundary

    # H3 encoding from saved captures
    caps = {}
    for r in rows:
        if r.get("capture_file"):
            t = torch.load(a.run_dir / "captures" / r["capture_file"]["name"]).float()   # [24, 31, D]
            caps[(r["target_scene"], r["target_arm"])] = t.mean(dim=1)                    # [24, D]
    scenes = sorted({s for s, _ in caps})
    delta = {s: caps[(s, "new")] - caps[(s, "SA")] for s in scenes}
    donors = [x["scene_sha256"] for x in design["donors"]]
    pattern = {s: per[s]["pattern"] for s in scenes}
    prof = {}
    for L in range(24):
        def u_excl(ex):
            v = torch.stack([delta[d][L] for d in donors if d != ex]).mean(dim=0)
            return v / v.norm()
        u_all = u_excl(None)
        p = {s: float(delta[s][L] @ (u_excl(s) if s in donors else u_all)) for s in scenes}
        fff = [p[s] for s in scenes if pattern[s] == "FFF"]
        ftf = [p[s] for s in donors]
        prof[L] = {"median_p": {pat: round(st.median([p[s] for s in scenes if pattern[s] == pat]), 4)
                                for pat in sorted(set(pattern.values()))},
                   "donor_p_lodo": [round(x, 4) for x in ftf], "auc_FTF_vs_FFF": round(auc(ftf, fff), 4),
                   "fff_median_below_all_donors": st.median(fff) < min(ftf)}
    h3 = {"L11": prof[11], "profile": prof,
          "prediction_holds_L11": prof[11]["fff_median_below_all_donors"] and prof[11]["auc_FTF_vs_FFF"] >= 0.9}
    res.update(H1_dose_matched_restoration_L11=h1, H1b_dose_matched_suppression_L11=h1b, H2_layers=h2, H3_encoding=h3)
    a.out.mkdir(mode=0o700, exist_ok=False)
    (a.out / "stage_c_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"H1": h1, "H1b": h1b, "H2": h2,
                      "H3_L11": {k: prof[11][k] for k in ("auc_FTF_vs_FFF", "fff_median_below_all_donors", "median_p",
                                                          "donor_p_lodo")},
                      "H3_auc_by_layer": {L: prof[L]["auc_FTF_vs_FFF"] for L in range(24)},
                      "H3_prediction_holds_L11": h3["prediction_holds_L11"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
