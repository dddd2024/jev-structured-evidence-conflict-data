# A461-MECH-M16 R1: is M14's lower AB threshold the linear readout of the common shift at the middle span positions? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Designed at the user's request ("Design M16", 2026-10-31) and run under the 2026-10-30 grant and the standing GPU authorization (policy V2). 2992 kev-4B forwards in 24 batches (23 × 128 + 48).

**Parent:** M15 R1 (0e3339a).
- **What M15 found:** the AB shift lowers SMIN against the all-position shift whether or not c₃₀ is kept (Q1_GAIN_LOC_ONLY). Yet its C is lower at every s on all three responsive hosts.
- **The only difference:** with c at 29, the two arms differ only in the common shift at span positions 13–28 (the KIND, RECV and RKEY lines). That is the same tensor for the main and the round source.
- **Exploratory reading of M14 and M15 rows (not a verdict):**
  - Removing that shift lowers A for both sources (main by about 0.11, round by 0.03–0.08 on 264c458d).
  - The main source keeps headroom, so the round source drops below A = 0 first.
  - A per-cell common offset reproduces AB's S on 264c458d and 4bcbaf15, but not on 1fb5651c at s ¼.

## Questions
1. **Linearity.** With w the weight of the common shift at 13–28, do each cell's M and A move linearly in w? Concretely, do per-cell predictions from the w = 0 (M14) and w = 1 (M15) rows reproduce JOINT decisions and host S at w = −1, −½, ½, 3/2?
2. **S against C.** Within a host, does lowering w raise S while lowering C?

## Research contract: safety value, novelty delta and decision ([standard V1](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §2–§5)
- **Safety endpoint and evidence level:**
  - The endpoint is the native typed `certificate_action` (reject_conflict vs accept / wait) jointly with the conflict margin, scored against the source-internal executable rule Gold. That is level **S1–S2**.
  - Every M16 effect is an artificial activation intervention on host new. M16 therefore says nothing about the natural error path (S3) and nothing about deployment (S4).
- **Which standard clause it addresses:** M16 tests the §3.6 caution directly. When a common shift repairs errors, first check whether it only pushes the host over the decision threshold.
- **No false-veto measurement:** every target is the conflicting host new, so M16 does not measure false veto. The round source controls for the source (a non-conflicting donor gives no repair). It does not test whether the patch makes benign hosts reject.
- **Novelty delta:** small and methodological. At issue is whether the M14 / M15 location result (author / block lines) is a contrast-carrying site or a threshold readout of a linear common offset. Either outcome fixes how the mechanism section of the paper may describe M14–M15. Neither adds a new safety-relevant mechanism.
- **What the result decides:**
  - **W_LINEAR HOLDS:** DOWNGRADE M14's AB-threshold reading to a readout-threshold effect. Stop deepening the position line, and move to consolidation and to the open safety controls (false veto on benign hosts, the 5 non-responsive hosts).
  - **FAILS:** the middle shift interacts with the contrast. Keep the location reading as CONDITIONAL, and design at most one stage that separates the interaction.
- **What it cannot show:** a natural mechanism, a necessity claim, a defence benefit, or any effect outside kev-4B and the twins_streamlet DEV simulator.

## Arms (all patch the L11 `o_proj` input at the 31 span positions of host new in every question row; sources donor new = main, donor ROUND = round; pools, mid and c as in M8–M15; common shift t = 1; contrast ∓ s/2 c with c₃₀ weight 0)
| arm | patch | role |
|---|---|---|
| `full`, `meanD_host` | M3 all-heads patch / M6 pooled-donor arm, all 208 rows | bitwise anchors (S 51 / 39) |
| `abc_s0375`, `csc29_s0375` | M14's AB arm and M15's all-position c-29 arm, same patch fields, on the 6 subset cells | bitwise replays (w = 0 and w = 1 at s ⅜) |
| `mw0_s0375` | new field `shift_pos_weight`, weight 0 at 13–28, on the 6 subset cells | must equal `abc_s0375` bitwise: the GPU check of the new code path |
| `mw{m1,m05,p05,p15}_s{025,0375,05}` | common shift × w at 13–28 (× 1 elsewhere), w = −1, −½, ½, 3/2; s = ¼, ⅜, ½ | the w dose (12 arms × 208 rows) |

w = 0 and w = 1 at every s come from the pinned M14 `abc_<s>` and M15 `csc29_<s>` rows.

**The new runner field.**
- **Construction:** `shift_pos_weight` builds the patch with the same mask-times-shift expression as `shift_positions`; only the mask values differ.
- **Self-test:** weights 0 / 1 reproduce the AB and the all-position shifts bitwise.
- **Exclusivity:** the field cannot be combined with `t`, `shift_positions`, `shift_scale` or `shift_rescale`. The self-test checks that the manifest check refuses such a row.

## Linear predictions, frozen in the design before the run (host S)
| arm | 1fb5651c | 264c458d | 4bcbaf15 |
|---|---|---|---|
| s ¼: w −1 / −½ / ½ / 3/2 | 0 / 0 / 13 / 13 | 10 / 2 / 0 / 0 | 2 / 12 / 7 / 0 |
| s ⅜: w −1 / −½ / ½ / 3/2 | 0 / 0 / 13 / 13 | 13 / 12 / 1 / 0 | 2 / 13 / 13 / 12 |
| s ½: w −1 / −½ / ½ / 3/2 | 0 / 0 / 13 / 13 | 13 / 13 / 13 / 12 | 2 / 12 / 13 / 13 |
| observed endpoints, s ¼ / ⅜ / ½, at w = 0 (M14) | 5 / 13 / 13 | 0 / 10 / 13 | 11 / 13 / 13 |
| observed endpoints, s ¼ / ⅜ / ½, at w = 1 (M15) | 13 / 13 / 13 | 0 / 0 / 12 | 0 / 13 / 13 |

The per-cell, per-source predicted M and A are under `linear_predictions` in the design.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m16_freeze_v1.py` (CPU + tokenizer only), derived from the M15 freeze by checked edits. It cross-checks the M3–M15 key classes and pools, the span width and field layout, that the 4 replay arms' patch fields equal the M15 rows' fields, that `mw0_s0375` equals `abc_s0375` with its 0/1 mask written as weights, that the subset cells are M14's and M15's, the rows per arm, and that the endpoint rows have the same contrast sign and size as each dose row |
| manifest blob | `5b2de6f48a041e1ca9726179f876489fcb837410` |
| design blob | `c061686a5a3271e2b06f418f213bce81fa3ff05a`: the rules are under `preregistered_analysis`, the predictions under `linear_predictions` |
| runner blob | `2886a05c6852ee4d65871c069cbb9c642a14cbab`: the M15 runner 8632c3a1 with the plan, pins and names changed and the `shift_pos_weight` field added (validation, code path, logged key) |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m16_selftest_v1.py` (blob `27137ba02ef3c915a603ccf083dad73e7d2c9c6e`; 24 CPU threads): **17/17 PASS** on the server (2026-10-31 12:28 +08), zero GPU loads; analysis dry run on fake logits exits 0 with every verdict INCONSISTENT_WITH_M3_M6_M14_M15, as it must (`M16_SELFTEST_R1/`). **First run (blob f3452889) FAILED 16/17, kept in `M16_SELFTEST_R1_FAILED_TESTBUG/`:** the identity test also required the w = 1/2 arm to equal cs1 within 1e-4. It differs by 4.1e-3, as a half-weighted shift must, so that requirement was a test-specification error. Every bitwise identity in that run held, including weight 0 = the AB shift and weight 1 = the all-position shift. The fix drops that tolerance check and adds that w = 1/2 differs from both endpoints. Runner, manifest and design are unchanged |
| analysis | `A461_mech_m16_analysis_v1.py` (blob `7950fce050df84ca498ee255a3829fb890bdb900`), written before the run |
| inputs | as M15, plus M15 design `4288440c` and M15 raw `b6807b13` |

## Rules (coded in the design JSON)
- **S, SPEC, SUF and C:** as in M2–M15. The responsive hosts are 1fb5651c, 264c458d and 4bcbaf15 (S(cs1) > half their cells in M13).
- **Consistency gate:** all of the following must hold, otherwise every verdict is INCONSISTENT_WITH_M3_M6_M14_M15.
  - S(full) = 51, with its 208 rows bitwise equal to M3.
  - S(meanD_host) = 39, with its 208 rows bitwise equal to M6.
  - `abc_s0375` and `csc29_s0375`: 12/12 rows each bitwise equal to M15, and `abc_s0375` also 12/12 to M14.
  - `mw0_s0375`: 12/12 rows bitwise equal to `abc_s0375`.
  - Every dose row records its planned shift weights.
- **Linearity:**
  - **Prediction:** for each dose arm, cell and source, M_pred, A_pred = (1 − w) × (w = 0 row) + w × (w = 1 row). JOINT_pred is M_pred > 0 and A_pred > 0.
  - **Measures per responsive host:** AGREE = the share of the 312 (cell, source, s, w) JOINT decisions where observed = predicted; dS = S_obs − S_pred.
  - **LIN_BY_HOST:**
    - LINEAR_HOLDS iff AGREE ≥ 0.95 and max |dS| ≤ 1.
    - LINEAR_FAILS iff AGREE < 0.90 or max |dS| ≥ 3.
    - Otherwise LINEAR_APPROX.
  - **Pooled W_LINEAR:** HOLDS iff every host holds; FAILS iff any fails; otherwise APPROX.
  - **Reported but not verdicts:** interpolation (w = ½) and extrapolation separately; R² and median |error| of M and A.
- **w trends:** per host and s, over the six w in increasing order, for S (WS_) and C (WC_):
  - NO_EFFECT iff all six values are equal.
  - OPPOSES iff non-increasing with first > last.
  - SUPPORTS iff non-decreasing with first < last.
  - PEAKED iff rising to the first maximum, then falling, with both ends below the maximum.
  - Otherwise MIXED.
- **DISSOC_BY_HOST,** over the s where WS is not NO_EFFECT:
  - S_C_DISSOCIATE iff WC = SUPPORTS and WS is OPPOSES or PEAKED at every such s.
  - S_C_ALIGNED iff WS = WC is SUPPORTS or OPPOSES at every such s.
  - UNINFORMATIVE iff there is no such s.
  - Otherwise S_C_MIXED.
- **Always reported:**
  - per arm: S, SPEC, J and C;
  - per host: S and C;
  - observed and predicted attribution per host, s and w (main JOINT, round JOINT among main-JOINT cells, round A > 0 and M > 0, medians);
  - leave one donor group out for every verdict;
  - change norms relative to full.

## Interpretation fixed in advance
- **W_LINEAR HOLDS:** within w ∈ [−1, 3/2], each cell's M and A move linearly in the weight of the middle common shift. The AB / all-position difference in S, and with it M14's lower AB threshold, is then the threshold readout of a linear per-cell, per-source effect of that shift. It is not evidence of a contrast component carried by the author and block lines.
- **FAILS:** the middle shift interacts non-linearly with the rest of the patch.
- **S_C_DISSOCIATE on a host:** S at a fixed s ranks arms opposite to the contrast they carry, so S thresholds should not be read as contrast strength there.
- **Limits:**
  - All arms except `full` are pooled-donor arms (effectively 8 host replicates, 3 responding), so per-host S is the honest unit.
  - The predictions and the w = 0 / 1 points come from M14 and M15 rows. Using them is valid because the replays are bitwise equal.
  - One model (kev-4B) and one simulator family.
