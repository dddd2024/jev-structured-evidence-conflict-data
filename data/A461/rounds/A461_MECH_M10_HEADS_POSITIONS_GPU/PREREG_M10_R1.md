# A461-MECH-M10 R1: is the writer-head reading of the pooled round contrast an energy effect, at which span position does the contrast act, where must the common shift be, and does the split survive a multi-seed null? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 5244 kev-4B forwards in 41 batches (40 × 128 + 124).

**Parent:** M9 R1 (da03730). The pooled contrast c = mean_D B(ROUND) − mean_D B(new) is read only on the (nearly) full common shift.
- **GAIN_MIXED, GAIN_TMIN:1.0.**
- **CONTRAST_IN_WRITER_HEADS:** chW S 39, chR 0, ch10 25 (not SPEC). The head slices were not size-matched; heads 8–14 hold 82 % of c's energy.
- **CONTRAST_OUTSIDE_COMMON_SUBSPACE_UNRESOLVED:** cperp16_sm S 39; cpar16_sm 27, not SPEC; one-seed null crand16_sm S 7 > 5.

**New fact used in the design:** in all 22 M9 ROUND/new capture pairs, the BULK difference is nonzero only at span positions **29 and 30** (‖c‖ ≈ 7 at 29 and ≈ 2–4 at 30). ROUND changes the token at position 29, so only the queries from there on attend differently. This was read from the M9 captures (`M9_GPU_RUNS/ATTEMPT_R1/captures`, all 22 scenes) before this freeze.

## Questions
1. **Size-matched heads.** With each head slice of c rescaled to ‖c‖ per row and span position, does the writer slice (heads 8–14) still repair and the other heads' slice not? Does head 10 alone, or the writer heads without head 10, suffice?
2. **Position of the contrast.** Does c act at position 29 (the changed token) or at 30?
3. **Location of the common shift.** Is the common shift needed only at the contrast positions 29–30, only at the earlier positions 0–28, or at both?
4. **Null.** Does the M9 split survive a null of 5 random frames (M9's seed plus 4 new ones)?
5. **Finer gain.** What is the smallest t ∈ {0.6, 0.7, 0.8, 0.9, 1} at which the contrast at s = 1 repairs?

## Arms (all patch the L11 `o_proj` input at the 31 span positions of host new in every question row; sources donor new = main, donor ROUND = round; Pool_D, mid and c as in M8–M9; scale ∓ ½ c)
| arm | patch | role |
|---|---|---|
| `full` | the M3 all-heads patch | bitwise anchor (S 51) |
| `meanD_host` | as M6 | bitwise anchor (S 39) |
| `cs1`, `chW`, `ch10`, `chR`, `cpar16_sm`, `cperp16_sm`, `crand16_sm` | the M9 arms with identical patch fields | bitwise anchors (S 39 / 39 / 25 / 0 / 27 / 39 / 7) |
| **`chW_sm` / `ch10_sm` / `chR_sm` / `chWx10_sm`** | cs1 with c restricted to the `o_proj`-input slice of heads 8–14 / 10 / 0–7 and 15 / 8, 9, 11–14, each rescaled to ‖c‖ per row and span position (cap 10) | Q1 |
| **`cpos29` / `cpos30`** | cs1 with c kept only at span position 29 / 30 (not size-matched) | Q2 |
| **`sh2930` / `sh0_28`** | the common shift (t = 1) only at span positions 29–30 / 0–28, plus the full ∓ ½ c | Q3 |
| `crand16_sm_s1` … `_s4` | as crand16_sm with 4 new seeds (`A461_M10_CRAND\|16\|d\|h\|i`) | Q4 null |
| **`g06_1` … `g09_1`** | host + t (mid − h_B) ∓ ½ c, t ∈ {0.6, 0.7, 0.8, 0.9} | Q5 |

- **Identities shown by the self-test:**
  - c on all 16 heads equals cs1 bitwise, and so does c kept at all 31 positions.
  - All 16 heads rescaled, and the common shift at all 31 positions, equal cs1 up to float rounding.
- **What the rescaling keeps:** each rescaled slice keeps its unscaled energy share (recorded). The writer slice without head 10, plus head 10, gives the writer slice's share.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m10_freeze_v1.py` (blob `3d43da50f30fc12b46aeb65615c0d678e1398d50`; CPU + tokenizer only), derived from the M9 freeze by checked substitutions. It cross-checks the M3–M9 key classes and pools, the span width (31), and that the 9 replay arms' patch fields equal the M9 rows' fields. It also checks 5 distinct random frames per row |
| manifest blob | `c67df778f46f9b3fecaf96fd55cb62c48455bfba` |
| design blob | `f127d850223174f8ef10997c8539a2c348102b89`: the rules are under `preregistered_analysis` |
| runner blob | `7f2577cc1673d946692d962fddf857e05485a19a`, derived from the M9 runner 8efd4a28 by checked substitutions. The `cshift` op gains `shift_positions`, `contrast_positions` and `contrast_rescale`; the M9 arms run the M9 code unchanged |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m10_selftest_v1.py` (blob `bb78f50deeb9b0df3adb069fec37a6125f451657`): PASS 16/16 on the fake model with no GPU (`M10_SELFTEST_R1/`): wiring of the 25 arms, the bookkeeping identities above, the size gate on 2288 rescaled rows (max rel err 3.4e-08), the identities with cs1, the ROUND sources, and the admission refusals. The analysis dry run on the fake raw completes |
| analysis | `A461_mech_m10_analysis_v1.py` (blob `e0f28aac7fd310f01023b261743a392311d42eaf`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, M6 design `43967513`, M6 raw `2147311c`, M7 design `f7d5318c`, M7 raw `0383fccf`, M8 design `14cee4c2`, M8 raw `997c9b71`, M9 design `fe91481e`, M9 raw `c74e5117`, G1.0 counterfactuals `06ee06d7` |

## Design
- **Captures:** 44, as in M4–M9. They are fail-closed on class additivity, and 36 must replay M1 bitwise.
- **Patches:** 25 arms × 2 sources × 104 cells = 5200.
- **Gates checked in the run:** the 208 `full` rows must equal M3 bitwise, and the 208 `meanD_host` rows must equal M6 bitwise.
- **Size gate:** applies to the rescaled head slices (fail-closed at 1e-3 relative at every non-capped, nonzero position) and to the contrast parts as in M9.

## Rules (coded in the design JSON)
- **S, SPEC, SUF and C:** as in M2–M9.
- **Consistency gate:**
  - S(full) = 51, and its 208 rows equal M3 bitwise;
  - S(meanD_host) = 39, and its rows equal M6 bitwise;
  - the 7 M9 arms each have 208 rows equal to M9 bitwise, with S = 39 / 39 / 25 / 0 / 27 / 39 / 7.
  - Otherwise every verdict is INCONSISTENT_WITH_M3_M6_M9.
- **Q1 heads (size-matched):**
  - CONTRAST_SM_IN_WRITER_HEADS iff SUF(chW_sm) and not SUF(chR_sm);
  - CONTRAST_SM_OUTSIDE_WRITER_HEADS iff the reverse;
  - CONTRAST_SM_EITHER_HEAD_SET iff both;
  - CONTRAST_SM_NEEDS_ALL_HEADS iff neither.
  - Suffix **+H10** iff SUF(ch10_sm), and **+WX10** iff SUF(chWx10_sm).
- **Q2 position:**
  - CONTRAST_AT_P29 iff SUF(cpos29) and not SUF(cpos30);
  - CONTRAST_AT_P30 iff the reverse;
  - CONTRAST_AT_EITHER_POSITION iff both;
  - CONTRAST_NEEDS_BOTH_POSITIONS iff neither.
- **Q3 shift location:**
  - SHIFT_AT_CONTRAST_POSITIONS iff SUF(sh2930) and not SUF(sh0_28);
  - SHIFT_AT_OTHER_POSITIONS iff the reverse;
  - SHIFT_AT_EITHER iff both;
  - SHIFT_NEEDS_ALL_POSITIONS iff neither.
- **Q4 null:** SPLIT_NULL5 holds iff the median S over the 5 random frames is ≤ 5 and none is SPEC.
  - The contrast subspace verdict is re-applied to the replayed cpar16_sm / cperp16_sm rows, with the M9 categories and the `_UNRESOLVED` suffix iff SPLIT_NULL5 fails.
  - The M9 one-seed verdict stays as reported in M9.
- **Q5:** t\* is the smallest t ∈ {0.6, 0.7, 0.8, 0.9, 1} with SUF at s = 1; the verdict is GAIN_TFINE:t\* (or GAIN_TFINE_NONE).
- **Always reported:**
  - per-host S;
  - leave-one-donor-group-out of every verdict;
  - energy shares, α, capped and zero-part shares;
  - each random frame's S;
  - the position energy check: the cpos29 + cpos30 share is 1 iff c is zero elsewhere;
  - change norms relative to full.

## Interpretation fixed in advance
- **CONTRAST_SM_IN_WRITER_HEADS:** at the size of c, the writer slice carries the contrast's effect and the other heads' slice does not, so the M9 head result is not an energy effect. **+H10:** head 10's slice alone suffices at matched size. **+WX10:** the writer heads without head 10 suffice.
- **CONTRAST_AT_P29:** the contrast acts at the position whose token ROUND changes. **CONTRAST_AT_P30:** it acts at the next position.
- **SHIFT_AT_CONTRAST_POSITIONS:** the common shift is needed only where the contrast is, a local gate. **SHIFT_AT_OTHER_POSITIONS:** the shift acts through the earlier positions, as context read by later layers.
- **SPLIT_NULL5 failing:** a contrast-sized push in a random 16-dim direction often repairs, and the M9 split stays unresolved.
- **Limits:**
  - All M10 arms except `full` are pooled-donor arms, effectively 8 host replicates (3 responded in M9). Per-host S is the honest unit.
  - The position arms are not size-matched: position 29 holds most of c's energy.
  - The counts are preregistered decision rules on shared donors and hosts, not independent tests.
  - One model (kev-4B) and one simulator family.
