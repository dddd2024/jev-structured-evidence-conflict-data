# A461 G3 post-execution: independent native-data + control contract audit (V1)

Date 2026-10-25. Repo `dddd2024/jev`. **Read-only independent secondary evaluation; no new model forward, server access, TEST/CAL, or alteration of original G3 artifacts.** Machine-readable numbers, blob SHAs and explicit decision: [companion JSON](2026-10-25_A461_G3_post_execution_independent_evidence_contract_audit_v1.json).

## 1. Execution existence: reconcile prior static expectation with new actual archive

At repository main HEAD the G3 result archive is real: G0C 79 edited arms/26 pairs, independent-verifier PASS, G1C original `raw_native_logits_109_requests.jsonl` 109 native FP32 row records, 4 replay identical, G2C actual output. The old claim that the proposed G1C run necessarily stopped before inference **must be superseded by verified archived execution**; it does not resolve the separate mismatch between checked-in source, frozen budget and output composition.

## 2. Recomputed primary endpoints (independent of G2 aggregate counters)

| Arm | n | new conflicting_vote=true | old conflicting_vote=false | new action correct | E=2 correct after numeric parsing |
|---|---:|---:|---:|---:|---:|
| T2 wait→reject | 10 | 0 | 10 | 0 | 0 |
| T2 accept→reject | 10 | 4 | 7 | 3 | 1 |
| T2 total | 20 | 4 | 17 | 3 | 1 |
| T3 pre-existing conflict | 6 | 6 | 0 | 4 | 4 |

All 20 T2 treatments have source Gold `conflicting_vote=true`. But of the 4 true predictions in new T2 arms, 3 were **already true on old, no-conflict** arms (run-211, run-212, run-328). Thus **genuine clean-old false→new true recognition is 1/17 eligible clean-old cases**, or 1/20 across all T2 pairs, not 4/20 newly recognized. The only such run is run-338. Of the 3 action-correct T2 arms, run-211 and run-328 already had an old-arm C false alarm; run-338 is the actual new C recognition. This sharpens the paper thesis to a *clean-to-conflicted response deficit* plus separate false-alarm behavior, not all-or-none C-head failure.

T3 6/6 C=true, but T3 started C=true in the source and is not a matched clean→conflict test; 2/6 T3 actions choose `accept` despite correct C=true. Across six T3 groups only 2 overlap the twenty T2 groups; pooled Fisher (1/20 vs 6/6, nominal p≈3.04e−5) uses potentially dependent units and different baseline states. Dropping overlapping T3 groups yields 1/20 vs 4/4, one-sided exact p≈4.71e−4 **as a descriptive category contrast only**; neither result identifies an internal mechanism or licenses a clean causal effect of “appended” versus “pre-existing”.

## 3. Strongest control-contract defect: core accept→reject N1B

A source-Gold-invariant single-field neutral must be a valid fresh validator and treatment-token-count matched. Direct reads of all 79 G0C arms and token audit find:
- T2 wait: 10/10 N1B author-valid **and** token-length matched;
- T2 accept: **3/10** valid and matched; other 7 use `z_neutral_outside_set` outside `validator_set` **and** token lengths differ from treatment;
- across all 26 pairs, N1B token matched 19/26, not 26/26.

This directly contradicts the G3 memo's “each pair token-matched N1B” claim. No claim that nuisance variables are fully controlled in the quorum-satisfied cell is admissible from these data.

Among 13 T2 with legitimate and matched N1B, 12 had old C=false. Of those 12, **11 also had correctly predicted neutral C=false**, and **none of those 11 yielded new C=true**. The sole true clean→conflict hit **run-338** also had a **neutral false-positive C=true** despite neutral Gold=false and valid/token-matched author swap (T2–neutral C logit margin difference +7.2185). This case is not “pure semantic recognition” without qualification; its null control itself triggers spurious conflict. Exploratory specificity `D_C = M_C(treat)-M_C(neutral)` is positive in 7/13 valid T2 triples (wait 5/10; accept 2/3). Direction, not only argmax, fails to isolate semantics robustly.

## 4. SHAM input validity and duplicate-control check

- All 6 SHAM_TS arms and all 6 SHAM_RO arms have at least one violation of `received_messages` nondecreasing `received` order; the original source selection code expressly requires old states to be sorted this way. SHAM_TS appends a lower receive timestamp to the tail; SHAM_RO reverses. Their results may be discussed as deliberately out-of-distribution format stress, not valid source-contract-preserving controls.
- All 9 SHAM_SA arms come from T2 wait cells; zero from T2 accept. Format controls therefore cannot justify a strong claim for the accept cell.
- Six G3 N1 rows have **exactly the same state-token SHA as corresponding N1B rows**; they are not six independent nuisance variants.
- High agreement of an invalid-neutral model prediction with the treatment prediction is **not** evidence that semantics, rather than format, drove the outcome. With different oracle Golds, identical wrong predictions can instead indicate missing semantic discrimination.

## 5. G2C code-level metric error: `evidence_level` coercion

In checked-in `A461_g3_g2c_analysis_v1.py`, `norm` maps candidate labels `"0"` and `"1"` into booleans and leaves `"2"` as string. Against oracle integer 2, every predicted `"2"` is declared wrong. Original G1 logits contain evidence_level candidate strings `"0","1","2"`. Correct numeric casting restores correct-E counts: **T2 wait 0/10, T2 accept 1/10, T3 4/6**, whereas G2 per-pair `new_correct.evidence_level` misleadingly returns zero across all 26. `"0"` and `"1"` compare equal to False/True in Python incidentally but are still semantically mistyped. This is a reproducible calculation bug, not an inference failure of the model.

The G2 `persist_at_old_decision_on_t2=16/20` metric is also mislabeled: the implementation counts NEW predictions equal to OLD GOLD. It measures **persistence/under-response**, not correctness of a persist-old decision baseline on the new Gold. Since all twenty T2 source Gold actions change to reject_conflict, persisting the old Gold decision would score **0/20 against the new Gold**. Likewise, `majority_class_old_gold_on_t2=10/20` describes the old-Gold distribution, not an independently evaluated new-Gold classifier accuracy.

## 6. G0C reproducibility/forward-budget discrepancy (must not conceal actual execution)

Frozen G3 protocol V1 has `forward_stage_budget=106`, hard cap 128. **Current checked-in G0C constructor** explicitly has `SHAM_CAP=6` and a single SHAM loop stopping when `sham_used>=6`, hence can emit **at most six** SHAM_SA, six SHAM_TS, six SHAM_RO, total **at most 106** planned native forward calls with 26 pairs and 4 replays. **Actually archived G0C** emits **nine** SHAM_SA (and six each TS/RO), 79 arms, planned 109, followed by true G1C 109/109. Therefore archived G0C artifacts cannot be reproduced from the exact checked-in G0C constructor without some additional modification/runner; the original effective generator source and relevant code hash must be located and documented. Successful replay of 109 logits is *not* equivalent to code provenance or frozen 106-stage-budget compliance. Keep the original receipt and count fully intact; issue prospective protocol/code reconciliation and a formal erratum, not retroactive alteration.

## 7. Literature positioning and verdict

G−1 has already included the SecJev source paper and Tang et al., *Do Language Models Track Entities Across State Changes?* (ICML 2026). Tang et al. identify non-incremental state aggregation and actual internal circuits; behavioral new-conflict recognition failure alone does not duplicate their precise setup, but also does **not** establish a mechanistic novelty beyond that literature. Further bidirectional hidden-state/attention/pointer/LoRA interventions, with both positive and sham causal controls, are needed before a white-box mechanism claim.

**Updated formal decision:** `G3_REAL_BEHAVIORAL_EVIDENCE_VALID; G3_FULL_MATCHED_AND_FORMAT_EXCLUSION_CLAIMS_NOT_ESTABLISHED; G3_EVIDENCE_LEVEL_AGGREGATES_NEED_ERRATUM; G3_CODE_PROVENANCE_AND_BUDGET_NOT_RECONCILED`.

Next named task: `A461_G3_POSTHOC_SOURCE_AND_METRIC_ERRATUM` (existing G3 repair/independent readback, **not new GPU experiment**). Reconstruct actual executed G0C generator, assert chronological and validator legality, recompute numeric E and baseline labels, publish strata-qualified C/A/N1B results, and document whether a genuinely valid unseen-group causal phase can be admitted. Do not overwrite original G3 evidence. Server/GPT Library replication is not asserted for this report; GitHub save/readback is the deliverable of this independent session.
