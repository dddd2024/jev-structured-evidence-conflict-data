# A461-MECH-M11 R1: is the position-29 effect of the pooled round contrast more than its size, is the shift needed at the context positions or only more shift, and does the subspace split hold per host? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 5244 kev-4B forwards in 41 batches (40 × 128 + 124).

**Parent:** M10 R1 (c4c4aeb). The pooled contrast c = mean_D B(ROUND) − mean_D B(new) sits only at span positions 29 and 30.
- **CONTRAST_AT_P29:** cpos29 S 39, cpos30 S 3. Not size-matched: position 29 holds 89 % of c's energy. The A573 CPU audit shows that a pure amplitude threshold reproduces this verdict.
- **SHIFT_NEEDS_ALL_POSITIONS:** sh2930 J 0 / 0, sh0_28 S 13 (host 1fb5651c only). Also not size-matched: the shift at 29–30 is 5 % of the shift's change norm.
- **SPLIT_NULL5 fails:** S 7 / 11 / 4 / 7 / 4; 27 of the 33 null repairs are on host 1fb5651c. On host 264c458d the null is 0 in all 5 seeds, cperp 13, cpar 1.

## Questions
1. **Position at matched size.** If c is kept only at position 30 and rescaled to the norm c has at 29, does it repair? And c at 29 rescaled down to c's norm at 30? Plus a dose on each position.
2. **Shift location at matched size.** If the common shift is applied only at 29–30, but rescaled to the total norm (or the per-token norm) of the shift at 0–28, does it repair? Plus a dose on the shift at 29–30.
3. **Split per host.** On each responsive host, does the part of c outside (or inside) the 16-dim common subspace repair more cells than any of 10 contrast-sized random frames?

## Arms (all patch the L11 `o_proj` input at the 31 span positions of host new in every question row; sources donor new = main, donor ROUND = round; Pool_D, mid and c as in M8–M10; common shift t = 1; contrast ∓ s/2 c)
| arm | patch | role |
|---|---|---|
| `full` | the M3 all-heads patch | bitwise anchor (S 51) |
| `meanD_host` | as M6 | bitwise anchor (S 39) |
| `cs1`, `chR_sm`, `cpar16_sm`, `cperp16_sm`, `cpos29`, `cpos30`, `sh2930`, `sh0_28` | the M10 arms with identical patch fields | bitwise anchors (S 39 / 0 / 27 / 39 / 39 / 3 / 0 / 13) |
| **`cpos29_n30`** / **`cpos30_n29`** | cs1 with c kept only at 29 / 30, rescaled per row to the norm of c at 30 / 29 (cap 10) | Q1 |
| `cpos29_s025`, `cpos29_s05` / `cpos30_s2`, `cpos30_s4` | c kept only at 29 with s = ¼, ½ / only at 30 with s = 2, 4 | Q1 dose |
| **`sh2930_tm`** / **`sh2930_pt`** | the shift only at 29–30, rescaled per row to the total norm / the per-token norm of the shift at 0–28 (cap 10), plus the full c | Q2 |
| `sh2930_u2`, `sh2930_u4` | the shift only at 29–30 times 2 / 4, plus the full c | Q2 dose |
| `crand16_sm_s5` … `_s9` | as M10's crand16_sm frames, seeds 5–9 of the M10 family (`A461_M10_CRAND\|16\|d\|h\|i`) | Q3 null (with M10's 5 frames from the pinned M10 raw) |

- The swapped-norm factors are ‖c₂₉‖ / ‖c₃₀‖ (cpos30_n29) and its inverse (cpos29_n30). In the M9–M10 captures this ratio is about 1.75–3.5, below the cap.
- The per-token shift factor is (‖d₀₋₂₈‖ / √29) / (‖d₂₉,₃₀‖ / √2); the total factor is ‖d₀₋₂₈‖ / ‖d₂₉,₃₀‖, where d = mid − h_B.
- There is no `chR_sm` sign-flip arm. For a target-based contrast shift, flipping the sign only swaps the main and round patches, so it would relabel M10's chR_sm rows and add nothing.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m11_freeze_v1.py` (blob `54da0828d40d275826965209c047fee4e2f1c53b`; CPU + tokenizer only), derived from the M10 freeze by checked substitutions. It cross-checks the M3–M10 key classes and pools, the span width (31), that the 10 replay arms' patch fields equal the M10 rows' fields, and that the 5 random frames per row are distinct and disjoint from M10's |
| manifest blob | `8e5762826973d49d2efd3f187f94c5c913f9b0c1` |
| design blob | `53d2bc8d89098c8e3434be9f11851bc459e1389a`: the rules are under `preregistered_analysis` |
| runner blob | `54479b0480666fde9e2681346e8e46d384236610`, derived from the M10 runner 7f2577cc by checked substitutions. It adds `contrast_pos_norm_from`, `shift_rescale` (`complement_total` / `complement_token`) and `shift_scale`, each with a fail-closed size gate at 1e-3 relative where not capped. The M10 arms run the M10 code unchanged |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m11_selftest_v1.py` (blob `d46db5dfd2d1c3ed345ce436e8ed67eee317e815`): PASS 16/16 on the fake model with no GPU (`M11_SELFTEST_R1/`): wiring of the 25 arms (21 distinct in 208/208; the tiny cpos30-family arms exempt), the position and part shares, the size gate on 2912 rescaled rows (max rel err 5.1e-08; contrast factor max 10.0, cap reached only by cpos30_n29 on fake weights; shift factor max 4.40), the identities with cs1 and the factor-1 rescaled shift equal to the plain shift (bitwise), the ROUND sources, and the admission refusals. The analysis dry run on the fake raw exits 0 |
| analysis | `A461_mech_m11_analysis_v1.py` (blob `31dbc6fcdf4e14ef45bd7457802e3a8b3d26fbbd`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, M6 design `43967513`, M6 raw `2147311c`, M7 design `f7d5318c`, M7 raw `0383fccf`, M8 design `14cee4c2`, M8 raw `997c9b71`, M9 design `fe91481e`, M9 raw `c74e5117`, M10 design `f127d850`, M10 raw `755c74e1`, G1.0 counterfactuals `06ee06d7` |

## Rules (coded in the design JSON)
- **S, SPEC, SUF and C:** as in M2–M10. SUF = S ≥ ½ S(full) and SPEC.
- **Consistency gate:**
  - S(full) = 51, and its 208 rows equal M3 bitwise;
  - S(meanD_host) = 39, and its rows equal M6 bitwise;
  - the 8 M10 arms each have 208 rows equal to M10 bitwise, with S = 39 / 0 / 27 / 39 / 39 / 3 / 0 / 13.
  - Otherwise every verdict is INCONSISTENT_WITH_M3_M6_M10.
- **Q1 position at swapped norm:**
  - POSITION29_SPECIFIC iff SUF(cpos29_n30) and not SUF(cpos30_n29);
  - AMPLITUDE_DRIVEN iff the reverse;
  - BOTH_POSITIONS_ACT_AT_SWAPPED_NORM iff both;
  - P30_INERT_AT_P29_NORM iff neither.
  - **AMPLITUDE_ONLY_EXCLUDED** iff not SUF(cpos30_n29).
  - Dose: POS29_SMIN = the smallest s ∈ {¼, ½, 1} with SUF; POS30_SMIN = the smallest s ∈ {1, 2, 4} with SUF; NONE otherwise.
- **Q2 shift at matched size:**
  - SHIFT_LOCAL_AT_TOTAL_NORM iff SUF(sh2930_tm) and not SUF(sh2930_pt);
  - SHIFT_LOCAL_AT_TOKEN_NORM iff the reverse;
  - SHIFT_LOCAL_SUFFICES iff both;
  - SHIFT_NEEDS_CONTEXT_POSITIONS iff neither.
  - Dose: SHIFT2930_UMIN = the smallest u ∈ {1, 2, 4} with SUF.
- **Q3 split by host:**
  - A host is responsive if S(cs1) on its cells exceeds half its cells.
  - Per responsive host, null_max is the largest S over the 10 random frames.
  - OUTSIDE iff S(cperp16_sm) > null_max and S(cpar16_sm) ≤ null_max; INSIDE iff the reverse; BOTH; NEITHER.
  - The verdict is SPLIT_BY_HOST:<host8>=<v>,….
  - Also reported: SPLIT_NULL10 (median pooled S over the 10 frames ≤ 5, none SPEC) and the pooled subspace verdict, re-applied with `_UNRESOLVED` iff SPLIT_NULL10 fails.
- **Always reported:**
  - per-host S;
  - leave-one-donor-group-out of every verdict;
  - energy shares, factors and capped shares;
  - the shift norm ratios (total and per-token);
  - each random frame's S, pooled and per host;
  - change norms relative to full.

## Interpretation fixed in advance
- **A pure amplitude threshold** (A573) predicts SUF(cpos30_n29). **AMPLITUDE_ONLY_EXCLUDED:** c at 30, given the size c has at 29, does not act, so the M10 P29 effect is not size alone. This separates position and direction together from size, not position from direction, since c's direction at 30 differs from that at 29. **AMPLITUDE_DRIVEN:** the M10 P29 verdict reflects size.
- **SHIFT_LOCAL_AT_TOTAL_NORM:** with the same total shift norm, the shift at 29–30 alone suffices, so M10's SHIFT_NEEDS_ALL_POSITIONS was an amount effect. **SHIFT_NEEDS_CONTEXT_POSITIONS:** even the norm-matched local shift fails, so the shift must reach the context positions.
- **SPLIT_BY_HOST:** per responsive host, whether the part of c outside (or inside) the 16-dim common subspace repairs more cells than any of 10 contrast-sized random frames.
- **Limits:**
  - All M11 arms except `full` are pooled-donor arms, effectively 8 host replicates (3 responded in M9–M10). Per-host S is the honest unit.
  - The total-norm shift (factor ≈ √(29/2) ≈ 3.8 if per-token norms were equal) puts a much larger per-token push at 29–30 than the model ever sees there.
  - The counts are preregistered decision rules on shared donors and hosts, not independent tests.
  - One model (kev-4B) and one simulator family.
