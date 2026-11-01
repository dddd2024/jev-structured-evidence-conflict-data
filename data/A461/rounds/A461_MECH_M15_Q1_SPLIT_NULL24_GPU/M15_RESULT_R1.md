# A461-MECH-M15 R1: result (is M14's lower AB threshold due to dropping c at 30 or to confining the shift, is the 264c458d tilt opposition graded in λ, and does it survive 24 random-tilt nulls?)

**Run:**
- 5500/5500 kev-4B forwards in 43 batches (42 × 128 + 124); 0 denied; one model load; elapsed 8309 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`.
- Raw blob `b6807b136acd3a00944705fae50b5d910946cf16` (sha256 7fdc9283…).
- The run follows prereg 103483a under the standing GPU authorization, extended on 2026-10-30 to autonomous stage design and execution. The pre-model gate passed (`COMPLETE_A461_MECH_M15_PRE_MODEL_GATE`, saved as `M15_GPU_R1/pre_model_gate_receipt.json`). There was a single ledger attempt.

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- The tilt gate (1e-6) passed on every tilt and null row (max error 0.0 at the recorded precision).
- r on real activations is as in M13–M14: median ‖r‖/‖c‖ 0.46 and median energy share 0.219. The 3× nulls carry a median energy of 2.97 ‖c‖², and their median cosine to r is |·| ≤ 0.005.
- The captures stay on the server under `M15_GPU_RUNS/ATTEMPT_R1/captures`. The run's `SHA256SUMS`, including all 88 capture entries, checks clean both on the server and on a full local copy. The local captures were then removed. `M15_GPU_R1/SHA256SUMS` now lists the 47 kept files, which include the run log and the pre-model gate receipt.

**Analysis:** `A461_mech_m15_analysis_v1.py` (blob 83d1c5a4, frozen before the run), run automatically by the server launch script after the receipt read COMPLETE (exit 0, 2026-10-31 09:12 +08:00). Output: `M15_ANALYSIS_R1/m15_analysis.json` (sha256 c5e2ff92…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51, 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 bitwise equal to M6; `abc_s0375`, `rem_p3_s0437`, `rnull3_s0437_1`, `cs_s0312` each 12/12 bitwise equal to M14 |
| **Q1 split** | **Q1_GAIN_LOC_ONLY**: on both informative hosts the AB shift lowers SMIN with or without c₃₀ (AB_LOWERS), and c₃₀ has no cost (C30_NO_COST) |
| Q1 SMIN (AB29 / AB30 / ALL29 / ALL30) | 264c458d ⅜ / ⅜ / ½ / ½; 4bcbaf15 ¼ / ¼ / ⅜ / ⅜; 1fb5651c ⅜ / ¼ / ¼ / ¼ (C30_MIXED, LOC_MIXED; not one of the hosts the pooled rule reads) |
| **Q2 dose, s 7/16** | **DOSE_OPPOSES**: pooled S 38 / 38 / 35 / 33 / 28 / 28 / 28 for λ −3 … +3. By host: 264c458d **12 / 12 / 9 / 7 / 2 / 2 / 2** (DOSE_OPPOSES); 1fb5651c and 4bcbaf15 13 at every λ (DOSE_NO_EFFECT, ceiling) |
| **Q3 24 nulls, by S** | **NULL24_S_DIRECTION_SPECIFIC**: 264c458d HARM_BEYOND_NULL24 (c + 3r: 2 < null min 3) and REMOVAL_BEYOND_NULL24 (c − 3r: 12 > null max 10); 4bcbaf15 AT / AT (near ceiling); 1fb5651c uninformative (13 everywhere) |
| **Q3 24 nulls, by C** | **NULL24_C_DIRECTION_SPECIFIC**: HARM / REMOVAL BEYOND_NULL24 on 264c458d and 1fb5651c; 4bcbaf15 AT (2 of 24 nulls ≤ c + 3r) / REMOVAL_BEYOND_NULL24 |
| round action | **ROUND_A_RANK_264C ge_add 0/24, le_remove 0/24**: no null pushes as many 264c458d round sources to A > 0 as c + 3r (11 of 13), and none as few as c − 3r (1 of 13) |

**Leave one donor group out (14 splits):**
- **Unchanged in 14/14:** DOSE_OPPOSES (pooled and by host), NULL24_S_DIRECTION_SPECIFIC and NULL24_C_DIRECTION_SPECIFIC.
- **NULL24_BY_HOST, 9/14:** in the other 5 splits, c + 3r on 264c458d ties the smallest null by S, so the verdict reads AT. REMOVAL_BEYOND by S and both C verdicts hold in all 14.
- **ROUND_A_RANK_264C, 9/14:** the other 5 splits give ge_add 1/24.
- **Q1_GAIN_LOC_ONLY, 7/14:** the other 7 give Q1_GAIN_MIXED. In those splits 264c458d's AB30 at ⅜ falls from S 7 to 6, so SMIN(AB30) rises to ½ and c₃₀ reads C30_COSTS_UNDER_AB. On 264c458d, AB_LOWERS (with or without the c₃₀ qualifier) and on 4bcbaf15 AB_LOWERS and C30_NO_COST hold in 14/14.
- SUF holds for `full`, `meanD_host` and `rem_m2_s0437` in every split.

## All M15 arms (S out of 104; C = median dM_main − dM_round)
| arm | S | J main / round | frac | grp | SPEC | C | change norm vs full |
|---|---|---|---|---|---|---|---|
| full (M3 anchor) | 51 | 58 / 7 | 0.99 | 14 | ✓ | 0.714 | 1 |
| meanD_host = cs1 | 39 | 39 / 0 | 1.00 | 14 | ✓ | 0.596 | 0.619 |
| abc30 (AB shift, c at 29 + 30), s ½ / ⅜ / ¼ | 39 / 33 / 18 | 39 / 0, 6, 15 | 0.75 / 0.50 / 0.38 | 14 / 4 / 0 | ✓ / — / — | 0.095 / 0.003 / −0.017 | 0.308 |
| csc29 (all-position shift, c₃₀ weight 0), s ½ / ⅜ / ¼ | 38 / 26 / 13 | 39 / 1, 13, 26 | 0.75 / 0.63 / 0.61 | 14 / 14 / 13 | ✓ / — / — | 0.167 / 0.048 / 0.007 | 0.614 |
| rem_m2 / rem_p2, s 7/16 | 38 / 28 | 39 / 1, 11 | 0.88 / 0.59 | 14 / 10 | ✓ / — | 0.149 / 0.048 | 0.616 |
| rnull3 s 7/16, seeds 9–24 | 29–35 | 39 / 4–10 | 0.65–0.75 | 12–14 | 1 of 16 ✓ | 0.061–0.137 | 0.617 |

SUF (S ≥ 25.5 and SPEC): full, meanD_host, abc30_s05, csc29_s05, rem_m2_s0437, rnull3_s0437_16. One of the 16 new nulls reaches SPEC by a hair (frac 0.75). The other 15 do not, nor do any of M14's 8.

## Q1: per-host S and C over s ¼ / ⅜ / ½ (AB29 = M14 `abc_*`, ALL30 = M13 `cs_*`)
| host | AB29 S | AB30 S | ALL29 S | ALL30 S | AB29 C | AB30 C | ALL29 C | ALL30 C |
|---|---|---|---|---|---|---|---|---|
| 264c458d | 0 / 10 / 13 | 0 / **7** / 13 | 0 / 0 / 12 | 0 / 0 / 12 | −.016 / −.004 / .064 | −.024 / −.016 / .048 | .010 / .037 / .129 | .003 / .027 / .115 |
| 4bcbaf15 | 11 / 13 / 13 | 11 / 13 / 13 | 0 / 13 / 13 | 0 / 13 / 13 | −.011 / .027 / .151 | −.014 / .021 / .141 | .007 / .054 / .219 | .007 / .053 / .216 |
| 1fb5651c | 5 / 13 / 13 | 7 / 13 / 13 | 13 / 13 / 13 | 13 / 13 / 13 | .134 / .202 / .268 | .137 / .207 / .274 | .184 / .271 / .351 | .185 / .272 / .353 |

## Dose and 24 nulls at s 7/16, per host
| | 1fb5651c | 264c458d | 4bcbaf15 |
|---|---|---|---|
| S, λ −3 … +3 | 13 each | 12 / 12 / 9 / 7 / 2 / 2 / 2 | 13 each |
| C, λ −3 … +3 | .491 / .437 / .377 / .314 / .248 / .185 / .128 | .171 / .129 / .089 / .057 / .028 / .001 / −.024 | .231 / .170 / .133 / .111 / .096 / .096 / .096 |
| 24 nulls, S | 13 × 24 | 3–10 (median 6) | 11–13 |
| 24 nulls, C | 0.261–0.348 | 0.008–0.114 | 0.078–0.185 |
| round A > 0, λ −3 … +3 (of 13) | 5 / 12 / 13 / 13 / 13 / 13 / 13 | **1 / 1 / 4 / 6 / 11 / 11 / 11** | 0 each |
| round A > 0, 24 nulls | 12–13 | 3–10 | 0–2 |

On 264c458d every round source has M > 0 in every arm. S therefore equals 13 minus the number of round sources with A > 0. The tilt moves that count monotonically in λ, from 1 to 11. On 4bcbaf15 the round A stays negative in every arm, so S stays at ceiling, and the tilt shows only in C.

## What this says
1. **The lower threshold comes from where the shift sits, not from c₃₀.** Under the all-position shift, removing the c₃₀ weight changes nothing measurable: S is identical on every host and s, and C changes by ≤ 0.015. Under the AB shift, removing c₃₀ makes no SMIN difference on 4bcbaf15. On 264c458d it moves S at ⅜ only from 7 to 10, which straddles the threshold of 7, so 7 of 14 splits read a c₃₀ cost there. The preregistered reading **Q1_GAIN_LOC_ONLY** therefore rests on a robust location effect, combined with a c₃₀ effect that is null on 4bcbaf15 and marginal on 264c458d.
2. **How the AB shift wins (descriptive, not a verdict).** At equal s, the AB shift has a lower C than the all-position shift on all three hosts. It reaches S ≥ 7 sooner only because fewer round sources become JOINT: for example, at ⅜ J_round is 6 (AB30) or 3 (M14 AB29), against 13 (ALL29). So confining the shift does not make the main source repair more. It makes the round source repair less.
3. **The tilt opposition on 264c458d is graded and beyond 24 nulls.**
   - S falls monotonically in λ (12 → 2) and C falls strictly (0.171 → −0.024).
   - c + 3r and c − 3r lie outside all 24 random 3× tilts, by S and by C.
   - The mechanism is the round source's action margin. r raises the number of round sources with A > 0 from 1 to 11, beyond every null in both directions.
   - The S margin on the harm side is one cell (2 vs a null minimum of 3), and 5 of 14 splits tie it. The C margin (−0.024 vs 0.008) and the removal side (12 vs 10 by S; 0.171 vs 0.114 by C) hold in every split.
4. **C is graded in λ on every responsive host.** It falls strictly on 1fb5651c and 264c458d, and flattens at λ ≥ +1 on 4bcbaf15. Removing r (c − 3r) raises C beyond all 24 nulls on all three hosts. Adding it lowers C beyond the nulls on 1fb5651c and 264c458d, but not on 4bcbaf15 (AT, rank 2).

## Limits
- All arms except `full` are pooled-donor arms. That is effectively 8 host replicates, of which 3 respond. Every informative S verdict rests on 264c458d or 4bcbaf15, and the S harm on 264c458d rests on one cell of margin.
- The Q1 table combines M13, M14 and M15 rows. That is valid because the replay arms are bitwise equal. The ¼–⅜–½ grid cannot separate thresholds within a step.
- The "how the AB shift wins" point (2) and the round-action reading come from the reported tables. They are not preregistered verdicts, apart from ROUND_A_RANK_264C.
- One model (kev-4B) and one simulator family. No paper-level audit has been run.
