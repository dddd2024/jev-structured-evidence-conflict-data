#!/usr/bin/env python3
"""A461-G5-G2 Stage-A donor qualification analysis (CPU, reads raw GPU rows only).

Frozen rule (admission draft f85f5fd1): strict donor = on the frozen W31 witness
inputs, conflicting_vote readout C is old=false, new=true, SA=false; report per
(W, cell) stratum and per source group; < 2 qualified donors => HOLD.
Readout C = argmax over keys ["false","true"]; margin M = logit(true) - logit(false).
Also reports all 8 (old,new,SA) C patterns, certificate_action argmax per arm,
margins, replay bitwise recheck, and the ledger/receipt reconciliation.
"""
import argparse, collections, hashlib, json, statistics, sys
from pathlib import Path


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def q(row, qid):
    return next(x for x in row["questions"] if x["id"] == qid)


def margin(row):
    c = q(row, "conflicting_vote")
    return c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]


def action(row):
    a = q(row, "certificate_action")
    return a["keys"][max(range(len(a["logits"])), key=lambda i: a["logits"][i])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--ledger", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    rows = [json.loads(x) for x in (a.run_dir / "raw_native_logits_stage_a.jsonl").read_text("utf8").splitlines() if x.strip()]
    rec = json.loads((a.run_dir / "execution_receipt.json").read_text("utf8"))
    ledger = [json.loads(x) for x in a.ledger.read_text("utf8").splitlines() if x.strip()]
    assert rec["status"] == "COMPLETE_A461_G5_G2_STAGE_A_SCREEN" and len(rows) == 378
    assert [r["forward_index"] for r in rows] == list(range(1, 379))
    reserves = [e["forward_index"] for e in ledger if e["event"] == "reserve"]
    assert reserves == list(range(1, 379)), "ledger reservations != 1..378"

    by_idx = {r["forward_index"]: r for r in rows}
    replay = [{"forward_index": r["forward_index"], "of": r["replay_of_forward_index"],
               "bitwise": r["questions"] == by_idx[r["replay_of_forward_index"]]["questions"]}
              for r in rows if r["kind"] == "replay"]
    assert len(replay) == 6 and all(x["bitwise"] for x in replay)

    scenes = collections.defaultdict(dict)
    for r in rows:
        if r["kind"] == "primary":
            scenes[r["scene_sha256"]][r["arm"]] = r
    assert len(scenes) == 124 and all(set(v) == {"old", "new", "SA"} for v in scenes.values())

    per_scene = []
    for s, arms in sorted(scenes.items()):
        M = {k: margin(v) for k, v in arms.items()}
        C = {k: M[k] > 0 for k in M}
        per_scene.append({
            "scene_sha256": s, "source_group": arms["old"]["source_group"], "cell": arms["old"]["cell"],
            "frozen_width": arms["old"]["frozen_width"],
            "C": C, "M": {k: round(v, 6) for k, v in M.items()},
            "action": {k: action(v) for k, v in arms.items()},
            "pattern": "".join("T" if C[k] else "F" for k in ("old", "new", "SA")),
            "strict_qualified": (not C["old"]) and C["new"] and (not C["SA"]),
            "delta_new_minus_old": round(M["new"] - M["old"], 6),
            "delta_new_minus_SA": round(M["new"] - M["SA"], 6)})
    q_ = [x for x in per_scene if x["strict_qualified"]]
    patt = collections.Counter(x["pattern"] for x in per_scene)
    by_cell = collections.defaultdict(lambda: collections.Counter())
    for x in per_scene:
        by_cell[x["cell"]][x["pattern"]] += 1
    groups = collections.defaultdict(lambda: {"scenes": 0, "qualified": 0})
    for x in per_scene:
        groups[x["source_group"]]["scenes"] += 1
        groups[x["source_group"]]["qualified"] += int(x["strict_qualified"])
    qual_groups = sorted({x["source_group"] for x in q_})
    med = lambda v: round(statistics.median(v), 4)
    summary = {
        "schema": "JEV_A461_G5_G2_STAGE_A_ANALYSIS_V1",
        "rule": "strict: C(old)=false, C(new)=true, C(SA)=false; C = logit(true) > logit(false)",
        "scenes": 124, "strict_qualified": len(q_), "qualified_source_groups": qual_groups,
        "decision": ("PROCEED_STAGE_B_DESIGN" if len(q_) >= 2 else "HOLD") +
                    ("" if len(qual_groups) >= 2 or len(q_) < 2 else "_SINGLE_GROUP_ONLY"),
        "pattern_counts_old_new_SA": dict(sorted(patt.items())),
        "pattern_by_cell": {c: dict(sorted(v.items())) for c, v in sorted(by_cell.items())},
        "C_rate": {arm: round(sum(x["C"][arm] for x in per_scene) / 124, 4) for arm in ("old", "new", "SA")},
        "median_margin": {arm: med([x["M"][arm] for x in per_scene]) for arm in ("old", "new", "SA")},
        "median_delta_new_minus_old": med([x["delta_new_minus_old"] for x in per_scene]),
        "median_delta_new_minus_SA": med([x["delta_new_minus_SA"] for x in per_scene]),
        "action_counts": {arm: dict(collections.Counter(x["action"][arm] for x in per_scene)) for arm in ("old", "new", "SA")},
        "groups": dict(sorted(groups.items())),
        "qualified": q_,
        "replay_bitwise": replay,
        "accounting": {"physical": rec["physical_forwards"], "reserved": len(reserves),
                       "batches": [(b["run"], b["physical"]) for b in rec["batch_receipts"]],
                       "raw_sha256": hashlib.sha256((a.run_dir / "raw_native_logits_stage_a.jsonl").read_bytes()).hexdigest()}}
    a.out.mkdir(mode=0o700, parents=False, exist_ok=False)
    with (a.out / "stage_a_analysis.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(summary, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (a.out / "stage_a_per_scene.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for x in per_scene:
            f.write(canon(x) + "\n")
    print(json.dumps({k: summary[k] for k in ("strict_qualified", "qualified_source_groups", "decision",
                                              "pattern_counts_old_new_SA", "pattern_by_cell", "C_rate",
                                              "median_margin", "median_delta_new_minus_old",
                                              "median_delta_new_minus_SA", "action_counts")}, indent=1, ensure_ascii=False))
    for x in q_:
        print("QUALIFIED", x["scene_sha256"][:12], x["source_group"], x["cell"], x["M"], x["action"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
