# A461-MECH-M13 R1: result (is the common shift at the author and block lines enough, and does tilting the round contrast toward the common subspace work against the repair beyond a random tilt?)

**Run:**
- 7116/7116 kev-4B forwards in 56 batches (55 × 128 + 76); 0 denied; one model load; elapsed 10708 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`.
- Raw blob `cdbf677bd2b89d487045b104af040f2e39fcf5a3`.
- The run follows prereg 3a24afb under the standing GPU authorization (freeze pre-authorized by the user). The pre-model gate passed (`COMPLETE_A461_MECH_M13_PRE_MODEL_GATE`, saved as `M13_GPU_R1/pre_model_gate_receipt.json`). There was a single ledger attempt (`A461_MECH_M13_GPU_R1`, 7116 reserved, 7116 consumed).

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- The tilt gate (c's component along c and the tilt norm, fail-closed at 1e-6) passed on every tilt and null row; max error 0.0 at the recorded precision.
- On real activations r is large:
  - median energy share 0.219 (range 0.156–0.248) of ‖c‖²;
  - median ‖r‖/‖c‖ 0.46;
  - c's 16-dim projection holds a median 0.33 of its energy.
- The tilt arms have energy 1 + λ² r_share as planned (λ ±1: median 1.219; λ +2: 1.876). The nulls keep r's norm, and their median cosine to r is about 0 (|median| ≤ 0.021).
- The captures stay on the server under `M13_GPU_RUNS/ATTEMPT_R1/captures`. The run's `SHA256SUMS` checks clean on the server. Every non-capture file was fetched here and matches the server by sha256 (59/59, plus the run log and the pre-model gate receipt). `M13_GPU_R1/SHA256SUMS` lists the local copies.

**Analysis:** `A461_mech_m13_analysis_v1.py` (blob 76489a54, frozen before the run), run automatically by the server launch script after the receipt read COMPLETE (exit 0, 2026-10-31 00:49 +08:00). Output: `M13_ANALYSIS_R1/m13_analysis.json` (sha256 35a5a0d4…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51, 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 bitwise equal to M6; cs1 / cs_s05 / cs_s025 / cpar16_sm / sh_fBLOCK / sh_xAUTH / sh_xBLOCK each 208/208 bitwise equal to M12, S = 39 / 38 / 13 / 27 / 18 / 26 / 20 |
| **Q1 sufficiency** | **SHIFT_AB_SUFFICES** (sh_fAB S 33, SPEC), **SHIFT_AB_C29_SUFFICES** (S 39), **SHIFT_AB_S05_SUFFICES** (S 39) |
| Q1 necessity | **SHIFT_AB_NEEDED** (sh_xAB S 13, not SUF) |
| Q1 location | **AB_LOCATION_SPECIFIC** (sh_fKR 13, sh_fRR 13, neither SUF) |
| Q1 by host | AB_BY_HOST: 264c458d = 13/13, 1fb5651c = 13/13, 4bcbaf15 = 7/13 |
| **Q2 tilt** | **TILT_NO_EFFECT** at s 1, ½ and ⅜ → **REM_NO_EFFECT** |
| **Q3 random-tilt null** | AT / AT on every responsive host at s ½ and ⅜ → **REM_DIRECTION_NOT_SPECIFIC** (a floor or ceiling on every host; see reading 2) |

**Leave one donor group out:** 14/14 splits give SHIFT_AB_SUFFICES, SHIFT_AB_C29_SUFFICES, SHIFT_AB_NEEDED, AB_LOCATION_SPECIFIC, TILT_NO_EFFECT at every s, REM_NO_EFFECT and REM_DIRECTION_NOT_SPECIFIC. SHIFT_AB_S05_SUFFICES holds in 12/14; in the other 2 it falls below SUF. sh_fAB on 4bcbaf15 is 6/12 in 7 splits, 7/12 in 6 and 7/13 in 1.

## All arms (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority; C = median dM_main − dM_round)
| arm | S | J main / round | frac | grp | SPEC | median dM main / round | C | change norm vs full |
|---|---|---|---|---|---|---|---|---|
| full (M3 anchor) | 51 | 58 / 7 | 0.99 | 14 | ✓ | +0.35 / −0.37 | 0.71 | 1 |
| meanD_host = cs1 | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.66 | 0.60 | 0.619 |
| cs_s05 | 38 | 39 / 1 | 0.75 | 14 | ✓ | +0.28 / +0.19 | 0.161 | 0.616 |
| cs_s0375 | 26 | 39 / 13 | 0.62 | 13 | — | +0.30 / +0.34 | 0.042 | 0.615 |
| cs_s025 | 13 | 39 / 26 | 0.60 | 12 | — | +0.31 / +0.37 | 0.007 | 0.614 |
| cpar16_sm (M11) | 27 | 39 / 12 | 0.60 | 12 | — | +0.23 / +0.12 | 0.094 | 0.619 |
| sh_fBLOCK (M12) | 18 | 18 / 0 | 1.00 | 14 | ✓ | +0.11 / −0.48 | 0.51 | 0.192 |
| sh_xAUTH (M12) | 26 | 26 / 0 | 1.00 | 14 | ✓ | +0.17 / −0.56 | 0.55 | 0.497 |
| sh_xBLOCK (M12) | 20 | 20 / 0 | 1.00 | 14 | ✓ | +0.14 / −0.48 | 0.51 | 0.481 |
| **sh_fAB** (0–12 + 29–30) | **33** | 33 / 0 | 1.00 | 14 | ✓ | +0.19 / −0.61 | 0.59 | 0.313 |
| **sh_fAB_c29** (c₃₀ weight 0) | **39** | 39 / 0 | 1.00 | 14 | ✓ | +0.20 / −0.62 | 0.64 | 0.311 |
| **sh_fAB_s05** | **39** | 39 / 0 | 0.75 | 14 | ✓ | +0.23 / +0.17 | 0.095 | 0.308 |
| sh_xAB (13–30) | 13 | 13 / 0 | 0.99 | 14 | ✓ | +0.13 / −0.50 | 0.50 | 0.362 |
| sh_fKR (13–24 + 29–30) | 13 | 13 / 0 | 0.98 | 14 | ✓ | +0.07 / −0.51 | 0.45 | 0.298 |
| sh_fRR (18–28 + 29–30) | 13 | 13 / 0 | 1.00 | 14 | ✓ | +0.08 / −0.45 | 0.48 | 0.258 |
| rem_m1 (c − r, s 1) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.26 / −0.67 | **0.80** | 0.620 |
| rem_p1 (c + r, s 1) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.21 / −0.57 | **0.45** | 0.619 |
| rem_p2 (c + 2r, s 1) | 37 | 37 / 0 | 1.00 | 14 | ✓ | +0.18 / −0.50 | **0.27** | 0.623 |
| rem_m1_s05 | 38 | 39 / 1 | 0.84 | 14 | ✓ | +0.29 / +0.19 | **0.225** | 0.617 |
| rem_p1_s05 | 38 | 39 / 1 | 0.74 | 14 | — | +0.27 / +0.19 | **0.128** | 0.615 |
| rem_p2_s05 | 38 | 39 / 1 | 0.71 | 13 | — | +0.26 / +0.18 | **0.109** | 0.616 |
| rnull_s05_1 … 5 | 38 each | 39 / 1 | 0.74–0.75 | 14 | ✓ for 1, 3, 5 | +0.28–0.30 / +0.18–0.20 | 0.139–0.174 | 0.616 |
| rem_m1_s0375 | 26 | 39 / 13 | 0.63 | 14 | — | +0.31 / +0.33 | **0.059** | 0.615 |
| rem_p1_s0375 | 26 | 39 / 13 | 0.60 | 11 | — | +0.29 / +0.34 | **0.024** | 0.614 |
| rnull_s0375_1 … 5 | 25 / 26 / 25 / 26 / 26 | 39 / 13–14 | 0.60–0.63 | 11–14 | — | +0.29–0.31 / +0.33–0.35 | 0.038–0.049 | 0.615 |

## Per-host S (13 cells per host; the other five hosts are 0 in every arm except `full`)
| arm | 1fb5651c | 264c458d | 4bcbaf15 |
|---|---|---|---|
| cs1 / cs_s05 / cs_s0375 / cs_s025 | 13 / 13 / 13 / 13 | 13 / 12 / **0** / 0 | 13 / 13 / 13 / 0 |
| sh_fAB / sh_fAB_c29 / sh_fAB_s05 | 13 / 13 / 13 | 13 / 13 / 13 | **7** / **13** / **13** |
| sh_xAB / sh_fKR / sh_fRR | 13 / 13 / 13 | 0 / 0 / 0 | 0 / 0 / 0 |
| sh_fBLOCK / sh_xAUTH / sh_xBLOCK (M12) | 13 / 13 / 13 | 5 / 13 / 6 | 0 / 0 / 1 |
| s 1: rem_m1 / cs1 / rem_p1 / rem_p2 | 13 each | 13 each | 13 / 13 / 13 / **11** |
| s ½: rem_m1 / cs / rem_p1 / rem_p2; nulls | 13 each; 13 ×5 | 12 each; 12 ×5 | 13 each; 13 ×5 |
| s ⅜: rem_m1 / cs / rem_p1; nulls | 13 each; 13 ×5 | 0 each; 0 ×5 | 13 each; 12 / 13 / 12 / 13 / 13 |
| cpar16_sm (M11) | 13 | 1 | 13 |

## Reading, with its limits
1. **The common shift at the author and block lines, with the contrast at the round value, is enough (SHIFT_AB_SUFFICES, SHIFT_AB_C29_SUFFICES, SHIFT_AB_NEEDED, AB_LOCATION_SPECIFIC).**
   - With the shift only at positions 0–12 plus 29–30 and c kept only at 29, all three responsive hosts are repaired (13/13 each, S 39, J_round 0). That equals cs1, which shifts all 31 positions, at half the change norm (0.311 vs 0.619 of full).
   - With the full contrast (c at 29 and 30), 4bcbaf15 drops to 7/13. Zeroing c₃₀ or halving c brings it back to 13/13. So under the AB-only shift c₃₀ opposes the repair on 4bcbaf15 by 6 cells. That is a much clearer form of M12's weak P30_OPPOSES (2 cells at s ¼ with the shift everywhere).
   - The location matters, not only the size. Shifting at 13–30 (sh_xAB, change norm 0.362) or at kind+received or received+round key plus 29–30 (0.298 / 0.258) repairs only 1fb5651c, which flips under almost any push. 264c458d and 4bcbaf15 stay at 0.
   - With M12: 4bcbaf15 needs both AUTH and BLOCK and 264c458d needs BLOCK; both are satisfied by AB, and neither needs any other context field.
   - Limits: AB (13 tokens) is larger than KR (12) and RR (11), and the shifts are not rescaled. The location controls are close in norm but not matched. All arms are pooled-donor arms; the AB claim rests on two informative hosts.
2. **The tilt of c toward the common subspace does not change S at any size (TILT_NO_EFFECT, REM_NO_EFFECT), and the random-tilt null comparison is uninformative (REM_DIRECTION_NOT_SPECIFIC from floors and ceilings).**
   - The preregistered off-ceiling size failed. At s ⅜, 264c458d is at 0 and 4bcbaf15 at 13 for every tilt and null arm. 264c458d's threshold lies between ⅜ and ½, and 4bcbaf15's below ⅜. At s ½, 264c458d is at 12 and 4bcbaf15 at 13. So no responsive host sits between floor and ceiling for any Q2 or Q3 comparison. Every AT there is a floor or ceiling, not evidence that r acts like a random tilt.
   - The only S change is rem_p2 at s 1 (c + 2r): 4bcbaf15 drops to 11/13.
   - **Reported but not preregistered as a verdict:** the specificity margin C falls monotonically with λ at every size, and r lies outside the 5-null range in both directions where nulls exist:
     - s 1: 0.80 / 0.60 / 0.45 / 0.27 for λ −1 / 0 / +1 / +2.
     - s ½: 0.225 / 0.161 / 0.128 / 0.109, against nulls 0.139–0.174.
     - s ⅜: 0.059 / 0.042 / 0.024, against nulls 0.038–0.049.
     - Adding r lowers C below every null, and removing r raises it above every null. Adding r mainly weakens the main source's push (median dM_main 0.24 → 0.21 → 0.18 at s 1) and lets the round source rise.
     - This is a pooled median over 104 cells with five nulls, so it is suggestive only: r, the in-subspace component of c orthogonal to c, works against the repair's specificity more than a random orthogonal push of the same size, but it does not move any host across threshold at these sizes.
   - With M12: on 264c458d, cpar16_sm (P c rescaled to ‖c‖) repairs 1 cell, but c + r and c − r both repair 13 at s 1. So M12's SUBSPACE_BELOW_COSINE on 264c458d is not explained by r at the S level. It may come from the loss of c's out-of-subspace part (median 0.67 of c's energy) in cpar.
3. **What M13 does not change:** the pooled-contrast arms still repair only 1fb5651c, 264c458d and 4bcbaf15. Hosts 75642418, 2c9118bb and 8ae85754 need the cell's own common part; 1c7158b6 and 2a4f596d are repaired by nothing outside `full`.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.
- Every Q1–Q3 verdict that is more than a ceiling rests on 264c458d and 4bcbaf15.
- C is a pooled median; the C-based reading in point 2 was not preregistered as a verdict.

## Where the M1–M13 chain now stands
- M1–M12 as in M12_RESULT_R1.
- **M13:**
  - The repair needs only the common shift at the author and block lines of the appended item (positions 0–12) plus c at the round value (position 29). That reproduces cs1 on all three responsive hosts at half the change norm. Moving the shift to other context fields does not work on the two informative hosts.
  - c₃₀ opposes the repair when the shift is confined to AB: on 4bcbaf15 it costs 6 of 13 cells.
  - Tilting c toward the common subspace (+r) lowers the specificity margin beyond random tilts and removing r raises it, but neither moves S at s 1, ½ or ⅜. The S-level null test was uninformative because both hosts sit at floor or ceiling.

## Suggested next steps (not frozen)
- **Minimal patch:** shift at 0–12 + c at 29 only (sh_fAB_c29) as the new reference; test its size threshold per host (s ½, ⅜, ¼) and whether the shift can be cut to BLOCK + part of AUTH.
- **Off-ceiling tilt test:** sizes chosen per host between its thresholds (264c458d between ⅜ and ½, e.g. 0.44; 4bcbaf15 between ¼ and ⅜, e.g. 0.31), with ≥ 10 nulls, so that S can move in both directions.
- **cpar on 264c458d:** test c's out-of-subspace part alone and removed, against the M12 cosine nulls, to locate the M12 shortfall.
- Pending separately: replication of the M2/M3 chain on SecJev-0.8B, and the non-pooled hosts (75642418, 2c9118bb, 8ae85754).
