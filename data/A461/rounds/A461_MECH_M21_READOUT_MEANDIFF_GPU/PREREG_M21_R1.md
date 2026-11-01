# A461-MECH-M21 R1: can the conflict direction drive the readout? (high-energy readout test; preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. This is part of the high-standard plan ("按照高标准的来", 2026-10-31). It runs under the 2026-10-30 grant and the standing GPU authorization (policy V2): 6820 kev-4B forwards in 54 batches (53 × 128 + 36).

**Parent:** [M19](../A461_MECH_M19_READOUT_GAIN_GPU/M19_RESULT_R1.md) (f2256e8).
- **What M19 found:** amplifying the held-out *probe* direction at the `<decide>` token was inert, and that direction is orthogonal to the head's reject − accept gradient.
- **Why that null is weak:** the probe direction carries only about 0.6% (L19) and 0.06% (L31) of |h|.
- **What M21 changes:** it uses the high-energy direction instead. That is the held-out class-mean difference (new minus BENIGN) of the decide-token residual, whose held-out deviation is 4.6% (L19) and 1.0% (L31) of |h|. It also adds input-independent pushes calibrated to |h|.

## Operations
All operations act only at the `<decide>` token of the `certificate_action` row, on the residual output of layer L ∈ {19, 31}.

| family | operation | doses |
|---|---|---|
| gain (input-dependent) | h′ = h + (γ − 1)(h·u − c)u | γ ∈ {8, 32} |
| push (dose-calibrated) | h′ = h + β‖h‖u | β ∈ {0.05, 0.2} |
| rand (control) | h′ = h + 0.2‖h‖v, with v a seeded random unit direction | 0.2 |

- u is fitted on the 16 other source groups.
- c is the training groups' BENIGN mean of h·u.
- There are 620 plain replays, which must be bitwise equal to M18.
- The runner checks that every op row leaves the other question rows bitwise unchanged.

## Rules (coded in the design JSON)
**Sets:** as M19 (MISSED 84, RECOGNIZED 40, BENIGN 483).

**Measures:** REPAIR, FV per benign arm, recognized kept, median dA, and group-level FV with a Clopper–Pearson bound.

**Per-layer verdict:**
- **CAUSAL_SELECTIVE:** some gain γ reaches REPAIR ≥ 0.5 with FV ≤ 0.05 on every benign arm.
- **CAUSAL_PUSH_ONLY:** no gain arm qualifies, but some push β reaches REPAIR ≥ 0.5 with REPAIR − FV_max ≥ 0.30, and rand reaches REPAIR ≤ REPAIR(push 0.2) − 0.30.
- **NOT_READABLE:** every gain and push arm has REPAIR < 0.5.
- **NONSELECTIVE:** otherwise.

**Geometry (reported):** the cosine between the held-out mean-difference direction in head-input space and each row's exact reject − accept gradient.

## Research contract ([standard V1](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §2–§5)
**Level:** S1–S2. This is an intervention on the native action. False veto is built in: four benign arms, including the near misses.

**What it decides:**
- **CAUSAL_SELECTIVE:**
  - the paper states the failure as an under-weighted readout of a present feature, shown causally;
  - this closes the readout question.
- **CAUSAL_PUSH_ONLY:**
  - the readout can be driven along the conflict direction, but not selectively by a row's own conflict signal;
  - the failure is stated as "a weak per-row signal along a readable direction".
- **NOT_READABLE:**
  - even a 20% push along the conflict direction does not move the decision;
  - the readout does not read this direction at all, consistent with the M19 orthogonality;
  - the failure statement is final at "present at the decide token, not read by the head".

**Novelty delta:** small. Steering along mean-difference directions is standard. The value lies in turning the failure statement into a causal one, with a false-veto control.

**What it cannot show:** a natural-path fix, a defence (the direction needs rule-labelled data), or generality beyond kev-4B (M22).

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m21_freeze_v1.py` (CPU, torch on the M18 features; mean-difference directions per held-out group) |
| manifest blob | `e559fc17f1adcd1a73919cebfe5c3c0bc6b6e1c4` (6820 rows) |
| design blob | `eff089949d542f828e29a1675dfdb126b62d78f0` |
| directions file | `m21_directions.pt` (sha256 `4dba9d6b…`; 34 mean-difference + 1240 random directions) |
| runner blob | `f190e5989989fee965a16d2269569bb8b2a22163`. It is the M19 runner 9c0a3108 with a `push` op kind added (h + β‖h‖u), and with names, plan and pins changed. The gain op, gates and other-rows check are unchanged |
| self-test | `A461_mech_m21_selftest_v1.py` (blob `7e14517c`); result below |
| analysis | `A461_mech_m21_analysis_v1.py` (blob `85da878a`), written before the run |

## Self-test
**R1 (`M21_SELFTEST_R1/`, 2026-11-01 01:07 +08): 13/13 PASS**, with zero GPU loads. It covers:
- preflight on the real 6820-row manifest;
- the fake full path, using a synthetic 64-wide directions file: 6820 rows and 620 replay captures;
- the decide capture reproduces the fake head's logits exactly;
- **the op rows of both kinds:**
  - gain rows record dev = proj − c and |Δ| = (γ − 1)|dev|;
  - push rows record dev = |h| and |Δ| = β|h|;
  - all 6200 op rows moved the `certificate_action` logits while the other rows stayed unchanged;
- refusals: a held-out leak, tampered directions, an extra LM call, approval reuse, and the GPU admission gates.

The analysis dry run exits 0 with INCONSISTENT, as it must.
