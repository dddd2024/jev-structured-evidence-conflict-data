# A461-MECH-M12 R1: is c at position 30 a counter-signal, which fields of the appended item must carry the common shift, and is the subspace split more than cosine to c? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 7740 kev-4B forwards in 61 batches (60 × 128 + 60).

**Parent:** M11 R1 (76e6537). The pooled contrast c = mean_D B(ROUND) − mean_D B(new) sits only at span positions 29 and 30.
- **AMPLITUDE_ONLY_EXCLUDED:** c at 30 scaled to c₂₉'s norm repairs 1 cell, and larger c₃₀ suppresses the main flip (J_main 30 → 1 at ×4).
- **SHIFT_NEEDS_CONTEXT_POSITIONS:** the shift at 29–30 alone flips nothing at any size.
- **Split by host:** 264c458d is substantively OUTSIDE (cperp 13, cpar 1, null 0); 4bcbaf15 is BOTH; SPLIT_NULL10 fails (59 of 69 null repairs on 1fb5651c). The null frames keep 0.4 % of c's energy (α 27–39), so they are not matched to cpar's or cperp's overlap with c: cperp keeps about 67 % of c's energy (cosine ≈ 0.82), cpar about 33 % (≈ 0.58).

**The 31-token span** is the appended item, identical in layout in all 44 captures (checked by the freeze from the decoded tokens): `␠ - author: v<n>⏎` 0–6, `␣␣␣ block: b<n>⏎` 7–12, `␣␣␣ kind: vote⏎` 13–17, `␣␣␣ received: <nn>⏎` 18–24, `␣␣␣ round: ␠` 25–28, the round value 29 (the token ROUND changes), `⏎` 30.

## Questions
1. **Position 30 as a counter-signal.** With c₂₉ fixed, does c₃₀'s weight w ∈ {−1, 0, +1, +2} change the repair? Tested at s = ¼, where w = 0 repairs 13 cells (room in both directions), and at s = ½ and 1.
2. **Which fields carry the shift.** Common shift (t = 1) at one field plus 29–30, or everywhere except one field, with the full c.
3. **Subspace vs cosine.** Per row and position, a null with the norm and the cosine to c of cpar16_sm (or cperp16_sm), with its remainder orthogonal to c drawn at random. Does the subspace part repair more (or less) than such nulls, per responsive host?

## Arms (all patch the L11 `o_proj` input at the 31 span positions of host new in every question row; sources donor new = main, donor ROUND = round; Pool_D, mid and c as in M8–M11; common shift t = 1; contrast ∓ s/2 c)
| arm | patch | role |
|---|---|---|
| `full` | the M3 all-heads patch | bitwise anchor (S 51) |
| `meanD_host` | as M6 | bitwise anchor (S 39) |
| `cs1`, `cpos29`, `cpos29_s05`, `cpos29_s025`, `cpar16_sm`, `cperp16_sm`, `sh2930`, `sh0_28` | the M11 arms with identical patch fields | bitwise anchors (S 39 / 39 / 38 / 13 / 27 / 39 / 0 / 13) |
| **`cw30_m1`**, `cw30_p2` | c₂₉ + w c₃₀ with w = −1 / +2, s = 1 | Q1 |
| `cs_s05`, **`cw30_m1_s05`**, `cw30_p2_s05` | w = +1 / −1 / +2 at s = ½ | Q1 |
| `cs_s025`, **`cw30_m1_s025`** | w = +1 / −1 at s = ¼ | Q1 (primary) |
| `sh_fAUTH` … `sh_fRKEY` | shift at one field + 29–30 | Q2 sufficiency |
| `sh_xAUTH` … `sh_xRKEY` | shift at all 31 positions except one field | Q2 necessity |
| `ccos_par_s1` … `s5`, `ccos_perp_s1` … `s5` | cosine-matched nulls of cpar16_sm / cperp16_sm (seeds `A461_M12_CCOS\|part\|16\|d\|h\|i`, shared by main and round) | Q3 |

- The w = 0 arms are cpos29 / cpos29_s05 / cpos29_s025, and the w = +1, s = 1 arm is cs1 (M11 replays).
- In the M9–M11 captures c is exactly 0 outside 29–30, so the weight acts on c₃₀ only. c₃₀ holds about 11 % of c's energy (min 9 %); at w = +2 the contrast's energy is about 1.34 × ‖c‖².
- The nulls keep the part's per-(row, position) norm and cosine to c exactly, so they test what the part's direction adds beyond its overlap with c.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m12_freeze_v1.py` (blob `0601108125ee18e4f44e28314f62d06bb6e741e9`; CPU + tokenizer only), derived from the M11 freeze by checked substitutions. It cross-checks the M3–M11 key classes and pools, the span width (31), the field layout of every capture, that the 10 replay arms' patch fields equal the M11 rows' fields, and that the 5 null seeds per cell and part are distinct |
| manifest blob | `959a010675081bf78eb060f3c402edd8c100d841` |
| design blob | `3b2ef50f3f45274249b1ed05dcc578d67807f173`: the rules are under `preregistered_analysis` |
| runner blob | `6dcaff0e2eed15e3296a11f94d057fcf23c5a4fe`, derived from the M11 runner 54479b04 by checked substitutions. It adds `contrast_pos_weight` (c at listed positions times w, \|w\| ≤ 10) and the contrast_proj `null_seed` (cosine-matched null, fail-closed norm and cosine gate at 1e-6), and records each part's median cosine to c. The M11 arms run the M11 code unchanged |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m12_selftest_v1.py` (blob `ff208f410384b78f060cb7f9f118e9bf56bc1d62`): PASS 16/16 on the fake model with no GPU (`M12_SELFTEST_R1/`): wiring of the 37 arms (32 distinct in 208/208; the weighted arms exempt), the weighted energy share 1 + (w² − 1) e₃₀ (max err 1.0e-06; on fake weights e₃₀ is ≈ 0, so the weight is checked mainly by the identities), the size gate on 2496 part and null rows (max rel err 1.9e-08; part factor max 9.13), the cosine-null gate (max 4.4e-16), the identities (weight 1 = cs1 and weight 0 = cpos29 bitwise; the null of a cosine-1 part = cs1 to 7.2e-07), 5 distinct null seeds per cell and part, the ROUND sources, and the admission refusals. The analysis dry run on the fake raw exits 0 (every verdict INCONSISTENT on fake logits, as intended) |
| analysis | `A461_mech_m12_analysis_v1.py` (blob `13d2737915b399f978793b4bc0535ef2d284f18a`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, M6 design `43967513`, M6 raw `2147311c`, M7 design `f7d5318c`, M7 raw `0383fccf`, M8 design `14cee4c2`, M8 raw `997c9b71`, M9 design `fe91481e`, M9 raw `c74e5117`, M10 design `f127d850`, M10 raw `755c74e1`, M11 design `53d2bc8d`, M11 raw `393f0d6e`, G1.0 counterfactuals `06ee06d7` |

## Rules (coded in the design JSON)
- **S, SPEC, SUF and C:** as in M2–M11. SUF = S ≥ ½ S(full) and SPEC.
- **Consistency gate:**
  - S(full) = 51, and its 208 rows equal M3 bitwise;
  - S(meanD_host) = 39, and its rows equal M6 bitwise;
  - the 8 M11 arms each have 208 rows equal to M11 bitwise, with S = 39 / 39 / 38 / 13 / 27 / 39 / 0 / 13.
  - Otherwise every verdict is INCONSISTENT_WITH_M3_M6_M11.
- **Q1 position-30 weight (at s = ¼):** with S₋ = S(cw30_m1_s025), S₀ = S(cpos29_s025), S₊ = S(cs_s025):
  - P30_OPPOSES iff S₋ > S₀ ≥ S₊ and S₋ > S₊;
  - P30_SUPPORTS iff S₊ > S₀ ≥ S₋ and S₊ > S₋;
  - P30_NO_EFFECT iff S₋ = S₀ = S₊;
  - P30_MIXED otherwise.
  - Dose: WSMIN(w) = the smallest s ∈ {¼, ½, 1} with SUF for w = −1, 0, +1 (and s ∈ {½, 1} for w = +2); FLIP_LOWERS_THRESHOLD iff WSMIN(−1) < WSMIN(0).
- **Q2 fields:** NEEDED(F) iff not SUF(sh_x\<F\>); SUFFICES(F) iff SUF(sh_f\<F\>). Verdicts SHIFT_FIELDS_NEEDED:\<F,…|NONE\> and SHIFT_FIELDS_SUFFICE:\<F,…|NONE\>.
- **Q3 cosine null by host:**
  - A host is responsive if S(cs1) on its cells exceeds half its cells.
  - Per responsive host and part: BEYOND iff S(c\<part\>16_sm) > the maximum host S over its 5 nulls; BELOW iff < the minimum; AT otherwise.
  - COS_SPLIT_BY_HOST:\<host8\>=par:\<v\>/perp:\<v\>,….
  - Pooled: SUBSPACE_EXPLAINED_BY_COSINE iff every responsive host is AT for both parts; SUBSPACE_BEYOND_COSINE iff some BEYOND and no BELOW; SUBSPACE_BELOW_COSINE iff some BELOW and no BEYOND; SUBSPACE_COSINE_MIXED otherwise.
- **Always reported:**
  - per-host S of every arm;
  - leave-one-donor-group-out of every verdict;
  - energy shares, factors, capped shares and cosines;
  - each null's S, pooled and per host;
  - change norms relative to full.

## Interpretation fixed in advance
- **P30_OPPOSES:** c at the newline after the round value works against the round-specific repair that c at the round value drives, as cpos30_s4 suggested in M11; the pooled contrast is then c₂₉ minus a counter-signal. **P30_SUPPORTS:** c₃₀ helps once c₂₉ is present, though it does nothing alone.
- **SHIFT_FIELDS_NEEDED** lists the fields whose shift cannot be dropped; **SHIFT_FIELDS_SUFFICE** the fields whose shift, with 29–30, suffices. NONE / NONE means the shift's role is spread over fields, each dispensable and none sufficient.
- **SUBSPACE_EXPLAINED_BY_COSINE:** the parts of c inside and outside the 16-dim common subspace act as any direction with the same cosine to c would, so the M9–M11 split reading reduces to "closer to c works better". **BEYOND:** the subspace part acts beyond its cosine. **BELOW:** it acts less than a random direction of the same cosine.
- **Limits:**
  - All M12 arms except `full` are pooled-donor arms, effectively 8 host replicates (3 responded in M9–M11). Per-host S is the honest unit, and 1fb5651c flips under almost any contrast-sized push.
  - Five null seeds per part give a coarse per-host range; a part sitting at the edge reads AT.
  - The field arms change the shift's total size along with its location; the per-host S and the change norms are reported for that reason.
  - The counts are preregistered decision rules on shared donors and hosts, not independent tests.
  - One model (kev-4B) and one simulator family.
