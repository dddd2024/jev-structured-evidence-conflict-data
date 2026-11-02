#!/usr/bin/env python3
"""A461 read-only analysis of an EXISTING archived LANL-V2 derived-Gold JSONL.
No SecJev model, GPU, corpora, synthetic edits, TEST/CAL, or network.
Input: previously archived A427 V2 independent_gold_rows.jsonl, Git blob pinned.
Output: aggregate counts on stdout ONLY; never emit raw security event rows.
This is NOT experimental A461 G0 admission or a counterfactual generator.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

EXPECTED_GIT_BLOB = "af2e68efff36a604b635bdf9402324a6ecf36508"
EXPECTED_SUFFIX = "research/rounds/A427_20261023_LANL_TRIAGE_FAIL_VOCABULARY_V2_CPU_GATE/P0_REAL_20261023/independent_gold_rows.jsonl"
ROOT = (Path.home() / "wjc").resolve()


def audit(rows):
    groups = defaultdict(lambda: {
        "n": 0, "burst": 0, "investigate": 0, "spread_only": 0,
        "burst_seed": 0, "spread_seed": 0
    })
    for r in rows:
        assert r["evaluable"] and r["official_gold_matches"]
        g = groups[r["source_group"]]
        g["n"] += 1
        f = r["count_visible_failed_logons"]
        d = r["count_distinct_known_failed_destinations"]
        burst = r["inferred"]["failure_burst"]
        action = r["inferred"]["triage"]
        assert burst == (f >= 5), "Independent Gold result and visible-burst threshold differ"
        assert action in {"continue_monitoring", "record_failed_attempt", "investigate"}
        g["burst"] += int(burst)
        g["investigate"] += int(action == "investigate")
        g["spread_only"] += int(not burst and action == "investigate")
        clean = (
            r["unknown_destination_failed_events"] == 0
            and r["older_summary_failed_count_unscoped"] == 0
            and not burst and action != "investigate"
        )
        g["burst_seed"] += int(clean and f == 4 and 1 <= d < 3)
        g["spread_seed"] += int(clean and d == 2 and f <= 3)
    counts = list(groups.values())
    total = sum(z["n"] for z in counts)
    def sum_key(key):
        return sum(z[key] for z in counts)
    output = {
        "schema": "A461_READONLY_ARCHIVED_GOLD_METADATA_COUNTS",
        "total": total,
        "group_counts": dict(sorted(groups.items())),
        "spread_only": sum_key("spread_only"),
        "spread_only_groups": [g for g,z in sorted(groups.items()) if z["spread_only"]],
        "burst_seed_necessary_only": sum_key("burst_seed"),
        "burst_seed_groups": sum(z["burst_seed"] > 0 for z in counts),
        "spread_seed_necessary_only": sum_key("spread_seed"),
        "spread_seed_groups": sum(z["spread_seed"] > 0 for z in counts),
        "group_exposure_inverse_hhi": total**2 / sum(z["n"]**2 for z in counts),
        "new_model_forwards": 0,
        "validated_counterfactual_pairs": 0,
    }
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        def r(group,f,d,action):
            return {
                "evaluable": True, "official_gold_matches": True,
                "source_group": group, "count_visible_failed_logons": f,
                "count_distinct_known_failed_destinations": d,
                "inferred": {"failure_burst": f>=5, "triage": action},
                "unknown_destination_failed_events": 0,
                "older_summary_failed_count_unscoped": 0
            }
        out = audit([r("g1",4,1,"record_failed_attempt"),
                     r("g2",2,2,"continue_monitoring"),
                     r("g2",3,3,"investigate")])
        assert out["burst_seed_necessary_only"]==1 and out["spread_seed_necessary_only"]==1
        assert out["spread_only"]==1 and out["total"]==3
        print("SELF_TEST_PASS")
        return
    if args.input is None:
        parser.error("--input (archived derived-Gold path) required")
    source = args.input.expanduser().resolve()
    assert source.is_relative_to(ROOT), "Source must be under ~/wjc"
    assert str(source).endswith(EXPECTED_SUFFIX), "Unexpected archived input path"
    raw = source.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    assert blob == EXPECTED_GIT_BLOB, "Existing archived evidence bytes drifted"
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    out = audit(rows)
    assert out["total"]==328 and len(out["group_counts"])==7
    assert out["spread_only"]==3 and out["spread_only_groups"]==["lanl:day:50"]
    assert out["burst_seed_necessary_only"]==31 and out["burst_seed_groups"]==3
    assert out["spread_seed_necessary_only"]==22 and out["spread_seed_groups"]==2
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
