#!/usr/bin/env python3
"""A461-G5-G2 Stage-F preregistered analysis (frozen with the design before any Stage-F forward).

Implements stage_f_design.json "preregistered_analysis":
  per cell (source, host): C = conflict readout true; R = argmax certificate_action == reject_conflict;
  JOINT = C and R in the same forward.
  H_F1 class prototype: content beyond decision class iff JOINT(ttt_new) - JOINT(ttt_sa) >= 5 AND
       JOINT(ttt_new) >= 2 x JOINT(ttt_sa).
  H_F2 recognition: JOINT(fff_new) <= 2 AND JOINT(donor_new) - JOINT(fff_new) >= 5.
  H_F3 source diversity: ttt_new JOINT cells from >= 3 source groups and >= 3 host groups.
  Always reported: C-only, R-only, JOINT per source kind, per source group, per host; leave-one-source-group-out.
Baselines are the in-run host capture rows (bitwise == Stage-A rows on the GPU backend, runner-enforced).
"""
import argparse, collections, json, sys
from pathlib import Path

KINDS = ("donor_new", "donor_sa", "ttt_new", "ttt_sa", "fff_new")


def lg(qs, q):
    d = next(x for x in qs if x["id"] == q)
    return dict(zip(d["keys"], d["logits"]))


def C(qs):
    d = lg(qs, "conflicting_vote")
    return d["true"] > d["false"]


def R(qs):
    d = lg(qs, "certificate_action")
    return d["reject_conflict"] > max(d["accept"], d["wait"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = [json.loads(x) for x in (a.run_dir / "raw_native_logits_stage_f.jsonl").read_text("utf8").splitlines() if x.strip()]
    assert len(rows) == 296 and [r["forward_index"] for r in rows] == list(range(1, 297))
    des = json.loads(a.design.read_text("utf8"))
    sgroup = {x["scene_sha256"]: x["source_group"] for x in des["donors"]}
    sgroup.update({x["scene_sha256"]: x["source_group"] for x in des["sources"]["ttt"] + des["sources"]["fff"]})
    hgroup = {x["scene_sha256"]: x["source_group"] for x in des["hosts"]}
    base = {r["target_scene"]: r for r in rows if r["condition"] == "capture_new_all_rows" and r.get("source_kind") == "host"}
    assert len(base) == 8
    # on the real model the hosts are Stage-A FFF scenes with A < 0; reported, not assumed
    baselines_neither_C_nor_R = not any(C(b["questions"]) or R(b["questions"]) for b in base.values())
    cells = []
    for r in rows:
        if not r["condition"].startswith("patch_"):
            continue
        c, rr = C(r["questions"]), R(r["questions"])
        cells.append({"kind": r["source_kind"], "source": r["donor"][:12], "source_group": sgroup[r["donor"]],
                      "host": r["host"][:12], "host_group": hgroup[r["host"]], "C": c, "R": rr, "JOINT": c and rr})
    assert len(cells) == 256

    def summ(cs):
        j = [c for c in cs if c["JOINT"]]
        return {"cells": len(cs), "C": sum(c["C"] for c in cs), "R": sum(c["R"] for c in cs), "JOINT": len(j),
                "C_only": sum(c["C"] and not c["R"] for c in cs), "R_only": sum(c["R"] and not c["C"] for c in cs),
                "joint_source_groups": sorted({c["source_group"] for c in j}), "joint_host_groups": sorted({c["host_group"] for c in j})}
    by_kind = {k: summ([c for c in cells if c["kind"] == k]) for k in KINDS}
    by_group = {k: {g: summ([c for c in cells if c["kind"] == k and c["source_group"] == g])
                    for g in sorted({c["source_group"] for c in cells if c["kind"] == k})} for k in KINDS}
    by_host = {h: {k: summ([c for c in cells if c["kind"] == k and c["host"] == h])["JOINT"] for k in KINDS}
               for h in sorted({c["host"] for c in cells})}
    logo = {k: {g: summ([c for c in cells if c["kind"] == k and c["source_group"] != g])["JOINT"]
                for g in sorted({c["source_group"] for c in cells if c["kind"] == k})} for k in KINDS}
    J = {k: by_kind[k]["JOINT"] for k in KINDS}
    h1 = J["ttt_new"] - J["ttt_sa"] >= 5 and J["ttt_new"] >= 2 * J["ttt_sa"]
    h2 = J["fff_new"] <= 2 and J["donor_new"] - J["fff_new"] >= 5
    h3 = len(by_kind["ttt_new"]["joint_source_groups"]) >= 3 and len(by_kind["ttt_new"]["joint_host_groups"]) >= 3
    res = {"schema": "JEV_A461_G5_G2_STAGE_F_ANALYSIS_V1", "host_baselines_neither_C_nor_R": baselines_neither_C_nor_R,
           "H_F1_content_beyond_class": h1, "H_F2_recognition_matters": h2, "H_F3_source_diversity": h3,
           "verdict_H_F1": "CONTENT_BEYOND_DECISION_CLASS" if h1 else "CONSISTENT_WITH_POSITIVE_CLASS_REPRESENTATION",
           "joint": J, "by_kind": by_kind, "by_source_group": by_group, "by_host_joint": by_host,
           "leave_one_source_group_out_joint": logo, "cells": cells}
    a.out.mkdir(mode=0o700, exist_ok=False)
    (a.out / "stage_f_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("host_baselines_neither_C_nor_R", "H_F1_content_beyond_class", "H_F2_recognition_matters", "H_F3_source_diversity",
                                         "verdict_H_F1", "joint")} | {"by_kind": {k: {kk: v[kk] for kk in ("C", "R", "JOINT", "C_only", "R_only")}
                                                                                   for k, v in by_kind.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
