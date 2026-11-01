# A461-MECH-M19 R1: result (is the encoded conflict usable by the readout?)

Reported in the order of the [novelty × security-value standard](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §9.

## 1. Experiment and receipt
**Run:**
- 5580/5580 kev-4B forwards in 44 batches; 0 denied; one model load; elapsed 8211 s.
- `bitwise_vs_m18: checked`: all 620 replays are bitwise equal to M18.
- In every one of the 4960 op rows, the three other question rows' logits equal the replay's bitwise. This is runner-enforced and fail-closed.
- Raw blob `f766128ab2ad983fc93687ffcde7f61be764ee96`.
- The run follows prereg 50227eb (requested by the user: "Yes, readout test"), under the standing GPU authorization. The pre-model gate passed, and there was a single ledger attempt.

**Files:**
- The run's `SHA256SUMS` lists 667 entries. Its 47 non-capture entries check clean locally.
- The 620 replay captures (post-norm `<decide>` and option states) stay on the server.

**Analysis:** the frozen `A461_mech_m19_analysis_v1.py` (blob 1f8ceeee) ran automatically and exited 0. **No deviation from the prereg.**

## 2. Native safety endpoint and Gold
- **What is scored:** kev-4B's `certificate_action` on the 124 Stage-A scenes × five arms, against source-internal Gold.
- **REPAIR:** the share of the 84 MISSED equivocations that become `reject_conflict`.
- **FV:** the share of the 483 BENIGN rows (old / SA / ROUND / OUTSIDER, not natively rejected) that become `reject_conflict`.
- **Level:** S1–S2, an intervention scored on the native action.

## 3. Main results and failed controls
**Consistency gate: PASS.** 5580 rows; 620 replays bitwise equal to M18; 620 rows per op condition.

**Preregistered verdicts:** **L19: READOUT_GAIN_INERT; L31: READOUT_GAIN_INERT.**

| arm | REPAIR (of 84) | FV (of 483; every arm) | recognized kept | median dA, missed |
|---|---|---|---|---|
| probe L19, γ 2 / 4 / 8 | 0 / 0 / 0 | 0 / 0 / 0 | 40/40 | −0.0003 / −0.0009 / −0.0021 |
| probe L31, γ 2 / 4 / 8 | 0 / 0 / 0 | 0 / 0 / 0 | 40/40 | −0.0008 / −0.0024 / −0.0056 |
| random L19 / L31, γ 8 | 0 / 0 | 0 / 0 | 40/40 | −0.0000 / 0.0000 |

- The group-bootstrap intervals are [0, 0] for every arm.
- No benign group shows a false veto (0/17; the one-sided 95% bound is 16.2%).

**Size of the intervention (descriptive, from the recorded op stats; median over rows):**

| layer | \|h·u − c\| | \|h\| | \|Δh\| / \|h\| at γ 2 / 4 / 8 |
|---|---|---|---|
| L19 | 0.12 | 19.3 | 0.6% / 1.9% / 4.4% (p95 at γ 8: 25%) |
| L31 | 0.20 | 340 | 0.06% / 0.18% / 0.41% (p95 at γ 8: 2.1%) |

**Readout geometry (reported).** In the head's input space (post-final-norm `<decide>` states), the median cosine is as follows:
- between a held-out probe direction fit on those states and each row's exact gradient of z_reject − z_accept;
- **MISSED −0.024; RECOGNIZED +0.002; BENIGN −0.022.**

**Failed controls:** none. Random directions are inert, as expected.

## 4. Causal level and scope
1. **At the preregistered doses, amplifying the model's own deviation along the held-out conflict direction does not move the decision (INERT at L19 and L31).** The action margin of the missed rows changes by less than 0.006 even at γ 8.
2. **This is a weak negative, and it must be read with its size.**
   - The probe direction, de-standardised from a probe trained on standardised features, weights low-variance coordinates. So the conflict deviation along it is tiny relative to the residual stream: 0.6% of |h| at L19 and 0.06% at L31.
   - Even γ 8 changes the decide state by 4.4% (L19) and 0.4% (L31).
   - M19 therefore does **not** show that the conflict feature is unusable. It shows that the *linearly most separating direction* carries almost no energy at the decision token, and that amplifying it within 8× is inert.
3. **The geometry explains the miss better than the dose test does.**
   - In the space the pointer head actually reads, the direction that separates conflict from benign states is essentially orthogonal (cos ≈ −0.02) to the direction that would raise `reject_conflict` over `accept`.
   - The same near-zero cosine holds for recognized rows. So recognition, when it happens, does not run along this probe direction either, and the head's decision depends on other components of the state.
   - Read together with M18: the conflict is linearly present at the decision token, but in a low-energy direction that the readout does not weight. "Present but not read" is supported geometrically. It is **not** established causally (§7).
4. **Scope:** kev-4B, twins_streamlet DEV, 124 scenes in 17 groups. The geometry is descriptive, and the dose test covers γ ≤ 8 along one direction family.

## 5. Strongest prior art and the novelty delta
- **Prior art:** steering along probe directions (representation engineering), and the known gap between probe directions and causally used directions. A probe direction is not the model's own readout direction; mean-difference or causally fitted directions often steer better.
- **What M19 adds:** a preregistered, false-veto-controlled null for input-dependent gain along the held-out probe direction on a safety decision, together with the readout geometry that explains it.
- **Size of the delta:** small. Negative and descriptive results of this kind are expected by the literature.
- **Novelty status:** unchanged. The mechanism section can now state the failure precisely, as present in a low-energy direction that is orthogonal to the readout. It cannot claim a causal readout repair.

## 6. Safety reading
- **For defence:** the intervention is inert, and so cannot be one. The only useful practical tool remains the M18 probe *monitor*. It flags 82–100% of the missed equivocations at about 1% held-out false veto, but it needs rule-labelled data and is dominated by the deterministic rule.
- **Side effect:** no false veto in any arm. The operation is safe but useless at these doses.

## 7. Open decisive questions
1. **Whether a high-energy conflict direction steers.** The candidates are the class-mean difference (new minus benign) of the decide states, or a direction fitted for causal effect (e.g. trained against the head gradient), dosed to a fixed fraction of |h|.
   - This would decide between "the feature is usable but the probe direction was the wrong handle" and "the readout cannot use the conflict information at the decision token".
   - It would be one GPU stage of about the M19 size.
   - Its expected information value is moderate: either outcome refines the mechanism sentence, and neither changes the safety level.
2. **Second model:** M18 and M19 on SecJev-0.8B.

## 8. Decision
- **The readout account is DOWNGRADED, as preregistered.**
  - The failure statement stays at decodability (M18) plus orthogonality to the readout (M19 geometry).
  - "Under-weighted readout of a present feature" is **not** claimed causally.
- **No defence claim.**
- **The mechanism line can stop here for the paper, with a precise, bounded failure statement:**
  - present at the decision token (M18);
  - in a low-energy direction orthogonal to the head's reject − accept gradient (M19);
  - not moved by gain along that direction (M19).
- §7.1 is the only remaining experiment that could upgrade the statement. It is optional.
