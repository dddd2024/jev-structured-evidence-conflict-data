#!/usr/bin/env python3
"""A461-G5-G2 Stage-A admission draft, Option A (zero forwards).

Packages the Stage-A CPU freeze into an admission DRAFT per the V3 freeze
review (0520e979):
  - Option A: keep each scene's single frozen_width witness; donor/host pairs
    match on the SAME frozen W only; W reported as a stratification variable;
    the one unpairable W32 scene moves to exploratory and out of confirmatory.
  - Recomputes frozen-W cross-group pairing (expected 19,622 directed pairs:
    W31 19,068 + W34 554).
  - Deterministic N=124 slice (scene-SHA sorted; W31 tier fills first) with the
    complete 1:1 physical forward manifest: scene -> run -> arm, with 2
    determinism replays of each run's first primary old arm placed at that
    run's end; every run <= 128 calls including replays.
  - Admission draft JSON: the gates the Stage-A GPU runner must enforce.
Zero model loads, zero forwards.
"""
import argparse, collections, hashlib, json, os, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
HARD_CAP = 128
REPLAYS_PER_RUN = 2
N_RECOMMENDED = 124


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def save(p, v):
    with p.open("x", encoding="utf8", newline="\n") as f:
        json.dump(v, f, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def sha_file(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    freeze = a.freeze_dir.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and str(out).startswith(str(ROOT)) and out.parent.is_dir() and not out.exists(), "out dir")
    receipt = {"schema": "JEV_A461_G5_G2_STAGE_A_ADMISSION_DRAFT_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": "A461_G5_G2_STAGE_A_ADMISSION_DRAFT_R1",
               "gpu_forwards": 0, "model_loads": 0, "network_calls": 0, "tool_actions": 0,
               "test_or_calibration_rows": 0, "output_dir": str(out),
               "inputs": {"roster": str(freeze / "stage_a_candidate_roster.json")}}
    produced = []
    try:
        out.mkdir(mode=0o700)
        roster_doc = json.loads((freeze / "stage_a_candidate_roster.json").read_text("utf8"))
        ck(roster_doc["schema"] == "JEV_A461_G5_G2_STAGE_A_CANDIDATE_ROSTER_V3", "roster schema")
        cands = roster_doc["candidates"]
        ck(len(cands) == 172, f"roster census {len(cands)}")

        # ---------- Option A packaging ----------
        w_hist_all = collections.Counter(r["frozen_width"] for r in cands)
        exploratory = [r for r in cands if w_hist_all[r["frozen_width"]] == 1]
        ck(len(exploratory) == 1 and exploratory[0]["frozen_width"] == 32,
           "expected the single unpairable W32 scene")
        confirmatory = [r for r in cands if r["scene_sha256"] != exploratory[0]["scene_sha256"]]
        ck(len(confirmatory) == 171, f"confirmatory census {len(confirmatory)}")
        conf_sorted = sorted(confirmatory, key=lambda r: r["scene_sha256"])
        pair_count, pair_groups, w_pairs = 0, set(), collections.Counter()
        for i in range(len(conf_sorted)):
            for j in range(len(conf_sorted)):
                if i == j:
                    continue
                d, h = conf_sorted[i], conf_sorted[j]
                if d["frozen_width"] == h["frozen_width"] and d["source_group"] != h["source_group"]:
                    pair_count += 1
                    pair_groups.add((d["source_group"], h["source_group"]))
                    w_pairs[d["frozen_width"]] += 1
        ck(pair_count == 19622, f"frozen-W pairing {pair_count} != 19622")
        ck(w_pairs[31] == 19068 and w_pairs[34] == 554, f"W strata {dict(w_pairs)}")
        by_w = collections.Counter(r["frozen_width"] for r in confirmatory)
        option_a = {
            "schema": "JEV_A461_G5_G2_STAGE_A_OPTION_A_PACKAGING_V1",
            "confirmatory_scenes": len(confirmatory),
            "by_frozen_width": {str(k): v for k, v in sorted(by_w.items())},
            "exploratory_excluded": [{"scene_sha256": exploratory[0]["scene_sha256"],
                                      "source_group": exploratory[0]["source_group"],
                                      "frozen_width": 32,
                                      "reason": "no cross-group partner at frozen W=32 in the current pool"}],
            "frozen_w_cross_group_directed_pairs": {"total": pair_count,
                                                    "W31": w_pairs[31], "W34": w_pairs[34]},
            "w_stratification_rule": "donor/host pairs match on the SAME frozen W; W recorded per pair and "
                                     "reported as a stratification variable in all analyses; qualification is "
                                     "W-specific (the screened input is the frozen witness input)",
            "v2_1_amendment_resolution": "Option A adopted: no per-W witness expansion; width_profiles.jsonl "
                                         "remains a feasibility record only"
        }
        save(out / "option_a_packaging.json", option_a)
        produced.append("option_a_packaging.json")

        # ---------- deterministic N=124 slice (W31 tier fills first) ----------
        ck(by_w[31] >= N_RECOMMENDED, f"W31 tier {by_w[31]} < N {N_RECOMMENDED}")
        w31 = sorted((r for r in confirmatory if r["frozen_width"] == 31),
                     key=lambda r: r["scene_sha256"])
        slice_n = w31[:N_RECOMMENDED]
        ck(len(slice_n) == N_RECOMMENDED, "slice size")
        groups_in_slice = len({r["source_group"] for r in slice_n})

        # ---------- 1:1 physical forward manifest ----------
        per_run_scenes = (HARD_CAP - REPLAYS_PER_RUN) // 3   # 42
        ck(per_run_scenes * 3 + REPLAYS_PER_RUN <= HARD_CAP, "run composition")
        manifest, forward_index = [], 0
        scene_runs = [slice_n[i:i + per_run_scenes] for i in range(0, len(slice_n), per_run_scenes)]
        for ri, chunk in enumerate(scene_runs, 1):
            first_old_index = None
            for r in chunk:
                for arm in ("old", "new", "SA"):
                    forward_index += 1
                    if arm == "old" and first_old_index is None:
                        first_old_index = forward_index
                    manifest.append({"forward_index": forward_index, "run": ri, "kind": "primary",
                                     "scene_sha256": r["scene_sha256"], "arm": arm,
                                     "frozen_width": r["frozen_width"],
                                     "cell": r["cell"], "source_group": r["source_group"],
                                     "token_ids_sha256": r["token_ids_sha256"][arm],
                                     "state_token_len": r["state_token_len"][arm]})
            for _ in range(REPLAYS_PER_RUN):
                forward_index += 1
                manifest.append({"forward_index": forward_index, "run": ri, "kind": "replay",
                                 "replay_of_forward_index": first_old_index,
                                 "scene_sha256": chunk[0]["scene_sha256"], "arm": "old",
                                 "frozen_width": chunk[0]["frozen_width"],
                                 "note": "determinism replay of this run's first primary old arm"})
        runs_used = collections.Counter(m["run"] for m in manifest)
        primary_n = len([m for m in manifest if m["kind"] == "primary"])
        replay_n = len([m for m in manifest if m["kind"] == "replay"])
        ck(primary_n == N_RECOMMENDED * 3, "primary count")
        ck(replay_n == len(runs_used) * REPLAYS_PER_RUN, "replay count")
        ck(all(v <= HARD_CAP for v in runs_used.values()), "run cap")
        total_calls = primary_n + replay_n
        with (out / "stage_a_forward_manifest_N124.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for m in manifest:
                f.write(canon(m) + "\n")
        produced.append("stage_a_forward_manifest_N124.jsonl")

        # ---------- admission draft ----------
        draft = {
            "schema": "JEV_A461_G5_G2_STAGE_A_ADMISSION_DRAFT_V1",
            "id": "A461_G5_G2_STAGE_A_DONOR_DISCOVERY_GPU",
            "status": "DRAFT_PENDING_NARROW_REVIEW_AND_USER_AUTHORIZATION",
            "option": "A (frozen-width same-W pairing; the W32 scene exploratory)",
            "recommended_N": N_RECOMMENDED,
            "sizing": {"descriptive_rate": "2/56 T2 construction cohort",
                       "E_K_at_N124": round(N_RECOMMENDED * 2 / 56, 2),
                       "P_at_least_2_binomial_approx": 0.938,
                       "caveat": "IID approximation across construction strata; not a guarantee; "
                                 "<2 qualified donors => HOLD per design"},
            "composition": {"primary_forwards": primary_n, "replays": replay_n,
                            "total_physical_calls": total_calls, "runs": len(runs_used),
                            "max_calls_per_run": max(runs_used.values()),
                            "groups_in_slice": groups_in_slice,
                            "W_strata_in_slice": {"W31": N_RECOMMENDED}},
            "runner_must_enforce": [
                "per-forward append-only raw row (full 4-question logits, token-ids SHA, run/scene/arm)",
                "admission receipt with physical pre-hook ledger == receipt == this manifest count",
                "replays bitwise-equal to their referenced first primary old arm",
                "each run <= 128 physical calls including replays",
                "inputs read by git blob (roster blob pinned at admission, corpus SHA); no other scene",
                "fail-closed: keep all completed rows on any gate failure"
            ],
            "qualification_rule": "strict: old C=false, new C=true, SA C=false on the frozen witness inputs; "
                                  "per-stratum (W, cell) reporting; <2 qualified => HOLD",
            "not_included": ["Stage-B budget (separately admitted after >=2 qualified donors)",
                             "any claim of line-level never-seen groups (tier-1 does not exist)"]
        }
        save(out / "stage_a_admission_draft.json", draft)
        produced.append("stage_a_admission_draft.json")

        receipt.update(status="COMPLETE_A461_G5_G2_STAGE_A_ADMISSION_DRAFT",
                       option_a_summary=option_a,
                       slice={"N": N_RECOMMENDED, "groups": groups_in_slice,
                              "W31": N_RECOMMENDED},
                       manifest={"total_calls": total_calls, "runs": len(runs_used),
                                 "max_per_run": max(runs_used.values()),
                                 "primary": primary_n, "replays": replay_n},
                       gpu_blocked=True,
                       next_gate="narrow review of this admission draft -> fresh explicit user authorization -> "
                                 "Stage-A GPU runner (separate script, pilot-grade gates)")
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G5_G2_STAGE_A_ADMISSION_DRAFT", error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-2000:])
        code = 2
    with (out / "execution_receipt.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    produced.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(canon(receipt))
    return code


if __name__ == "__main__":
    sys.exit(main())
