#!/usr/bin/env python3
"""A461-PSMI G0 physical forward manifest generator (CPU only, no model).

Derives the planned G1 forward ledger from frozen G0 outputs:
one row per planned physical forward (shared old-arm baseline counted once
per pair), with native request hashes, gold, token facts and the N1
token-count-match flags required by the pre-execution shadow QA.
"""
import argparse, hashlib, json, os, sys
from pathlib import Path

HOME = Path.home() / "wjc"


def hx(s):
    return hashlib.sha256(s.encode("utf8")).hexdigest()


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g0", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    g0 = a.g0.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    assert out.parent.is_dir() and not out.exists(), "new out dir required"
    out.mkdir(mode=0o700)
    prows = [json.loads(x) for x in (g0 / "pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
    trows = {r["row_id"]: r for r in (json.loads(x) for x in (g0 / "token_audit.jsonl").read_text("utf8").splitlines() if x.strip())}
    by_pair = {}
    for r in prows:
        by_pair.setdefault(r["pair_key"], []).append(r)
    rows = []
    replays_planned = 4
    for key, rs in sorted(by_pair.items()):
        first = rs[0]
        old_row = {
            "source_family": first["source"], "source_group": first["source_group"],
            "axis": first["family"], "original_scene_sha": key.split(":", 1)[1],
            "role": "old_baseline", "row_id": first["pair_key"] + ":old",
            "native_request_sha256": None, "old_rule_gold": None, "new_rule_gold": None,
            "token_count": None, "token_sha": None, "N1_equal_token_count": None,
            "question_order": None, "model_precision": "fp32_planned_g1_cpu_audited_only",
            "intended_forward_count": 1,
            "cached_baseline_policy": "one physical old-arm forward per pair; shared by treatment/neutral/retimed arms of the same scene via exact native_request hash identity",
        }
        # old-arm gold & tokens: recover from any arm's token audit old_* fields
        ta = next(trows[r["row_id"]] for r in rs)
        old_row["token_count"] = ta["old_state_token_len"]
        old_row["token_sha"] = ta["old_state_token_sha256"]
        rows.append(old_row)
        for r in sorted(rs, key=lambda x: x["row_id"]):
            ta = trows[r["row_id"]]
            rows.append({
                "source_family": r["source"], "source_group": r["source_group"],
                "axis": r["family"], "original_scene_sha": key.split(":", 1)[1],
                "role": {"new": "treatment", "neutral": "N1_neutral", "retimed": "N2_retime"}[r["arm"]],
                "row_id": r["row_id"],
                "native_request_sha256": hx(canon(r["native_request"])),
                "old_rule_gold": None, "new_rule_gold": r["oracle_gold_impl1"],
                "token_count": ta["state_token_len"], "token_sha": ta["state_token_sha256"],
                "N1_equal_token_count": (ta["token_len_delta_vs_old"] == 0) if r["arm"] == "neutral" else None,
                "question_order": sorted(r["native_request"]["questions"].keys()),
                "model_precision": "fp32_planned_g1_cpu_audited_only",
                "intended_forward_count": 1,
                "cached_baseline_policy": "reuses old_baseline row of its pair",
            })
    manifest = {
        "schema": "JEV_A461_PSMI_PHYSICAL_FORWARD_MANIFEST_V1",
        "g0_dir": str(g0), "total_planned_forwards": len(rows) + replays_planned,
        "baseline_reuse_policy": "one old-arm forward per pair_key (34 total)",
        "repeated_baseline_precision_replays_planned": replays_planned,
        "forward_cap": 128, "rows": rows,
        "n1_rows_total": sum(1 for r in rows if r["role"] == "N1_neutral"),
        "n1_token_matched": sum(1 for r in rows if r["role"] == "N1_neutral" and r["N1_equal_token_count"] is True),
        "n1_token_mismatched": sum(1 for r in rows if r["role"] == "N1_neutral" and r["N1_equal_token_count"] is False),
        "note": "CPU-only derivation; no model run. N1 rows with N1_equal_token_count=false are excluded from strict matched-length causal contrast vs arXiv:2610.12292 per shadow QA QA-1."
    }
    with (out / "physical_forward_manifest.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(manifest, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    h = hashlib.sha256()
    with (out / "physical_forward_manifest.json").open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        f.write(h.hexdigest() + "  physical_forward_manifest.json\n")
    print(json.dumps({k: manifest[k] for k in ("total_planned_forwards", "n1_rows_total", "n1_token_matched", "n1_token_mismatched", "forward_cap")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
