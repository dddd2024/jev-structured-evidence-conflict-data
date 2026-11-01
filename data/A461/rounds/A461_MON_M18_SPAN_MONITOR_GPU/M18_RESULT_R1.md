# A461-MON-M18 R1: result (a diagnostic monitor at the L11 append-span state, against generic monitors)

Reported in the order of the [novelty × security-value standard](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §9.

## 1. Experiment and receipt
**Run:**
- 620/620 plain kev-4B forwards in 5 batches; 0 denied; one model load; elapsed 942 s.
- `bitwise_vs_stage_a: checked`: all 372 old / new / SA rows equal the pinned Stage-A raw rows bitwise. The runner fails closed otherwise.
- Raw blob `10e04cfadfaba7364abbb2eeb922b92c09ad9ea4`.
- The run follows prereg ebd82ff, under the user's safety target ("S2 + diagnostic monitor"), the request "Yes, design monitor", and the standing GPU authorization. The pre-model gate passed. There was a single ledger attempt.

**Files:**
- The run's `SHA256SUMS` lists 628 entries. Its 8 non-capture entries check clean locally.
- The 620 feature files (264 MB) stay on the server under `M18_GPU_RUNS/ATTEMPT_R1/captures`.
- `M18_GPU_R1/SHA256SUMS` lists the kept files.

**Analysis:**
- The frozen `A461_mon_m18_analysis_v1.py` (blob da541fdb) ran automatically and exited 0.
- Output: `M18_ANALYSIS_R1/m18_analysis.json` (sha256 94c30ab3…).
- **No deviation from the prereg.**

## 2. Native safety endpoint and Gold
- **Scored output:** `certificate_action` of kev-4B on the 124 Stage-A scenes (17 source groups) × five arms: old, new, SA, ROUND and OUTSIDER.
- **Gold:** the source-internal rule. `reject_conflict` is correct only for new, a lawful equivocation.
- **MISSED:** the 84 new rows the model accepts. These are its false accepts.
- **BENIGN:** the 483 benign rows the model does not reject.

**Natural false veto, a new S2 fact:**
- kev-4B itself rejects 7/124 ROUND rows (5.6%) and 6/124 OUTSIDER rows (4.8%), across 7 source groups. 7 of these 13 are on `wait`-Gold scenes.
- It rejects 0 old and 0 SA rows.
- So the S2 note's "0 false veto" holds for legal and duplicate scenes only. On near-miss votes the model does false-veto, about 5% of the time.

## 3. Main results and failed controls
**Consistency gate: PASS.**
- 620/620 rows, with every token sha as frozen.
- Span features are identical across question rows (maximum difference 0.0).
- The Stage-A anchors are bitwise.

**Preregistered verdicts:**

| verdict | value |
|---|---|
| **V1 encoded** | **ENCODED_AT_L11**: AUROC(probe on the L11 span write; MISSED vs BENIGN, held-out groups) = 0.993 [0.985, 0.998] |
| **V1 surface** | **ABOVE_SURFACE**: the token-embedding span probe gives 0.816 [0.796, 0.836]; the difference is +0.18 [0.158, 0.197] |
| **V2 location** | **GENERIC_MATCHES → INFRASTRUCTURE_VALIDATION_ONLY**. The best calibrated generic detector is the last-token probe after layer 19: TPR_missed@FV5 1.000 against 0.952 for the span monitor (difference −0.048 [−0.109, −0.010]) |
| **V3 useful** | **MONITOR_USEFUL**. At FV1 the span monitor flags 82.1% [63.4, 95.1] of the missed equivocations, with held-out FPR 1.7% overall (old 1.6%, SA 4.0%, ROUND 0.9%, OUTSIDER 0.0%) |

**Held-out detectors:** leave one source group out. Thresholds come from inner leave-one-group-out benign scores.

| detector | AUROC | TPR_missed @ FV5 (FPR) | TPR_missed @ FV1 (FPR) |
|---|---|---|---|
| probe, L11 span attention write (**the preregistered monitor**) | 0.993 | 0.952 (0.048) | 0.821 (0.017) |
| probe, same, writer heads 8–14 only | 0.993 | 0.964 (0.052) | 0.869 (0.010) |
| probe, span residual after L11 | 0.997 | 1.000 (0.048) | 0.940 (0.010) |
| probe, span residual after L15 | **1.000** | 1.000 (0.046) | **1.000 (0.006)** |
| probe, last token after L19 (best generic) | 0.999 | 1.000 (0.043) | 0.976 (0.010) |
| probe, last token after L31 (the head's input layer) | 0.990 | 0.964 (0.048) | 0.940 (0.012) |
| probe, last token after L11 | 0.938 | 0.488 (0.046) | 0.155 (0.027) |
| whitening (last token L11 / L31; span write) | 0.40 / 0.49 / 0.50 | ≤ 0.05 | ≤ 0.01 |
| native A / native M (the model's own margins) | 0.64 / 0.73 | 0.155 / 0.119 | 0.024 / 0.036 |
| probe, span token embeddings (surface) | 0.816 | 0.143 (0.050) | 0.036 (0.006) |

**Layer profile (AUROC):**

| position | emb | 3 | 7 | 11 | 15 | 19 | 23 | 27 | 31 |
|---|---|---|---|---|---|---|---|---|---|
| span | 0.82 | 0.99 | 0.98 | 1.00 | 1.00 | 1.00 | 0.99 | 0.99 | 0.99 |
| last token | 0.50 | 0.85 | 0.88 | 0.94 | 0.98 | 1.00 | 1.00 | 0.99 | 0.99 |

**Group-level false veto of the span monitor:**
- **At FV1:** 2 of 17 groups have any false positive. The Clopper–Pearson one-sided 95% upper bound on the group rate is 32.6%.
- **At FV5:** 8 of 17 groups, bound 68.9%.

**Failed controls:**
- Whitening does not detect the conflict at all (AUROC ≈ 0.4–0.5). The equivocation rows are not out of distribution relative to benign rows, so an unsupervised OOD monitor (2512.03994) is blind to this error.
- The model's own margins are weak monitors (AUROC 0.64 / 0.73).

## 4. Causal level and scope
1. **The conflict is represented but not acted on (H-READ over H-ENC), for the scenes the model misses.**
   - In the 84 scenes where kev-4B accepts the equivocation, a linear probe trained on other source groups separates them from benign scenes with AUROC 0.99–1.00:
     - from the appended span from layer 3 on;
     - from the decision position (the `certificate_action` row's last token) from layer 15 on;
     - including the layer-31 state that feeds the decision head (AUROC 0.990; 94% flagged at a 1.2% false-veto rate).
   - The token-embedding control (0.82) shows this is not just which tokens are in the vote.
   - So the miss is not a failure to form the conflict representation. It sits in the final readout: the head maps a state that linearly encodes the conflict to `accept`.
   - **This revises the candidate account of the consolidation (§5).** It had favoured an L11 read or composition failure, with H-ENC open.
   - **Limit:** decodability is not use. A supervised probe can find a direction that the model's head does not use, and this result shows exactly that gap. A causal statement needs a readout-level intervention (§7).
2. **Mechanism-located monitor: no advantage.**
   - The causally located L11 write is a good monitor, but generic last-token probes at mid-depth are as good or better.
   - So the M-line localization does not buy monitoring power (V2, preregistered → INFRASTRUCTURE_VALIDATION_ONLY).
   - The best detectors overall are mid-depth residuals at the span (L15) or at the decision position (L19).
3. **Scope:**
   - One model (kev-4B), one simulator family, 124 scenes in 17 groups.
   - Detection rates are held out by group.
   - Group-level uncertainty is large: the 1% operating point still leaves false positives in 2 of 17 groups.

## 5. Strongest prior art and the novelty delta
- **Prior art:**
  - Last-token probes for model errors (2608.27750);
  - "the model knows more than it says": answer-correctness and hallucination probes, e.g. 2509.10625, and the A612 index;
  - whitening monitors (2512.03994).
- **Monitor novelty:** **does not survive** (preregistered GENERIC_MATCHES). The span monitor is reported as infrastructure validation.
- **What M18 adds, at S2:**
  1. The specific safety error of these scorers is a *readout* failure. The equivocation is linearly present at the head's input layer in 94–100% of the missed cases, at about 1% held-out false veto.
  2. An unsupervised OOD monitor is blind to it, while a cheap supervised last-token probe catches nearly all of it.
  3. The model natively false-vetoes about 5% of near-miss votes.
- (1) is the substantive mechanism finding. It shares its form with known "knows but does not say" results, so its novelty lies in the safety task, the held-out source-group design and the link to the M-line interventions, not in the phenomenon class.

## 6. Safety reading
- **Practical:**
  - A learned scorer of this kind should not be trusted alone for equivocation. That was already the S2 conclusion.
  - If it is deployed without the deterministic rule, a supervised probe on its own internal states recovers almost all of its missed equivocations at about 1% false veto on held-out source groups:
    - last-token L19: 97.6% at 1.0%;
    - span L15: 100% at 0.6%.
  - The model's own confidence (its margins) does not.
- **Bounds:**
  - The deterministic rule still dominates: 0 errors.
  - The group-level false-veto bound at 1% is wide (≤ 32.6% of groups).
  - The labels come from the rule, so a probe monitor needs rule-labelled training data. In practice that means the rule is available, and the monitor's value is as a check on the scorer, or as a diagnostic of where it fails.

## 7. Open decisive questions
1. **Why the head ignores a present feature (the readout question).** Compare the held-out probe direction at the decision position (layer 31) with the head's `reject_conflict` − `accept` readout direction, and test whether adding the probe direction at the decision position, scaled, flips the action. Run it with the M17 false-veto controls.
   - The comparison can be done on CPU from the saved features and the head weights.
   - The steering test is one GPU stage.
   - It is the step that would turn H-READ from decodability into a causal statement.
2. **Second model:** the same monitor on SecJev-0.8B, which also false-vetoes about 9% of benign scenes.

## 8. Decision
- **Diagnostic monitor:**
  - V3 KEEP: useful at FV1.
  - Novelty REJECT: infrastructure only.
  - For the paper it is a safety demonstration, not a contribution claim.
- **Mechanism:**
  - **KEEP and upgrade the failure account to H-READ (representation present; readout fails)** at the level of linear decodability.
  - The consolidation's candidate account is revised.
  - The natural-path step now targets the readout (§7.1), not L11 formation.
- **S2:**
  - Add the near-miss natural false veto: ROUND 5.6%, OUTSIDER 4.8%.
  - "0 false veto" now applies to legal and duplicate scenes only.
