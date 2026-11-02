# A461 mechanism and safety route: handoff (2026-11-01, 01:20 +08:00)

This supersedes `A461_MECH_HANDOFF_20261029.md` for the current state. The "how each stage was built" and "gotchas" notes of the 2026-10-28 handoff still apply. The user shut the local machine down. Nothing below depends on it.

## User decisions in force
- **2026-10-30 grant:** stages may be designed and run without asking. Ask before the final paper-level audit and before anything outward-facing.
- **Safety target (2026-10-31):** "S2 + diagnostic monitor". No S4.
- **High standard (2026-10-31, "按照高标准的来"):** the order is M20 necessity → M21 causal readout → M22 second-model replication → paper package. Capture release and the final audit both need the user's go-ahead.
- **Reporting:** every stage reports its safety value in standard V1 §9 order.

## Done today (all pushed)
| stage | commits | headline |
|---|---|---|
| Consolidation M1–M16 | 350fa77 | Tier A KEEP / B CONDITIONAL / C DOWNGRADE |
| S2 endpoint + G−1 + threat model | 4b69b50, 84bd0a0 | kev-4B false accept 66.9%, natural false veto 0 on old / SA; SecJev 55.7% + 33.1% wait, false veto 8.9% |
| M17 false veto | 84bd0a0 / dfa3aac | `full` NONSELECTIVE. The frozen v1 analysis had a bug, fixed in v1.1 and documented as a deviation |
| M18 monitor | ebd82ff / c56729c | ENCODED_AT_L11 (0.993) + ABOVE_SURFACE; GENERIC_MATCHES → infrastructure only; MONITOR_USEFUL; near-miss natural false veto about 5% |
| M19 readout gain (probe direction) | 50227eb / f2256e8 | INERT; probe direction about 0.6% / 0.06% of \|h\|; orthogonal to the head gradient |
| M20 necessity | c286b38 / 8b87ff9 | NEC_FULL_PARTIAL / NEC_BULK_PARTIAL; `bulk_round_self` lowers M in 14/14 donors, recognition lost in 9/14 |
| M21 prereg | bc61ce9 | see below |

## Running on `REDACTED_RESEARCH_HOST` (detached; it does not depend on the local machine)
**M21 GPU run (`M21_gpu_launch.sh`):**
- At 01:15 it had written 195 of 6820 rows. At about 1.5 s per forward it should finish around **04:00 +08**.
- When the receipt reads COMPLETE, the launcher runs the frozen analysis and writes `M21_AFTER_RUN.done`.

**M22 self-test rerun (`M22_selftest_launch.sh`):**
- It writes `M22_SELFTEST.done`.
- R0 failed 9/13 and is kept as `M22_SELFTEST_R0_FAILED_FAKE_HEADS*`. The defect was in the self-test fixture: the fake model is 16 × 4 wide, while the runner checked the width as 8 heads × head_dim.
- The fix reads the `o_proj` width from the module, and the GPU separately checks that SecJev's width is 8 × 256 = 2048.
- New runner blob: `caf75530`.

## Resume steps (next session)
### 1. M21
1. On the server, `cat M21_AFTER_RUN.done` should read `run exit 0 analysis exit 0`. If it is missing, check `wc -l M21_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m21.jsonl`.
2. Fetch into `M21_GPU_R1/` everything in `ATTEMPT_R1` except `captures/`, plus `M21_GPU_R1.log` and `pre_model_gate_receipt.json` (from `M21_GPU_R1_PRE_MODEL_GATE/`).
3. Fetch `M21_ANALYSIS_R1/m21_analysis.json` and `analysis.log`.
4. Verify the fetched files against the run's `SHA256SUMS` (non-capture entries), then rewrite the local `SHA256SUMS`.
5. Write `M21_RESULT_R1.md` in §9 order, using the per-layer verdict rule:
   - CAUSAL_SELECTIVE;
   - CAUSAL_PUSH_ONLY;
   - NOT_READABLE;
   - NONSELECTIVE.

   Also report the push and gain dose sizes and the head-input geometry of the mean-difference direction. Use the interpretation fixed in the prereg.
6. Commit, push, and update memory.

### 2. M22 (SecJev-0.8B replication of M18)
1. Read `M22_SELFTEST_R1.log`; it should be 13/13.
2. Fetch `M22_SELFTEST_R1/` (the log, receipt and dry-run log) and `M22_SELFTEST_R0_FAILED_FAKE_HEADS/` (the log and receipt) into the stage directory.
3. Fill in the "Self-test" section of `PREREG_M22_R1.md`: R1 PASS, plus the R0 failure and fix.
4. **Commit the prereg before any GPU forward.** The M22 files are in the WIP commit of this handoff. The admission already pins runner `caf75530` and SecJev identity `5f62d083…`.
5. Upload the admission as the committed bytes (`git show HEAD:...`).
6. Run the pre-model gate:

   ```
   A461_mon_m22_runner_v1.py --repo-root ~/wjc/jev-checkout --admission admission_m22_gpu_R1.json --manifest M22_FREEZE_R1/m22_manifest.jsonl --design M22_FREEZE_R1/m22_design.json --stage-a-raw M18_INPUTS/raw_secjev_stage_a.jsonl --out $PWD/M22_GPU_R1_PRE_MODEL_GATE --pre-model-gate-only
   ```

7. Launch only after M21 has freed the GPU.
   - **The M22 GPU launch script has not been written yet.** Derive it from `M18_gpu_launch.sh`: change the runner and analysis names, use `--stage-a-raw M18_INPUTS/raw_secjev_stage_a.jsonl`, and drop `--m3/--m6`.
   - Run size: 620 forwards, about 15 minutes, then the analysis.
8. Write `M22_RESULT_R1.md`.

### 3. Then the paper package
- v10 manuscript: a mechanism section built from the consolidation plus M17–M22.
- `CLAIMS_EVIDENCE_MAP`, `LIMITATIONS` (with all the failed and edge criteria), `NOVELTY`.
- A recompute script.
- Checking the V3 P1/P2 leftovers.
- **Ask the user before** the capture release (outward-facing) and before the final audit.

## Mechanism statement, as of M20 (kev-4B)
1. The conflict is decodable early: at the append span from L3 (M18).
2. **L11:** attention heads 8–14 read the context and write a round-keyed verdict into the span. It is sufficient in hosts (M1–M5) and necessary in most donors under the round swap (M20). It is partly redundant: the strong donors survive.
3. Downstream layers apply the L11 verdict without re-checking the round. Author validity is checked separately (M17, post hoc).
4. In the missed scenes the conflict is still present at the decision token (M18). It lies in a direction orthogonal to the head's reject − accept gradient, and gain along the probe direction is inert (M19). M21 decides whether a high-energy direction can drive the readout.

## Gotchas found today
- **Sparse checkout:** `git pull --rebase` re-applies the sparse patterns and silently drops new stage directories from the working tree. Run `git sparse-checkout add research/rounds/<stage>` for each new stage. M17, M18 and SAFETY were added after the fact.
- **Analysis inputs:** a raw-row field that is only in the manifest (`anchor_of`, M17) is not copied by the runner. The analysis must read it from the manifest.
- **Fake model:** it has a fixed width (64) and 16 × 4 heads. Self-tests on a model with a different width or head count need synthetic fixtures (M19 directions, M22 heads).
- **Paths:** Windows Python cannot read the shell's `/tmp`. Use repo-relative or scratchpad paths.
