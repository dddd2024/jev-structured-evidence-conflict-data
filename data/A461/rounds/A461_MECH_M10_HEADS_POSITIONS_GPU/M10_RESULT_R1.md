# A461-MECH-M10 R1: result (is the writer-head reading of the pooled round contrast an energy effect, at which span position does the contrast act, where must the common shift be, and does the split survive a multi-seed null?)

**Run:**
- 5244/5244 kev-4B forwards in 41 batches (40 × 128 + 124); 0 denied; one model load; elapsed 7889 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`.
- Raw blob `755c74e1d722cdd0429916a13608fd60c647bb53`.
- The run follows prereg 73784df under the standing GPU authorization. The pre-model gate passed (`COMPLETE_A461_MECH_M10_PRE_MODEL_GATE`, saved as `M10_GPU_R1/pre_model_gate_receipt.json`). There was a single ledger attempt (`A461_MECH_M10_GPU_20261029_R1`, 5244 reserved, 5244 consumed).

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- The size gate of the rescaled head slices and contrast parts passed in the run (fail-closed at 1e-3 relative). No position hit the cap of 10.
- The captures stay on the server under `M10_GPU_RUNS/ATTEMPT_R1/captures`. Every non-capture file was fetched here and verified against the run's `SHA256SUMS` (44/44). The receipt, run log and pre-model gate receipt match the server copies by sha256.

**Analysis:** `A461_mech_m10_analysis_v1.py` (blob e0f28aac, frozen before the run), run automatically by the server launch script after the receipt read COMPLETE (exit 0, 2026-10-30 01:59 +08:00). Output: `M10_ANALYSIS_R1/m10_analysis.json` (sha256 18497ebf…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51, 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 rows bitwise equal to M6; cs1 / chW / ch10 / chR / cpar16_sm / cperp16_sm / crand16_sm each 208/208 rows bitwise equal to M9, S = 39 / 39 / 25 / 0 / 27 / 39 / 7 |
| **Q1 heads (size-matched)** | **CONTRAST_SM_IN_WRITER_HEADS+H10+WX10**: chW_sm S 39, SPEC; chR_sm S 0; ch10_sm S 39, SPEC; chWx10_sm S 39, SPEC |
| **Q2 position** | **CONTRAST_AT_P29**: cpos29 S 39, SPEC; cpos30 S 3, not SPEC (positions not size-matched) |
| **Q3 shift location** | **SHIFT_NEEDS_ALL_POSITIONS**: sh2930 S 0 (J 0 / 0); sh0_28 S 13, not SPEC |
| **Q4 SPLIT_NULL5** (median S ≤ 5 over 5 frames, none SPEC) | **fails**: S 7 / 11 / 4 / 7 / 4, median 7, max 11; none SPEC |
| Q4 subspace verdict, re-applied | **CONTRAST_OUTSIDE_COMMON_SUBSPACE_UNRESOLVED** (cperp16_sm S 39 SPEC; cpar16_sm 27, not SPEC) |
| **Q5 finer gain** | **GAIN_TFINE:0.8**: g08_1 S 26 (SUF line 25.5), SPEC; g07_1 S 14; g06_1 S 13 |

**Leave one donor group out:**
- 14/14 splits give CONTRAST_SM_IN_WRITER_HEADS+H10+WX10, CONTRAST_AT_P29 and SHIFT_NEEDS_ALL_POSITIONS.
- The split verdict is _UNRESOLVED in 13/14 splits. In the run-68 split the null median is 5 and the verdict is a plain CONTRAST_OUTSIDE_COMMON_SUBSPACE (as in M9's one split, now with 5 seeds).
- GAIN_TFINE is 0.8 in 11/14 splits and 0.9 in 3/14 (run-181, run-212, run-272). t = 0.8 sits on the SUF edge (26 vs 25.5).

## All arms (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority; C = median dM_main − dM_round)
| arm | S | J main / round | frac | grp | SPEC | median dM main / round | C | energy share of c (median / min) | α median / max |
|---|---|---|---|---|---|---|---|---|---|
| full (M3 anchor) | 51 | 58 / 7 | 0.99 | 14 | ✓ | +0.35 / −0.37 | 0.71 | — | — |
| meanD_host = cs1 | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.66 | 0.60 | 1 | — |
| chW (M9, unscaled) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.26 / −0.61 | 0.66 | 0.82 / 0.82 | — |
| ch10 (M9, unscaled) | 25 | 39 / 14 | 0.50 | 4 | ✗ | +0.28 / +0.34 | −0.01 | 0.31 / 0.30 | — |
| chR (M9, unscaled) | 0 | 26 / 39 | 0.00 | 0 | ✗ | +0.33 / +0.36 | −0.04 | 0.18 / 0.17 | — |
| **chW_sm** (heads 8–14) | **39** | 39 / 0 | 1.00 | 14 | ✓ | +0.26 / −0.68 | 0.71 | 0.82 / 0.82 | 1.07 / 1.53 |
| **ch10_sm** (head 10) | **39** | 39 / 0 | 0.78 | 14 | ✓ | +0.24 / −0.25 | 0.43 | 0.31 / 0.30 | 1.73 / 3.60 |
| **chWx10_sm** (8, 9, 11–14) | **39** | 39 / 0 | 1.00 | 14 | ✓ | +0.31 / −0.33 | 0.57 | 0.52 / 0.51 | 1.37 / 1.70 |
| **chR_sm** (0–7, 15) | **0** | 26 / 39 | 0.00 | 0 | ✗ | +0.32 / +0.38 | −0.09 | 0.18 / 0.17 | 1.36 / 2.83 |
| **cpos29** | **39** | 39 / 0 | 1.00 | 14 | ✓ | +0.25 / −0.66 | 0.66 | 0.886 / 0.878 | — |
| cpos30 | 3 | 30 / 27 | 0.24 | 0 | ✗ | +0.34 / +0.35 | −0.02 | 0.114 / 0.093 | — |
| sh2930 (shift at 29–30 only) | 0 | 0 / 0 | 1.00 | 14 | ✓ | +0.02 / −0.41 | 0.45 | — | — |
| sh0_28 (shift at 0–28 only) | 13 | 16 / 26 | 0.38 | 0 | ✗ | +0.15 / +0.33 | −0.12 | — | — |
| cpar16_sm (M9) | 27 | 39 / 12 | 0.60 | 12 | ✗ | +0.23 / +0.12 | 0.09 | 0.33 / 0.22 | — / 2.40 |
| **cperp16_sm** (M9) | **39** | 39 / 0 | 1.00 | 14 | ✓ | +0.27 / −0.53 | 0.72 | 0.67 / 0.42 | — / 1.59 |
| crand16_sm (M9 seed) | 7 | 32 / 28 | 0.52 | 5 | ✗ | +0.34 / +0.35 | 0.00 | 0.004 / 0.002 | — / 26.4 |
| crand16_sm_s1 | 11 | 34 / 24 | 0.61 | 10 | ✗ | +0.34 / +0.36 | 0.03 | 0.004 / 0.002 | — / 29.2 |
| crand16_sm_s2 | 4 | 31 / 31 | 0.46 | 6 | ✗ | +0.35 / +0.35 | −0.01 | 0.004 / 0.001 | — / 33.1 |
| crand16_sm_s3 | 7 | 32 / 29 | 0.39 | 3 | ✗ | +0.33 / +0.38 | −0.02 | 0.004 / 0.002 | — / 26.5 |
| crand16_sm_s4 | 4 | 30 / 29 | 0.56 | 8 | ✗ | +0.33 / +0.36 | 0.01 | 0.004 / 0.002 | — / 30.2 |

- **Where c is nonzero:** the cpos29 + cpos30 energy share is 1.000 in every row (min = max = 1), so c is zero at the other 29 span positions. Zero-part share 0.935 in every rescaled row, as in M9.
- **Capped share:** 0 for every rescaled arm.
- **Change norm vs full:** 0.615–0.620 for every head, position, split and null arm (cs1 0.619). sh0_28 0.587 and sh2930 **0.053**: the common shift's energy sits almost entirely at positions 0–28.

## Finer gain at s = 1 (host + t (mid − h_B) ∓ ½ c)
| t | arm | S | J main / round | SPEC | C | change norm vs full |
|---|---|---|---|---|---|---|
| 0.6 | g06_1 | 13 | 13 / 0 | ✗ (frac 0.375) | −0.05 | 0.375 |
| 0.7 | g07_1 | 14 | 14 / 0 | ✓ | +0.16 | 0.437 |
| **0.8** | g08_1 | **26** | 26 / 0 | ✓ | +0.39 | 0.497 |
| 0.9 | g09_1 | 39 | 39 / 0 | ✓ | +0.57 | 0.558 |
| 1.0 | cs1 | 39 | 39 / 0 | ✓ | +0.60 | 0.619 |

- J_round is 0 at every t: the round source never flips on the shift alone plus contrast.
- The hosts switch on one at a time: 1fb5651c at t ≤ 0.6, 264c458d at 0.8 (1 at 0.7, 12 at 0.8), 4bcbaf15 at 0.9 (1 at 0.8). So GAIN_TFINE:0.8 is "two of three hosts", and t\* is a per-host threshold, not a common one.

## Per-host S
| host | full | cs1 | chW_sm | ch10_sm | chWx10_sm | chR_sm | ch10 (M9) | cpos29 | cpos30 | sh2930 | sh0_28 | g06 / g07 / g08 / g09 | cpar | cperp | null s0 / s1 / s2 / s3 / s4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1fb5651c | 13 | 13 | 13 | 13 | 13 | 0 | 13 | 13 | 3 | 0 | 13 | 13 / 13 / 13 / 13 | 13 | 13 | 6 / 8 / 4 / 5 / 4 |
| 264c458d | 10 | 13 | 13 | 13 | 13 | 0 | 0 | 13 | 0 | 0 | 0 | 0 / 1 / 12 / 13 | 1 | 13 | 0 / 0 / 0 / 0 / 0 |
| 4bcbaf15 | 11 | 13 | 13 | 13 | 13 | 0 | 12 | 13 | 0 | 0 | 0 | 0 / 0 / 1 / 13 | 13 | 13 | 1 / 2 / 0 / 1 / 0 |
| 75642418 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0 | 0 | 0 / 1 / 0 / 1 / 0 |
| 2c9118bb | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0 | 0 | 0 / 0 / 0 / 0 / 0 |
| 8ae85754 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0 | 0 | 0 / 0 / 0 / 0 / 0 |
| 1c7158b6 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0 | 0 | 0 / 0 / 0 / 0 / 0 |
| 2a4f596d | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 / 0 / 0 | 0 | 0 | 0 / 0 / 0 / 0 / 0 |

## Reading, with its limits
1. **The writer-head result is not an energy effect (CONTRAST_SM_IN_WRITER_HEADS+H10+WX10).**
   - At the same per-position norm ‖c‖, any writer slice repairs all three responsive hosts: heads 8–14 (S 39, C 0.71), head 10 alone (S 39, C 0.43), and heads 8–14 without head 10 (S 39, C 0.57).
   - The other nine heads' slice at the same norm gives S 0 and is reversed: dM_round > dM_main in every cell (frac 0.00), J 26 / 39. The reversal is also present unscaled in M9 (chR C −0.04), and grows with the rescale (C −0.09).
   - M9's ch10 failure (S 25, not SPEC; 264c458d 0) was a size effect: head 10's slice holds 31 % of c's energy; rescaled by α ≈ 1.7 it repairs 264c458d too and becomes specific.
   - So the effective direction of the round contrast is in the writer heads' `o_proj`-input coordinates, and it is redundant across them: head 10 alone and the rest without head 10 each suffice at full size. This sits with M3, where no single head sufficed for the full patch and drop10 was the most damaging single drop.
   - Limit: "same norm" is matched to ‖c‖, so the head-10 and non-writer slices are amplified (α up to 3.6 and 2.8). Head 10's C (0.43) and frac (0.78) are the weakest among the writer arms, close to the SPEC line.
2. **The contrast acts at position 29, under unequal sizes (CONTRAST_AT_P29).**
   - c kept at position 29 alone reproduces cs1 (S 39, J 39 / 0, C 0.66). c at position 30 alone gives S 3 (all on 1fb5651c), not specific.
   - Position 29 holds 89 % of c's energy (min 88 %), position 30 11 %. As fixed in the prereg, and as the A573 CPU audit shows with a pure-amplitude threshold counterexample, this verdict cannot by itself separate "position 29" from "the bigger part". The supported statement is: under the unmatched patch, the contrast's effect comes from the changed-token position.
3. **The common shift is needed at both the earlier positions and the contrast positions (SHIFT_NEEDS_ALL_POSITIONS).**
   - Shift only at 29–30 plus the full contrast: J 0 / 0 (it is SPEC in direction, C 0.45, but flips nothing). Shift only at 0–28: S 13, all on 1fb5651c, and it flips more round rows (26) than main rows (16).
   - So the round-specific repair needs the shift at the contrast positions (without it, round rows flip too), and the flip needs the shift at the context positions.
   - Limit: also not size-matched. Positions 29–30 carry only 5 % of the shift's change norm against 59 % for 0–28; "needs all positions" may partly be "needs enough shift".
4. **The 5-seed null fails, so the subspace split stays unresolved (SPLIT_NULL5 fails; CONTRAST_OUTSIDE_COMMON_SUBSPACE_UNRESOLVED).**
   - Random 16-dim frames, rescaled to ‖c‖, give S 4–11 (median 7); none is specific (frac 0.39–0.61, C −0.02 to 0.03).
   - 27 of the 33 null repairs are on host 1fb5651c, which flips under almost any contrast-sized push on the common shift. On 264c458d the null is 0 in all 5 seeds, against cperp 13 and cpar 1. On 4bcbaf15 the null is 0–2 against 13 for both parts.
   - So by host: on 264c458d the outside-subspace part is needed and the inside part does not work; on 4bcbaf15 both parts work; on 1fb5651c nothing separates from the null. The pooled verdict cannot be resolved by the median rule, and the per-host reading rests on one host.
   - The null also produced 2 repairs (seeds s1, s3) on host 75642418, which no pooled arm in M6–M10 has repaired.
   - As A574 notes, even a passing median gate would not show that random directions rarely repair; a failing one is the conservative outcome here.
   - Random frames keep 0.4 % of c's energy, so their rescale factor is 26–33; the null is a large push in a direction c barely uses, not an energy-share-matched frame.
5. **The contrast's threshold in t is per host (GAIN_TFINE:0.8).**
   - On the 0.1 grid, 1fb5651c already repairs at 0.6, 264c458d switches between 0.7 and 0.8, and 4bcbaf15 between 0.8 and 0.9. The pooled t\* = 0.8 is the step where the second host switches, on the SUF edge (26 vs 25.5; 0.9 in 3/14 splits).
   - The specificity is perfect at every t (J_round 0), so what grows with t is only how many hosts flip, not specificity.
6. **What M10 does not change:** the pooled-contrast arms repair only hosts 1fb5651c, 264c458d and 4bcbaf15. Hosts 75642418, 2c9118bb and 8ae85754 need the cell's own common part (M8 tp16 / xdlr). Hosts 1c7158b6 and 2a4f596d are repaired by nothing in M3–M10.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.
- All M10 arms except `full` are pooled-donor arms, effectively 8 host replicates with 3 that respond. Per-host S is the honest unit, and every pooled verdict here rests on hosts 1fb5651c, 264c458d and 4bcbaf15.
- Neither the position arms (Q2) nor the shift-location arms (Q3) are size-matched.

## Where the M1–M10 chain now stands
- M1: the span's L11 representation carries a signed, round-specific conflict evaluation.
- M2: L11 full attention writes it.
- M3: heads 8–14 write it together, with head 10 most necessary.
- M4: the write reads mainly from the other messages and the state header, not the partner vote.
- M5: the context-wide (BULK) part carries the evaluation in its direction, and a third donor's BULK keeps 51/51.
- M6: one pooled donor BULK component repairs 39/104; not captured by a ≤ 64-dimensional raw basis.
- M7: the repair splits into a conflict-raising part common to both source kinds and a small round contrast that does nothing alone.
- M8: a 16-dim common part plus one shared contrast vector (tp16 S 44); the contrast's effect is non-additive with the common shift.
- M9: the contrast is read only on a (nearly) full common shift; it works through the writer heads' slice; at matched size its active part lies outside the 16-dim common subspace (one-seed null marginal).
- **M10:**
  - The writer-head location of the contrast survives size matching, and is redundant within the writer heads (head 10 alone, or heads 8–14 without 10, each suffice). The non-writer slice at the same size pushes the wrong way.
  - The contrast lives at span positions 29–30 only, and its effect comes from position 29 (the token ROUND changes), though position 29 also holds 89 % of its energy.
  - The common shift is needed both at the contrast positions (for specificity) and at the earlier positions (for the flip).
  - The subspace split stays unresolved under 5 seeds; by host it is clear on 264c458d only.
  - The gain threshold is per host: 0.6 / 0.8 / 0.9 for the three responsive hosts.

## Suggested M11 (not frozen)
- **Size-matched positions:** c at position 30 alone rescaled to ‖c‖ (and position 29 scaled down to position 30's norm), plus a dose curve at each position, to answer A573's amplitude-threshold counterexample.
- **Size-matched shift location:** the shift at 29–30 rescaled to the 0–28 part's norm (or matched per token), to separate location from amount.
- **A split null that is not decided by host 1fb5651c:** report and decide per host (264c458d / 4bcbaf15), and use more seeds or an energy-share-matched random frame instead of the large-α 16-dim frame.
- **The non-writer reversal:** chR_sm pushes the round source toward repair in all cells. A sign-flipped chR slice or chR at larger scale would show whether the non-writer heads carry an opposing (or default-accept) component of the contrast.
- Pending separately: replication of the M2/M3 chain on SecJev-0.8B, and the non-pooled hosts (75642418, 2c9118bb, 8ae85754), which none of the pooled-contrast arms reach.
