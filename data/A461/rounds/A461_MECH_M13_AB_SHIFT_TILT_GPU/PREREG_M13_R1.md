# A461-MECH-M13 R1: is the common shift at the author and block lines enough, and does tilting the round contrast toward the common subspace work against the repair beyond a random tilt? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 7116 kev-4B forwards in 56 batches (55 × 128 + 76).

**Parent:** M12 R1 (b72a451).
- **Position 30:** the contrast at position 30 opposes the repair only weakly (P30_OPPOSES on a 2-cell lead), and no threshold moves.
- **Shift location:** the shift is needed at the block line (SHIFT_FIELDS_NEEDED:BLOCK), with the author line on the edge: 4bcbaf15 needs both lines, 264c458d needs the block line. No single field plus 29–30 is enough.
- **Subspace:** SUBSPACE_BELOW_COSINE. On 264c458d, cpar16_sm repairs 1 cell, and nulls with its norm and its cosine to c repair 5–10. On the other two responsive hosts every arm is at ceiling.

## Questions
1. **Author+block location.** Is the common shift at span positions 0–12 (author and block lines) plus 29–30 enough? Test it with the full contrast, with c at position 29 only, and at s = ½. Is it needed (shift at 13–30 only)? Is the location specific, compared with kind+received (13–24) or received+round key (18–28), each plus 29–30?
2. **Tilt.** Per question row and span position, let r be the part of P c that is orthogonal to c, where P projects on the cell's 16-dim common subspace (the cpar16_sm basis). Since r ⟂ c, the contrast c + λ r keeps c's component along c and tilts it toward the common subspace (λ > 0) or away from it (λ < 0). Since c = par + perp, the perp part carries −r. Does the repair fall as λ rises, at s = 1, ½ and ⅜?
3. **Null.** Is r special, or does any orthogonal push of the same size act the same? Each null is c + q, with q ⟂ c, ‖q‖ = ‖r‖ per row and position, and a random direction. There are 5 seeds per cell, shared by both sizes and by the main and round patches. Nulls are compared per responsive host at s = ½ and ⅜, below the s = 1 ceiling.

## Arms (all patch the L11 `o_proj` input at the 31 span positions of host new in every question row; sources donor new = main, donor ROUND = round; pools, mid and c as in M8–M12; common shift t = 1; contrast ∓ s/2 c)
| arm | patch | role |
|---|---|---|
| `full`, `meanD_host` | M3 all-heads patch / M6 pooled-donor arm | bitwise anchors (S 51 / 39) |
| `cs1`, `cs_s05`, `cs_s025`, `cpar16_sm`, `sh_fBLOCK`, `sh_xAUTH`, `sh_xBLOCK` | the M12 arms with identical patch fields | bitwise anchors (S 39 / 38 / 13 / 27 / 18 / 26 / 20) |
| **`sh_fAB`**, `sh_fAB_c29`, `sh_fAB_s05` | shift at 0–12 + 29–30; full c / c₃₀ weight 0 / s = ½ | Q1 sufficiency |
| `sh_xAB` | shift at 13–30 | Q1 necessity |
| `sh_fKR`, `sh_fRR` | shift at 13–24 + 29–30 / 18–28 + 29–30 | Q1 location controls |
| `cs_s0375` | c at s = ⅜ | Q2 / Q3 baseline |
| `rem_p1`, `rem_m1`, `rem_p2` (s 1); `_s05` versions; `rem_p1_s0375`, `rem_m1_s0375` | c + λ r, λ = +1 / −1 / +2 | Q2 |
| `rnull_s05_1` … `5`, `rnull_s0375_1` … `5` | c + q, random q ⟂ c with ‖q‖ = ‖r‖ (seeds `A461_M13_RNULL\|16\|d\|h\|i`) | Q3 |

- AB has 13 tokens, KR 12 and RR 11. The shifts are not rescaled, and their change norms are reported.
- s = ⅜ sits between the per-host contrast thresholds seen in M11 (4bcbaf15 about 0.36, 264c458d between 0.36 and ½), so at least one responsive host should be off ceiling there.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m13_freeze_v1.py` (CPU + tokenizer only), derived from the M12 freeze by checked edits. It cross-checks the M3–M12 key classes and pools, the span width and field layout of every capture, that the 9 replay arms' patch fields equal the M12 rows' fields, and that the 5 null seeds per cell are distinct and shared across s |
| manifest blob | `c91c34efccccddd5f846eb8b103240691de43f9c` |
| design blob | `900b1f0595ab30f45cc07264a14280bf2f8c222a`: the rules are under `preregistered_analysis` |
| runner blob | `28bcffba25b9b1b99ef231196653a48d33b0e7f8`, derived from the M12 runner 6dcaff0e by checked edits. It adds `contrast_rem` (c + λ r, or with `null_seed` a random tilt orthogonal to c with r's norm), with a fail-closed gate at 1e-6 on c's component along c and on the tilt norm. The M12 arms run the M12 code unchanged |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m13_selftest_v1.py` (blob `30f65f4684381f8e17cbe368bc83d37b2ff63d80`): PASS 16/16 on the fake model with no GPU (`M13_SELFTEST_R1/`).<br>• Full path: 7116 rows in 56 batches with 44 captures.<br>• Wiring: 34 arms × 208 rows, 33 distinct in 208/208; `sh_fAB_c29` is exempt.<br>• Tilt: tilt arms share r per cell; energy share = 1 + λ² r_share (max err 2.0e-09); tilt gate max 8.6e-16 on 3744 tilt and null rows. Median ‖r‖/‖c‖ is 0.21 and r_share min 0.012 on fake activations. Median \|cos(null, r)\| is at most 0.26.<br>• Size gate on the 208 cpar16_sm rows: max rel err 1.9e-08.<br>• Identities, bitwise: the AB shift with c₃₀ weight 0 = c at 29 only; a k = 64 basis (r = 0) gives the tilt, its λ = −2 version and its null = cs1. Field shifts are unscaled.<br>• Seeds: 5 distinct null seeds per cell, shared by both s and by main and round.<br>• Also checked: ROUND sources and the admission refusals.<br>The analysis dry run on the fake raw exits 0; every verdict reads INCONSISTENT on fake logits, as intended. |
| analysis | `A461_mech_m13_analysis_v1.py` (blob `76489a54a432963547434ff16056d400c274abbd`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, M6 design `43967513`, M6 raw `2147311c`, M7 design `f7d5318c`, M7 raw `0383fccf`, M8 design `14cee4c2`, M8 raw `997c9b71`, M9 design `fe91481e`, M9 raw `c74e5117`, M10 design `f127d850`, M10 raw `755c74e1`, M11 design `53d2bc8d`, M11 raw `393f0d6e`, M12 design `3b2ef50f`, M12 raw `cc79f23a`, G1.0 counterfactuals `06ee06d7` |

## Rules (coded in the design JSON)
- **S, SPEC, SUF and C:** as in M2–M12. SUF = S ≥ ½ S(full) and SPEC. A host is responsive if S(cs1) on its cells exceeds half its cells.
- **Consistency gate:**
  - S(full) = 51, and its 208 rows equal M3 bitwise;
  - S(meanD_host) = 39, and its rows equal M6 bitwise;
  - the 7 M12 arms each have 208 rows equal to M12 bitwise, with S = 39 / 38 / 13 / 27 / 18 / 26 / 20.
  - Otherwise every verdict is INCONSISTENT_WITH_M3_M6_M12.
- **Q1:**
  - SHIFT_AB_SUFFICES iff SUF(sh_fAB). The same rule applies to sh_fAB_c29 (SHIFT_AB_C29_SUFFICES) and sh_fAB_s05 (SHIFT_AB_S05_SUFFICES).
  - SHIFT_AB_NEEDED iff not SUF(sh_xAB).
  - AB_LOCATION_SPECIFIC iff SUF(sh_fAB), neither control is SUF, and S(sh_fAB) > both controls' S. AB_LOCATION_NOT_SPECIFIC iff SUF(sh_fAB) and a control is SUF. Otherwise UNRESOLVED.
  - AB_BY_HOST lists S(sh_fAB)/S(cs1) per responsive host.
- **Q2:** per s ∈ {1, ½, ⅜}, with S₋ = S(rem_m1…), S₀ = S(cs at that s) and S₊ = S(rem_p1…):
  - TILT_OPPOSES iff S₋ ≥ S₀ ≥ S₊ and S₋ > S₊;
  - TILT_SUPPORTS iff S₋ ≤ S₀ ≤ S₊ and S₋ < S₊;
  - TILT_NO_EFFECT iff all three are equal;
  - TILT_MIXED otherwise.
  - Pooled: REM_OPPOSES iff some s OPPOSES and every s OPPOSES or NO_EFFECT; REM_SUPPORTS likewise; REM_NO_EFFECT iff every s is NO_EFFECT; REM_MIXED otherwise.
  - S and C of λ = +2 are reported.
- **Q3:** per responsive host and s ∈ {½, ⅜}, with N = the host S of the 5 nulls:
  - adding r: HARM_BEYOND_NULL iff S(rem_p1) < min N; LESS_HARM_THAN_NULL iff S(rem_p1) > max N; AT otherwise;
  - removing r: REMOVAL_BEYOND_NULL iff S(rem_m1) > max N; REMOVAL_BELOW_NULL iff S(rem_m1) < min N; AT otherwise.
  - Pooled: REM_DIRECTION_SPECIFIC iff some BEYOND and no LESS_HARM / REMOVAL_BELOW; NOT_SPECIFIC iff all AT; REVERSED iff the opposite holds; MIXED otherwise.
- **Always reported:**
  - per-host S of every arm;
  - leave-one-donor-group-out of every verdict;
  - r's energy share and ‖r‖/‖c‖, tilt errors and the energy share of every tilt arm;
  - each null's S, pooled and per host;
  - change norms relative to full.

## Interpretation fixed in advance
- **SHIFT_AB_SUFFICES with AB_LOCATION_SPECIFIC:** the common shift's role sits at the author and block lines of the appended item. With SHIFT_AB_C29_SUFFICES too, the repair needs only that shift and c at the round value.
- **REM_OPPOSES with REM_DIRECTION_SPECIFIC:** tilting c toward the common subspace works against the round-specific repair more than a random tilt of the same size. That locates M12's SUBSPACE_BELOW_COSINE in r.
- **REM_OPPOSES with REM_DIRECTION_NOT_SPECIFIC:** any orthogonal push of that size does the same, so r is not special.
- **Limits:**
  - All M13 arms except `full` are pooled-donor arms, effectively 8 host replicates, of which 3 responded in M9–M12. Per-host S is the honest unit.
  - A host at its ceiling or floor for an arm and all its nulls reads AT.
  - Five null seeds per cell give a coarse per-host range.
  - The location arms change the shift's total size along with its place.
  - The counts are preregistered decision rules on shared donors and hosts, not independent tests.
  - One model (kev-4B) and one simulator family.
