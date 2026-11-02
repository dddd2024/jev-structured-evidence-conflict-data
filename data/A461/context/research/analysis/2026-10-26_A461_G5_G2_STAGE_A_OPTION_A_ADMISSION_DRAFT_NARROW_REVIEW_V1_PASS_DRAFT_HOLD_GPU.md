# A461 G5 G2 Stage-A Option A admission draft — narrow independent audit

**Date:** 2026-10-26. **Verdict:** **`PASS_ADMISSION_DRAFT_DATA_AND_MANIFEST / NOT_ADMITTED_GPU`**. The submission is a reproducible CPU admission **plan**, not an executable frozen GPU runner or permission to consume inference budget.

## Exact submission and source identities

- Submission commit **`1f773ef5e8020834380d0a38f25097a293075eeb`**, Issue #2 request [6420429980](https://github.com/dddd2024/jev/issues/2#issuecomment-6420429980).
- Root `research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/`.
- `G2_STAGE_A_ADMISSION_DRAFT/stage_a_forward_manifest_N124.jsonl`, Git blob **`01ca53908cc73276d4f6821a4892f05e47e02a15`**, exactly **378** JSONL rows.
- `G2_STAGE_A_ADMISSION_DRAFT/stage_a_admission_draft.json`, Git blob **`f85f5fd14d80ffcbf533b861bee6d8370e93a5b3`**.
- `G2_STAGE_A_ADMISSION_DRAFT/option_a_packaging.json`, Git blob **`586196a5d42d218baac78e962eb1b44d926b50a0`**.
- `G2_STAGE_A_ADMISSION_DRAFT/execution_receipt.json`, Git blob **`f0b530974c630b920f67ecedda62b7a7578f5b9f`**, status `COMPLETE_A461_G5_G2_STAGE_A_ADMISSION_DRAFT`, GPU forwards **0**.
- Previously frozen source `G2_STAGE_A_CPU_FREEZE_REAL/stage_a_candidate_roster.json`, blob **`1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8`**, 172 scenes with actual old/new/SA token ids SHA, legal edits and span anchors.

**Method:** independent GitHub readback and row-by-row reconstruction of the 378-row manifest, checking each primary against source roster, replay reference resolution, full sequence and per-run budget; independently counted grouped source scenes, frozen width and strata. **No local/remote model inference was performed**; no GPU runner was present in this request.

## Source/manifest review: PASS

1. **Option A resolved correctly:** no retrospective change of donor width; each candidate uses exactly one previously frozen witness. The W32 orphan `run-231:980ea36b...` is exploratory excluded from current Stage-B pairing. The 171 potentially pairable candidates are **W31=145/W34=26**. Independent across-group directed pairing recalc **19,622 = W31 19,068 + W34 554**, as reported. The earlier 27,148 potential matches rely on as-yet-unfrozen alternative width witnesses and are no longer used as executable matches.
2. **Selection:** actual 124 chosen candidates equal **the first 124 W31 source scene SHAs in ascending deterministic order**, yielding **17** different pilot-relative source run groups, **106 accept / 18 wait**. The 26 W34 scenes and the last 21 W31 scenes are **not in the Stage-A 124-run GPU screen**. Exact interpretation: Stage-A results from this slice would characterize a deterministically selected **W31-biased, cell-imbalanced** discovery sample only—not overall W31/W34 or previously unseen run groups. The previous prose claiming a `seeded order` needs aligning to actual lexical SHA ordering; no random-seed draw is visible.
3. **Manifest primary integrity:** **372 primary** records = 124 exact triples of old→new→SA; every record `token_ids_sha256`, `state_token_len`, `frozen_width`, `source_group`, `cell` matches its source roster field; every complete triple is wholly inside a single batch. The manifest `forward_index` strictly increases 1…378 with no gaps; no scene is repeated as primary.
4. **Replay reference integrity:** six replay rows (127,128,255,256,377,378) resolve within their own batches to old primary rows (1,1,129,129,257,257 respectively); reference type `primary-old`, scene and run all match. Replay records omit token SHA/length but have a resolvable `replay_of_forward_index` and can inherit the exact frozen input **if and only if the actual runner explicitly materializes that referenced input and asserts token SHA equality**. Each batch uses two identical old-source replays, a limited determinism check, not diversity across arms.
5. **Correct physical counts:** run1 **126 primary+2 replay=128**; run2 **126+2=128**; run3 **120+2=122**. Total **372+6=378**, no batch >128. The 3rd batch is **122**, **not 128**. This is a fixed total **across three runs**, and independent `<=128` cap cannot be used to imply one permitted 378-call run.

## Conditions still required before GPU; NOT a review failure of this *draft*

- **Executable GPU runner absent:** `stage_a_admission_draft.json` contains only runner-must-enforce requirements, not implemented and tested GPU execution code. The next actual pre-GPU reviewer must inspect its pinned Git blob and compare its **emitted/physical-forward trace 1:1** against all 378 manifest conditions, batch-by-batch. Enforce known source Git blob, corpus hash, actual base tokenizer, dynamic C row, frozen token SHA, GPU backbone/PEFT identity, per-forward 4-head raw logit write-before-post-gates, physical-prehook counter and fail-closed receipt. A `PASS_ADMISSION_DRAFT` must **never** set `blind_review_verdict=PASS` for a future runner whose blob is unknown.
- **Replay contract:** the runner must resolve replay references to the identical `old` request and compare all four question-head logits **bitwise**, while logging all six physical calls even if an early failure occurs. Reference-only replay rows are acceptable for planning, but must not silently inherit a different rendered arm.
- **Donor qualification and selection:** strict `old C=false, new C=true, SA C=false` on **frozen W31 witness**; report rates by (W, accept/wait cell, group), avoid treating 124 scenes as IID trials or calling them independent *new historical* groups. **>=2 candidate donors** should be **in distinct source-run groups** for a stronger replication claim; two positives from the same run group are not two independent source groups. Any 0/1 positive, lack of distinct source groups, or no W-matched qualifying hosts must trigger a clearly labeled HOLD, not a silent protocol relaxation or posthoc witness swap.
- **W34 and cross-width limits:** W34 donors are **not** tested in the current plan; Stage-B cannot use a W34 donor from this Stage-A unless a separate W34 strict screening run occurs. Also, donor and host must be W31-equal *as frozen*, with independently verified native span alignment and source group disjointness.
- **Fresh explicit budget approval:** approval request must state **378 native physical forwards in 3 distinct <=128 runs** (128, 128, 122), exact manifest/runner blob identity, deterministic replay budget, contingencies for abort/retry. This draft is **0 model loads/0 GPU** and does not itself grant user authorization. Stage-B requires a separate protocol, budget, review and approval.

## Final decision

**`PASS_ADMISSION_DRAFT_DATA_AND_MANIFEST`** because Option A fixes the earlier width/roster ambiguity, and all 378 rows and three batch counts reconcile with source evidence.

**`NOT_ADMITTED_GPU`** because there is **no independently audited executable GPU runner**, no final runner-bound review/receipt, and no new explicit user authorization. The shortest next task is to implement/freeze the Stage-A screening GPU runner to the precise manifest plus one CPU dry-run/plan check, submit for targeted independent code/execution-gate review, then request fresh 378-call authorization. No G5 rerun or Stage-B patching follows from this PASS alone.
