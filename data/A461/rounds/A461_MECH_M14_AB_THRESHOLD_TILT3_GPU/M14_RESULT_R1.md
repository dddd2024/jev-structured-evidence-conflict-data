# A461-MECH-M14 R1: result (how much contrast does the author+block shift need per host, and does a 3× tilt of the round contrast toward the common subspace oppose the repair beyond a random tilt where hosts can move?)

**Run:**
- 6956/6956 kev-4B forwards in 55 batches (54 × 128 + 44); 0 denied; one model load; elapsed 10485 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`.
- Raw blob `d2ac9f4221728d309300cbf617385ad79925eb0b` (sha256 ae09c756…).
- The run follows prereg d686b4e under the standing GPU authorization, extended on 2026-10-30 to autonomous stage design and execution. The pre-model gate passed (`COMPLETE_A461_MECH_M14_PRE_MODEL_GATE`, saved as `M14_GPU_R1/pre_model_gate_receipt.json`). There was a single ledger attempt.

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- The tilt gate (1e-6) passed on every tilt and null row (max error 0.0 at the recorded precision), and the shift-size gate (1e-3) passed on the 208 half-shift rows.
- On real activations r is as in M13: median ‖r‖/‖c‖ 0.46; median energy share 0.219 of ‖c‖². The 3× arms therefore carry a median energy of 2.97 ‖c‖² (range 2.41–3.23), and the nulls keep r's norm.
- The captures stay on the server under `M14_GPU_RUNS/ATTEMPT_R1/captures`. The run's `SHA256SUMS` checks clean on the server. Every non-capture file was fetched here and matches the server's sums (58/58), and the two receipts and the analysis JSON match by sha256. `M14_GPU_R1/SHA256SUMS` lists the local copies, plus the run log and the pre-model gate receipt.

**Analysis:** `A461_mech_m14_analysis_v1.py` (blob 4dd14bbf, frozen before the run), run automatically by the server launch script after the receipt read COMPLETE (exit 0, 2026-10-31 05:26 +08:00). Output: `M14_ANALYSIS_R1/m14_analysis.json` (sha256 cae43d12…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51, 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 bitwise equal to M6; `sh_fAB_c29`, `cs_s0375`, `rem_p1`, `rnull_s05_1` each 12/12 bitwise equal to M13 |
| **Q1 threshold** | **AB_THRESHOLD_MIXED**. SMIN_AB / SMIN_CS: 1fb5651c ⅜ / ¼ (higher), 264c458d ⅜ / ½ (lower), 4bcbaf15 ¼ / ⅜ (lower) |
| Q1 shift at 29–30 | **SHIFT_2930_NEEDED** (`ab_only_c29` S 0) |
| Q1 shift size | **AB_T05_INSUFFICIENT** (`abc_t05` S 0) |
| **Q2 tilt, s 7/16** | **TILT_OPPOSES**: S 38 / 35 / 33 / 28 / 28 for λ −3 / −1 / 0 / +1 / +3 |
| **Q2 tilt, s 5/16** | **TILT_SUPPORTS**: S 21 / 24 / 25 / 25 / 25 → pooled **REM_MIXED** |
| Q2 by host | 264c458d: OPPOSES at 7/16 (12 / 9 / 7 / 2 / 2), floor at 5/16. 4bcbaf15: SUPPORTS at 5/16 (8 / 11 / 12 / 12 / 12), ceiling at 7/16. 1fb5651c: ceiling at both |
| **Q3 null, by S** | **REM3_DIRECTION_MIXED** (informative pairs only): 264c458d at 7/16 HARM_BEYOND_NULL / REMOVAL_BEYOND_NULL; 4bcbaf15 at 5/16 LESS_HARM_THAN_NULL / AT; 4bcbaf15 at 7/16 AT / AT (12–13 of 13, near ceiling) |
| **Q3 null, by C** | **REM3C_DIRECTION_SPECIFIC**: HARM_BEYOND_NULL and REMOVAL_BEYOND_NULL on 5 of the 6 responsive (host, s) pairs; 4bcbaf15 at 7/16 is AT / REMOVAL_BEYOND_NULL |

**Leave one donor group out:** 14/14 splits give every verdict above unchanged, including AB_SMIN_BY_HOST, both TILT verdicts and REM3C_DIRECTION_SPECIFIC. SUF holds for `abc_s05` and `rem_m3_s0437` in 12/14 splits; in the other 2, `abc_s05` falls below SUF and `rem_m3_s0437` stays.

## All arms (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority; C = median dM_main − dM_round)
| arm | S | J main / round | frac | grp | SPEC | C | change norm vs full |
|---|---|---|---|---|---|---|---|
| full (M3 anchor) | 51 | 58 / 7 | 0.99 | 14 | ✓ | 0.714 | 1 |
| meanD_host = cs1 | 39 | 39 / 0 | 1.00 | 14 | ✓ | 0.596 | 0.619 |
| **abc_s05** (AB shift, c at 29, s ½) | **39** | 39 / 0 | 0.75 | 14 | ✓ | 0.098 | 0.307 |
| abc_s0375 | 36 | 39 / 3 | 0.53 | 7 | — | 0.009 | 0.307 |
| abc_s025 | 16 | 31 / 15 | 0.38 | 0 | — | −0.012 | 0.308 |
| ab_only_c29 (shift 0–12 only, s 1) | 0 | 3 / 22 | 0.38 | 0 | — | −0.104 | 0.278 |
| abc_t05 (AB shift × ½, s 1) | 0 | 0 / 0 | 0.38 | 0 | — | −0.125 | 0.163 |
| cs_s0437 | 33 | 39 / 6 | 0.65 | 14 | — | 0.086 | 0.615 |
| rem_m3 / m1 / p1 / p3, s 7/16 | 38 / 35 / 28 / 28 | 39 / 1, 4, 11, 11 | 0.99 / 0.72 / 0.64 / 0.53 | 14 / 14 / 13 / 7 | ✓ / — / — / — | 0.199 / 0.117 / 0.065 / 0.033 | 0.615–0.617 |
| rnull3 s 7/16 (8 seeds) | 29–35 | 39 / 4–10 | 0.64–0.72 | 12–14 | — | 0.079–0.118 | 0.617 |
| cs_s0312 | 25 | 39 / 14 | 0.62 | 13 | — | 0.018 | 0.614 |
| rem_m3 / m1 / p1 / p3, s 5/16 | 21 / 24 / 25 / 25 | 39 / 18, 15, 14, 14 | 0.80 / 0.63 / 0.55 / 0.44 | 14 / 14 / 7 / 2 | ✓ / — / — / — | 0.061 / 0.030 / 0.002 / −0.020 | 0.614–0.615 |
| rnull3 s 5/16 (8 seeds) | 18–23 | 39 / 16–21 | 0.55–0.60 | 6–12 | — | 0.009–0.027 | 0.615 |

SUF (S ≥ 25.5 and SPEC): full, meanD_host, abc_s05, rem_m3_s0437.

## Per-host S (13 cells per host; the other five hosts are 0 in every arm except `full`)
| arm | 1fb5651c | 264c458d | 4bcbaf15 |
|---|---|---|---|
| AB, s ¼ / ⅜ / ½ / 1 (s 1 = M13 `sh_fAB_c29`) | 5 / 13 / 13 / 13 | 0 / **10** / 13 / 13 | **11** / 13 / 13 / 13 |
| all-position cs, s ¼ / ⅜ / ½ / 1 (M13) | 13 / 13 / 13 / 13 | 0 / 0 / 12 / 13 | 0 / 13 / 13 / 13 |
| ab_only_c29 / abc_t05 | 0 / 0 | 0 / 0 | 0 / 0 |
| s 7/16: λ −3 / −1 / 0 / +1 / +3 | 13 each | **12 / 9 / 7 / 2 / 2** | 13 each |
| s 7/16: 8 nulls (c + 3q) | 13 ×8 | 6, 4, 8, 4, 8, 10, 5, 3 | 13, 13, 13, 13, 13, 12, 13, 13 |
| s 5/16: λ −3 / −1 / 0 / +1 / +3 | 13 each | 0 each | **8 / 11 / 12 / 12 / 12** |
| s 5/16: 8 nulls | 13 ×8 | 0 ×8 | 9, 8, 10, 7, 9, 10, 5, 10 |

## Per-host C (median dM_main − dM_round over the host's 13 cells)
| host, s | λ −3 | λ 0 (cs) | λ +3 | 8 nulls |
|---|---|---|---|---|
| 1fb5651c, 7/16 | 0.491 | 0.314 | 0.128 | 0.306–0.348 |
| 1fb5651c, 5/16 | 0.362 | 0.229 | 0.097 | 0.224–0.258 |
| 264c458d, 7/16 | 0.171 | 0.057 | −0.024 | 0.020–0.114 |
| 264c458d, 5/16 | 0.059 | 0.010 | −0.034 | −0.016–0.033 |
| 4bcbaf15, 7/16 | 0.231 | 0.111 | 0.096 | 0.078–0.139 |
| 4bcbaf15, 5/16 | 0.063 | 0.022 | 0.002 | 0.008–0.031 |

## Reading, with its limits
1. **Confining the shift to the author and block lines, with c at the round value only, lowers the contrast each informative host needs (AB_THRESHOLD_MIXED, but lower on both informative hosts).**
   - On 264c458d the threshold drops from between ⅜ and ½ to ⅜ (10/13 at ⅜ vs 0/13 with the all-position shift). On 4bcbaf15 it drops from between ¼ and ⅜ to ¼ (11/13 at ¼ vs 0/13). Only 1fb5651c, which flips under almost any push, is higher (5/13 at ¼ vs 13/13), so the pooled rule reads MIXED.
   - The AB patch at s ½ (`abc_s05`) is SUF with S 39, repairing all three responsive hosts at half the change norm of cs_s05 (0.307 vs 0.616), and J_round falls to 0.
   - Limit: the AB arms differ from the M13 cs arms in two ways at once (no shift at 13–28, and no c at 30), so this does not separate the two. M13 showed c₃₀ costs 4bcbaf15 6 cells under the AB shift at s 1, which may be most of the gain here.
2. **The shift is needed at 29–30, and it is needed at full size (SHIFT_2930_NEEDED, AB_T05_INSUFFICIENT).**
   - Without the shift at 29–30 (`ab_only_c29`), no host is repaired and the round source becomes JOINT in 22 cells: the shift at the round value and newline is what blocks the round-source repair.
   - Halving the AB shift repairs nothing on any host (J_main 0). This fits M10's fine shift threshold near 0.8.
3. **A 3× tilt toward the common subspace opposes the repair beyond random tilts on 264c458d, but not on 4bcbaf15 (TILT_OPPOSES at 7/16, TILT_SUPPORTS at 5/16, REM3_DIRECTION_MIXED by S, REM3C_DIRECTION_SPECIFIC by C).**
   - **264c458d at s 7/16**, its first size between floor and ceiling: S falls monotonically 12 → 9 → 7 → 2 → 2 as λ runs from −3 to +3. c + 3r (2) is below all 8 nulls (3–10), and c − 3r (12) is above all of them. C behaves the same way (−0.024 and 0.171 against nulls 0.020–0.114). This is the first S-level evidence that r, the part of c's 16-dim projection orthogonal to c, works against the repair beyond a random orthogonal push of the same size. It is a plausible account of M12's SUBSPACE_BELOW_COSINE on 264c458d, where cpar16_sm (≈ 0.58 c + 1.77 r, a tilt of about λ 3 on a smaller c) repaired 1 cell; M14 did not test cpar16_sm itself.
   - **4bcbaf15 at s 5/16** goes the other way by S: every 3× push costs cells (nulls 5–10 of 13, against 12 for cs). c − 3r costs as much as a random push (8, AT), and c + 3r costs nothing (12, LESS_HARM_THAN_NULL). But its C is still lowest for c + 3r (0.002 against nulls 0.008–0.031, HARM_BEYOND_NULL). So on 4bcbaf15 adding r weakens the specificity margin while keeping more cells JOINT. The JOINT criterion also needs the action A > 0, and r may help A while lowering M. The preregistered readout does not report A separately, so this is not resolved.
   - **C** falls monotonically with λ on every host and size, and lies outside the 8-null range in both directions on 5 of 6 pairs (REM3C_DIRECTION_SPECIFIC). This confirms, at 3× and with 8 nulls, the M13 C trend that was only reported there.
   - λ −3 at s 7/16 (`rem_m3_s0437`) is SUF (S 38, frac 0.99), against cs_s0437 at 33 and not SUF: removing 3r is worth about as much as raising s from 7/16 to ½.
4. **What M14 does not change:** the pooled-contrast arms still repair only 1fb5651c, 264c458d and 4bcbaf15. Hosts 75642418, 2c9118bb and 8ae85754 need the cell's own common part; 1c7158b6 and 2a4f596d are repaired by nothing outside `full`.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests. Every informative Q1–Q3 verdict rests on 264c458d or 4bcbaf15, one size each.
- The two hosts disagree on the S-level tilt verdict; C agrees on both.
- 8 nulls bound the null range only coarsely; "beyond null" means outside 8 draws.
- The Q1 thresholds compare M14 rows with M13 rows, which is valid because the replay arms are bitwise equal.

## Exploratory addendum (after the preregistered analysis; not a verdict)
`A461_mech_m14_explore_round_action_v1.py` (blob fbcbb54f; output `M14_ANALYSIS_R1/explore_round_action.txt`) splits JOINT into its two parts per source on the tilt arms of 264c458d and 4bcbaf15:
- **On both hosts, at both sizes, the main source is JOINT in 13/13 cells in every tilt and null arm, and the round source's conflict margin M is > 0 in every cell** (except 3–2 cells of 4bcbaf15 at 7/16). So S there is decided entirely by the round source's action margin A = logit(reject_conflict) − max(accept, wait).
- **264c458d, s 7/16:** adding r raises the round source's A. Round cells with A > 0 go 1 / 4 / 6 / 11 / 11 for λ −3 / −1 / 0 / +1 / +3, against 3–10 for the nulls; median A goes −0.054 → +0.019.
- **4bcbaf15, s 5/16:** adding r lowers it. Round A > 0 goes 5 / 2 / 1 / 1 / 1, against 3–8 for the nulls; median A goes −0.006 → −0.053. Any random 3× push raises the round source's A here, and +3r is the one push that does not.
- On both hosts r lowers the main source's M (264c458d 0.425 → 0.312; 4bcbaf15 0.272 → 0.213), which is what C picks up. So the S/C split on 4bcbaf15 is not a contradiction: C reads the conflict vote, and S at these sizes reads the round source's action, which r moves in opposite directions on the two hosts.
- This is not a general rule. Over all M14 arms on the three responsive hosts (1272 cells), a round source that is not JOINT is blocked by M in 442 cells and by A alone in 419.

## Where the M1–M14 chain now stands
- M1–M13 as in M13_RESULT_R1.
- **M14:**
  - The minimal patch is the common shift at positions 0–12 and 29–30 with c at 29 only. It needs the full-size shift, and it needs the shift at 29–30, which stops the round source from being repaired. With it, each informative host needs less contrast than with the all-position shift (264c458d ⅜, 4bcbaf15 ¼), and s ½ repairs all three responsive hosts.
  - r, the in-subspace remainder of the round contrast, opposes the repair's specificity (C) beyond random tilts on every responsive host. At the S level that shows on 264c458d (beyond 8 nulls in both directions) but not on 4bcbaf15, where any large push costs cells and +r costs the least.

## Suggested next steps (not frozen)
- **Separate the two Q1 differences:** AB shift with c at 29 and 30, and all-position shift with c at 29 only, at s ¼ / ⅜ / ½.
- **Round-source action:** the addendum shows S at off-ceiling sizes is set by the round source's action margin, which r moves in opposite directions on 264c458d and 4bcbaf15; a preregistered test of why (e.g. r's projection on the action readout per host) is open.
- **Dose of r on 264c458d:** λ in finer steps (−3…+3) at s 7/16 with more nulls, and r alone (no c) to see whether r by itself pushes toward the round source.
- Pending separately: replication on SecJev-0.8B, and the non-pooled hosts (75642418, 2c9118bb, 8ae85754).
