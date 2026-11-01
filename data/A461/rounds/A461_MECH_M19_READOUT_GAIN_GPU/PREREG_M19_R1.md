# A461-MECH-M19 R1: is the encoded conflict usable by the readout? (readout-gain test; preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Requested by the user on 2026-10-31 ("Yes, readout test") after M18. Run under the 2026-10-30 grant and the standing GPU authorization (policy V2): 5580 kev-4B forwards in 44 batches (43 × 128 + 76).

**Parent:** [M18](../A461_MON_M18_SPAN_MONITOR_GPU/M18_RESULT_R1.md) (c56729c).
- In the 84 scenes where kev-4B accepts a lawful equivocation, a held-out linear probe decodes the conflict at the decision position of the `certificate_action` row. AUROC is 0.999 after layer 19 and 0.990 after layer 31, the layer that feeds the head.
- **Decodability is not use.** M19 tests use.

## Question
Is the conflict feature that is already present in the missed scenes causally usable by the pointer head? Concretely: if the model's own deviation along that feature is amplified, only at the decision token, do the missed equivocations flip to `reject_conflict`? And does that happen while benign rows stay, and not along a random direction?

## Operation and arms
**The operation:**
- It acts on the residual output of decoder layer L ∈ {19, 31}, only at the `<decide>` token of the `certificate_action` row. Every other row and position is untouched, and the runner checks that the other question rows' logits equal the replay's bitwise.
- h′ = h + (γ − 1)·(h·u − c)·u, where:
  - u is the M18 probe direction for that layer, fit on the 16 other source groups (held out, as in M18);
  - c is those groups' benign mean of h·u.
- The operation is input-dependent: a row at the benign mean is unchanged, and a row carrying the conflict feature is pushed further along it.

**Arms (per M18 row, 620 rows):**
- a plain replay, which must equal M18 bitwise and saves the post-norm `<decide>` and option states;
- PROBE at L19 and L31 × γ 2 / 4 / 8;
- RANDOM, a unit direction seeded per row with its own benign centre, at L19 and L31 × γ 8.

**Sets, defined from the replay's native action:**
- MISSED: 84;
- RECOGNIZED: 40;
- BENIGN: old / SA / ROUND / OUTSIDER rows that are not rejected (483);
- NATIVE_FV: the 13 near misses already rejected.

## Rules (coded in the design JSON)
**Measures:**
- **REPAIR:** the share of MISSED rows that become `reject_conflict`.
- **FV:** the share of BENIGN rows that become `reject_conflict`, overall and per arm.
- Group-level false-veto counts, with a Clopper–Pearson bound.
- Group-bootstrap CIs.

**Per-layer verdicts:**
- **READOUT_GAIN_REPAIRS:** some PROBE γ reaches REPAIR ≥ 0.5 with FV ≤ 0.05 on every benign arm, and RANDOM at γ 8 reaches REPAIR ≤ 0.10.
- **READOUT_GAIN_NONSELECTIVE:** REPAIR ≥ 0.5 is reached, but only together with FV > 0.05.
- **READOUT_GAIN_INERT:** REPAIR < 0.5 at every γ.
- **RANDOM_ALSO_REPAIRS** is appended when RANDOM γ 8 gives REPAIR > 0.10.

**Readout geometry (reported):**
- From the replay captures and the pinned head weights (`head.pt`): the cosine between each row's exact gradient of z_reject − z_accept with respect to the `<decide>` state, and a held-out probe direction fit on the head-input states themselves.
- This stays in head-input space, so it needs no final-norm convention.

**Consistency gate:**
- 620 replays bitwise equal to M18;
- every op row reaches only the `certificate_action` row (runner);
- the op conditions are as planned.
- Otherwise every verdict is INCONSISTENT.

## Research contract ([standard V1](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §2–§5)
**Level:** S1–S2. This is an artificial intervention scored on the native action against source-internal Gold.

**What it can show:** whether the readout can use a feature the model already computes. That is the causal half of H-READ, and it sits at the readout.

**What it cannot show:**
- A natural mechanism of the miss. The operation amplifies, it does not ablate.
- A defence. The operation needs the held-out probe, which needs rule-labelled data, and the rule has 0 errors.
- Anything beyond kev-4B and twins_streamlet.

**False-veto control:** built in. All four benign arms are scored under the same operation, with the near misses (ROUND, OUTSIDER) where M17 found the L11 verdict and the action come apart.

**Novelty delta:**
- **Expected and known:** steering along probe directions changes behaviour; that alone is not new.
- **What is at issue:**
  - whether an *input-dependent* gain on the model's own conflict feature, at the decision token only, corrects this safety error without false veto;
  - whether the head's readout direction is near-orthogonal to that feature (the geometry).
- Together these give the mechanism statement for the paper: a present but under-weighted feature.

**What the result decides:**
- **REPAIRS at L31:** the paper states the failure as an under-weighted readout of a present conflict feature, shown causally at the head input. The natural-path work stops there, and the stage list moves to the paper package.
- **NONSELECTIVE or INERT:** the failure statement stays at decodability (M18), and the readout account is DOWNGRADED to "present but not usable along the probe direction".

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m19_freeze_v1.py` (CPU, torch on the M18 features; directions fit per held-out group with the M18 probe spec; deterministic: a re-freeze reproduced manifest, design and directions byte-for-byte) |
| manifest blob | `080bc5741bfc676f6d0f2b5dbc613652a6a9ddd4` (5580 rows) |
| design blob | `b36e10a9ed0a67e056e14130cee35e90caa0456c` |
| directions file | `m19_directions.pt` (sha256 `974137d1…`; 34 probe + 1240 random directions) |
| runner blob | `9c0a3108308510c7bc1a18807d8bd234d032758e`. Built from the M18 runner: gate, ledger, admission, model load, batch loop and state rebuild are kept; pins, manifest checks, the op and capture hooks and the per-forward body are new |
| self-test | `A461_mech_m19_selftest_v1.py` (blob `c00ef079`); result below |
| analysis | `A461_mech_m19_analysis_v1.py` (blob `1f8ceeee`), written before the run |
| inputs | M18 design `1998024b`, M18 raw `10e04cfa`, M18 feature files (server), kev-4B `head.pt` |

## Self-test
- **R1 (`M19_SELFTEST_R1/`, 2026-10-31 20:56 +08): 13/13 PASS**, with zero GPU loads. It covers:
  - preflight on the real 5580-row manifest;
  - the fake full path: 5580 rows, 620 replay captures, sha verified;
  - **the replay's decide state times the fake head reproduces the `certificate_action` logits exactly**;
  - **every one of the 4960 op rows records dev = proj − c and |Δ| = (γ − 1)|dev|** (the frozen amplification). Each moved the `certificate_action` logits while the other rows stayed unchanged (runner-enforced);
  - a probe direction of another source group (a held-out leak) is refused;
  - a tampered directions file is refused;
  - an extra LM call, approval reuse and the GPU admission gates are refused or gated as required.

  The analysis dry run exits 0 with every verdict INCONSISTENT, as it must.
- **R0 (`M19_SELFTEST_R0_FAILED_FAKE_WIDTH/`): FAILED 9/13. Kept.**
  - **The defect was in the self-test spec:** the fake model is 64 wide, and the fake full path was given the real 2560-wide frozen directions, so it stopped at the first op row.
  - **Fix:**
    - The self-test now builds a synthetic 64-wide directions file under the frozen keys and a design copy carrying its sha. The runner accepts a non-pinned design on the fake backend only, and the GPU tests use the real files.
    - The runner gained an explicit fail-closed check, `direction width != hidden`, in place of a raw tensor error. The op math is unchanged.
  - The runner blob changed from `2ccff200` to `9c0a3108`.
