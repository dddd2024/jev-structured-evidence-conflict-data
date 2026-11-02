# A461 mechanism route — handoff (2026-10-30, 00:10 +08:00)

Supersedes `A461_MECH_HANDOFF_20261028.md` for the current state. Its sections "How each stage was built" and "Gotchas" still apply.

**State at handoff:**
- The M10 GPU run is going on `REDACTED_RESEARCH_HOST`: 858 / 5244 rows at 00:09 (+08:00). At about 1.5 s per call it should finish around **02:00 (+08:00) on 2026-10-30**.
- `M10_gpu_launch.sh` (detached with `setsid nohup`) runs the frozen M10 analysis automatically when the run exits, and only if the receipt says COMPLETE. It then writes `M10_AFTER_RUN.done`.
- The local watcher dies at shutdown. That does not matter, because nothing depends on the local machine.
- Nothing else is running.
- The final paper-level audit has **not** been triggered; it needs the user's go-ahead.

## Chain so far (all preregistered, self-tested, bitwise-anchored)
| stage | prereg / result | finding |
|---|---|---|
| M1 | c235549 | REL_SUPPORTED: the L11 span carries a round-specific conflict evaluation |
| M2 | 3d561c9 / ca949e7 | MIXER_WRITER@L11: the L11 `self_attn` output at the span repairs 51/104; the MLP never does |
| M3 | 342e559 / e9d9746 | Heads 8–14 cooperate; head 10 is most necessary |
| M4 | 4c8de7a / f5bbf87 | The write reads the bulk context (OTHER_ITEMS + CONTEXT), not the partner; V_NONE |
| M5 | 7187842 / 695f4fe | BULK_DIRECTION + XD_HOLDS |
| M6 | 18aae99 | SHARED_DONOR_COMPONENT + NOT_LOWRANK_LE64: the mean-donor BULK patch `meanD_host` gives S 39 |
| M7 | edc49cb | NOT_DELTA_LOWRANK / NOT_MEANDIFF / RC_INSUFFICIENT |
| M8 | d1d9125 | XDELTA_LOWRANK:16 + TWOPART:16 on the pooled contrast; CONTRAST_NONADDITIVE |
| M9 | 7124fd7 / da03730 | GAIN_MIXED, GAIN_TMIN:1.0. CONTRAST_IN_WRITER_HEADS (chW 39, chR 0, ch10 25), but the head slices were not size-matched. CONTRAST_OUTSIDE_COMMON_SUBSPACE_UNRESOLVED (cperp 39, cpar 27, one-seed null crand 7 > 5). Only hosts 1fb5, 264c and 4bcb respond |
| **M10** | **73784df / pending** | size-matched head slices; contrast at span position 29 vs 30; where the common shift must be; a 5-seed split null; finer t ∈ {0.6..0.9} |

New fact from the M9 captures: the pooled contrast c = mean_D B(ROUND) − mean_D B(new) is nonzero only at span positions 29 and 30 (‖c‖ ≈ 7 and ≈ 2–4). ROUND changes the token at 29.

## M10 pins (`A461_MECH_M10_HEADS_POSITIONS_GPU/`)
- **Scripts:** freeze `3d43da50`, runner `7f2577cc`, self-test `bb78f50d` (PASS 16/16), analysis `e0f28aac`.
- **Frozen inputs:** manifest `c67df778`, design `f127d850`, admission `2b843f94` (`admission_m10_gpu_R1.json`; the server copy equals the committed blob).
- **Run size:** 25 arms × 208 rows plus 44 captures = 5244 forwards in 41 batches ([128]×40 + [124]).
- **Pre-model gate:** passed, in `M10_GPU_R1_PRE_MODEL_GATE/` on the server. Run log `M10_GPU_R1.log`.

## Resume M10 (next session)
1. On the server (`ssh REDACTED_RESEARCH_HOST`, `cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1`):
   - `cat M10_AFTER_RUN.done` should read `run exit 0 analysis exit 0 …`.
   - The receipt `M10_GPU_RUNS/ATTEMPT_R1/execution_receipt.json` should show status `COMPLETE_A461_MECH_M10` and 5244 rows.
   - `M10_ANALYSIS_R1/m10_analysis.json` should exist; its log is `M10_ANALYSIS_R1.log`.
   - If `.done` is missing, the run is still going: check `wc -l M10_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m10.jsonl`. Do **not** use a `pgrep` pattern that matches itself.
   - If `.done` reads "not COMPLETE", read the receipt's `error_message` and `M10_GPU_R1.log`.
2. Check the consistency gate in the analysis first:
   - `full` S 51, bitwise vs M3;
   - `meanD_host` S 39, bitwise vs M6;
   - the 7 M9 arms bitwise vs M9, with S 39 / 39 / 25 / 0 / 27 / 39 / 7.
   - If it fails, every verdict is INCONSISTENT_WITH_M3_M6_M9.
3. Fetch the outputs into the local stage dir, as for M9, and verify each with `SHA256SUMS`. The captures stay on the server.
   - `M10_GPU_R1/`: everything in `ATTEMPT_R1/` except `captures/`, plus `M10_GPU_R1.log` and `pre_model_gate_receipt.json` (taken from `M10_GPU_R1_PRE_MODEL_GATE/execution_receipt.json`).
   - `M10_ANALYSIS_R1/`: `m10_analysis.json` and its log.
4. Write `M10_RESULT_R1.md`, modelled on `../A461_MECH_M9_GAIN_HEADS_SPLIT_GPU/M9_RESULT_R1.md`. It needs:
   - the verdicts for Q1–Q5 (heads_sm with +H10 / +WX10, position, shift location, SPLIT_NULL5 and the re-applied subspace verdict, GAIN_TFINE);
   - the per-arm S / SPEC / SUF / C table;
   - per-host S, which is the honest unit (effectively 8 host replicates, 3 responsive);
   - the energy shares, α and capped shares, the position energy check, and leave-one-group-out.
5. Commit (`git add --sparse`; **delete any `__pycache__` first**), `pull --rebase`, push. Retry on a TLS failure.
6. Update memory: `a461-g2-stage-a-status.md` and the line in `MEMORY.md`.
7. Ask the user about next steps; do not trigger the final audit without asking.

## Notes
- **Derive scripts are not committed.** They are in the old session scratchpad `REDACTED_WINDOWS_HOME\AppData\Local\Temp\claude\F--jev\b0ee449e-21d8-4358-87ef-f4fa3139d4e3\scratchpad\`: `derive_m10.py`, `M10_selftest_launch.sh` and `M10_gpu_launch.sh`. The launch script is also on the server. If Temp is cleaned, derive M11 from the committed M10 files instead.
- **Admission line endings.** The local working copy of the admission has CRLF. Upload the committed bytes (`git show HEAD:<path>`) so the server copy matches blob `2b843f94`.
- **Other commits.** A570 / A571 (literature screening, "M9 energy confound audit") were pushed by another author on 2026-10-29. Read them before designing M11; the energy confound is exactly what M10's size-matched arms test.
- **Same notes as before:** governance, venv Python, the thread limit and blob identity are unchanged from the 2026-10-28 handoff.
