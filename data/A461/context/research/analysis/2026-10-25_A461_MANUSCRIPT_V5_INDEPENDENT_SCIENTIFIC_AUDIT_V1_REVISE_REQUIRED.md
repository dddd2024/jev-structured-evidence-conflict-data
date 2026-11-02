# A461 Manuscript v5 — independent scientific/evidence audit V1

**Date:** 2026-10-25. **Verdict:** **REVISE_REQUIRED (not yet submission-ready)**. This verdict concerns claims, historical accounting, and manuscript QC, **not** the validity of the archived G5 28-forward experiment. No new GPU call. Do not overwrite v5; publish a corrected v5.1 with an explicit diff and re-review.

## Audited exact artifacts

- v5 delivered `research/rounds/A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/manuscript_draft_v5.docx`, Git blob **`5d81d46c00c117e9451330b281237998556b8fe1`**, commit **`d89ed3880982950f2d3896256e30bbbb7618c4ba`**.
- Corresponding source `generate_v5.js` blob **`0f6869c1238fad0f82e5daf864036e61310cdc52`** and self-authored changelog blob **`ef97929fc184f36ad44bcbe00aae2fd19f036636`**.
- Previous v4 manuscript blob `deab434314b4142a4f8bce6cc8954edc4206ef91`. v5 generator and changelog substantiate appended Section 4.4, Table 2, abstract/discussion/limitations/evidence-chain changes and retained 15 references.
- Independent G5 audit commit `657ca25c`; frozen 28 raw native outputs blob `790a71a55b99ea3a362158f2a389f05a49626f92`; analysis `bae4cc1668dd83a58c320c9b99a1b9391fb21b93`; GPU final receipt `2ab28abd8d2fe47feeb15c335f47fc6e0140e382`.
- G5 corrected V2 donor-search 112-logit rows + `G5_POSTHOC/g5_construction_exclusion_erratum.json` and G3/G4 execution receipts reviewed. G4 decomposition data/analysis saved separately.

**Scope disclosure:** Direct GitHub readback of DOCX Git blob plus **full exact generator source** and changelog; mathematical/audit cross-reference of original experiment data and admission records. Independent visual-page rendering of binary DOCX was **not** achieved in this review environment, so layout remains an explicit outstanding QA gate. Changelog's own 8/8 and 13/13 are not substitutes for manuscript peer review.

## What passed

1. The v5 **Table 2** values in `generate_v5.js` line 118–129 are numerically consistent with the frozen G5 primary-logit audit to the displayed precision: run114 restoration Δ+1.80, SA-sham +1.44, permuted +0.98; run182 Δ+1.94, SA-sham **+1.04** (correctly rounded from +1.044948), permuted +0.98; suppression Δ−4.64/−2.75; layer23 all zero.
2. The Section 4.4 note **explicitly** states host margins remain −7.78/−7.45 and **0/4 restoration argmax flips**, labels margin improvement as partial; notes suppression has no donor-side sham/norm-matched control, and does not treat independent question-row action nonchange as preserved utility.
3. One qualified donor/two DEV host sources/two layers, no significance/cross-model generality and post-GPU status are mostly documented correctly. Related work [1] SecJev (arXiv:2610.03073v2), [2] One Word Opens the Gate (arXiv:2610.12292), and Tang et al. ICML 2026 / PMLR 306 are externally findable, though **15/15 unchanged references is not the same as 15/15 factual citation verification**.
4. G5 successful 28/28 and preceding fail-closed extra physical forward recorded (cumulative 29) in provenance.

## P0 — must correct before declaring the manuscript scientifically audited

### P0-1: Whole-backbone hidden-state transplant is incorrectly promoted to causal Key-side mechanism

`generate_v5.js` **line 132** currently says `the recognition-carrying signal lives in the key-side span encoding itself`; **line 140** says `the key-side span encoding is causally load-bearing at mid-depth`. Other nearby parts (line 132 later) correctly admit that actual hooks patch **backbone layer-output hidden states, not the Pointer Head K projection**. The correct disclaimer does not erase those preceding, mechanistically stronger assertions. Readout algebra G4 supports a **key-term accounting**; G5 supports **mid-layer appended-evidence-span state perturbation**. It **does not isolate K-vs-Q mediation, nor token feature semantics**.

**Mandatory rewrite:** Use `the appended-evidence-span hidden-state representation has a reproducible signed causal effect on the conflict-readout margin in this exploratory pilot; consistent with, but not uniquely attributable to, the candidate-key side`. Change Section 6's `key-side span encoding` to `backbone appended-evidence-span representation`. Abstract/Discussion's key-side mechanism claims must be consistently qualified. No phrase suggesting exclusive Key mediation.

### P0-2: v5 cites superseded G5-V1 donor counts

`generate_v5.js` **line 114**, Section 4.3: `one scene, with four partial cases carried by old-arm false alarms`. The **corrected archived G5 V2** source (`G1S_V2_REAL/raw_native_logits_112_requests.jsonl`, rejoined to `G0D_CONS_V2/pair_rows.jsonl`) independently gives **1 qualified donor / 2 partial old-arm false alarms / 33 failed = 36**. `G5_POSTHOC/g5_construction_exclusion_erratum.json` explicitly records V1 superseded **4 partial**, and V2 **2 partial**.

**Mandatory rewrite:** `one qualified donor, two partial cases attributable to old-arm false alarms, and 33 failed cases in the corrected V2 36-pair search`. Preserve the erratum's provenance, not the superseded count.

### P0-3: Reversed meaning of typed conflict-head output under suppression

`generate_v5.js` **line 132** states `flips the donor scene back to rejection`; Abstract **line 78** has `flips its recognized read back to rejection`. The affected variable is **`conflicting_vote`** with `true/false` choices, **not** `certificate_action` with `accept/reject_conflict/wait`. The archived G5 data show donor C-margin +1.446688 goes to −3.193467/−1.304866 on layer11; that means **conflict-readout true→false**. The separate action row is architecturally independent, remains unchanged across C-only patch and was **already rejecting** in the donor.

**Mandatory rewrite:** `suppresses the donor's conflict recognition, flipping the typed conflicting_vote read from true to false; the certificate_action head is not intervened upon and does not flip`. Don't write `rejection` as shorthand for `C=false`.

## P1 — historical/provenance, interpretability and academic rigor

### P1-1: Review timeline is internally false

`generate_v5.js` **line 93** says the `first two rejections` involved gzip loader and condition-name drift. The actual sequence is (1) **REJECT** on old gzip loader blob d2efc395, (2) **PASS narrow delta** on c5dd9e0c, (3) **PASS_CODE/HOLD_AUTH reconciliation** on d05b070e after a **fail-closed execution attempt** consumed one forward. The condition-name bug was a runtime FAIL, **not** a second independent review REJECT. Correct audit chronology; avoid counting a runtime stop as an independent reviewer rejection.

### P1-2: Native-forward stage arithmetic and terminal status are not reconciled

`generate_v5.js` **line 143** asserts `103 + 112 + 56 native forwards across three stages`; the frozen **G3 `G1C_REAL_20261025/execution_receipt.json` explicitly reports 109 native/physical forwards**, not 103 (plan composition 105 rows + 4 replay). G4 `G1R_REAL_20261025/execution_receipt.json` reports **56 forwards but terminal `FAIL_A461_G4_G1R`**, with **NameError: `hook` undefined** during cleanup; readout-analysis/raw-logit files do exist and separately support G4's 224 branch readout reconstructions. Correct language: usable archived G4 analysis plus terminal post-forward cleanup FAIL; cannot say its execution receipt is COMPLETE. G5 corrected search reports 112, and G5 minimal pilot 28 (+1 fail-closed). Four directly identified G3/G4/G5-search/G5-pilot receipts total **109 + 56 + 112 + 28 = 305 forwards** (306 including extra G5 failed attempt). The cover-line `349 archived native FP32 logit rows across four GPU stages` (**line 75**) **does not reconcile to these four stage counts**. If 349 intentionally includes other earlier stages or superseded artifacts, enumerate each exact stage, log path, unique-vs-replay-vs-attempt policy and rows; otherwise correct. Do **not** conflate unique archived rows and physical forward spend, or silently double-count superseded reruns.

### P1-3: Correlative readout decomposition overclaims exclusion of alternative mechanisms

`generate_v5.js` **line 112** says small query-term accounting `rules out a query-aggregation account`; Discussion **line 135** asserts failure `is not ... query-aggregation artifact ... not a format artifact`. A local bilinear q/k decomposition bounds the **observable contribution under that specific readout path**, not all upstream query formation, backbone aggregation, input positions, or format/context distribution shifts; the controls themselves have documented validity gaps. Rewrite as `the observed query-term contribution is small in this readout decomposition`; `under the checked controls and dataset, the findings are more consistent with reduced key-term response than with a large query-term contribution`. Preserve viable competing hypotheses.

### P1-4: Bibliography and new evidence trail need updating

Claim `15/15 references identical to v4` is a **source-diff fact**, not proof all 15 bibliographic metadata are verified. Reference **[15]** lists old A461 G5 donor-resolution folder but **does not list the new `A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_G0_G1/` containing the very G5 experimental claim supporting v5**. Add a stable content-addressed citation/path for G5 pilot protocol, raw logits (blob 790a71a5), independent audit (657ca25c), and execution receipt. Confirm all bibliographic records separately before external submission.

## P2 — document preparation

- `generate_v5.js` **line 167** still hardcodes **`Appended-Conflict Recognition Audit (v4, white-box chapter)`** in the **header of the generated v5**; update to v5 and keep in sync with subtitle.
- Table 2 `widths=[30,7,15,13,12,12,15]` (**line 129**) sum to **104%, not 100%**. This may cause overwide columns / wrapping / layout defects; independently render all DOCX pages and inspect table breaking, page numbers, headings, long author/title line. This audit has **not** issued a visual-render PASS.
- Long new Abstract and single-paragraph Section 4.4 assertions should be edited for paper-style clarity and not overstate the central contribution. “three independent reviews” should be supported by provenance of **review process**, not inferred from three comments written within one project.

## v5.1 concrete exit contract (no new GPU)

1. Fix P0-1/P0-2/P0-3 across Abstract, §4.3, §4.4, Discussion and Limitations; grep generated manuscript for `key-side span encoding itself`, `back to rejection`, `four partial cases`; must be absent/corrected **in DOCX, not only JS**.
2. Correct frozen pre-GPU review timeline and source-count provenance; publish machine-readable stage ledger (native forwards, persisted raw rows, primary/replay, failed attempts, terminal receipt status), and reconcile/annotate 349. Do not silently change raw logs.
3. Preserve Table 2's 13/13 correctly rounded cells and the 0/4 restoration flip limitation. Compare revised Section 4.4 to **actual** G5 28-row raw logits, G4 readout and V2 G5 source, not only the author's changelog.
4. Update new-pilot evidence reference; fix v5 header/table widths; execute the DOCX **render-to-PNG QA** and paragraph/table/reference/section structure diff vs v4.
5. Deliver v5.1 `docx` + exact updated generator + changelog + raw evidence/source table + independent reviewer re-verdict. **No GPU needed** for these manuscript fixes.

**Decision:** The experimental **G5 data remain valid exploratory evidence**. The v5 manuscript is **written and archived**, but **not independently approved for external submission**, because typed-decision semantics, superseded donor counts and strength of mechanism claims need correction. No claim that its current 8/8 self-gates equate to an independent reviewer PASS.
