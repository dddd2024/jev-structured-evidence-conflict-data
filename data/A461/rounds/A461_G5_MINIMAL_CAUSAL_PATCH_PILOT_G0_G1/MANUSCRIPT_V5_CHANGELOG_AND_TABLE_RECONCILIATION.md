# Manuscript v5 changelog, writing-gate compliance, and table reconciliation

**Date**: 2026-10-25. **Scope**: A461_G5_audit_paper_draft_v5.docx and its generator generate_v5.js, built on v4 (generate_v4.js) in F:/jev/paper_a461_psmi/, archived to this directory. **Basis**: v4 manuscript + the executed minimal causal patching pilot (research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/) + the writing-gate review (issue comment 6399512807) + the independent post-run raw-logits audit (657ca25c).

## 1. Structural diff v4 -> v5

- Subtitle and header note: v4 -> v5; evidence-chain line now "349 archived native FP32 logit rows across four GPU stages" and "three independent pre-GPU code reviews".
- Abstract: tail rewritten - the frozen-protocol sentence becomes the executed-pilot sentence (28 forwards, three review rounds, restoration +1.8/+1.9 beyond both controls, suppression flips true->false, last-layer structural null); interpretation now "appended-evidence span representation is causally load-bearing at mid-depth (consistent with the key-side readout localization)" with the single-donor/two-host exploratory ceiling.
- Section 3.3: the "patching 95+88 frozen, execution gated on blind review" tail is replaced by the governance-decision supersession: minimal pilot (2 hosts x 2 layers x 2 directions, 28 auto-derived forwards), the CPU closed-loop gates, three independent reviews, the fail-closed first attempt, and the completed 28/28 rerun.
- Section 4.3: last sentence now points to the executed pilot (Section 4.4); the 10x6 design is stated as future work.
- NEW Section 4.4 (results) with Table 2 and two paragraphs: intervention geometry, fail-closed execution, bitwise determinism/identity, results table, three observations, ceilings.
- Discussion paragraph 1: adds one sentence connecting localization to function (sufficiency beyond controls; replaceability without donor-side control).
- Discussion "Boundaries": replaced - no longer "patching pending"; now states exactly what the pilot licenses and what it does not.
- Limitations: "pending patching stage" replaced by pilot-scale limits (1 donor / 2 hosts / 2 layers; open question moved to the encoding-computation failure upstream of layer 11).
- Section 7: evidence chain extended with the pilot stage (plan + raw logits + three reviews + authorization reconciliation + analysis artifacts).
- References: IDENTICAL to v4 (15/15; verified by diff of the generator ref() lines).

## 2. Writing-gate compliance (issue comment 6399512807)

1. **28/28 + 1 fail-closed (cumulative 29); bitwise baselines/identity** - stated in Section 4.4 ("28 of 28 planned forwards completed with three fresh baselines and both identity patches bitwise-identical") and Section 7 (cumulative-29 reconciliation disclosed). PASS.
2. **Restoration is margin improvement, not classification correction** - the note reports post-patch margins (-7.78 / -7.45), "0 of 4 restoration sites flips the argmax", "partial margin improvement, not a classification correction"; the phrases "successful restoration" / "corrected recognition" are absent from the generated text (verified). PASS.
3. **Suppression flips are real but have no donor-side matched controls** - Section 4.4: "the pilot budget contains no donor-side sham, permutation, or norm-matched control, so this is a signed-change and flip observation, not a demonstration that the suppressed information is semantic-specific conflict evidence"; Discussion: "exploratory; no donor-side matched control within budget". PASS.
4. **Layer 23 exact null** - caption and text: "an exact null that matches the structural prediction of the row geometry ... and is not evidence about what the layer encodes". PASS.
5. **Off-target zeros are architectural** - Section 4.4: "bit-identical on every patched forward because the architecture runs the four question rows independently - a built-in integrity check, not evidence that action utility is causally preserved". PASS.
6. **Backbone layer-output patch, not Pointer-Head K; no Key-only mediation claim** - the section title and all causal statements say "appended-evidence span representation"; the final paragraph states explicitly that the pilot "does not establish that the causal path is exclusive to the key side of the readout". The phrase "key encoding is causally load-bearing" is absent from the generated text (verified). PASS.
7. **2/4 cells are not four independent samples** - the note states the two host sites share one donor and one construction round, that no statistical significance / cross-group stability / model-generality claim is made, and adds "hypothesis-generating" to the standing labels. PASS.
8. **v4 chain preserved; new section marked post-GPU** - Section 4.4 opens with "This section reports post-GPU evidence acquired after the behavioral and readout rounds above were frozen; it does not retroactively upgrade them." All v4 sections, errata, and the reference list are unchanged. PASS.

## 3. Table 2 cell-by-cell reconciliation (13 numeric cells vs the independent audit 657ca25c)

| Cell | Exact (audit) | v5 table | Status |
|---|---:|---:|---|
| Restoration run114 L11 delta | +1.801410 | +1.80 | OK |
| Restoration run114 L11 SA-sham | +1.440941 | +1.44 | OK |
| Restoration run114 L11 permuted | +0.982751 | +0.98 | OK |
| Restoration run182 L11 delta | +1.938604 | +1.94 | OK |
| Restoration run182 L11 SA-sham | +1.044948 | +1.04 (fixed from +1.05 during reconciliation) | OK |
| Restoration run182 L11 permuted | +0.982465 | +0.98 | OK |
| Suppression run114 L11 | -4.640155 | -4.64 | OK |
| Suppression run182 L11 | -2.751554 | -2.75 | OK |
| Host SA baseline run114 | -9.577639 | -9.58 | OK |
| Host SA baseline run182 | -9.390018 | -9.39 | OK |
| Donor NEW baseline | +1.446688 | +1.45 | OK |
| Post-restore run114 | -7.776229 | -7.78 | OK |
| Post-restore run182 | -7.451414 | -7.45 | OK |

Layer 23 rows are exact zeros in the analysis JSON and the table says 0.000 for every condition. All 13 cells verified programmatically against the analysis results and the independent audit values; every value appears in the generated docx.

## 4. File mapping

- research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/manuscript_draft_v5.docx - the generated manuscript (this file's Git blob is the citable version).
- research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/generate_v5.js - the exact generator (docx built with the docx 9.x library; run `node generate_v5.js` in the paper workspace).
- Frozen evidence blobs referenced by the text: raw logits 790a71a5, analysis bae4cc16, GPU runner d05b070e, execution receipt 2ab28abd.
- Status: v5 complete at the pilot's evidence level; awaiting independent academic review. No claim beyond single-donor/two-host/two-layer DEV exploratory causal signal (hypothesis-generating).

## 5. v5.1 revision (independent scientific audit 2649a4b4 / comment 6399512807)

**P0 fixes (all applied and programmatically verified in the generated docx):**
1. All remaining "key-side span encoding" causal wordings replaced by "appended-evidence-span hidden-state representation" (Section 4.4 observations, Limitations, Boundaries, Abstract transplant sentence now "recognized-evidence span representation (backbone layer-11 hidden states)"); the 5 remaining "key-side" occurrences are exclusively G4 readout-decomposition contexts (25/26 dominance, term names, the one +9.02 case) plus the compatibility-hypothesis framing "(consistent with the key-side readout localization)".
2. Section 4.3 corrected V2 counts: "1 qualified / 2 partial / 33 failed"; "2 of 62 constructed scenes recognized in total" (was "four partial ... 2 of 56").
3. Typed-readout language: abstract and Section 4.4 now say "flips the donor's conflicting_vote readout from true to false; the certificate-action head, on its independent row, is unchanged" - "back to rejection" removed.

**P1 fixes:**
- Section 3.3 review history corrected: rejection (gzip) -> narrow-delta PASS -> fail-closed first GPU attempt (1 forward, condition-name deviation) -> PASS_CODE; no longer "the first two rejections".
- Section 7 now carries the complete physical ledger: G1 pilot 103/103 (receipt FAIL from a disclosed post-loop replay bookkeeping bug; rows usable), G3 109/109 COMPLETE, G4 56/56 (receipt FAIL from a hook-cleanup NameError after all forwards; rows usable), G5 search 112/112 (108 primary + 4 replays), G5 pilot 28/28 COMPLETE, plus 1 fail-closed forward with no archived row: **409 physical forwards, 408 archived rows**. Cover line updated to "408 archived native FP32 logit rows across the five GPU stages of this line"; intro "five preregistered GPU stages".
- Section 4.2 and Discussion downgrades: "rules out a query-aggregation account" -> "argues against - at this readout level - a query-aggregation account ... upstream encoding-side alternatives are not excluded by the decomposition alone"; "not a decision-threshold artifact, not a query-aggregation artifact, and not a format artifact" -> bounded readout-level observations.
- Reference [16] added: pilot round dir (protocol, CPU gates, raw logits, three reviews, admission reconciliation, analysis), G2 feasibility round dir, and the post-run independent audit path.

**P2 fixes:**
- Generator header comment and page header now v5.1; subtitle "Anonymous draft (v5.1; ...)".
- Table 2 column widths 104% -> 100% ([28,7,14,13,12,12,14]).
- Rendered QA: DOCX exported to PDF via Word (11 pages), all pages inspected - header, tables (Table 1, Table 2 with corrected +1.04), ledger paragraph, and references render cleanly; no truncation, no overflow.

**v4 -> v5 -> v5.1 diff verification (programmatic, on generated docx text):** every new-in-v5.1 marker present; every superseded v4 phrase absent; v4 char count 26071 -> v5.1 29463.

**Deliverables:** manuscript_draft_v5_1.docx + generate_v5.js (exact generator) + this changelog. Status: awaiting P0-focused re-review; no claim beyond the pilot's exploratory ceilings.
