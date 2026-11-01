# A461-MECH-M15 R1: is M14's lower AB threshold due to dropping c at 30 or to confining the shift, and does M14's 3× tilt harm on 264c458d survive 24 random-tilt nulls? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Designed and run autonomously under the user's 2026-10-30 grant ("权限给你，不用询问我你可以自己设计并执行实验等科研相关的事") and the standing GPU authorization (policy V2). 5500 kev-4B forwards in 43 batches (42 × 128 + 124).

**Parent:** M14 R1 (e8dcd0f; exploratory addendum bf12ae7).
- **Two differences at once:** the AB patch (shift at 0–12 + 29–30, c at 29 only) needs less contrast than the all-position shift with c at 29 and 30 on 264c458d (⅜ vs ½) and 4bcbaf15 (¼ vs ⅜). It differs from the all-position shift both in where the shift sits and in c₃₀.
- **Tilt at s 7/16:** on 264c458d, S falls 12 / 9 / 7 / 2 / 2 for λ −3 / −1 / 0 / +1 / +3. c + 3r (2) sits just below the 8 random 3× tilts (3–10), and c − 3r (12) just above them.
- **Round action:** at that size, S is set by the round source's action margin A (addendum).

## Questions
1. **Split the Q1 gain.** Per host, a 2 × 2 table of thresholds (shift AB / all positions × c₃₀ on / off) at s ¼, ⅜, ½. Which of the two differences lowers the threshold on 264c458d and 4bcbaf15?
2. **Dose.** At s 7/16, is S graded in λ once λ −2 and +2 fill the gaps?
3. **Null robustness.** Do c + 3r and c − 3r stay outside the range of 24 random 3× tilts (M14's 8 plus 16 new)?

## Arms (all patch the L11 `o_proj` input at the 31 span positions of host new in every question row; sources donor new = main, donor ROUND = round; pools, mid and c as in M8–M14; common shift t = 1; contrast ∓ s/2 c)
| arm | patch | role |
|---|---|---|
| `full`, `meanD_host` | M3 all-heads patch / M6 pooled-donor arm, all 208 rows | bitwise anchors (S 51 / 39) |
| `abc_s0375`, `rem_p3_s0437`, `rnull3_s0437_1`, `cs_s0312` | the M14 arms with identical patch fields, on M14's 6 subset cells | bitwise replay of M14 |
| `abc30_s05`, `abc30_s0375`, `abc30_s025` | shift at 0–12 + 29–30, c at 29 and 30 | Q1 cell AB30 |
| `csc29_s05`, `csc29_s0375`, `csc29_s025` | shift at all 31 positions, c₃₀ weight 0 | Q1 cell ALL29 |
| `rem_m2_s0437`, `rem_p2_s0437` | c − 2r, c + 2r at s 7/16 | Q2 dose |
| `rnull3_s0437_9` … `24` | c + 3q, random q ⟂ c, ‖q‖ = ‖r‖ (seeds `A461_M14_RNULL\|16\|d\|h\|i`, i 9–24, disjoint from M14's 1–8) | Q3 |

There are 26 arms on all 208 rows plus 4 replay arms on 12 rows each. The other two Q1 cells come from pinned rows: AB29 = M14 `abc_*`, ALL30 = M13 `cs_*`. λ −3, −1, 0, +1, +3 and nulls 1–8 come from M14.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m15_freeze_v1.py` (CPU + tokenizer only), derived from the M14 freeze by checked edits. It cross-checks the M3–M14 key classes and pools, the span width and field layout, that full, meanD_host and the 4 replay arms' patch fields equal the M14 rows' fields, that the 6 subset cells are M14's, the rows per arm, and that the 16 null seeds per cell are distinct and disjoint from M14's 8 |
| manifest blob | `bcefb29e5b9ab20150680232c1e7c723a9b857a2` |
| design blob | `4288440cb835cb1e36211c949878428a2dba2ad2`: the rules are under `preregistered_analysis` |
| runner blob | `8632c3a13fd430be348ccf36996c63f942266793`, the M14 runner f7d5436b with only the plan, pins and names changed |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m15_selftest_v1.py` (blob `788dd77d6e2ad3704c3d2e386f99998c2f933fa6`; 24 CPU threads): **16/16 PASS** on the server (2026-10-31 06:47 +08), zero GPU loads; analysis dry run on fake logits exits 0 with every verdict INCONSISTENT_WITH_M3_M6_M14, as it must (`M15_SELFTEST_R1/`) |
| analysis | `A461_mech_m15_analysis_v1.py` (blob `83d1c5a4ac4c3eca1adcdaf46ef5d58f986fa85e`), written before the run |
| inputs | as M14, plus M14 design `87905a3c` and M14 raw `d2ac9f42` |

## Rules (coded in the design JSON)
- **S, SPEC, SUF and C:** as in M2–M14. Responsive hosts from M13 cs1.
- **Consistency gate:** S(full) = 51 with its 208 rows bitwise equal to M3; S(meanD_host) = 39 with its rows bitwise equal to M6; the 4 replay arms' 48 rows bitwise equal to M14. Otherwise every verdict is INCONSISTENT_WITH_M3_M6_M14.
- **Q1 split:** per responsive host and family, SMIN = the smallest s in {¼, ⅜, ½} with host S ≥ 7 (NONE above ½).
  - C30 effect = sign(SMIN(AB30) − SMIN(AB29)) and sign(SMIN(ALL30) − SMIN(ALL29)) → C30_COSTS (both > 0), C30_COSTS_UNDER_AB / _UNDER_ALL (one > 0, the other 0), C30_NO_COST (both 0), else C30_MIXED.
  - LOC effect = sign(SMIN(ALL29) − SMIN(AB29)) and sign(SMIN(ALL30) − SMIN(AB30)) → AB_LOWERS, AB_LOWERS_WITHOUT_C30, AB_LOWERS_WITH_C30, LOC_NO_EFFECT, else LOC_MIXED.
  - Pooled over 264c458d and 4bcbaf15: Q1_GAIN_C30_ONLY (both C30_COSTS* and LOC_NO_EFFECT), Q1_GAIN_LOC_ONLY (both AB_LOWERS* and C30_NO_COST), Q1_GAIN_BOTH (both have a C30 cost and an AB lowering), else Q1_GAIN_MIXED.
- **Dose at s 7/16:** S over λ −3, −2, −1, 0, +1, +2, +3: DOSE_OPPOSES iff non-increasing and S(−3) > S(+3); DOSE_SUPPORTS likewise; DOSE_NO_EFFECT iff all equal; else DOSE_MIXED. Pooled and per host.
- **24 nulls at s 7/16:** per responsive host, informative unless rem_p3, rem_m3 and all 24 nulls are all 0 or all at the host's cell count. HARM_BEYOND_NULL24 iff S(rem_p3) < min N24; LESS_HARM_THAN_NULL24 iff > max; REMOVAL_BEYOND_NULL24 iff S(rem_m3) > max N24; REMOVAL_BELOW_NULL24 iff < min; else AT. The same with C_h. Ranks are reported. Pooled NULL24_S / NULL24_C: SPECIFIC, NOT_SPECIFIC, REVERSED, MIXED or UNINFORMATIVE as in M14.
- **Round action, fixed in advance:** for every s 7/16 tilt and null arm and responsive host, report the main-JOINT count, the round M > 0 and A > 0 counts, and the round median A. ROUND_A_RANK_264C = the number of the 24 nulls whose round A > 0 count on 264c458d is ≥ that of rem_p3, and ≤ that of rem_m3.
- **Always reported:** S and C per arm and host; leave-one-donor-group-out of every verdict; energy shares and tilt errors; every null's S and C; change norms relative to full.

## Interpretation fixed in advance
- **Q1_GAIN_C30_ONLY:** M14's lower threshold comes from dropping c at 30, not from confining the shift. **LOC_ONLY:** it comes from confining the shift to the author and block lines. **BOTH:** each lowers it.
- **HARM_BEYOND_NULL24 on 264c458d:** M14's tilt result survives three times as many nulls. **AT:** it was within the null spread.
- **DOSE_OPPOSES on 264c458d:** the opposition is graded in λ.
- **Limits:**
  - All arms except `full` are pooled-donor arms (effectively 8 host replicates, 3 responding). Per-host S is the honest unit, and every informative verdict rests on 264c458d or 4bcbaf15.
  - The Q1 cells and the dose and null comparisons combine M13, M14 and M15 rows. That is valid because the replay arms are bitwise equal.
  - Thresholds on a ¼–⅜–½ grid can tie when the true thresholds differ within a step.
  - One model (kev-4B) and one simulator family.
