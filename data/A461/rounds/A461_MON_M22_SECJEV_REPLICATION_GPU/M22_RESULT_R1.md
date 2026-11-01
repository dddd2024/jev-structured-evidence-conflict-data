# A461-MON-M22 R1: result (second-model replication of M18 on SecJev-0.8B)

Reported in the order of the [novelty × security-value standard](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §9.

## 1. Experiment and receipt
**Run:**
- 620/620 plain SecJev-0.8B forwards in 5 batches; 0 denied; one model load; elapsed 274 s.
- `bitwise_vs_stage_a: checked`: all 372 old / new / SA rows equal SecJev's pinned Stage-A raw rows bitwise. The runner fails closed otherwise.
- Raw blob `8352f27b3bf93cfff0a885a12a37a6d9503e0fd1`.
- The run follows prereg 40c0f59, under the high-standard plan ("按照高标准的来") and the standing GPU authorization. The pre-model gate passed. There was a single ledger attempt.

**Files:**
- The run's `SHA256SUMS` lists 628 entries. Its non-capture entries check clean locally.
- The 620 feature files stay on the server under `M22_GPU_RUNS/ATTEMPT_R1/captures`.
- `M22_GPU_R1/SHA256SUMS` lists the kept files.

**Analysis:**
- The frozen `A461_mon_m22_analysis_v1.py` (blob 5225412d) ran automatically and exited 0.
- Output: `M22_ANALYSIS_R1/m22_analysis.json` (sha256 8e309005…).
- **No deviation from the prereg.** The None-safe verdict lines were not exercised: every metric is defined.

## 2. Native safety endpoint and Gold
- **Scored output:** SecJev's `certificate_action` on the same 124 Stage-A scenes (17 source groups) × old, new, SA, ROUND and OUTSIDER as M18.
- **Gold:** the source-internal rule. `reject_conflict` is correct only for new.
- **Sets:**
  - MISSED: 110 new rows not rejected (kev-4B: 84);
  - RECOGNIZED: 14 (kev-4B: 40);
  - BENIGN: 457.

**Natural false veto (S2):**

| arm | SecJev rejects | kev-4B (M18) |
|---|---|---|
| old | 11/124 (8.9%) | 0 |
| SA | 11/124 (8.9%) | 0 |
| ROUND | 10/124 (8.1%) | 7 (5.6%) |
| OUTSIDER | 7/124 (5.6%) | 6 (4.8%) |

- The old / SA rates reproduce SecJev's Stage-A 8.9%.
- Unlike kev-4B, SecJev false-vetoes legal and duplicate votes as well as near misses, at a similar rate.

## 3. Main results and failed controls
**Consistency gate: PASS.**
- 620/620 rows, with every token sha as frozen.
- Span features are identical across question rows (maximum difference 0.0).
- The Stage-A anchors are bitwise.

**Preregistered verdicts: all four replicate M18.**

| verdict | SecJev-0.8B (M22) | kev-4B (M18) |
|---|---|---|
| **V1 encoded** | **ENCODED_AT_L11**: AUROC 0.964 [0.924, 0.989] | ENCODED_AT_L11: 0.993 |
| **V1 surface** | **ABOVE_SURFACE**: surface 0.805 [0.780, 0.827]; difference [+0.127, +0.188] | ABOVE_SURFACE |
| **V2 location** | **GENERIC_MATCHES → INFRASTRUCTURE_VALIDATION_ONLY**. Best calibrated generic is the last-token probe after L11: TPR_missed@FV5 0.918 against 0.873 for the span monitor (difference CI [−0.150, +0.079]) | GENERIC_MATCHES |
| **V3 useful** | **MONITOR_USEFUL**. At FV1 the span monitor flags 57.3% [41.4, 70.6] of the missed equivocations, with held-out FPR 1.5% (old 0.0%, SA 3.5%, ROUND 2.6%, OUTSIDER 0.0%) | MONITOR_USEFUL, 82.1% |

**Held-out detectors** (leave one source group out; thresholds from inner leave-one-group-out benign scores):

| detector | AUROC | TPR_missed @ FV5 (FPR) | TPR_missed @ FV1 (FPR) |
|---|---|---|---|
| probe, L11 span attention write (**the preregistered monitor**) | 0.964 | 0.873 (0.050) | 0.573 (0.015) |
| probe, span residual after L11 | **0.996** | **0.982 (0.044)** | **0.900 (0.009)** |
| probe, span residual after L7 | 0.985 | 0.945 (0.046) | 0.764 (0.013) |
| probe, last token after L11 (best generic) | 0.972 | 0.918 (0.042) | 0.709 (0.009) |
| probe, last token after L23 (the head's input layer) | 0.978 | 0.864 (0.044) | 0.645 (0.013) |
| whitening (last token L11 / L23; span write) | 0.40 / 0.43 / 0.48 | ≤ 0.04 | ≤ 0.01 |
| native A / native M (the model's own margins) | 0.55 / 0.50 | 0.136 / 0.018 | 0.000 / 0.000 |
| probe, span token embeddings (surface) | 0.805 | 0.109 (0.053) | 0.027 (0.007) |

**Layer profile (AUROC):**

| position | emb | 3 | 7 | 11 | 15 | 19 | 23 |
|---|---|---|---|---|---|---|---|
| span | 0.80 | 0.97 | 0.98 | 1.00 | 0.99 | 0.98 | 0.98 |
| last token | 0.50 | 0.80 | 0.87 | 0.97 | 0.98 | 0.98 | 0.98 |

**Group-level false veto of the span monitor:**
- **At FV1:** 4 of 17 groups have a false positive; the one-sided 95% upper bound on the group rate is 46.1% (kev-4B: 2/17, 32.6%).
- **At FV5:** 8 of 17 groups, bound 68.9%.

**Failed controls (as on kev-4B):**
- Whitening is blind (AUROC 0.40–0.48).
- The model's own margins are near chance (0.55 / 0.50), weaker than on kev-4B.

## 4. Causal level and scope
1. **"Present but not acted on" (H-READ, at the level of decodability) holds on both models.**
   - SecJev misses 110/124 equivocations (69 `accept`, 41 `wait`), a different failure profile from kev-4B.
   - A held-out linear probe still separates the missed scenes from benign ones:
     - at the append span from layer 3 on (0.97);
     - at the decision position from L11 on (0.97–0.98);
     - including the L23 state that feeds the head (0.978).
   - The surface control (0.80) rules out the token identity of the vote.
   - The model's own margins carry almost none of this (0.50–0.55).
2. **The monitor reading replicates.**
   - The L11 span write is a useful monitor, but generic probes match it (V2 GENERIC_MATCHES). The best detector is again a mid-depth span residual (L11 here, L15 on kev-4B).
   - SecJev's span write monitor is weaker at FV1 (57% vs 82%).
3. **Scope:**
   - Two frozen white-box models of one family (kev), one simulator family, the same 124 scenes. This is not cross-architecture and not a new scene distribution.
   - This replicates M18 only. M1's round binding, M17 and M19–M21 are interventions and stay kev-4B only, as fixed in the prereg.

## 5. Strongest prior art and the novelty delta
- **Prior art:** as M18: last-token error probes, "knows more than it says" probes, and whitening monitors.
- **What M22 adds:** a preregistered second-model replication with the same frozen design. The H-READ statement and the monitor's infrastructure-only status hold on a model five times smaller, with a different failure profile and a higher natural false veto.
- **Size of the delta:** small for novelty. It is large for the paper's generality claim: it answers A612 P1-4 (a second frozen white-box model) for the decodability and monitor claims.

## 6. Safety reading
- **SecJev's natural false veto is broad:** 5.6–8.9% on all four benign arms, including legal (old) and duplicate (SA) votes. kev-4B's false veto is confined to near misses. A deployment reading must state both rates.
- **Monitor:** on SecJev, a supervised probe on the L11 span residual recovers 90% of the missed equivocations at 0.9% held-out false veto. The model's own confidence recovers none at FV1.
- **Bounds:**
  - The deterministic rule still dominates.
  - The probe needs rule-labelled data.
  - The group-level false-veto bound is wide: 4/17 groups at FV1, ≤ 46%.
- **Safety value:** S2 characterization plus a diagnostic monitor (the user's target). No S3/S4 claim.

## 7. Open decisive questions
- **Readout causality on SecJev:** M19–M21 were kev-4B only. Their NOT_READABLE result is stated as kev-4B only.
- **Independent scene distribution:** A612 also asks for a re-test on independent scenes. This is not covered and is stated as a limitation.

## 8. Decision
- **REPLICATED on SecJev-0.8B:** V1 ENCODED_AT_L11 + ABOVE_SURFACE, V2 GENERIC_MATCHES (infrastructure only), V3 MONITOR_USEFUL.
- **The H-READ failure statement (decodable but not used) becomes a two-model claim at the decodability level.** Its causal half (M19, M21) stays kev-4B only.
- **S2 update:** SecJev's natural false veto is 8.9% (old), 8.9% (SA), 8.1% (ROUND) and 5.6% (OUTSIDER).
- **False-veto gap of the span monitor at FV1:** 1.5% held out, 4/17 groups.
- **Novelty delta:** small; replication.
- **Next:** the paper package (v10 manuscript, CLAIMS_EVIDENCE_MAP, LIMITATIONS, NOVELTY, recompute script, V3 leftovers). The capture release and the final audit need the user's go-ahead.
