# A461-MECH-M12 R1: result (is c at position 30 a counter-signal, which fields of the appended item must carry the common shift, and is the subspace split more than cosine to c?)

**Run:**
- 7740/7740 kev-4B forwards in 61 batches (60 × 128 + 60); 0 denied; one model load; elapsed 11593 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`.
- Raw blob `cc79f23a0dc6d80ec17bdad0fed54f710291dbe4`.
- The run follows prereg ee05402 under the standing GPU authorization (freeze also pre-authorized by the user). The pre-model gate passed (`COMPLETE_A461_MECH_M12_PRE_MODEL_GATE`, saved as `M12_GPU_R1/pre_model_gate_receipt.json`). There was a single ledger attempt (`A461_MECH_M12_GPU_20261030_R1`, 7740 reserved, 7740 consumed).

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- The cosine-null gate (norm and cosine to c kept per row and position, fail-closed at 1e-6) passed in the run: max error 2.0e-15. The part size gate passed; no row hit the cap (capped share 0).
- The weighted arms have the planned energy: cw30_m1 1.000 × ‖c‖², cw30_p2 median 1.342 (min 1.278). Position 30 holds a median 11.4 % of c's energy.
- Median cosine to c per (row, position): cpar16_sm 0.559, cperp16_sm 0.681. The nulls keep these exactly.
- The captures stay on the server under `M12_GPU_RUNS/ATTEMPT_R1/captures`. Every non-capture file was fetched here and verified against the run's `SHA256SUMS` (64/64). The receipt, run log and analysis JSON match the server copies by sha256.

**Analysis:** `A461_mech_m12_analysis_v1.py` (blob 13d27379, frozen before the run), run automatically by the server launch script after the receipt read COMPLETE (exit 0, 2026-10-30 18:25 +08:00). Output: `M12_ANALYSIS_R1/m12_analysis.json` (sha256 44b2b3b7…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51, 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 bitwise equal to M6; cs1 / cpos29 / cpos29_s05 / cpos29_s025 / cpar16_sm / cperp16_sm / sh2930 / sh0_28 each 208/208 bitwise equal to M11, S = 39 / 39 / 38 / 13 / 27 / 39 / 0 / 13 |
| **Q1 position-30 weight at s = ¼** | **P30_OPPOSES**: S(w −1 / 0 / +1) = 15 / 13 / 13 |
| Q1 dose | **WSMIN(−1) = WSMIN(0) = WSMIN(+1) = WSMIN(+2) = 0.5** → **FLIP_DOES_NOT_LOWER_THRESHOLD** |
| **Q2 fields needed** | **SHIFT_FIELDS_NEEDED:BLOCK** (sh_xBLOCK S 20, not SUF; sh_xAUTH S 26 passes SUF by half a cell) |
| **Q2 fields sufficient** | **SHIFT_FIELDS_SUFFICE:NONE** (best: sh_fBLOCK S 18) |
| **Q3 cosine null by host** | **COS_SPLIT_BY_HOST:1fb5651c=par:AT/perp:AT,264c458d=par:BELOW/perp:AT,4bcbaf15=par:AT/perp:AT** |
| pooled | **SUBSPACE_BELOW_COSINE** |

**Leave one donor group out:**
- 14/14 splits give P30_OPPOSES, FLIP_DOES_NOT_LOWER_THRESHOLD, SHIFT_FIELDS_SUFFICE:NONE, the same COS_SPLIT_BY_HOST and SUBSPACE_BELOW_COSINE.
- The S triple at s ¼ is 14 / 12 / 12 in 11 splits, 13 / 12 / 12 in 2, and 15 / 13 / 13 in 1: always a 1–2 cell lead for w = −1.
- SHIFT_FIELDS_NEEDED is BLOCK in 12/14 splits and AUTH,BLOCK in 2/14 (sh_xAUTH falls below SUF).
- WSMIN is 0.5 for every w in 12/14 splits and 1.0 for every w in 2/14 (the s ½ arms sit at frac exactly 0.75, as in M11).

## All arms (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority; C = median dM_main − dM_round)
| arm | S | J main / round | frac | grp | SPEC | median dM main / round | C | change norm vs full |
|---|---|---|---|---|---|---|---|---|
| full (M3 anchor) | 51 | 58 / 7 | 0.99 | 14 | ✓ | +0.35 / −0.37 | 0.71 | 1 |
| meanD_host = cs1 (w +1, s 1) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.66 | 0.60 | 0.619 |
| cpos29 (w 0, s 1) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.25 / −0.66 | 0.66 | 0.617 |
| **cw30_m1** (w −1, s 1) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.26 / −0.67 | **0.73** | 0.618 |
| cw30_p2 (w +2, s 1) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.22 / −0.65 | 0.56 | 0.622 |
| cw30_m1_s05 | 38 | 39 / 1 | 0.75 | 14 | ✓ | +0.29 / +0.19 | 0.172 | 0.615 |
| cpos29_s05 | 38 | 39 / 1 | 0.75 | 14 | ✓ | +0.29 / +0.19 | 0.167 | 0.615 |
| cs_s05 | 38 | 39 / 1 | 0.75 | 14 | ✓ | +0.28 / +0.19 | 0.161 | 0.616 |
| cw30_p2_s05 | 38 | 39 / 1 | 0.75 | 14 | ✓ | +0.28 / +0.20 | 0.155 | 0.617 |
| **cw30_m1_s025** | **15** | 39 / 24 | 0.62 | 13 | — | +0.32 / +0.37 | 0.009 | 0.614 |
| cpos29_s025 | 13 | 39 / 26 | 0.61 | 13 | — | +0.31 / +0.37 | 0.007 | 0.614 |
| cs_s025 | 13 | 39 / 26 | 0.60 | 12 | — | +0.31 / +0.37 | 0.007 | 0.614 |
| sh2930 (M11) | 0 | 0 / 0 | 1.00 | 14 | ✓ | +0.02 / −0.41 | 0.45 | 0.053 |
| sh0_28 (M11) | 13 | 16 / 26 | 0.38 | 0 | — | +0.15 / +0.33 | −0.12 | 0.587 |
| sh_fAUTH | 0 | 0 / 0 | 1.00 | 14 | ✓ | +0.09 / −0.41 | 0.43 | 0.175 |
| **sh_fBLOCK** | **18** | 18 / 0 | 1.00 | 14 | ✓ | +0.11 / −0.48 | 0.51 | 0.192 |
| sh_fKIND | 0 | 0 / 0 | 1.00 | 14 | ✓ | +0.05 / −0.42 | 0.46 | 0.155 |
| sh_fRECV | 13 | 13 / 0 | 1.00 | 14 | ✓ | +0.03 / −0.47 | 0.43 | 0.194 |
| sh_fRKEY | 3 | 3 / 0 | 1.00 | 14 | ✓ | +0.08 / −0.39 | 0.47 | 0.118 |
| **sh_xAUTH** | **26** | 26 / 0 | 1.00 | 14 | ✓ | +0.17 / −0.56 | 0.55 | 0.497 |
| **sh_xBLOCK** | **20** | 20 / 0 | 1.00 | 14 | ✓ | +0.14 / −0.48 | 0.51 | 0.481 |
| sh_xKIND | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.22 / −0.64 | 0.63 | 0.518 |
| sh_xRECV | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.62 | 0.62 | 0.471 |
| sh_xRKEY | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.21 / −0.64 | 0.56 | 0.554 |
| cpar16_sm (M11) | 27 | 39 / 12 | 0.60 | 12 | — | +0.23 / +0.12 | 0.09 | 0.619 |
| ccos_par_s1 … s5 | 34 / 35 / 34 / 34 / 30 | 39 / 4–9 | 0.73–0.79 | 14 | ✓ except s2 (0.73) | +0.25–0.29 / +0.13–0.21 | 0.10–0.23 | 0.619 |
| cperp16_sm (M11) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.27 / −0.53 | 0.72 | 0.618 |
| ccos_perp_s1 … s5 | 39 each | 39 / 0 | 0.98–1.00 | 14 | ✓ | +0.25–0.27 / −0.44 to −0.49 | 0.47–0.54 | 0.619 |

## Per-host S (13 cells per host; the other five hosts are 0 in every arm except `full`)
| arm | 1fb5651c | 264c458d | 4bcbaf15 |
|---|---|---|---|
| cs1 / cpos29 / cw30_m1 / cw30_p2 | 13 / 13 / 13 / 13 | 13 / 13 / 13 / 13 | 13 / 13 / 13 / 13 |
| s ½: w −1 / 0 / +1 / +2 | 13 each | 12 each | 13 each |
| s ¼: w −1 / 0 / +1 | 13 / 13 / 13 | 0 / 0 / 0 | **2** / 0 / 0 |
| sh_f AUTH / BLOCK / KIND / RECV / RKEY | 0 / 13 / 0 / 13 / 3 | 0 / 5 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 |
| sh_x AUTH / BLOCK / KIND / RECV / RKEY | 13 / 13 / 13 / 13 / 13 | 13 / **6** / 13 / 13 / 13 | **0** / **1** / 13 / 13 / 13 |
| cpar16_sm vs its 5 cosine nulls | 13 vs 13 ×5 | **1 vs 8 / 10 / 8 / 8 / 5** | 13 vs 13 / 12 / 13 / 13 / 12 |
| cperp16_sm vs its 5 cosine nulls | 13 vs 13 ×5 | 13 vs 13 ×5 | 13 vs 13 ×5 |

## Reading, with its limits
1. **Position 30 opposes, but weakly (P30_OPPOSES; FLIP_DOES_NOT_LOWER_THRESHOLD).**
   - The rule fires on a 2-cell lead: at s ¼, w −1 repairs 2 cells of 4bcbaf15 that w 0 and w +1 do not. 1fb5651c is at 13 and 264c458d at 0 for every w. The lead holds in all 14 splits (1–2 cells).
   - The more consistent evidence is the specificity margin C, which falls monotonically with w at every size: s 1: 0.73 / 0.66 / 0.60 / 0.56 for w −1 / 0 / +1 / +2; s ½: 0.172 / 0.167 / 0.161 / 0.155; s ¼: 0.009 / 0.007 / 0.007. More c₃₀ moves the round source towards the main source's outcome, which is a counter-signal in direction. In size it is small: S does not change at s ½ or 1, and WSMIN is ½ for every w.
   - So c₃₀ is a weak opponent of the round-specific repair, consistent with M11's harm at 2–4 × c₃₀ alone, but it does not gate the repair. Removing or flipping it does not lower the contrast threshold. The pooled contrast is effectively c₂₉.
2. **The shift is needed at the first two lines of the appended item (SHIFT_FIELDS_NEEDED:BLOCK, with AUTH on the edge; SUFFICE:NONE).**
   - Dropping the shift at KIND, RECV or RKEY changes nothing (S 39 each, all three hosts). Dropping it at BLOCK (positions 7–12) loses 4bcbaf15 (1/13) and half of 264c458d (6/13). Dropping it at AUTH (0–6) loses 4bcbaf15 entirely (0/13) while 264c458d keeps 13. The pooled sh_xAUTH S 26 passes SUF by half a cell only because 1fb5651c and 264c458d are full; per host, 4bcbaf15 needs both AUTH and BLOCK and 264c458d needs BLOCK.
   - The size is not the reason: sh_xRECV has a smaller change norm (0.471) than sh_xAUTH (0.497) or sh_xBLOCK (0.481) and keeps S 39.
   - No single field with 29–30 is enough. sh_fBLOCK reaches 18 (1fb5651c 13, 264c458d 5), sh_fRECV 13 (1fb5651c only), AUTH and KIND 0. Every field arm stays specific (J_round 0), as sh2930 did.
   - Together with M11 (sh2930 S 0; sh0_28 S 13, not specific): the repair needs the common shift at the author and block lines of the appended item (positions 0–12) and the contrast at the round value. The other context fields are dispensable. AUTH+BLOCK+29–30 alone was not tested, so "0–12 suffice" is not established.
   - Limit: the field arms change the shift's total size together with its place, and each field is 6–7 tokens; a host-level threshold in shift size (M10) could still interact with which tokens carry it.
3. **The in-subspace part of c is worse than a random direction with its cosine on 264c458d (SUBSPACE_BELOW_COSINE).**
   - On 1fb5651c and 4bcbaf15 every part and every null repairs all or nearly all 13 cells, so AT there is a ceiling, not evidence of equivalence. Only 264c458d is informative.
   - **264c458d:** cperp and its nulls repair 13/13. cpar repairs 1, its cosine-matched nulls 5–10 (median 8). The null keeps cpar's norm and its cosine to c (median 0.56) and replaces the remainder orthogonal to c with a random direction. So the in-subspace remainder of cpar actively works against the repair on this host; it is not just "less aligned with c".
   - Pooled, the cperp nulls equal cperp (S 39 each), and the cpar nulls (30–35, J_round 4–9, frac 0.73–0.79) beat cpar (27, J_round 12, frac 0.60) in S and specificity.
   - With M11: the M9–M11 "contrast outside the common subspace" reading becomes concrete on one host. The outside part works as well as any direction with its cosine to c. The inside part carries a component in the common 16-dim subspace that blocks the repair on 264c458d and lowers specificity elsewhere.
   - Limits: one informative host; five nulls per part; median cosine differs between parts (0.56 vs 0.68), so par and perp are not compared with each other, each only with its own null.
4. **What M12 does not change:** the pooled-contrast arms still repair only 1fb5651c, 264c458d and 4bcbaf15; 1fb5651c flips under almost any push (it repairs at sh_fBLOCK, sh_fRECV and every null). Hosts 75642418, 2c9118bb and 8ae85754 need the cell's own common part; 1c7158b6 and 2a4f596d are repaired by nothing outside `full`.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.
- All M12 arms except `full` are pooled-donor arms, effectively 8 host replicates with 3 that respond. Per-host S is the honest unit. Every Q1–Q3 verdict that is more than a ceiling rests on 264c458d and 4bcbaf15.

## Where the M1–M12 chain now stands
- M1–M11 as in M11_RESULT_R1.
- **M12:**
  - c₃₀ is a weak counter-signal: it lowers the specificity margin monotonically at every size, adds 2 cells when flipped at s ¼, and changes no threshold. The contrast's working part is c₂₉.
  - The common shift must reach the author and block lines of the appended item (positions 0–12). KIND, RECV and RKEY are dispensable, and no single field is enough. Per host: 4bcbaf15 needs AUTH and BLOCK, 264c458d needs BLOCK.
  - The outside-subspace part of c acts like any direction with its cosine to c. The inside part does worse than such directions on 264c458d (1 vs 5–10) and is less specific pooled, so the common 16-dim subspace carries a component that opposes the repair there.

## Suggested next steps (not frozen)
- **AUTH+BLOCK sufficiency:** shift at positions 0–12 plus 29–30 with c (and c₂₉ only), with a size-matched control at other context fields, per host.
- **The opposing in-subspace component:** project cpar's in-subspace remainder (orthogonal to c) and test it alone and removed from cs1 on 264c458d and 4bcbaf15, against cosine nulls; a larger null count (≥ 10) on 264c458d.
- **Non-ceiling hosts:** the Q3 nulls are saturated on 1fb5651c and 4bcbaf15 at s 1; repeating Q3 at s ½ (where 264c458d is 12/13 and 4bcbaf15 13/13) or s 0.36 would give two informative hosts.
- Pending separately: replication of the M2/M3 chain on SecJev-0.8B, and the non-pooled hosts (75642418, 2c9118bb, 8ae85754).
