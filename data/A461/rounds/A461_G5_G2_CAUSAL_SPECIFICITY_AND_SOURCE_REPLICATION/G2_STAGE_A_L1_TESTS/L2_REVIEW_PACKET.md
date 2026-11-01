# A461_G5_G2_STAGE_A_GPU_SCREEN_RUNNER_G0_V2 — L2 review packet

Status: **L1 COMPLETE 27/27 PASS, 0 GPU, 0 native forwards.** Requesting ONE L2 narrow engineering review.
Not a GPU admission; `blind_review_verdict=null`, `explicit_user_gpu_approval=false`.

## Exact blobs under review

| file | git blob |
|---|---|
| `A461_g5_g2_stage_a_gpu_screen_runner_g0_v2.py` (runner) | `b0b9f6eea2e43006e743d91696f5bb8e8464c3ee` |
| `A461_g5_g2_fake_kev_model_v1.py` (L1 FakeModel) | `28852e69facccbe691d03297a0d4367ef2f19e94` |
| `A461_g5_g2_stage_a_l1_tests_v1.py` (L1 suite) | `e036eced3adf4f5e779e49cf255941688023b37f` |
| frozen manifest (unchanged) | `01ca53908cc73276d4f6821a4892f05e47e02a15` |
| frozen roster (unchanged) | `1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8` |

Server copies under `~/wjc/a461-g5-minimal-patch-pilot-20261025-v1/` hash to the same blobs.
Tested command (server, kev08b venv Python 3.12):
`python3 A461_g5_g2_stage_a_l1_tests_v1.py --repo-root ~/wjc/jev-checkout --out ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1/G2_STAGE_A_L1_RUN3`

## Review findings (3c4721da) → fix → L1 evidence

| finding | fix in runner b0b9f6ee | L1 test(s) |
|---|---|---|
| P0-1 replay rows lack `token_ids_sha256` → KeyError at call 127 | `effective_entries()`: replays inherit token SHA / state length / width / cell / source group from the referenced primary old row; same run, earlier index, same scene required; a replay field that disagrees with its primary is rejected | `primary_and_replay_all_call_contracts` (refs 127,128→1; 255,256→129; 377,378→257), `replay_effective_entry_negative_cases` (4 tampered manifests rejected), `replay_effective_entry_inherits_primary_metadata` (6 raw rows non-null), `replay_bitwise_pass`, `replay_bitwise_fault_fail` |
| P0-2 128 cap only a roster statistic; one global loop | Caps come from the frozen plan (run k → k-th of `128,128,122`), not the manifest. Three batch transactions run in sequence. Each has its own **pre-hook** physical ledger. Before every model call, `batch_guard` refuses the (cap+1)-th physical call of the open batch, and a check requires pre-hook count == recorded calls. Each batch closes with physical == planned == rows and writes `batch_receipt_run{k}.json` before the next batch starts. On failure, later batches show `NOT_STARTED` | `physical_cap_plus_one_batch{1,2,3}_refused_before_model`: a fault injects a hidden extra lm call at 127/255/377, so entries 128/256/378 are the 129th/129th/123rd physical call of their batch and are refused with the model **not** invoked (invocations 127/255/377). Also `all_batch_counts_exact`, `batch_guard_unit` |
| cumulative approval | `consumed + plan <= approved_max` at admission; per call `consumed + physical + 1 <= approved_max`; GPU backend needs exactly 378 / 3 batches; an `L1_FAKE` admission can never authorize the GPU backend | `attempt_extra_forward_before_model_must_fail`, `abort_resume_cumulative_count_no_overrun`, `fake_admission_cannot_authorize_gpu` |
| P1 manifest-vs-roster tuple re-check | preflight + run: all 372 primaries `(token SHA, state len, W, cell, group)` == roster; fresh-encode SHA **and** state length == roster | `corpus_to_roster_and_manifest_token_sha` (372/372 token + 372/372 tuple), `span_suffix_branch_and_question_gold_checks` |
| P1 "logits saved" vs "forward failed" | attempt rows: `FORWARD_FAILED` (model raised, no logits) vs `INVALID_OUTPUT` (returned, unusable); valid rows appended before any post-forward gate; failure receipt has `physical_prehook_count_at_failure` + per-batch | `forward_throw_keeps_attempt_receipt` (physical 4 charged, 3 successful), `post_forward_failure_keeps_raw_lines`, `nonfinite_shape_error_fail_receipt` |
| P1 path guard by string prefix | directory relation (`relative_to`, Python 3.8-safe); existing out dir refused | `output_realpath_inside_wjc_and_append_only`, `existing_out_dir_never_overwritten`; every test dir's `SHA256SUMS` lists exactly its files |

The full path on the real 378-row manifest with the FakeModel gives `COMPLETE`, physical 378, raw rows 1..378, batches 128/128/122 (`planned_forwards_all_covered`). Across all 11 runner receipts: gpu_model_loads=0, CUDA never initialized, network_calls=0.

## Disclosed for the reviewer

- The GPU load branch (checkpoint load, torch determinism flags) is unchanged from G0, and L1 does not execute it (by design). The fake backend shares every pre- and post-model gate with it.
- The L1 harness builds its mini fixture in a subprocess. When the fixture was built in the test parent, later runner children died from SIGINT during the numpy import, after the parent had loaded tokenizers in-process. This is a harness-only issue: runner code is unaffected, and it is recorded in the run logs (RUN1/RUN2 on the server, not committed).
- Science scope is unchanged from the PASS_DRAFT review 6991391c: W31 only, and same-group donors are not independent replications.

## After L2

L2 PASS bound to runner blob `b0b9f6ee` → a fresh explicit user approval for **378 calls / 3 batches** → GPU run → strict qualification analysis (<2 donors → HOLD) → L3.
