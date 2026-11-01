# A461-MECH-M11 R1: result (is the position-29 effect of the pooled round contrast more than its size, does the common shift need the context positions or only more shift, and does the subspace split hold per host?)

**Run:**
- 5244/5244 kev-4B forwards in 41 batches (40 × 128 + 124); 0 denied; one model load; elapsed 7862 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`.
- Raw blob `393f0d6e7d4a698db15f9217202039c52ad663a8`.
- The run follows prereg b5d1756 under the standing GPU authorization (freeze also pre-authorized by the user on 2026-10-29). The pre-model gate passed (`COMPLETE_A461_MECH_M11_PRE_MODEL_GATE`, saved as `M11_GPU_R1/pre_model_gate_receipt.json`). There was a single ledger attempt (`A461_MECH_M11_GPU_20261030_R1`, 5244 reserved, 5244 consumed).

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- The size gates of the swapped-norm contrast and the rescaled shift passed in the run (fail-closed at 1e-3 relative). No row hit the cap of 10 (capped share 0 for every rescaled arm).
- The captures stay on the server under `M11_GPU_RUNS/ATTEMPT_R1/captures`. Every non-capture file was fetched here and verified against the run's `SHA256SUMS` (44/44). The receipt, run log, pre-model gate receipt and analysis JSON match the server copies by sha256.

**Analysis:** `A461_mech_m11_analysis_v1.py` (blob 31dbc6fc, frozen before the run), run automatically by the server launch script after the receipt read COMPLETE (exit 0, 2026-10-30 13:08 +08:00). Output: `M11_ANALYSIS_R1/m11_analysis.json` (sha256 019272f0…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51, 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 rows bitwise equal to M6; cs1 / chR_sm / cpar16_sm / cperp16_sm / cpos29 / cpos30 / sh2930 / sh0_28 each 208/208 rows bitwise equal to M10, S = 39 / 0 / 27 / 39 / 39 / 3 / 0 / 13 |
| **Q1 position at swapped norm** | **P30_INERT_AT_P29_NORM**: cpos29_n30 S 25, not SPEC; cpos30_n29 S 1, not SPEC |
| **AMPLITUDE_ONLY** | **AMPLITUDE_ONLY_EXCLUDED** (not SUF(cpos30_n29)) |
| Q1 dose | **POS29_SMIN:0.5** (s ¼ / ½ / 1: S 13 / 38 / 39); **POS30_SMIN:NONE** (s 1 / 2 / 4: S 3 / 2 / 0) |
| **Q2 shift at matched size** | **SHIFT_NEEDS_CONTEXT_POSITIONS**: sh2930_tm and sh2930_pt both S 0 (J 0 / 0) |
| Q2 dose | **SHIFT2930_UMIN:NONE** (u 1 / 2 / 4: S 0 / 0 / 0, J 0 / 0 throughout) |
| **Q3 split by host** | **SPLIT_BY_HOST:1fb5651c=BOTH,264c458d=BOTH,4bcbaf15=BOTH** (see the 264c458d caveat below) |
| SPLIT_NULL10 (median S ≤ 5 over 10 frames, none SPEC) | **fails**: S 7 / 11 / 4 / 7 / 4 (M10) and 8 / 4 / 7 / 8 / 9 (new), median 7, max 11; none SPEC |
| pooled subspace verdict, re-applied | **CONTRAST_OUTSIDE_COMMON_SUBSPACE_UNRESOLVED** |

**Leave one donor group out:**
- 14/14 splits give AMPLITUDE_ONLY_EXCLUDED, P30_INERT_AT_P29_NORM, POS30_SMIN:NONE, SHIFT_NEEDS_CONTEXT_POSITIONS, SHIFT2930_UMIN:NONE and the _UNRESOLVED subspace verdict (null median 6–7 in every split).
- POS29_SMIN is 0.5 in 12/14 splits and 1.0 in 2/14 (run-140, run-212): s = ½ sits on the SUF/SPEC edge (frac exactly 0.75).
- SPLIT_BY_HOST is BOTH/BOTH/BOTH in 13/14 splits; in the run-337 split 264c458d reads OUTSIDE.

## All arms (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority; C = median dM_main − dM_round)
| arm | S | J main / round | frac | grp | SPEC | median dM main / round | C | factor (median; range) | change norm vs full |
|---|---|---|---|---|---|---|---|---|---|
| full (M3 anchor) | 51 | 58 / 7 | 0.99 | 14 | ✓ | +0.35 / −0.37 | 0.71 | — | 1 |
| meanD_host = cs1 | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.66 | 0.60 | — | 0.619 |
| cpos29 (M10) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.25 / −0.66 | 0.66 | — | 0.617 |
| **cpos29_s05** | **38** | 39 / 1 | 0.75 | 14 | ✓ | +0.29 / +0.19 | 0.17 | ½ | 0.615 |
| **cpos29_n30** (29 at ‖c₃₀‖) | **25** | 39 / 14 | 0.63 | 14 | ✗ | +0.30 / +0.35 | 0.04 | 0.36; 0.32–0.37 | 0.614 |
| cpos29_s025 | 13 | 39 / 26 | 0.61 | 13 | ✗ | +0.31 / +0.37 | 0.01 | ¼ | 0.614 |
| cpos30 (M10) | 3 | 30 / 27 | 0.24 | 0 | ✗ | +0.34 / +0.35 | −0.02 | — | 0.615 |
| **cpos30_n29** (30 at ‖c₂₉‖) | **1** | 18 / 26 | 0.17 | 0 | ✗ | +0.31 / +0.35 | −0.05 | 2.79; 2.69–3.13 | 0.620 |
| cpos30_s2 | 2 | 28 / 26 | 0.21 | 0 | ✗ | +0.33 / +0.35 | −0.03 | 2 | 0.616 |
| cpos30_s4 | 0 | 1 / 28 | 0.13 | 0 | ✗ | +0.27 / +0.35 | −0.08 | 4 | 0.626 |
| sh2930 (M10, u 1) | 0 | 0 / 0 | 1.00 | 14 | ✓ | +0.02 / −0.41 | 0.45 | 1 | 0.053 |
| **sh2930_pt** (per-token norm) | **0** | 0 / 0 | 0.75 | 14 | ✓ | −0.01 / −0.21 | 0.22 | 0.84; 0.68–1.02 | 0.049 |
| sh2930_u2 | 0 | 0 / 0 | 0.88 | 14 | ✓ | +0.00 / −1.02 | 1.08 | 2 | 0.099 |
| **sh2930_tm** (total norm) | **0** | 0 / 0 | 0.98 | 14 | ✓ | −0.83 / −1.23 | 0.26 | 3.18; 2.58–3.87 | 0.156 |
| sh2930_u4 | 0 | 0 / 0 | 0.89 | 14 | ✓ | −1.13 / −1.32 | 0.14 | 4 | 0.192 |
| sh0_28 (M10) | 13 | 16 / 26 | 0.38 | 0 | ✗ | +0.15 / +0.33 | −0.12 | 1 | 0.587 |
| chR_sm (M10) | 0 | 26 / 39 | 0.00 | 0 | ✗ | +0.32 / +0.38 | −0.09 | — | 0.620 |
| cpar16_sm (M10) | 27 | 39 / 12 | 0.60 | 12 | ✗ | +0.23 / +0.12 | 0.09 | — | 0.619 |
| cperp16_sm (M10) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.27 / −0.53 | 0.72 | — | 0.618 |
| crand16_sm_s5 … s9 | 8 / 4 / 7 / 8 / 9 | 30–34 / 27–29 | 0.43–0.54 | 3–8 | ✗ | ≈ +0.35 / +0.36 | −0.02 to 0.01 | α max 27–39 | 0.618 |

- **Factors:** the swapped-norm factor ‖c₂₉‖ / ‖c₃₀‖ is 2.69–3.13 per row (median 2.79), inside the prereg's expected range and far below the cap. The total-norm shift factor ‖d₀₋₂₈‖ / ‖d₂₉,₃₀‖ is 2.58–3.87 (median 3.18); the per-token factor is 0.68–1.02 (median 0.84), i.e. per token the shift at 29–30 is already about as large as at 0–28.
- **Change norm vs full** is the mean per-position change at the span, so a local shift has a small value even when its total norm matches.

## Per-host S
| host | full | cs1 | cpos29 s ¼ / 0.36 (n30) / ½ / 1 | cpos30 s 1 / 2.8 (n29) / 2 / 4 | sh2930 u 1 / 0.84 (pt) / 2 / 3.2 (tm) / 4 | sh0_28 | cpar | cperp | null (10 frames) | null max |
|---|---|---|---|---|---|---|---|---|---|---|
| 1fb5651c | 13 | 13 | 13 / 13 / 13 / 13 | 3 / 1 / 2 / 0 | 0 / 0 / 0 / 0 / 0 | 13 | 13 | 13 | 6 8 4 5 4 7 4 7 7 7 | 8 |
| 264c458d | 10 | 13 | 0 / 0 / 12 / 13 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 | 0 | 1 | 13 | all 0 | 0 |
| 4bcbaf15 | 11 | 13 | 0 / 12 / 13 / 13 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 | 0 | 13 | 13 | 1 2 0 1 0 1 0 0 0 1 | 2 |
| 75642418 | 7 | 0 | 0 / 0 / 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 1 0 1 0 0 0 0 1 1 | 1 |
| 2c9118bb | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | all 0 | 0 |
| 8ae85754 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | all 0 | 0 |
| 1c7158b6 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | all 0 | 0 |
| 2a4f596d | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | all 0 | 0 |

## Reading, with its limits
1. **The position-29 effect is not size alone (AMPLITUDE_ONLY_EXCLUDED; P30_INERT_AT_P29_NORM).**
   - c kept at position 30 and scaled up to the norm c has at 29 (factor ≈ 2.8) repairs 1 cell; ×2 and ×4 give 2 and 0. The A573 pure-amplitude threshold predicted SUF here; it does not hold.
   - Larger c at 30 pushes the wrong way: J_main falls from 30 (s 1) to 1 (s 4) while J_round stays 26–28, and frac falls to 0.13. Position 30's contrast, on its own, works against the round-specific repair, like the non-writer head slice in M10.
   - As fixed in the prereg, this separates position and direction together from size, not position from direction: c₃₀ points elsewhere than c₂₉.
   - c at 29 shrunk to position 30's norm (factor 0.36) still repairs 1fb5651c and 4bcbaf15 (S 13 / 12) but not 264c458d (0), and the round source flips too (J_round 14), so it is not specific (frac 0.63). The P30_INERT_AT_P29_NORM label is the prereg's name for "neither swapped arm is SUF"; the substantive asymmetry is that c₂₉ at c₃₀'s size keeps most of its effect (S 25) while c₃₀ at c₂₉'s size has none (S 1).
2. **The position-29 dose has per-host thresholds (POS29_SMIN:0.5).**
   - S rises 13 → 25 → 38 → 39 at s ¼ / 0.36 / ½ / 1. 1fb5651c flips at s ≤ ¼; 4bcbaf15 between ¼ and 0.36; 264c458d between 0.36 and ½.
   - Specificity grows more slowly than S: at s ½ frac is exactly 0.75 (the SPEC line), J_round 1, C 0.17; at s 1 frac 1.00, C 0.66. So POS29_SMIN:0.5 is on the edge (1.0 in 2/14 splits).
   - The host order differs from M10's gain threshold in t (1fb5651c ≤ 0.6, 264c458d 0.8, 4bcbaf15 0.9): 4bcbaf15 needs the most common shift but less contrast than 264c458d. The two thresholds are not one host-level "ease".
3. **The common shift must reach the context positions; more shift at 29–30 does not substitute (SHIFT_NEEDS_CONTEXT_POSITIONS; SHIFT2930_UMIN:NONE).**
   - With the full contrast, the shift at 29–30 alone gives J 0 / 0 at every size tried: per-token matched (0.84), u 1, 2, matched total norm (3.18) and u 4. No cell flips for either source.
   - The direction is right (frac 0.75–0.98, C 0.14–1.08, SPEC in every shift arm), but a larger local shift lowers both margins: median dM_main goes from +0.02 (u 1) to −0.83 (total-norm) and −1.13 (u 4). So M10's SHIFT_NEEDS_ALL_POSITIONS is not an amount effect. The shift at 29–30 alone cannot raise the conflict margin, and adding more of it lowers the margin.
   - Together with M10's sh0_28 (S 13, non-specific, 1fb5651c only): the flip needs the shift at the context positions, and the specificity needs it at the contrast positions.
   - Limit: "total norm matched" puts a per-token push about 3× larger than the model sees at 29–30; the margin drop at u ≥ 3 may be an off-distribution effect. The per-token-matched arm (no such push) also flips nothing.
4. **The subspace split by host (SPLIT_BY_HOST: BOTH on all three hosts; SPLIT_NULL10 fails; pooled verdict stays _UNRESOLVED).**
   - The 10-frame null gives pooled S 4–11 (median 7), none SPEC; 59 of the 69 null repairs are on 1fb5651c, 6 on 4bcbaf15 and 4 on 75642418.
   - **1fb5651c:** cpar and cperp 13 each, null max 8. Both beat the null, but this host flips under almost any contrast-sized push (null 4–8 of 13, cpos29 at s ¼ 13, sh0_28 13), so it says little about direction.
   - **4bcbaf15:** cpar and cperp 13 each, null max 2. Both parts work on this host, clearly above the null.
   - **264c458d:** cperp 13, cpar 1, null 0 in all 10 frames. The preregistered rule (strictly greater than null_max) labels it BOTH because cpar's single cell exceeds a null max of 0. Substantively the outside-subspace part works on this host and the inside part does not (OUTSIDE in the run-337 split). The verdict is reported as frozen; the reading is "OUTSIDE on 264c458d, with a one-cell rule artifact".
   - So the per-host answer is: outside part sufficient on all three hosts; inside part sufficient on 4bcbaf15 (and the uninformative 1fb5651c) but not on 264c458d. There is no host-independent "the contrast lives outside the common subspace".
   - Limit: the null frames keep 0.4 % of c's energy (α up to 27–39); they are a large push in a direction c barely uses, not an energy-share-matched frame.
5. **What M11 does not change:** the pooled-contrast arms repair only hosts 1fb5651c, 264c458d and 4bcbaf15. Hosts 75642418, 2c9118bb and 8ae85754 need the cell's own common part (M8 tp16 / xdlr); 75642418 also picked up 4 null repairs across the 10 frames. Hosts 1c7158b6 and 2a4f596d are repaired by nothing in M3–M11.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.
- All M11 arms except `full` are pooled-donor arms, effectively 8 host replicates with 3 that respond. Per-host S is the honest unit, and every pooled verdict rests on hosts 1fb5651c, 264c458d and 4bcbaf15; 1fb5651c is nearly uninformative about direction.

## Where the M1–M11 chain now stands
- M1–M9 as in M10_RESULT_R1.
- M10: the writer-head location of the contrast survives size matching; c lives at span positions 29–30 and acts from 29 (unmatched); the shift is needed at all positions (unmatched); the split is unresolved; the gain threshold is per host.
- **M11:**
  - The position-29 effect is position-plus-direction, not size: c at 30 scaled to c₂₉'s norm does nothing, and grows harmful with size; c at 29 scaled down to c₃₀'s norm keeps most of its effect on two hosts.
  - The contrast threshold at 29 is per host (¼ / 0.36 / ½), in a different host order than the gain threshold in t.
  - The common shift must reach the context positions 0–28; the shift at 29–30 alone flips nothing at any size, and more of it lowers the margin.
  - The outside-subspace part of c works on all three responsive hosts; the inside part works on 4bcbaf15 but not on 264c458d. The pooled split stays unresolved under a 10-frame null that host 1fb5651c dominates.

## Suggested next steps (not frozen)
- **Position 30 as an opposing component:** c₃₀ at larger size suppresses the main flip (J_main 30 → 1). Testing −c₃₀ (sign-flipped) on top of cs1 or cpos29 would show whether position 30 carries a counter-signal and whether removing it sharpens specificity.
- **Context-position shift structure:** which of positions 0–28 must carry the shift (e.g. state header vs other messages, following M4's reading), at matched per-token size.
- **An energy-share-matched null and a host-level design for the split:** random frames matched to c's energy share in 16 dims, decided on 264c458d and 4bcbaf15, with 1fb5651c reported separately.
- Pending separately: replication of the M2/M3 chain on SecJev-0.8B, and the non-pooled hosts (75642418, 2c9118bb, 8ae85754).
