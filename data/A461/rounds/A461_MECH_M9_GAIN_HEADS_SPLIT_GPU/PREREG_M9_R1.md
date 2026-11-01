# A461-MECH-M9 R1: how does the pooled round contrast's effect grow with the common shift, which heads' slice carries it, and does it lie in the common subspace? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 4828 kev-4B forwards in 38 batches (37 × 128 + 92).

**Parent:** M8 R1 (d1d9125). The repair factors as a 16-dimensional common part plus one shared contrast vector.
- **TWOPART:16 and POOLED_CONTRAST_SUFFICES:** tp16 S 44; tpD64 38.
- **Gain on the common shift:** on the pooled common shift, the pooled contrast c = mean_D B(ROUND) − mean_D B(new) at a quarter of its size per source already repairs (cs05 S 38, at the SPEC threshold).
- **CONTRAST_NONADDITIVE:** the contrast moves the main-vs-round margin 16.7× more there than on the plain host (C 1.149 vs M7 rcD 0.069).

## Questions
1. **Gain map.** How does the contrast's effect C grow with the size t of the common shift? Is it a product (bilinear), saturating early, or a late threshold? What is the smallest t at which the contrast repairs?
2. **Head slices.** The patch site is the L11 `o_proj` input, which is the concatenation of the 16 heads' outputs. Is the contrast's effect carried by the slice of the M3 writer heads 8–14, by head 10 alone, or by the other heads?
3. **Subspace split.** At matched size, does the part of c inside the cell's 16-dimensional common subspace repair, or the part outside it? The common subspace is the top-16 same-kind Δ basis, M7 dlr16 / M8 tp16.

## Arms
Every arm patches the L11 `o_proj` input at the 31 span positions of host new, in every question row. Sources are donor new (main) and donor ROUND (round), and X_B is the BULK part (OTHER_ITEMS + CONTEXT) of capture X. Pool_D is the 12 donors outside both the donor's and the host's group (as in M6–M8). mid = ½(mean_D B(new) + mean_D B(ROUND)), and c = mean_D B(ROUND) − mean_D B(new).

| arm | patch | role |
|---|---|---|
| `full` | the M3 all-heads patch | bitwise anchor (S 51) |
| `meanD_host` | host − h_B + mean_{Pool_D} p_B(src), as in M6 | bitwise anchor (S 39) |
| `cs0`, `cs05`, `cs1`, `cs2` | host − h_B + mid ∓ (s/2)c, s ∈ {0, ½, 1, 2}: the M8 arms with identical patch fields | bitwise anchors (S 0 / 38 / 39 / 36); the t = 1 row of the grid |
| **`g{t}_{s}`**, t ∈ {0, ¼, ½}, s ∈ {0, ½, 1, 2}, not t = s = 0 | host + t (mid − h_B) ∓ (s/2)c (− main, + round) | Q1 (11 arms); g0_2 is M7 rcD's construction |
| **`chW`** / **`ch10`** / **`chR`** | cs1 with c restricted to the `o_proj`-input slices of heads 8–14 / head 10 / the other 9 heads (0–7, 15) | Q2; not size-matched, slice energy recorded |
| **`cpar16_sm`** / **`cperp16_sm`** | cs1 with c replaced by U₁₆U₁₆ᵀc / (I − U₁₆U₁₆ᵀ)c, rescaled to ‖c‖ per row and span position (cap 10). U₁₆ is the top 16 right singular vectors of {p_B(a) − h_B(a)} over Pool_D (the M7 dlr16 basis) | Q3 |
| `crand16_sm` | the same with a seeded random 16-frame (no cap) | Q3 null |

- **cs0 and g{t}_0** have identical main and round patches, so S = 0 by construction. Their J counts measure the common shift alone, at size t.
- **g0_{s}** is the contrast on the plain host. g0_2 is the same construction as M7 rcD, and the self-test shows bitwise equality with a meandiff patch.
- **Contrast restricted to all 16 heads** is bitwise equal to cs1 (self-test).
- **The split arms are size-matched.** M8 found that a quarter of c per source already repairs, so without size matching any part with a large share of c's energy could pass on size alone.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m9_freeze_v1.py` (blob `f04b4996`; CPU + tokenizer only). Derived from the M8 freeze by checked substitutions. It cross-checks the M3, M4, M6, M7 and M8 key classes and the M6–M8 pools; it checks that the full, meanD_host and cs0–cs2 patch fields equal the M8 rows' fields, and that the split basis pairs equal M7 dlr16_sm's |
| manifest blob | `1594cf9da667c3a9e4852edefea64df3af35890d` |
| design blob | `fe91481e42e5cf33f20cd7c98dba16caf177268c`: rules under `preregistered_analysis` |
| runner blob | `8efd4a2835125a8ac0a8cd0de259547755345414`, derived from the M8 runner 7cd3ef9d by checked substitutions. The `cshift` op gains `t`, `contrast_heads` and `contrast_proj`; without a `t` field it runs the M8 code path |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m9_selftest_v1.py` (blob `178a15f5`): **PASS 16/16** on the fake attention model (`M9_SELFTEST_R1/`). It covers wiring of all 23 arms, energy bookkeeping (par + perp = 1, writer + rest heads = 1), the size gate of the rescaled parts (max rel err 1.9e-08), and the identities: all-16-heads = cs1, g0_2 = rcD meandiff, par at k = 64 = cs1 (bitwise). It also covers the refusals, and the frozen analysis dry run passed. Two earlier attempts are kept on the server: R0, where a zero contrast part failed closed, fixed by α = 0 at zero-part positions; and R0b, a self-test check bug, `t: null` read as None, with the runner unchanged |
| analysis | `A461_mech_m9_analysis_v1.py` (blob `59badbec`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, M6 design `43967513`, M6 raw `2147311c`, M7 design `f7d5318c`, M7 raw `0383fccf`, M8 design `14cee4c2`, M8 raw `997c9b71`, G1.0 counterfactuals `06ee06d7` |

## Design
- **Captures:** 44, as in M4–M8. They are fail-closed on class additivity, and 36 must replay M1 bitwise.
- **Patches:** 23 arms × 2 sources × 104 cells = 4784.
- **Gates checked in the run:** the 208 `full` rows must equal M3 bitwise, and the 208 `meanD_host` rows must equal M6 bitwise.
- **Size gate:** applies to the rescaled contrast parts at every non-capped, non-zero position, fail-closed at 1e-3 relative.

## Rules (coded in the design JSON)
- **S, SPEC, SUF:** as in M2–M8. SUF(arm) iff S(arm) ≥ ½ S(full) and SPEC(arm). C(arm) is the median over cells of dM_main − dM_round.
- **Consistency gate:** all of the following, otherwise every verdict is INCONSISTENT_WITH_M3_M6_M8.
  - S(full) = 51, with 208 rows bitwise equal to M3;
  - S(meanD_host) = 39, with 208 rows bitwise equal to M6;
  - cs0 / cs05 / cs1 / cs2: 4 × 208 rows bitwise equal to M8, and S = 0 / 38 / 39 / 36.
  - g0_2 against M7 rcD (bitwise and S) is reported, not gated.
- **Q1 gain shape:** for s ∈ {1, 2}, L(s) = (C(g05_s) − C(g0_s)) / (C(cs_s) − C(g0_s)), defined iff the denominator is > 0.
  - **GAIN_BILINEAR** if both L ∈ [0.3, 0.7];
  - **GAIN_EARLY_SATURATING** if both > 0.7;
  - **GAIN_LATE_THRESHOLD** if both < 0.3;
  - **GAIN_MIXED** otherwise; **GAIN_UNDEFINED** if either L is undefined.
  - The quarter-point ratios Q(s) (g025 in place of g05) are reported.
- **Q1 minimal shift:** t\* is the smallest t ∈ {0, ¼, ½, 1} with SUF at s = 1. The verdict is **GAIN_TMIN:t\*** (or GAIN_TMIN_NONE). The SUF set over the whole grid is reported.
- **Q2 heads:**
  - **CONTRAST_IN_WRITER_HEADS** iff SUF(chW) and not SUF(chR);
  - **CONTRAST_OUTSIDE_WRITER_HEADS** iff the reverse;
  - **CONTRAST_EITHER_HEAD_SET** iff both;
  - **CONTRAST_NEEDS_ALL_HEADS** iff neither;
  - suffix **+H10** iff SUF(ch10).
- **Q3 split:** SPLIT_NULL holds iff S(crand16_sm) ≤ 5 and not SPEC(crand16_sm).
  - **CONTRAST_IN_COMMON_SUBSPACE** iff SUF(cpar16_sm) and not SUF(cperp16_sm);
  - **CONTRAST_OUTSIDE_COMMON_SUBSPACE** iff the reverse;
  - **CONTRAST_BOTH_PARTS** iff both;
  - **CONTRAST_NOT_SPLITTABLE** iff neither;
  - suffix **_UNRESOLVED** on the first three if SPLIT_NULL fails.
- **Always reported:**
  - the (t, s) grid of S, C and J;
  - per-host S;
  - leave-one-donor-group-out of every verdict;
  - energy shares of the head slices and of the contrast parts, with α, capped and zero-part shares;
  - the change norm of every arm relative to full.

## Interpretation fixed in advance
- **GAIN_BILINEAR:** the contrast's effect on the margin grows in proportion to the common shift, a product.
- **GAIN_EARLY_SATURATING:** half the common shift already gives most of it.
- **GAIN_LATE_THRESHOLD:** there is little effect until the full common shift.
- **CONTRAST_IN_WRITER_HEADS:** the contrast acts through the M3 writer heads' slice of the `o_proj` input; **+H10:** head 10's slice alone suffices.
- **CONTRAST_IN_COMMON_SUBSPACE:** at matched size, the part of c inside the 16-dimensional common subspace repairs and the part outside does not. The contrast is aligned with the common part.
- **Limits:**
  - All M9 arms except `full` are pooled-donor arms, so they are effectively 8 host replicates (M8: they repair only 3 hosts). Per-host S is the honest unit.
  - The head arms are not size-matched.
  - The counts are preregistered decision rules on shared donors and hosts, not independent tests.
  - One model (kev-4B) and one simulator family.
