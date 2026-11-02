# A461-G5-G2 Stage-A GPU Screen Runner V3 — Independent L2 delta review

**Date:** 2026-10-27  
**Verdict:** **`L2_REJECT_P0x1_P1x2`**, no GPU admission  
**Reviewed Git commit:** `1b6ccadf6454fd794776711edac66799d05f0939`  
**Frozen V3 runner blob:** `b78da9c0476f0558cd77fa9771c04d020830dede`  
**Scope:** Incremental L2 review after [V2 L2 rejection `277fdb7`](https://github.com/dddd2024/jev/blob/main/research/analysis/2026-10-27_A461_G5_G2_STAGE_A_GPU_SCREEN_RUNNER_V2_INDEPENDENT_L2_NARROW_REVIEW_REJECT_V1.md). Source inspection and independent deterministic control-flow simulation, with GitHub blob/receipt checks. **No SSH execution of the V3 runner, real GPU load, or new model forward by this reviewer.**

## Frozen evidence inspected

- Runner: `research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/A461_g5_g2_stage_a_gpu_screen_runner_g0_v3.py` at Git blob `b78da9c0476f0558cd77fa9771c04d020830dede`.
- L1 suite `A461_g5_g2_stage_a_l1_tests_v2.py` blob `06fcd8c7b920fbfc9fd0124e93866334fadb87e1`.
- Fake model `A461_g5_g2_fake_kev_model_v1.py` blob `4f9fef35c23725d0ab71948fc93e222e935e7b03`.
- V3 review packet `G2_STAGE_A_L1V2_TESTS/L2_REVIEW_PACKET_V3.md` blob `af1b90793831e8b89ad7b201a8faceb9cb713156`.
- L1 matrix blob `1ccb51d4e68241e257e08b66638d89edf4a5d6c4`: **46/46 self-reported PASS**, independently re-counted the JSON rows and PASS labels.
- Verified GitHub L1 full-fake receipts: `T3_fullpath/execution_receipt.json` blob `463905bd6a3a9835d129434ecd4caf9467be712c` reports 378 fake forwards and batch counts 128/128/122; its ledger `_quota/L1_FULLPATH_0001/ledger.jsonl` blob `9992e155431b362fdf9dddb720f4ecae312a9b5f` has **380 events**: 1 attempt_open + 378 reserve + 1 attempt_close; this exact check confirms the submitted fixture/receipt, not runtime GPU correctness.
- GPU-shaped pre-model gate receipt `P1_gpu_pre_model_ok/execution_receipt.json` blob `2383c0c93eea449dc79e722fdebb54ec61d9a440`: pinned identity verified, torch/model load count 0. The experiment plan blobs remained unchanged: manifest `01ca5390`, roster `1bc84bf5`, questions `66c1f95e`.

## Prior P0/P1 fixes credited

**V2 P0-1 frozen GPU input/plan bypass — FIXED in V3 source.** `gpu_pin_gate()` (lines 212–231) binds immutable blobs, exactly `378` calls and batch plan `128/128/122`, approved model identity, reviewed code blob and user approval. `batch_plan()` also requires every cap ≤128. The owner's attempted 134/122/122 and alternative input controls appear in the published L1 matrix.

**V2 P0-2 absence of authoritative cumulative ledger — substantially fixed.** `QuotaLedger` (271–304) takes an exclusive flock, appends/fsyncs reservation *before* model.forward (552–557), and reconciles known attempts and prior consumption; tests include reuse of the same ID, partial retry, SIGKILL at call 5, lost ledger and lock conflict. This is a material engineering improvement.

**V2 P1 model identity and pre-model GPU-shaped verification — implemented.** Source contains explicit SHA256 file-tree pins (28 CKPT + 8 BASE + 26 SOURCE files); GPU pre-model gate runs checks without loading torch/model.

These credited corrections remain valid regardless of the new blocker below. No need to reconstruct the G2 172/171 scene census or rerun historical G5 forwards.

## P0-1 — The physical pre-hook itself has no hard budget/cap enforcement at the batch's last entry

**Source proof:** V3 `run_forward()` calls `batch_guard(physical_by_batch[b], caps[b])` at line **541**, before one call to `model.forward(enc)` at line **557**. But the installed LM pre-hook at lines **527–530** merely increments `physical[0]` and `physical_by_batch`; it contains **no cap, global budget, or reservation check**. Batch-level equality is evaluated only after all planned entries (line **609**); `unreserved_physical` accounting happens only in the finalizer (lines **644–653**). FakeModel explicitly supports an extra hook firing *within* a forward, `doublefire@N` (FakeModel lines 66–71).

**Constructive deterministic last-entry cases** (same mechanism as the author's actual fake doublefire test, moved to a boundary the L1 matrix does not exercise):

| Batch | Fault | Guard before last model.forward sees | Prehook count after last model.forward | Cap | Immediate prevention? |
|---|---|---:|---:|---:|---|
| 1 | `doublefire@128` | 127 | **129** | 128 | **No**; fails only at batch close |
| 2 | `doublefire@256` | 127 (batch 2) | **129** | 128 | **No**; fails only at batch close |
| 3 | `doublefire@378` | 121 | **123** | 122 | **No**; fails only at batch close |

These counts were recomputed independently from the frozen batch boundaries and the exact source increment/guard order. This is **not a claim of observed excess real GPU work**: FakeModel's extra hook represents additional physical LM activity, whereas the independent check is static. It proves the advertised *hook-based pre-forward hard cap* is not actually enforced inside the hook. Existing L1 probes inject at 127/255/377 and rely on the *next* planned call being blocked; they therefore do not cover a last-entry overshoot. In a crash after the extra hook but before the finalizer, its **unreserved** activity may also be absent from the durable ledger despite being seen by the in-memory hook.

**Required repair:** enforce batch cap, global approval, and current-call reservation invariants **inside `bump()` before allowing an LM forward to start**. On the unexpected second LM prehook of one reserved forward, fail closed before the extra LM body runs, rather than incrementing and charging after the fact. Update the execution/attempt ledger to preserve the single reserved attempt's evidence and avoid treating blocked pre-hook calls as completed physical forwards. Add CPU full-run FakeModel tests `doublefire@128`, `doublefire@256`, `doublefire@378` and at least one abrupt-stop/recovery fault around the edge. Assert **observed permitted physical forwards never exceed 128/128/122, never exceed 378 globally, and any unauthorized additional LM call is denied at its own prehook rather than after batch close**. Re-run all unchanged positive and negative tests together.

## P1-1 — Reconciliation does not require ledger-opened attempt_manifest to exist and match

`reconcile_ledger()` lines 246–268 checks a ledgered *directory* is present (line 257), and detects unknown on-disk attempt manifests (lines 248–254), but it never asserts **every** `attempt_open` has a durable `out_dir/attempt_manifest.json` whose `admission_id`, `attempt_id`, `runner_blob` and directory match the ledger. A missing/modified attempt manifest while the directory remains would not by itself trigger the same fail-closed policy. The previous L1 “missing ledgered dir” test moves the entire directory; it does not test deletion/modification of just `attempt_manifest.json`.

**Required:** validate the reverse bijection (every opened ledger attempt → exactly one matching durable manifest) and negative-test removal/mismatch with remaining quota. If a crash happens strictly between `attempt_open` and writing `attempt_manifest` (lines 497–501), treat it as a special, provably zero-forward incomplete start; do not accidentally label it a completed attempt.

## P1-2 — Raw model evidence does not use durable fsync before later calls

`run_forward()` appends valid logits to `raw_native_logits_stage_a.jsonl` at line **584** via `append_line(raw_log, row)`, whose `sync` default is false (lines 102–109); reservations are fsync'd but raw logits are not. SIGKILL alone generally closes/flushed file handles, but a machine/power failure can leave durable spend with lost recent raw outputs. For the long-running evidence-first research contract, fsync the raw logits and attempt receipts at defined transaction points (preferably every forward or a bounded explicitly accounted checkpoint); add a storage/fault-injection check or clearly document durability limits. This is a provenance/recovery improvement, not evidence that existing uploaded raw results are wrong.

## Verdict and next minimal action

- **`L1_RECEIPTS_RECOUNTED`**: 46/46 matrix entries all PASS; GitHub full-path FakeModel receipt, pre-model receipt, and 380-event quota ledger agree with their claims. This is not independent server re-execution.
- **`L2_REJECT_P0x1_P1x2`**, bound *only* to V3 runner blob `b78da9c0...`. Do **not** set blind review PASS and do **not** spend GPU quota on Stage-A yet.
- Developer: fix hook-level hard-cap enforcement and the two focused evidence-integrity gaps in **one L1 iteration**, add last-call and power/metadata failure tests, keep original frozen manifest/roster and G5 results unchanged, then request only a narrow code diff review (not another full historical study audit).
- Separate user approval for **378 physical calls, 3 bounded batches** is still mandatory after any future `L2_PASS`.
- Stage-A GPU actual model forward and Stage-B white-box interventions remain **unexecuted/unadmitted** on this review's verified evidence.

**Evidence limitation:** Review is grounded in GitHub file blobs and independent deterministic arithmetic on the control flow; this reviewer did not access the authorized server or GPU and does not claim to have executed the V3 Python runner in its native environment.
