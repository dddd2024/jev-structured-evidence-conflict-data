# A461-MECH-M14 R1: how much contrast does the author+block shift need per host, and does a 3× tilt of the round contrast toward the common subspace oppose the repair beyond a random tilt where hosts can move? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2), extended on 2026-10-30 to autonomous stage design and execution. 6956 kev-4B forwards in 55 batches (54 × 128 + 44).

**Parent:** M13 R1 (ceeda48).
- **AB shift with c at 29:** the shift at positions 0–12 + 29–30 with c at 29 only (`sh_fAB_c29`) repairs all three responsive hosts (S 39 = cs1) at half the change norm. The location is specific. Under the AB-only shift, c₃₀ costs 4bcbaf15 6 cells.
- **Tilt:** c + λ r with λ −1, +1, +2 left S flat at s 1, ½ and ⅜, because both informative hosts sat at floor or ceiling. At s ⅜, 264c458d was at 0 and 4bcbaf15 at 13. The pooled margin C fell with λ beyond 5 random-tilt nulls, but that was reported, not a verdict.
- **cpar16_sm and r:** per row, M12's cpar16_sm is approximately c scaled to about 0.58 plus about 1.77 r, since about ⅓ of P c's energy lies along c and about ⅔ in r. Its M12 cosine nulls were therefore random orthogonal tilts of that size. M12's SUBSPACE_BELOW_COSINE on 264c458d (1 vs 5–10) may be the tilt effect at λ ≈ 3, which M13 did not reach.

## Questions
1. **AB threshold.** For each responsive host, what is the smallest contrast size s (from ¼, ⅜, ½, 1) at which the AB shift with c at 29 repairs a majority (≥ 7 of 13) of the host's cells? How does that compare with the all-position shift's threshold, read from the pinned M13 rows? Is the shift at 29–30 needed, that is, does the shift at 0–12 only plus c at 29 still work? Does half the AB shift suffice?
2. **3× tilt where hosts can move.** At s = 7/16 (between 264c458d's thresholds) and 5/16 (between 4bcbaf15's), does S fall as λ runs over −3, −1, 0, +1, +3?
3. **Null.** Do c + 3r and c − 3r differ from c + 3q, where q ⟂ c with ‖q‖ = ‖r‖ in a random direction? Test with 8 seeds per cell, by host S where the host can move and by host C everywhere.

## Arms (all patch the L11 `o_proj` input at the 31 span positions of host new in every question row; sources donor new = main, donor ROUND = round; pools, mid and c as in M8–M13; common shift t = 1; contrast ∓ s/2 c)
| arm | patch | role |
|---|---|---|
| `full`, `meanD_host` | M3 all-heads patch / M6 pooled-donor arm, all 208 rows | bitwise anchors (S 51 / 39) |
| `sh_fAB_c29`, `cs_s0375`, `rem_p1`, `rnull_s05_1` | the M13 arms with identical patch fields (the null with its M13 seed), on 6 cells only: each responsive host's first 2 cells in donor order | bitwise replay of M13 (safe-cuts decision of 2026-10-30) |
| `abc_s05`, `abc_s0375`, `abc_s025` | shift at 0–12 + 29–30, c₃₀ weight 0, s = ½ / ⅜ / ¼ | Q1 threshold |
| `ab_only_c29` | shift at 0–12 only, c₃₀ weight 0, s 1 | Q1: is the shift at 29–30 needed? |
| `abc_t05` | as `sh_fAB_c29` with the shift at half size per row (`shift_scale` 0.5) | Q1 shift size |
| `cs_s0437`, `cs_s0312` | c at s = 7/16 / 5/16 | Q2 baseline (λ 0) |
| `rem_{m3,m1,p1,p3}_s0437`, `…_s0312` | c + λ r, λ = −3 / −1 / +1 / +3 | Q2 |
| `rnull3_s0437_1` … `8`, `rnull3_s0312_1` … `8` | c + 3q, random q ⟂ c with ‖q‖ = ‖r‖ (seeds `A461_M14_RNULL\|16\|d\|h\|i`) | Q3 |

There are 33 arms on all 208 rows plus 4 replay arms on 12 rows each.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m14_freeze_v1.py` (blob `67aa22550555e42746c6424777e9db0ea2ad3326`; CPU + tokenizer only), derived from the M13 freeze by checked edits. It cross-checks the M3–M13 key classes and pools, the span width and field layout of every capture, that full, meanD_host and the 4 replay arms' patch fields equal the M13 rows' fields, the 6 subset cells (2 per responsive host), the rows per arm, and that the 8 null seeds per cell are distinct and shared across s |
| manifest blob | `94b309d588578cfa87d5cba75af68106194e5f16` |
| design blob | `87905a3c4d0a5786a25bbd974ef13c40f3f3c06b`: the rules are under `preregistered_analysis` |
| runner blob | `f7d5436b583994f1d70ff3c14b1196d71aeca092`, the M13 runner 28bcffba with only the plan, pins and names changed. Every M14 field (`shift_positions`, `shift_scale`, `contrast_pos_weight`, `contrast_rem` with λ −3…+3 and `null_seed`) runs the M13 code, with the fail-closed tilt gate (1e-6) and shift-size gate (1e-3) |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m14_selftest_v1.py` (blob `1c2138b696f6ce1317df0e330877fe54f1ee9f7d`; 24 CPU threads): PASS 16/16 on the fake model with no GPU (`M14_SELFTEST_R1/`).<br>• Full path: 6956 rows in 55 batches with 44 captures.<br>• Wiring: 33 full arms distinct in 208/208 (cell, source); 4 replay arms on the 6 subset cells, 2 per responsive host. Tilt arms share r per cell; energy share = 1 + λ² r_share (max err 4.0e-09).<br>• Size gates: tilt gate max 1.5e-15 on 5016 tilt and null rows; shift-size gate on the 208 half-size AB rows, max rel err 4.9e-08.<br>• Identities, bitwise: weight 1 at 30 and all-position contrast = `cs_s0437`; the AB shift with c₃₀ weight 0 = c at 29 only; shift_scale 1 = unscaled.<br>• Seeds: 8 distinct null seeds per cell shared across s; the replay null keeps its M13 seed.<br>• Also checked: ROUND sources and the admission refusals.<br>A first attempt failed every test at the admission-stage check (a global rename had produced a wrong STAGE string); fixed in the self-test before this run, its output kept on the server as `_failed_M14_SELFTEST_R1_stage_name/`.<br>The analysis dry run on the fake raw exits 0; all 11 verdicts read INCONSISTENT_WITH_M3_M6_M13 on fake logits, as intended. |
| analysis | `A461_mech_m14_analysis_v1.py` (blob `4dd14bbf62d413a107fce0540203cf8ba19b196e`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, M6 design `43967513`, M6 raw `2147311c`, M7 design `f7d5318c`, M7 raw `0383fccf`, M8 design `14cee4c2`, M8 raw `997c9b71`, M9 design `fe91481e`, M9 raw `c74e5117`, M10 design `f127d850`, M10 raw `755c74e1`, M11 design `53d2bc8d`, M11 raw `393f0d6e`, M12 design `3b2ef50f`, M12 raw `cc79f23a`, M13 design `900b1f05`, M13 raw `cdbf677b`, G1.0 counterfactuals `06ee06d7` |

## Rules (coded in the design JSON)
- **S, SPEC, SUF and C:** as in M2–M13. SUF = S ≥ ½ S(full) and SPEC.
  - A responsive host is one where S(cs1) on its cells exceeds half its cells, with cs1 read from the pinned M13 rows.
  - C_h = the median over a host's cells of dM_main − dM_round.
- **Consistency gate:**
  - S(full) = 51, and its 208 rows equal M3 bitwise;
  - S(meanD_host) = 39, and its rows equal M6 bitwise;
  - the 4 replay arms' 48 rows equal M13 bitwise.
  - Otherwise every verdict is INCONSISTENT_WITH_M3_M6_M13.
- **Q1:**
  - Per responsive host, SMIN_AB = the smallest s in {¼, ⅜, ½, 1} with host S ≥ 7. The s = 1 value is the M13 `sh_fAB_c29` rows. SMIN_CS is the same rule on M13's `cs_s025` / `cs_s0375` / `cs_s05` / `cs1`. NONE counts as above 1.
  - AB_SMIN_BY_HOST lists SMIN_AB / SMIN_CS per responsive host.
  - Pooled: AB_THRESHOLD_SAME iff the two are equal on every responsive host; AB_THRESHOLD_LOWER iff SMIN_AB ≤ SMIN_CS everywhere and < somewhere; HIGHER likewise in the other direction; MIXED otherwise.
  - SHIFT_2930_NEEDED iff not SUF(`ab_only_c29`).
  - AB_T05_SUFFICES iff SUF(`abc_t05`).
- **Q2:** per s ∈ {7/16, 5/16}, S at λ −3, −1, 0, +1, +3:
  - TILT_OPPOSES iff S is non-increasing and S(−3) > S(+3);
  - TILT_SUPPORTS iff S is non-decreasing and S(−3) < S(+3);
  - TILT_NO_EFFECT iff all five are equal;
  - TILT_MIXED otherwise.
  - Pooled REM_* as in M13. The same rule per host is reported as TILT_BY_HOST.
- **Q3:** per responsive host h and s, N = the 8 3× nulls.
  - **S test:** (h, s) is informative unless the host S of `rem_p3`, `rem_m3` and the 8 nulls are all 0 or all equal to h's cell count. On informative pairs:
    - HARM_BEYOND_NULL iff S_h(`rem_p3`) < min N; LESS_HARM_THAN_NULL iff it is > max N; AT otherwise;
    - REMOVAL_BEYOND_NULL iff S_h(`rem_m3`) > max N; REMOVAL_BELOW_NULL iff it is < min N; AT otherwise.
    - Pooled REM3_DIRECTION_{SPECIFIC, NOT_SPECIFIC, REVERSED, MIXED} as in M13, or UNINFORMATIVE if no pair is informative.
  - **C test:** the same rules with C_h, on every responsive (h, s), giving REM3C_DIRECTION_*.
- **Always reported:**
  - S and C per arm and per host;
  - leave-one-donor-group-out of every verdict;
  - r's energy share, the tilt and shift-size errors;
  - every null's S and C;
  - change norms relative to full.

## Interpretation fixed in advance
- **AB_THRESHOLD_SAME:** confining the shift to the author and block lines costs no contrast size on any responsive host.
- **SHIFT_2930_NOT_NEEDED:** the shift is needed only at 0–12, and c alone carries the round value.
- **AB_T05_SUFFICES:** half the AB shift is enough.
- **REM_OPPOSES with REM3_DIRECTION_SPECIFIC (S or C):** at sizes where a host can move, the in-subspace remainder r works against the round-specific repair beyond a random orthogonal push of the same size. That would account for M12's SUBSPACE_BELOW_COSINE on 264c458d.
- **REM3_DIRECTION_NOT_SPECIFIC:** any orthogonal push of that size does the same.
- **Limits:**
  - All arms except `full` are pooled-donor arms, effectively 8 host replicates, of which 3 responded in M9–M13. Per-host S is the honest unit.
  - C is a continuous margin and can move with no host crossing threshold.
  - The chosen sizes rest on M11–M13 thresholds and may still put a host at floor or ceiling; the S test then reads UNINFORMATIVE, not AT.
  - The Q1 thresholds compare M14 rows with M13 rows. That is valid because the consistency gate requires bitwise replays across runs.
  - One model (kev-4B) and one simulator family.
