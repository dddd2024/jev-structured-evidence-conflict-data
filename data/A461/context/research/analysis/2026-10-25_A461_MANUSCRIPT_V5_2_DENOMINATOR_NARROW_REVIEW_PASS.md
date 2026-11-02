# A461 manuscript v5.2 — independent narrow denominator re-review

**Date:** 2026-10-25. **Verdict:** `PASS_PRIOR_P0_DENOMINATOR_CLOSED / NO_NEW_GPU`. This is **only** the targeted re-review requested in Issue #2 comment `6400272206`, following v5.1 review `a7bcb1d49442f9b898cbaac5b45734bec53cc791`. It is not a full independent journal peer review or visual layout certification.

## Frozen identities
- Commit `ef5ed996a2aefb58f6f7a5765d9ee5a69732b045`.
- New manuscript `research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/manuscript_draft_v5_2.docx`: Git blob **`00e04844c83b5699228441bb91d2cb9bda825100`**; obtained via GitHub base64 and verified ZIP container lists Word XML and header entries.
- Full amended generator `.../generate_v5.js`: Git blob **`fcf4c845036f986eb8235cc83fce1236ea1de125`**; previous v5.1 generator blob `8b333c35901e7b151bea1f87d654605274043ce2`.
- Source audit anchors: G3 `G0C_REAL_20261025/census.json` (T2_accept=10, T2_wait=10, T3=6), corrected G5-V2 36 T2 pairs with 1 qualified donor / 2 partial / 33 failed.

## Independent diff and numeric audit

A literal line diff of the actual generator versions shows only 5 changed lines: script header comment, anonymous draft version, §4.3 paragraph, Word header version, and emitted output filename. No other result, table, evidence ledger, references, limitations or experiment method content changed.

New §4.3 states: `two recognized among the 56 constructed T2 appended-conflict cases across both rounds (20 from the confirmation round plus 36 from this one; descriptive denominator - the rounds' strict-eligibility criteria differ, and the confirmation round's 6 pre-existing-conflict controls are excluded from this count)`.

**Independent validation:** G3 census T2=10+10=20; G3 T3=6 (pre-existing contrast, exclude); G5 corrected T2=36; denominator `20+36=56`; observed recognized events `1+1=2`. The wording does not claim a single pooled strict-positive-donor rate and expressly states that two rounds' strict-eligibility rules differ. This **fully closes the sole remaining §4.3 P0 from v5.1**. Generator no longer contains `2 of 62 constructed`.

Changed document metadata and output path correctly say v5.2; existing G5 Table 2 values and provenance remain unchanged. The DOCX Git blob exists and is a valid-looking ZIP/OOXML container, but this reviewer did **not** independently rerender 11 pages or verify text extraction from the compressed Word XML—those remain author-attested QA, not independent layout certification. The source-to-binary build reproducibility was not byte-rebuilt here.

## Claim and scope gates still apply

- Positive pilot remains: layer-11 restoration improves signed C margin versus SA-sham and permutation for 2 hosts, **0/4** host restoration argmax flips; donor-side suppression flips conflict-head `true→false` in two cases, **without matched donor-side negative controls**.
- G5 patched backbone layer-output hidden states, **not** isolated Pointer-K causal mediation.
- This review does not constitute cross-source replication or approve any new GPU inference. No new model execution or posterior data manufacture.
- Bibliographic factual verification / independent 11-page visual inspection and stronger publication-level external peer review remain separate tasks.

**Final:** `PASS` for v5.2's new denominator fix and the **previously raised manuscript P0 revisions**, as a narrow scientific claim review; manuscript may proceed to broader academic review. Do not label it `SUBMISSION_READY` without comprehensive bibliography/layout/publication peer review. G2 research remains an independent scientific workstream.
