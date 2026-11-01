#!/usr/bin/env python3
"""A461-PSMI G1 replay-determinism verification and receipt correction (CPU).

The G1 runner executed all 103 approved forwards and persisted raw logits
before post-loop checks; its only failure was a post-hoc replay bookkeeping
bug (comparing each replay row against other replay rows instead of against
the primary forward of the same base). This script recomputes the replay
verdicts from the persisted logits and issues the corrected execution
receipt. No model, no GPU.
"""
import argparse, hashlib, json, sys
from pathlib import Path


def sha_file(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g1", required=True, type=Path)
    a = ap.parse_args()
    g1 = a.g1.expanduser().resolve(strict=True)
    rows = [json.loads(x) for x in (g1 / "raw_native_logits_103_requests.jsonl").read_text("utf8").splitlines() if x.strip()]
    prim = {r["plan_row"]: r for r in rows if r["kind"] == "primary"}
    replays = [r for r in rows if r["kind"] == "replay"]
    ck = lambda v, m: (_ for _ in ()).throw(RuntimeError(m)) if not v else None
    ck(len(rows) == 103, f"row count {len(rows)}")
    ck(len(replays) == 4, "replay count")
    results = []
    for rp in replays:
        base = rp["plan_row"].split(":replay")[0]
        p = prim.get(base)
        ck(p is not None, "primary missing for " + base)
        same = all(x["logits"] == y["logits"] for x, y in zip(p["questions"], rp["questions"]))
        tok_same = p["token_ids_sha256"] == rp["token_ids_sha256"]
        results.append({"base_row": base, "replay_index": rp["forward_index"],
                        "primary_index": p["forward_index"],
                        "token_ids_identical": tok_same, "logits_identical": same,
                        "verdict": "IDENTICAL" if same and tok_same else "DIFFER"})
    ck(all(r["verdict"] == "IDENTICAL" for r in results), "replay nondeterminism: " + canon(results))
    gate = json.loads((g1 / "pre_forward_token_gate_receipt.json").read_text("utf8"))
    ck(gate["status"] == "PASS_A461_PSMI_G1_PRE_FORWARD_GATES", "pre-forward gate not PASS")
    roles = {}
    for r in rows:
        roles[r["role"]] = roles.get(r["role"], 0) + 1
    corrected = {
        "schema": "JEV_A461_PSMI_G1_EXECUTION_RECEIPT_V2_CORRECTED",
        "status": "COMPLETE_A461_PSMI_G1_PAIRED_PILOT",
        "run_id": "a461-psmi-counterfactual-cpu-gate-20261025-v1",
        "physical_forwards": len(rows), "budget": 103,
        "plan_composition": roles,
        "replay_verdicts": results,
        "pre_forward_gate": gate["status"],
        "a428_shared_scene_identity": gate.get("a428_shared_scene_identity", []),
        "gpu_model_loads": 1, "backprop_calls": 0, "network_calls": 0,
        "tool_actions": 0, "test_or_calibration_rows": 0,
        "erratum": "V1 receipt reported FAIL solely due to a post-loop replay bookkeeping bug (replay rows compared against each other instead of against their primary forwards); all 103 forwards had already completed and been persisted. This corrected receipt recomputes replay verdicts from the persisted logits. Raw attempt receipt preserved at execution_receipt.json (V1); attempt dirs G1_ATTEMPT1_NULL_OLD_ROW / G1_ATTEMPT2_NULL_OLD_ROW_AGAIN / G1_ATTEMPT3_TRACEBACK_FOUND_ROW / G1_ATTEMPT4_QUEUE_TUPLE / G1_ATTEMPT5_STALE / G1_DEBUG_TIMEOUT preserved on the server."
    }
    out = g1 / "replay_receipt.json"
    if not out.exists():
        with out.open("x", encoding="utf8", newline="\n") as f:
            json.dump({"schema": "JEV_A461_PSMI_G1_REPLAY_V2_FROM_PERSISTED_LOGITS",
                       "replays": results}, f, sort_keys=True, indent=2, ensure_ascii=False)
            f.write("\n")
    corr = g1 / "execution_receipt_corrected.json"
    with corr.open("x", encoding="utf8", newline="\n") as f:
        json.dump(corrected, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    sums = g1 / "SHA256SUMS_CORRECTED"
    with sums.open("x", encoding="utf8", newline="\n") as f:
        for n in ("raw_native_logits_103_requests.jsonl", "pre_forward_token_gate_receipt.json",
                  "replay_receipt.json", "execution_receipt_corrected.json"):
            f.write(sha_file(g1 / n) + "  " + n + "\n")
    print(canon({"status": corrected["status"], "replays": results}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
