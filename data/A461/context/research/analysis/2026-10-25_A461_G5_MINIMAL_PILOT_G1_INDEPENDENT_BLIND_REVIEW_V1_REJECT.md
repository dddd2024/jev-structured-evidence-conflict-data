# A461-G5 最小双向 patching pilot G1：独立盲审裁决 V1

**裁决：REJECT / HOLD_GPU_P0_GZIP_SOURCE_LOADER**。审查时间：2026-10-25。审查对象：GitHub Issue #2 盲审请求评论 `6398454990`；提交 `f9f2774a9a6b6aeac6f8b638412c77fa69aefa51`；按冻结 Git blob 定界：

| Artifact | Frozen Git blob |
|---|---|
| G1 GPU runner `research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/A461_g5_pilot_gpu_v1.py` | `d2efc395f8c7279695e893930105bcc2f75ce72e` |
| G0 CPU runner `.../A461_g5_pilot_cpu_closed_loop_v1.py` | `a8b507c1d0f5890575f882930bfd5a145f5e1b29` |
| Frozen protocol `.../A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_PROTOCOL_V1.json` | `111595a31f3fb18268142501602cf6d91df848dd` |
| G1 admission `.../admission_receipt_pilot_gpu.json` | `6fdd7d0a520c4c5838fc05d1f322b179302ba89d` |

**This is a pre-GPU static/source-contract and independent Python standard-library probe, NOT a completed GPU execution or proof of model mechanism.** No new model forward in this review.

## P0-A (deterministic runtime blocker): compressed DEV corpus opened as plain text

GPU runner lines **26–27** define `CORPUS=.../records/development.jsonl.gz` (a gzip file). At line **124** it uses:

```python
with CORPUS.open("rt", encoding="utf8") as f:
    for line in f:
        ...
```

`Path.open("rt")` performs plain text UTF-8 decoding, **not gzip decompression**. Normal gzip streams begin with bytes `1f 8b`, so the first `f` iteration will fail with `UnicodeDecodeError` (or non-JSON data if exotic encoding), before the runner reaches `import torch` (line **148**) or the backbone load (line **195+**). This is not a model negative result. The paired, successfully archived G0 CPU runner correctly uses `import gzip` (line **31**) and `with gzip.open(CORPUS, "rt", encoding="utf8")` (line **234**), confirming the expected file format.

Independent isolated Python probe (synthetic gzip fixture, **not claiming the server corpus bytes were downloaded**) returned: gzip magic `1f8b`, plain text `Path.open("rt")` raises `UnicodeDecodeError: invalid start byte 0x8b`, `gzip.open("rt")` parses the exact JSON fixture. This corroborates the deterministic API behavior and matches the same extension/expected access mode in the frozen project code.

**Minimal code fix**: add `import gzip` and change the GPU runner to `with gzip.open(CORPUS, "rt", encoding="utf8") as f:`. Then run **the GPU runner's exact CPU preflight path** (or factor it into a shared source-validation function) on the actual pinned server corpus, confirming split, source count and canonical state hashes against the G0 archived results. Freeze and post the **new exact runner git blob** for a narrowly scoped independent delta re-review. Do not edit/relabel `d2efc395` in place; preserve the rejected blob for provenance.

## Positive findings / what does NOT need to be redesigned

- The G0 artifacts include a `COMPLETE_A461_G5_PILOT_CPU_CLOSED_LOOP` receipt, 12/12 internal CPU gates, 108/108 tokenizer parity, source roster donor run83 and two failed hosts run114/run182, 34-token spans with suffix-preserving coordinates, mock C-row targeting/identity checks, and a deterministic 28-forward *planned* execution ledger. These are **archived internal gates**; no independent re-execution of the actual SecJev tokenizer or model was performed in this blind review.
- Compared with V3/V4, the new G1 GPU source now captures `caps[(tag,L)]` from the dynamic `conflicting_vote` row `c_idx` (line **223**) and patches the same `c_idx` row (lines **224–232**), addressing the earlier action-row-to-conflict-row mismatch. Capture tags are distinct and layer hooks are registered for [11,23].
- The code's frozen execution plan explicitly enumerates 28 physical `model.forward` calls (3 donor captures, 2 host unpatched, 2 host captures, 2 identity patches, 4 restoration, 4 SA-sham, 4 permutation, 2 host treatment captures, 1 donor baseline, 4 suppression = **28**); the CPU plan and receipt agree arithmetically. This is **not** proof of actual 28 GPU calls before execution.
- GPU admission is presently `blind_review_verdict=null`, `explicit_user_gpu_approval=false`. The self-blob gate checks the exact runner blob and reviews approval before importing the model. Thus the current gate correctly stops unapproved runs.

## Nonblocking caveats for the later scientific interpretation

1. The `donor_old` capture uses the *new-arm* appended span `[624,658)` on old-arm state length **652**; its last six captured positions are outside the old state (into the branch) in that independent question row. The current pilot does **not** use these states in any restoration/suppression, so this does not invalidate the other contrasts, but the corresponding label must not be interpreted as a clean 34-token old-state evidence baseline. Either mark this diagnostic as `MIXED_STATE_BRANCH_UNUSED` or omit it and recalculate budget if publishing.
2. The intervention directly patches only the **C / conflicting_vote** causal row; other question rows are computed independently, so “off-target action unchanged” is structurally expected and **not** evidence that security-action utility was causally preserved. An action-row intervention would require a distinct experiment/ledger. The study protocol already caps claims as *single-donor two-host DEV exploratory*.
3. The necessity/suppression direction does not yet have a matched donor-side SA/random control, and the two-host sample cannot establish general, source-independent mechanism. If pilot succeeds, require more controls and new groups before promoting to a paper's main causal claim.
4. `run_forward()` increments `receipt.native_model_forward_calls` after `model.forward` returns (line **263**), whereas `physical` prehook increments at actual invocation (line **205**). If a model call raises in-flight, the failure receipt may undercount physical calls; include `physical` in FAIL receipt or count prehook events in both. This is a provenance repair, not an excuse to withhold the CPU source loader fix.

## Execution gate and verdict

**REJECT the reviewed G1 blob `d2efc395` as currently submitted; DO NOT write blind-review PASS to its admission receipt; DO NOT start GPU.**

The specific blocker is simple and local. **Next review should be a targeted delta audit** of the one-line `gzip.open` repair plus an actual pinned-corpus CPU preflight PASS, along with unchanged frozen protocol and full plan. A full new Vn research design or another literature screening round is **not required**. A new PASS, if issued, must bind the corrected runner's new Git blob, and GPU execution additionally requires fresh explicit user approval and budget 28. The work has advanced materially relative to V4, but there are still **zero verified patching model forwards**.

Links: [blind review request](https://github.com/dddd2024/jev/issues/2#issuecomment-6398454990); [pilot tree](https://github.com/dddd2024/jev/tree/main/research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1).
