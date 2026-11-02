# A461-G3 secondary data analysis: direction vs semantic specificity, persistent action inconsistency, and exhausted Streamlet source groups

**Date:** 2026-10-25. **Status:** Independent read-only original-logit/CPU audit; **no new GPU forwards**. This report supplements, not replaces, the [manuscript v2 independent review](2026-10-25_A461_G3_manuscript_v2_independent_peer_review.md) and the [source contract audit](2026-10-25_A461_G3_post_execution_independent_evidence_contract_audit_v1.md).

**Machine-readable results:** [time_tie_margin_and_action_persistence_audit.json](2026-10-25_A461_G3_time_tie_margin_and_action_persistence_audit.json). **CPU-only candidate input rows:** [equal_received_tie_swap_CPU_candidates.jsonl](2026-10-25_A461_G3_equal_received_tie_swap_CPU_candidates.jsonl).

## 1. Input provenance and non-execution boundary

Directly parsed GitHub `G0C_REAL_20261025/pair_rows.jsonl` (Git blob `8de45fc200d0e37be676f172d844b3ab2c6c23c7`, 79 edits), `token_audit.jsonl` (`2c5b932ae9e36d5e5380eff558f0437424a39261`, 79), `G1C_REAL_20261025/raw_native_logits_109_requests.jsonl` (`7a55817abea0f15a4162b620a412a18564b315f4`, 109), and `G2C_REAL_20261025/per_pair_heads.jsonl` (`e33e75ae24816768661bb99bc52ae501356114c5`, 26). Reference source group ledger `G0C_REAL_20261025/census.json`, blob `78516e900167e5e94f9a134eeddbc64a047cb17b`. All data are from *existing* G3 DEV run artifacts; no TEST/CAL access, inference, training, remote-server command or causal patching.

Read and compare typed `conflicting_vote`, `quorum`, `certificate_action`, `evidence_level` predictions from raw `questions[].keys/logits` of each `pair_key:old` and `new`. `N1B` eligibility checks both validator membership and treatment-relative token-length equality.

## 2. New observation A: 17/20 directional margin response, but no robust valid-null specificity

Define `M_C(x) = logit_C(true,x) - logit_C(false,x)`; `Δ_old = M_C(new)-M_C(old)`; `Δ_N = M_C(new)-M_C(N1B)`.

| Population | Number | Positive margins | Median | Mean | Exact two-sided sign p |
|---|---:|---:|---:|---:|---:|
| All G3 T2 treatment vs old | 20 | **17/20** | +0.4457 | +0.9169 | **0.00257683** |
| **Only T2 with valid, length-matched N1B:** treatment vs N1B | 13 | **7/13** | +0.0615 | +0.8224 | **1.000** |
| Wait-cell eligible treatment vs N1B | 10 | **5/10** | −0.0997 | +0.3171 | **1.000** |

The 17/20 directional movement suggests the conflict head is **not numerically completely unresponsive** to appended material. Even excluding run338's +9.13 improvement, the old→new directional sign remains 16/19 (two-sided exact p≈0.00443). However valid N1B controls also produce logit changes, and treatment-relative neutral contrasts show **no stable preferred sign**. The valid-control `Δ_N` mean is strongly influenced by the lone run338 `+7.2185`; excluding run338 leaves 6/12 positive and median approximately **−0.0753**, mean approximately **+0.2894**.

**Interpretation:** the model has weak directional *sensitivity* to appending events without corresponding demonstrated *semantic selectivity* between a true conflict and a valid non-supporter appended vote. This supports separating three endpoints: changed numeric evidence readout; semantic discrimination vs valid null; and action decision. These tests are exploratory and multiple subgroup choices are post hoc, so the sign p-values are not a new preregistered inferential claim.

## 3. New observation B: correction to manuscript “3/20 action flips”

G3 has **three T2 new-state correct reject actions**, but they are not three action flips:

| Source | Old C | New C | Old A | New A | Mechanism-neutral interpretation |
|---|---|---|---|---|---|
| run211 | true (**old false alarm**) | true | reject_conflict (**old wrong**) | reject_conflict | Rejection already present; **no action flip** |
| run328 | true (**old false alarm**) | true | accept | reject_conflict | Action changed; old model already reported conflict; its pre-existing action inconsistency is repaired; N1B author invalid and tokens unmatched |
| run338 | false | true | wait (**old Gold accept**) | reject_conflict | Genuine C head false→true and action flip; but old quorum head was also false (**wrong on old**), new quorum true; **valid token-matched N1B also falsely predicts C=true** |

Therefore report `new action gold accuracy = 3/20`, `non-reject→reject transitions = 2/20`, `clean old C=false→new C=true = 1/20`. The last two are distinct from static new-state accuracy. The existing manuscript statement “flipping to ... rejection 3/20” needs to become “new-state rejection accuracy 3/20, of which only two are new action flips.”

Across **all 26 G3 pairs**, independent actions from typed C/Q violate the simple policy rule on old arms in **5/26** and new arms **4/26**. *All 4 new inconsistencies (run181, run212, run372, run83) were already present on the old arm*. Thus **no new inconsistency arises solely on a previously C/Q-action-consistent pair**. One pre-existing inconsistency (run328) **resolves**. This corrects over-interpretation of the T3 action mismatch as an append-*induced* integration failure. IMPORTANT: these are separately scored question rows, not confirmed causal paths between C, Q and A.

## 4. New observation C: remaining unseen source-run budget is exhausted

From G3 `census.json` and frozen per-arm groups:

- Previously frozen A428/A461 excluded groups: **18**.
- T2 confirmation group IDs: **20**, pairwise distinct, disjoint from the excluded 18.
- T3 groups: **6**, of which exactly two (run211, run231) overlap T2; other four (run358, run372, run45, run83) are additional.
- Distinct touched groups: **18+20+4=42/42** Streamlet DEV groups. The G3 candidate-eligible group union is 24 and all 24 have been touched by G3's T2 or T3; the other 18 were previously excluded/touched.

**Consequence:** a further `UNSEEN_DEV_RUN_GROUP` replication from the same frozen Streamlet DEV dataset is impossible without falsely relabeling used source groups. New tests on existing groups can support *paired mechanistic/format-control exploration* only, unless genuinely new independent source groups or an independently reserved corpus split are established and assessed for training leakage. Do **not** use TEST/CAL for ad hoc design selection.

## 5. New CPU design candidate: minimal equal-time final-two-message swap

Prior G3 `SHAM_TS` 6/6 and `SHAM_RO` 6/6 violate the documented observable `received_messages` nondecreasing-time constraint, and only cover the wait cell. I constructed an alternative **CPU-only candidate edit**, based on each of the **26 existing G3 treatment states** (20 T2 across both cells + 6 T3). It swaps *only the last two messages*, which **in all 26 states have identical numeric `received` timestamps**.

For all 26 candidates, verified from actual archived states:
1. Exactly same individual message multiset; only relative order of two adjacent equal-timestamp records changes.
2. Numeric `received` remains nondecreasing, with messages still in the same decision window.
3. Two independently coded oracles (author→list; author→set), using eligible validator, round, receipt-time, supporter and conflict rules, return identical full four-head Gold to the corresponding original G3 treatment (26/26).
4. Four candidates happen to swap same-author adjacent votes; three of those place a conflict event before an old candidate-support vote from that author. These are useful prespecified subgroups *after* provenance validation.

The actual 26 full native-request candidates are committed to [`2026-10-25_A461_G3_equal_received_tie_swap_CPU_candidates.jsonl`](2026-10-25_A461_G3_equal_received_tie_swap_CPU_candidates.jsonl) (Git blob `5cdacdad2ebc052bd607d829dc1713f913372034`). This is **neither a GPU run nor proof of legal original simulator micro-order**. It checks observable numeric chronology and oracle consistency; original message arrival micro-order/provenance constraints may still prohibit reordering equal recorded timestamps. Tokenizer equality and original source verifier rerender have **not** yet been performed. Do **not** label these 26 candidates “fully source-valid/token matched” without the further gates.

Research use: paired position/order stress test on the *same unchanged Gold* with minimal perturbation and full T2 wait/accept coverage, to distinguish a positional/recency contribution from the conflict semantic difference. This is not a new independent confirmation of the pilot because all old run groups are already touched and the new candidate was designed after viewing G3 behavior.

## 6. Literature gate awareness for any subsequent formal model experiment

Three nearest external comparators for this **new order-only control**, as of 2026-10-25:
- Tang et al., *Do Language Models Track Entities Across State Changes?*, ICML 2026, https://proceedings.mlr.press/v306/tang26ah.html — non-incremental state aggregation and a localized fragile suppression mechanism.
- Gur-Arieh, Geva & Geiger, *Mixing Mechanisms: How Language Models Retrieve Bound Entities In-Context*, ICLR 2026, https://proceedings.iclr.cc/paper_files/paper/2026/hash/2eeff35664016c7f0f8aa704f0d9a83e-Abstract-Conference.html — positional/lexical/reflexive binding mechanisms; direct prior-art motivation for the tie-swap confound.
- Zhou et al., *LGMT: Logic-Grounded Metamorphic Testing for Evaluating the Reasoning Reliability of LLMs*, Knowledge-Based Systems 2026, https://www.sciencedirect.com/science/article/pii/S0950705126010506 — logic-preserving metamorphic tests and their general surface sensitivity.

None of these validates the new manipulation *in SecJev*. No mechanism novelty or first-discovery claim is made. A fresh G−1 increment must be frozen and read back if promotion from post hoc CPU candidate to a new formal GPU protocol is proposed.

## 7. Exact next task and explicit stop/admission rules

- **Current necessary CPU task:** `A461_G3_POSTHOC_SOURCE_AND_METRIC_ERRATUM` — fix G3 original incorrect baselines, evidence-level integer parser, N1B legality/length roster, SHAM provenance limitation and 106-vs-109 code ledger. Publish corrected manuscript v3; retain originals.
- **Exploratory control candidate name only (not yet admitted GPU):** `A461_G3_EQUAL_TIMESTAMP_TIE_SWAP_G0_VALIDATION`. Verify original simulator arrival-tie contract; rerender native input with pinned tokenizer and ensure candidate-vs-treatment token lengths, truncated status and branch menus; independent reconstruction and Gold; preserve SHA.
- **STOP** if equal-timestamp swap is semantically illegal under source contract, if Gold changes, if any non-DEV/TRAIN leakage is detected, if independent rerender disagrees, or if no suitable new-group external confirmation can be assembled for generalization.
- Only **after** valid CPU and literature gates, separately freeze any budgeted native or white-box stage; no new GPU was executed in this audit. No claim of GPT Library or server replication for these new files; GitHub commit and readback are verified.

## Decision

**Keep A461 as an empirical behavioral finding; reject current manuscript's fully matched/format-excluded/full-paper claims.** The novel secondary-data result is the **decoupling between directional logit sensitivity to added text and specific discrimination of conflict vs neutral additions**. The new same-time swap is a plausible *minimal* control design to resolve position sensitivity, but the existing source group census forces any independent replication to seek new provenance, not recycle Streamlet DEV.
