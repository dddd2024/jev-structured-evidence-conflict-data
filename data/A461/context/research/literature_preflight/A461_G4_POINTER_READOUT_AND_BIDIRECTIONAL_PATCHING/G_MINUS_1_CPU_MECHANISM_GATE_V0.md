# A461-G4 G−1 literature/architecture gate (CPU-only, pre-protocol candidate)

Date: 2026-10-25. Status: **CPU_GATE_COMPLETE_FOR_RESEARCH_DESIGN, NO_GPU_OR_MODEL_INTERVENTIONS_AUTHORIZED**. This pre-G4 review follows `a6debce` (G3 posthoc errata) and `26875c8` (independent action/margin audit) and is deliberately separate from any future frozen GPU protocol.

## New mechanistic competitors actually relevant to G4

1. **SecJev** Chen et al. (2026), https://arxiv.org/html/2610.03073v2, §§3.1–3.3: defines this exact task interface and pointer scorer architecture. The inference backbone is **Qwen3.5 hybrid recurrent/attention**. Every question is an **independent state + branch causal row**; the `conflicting_vote`, `quorum`, `evidence_level`, and `certificate_action` predictions are *not a four-stage neural pipeline*. Learned pointer readout:
   `z_k = [(W_Q h_decide+b_Q)^T (W_K h_option_end_k+b_K)]/(sqrt(256)*T)`.
   The scorer's pointer `Q`/`K` projections are **not** attention-layer query/key heads. SecJev already supplies the scorer, candidate tokens, LoRA structure and corpus, so describing this decomposition or raw pointer head alone is **not new**.
2. **Tang et al.**, *Do Language Models Track Entities Across State Changes?* (ICML 2026), https://proceedings.mlr.press/v306/tang26ah.html. Finds retrieval/aggregation at query time and a fragile REMOVE suppression mechanism with patching. Strong closest mechanism comparator: a G4 result must isolate something specific to conflict-append/voter-block-round relations rather than re-demonstrating general state-tracking fragility.
3. **Gur-Arieh, Geva & Geiger**, *Mixing Mechanisms: How Language Models Retrieve Bound Entities In-Context* (ICLR 2026), https://proceedings.iclr.cc/paper_files/paper/2026/hash/2eeff35664016c7f0f8aa704f0d9a83e-Abstract-Conference.html. Distinguishes positional, lexical and reflexive binding channels; directly motivates independent order/position/author perturbations.
4. **Zhang & Nanda**, *Towards Best Practices of Activation Patching in Language Models: Metrics and Methods* (ICLR 2024), https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html. Restoration/localization depends on corruption distribution and metric. Report raw signed logits and matched sham/negative controls, not just hand-picked flip counts.
5. **Li, Guo & Andreas**, *(How) Do Language Models Track State?* (ICML 2025), https://proceedings.mlr.press/v267/li25r.html, provides alternative state-tracking computation and cautions against presupposing a sequential mechanism.

## Pinned source code anchor

SecJev `UPSTREAM.md` pins Kev commit `90990a5fac2995b9faa3190f7d437e84f2067768`; `kev/model.py` Git blob SHA `2b2dead6a03946b02c9be16c914672d7bde64f8b`:
- `PointerHead` uses `q:Linear(hidden,256)`, `k:Linear(hidden,256)`; head temperature divides logits only in eval if unequal to one;
- `rows_of(enc)` returns each question-branch's `decide` and candidate `opts` offsets *relative to the branch*;
- `DecisionModel.forward_rows_batch()` produces independent row forward passes when hybrid;
- the source explicitly warns that Qwen3.5 Gated DeltaNet hybrid layers cannot honor the naïve packed block-causal mask. Never patch recurrent state as though it were an ordinary attention-only Transformer residual stream.

The G3 frozen G1C `pre_forward_token_gate_receipt.json` reports **26/26 identical question-branch token hashes and candidate menus** within same-pair old/new requests, but the added event changes state token count **by +33 on 12 pairs and +34 on 14**. Thus absolute token indices differ for question marker and candidate delimiters; patch by independently located readout markers/branch-relative indices, with exact rerender/trace before intervention. Direct whole-sequence same-index patching is invalid. Some within-group donor pairs are not same-state and must not be promoted as semantic-isolated causal controls.

## Strict G3 cohort and donor limitation

CPU cohort frozen as `research/experiments/2026-10-25_A461_G4_POINTER_HEAD_CAUSAL_CPU_COHORT_V0.json`:
- **11 T2 pairs** are correctly old-C=false, valid token-matched N1B-C=false, and fail treatment C=true Gold.
- **7 accept T2** are invalid/unmatched N1B; must not join strict semantic-specificity estimates.
- **6 T3** are existing-conflict positive contexts; only 2 source groups overlap any T2 group, and source states differ.
- **run338** clean old-C=false to new-C=true is the rare successful transition, **but its matched valid N1B is already false-positive C=true**. There is therefore **zero same-scene clean-to-conflict donor with valid-neutral-C=false and treatment-C=true** in the G3 archive.

This is an *admission failure for the claimed full bidirectional semantic-restoration mechanism*, not a failure to study pointer-algebra decomposition. A G4 readout reconstruction from old/new can be conducted later after separate GPU approval, but a positive/negative donor study capable of ruling out semantic-independent transfers currently lacks qualified positive donors.

## Planned falsifiable G4 alternatives

- **H_Q:** added evidence has a weak/irrelevant effect on decision-marker query vector while candidate key differences stay usable.
- **H_K:** evidence affects candidate-end representations but does not properly encode true-vs-false relationship at key positions.
- **H_B:** neither Q nor K in isolation is defective; their conjunction/interaction is inconsistent across conflict edits.
- **H_P:** missed evidence is primarily positional/recency or source-format sensitive; chronology-valid matched order/author controls reduce apparent effect.
- **H_A:** certificate action anomalies persist independently of conflict readout errors; C/Q/A row predictions are separate, so direct C→A neural mediation does not exist in this architecture as previously claimed.

A first readout-only *exact accounting identity* uses `q_i = W_Q h_decide_i+b_Q`, `d_i = k_true_i-k_false_i`, `k = W_K h_option+b_K`, `T` = readout temperature and `s=sqrt(256)T`; `M_i=q_i·d_i/s`. Then
`M_new - M_old = [(q_new-q_old)·d_old + q_old·(d_new-d_old) + (q_new-q_old)·(d_new-d_old)] / s`.
The three terms are **query, candidate-key, interaction algebra**. They are not neuron-level causal mediators; their computation requires saved projected vectors from actual model forwards. Validate exact reconstruction against native logits to FP32 tolerance before interpreting any term. **The existing archived G1C logits alone cannot identify Q and K separately** (factorization is underdetermined).

Actual causal patching must be independently preregistered: full state/branch row path, semantically aligned token positions, both `failing target ← valid positive donor` and `positive target ← failing donor` directions, donor/target logits, same-location sham, random-token and unrelated-head controls, and off-target Q/action metrics, with cluster/source group reporting. A T3 donor can serve as a *diagnostic OOD/same-task positive* but **cannot** establish semantic-specific same-scene restoration.

## Decision and next action

**G−1 verdict: NO DUPLICATE ESTABLISHED, NOVELTY UNPROVEN, G4_CPU_DESIGN_ALLOWED, GPU_PATCHING_NOT_ADMITTED.**

CPU next: independent hook/architecture validation + exact token-position map and source contract for donors, run grouping, metric/stop-condition freeze; execute no GPU until the anticipated independent G3-v3 review has been read and its blockers resolved. If no legally matched positive donor exists, demote “bidirectional causal mechanism” to *readout decomposition + negative-result probe*; seek truly independent groups/legitimate counterfactuals before claiming a causal security-specific mechanism. Do not use previously seen Streamlet DEV groups as “unseen group” confirmation.
