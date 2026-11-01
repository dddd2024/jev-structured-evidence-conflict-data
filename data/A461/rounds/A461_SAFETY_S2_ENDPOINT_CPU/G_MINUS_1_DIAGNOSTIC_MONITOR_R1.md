# G−1 for the A461 diagnostic monitor (literature only, 2026-10-31)

**Scope:**
- **Required by:** standard V1 §1.1, before any monitor protocol is frozen.
- **Requested by:** the user, who chose the safety target "S2 + diagnostic monitor" on 2026-10-31.
- **Method:** web search only, no experiment. I read only abstracts or conclusions of the works below, so the method sections of the closest competitors must still be read before the protocol is frozen. The status is set accordingly.

## Closest prior work, by the four G−1 classes
| class | work | what it shows | relation to us |
|---|---|---|---|
| same method: activation probes for model errors | [Probe-based detection of tool-calling errors](https://arxiv.org/pdf/2608.27750) | Linear probes detect tool-call errors. Effectiveness depends on model size, layer and post-training | Generic error probe, no rule-defined safety Gold |
| same method | [Question-only linear probes predict answer accuracy](https://en.papernotes.org/ICLR2026/llm_reasoning/no_answer_needed_predicting_llm_answer_accuracy_from_question-only_linear_probes/) (ICLR 2026) | A pre-answer probe predicts correctness and transfers across domains | Same idea (read the error before the action), different task |
| same method, limits | [Hallucination detectors out of distribution](https://preview.aclanthology.org/author-page-yu-wang-polytechnic/2025.findings-emnlp.952.pdf) (EMNLP 2025 Findings); [arXiv 2604.24801](https://arxiv.org/pdf/2604.24801.pdf) | Representation detectors can fall to near chance OOD. Probes miss confident errors when the architecture does not keep the signal | Our held-out split must be by source group, and the result may be negative |
| same safety endpoint: policy violation | [Training-free policy-violation detection via activation whitening](https://arxiv.org/html/2512.03994v2) | OOD scoring of hidden states against compliant responses; AUC 0.87 on τ-bench agent trajectories | Strongest competitor for "a white-box monitor of a policy error"; a baseline to adopt |
| same safety endpoint: unauthorized actions | [arXiv 2604.03870](https://www.emergentmind.com/papers/2604.03870) | Probes at the tool-input position intercept hijacked actions | Position-specific probing, as we would do at the append span |
| same problem: equivocation in consensus | [CometBFT evidence](https://docs.cometbft.com/main/spec/consensus/evidence); [Byzantine detection in DAG consensus](https://arxiv.org/html/2408.02000v1) | Deterministic equivocation evidence is standard in BFT systems | The rule baseline. No LLM-based equivocation checker was found |

## Novelty delta and verdict
**Not new:** a probe or OOD detector on hidden states that flags model errors. To be a contribution, the monitor has to win on the following, all of them testable:
1. **Mechanism-located against generic:**
   - A monitor read at the location found by M1–M5 (the L11 append-span state) against generic baselines on the same rows:
     - a last-token probe at the same and other layers;
     - activation whitening (2512.03994);
     - the model's own conflict and action margins.
   - All are compared at a fixed false-veto rate, on held-out source groups.
   - If the mechanism-located monitor does not beat the generic ones, the monitor is infrastructure validation, not a contribution.
2. **Missed errors specifically:**
   - The monitor must flag the scenes the model *gets wrong*: Gold `reject_conflict`, predicted `accept`.
   - Its false veto on benign and duplicate scenes must stay near kev-4B's natural 0% (S2 note).
   - This also tests the mechanism: whether conflict information is present in the failing scenes' internal state even though the action misses it.
     - Present: H-READ, encoded but not acted on.
     - Absent: H-ENC.
   - M1 and SecJev's H3 (layer 11 AUC 0.84, below its 0.9 threshold) suggest that the answer may be partial.
3. **Honest baseline:** the executable rule has 0 errors. The monitor's value is therefore restricted to settings where the learned scorer is deployed without that rule, or as a check on the scorer itself. The paper says this explicitly.

## Method sections read (2026-10-31)
- **2608.27750 (tool-calling error probes, PNNL / NSA):**
  - Logistic-regression probes on the hidden state at the **last token** of the generated tool call, every 5th layer, 18 models.
  - Evaluation: AUROC, AUPR and FPR@90%TPR. Generalization is tested to held-out *error types*.
  - The authors state as a limitation that they used only the last token and did not compare other token positions.
  - **Their measurements are correlational. No causal localization was done.**
- **2512.03994 (activation whitening):**
  - The final-token hidden state at one layer per policy category.
  - PCA whitening (k = 15) is fit on compliant samples only, using GPT-4o synthetic contrastive data. The score is a Mahalanobis distance, with a Youden-J threshold.
  - Results: DynaBench F1 74–82 against guard models. There is no cross-dataset OOD test.
- **2604.03870 (hijacked agent actions):**
  - Per-layer logistic regression and a cosine "danger direction", tested at two positions: the **tool-input** position (where the injection is) and the function-call position.
  - The input position is far better: TPR@5%FPR is 97% against 53% on Qwen3-14B.
  - The split is 80/20 random on one benchmark, with no held-out environments.
  - **This is the closest result to our position question.** Position matters, and the position carrying the offending input wins.

**Consequence for the delta:**
- **Already shown:** reading at the offending input's position, rather than the last token, has been shown once, with an empirically chosen position.
- **Not yet shown:**
  - a monitor position derived from a *causal* localization (M1–M5: the L11 append-span state is sufficient to repair, and is written by heads 8–14);
  - such a monitor tested against a rule-defined safety Gold, on held-out *source groups*, at a fixed false-veto rate, against a last-token probe and a whitening detector on the same rows;
  - the encoded-but-not-acted question (H-READ against H-ENC), which none of the three addresses.
- **Already done locally:** the three comparisons above are fixed as the required arms of the monitor prereg.

**G−1 status: `NOVELTY_DELTA_TESTABLE` (narrow).** The delta survives if the causally located span monitor beats the last-token probe and the whitening detector on held-out source groups at the same false-veto rate. It fails if they match or beat it, in which case the monitor is reported as `INFRASTRUCTURE_VALIDATION_ONLY`. The H-READ/H-ENC answer is a mechanism result either way.

**What would make it redundant:** a generic last-token probe or whitening detector that matches the span monitor on held-out groups at the same false-veto rate.
