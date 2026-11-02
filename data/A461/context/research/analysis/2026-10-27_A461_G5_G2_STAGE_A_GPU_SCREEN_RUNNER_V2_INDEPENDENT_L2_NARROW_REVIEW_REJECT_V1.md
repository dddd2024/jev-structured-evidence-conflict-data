# A461-G5-G2 Stage-A GPU Screen Runner V2 — independent narrow L2 engineering review

**Date:** 2026-10-27  
**Verdict:** `L2_REJECT_P0x2_P1x2` / `GPU_NOT_ADMITTED`  
**Scope:** Review of the newly frozen V2 runner and its L1 packet against the already reviewed scientific/CPU roster and manifest. **Static independent source review plus deterministic offline manifest re-partition check. No server execution, GPU loading, native model forward, or new scientific experiment was performed by this reviewer.** This report does not overturn the previously passed CPU data/roster/manifest audit.

## Pinned artifacts

- PR/issue handoff: [JEV issue #2](https://github.com/dddd2024/jev/issues/2), latest V2 L1 owner receipt at comment `6433673528`.
- Submitted commit: [ff7cd52](https://github.com/dddd2024/jev/commit/ff7cd52b84ace51e91b468923c821148f65dfd40).
- Runner `A461_g5_g2_stage_a_gpu_screen_runner_g0_v2.py`: blob `b0b9f6eea2e43006e743d91696f5bb8e8464c3ee`.
- FakeModel: blob `28852e69facccbe691d03297a0d4367ef2f19e94`; L1 suite: `e036eced3adf4f5e779e49cf255941688023b37f`.
- L1 matrix and receipt: reported **27/27 PASS**, full FakeModel path 378/378, prehook ledgers 128/128/122, 6/6 replay bitwise with negative-path fault tests; no GPU in L1.
- Frozen input blobs (no change requested): manifest `01ca53908cc73276d4f6821a4892f05e47e02a15`; roster `1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8`.

## Accepted V2 repairs (not repeated rejections)

1. Old P0 replay KeyError: V2 `effective_entries()` (lines 107–134) checks same-batch prior primary-old reference and inherits token ID SHA, state length, width, cell and source group. L1 checks 6 replay references, four negative mutations, logit success/failure and non-null output fields.
2. Old P0 missing per-batch runtime counters: V2 `batch_guard()` and the physical pre-hook ledger (lines 137–141, 349–367, 408–433) now implement in-process batch transactions; L1 reports 128/128/122 with injected hidden extra-call rejection in each batch.
3. Prior P1 manifest/roster tuple checks, forward-attempt receipts and output directory-relation checks have concrete code/test evidence (lines 259–301, 355–403, 447–472). These fixes are credited.

**However, L1 PASS is not L2 admission.** Below are independent blockers on the *GPU entrypoint* and its approved resource envelope.

## P0-1 — Frozen GPU plan and input blob identity are still overrideable

**Evidence:** V2 CLI lines 162–167 expose `--roster-blob`, `--manifest-blob`, `--g5v2-questions-blob`, `--expect-total` and `--expect-batches`. The runner reads those attacker/operator-supplied values at lines 181–191 and 233–240 and validates `sum(expect_batches)==expect_total`, `approved_batches==len(expect_batches)`, `approved_max==expect_total` (GPU mode). **It never requires `a.expect_total==378`, `expect_batches==[128,128,122]` or `(a.roster_blob,a.manifest_blob,a.g5v2_questions_blob)==(BLOB_ROSTER,BLOB_MANIFEST,BLOB_G5V2_PAIRS)` for the GPU backend. Nor does it require every batch cap ≤128.** Binding only the runner self-blob to L2 review does not bind these experiment inputs.

**Constructive CPU-only counterexample:** Independently parse the actual 378-row frozen manifest (`01ca5390`): 372 primary rows = 124 complete three-arm scenes and six replay rows. Repartition the *same* 124 three-arm scenes into 44/40/40 scenes, assign two replay rows to each batch pointing to its own batch's first primary-old, and renumber forward_index contiguously. The resulting plan has **378 calls and three batches 134/122/122**; all six replay refs are earlier, primary-old, same-run, same-scene; there are still 124 unique scenes, three distinct arms per scene, same original token SHA and roster tuples, and all inputs remain W31. Static shape/identity checks admit this plan when supplied as a different manifest blob with `--expect-batches 134,122,122`. The GPU receipt can still say 378 calls, three batches, with the approved runner blob; hence the hard ≤128/batch contract can be bypassed. **This is a static source/manifest counterexample, not a real GPU attempt.**

**Remediation:** In `--backend gpu`, reject any override of the exact approved manifest, roster, questions, `expect-total=378`, `expect-batches=[128,128,122]`, and enforce `cap<=128` at admission and at the per-batch physical guard. Bind the exact input blobs and per-batch plan in the signed/reviewed admission receipt and verify equality before loading weights. The synthetic override arguments may remain available **only** in isolated L1_FAKE mode. Add negative L1 tests that attempt alternative valid-but-unapproved manifest/plan/blob values through the actual GPU admission branch (still refusing before load).

## P0-2 — No authoritative durable cumulative quota/attempt reconciliation

**Evidence:** Lines 210–215 read `cumulative_calls_already_consumed` directly from the caller-provided admission JSON (default **0**) and check `consumed+expect_total<=approved_max`. Per-call check at lines 363–367 uses only that submitted `consumed` plus this process's in-memory `physical[0]`. A run/attempt identifier is hard-coded into an informational receipt (line 184), but there is no lookup, lock, transactional reservation, or reconciliation with prior server job receipts and raw outputs. Output path exclusivity (lines 173–176) prevents overwriting **the same** directory, not reusing the same approval in a **different** output directory. The L1 `abort_resume_cumulative_count_no_overrun` test manually sets `consumed=4` (test suite lines 371–380): it proves correct rejection **conditional on the supplied number being accurate**, not recovery of actual spend after process termination.

**Failure scenario:** After some physical forwards followed by a crash/kill (or even after completing 378 calls), a second invocation with a new `--out` and the original admission JSON still saying `consumed=0` can pass the same global budget pre-check and start the plan again, consuming another approval's worth. Even when the crash-path receipt is absent, the runner itself does not stop to reconcile evidence. Thus the claim `dropout/resume cannot overrun the approval` is not yet proven.

**Remediation:** Pin one admission ID and run/attempt lineage, enforce a lock plus an authoritative append-only cumulative physical ledger under `~/wjc`, and reconcile persisted raw/attempt receipts and any external GPU jobs before permitting another attempt. Fail closed on missing/ambiguous prior ledger or stale authorization; do not accept a caller-supplied `consumed=0` as proof. Add an L1 subprocess two-invocation test using **the same approval and different output directories** following partial and complete simulated runs, plus an abrupt-stop/missing-final-receipt case. Any redesign should retain frozen original data.

## P1-1 — Runtime model/base/tokenizer hashes not admission-pinned

Paths `CKPT`/`BASE` and `SOURCE` are constants (lines 41–45), but the GPU load (lines 333–343) does not compare current checkpoint/config/model/base/tokenizer/SOURCE content SHA against an expected frozen identity. The tokenizer JSON SHA is recorded in the receipt (line 278) but not checked against a pinned approved hash. This allows a changed weight/tokenizer at an unchanged path to evade L2 provenance. The full token SHA gate catches many tokenizer changes but not weight changes. Require explicit pinned hashes/version identifiers verified before model load and persisted in the execution receipt.

## P1-2 — L1 tests do not cover authorized GPU-branch admission shape

L1 correctly tests rejection of `L1_FAKE` when `--backend gpu` is requested, but never supplies a syntactically approved, blob-pinned GPU-mode admission to exercise the GPU-branch **up to but not including model load**, including the negative tests for changed frozen plan/manifest. This is the coverage gap enabling P0-1 and should be covered using a `--pre-model-gate-only` mode that enforces all actual GPU admission conditions without CUDA.

## Verdict and immediate next action

- **`L1_EVIDENCE_RECEIVED`**: acknowledge 27/27 L1 report and validated prior P0 repairs.
- **`L2_REJECT_P0x2_P1x2`** for exact runner blob `b0b9f6ee...`: GPU remains **0 authorized by this review**. Never set `blind_review_verdict=PASS` on this blob.
- Do **not** re-run G5 28 native forwards, repeat the 172/171 CPU scene census, or change the reviewed `01ca5390` manifest merely to fix the runner.
- Developer should address both P0 and affected P1 **in one L1 fix cycle**, freeze new code/test/receipt blobs, then request only one incremental L2 review on that release candidate. After a true L2 PASS, explicit user authorization remains a separate gate for 378 forwards / 128+128+122 physical batches.
- This report concerns engineering admission only; A511 CPU G−1 remains designed/not executed, and no L3 model-causality result is inferred here.

**Evidence limitation:** GitHub connector blob reads and independent static calculations only. No SSH/server GPU state was checked from this reviewer session. Test success, runtime model pinning, and process crash recovery are not independently claimed.
