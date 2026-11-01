# A461-MON-M23 R1: do the M18 / M22 probes track conflict validity or the arm? (same-span twin test; preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. This answers paper audit `02a2b73` P0-1. The user chose "Run M23" on
2026-11-01. It runs under the standing GPU authorization (policy V2) as two runs:

- kev-4B: 248 forwards, batches [128, 120];
- SecJev-0.8B: 248 forwards, batches [128, 120].

## The confound
- In M18 (kev-4B) and M22 (SecJev), every positive probe row is a `new` row and every negative row is a non-`new` row.
- Arm, Gold, message form and role therefore vary together.
- A probe that separates missed `new` rows from benign rows may read the appended item's form or arm rather than whether
  the vote is a conflict in its context.

## The twin
- G2.3 (`../A461_MON_G23_CONTEXT_COUNTERFACTUAL_CPU/G23_RESULT_V1.md`) built a PARTNER_ROUND twin for each of the 124
  scenes:
  - the state and the appended `new` vote are kept unchanged;
  - only the appended author's earlier vote for the candidate block in the candidate round is moved to the nearest
    non-candidate round.
- The appended span is **byte-identical and at the same position**. Exactly one token differs, and it comes before the
  span.
- Gold becomes accept (102) or wait (22), never `reject_conflict`, and both oracles agree.
- The twin has the same arm and form as `new`, but no conflict.

## Rows (per model)
- **124 `new` replays.** Each is the parent's `new` row with its Stage-A anchor. It must replay bitwise, as in the parent
  runner.
- **124 `TWIN` rows.** The runner checks the partner edit field by field against the corpus state and requires the
  frozen token sha.
- The read-only captures are those of M18 / M22: the L11 attention write over the span, span-mean residuals, and the
  decision-position residuals.

## Analysis (`A461_mon_m23_analysis_v1.py`, frozen here)

**Probe refit.** The parent's probes are refit exactly as the parent analysis did:
- same features, probe spec and labels;
- leave one source group out;
- inner leave-one-group-out FV5 / FV1 thresholds on the training groups' benign rows.

Each held-out group's M23 `new` and `TWIN` rows are then scored.

**Consistency gate** (otherwise every verdict is INCONSISTENT):
- 248 rows;
- the `new` rows' logits and capture tensors equal the parent's bitwise;
- every TWIN's emb-layer span mean equals its `new` row's;
- the refit reproduces the parent's held-out AUROC for both primary detectors.

**Unit.** The MISSED scenes, where the parent's native action on `new` is not `reject_conflict`: kev-4B 84, SecJev 110.

**Primary detectors.**
- `PROBE:SPAN_ATTN11`, the preregistered monitor;
- `PROBE:LAST_RESID_<last layer>`, the state the decision head reads: L31 for kev-4B, L23 for SecJev.

**Reported detectors.**
- the L11 span residual;
- the parent's best generic detector;
- the surface (embedding) probe.

**Measures.** AUROC_pair (new-missed vs their twins), twin_flag and new_flag at FV5 / FV1, the share of scenes with
score(new) > score(TWIN), and AUROC(TWIN vs the parent's benign rows). There is a group bootstrap with 2000 draws.

| verdict (per detector) | rule |
|---|---|
| **VALIDITY_TRACKED** | AUROC_pair ≥ 0.80, its CI lower bound ≥ 0.65, and twin_flag@FV5 ≤ 0.25 |
| **ARM_SHORTCUT** | AUROC_pair ≤ 0.65, or twin_flag@FV5 ≥ 0.50 |
| **PARTIAL** | otherwise |

**Interpretation, fixed in advance.**
- **VALIDITY_TRACKED on both primary detectors.** Claim M-E may say that the separability tracks conflict validity in
  context, not only the arm: same span, one context token, Gold flipped.
- **ARM_SHORTCUT.** M-E stays narrowed. The paper says that the appended item's form or arm explains the separability,
  and the "represented but not used" candidate loses its main support.
- **PARTIAL or mixed.** Reported as it is. M-E stays narrowed, with the partial result stated.

**Native behaviour (reported).** The models' actions on the twins. A `reject_conflict` on a twin is a false veto driven
by the appended item's form.

## Research contract
- **Level:** S1–S2. This is read-only capture plus held-out probes, and the false-veto side is reported.
- **What it cannot show:** that the model *uses* the feature (M19 and M21 remain decision-token nulls); any
  generalization beyond these 124 scenes.
- **Novelty delta:** small. Its value is removing the arm confound that the audit found.

## Pins
| item | value |
|---|---|
| freeze | `A461_mon_m23_freeze_v1.py`; outputs in `M23_FREEZE_R1/` |
| kev-4B manifest / design blobs | `003faaffa6359c895f72972f8d8802d21b645b12` / `3a38de9b0e98f94bdb0678002462cc4c36de2fb6` |
| SecJev manifest / design blobs | `ebe6979dba4b0e719bda66b7c849bec95553a170` / `480ca62c1e88ffa3fdd7348e557692c515415390` |
| runners | `A461_mon_m23k_runner_v1.py` and `A461_mon_m23s_runner_v1.py`, derived from M18 / M22 by `A461_mon_m23_derive_v1.py` (the hooks, gate, ledger, model load and per-forward body are unchanged); blobs `63308265` (kev-4B), `a8955fe3` (SecJev) |
| self-tests | `A461_mon_m23k_selftest_v1.py`, `A461_mon_m23s_selftest_v1.py`; result below |
| analysis | `A461_mon_m23_analysis_v1.py` (blob `128ee26a`) |

## Self-test
**R1 (2026-11-01 14:08 +08): kev-4B 13/13 PASS and SecJev 13/13 PASS, with zero GPU loads** (`M23K_SELFTEST_R1/`,
`M23S_SELFTEST_R1/`). The tests cover:
- preflight on the real 248-row manifests (token and span gates);
- the fake full path: 248 rows, 248 feature files, arms {new: 124, TWIN: 124};
- the decision position is the one the head reads;
- the emb-layer span mean of `new` equals TWIN's in 124/124 scenes, while the full token sequences differ in 124/124;
- refusals: tampered manifest (caught at the TWIN token gate), tampered Stage-A raw, an extra LM call, approval reuse,
  and the GPU admission gates.

**Analysis dry run on fake data.** The fake M18 / M22 self-test outputs serve as the parents. Both runs exit 0.
- kev-4B's fake data reaches verdicts.
- SecJev's fake head rejects every row, so the gate fails and every verdict is INCONSISTENT, as it must be.
