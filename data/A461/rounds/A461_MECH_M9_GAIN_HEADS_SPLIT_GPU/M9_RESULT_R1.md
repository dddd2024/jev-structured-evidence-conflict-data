# A461-MECH-M9 R1: result (how does the pooled round contrast's effect grow with the common shift, which heads' slice carries it, and does it lie in the common subspace?)

**Run:**
- 4828/4828 kev-4B forwards in 38 batches (37 × 128 + 92); 0 denied; one model load; elapsed 7259 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`.
- Raw blob `c74e5117da511f7d0be1503746b752f1a41c62b8`.
- The run follows prereg 7124fd7 under the standing GPU authorization. The pre-model gate passed (`COMPLETE_A461_MECH_M9_PRE_MODEL_GATE`, saved as `M9_GPU_R1/pre_model_gate_receipt.json`). There was a single ledger attempt (`A461_MECH_M9_GPU_20261029_R1`, 4828 reserved).

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- The size gate of the rescaled contrast parts passed in the run.
- The captures stay on the server under `M9_GPU_RUNS/ATTEMPT_R1/captures`. All files match the run's `SHA256SUMS` there. Every non-capture file was fetched here and verified against the same `SHA256SUMS`.

**Analysis:** `A461_mech_m9_analysis_v1.py` (blob 59badbec, frozen before the run), run automatically by the server launch script after the receipt read COMPLETE (exit 0). Output: `M9_ANALYSIS_R1/m9_analysis.json` (sha256 8f29fe31…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51, 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 rows bitwise equal to M6; cs0 / cs05 / cs1 / cs2 each 208/208 rows bitwise equal to M8, S = 0 / 38 / 39 / 36 |
| M7 rcD replay (reported) | g0_2 = M7 rcD bitwise in 208/208 rows; S 0, C 0.0687 in both |
| **Q1 gain shape** | **GAIN_MIXED**: L(1) = 0.007 (< 0.3), L(2) = 0.592 (in [0.3, 0.7]); Q(1) = −0.033, Q(2) = 0.307 |
| **Q1 minimal shift** | **GAIN_TMIN:1.0**: at s = 1, no t < 1 is SUF. Over the whole grid, SUF holds only for cs05 / cs1 / cs2 |
| **Q2 heads** | **CONTRAST_IN_WRITER_HEADS** (no +H10): chW S 39, SPEC; chR S 0; ch10 S 25, not SPEC (frac 0.50) |
| SPLIT_NULL (crand16_sm S ≤ 5, not SPEC) | **fails**: S 7, not SPEC (frac 0.52) |
| **Q3 split** | **CONTRAST_OUTSIDE_COMMON_SUBSPACE_UNRESOLVED**: cperp16_sm S 39, SPEC; cpar16_sm S 27, not SPEC (frac 0.60) |

**Leave one donor group out:** 14/14 splits give GAIN_MIXED, GAIN_TMIN:1.0 and CONTRAST_IN_WRITER_HEADS. L(1) ranges over [−0.032, 0.047] and L(2) over [0.579, 0.608]. The split verdict is _UNRESOLVED in 13/14 splits. In the remaining split the null holds and the verdict is a plain CONTRAST_OUTSIDE_COMMON_SUBSPACE. cs05 drops out of the SUF set in 2/14 splits (run-140 and run-212, as in M8).

## Gain grid (S / C; J main / round; host + t (mid − h_B) ∓ (s/2) c)
| t \ s | 0 | ½ | 1 | 2 |
|---|---|---|---|---|
| 0 | — (host) | 0 / −0.07; 0 / 0 | 0 / −0.15; 0 / 0 | 0 / +0.07; 0 / 0 (= M7 rcD) |
| ¼ | 0 / 0; 0 / 0 | 0 / −0.09; 0 / 0 | 0 / −0.17; 0 / 0 | 13 / +0.40; 13 / 0 |
| ½ | 0 / 0; 0 / 0 | 0 / −0.11; 0 / 2 | 13 / −0.14; 13 / 0 (frac 0.375) | 13 / +0.71; 13 / 0 |
| 1 | 0 / 0; 28 / 28 | **38** / +0.16; 39 / 1 | **39** / +0.60; 39 / 0 | **36** / +1.15; 36 / 0 |

- **The common shift alone flips nothing below t = 1.** At t ≤ ½ (s = 0) J is 0 / 0. At t = 1 it is 28 / 28.
- **Every S of 13 below t = 1 is host 1fb5651c alone** (13 cells, one host). Hosts 264c458d and 4bcbaf15 need t = 1.
- **C below t = 1 is negative at s ≤ 1**: the median main source is moved slightly less toward conflict than the round source. It turns positive only at s = 2, and there it grows with t: 0.07, then 0.40, 0.71, 1.15.
- **Change norms relative to full:** t = ¼ 0.15–0.19, t = ½ 0.31–0.33, t = 1 0.61–0.63, g0_* 0.01–0.04.

## Head and split arms (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority; C = median dM_main − dM_round)
| arm | S | J main / round | frac | grp | SPEC | median dM main / round | C | energy share of c (median / min) |
|---|---|---|---|---|---|---|---|---|
| cs1 (all heads, = meanD_host) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.66 | 0.60 | 1 |
| **chW** (heads 8–14) | **39** | 39 / 0 | 1.00 | 14 | ✓ | +0.26 / −0.61 | 0.66 | 0.82 / 0.82 |
| ch10 (head 10) | 25 | 39 / 14 | 0.50 | 4 | ✗ | +0.28 / +0.34 | −0.01 | 0.31 / 0.30 |
| chR (heads 0–7, 15) | 0 | 26 / 39 | 0.00 | 0 | ✗ | +0.33 / +0.36 | −0.04 | 0.18 / 0.17 |
| cpar16_sm (in U₁₆, rescaled) | 27 | 39 / 12 | 0.60 | 12 | ✗ | +0.23 / +0.12 | 0.09 | 0.33 / 0.22 |
| **cperp16_sm** (outside U₁₆, rescaled) | **39** | 39 / 0 | 1.00 | 14 | ✓ | +0.27 / −0.53 | 0.72 | 0.67 / 0.42 |
| crand16_sm (null, rescaled) | 7 | 32 / 28 | 0.52 | 5 | ✗ | +0.34 / +0.35 | 0.00 | 0.004 / 0.002 |

- **Where c is nonzero:** at only 2 of the 31 span positions (zero-part share 0.935 in every split row). The size-matched parts are rescaled there only, and α is 0 elsewhere.
- **α (max over rows):** cpar 2.40, cperp 1.59, crand 26.4 (uncapped). No position hit the cap.
- **Change norm vs full:** 0.615–0.619 for all head and split arms, against 0.619 for cs1.

## Per-host S
| host | full | meanD_host / cs1 | cs05 | g05_1 | g025_2 / g05_2 | chW | ch10 | chR | cpar16_sm | cperp16_sm | crand16_sm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1fb5651c | 13 | 13 | 13 | 13 | 13 / 13 | 13 | 13 | 0 | 13 | 13 | 6 |
| 264c458d | 10 | 13 | 12 | 0 | 0 / 0 | 13 | 0 | 0 | 1 | 13 | 0 |
| 4bcbaf15 | 11 | 13 | 13 | 0 | 0 / 0 | 13 | 12 | 0 | 13 | 13 | 1 |
| 75642418 | 7 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2c9118bb | 5 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 8ae85754 | 4 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1c7158b6 | 1 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2a4f596d | 0 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Reading, with its limits
1. **The contrast is gated by the full common shift; the shape is not a simple product (GAIN_MIXED, GAIN_TMIN:1.0).**
   - At the M8 contrast size (s = 1), half the common shift gives essentially none of the effect (L(1) = 0.007), so at s = 1 this is a late threshold.
   - At twice the contrast (s = 2) half the shift gives 59 % (L(2) = 0.59), which is in the bilinear band.
   - So the threshold on t moves down as the contrast grows. A product C ∝ t·s does not fit, because C at t ≤ ½ is negative for s ≤ 1. Neither does a fixed threshold. The preregistered verdict is MIXED and stable in 14/14 splits.
   - The common shift is itself thresholded: it flips nothing at t ≤ ½ and 28 / 28 cells at t = 1.
   - Below t = 1, only host 1fb5651c (the most easily repaired host since M6) responds. The other two pooled-repairable hosts need the full shift.
   - Limit: the grid is 4 × 4 on 8 host replicates. The t\* = 1 result rests on hosts 264c458d and 4bcbaf15.
2. **The contrast acts through the writer heads' slice (CONTRAST_IN_WRITER_HEADS).**
   - Restricting c to the `o_proj`-input slices of heads 8–14 keeps the whole effect: S 39, J 39 / 0, C 0.66 ≥ cs1's 0.60.
   - The other nine heads' slice gives S 0, and their round rows flip like the main rows (J 26 / 39).
   - The writer slice holds 82 % of c's energy, so this is not size-matched (prereg limit). Still, it shows the contrast is effective in the same heads M3 found write the evaluation.
   - Head 10 alone (31 % of the energy) repairs hosts 1fb5651c and 4bcbaf15 but not 264c458d, and is not specific (J_round 14, frac 0.50). So head 10's slice is not enough by itself, and the contrast is spread over the writer group.
3. **At matched size, the part of c outside the common subspace repairs and the part inside does not, but the random-frame null is slightly above its bound (CONTRAST_OUTSIDE_COMMON_SUBSPACE_UNRESOLVED).**
   - cperp16_sm reproduces cs1 exactly in S (39, J 39 / 0, 3 hosts).
   - cpar16_sm, rescaled to the same per-position norm, gives S 27 and is not specific. It loses host 264c458d and leaves 12 round rows flipped.
   - The null (crand16_sm) gives S 7, of which 6 are on host 1fb5651c. It is not specific (frac 0.52, C 0.00), but it exceeds the preregistered S ≤ 5, so the verdict carries _UNRESOLVED. The null holds in 1 of the 14 leave-one-group-out splits.
   - Why the null is weak: crand's 16-frame keeps 0.4 % of c's energy, so its rescale factor reaches 26. Host 1fb5651c flips under almost any contrast-sized push on the common shift, as the t < 1 grid also shows.
   - So the specificity and the hosts 264c458d / 4bcbaf15 come from the part orthogonal to the 16-dim common basis. That part holds 67 % of c's energy (median; min 42 %).
   - Limit: c is nonzero at only 2 of 31 span positions, so the split, the head slices and the size matching all act on those 2 positions.
4. **What M9 does not change:** the pooled-contrast arms still repair only hosts 1fb5651c, 264c458d and 4bcbaf15. Hosts 75642418, 2c9118bb and 8ae85754 need the cell's own common part (M8 tp16 / xdlr). Hosts 1c7158b6 and 2a4f596d are repaired by nothing in M3–M9.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.
- All M9 arms except `full` are pooled-donor arms, effectively 8 host replicates with 3 that respond. Per-host S is the honest unit.

## Where the M1–M9 chain now stands
- M1: the span's L11 representation carries a signed, round-specific conflict evaluation.
- M2: L11 full attention writes it.
- M3: heads 8–14 write it together, with head 10 most necessary.
- M4: the write reads mainly from the other messages and the state header, not the partner vote.
- M5: the context-wide (BULK) part carries the evaluation in its direction, and a third donor's BULK keeps 51/51.
- M6: one pooled donor BULK component repairs 39/104; not captured by a ≤ 64-dimensional raw basis.
- M7: the repair splits into a conflict-raising part common to both source kinds and a small round contrast that does nothing alone.
- M8: a 16-dim common part plus one shared contrast vector (tp16 S 44); the contrast's effect is non-additive with the common shift.
- **M9:**
  - The contrast is read only once the common shift is (nearly) full. Its threshold on t drops as the contrast grows, so the interaction is neither a product nor a fixed threshold.
  - The contrast works through the writer heads 8–14's slice of the `o_proj` input, and not through the other heads; head 10 alone is not enough.
  - At matched size, its active part lies outside the 16-dim common subspace (with a marginal null: S 7 vs bound 5).
  - All of this rests on 3 responding hosts and on 2 span positions where c is nonzero.

## Suggested M10 (not frozen)
- **Size-matched head slices:** chW / chR / ch10 rescaled to ‖c‖ per position, to separate head location from energy share.
- **Position of the contrast:** identify the 2 span positions where c ≠ 0 (likely the round token and its successor). Test the contrast at each position alone on the common shift.
- **A stronger split null:** several random seeds, or a random frame matched in energy share to U₁₆, so that SPLIT_NULL is not decided by one seed's large rescale.
- **Threshold in t:** a finer grid t ∈ {0.6, 0.7, 0.8, 0.9} at s = 1 on hosts 264c458d / 4bcbaf15.
- Pending separately: replication of the M2/M3 chain on SecJev-0.8B.
