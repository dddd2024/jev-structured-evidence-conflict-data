# A461-G5-G2 Stage-A GPU Screen Runner G0 — independent code review

**Date:** 2026-10-26. **Verdict:** **`REJECT_P0_RUNTIME_REPLAY_AND_BATCH_LEDGER`**. This rejection is strictly for the pinned GPU execution runner, not for the already verified CPU roster or 378-row manifest. **No GPU execution was conducted by this reviewer; no new model-qualified donor exists.**

## Reviewed immutable source/inputs

- New runner `research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/A461_g5_g2_stage_a_gpu_screen_runner_g0.py` Git blob **`3435cdd517976432e311826faaf41d809154c911`**, submit commit **`b6f2ff6bbfa8796b3bd5483c0efb4d14e62c871a`**.
- `G2_STAGE_A_G0_PREFLIGHT/execution_receipt.json` Git blob **`fc8f625e4e929e4665ab68bfc815e99f784238ba`**, status `COMPLETE_A461_G5_G2_STAGE_A_PREFLIGHT`, `token_gate=372/372 PASS`, `gpu_model_loads=0`, `native_model_forward_calls=0`.
- Previously audited manifest `G2_STAGE_A_ADMISSION_DRAFT/stage_a_forward_manifest_N124.jsonl` blob **`01ca53908cc73276d4f6821a4892f05e47e02a15`**, 378 rows, 372 primary + 6 replays. Previously audited roster `G2_STAGE_A_CPU_FREEZE_REAL/stage_a_candidate_roster.json` blob **`1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8`**.
- Admission at CPU preflight: runner self Git blob matches `3435cdd5`, but `blind_review_verdict=null`, `explicit_user_gpu_approval=false`. No approval or GPU inference occurred.

## P0-1 (deterministic): first replay accesses missing `token_ids_sha256` field

All **six** frozen replay entries (forward indices **127, 128, 255, 256, 377, 378**) have only reference metadata and **no `token_ids_sha256`, no `state_token_len` or `source_group`**. In source **lines 264–268**, the replay path resolves the old request but calls `run_forward(ref_req, entry)` on the unchanged replay manifest entry. In source **line 239**, the shared `run_forward` function unconditionally accesses:

```python
ck(hids(enc["ids"]) == entry["token_ids_sha256"],
   "encode != frozen witness " + entry["scene_sha256"][:8])
```

For the first replay **#127**, this is an unconditional `KeyError('token_ids_sha256')` **before replay model.forward**. If the preceding primary requests all succeed, the attempted GPU execution would already have **126 physical primary forwards** and **126 persisted primary raw rows**, but the first replay fails, leaving a FAIL receipt. This is **not** a failure of replay bitwise determinism or a model negative outcome. The CPU preflight passed because its tokenizer/roster gate iterated **only the 372 primary rows** and its replay validation checked only reference existence/arm/scene identity, never exercised the GPU `run_forward` input-validation path for a replay.

**Required fix**: resolve every replay entry's canonical frozen token SHA, length, cell, group and width **from the referenced primary-old row** at the CPU plan/materialization gate; either materialize an execution entry with those inherited fields or have `run_forward` accept a separate immutable `effective_expected_sha` derived from the referenced primary. Keep the original manifest unchanged and unchanged blob as source of truth. In the CPU G0 path add a **378/378 executable input-contract check**, asserting all six replay effective IDs SHA and metadata match their referenced primaries and that the same effective entry can be handed to `run_forward` without a missing-field path. Include simulated replay logit-equality success and failure tests without GPU; don't claim `372/372` implies end-to-end 378/378 forward-path readiness.

## P0-2 (resource contract): three logical batch labels are not enforced as three bounded physical runs

The consent/protocol contract was **378 physical forwards in three capped runs (128,128,122)**, with per-run cap **128**, replay included and separate batch accountability.

The new runner **line 233** checks only global `receipt["native_model_forward_calls"] < TOTAL_CALLS` where `TOTAL_CALLS=378`. Its execution **lines 262–276** is a single uninterrupted `for entry in manifest` in one Python invocation, one checkpoint load and one global `model.lm` prehook counter. The source **lines 140–147** checks the *declared* manifest group sizes before model load, and **line 278** checks only the **final global physical == 378**. There is **no runtime per-run pre-forward `<=128` gate, no per-run physical-counter reconciliation, no per-run receipt/failure boundary or separately admitted invocation checkpoint**. Merely carrying `run=1,2,3` tags in the manifest cannot by itself establish that the 128 per-*run* execution cap was enforced. If the program is actually launched as one run, it proposes 378 physical calls inside that run.

**Required fix**: give each of the three batches an explicit execution boundary and physically enforced cap, reporting exact physical prehook counts **run1 128; run2 128; run3 122**, with fail-closed receipts and durable append-only raw outputs per independently admitted batch. Either (A) run three independent invocations with per-batch admission and preserved total budget state, or (B) formally document and independently approve a batch-scoped execution model with per-batch prehook counters and receipts inside one process, if allowed by the frozen research SOP. Do **not** silently redefine `run` or use the `approved_max_native_forwards=378` aggregate field to bypass per-run 128. Make the CPU mock/trace enforce transitions between batches and prove an injected 129th physical call in any batch fails **before** invoking the model.

## Additional P1 audit improvements (not reasons to restart data construction)

- The CPU preflight recomputes frozen input SHAs against the **roster** for the primary records, but currently does not itself assert the **manifest** primary `token_ids_sha256`, `arm`, `source_group`, `state_token_len` and `frozen_width` tuple before load. The earlier independent manifest audit did validate these, but source regression should include it so a future manifest change fails in G0 rather than wasting GPU. All 378 frozen entries need a common canonical executor contract.
- The routine comments promise raw rows **before any post-forward gate**, whereas source lines 243–246 validate outlogits length and finite values *before* appending. Distinguish valid-logit post-forward storage from physical-attempt evidence when model outputs are malformed/forward throws; always preserve prehook physical attempts and FAIL receipt. Neither length nor numerical validity can be inferred from CPU preflight.
- Replay raw metadata currently uses `entry.get("cell")`, `entry.get("source_group")` and `entry.get("replay_of_forward_index")`; absent replay cell/group fields would produce **null** metadata even after token SHA fix. Materialize these from referenced primary for complete traceability.
- `ck(str(out).startswith(str(ROOT)))` is only a lexical path-prefix check. Use resolved `out.is_relative_to(ROOT)` to enforce all server artifacts remain inside `~/wjc`; ensure cache/TMPDIR parents exist or fail early.
- Preserve scientific limits: screened 124 selected samples are **W31 only**, stratified **106 accept/18 wait**, 17 **pilot-relative** source groups. Strict qualification is per frozen W31 witness; two positives from the same source group do not establish independent-group replication. No Stage-B GPU budget or Key-only causal claim follows from this screening.

## Current evidence and next narrow review

**PASS already established:** the immutable 378-row manifest/roster, source scene construction and reported G0 primary tokenizer gate are internally consistent. The CPU preflight itself reports no GPU model calls. The runner code hash is properly pinned and the admission gate correctly refuses GPU when review/approval fields are absent.

**REJECT pinned `3435cdd517976432e311826faaf41d809154c911`.** Do not set its `blind_review_verdict` to PASS. Do not begin the 378-forward GPU discovery stage; the first replay is a deterministic crash and 128/run physical contract is not yet implemented. The next fixed deliverable is **`A461_G5_G2_STAGE_A_GPU_SCREEN_RUNNER_G0_V2`** (CPU all-entries executor mock, replay inheritance, per-run physical counts/receipt), immutable new runner blob, new 0-GPU preflight receipt, and *only then* independent narrow delta re-review. After PASS, fresh explicit authorization for 378 physical calls across three bounded batches is still required.

No need to redo G5 native 28 forwards or the 172/171 candidate CPU inventory.
