# A461-MECH-M21 R1: result (can the high-energy conflict direction drive the readout?)

Reported in the order of the [novelty × security-value standard](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §9.

## 1. Experiment and receipt
- **Run:**
  - 6820/6820 kev-4B forwards in 54 batches; 0 denied; one model load; elapsed 10052 s.
  - Raw blob `42cbbb71c365b06072398e38f4abec1b4f5627b4`.
  - Run under prereg bc61ce9, following the user's high-standard request ("按照高标准的来"), with the standing GPU authorization.
  - The pre-model gate passed. There was a single ledger attempt.
- **Files:** the run's `SHA256SUMS` checks clean on all non-capture entries. The local `SHA256SUMS` was rewritten over the 59 fetched files. The captures stay on the server.
- **Analysis:** the frozen `A461_mech_m21_analysis_v1.py` (blob 85da878a) ran automatically and exited 0. **No deviation.**

## 2. Native safety endpoint and Gold
- **Endpoint:** the native `certificate_action` choice and the action margin A = z_reject − max(z_accept, z_wait).
- **Sets (from the in-run replays, as M19):** MISSED 84 (Gold `reject_conflict`, natively not rejected), RECOGNIZED 40, BENIGN 483, native FV 13.
- **Native margin scale (reported, not preregistered):** median A is −0.91 for MISSED (q10–q90: −1.29 to −0.21), +0.34 for RECOGNIZED and −1.03 for BENIGN. A repair needs |dA| of about 0.9.
- **Level:** S1–S2, an intervention on the native action, with false veto built in on four benign arms.

## 3. Main results and failed controls
**Consistency gate: PASS.** All 620 replays are bitwise equal to M18. Every condition has 620 op rows, and the runner checked that every op row reached only the `certificate_action` row.

**Preregistered verdicts:**
- **L19: NOT_READABLE**
- **L31: NOT_READABLE**

| arm | REPAIR (of 84) | FV (of 483) | recognized kept | median dA, missed | max dA, missed | action flips (620) |
|---|---|---|---|---|---|---|
| gain L19 γ8 | 0 | 0 | 1.00 | −0.005 | +0.04 | 0 |
| gain L19 γ32 | 0 | 0 | 0.95 | −0.012 | +0.68 | 3 |
| gain L31 γ8 | 0 | 0 | 1.00 | −0.010 | +0.20 | 0 |
| gain L31 γ32 | 1 (0.012) | 17 (0.035; 5/17 groups) | 0.975 | −0.027 | +1.88 | 20 |
| push L19 β0.05 | 0 | 0 | 1.00 | −0.002 | −0.000 | 0 |
| push L19 β0.2 | 0 | 0 | 1.00 | −0.008 | −0.001 | 0 |
| push L31 β0.05 | 0 | 0 | 1.00 | −0.011 | −0.002 | 0 |
| push L31 β0.2 | 0 | 0 | 1.00 | −0.038 | −0.005 | 0 |
| rand L19 0.2 | 0 | 0 | 1.00 | −0.000 | +0.01 | 0 |
| rand L31 0.2 | 0 | 0 | 1.00 | +0.015 | +0.14 | 1 |

The max-dA and flip columns are reported and were not preregistered. The group-bootstrap CIs are 0 for every arm except gain L31 γ32 (REPAIR [0, 0.035], FV [0.007, 0.062]).

- **Push dose size:**
  - At 20% of |h| along the held-out mean-difference direction, the margin of every missed row moves by at most 0.07, about 8% of the margin a repair needs.
  - It moves **toward accept** in every missed row: the push max dA is negative at both layers.
- **Gain dose size:**
  - γ32 at L31 is the only arm that moves any decision. It flips 1 missed row to reject and 17 benign rows to reject (FV 3.5%, in 5/17 groups).
  - It is therefore a non-selective tail on rows with a large deviation, far below the REPAIR 0.5 bar.
- **Head-input geometry (preregistered report):** the median cosine between the held-out mean-difference direction and each row's exact reject − accept gradient is −0.062 for MISSED, −0.062 for BENIGN and +0.018 for RECOGNIZED. It is near orthogonal and slightly opposed, which matches the sign of the push effect.

**Failed controls:** none. The random-direction push at the same 20% dose moves the margin about as little (missed max dA +0.14 at L31), so the inertness is not specific to the conflict direction.

## 4. Causal level and scope
1. **The readout does not read the conflict direction at the decide token.**
   - Under the interpretation fixed in advance, NOT_READABLE at both layers means that even a push of 20% of |h| along the conflict direction does not move the decision.
   - The direction is near orthogonal to the head's reject − accept gradient, and slightly opposed. This extends M19's orthogonality from the low-energy probe direction to the high-energy class-mean difference.
2. **The failure statement is final at "present at the decide token, not read by the head" (M18 + M19 + M21).**
3. **Scope limits:**
   - The intervention acts on one token, the `<decide>` token. The pinned head also reads the option-token states, which this intervention cannot reach because those tokens come first.
   - A random 20% push is about as inert. So the decide-token residual at L19/L31, at this dose, has little leverage on the action in any direction. "Not read" is therefore a statement about this token and dose, not about the decision's whole input.
   - kev-4B only; SecJev-0.8B is M22.

## 5. Strongest prior art and the novelty delta
- **Prior art:** activation steering along class-mean-difference directions (ActAdd / mean-difference steering, representation engineering) is standard, as is the observation that linearly decodable features need not be causally used.
- **What M21 adds:** a preregistered null with false-veto control, on a safety relation, at a dose calibrated to |h|, together with the head-gradient geometry that explains it.
- **Size of the delta:** small. Its value is that it closes the readout question honestly instead of leaving M19's weak null open.

## 6. Safety reading
- Steering the decide state along the conflict direction is **not a defence**. It does not repair, and at γ32 it adds false veto.
- The only practical tool remains the M18 probe monitor, which needs rule-labelled data and is dominated by the deterministic rule. The model-internal failure is stated as decodable but not used at the decision.
- **Safety value:** S2 characterization (the user's target). There is no new defence and no S3/S4 claim.

## 7. Open decisive questions
- Whether the decision is driven mainly by the option-token states, which is not tested and not needed for the S2 target.
- **Second model:** M22, SecJev-0.8B replication of M18 decodability, the monitor and the natural false veto.

## 8. Decision
- **The readout question is CLOSED as NOT_READABLE** at L19 and L31. The failure statement is final: the conflict is present at the decide token (M18), lies near orthogonal to the head's reject − accept gradient (M19, M21), and neither gain nor a 20% push along it moves the decision.
- **False-veto gap:** 0 for every arm except gain L31 γ32 (FV 3.5% for 1.2% repair).
- **Novelty delta:** small; a preregistered causal null.
- **Next:** M22.
