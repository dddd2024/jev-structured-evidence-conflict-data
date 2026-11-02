# A461 manuscript v5.1 — independent targeted review against v5 REVISE_REQUIRED

**Review date:** 2026-10-25. **Verdict:** `REVISE_REQUIRED_ONE_NEW_P0`. This is a narrow post-revision scientific-evidence review; **not** a GPU experiment re-audit or full journal peer review. Prior v5 review: `research/analysis/2026-10-25_A461_MANUSCRIPT_V5_INDEPENDENT_SCIENTIFIC_AUDIT_V1_REVISE_REQUIRED.md` (commit `2649a4b4`).

## Exact frozen artifacts

- New v5.1 `research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/manuscript_draft_v5_1.docx` Git blob **`f6385b11116ef558d9ee2e8b0bbcd57f8ed0bac5`**, commit `f492c1107e36fd7a8c7dab246abf035b5677808b`.
- Actual updated generator `generate_v5.js` Git blob **`8b333c35901e7b151bea1f87d654605274043ce2`**, changes log blob `2f94480e4fedd940c247eab59a45f8d4d60a987b`.
- G3 independent source census `research/rounds/A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE/G0C_REAL_20261025/census.json`; corrected G5 donor search `G1S_V2_REAL/raw_native_logits_112_requests.jsonl` and posthoc erratum; G5 independent raw-logit audit commit `657ca25c`.

**Method:** independently read exact GitHub file/blob metadata, updated complete JS authoring source, its original v5 predecessor and source-level claims, G3 cohort census, corrected G5 V2 roster. No model calls. The submitter reports Word COM 11-page render QA; this reviewer did not independently re-render the exact DOCX and therefore does **not** independently sign visual QA or bibliographic metadata.

## Confirmed closed issues from prior P0/P1/P2

1. `generate_v5.js` no longer includes `key-side span encoding itself` or the causal `key-side span encoding is causally load-bearing` claim; §4.4/Limitations use `appended-evidence-span hidden-state representation` and explicitly admit that backbone state patch **does not** establish independent K-only mediation. **P0-1 CLOSED for targeted claim gate.**
2. §4.3 corrected G5 V2 donor-resolution 36-pair distribution to **1 qualified / 2 partial old-baseline false alarm / 33 failed**. Old V1 “four partial” phrase absent. **P0-2 historical V2 count CLOSED**, subject to the **new denominator blocker below**.
3. Abstract/§4.4 replace `back to rejection` with typed `conflicting_vote true→false` and disclose independent `certificate_action` row unchanged. **P0-3 CLOSED.**
4. Pre-GPU review sequence now distinguishes gzip-loader **REJECT** → narrow-delta **PASS** → first real GPU attempt failed closed (1 physical forward) → subsequent **PASS_CODE**. §7 newly distinguishes G1 receipt **FAIL despite 103 persisted usable rows**, G3 **109/109 COMPLETE**, G4 **56/56 receipt FAIL due post-forward cleanup**, G5 donor search **112/112**, G5 patch **28/28 COMPLETE**, and one prior fail-closed forward without persisted readout: **408 archived outputs / 409 physical forwards** by the five identified stage ledgers. Claim downgraded to avoid absolute exclusion of all alternative mechanisms; [16] cites G5 pilot original evidence. Those revisions close prior P1 accounting/wording objections at the source level.
5. Header and subtitle are v5.1, Table 2 widths **[28,7,14,13,12,12,14]** total 100%. G5 result values and 0/4 restoration flips remain unchanged. Rendering is **author-reported**, not independently verified.

## NEW P0: corrected v5.1 denominator ‘2 of 62’ mixes a distinct contrast cohort

`generate_v5.js` **line 114**, §4.3, currently writes: `replicating the rarity of recognition across an independent construction round (2 of 62 constructed scenes recognized in total)`. The revision treated **G3 26 + G5 36 = 62** as if all 62 tested **new appended conflict recognition**.

But **G3 contains only 20 constructed T2 appended-conflict pairs**, plus **6 T3 pre-existing-conflict contrast pairs**. This is directly established by `G0C_REAL_20261025/census.json`:
```
selected: { T2_accept: 10, T2_wait: 10, T3: 6 }
```
Those **six T3 cases are NOT appended-conflict recognition failures or opportunities**, and cannot be put in the same denominator as newly appended-conflict recognition. Correct descriptive construction denominator:
```
G3 T2 appended-conflict pairs = 10 + 10 = 20
G5 V2 corrected T2 pairs   = 36
TOTAL comparable constructed pairs = 56
newly recognized cases = 1 G3 + 1 G5 = 2
descriptive construction count = 2 / 56 (not 2 / 62)
```
This is **not** a strict matched eligible-donor fraction, since eligibility/controls vary between rounds; when citing strict eligibility use the pre-registered, per-stage eligible denominators and don't pool incompatible cases.

The original v5 phrase `2 of 56` for T2 construction counts was correctly framed; v5.1's `2 of 62` is a **regression introduced by the correction**. The issue is also carried into G2's observed donor qualification estimate (`G3_confirmation pairs=26` in G2 CPU runner), so coordinate the fix with G2 reviewers. **Do not merely replace 62 by 56 without qualifying “constructed T2 pairs (descriptive across two rounds)”**. Preferred:
> Across the 20 G3 T2 appended-conflict pairs and 36 corrected G5 V2 T2 pairs, we observed two genuine recognition cases in 56 constructed T2 pairs (descriptive; the clean-baseline/strict-control eligible denominators differ and are not pooled).

**Exit requirement:** update the actual generator AND regenerated v5.2 or v5.1-corr DOCX, commit both blobs; recompute text probe on the rendered docx; re-review just this statement. The rest of the P0 corrections stand.

## Further scoped caution (nonblocking after the one P0 is fixed)

- G5 restoration margin improves without classification recovery; G5 suppression lacks donor-side matched controls; “load-bearing” must remain **exploratory signed-effect of backbone span states**, not semantic conflict-specific or K-only mediation.
- Exact Word 11-page render QA and all 16 bibliographic metadata still require an independent external submission QA; author self-report is not independent verification. This is not a reason to reopen already corrected G5 experiment data.
- Do not use the new G2 screen rate 2/62 as a prior or as a confirmatory sample power calculation until the denominator and eligibility have been corrected.

**Final:** **V5.1 original three P0 items CLOSED**, but **one new scientifically meaningful P0 introduced by §4.3 pooled denominator**. **REVISE_REQUIRED_ONE_NEW_P0**; a small targeted manuscript edit suffices, no new GPU or full manuscript redesign.
