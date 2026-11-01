# A461-MECH-M8 R1: result (does a cross-kind Δ basis, a low-rank common part plus a round contrast, or the pooled contrast on the common shift carry the round-specific repair?)

**Run:**
- 3164/3164 kev-4B forwards in 25 batches (24 × 128 + 92); 0 denied; one model load; elapsed 4808 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`: the 36 M1 replays, the 208 `full` rows (vs M3) and the 208 `meanD_host` rows (vs M6) are bitwise equal.
- Raw blob `997c9b71054ee2adec472a5410705068511650aa`.
- The run follows prereg 2a4fea7 under the standing GPU authorization. The pre-model gate passed (`COMPLETE_A461_MECH_M8_PRE_MODEL_GATE`, saved as `M8_GPU_R1/pre_model_gate_receipt.json`), and there was a single ledger attempt (`A461_MECH_M8_GPU_20261029_R1`, 3164 reserved).

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- **Size gate (all `_sm` arms, rand64_sm and the low-rank part of tp):** passed in the run (fail-closed at 1e-3 relative per row and span position).
- The captures stay on the server under `M8_GPU_RUNS/ATTEMPT_R1/captures`. All files match the run's `SHA256SUMS` there. Every non-capture file was fetched here and verified against the same `SHA256SUMS`.

**Analysis:** `A461_mech_m8_analysis_v1.py` (blob a09ce224, frozen before the run), run automatically by the server launch script after the receipt read COMPLETE (exit 0). Output: `M8_ANALYSIS_R1/m8_analysis.json` (sha256 eb7b1c3b…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51, 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 rows bitwise equal to M6; S(dlr64_sm) = 24 and S(rand64_sm) = 1, as in M7 |
| NULL (rand64_sm S ≤ 5, not SPEC) | **holds**: S = 1 |
| **Q1 cross-kind Δ basis** | **XDELTA_LOWRANK:16**: xdlr16_sm S 36, SPEC; xdlr4_sm S 13, not SPEC |
| **Q2 two parts** | **TWOPART:16**: tp16 S 44, SPEC |
| **Q2 contrast source** | **POOLED_CONTRAST_SUFFICES**: tpD64 S 38, SPEC |
| **Q3 contrast on the common shift** | **CS_SUFFICIENT:0.5**: cs05 S 38, SPEC (frac exactly 0.75) |
| **Q3 non-additivity** | **CONTRAST_NONADDITIVE**: C(cs2) = 1.149 vs 3 · \|C(rcD, M7)\| = 0.206 (ratio 16.7) |

**Leave one donor group out:** 14/14 splits give XDELTA_LOWRANK:16, TWOPART:16, POOLED_CONTRAST_SUFFICES and CONTRAST_NONADDITIVE, and the null holds in all of them. The cshift verdict is CS_SUFFICIENT:0.5 in 12/14 splits and CS_SUFFICIENT:1.0 in 2/14 (run-140, run-212). The 0.5 result sits exactly on the frac 0.75 threshold.

**M7 replay rows (reported, not gated):** all bitwise equal: dlr64_sm 208/208, rand64_sm 208/208, and the tp16 / tp64 / tpD64 main rows 104/104 each against M7 dlr16_sm / dlr64_sm. cs0 main == round: 104/104 rows.

## Table (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority; C = median dM_main − dM_round)
| arm | S | J main / round | frac | grp | SPEC | median dM main / round | C | change norm / full |
|---|---|---|---|---|---|---|---|---|
| full (M3 all-heads) | 51 | 58 / 7 | 0.99 | 14 | ✓ | +0.35 / −0.37 | 0.71 | 1.00 |
| meanD_host (M6 anchor) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.66 | 0.60 | 0.62 |
| dlr64_sm (M7 replay) | 24 | 42 / 18 | 0.72 | 13 | ✗ | +0.23 / +0.03 | 0.09 | 0.78 |
| rand64_sm (null) | 1 | 1 / 1 | 0.47 | 4 | ✗ | −0.03 / −0.01 | −0.01 | 0.78 |
| xdlr4_sm | 13 | 32 / 27 | 0.63 | 10 | ✗ | +0.25 / +0.07 | 0.03 | 0.78 |
| **xdlr16_sm** | **36** | 40 / 5 | 0.93 | 13 | ✓ | +0.26 / −0.62 | 0.61 | 0.78 |
| xdlr64_sm | 34 | 41 / 7 | 0.97 | 14 | ✓ | +0.23 / −0.66 | 0.65 | 0.78 |
| xdlr64 (not rescaled) | 33 | 39 / 6 | 0.97 | 14 | ✓ | +0.21 / −0.55 | 0.56 | 0.65 |
| **tp16** | **44** | 51 / 7 | 0.99 | 14 | ✓ | +0.28 / −0.67 | 0.70 | 0.78 |
| tp64 | 37 | 42 / 5 | 1.00 | 14 | ✓ | +0.23 / −0.61 | 0.57 | 0.78 |
| **tpD64** (pooled contrast) | **38** | 42 / 4 | 0.98 | 14 | ✓ | +0.23 / −0.53 | 0.52 | 0.77 |
| cs0 (common shift alone) | 0 | 28 / 28 | 0.00 | 0 | ✗ | +0.35 / +0.35 | 0 | 0.61 |
| **cs05** | **38** | 39 / 1 | 0.75 | 14 | ✓ | +0.28 / +0.19 | 0.16 | 0.62 |
| cs1 (≈ meanD_host) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.66 | 0.60 | 0.62 |
| cs2 | 36 | 36 / 0 | 1.00 | 14 | ✓ | +0.20 / −1.08 | 1.15 | 0.63 |

M7 references: dlr16_sm S 17 (J 51 / 38), rcD S 0 (C 0.069, change 0.04).

## Subspace statistics (median over rows of the per-row median)
| arm | energy ‖PΔ_B‖/‖Δ_B‖ | energy min | basis sv share at k | α median | α max | capped share |
|---|---|---|---|---|---|---|
| xdlr4_sm | 0.41 | 0.04 | 0.35 | 2.46 | 10.0 | 0.009 |
| xdlr16_sm | 0.65 | 0.16 | 0.64 | 1.53 | 6.14 | 0 |
| xdlr64_sm / xdlr64 | 0.84 | 0.40 | 0.87 | 1.18 / 1 | 2.51 / 1 | 0 |
| dlr64_sm / tp64 / tpD64 | 0.84 | 0.40 | 0.87 | 1.18 | 2.50 | 0 |
| tp16 (= M7 dlr16 basis) | 0.65 | 0.19 | 0.62 | 1.54 | 5.27 | 0 |
| rand64_sm | 0.12 | 0.09 | — | 8.05 | 11.18 (uncapped) | — |

The cross-kind basis captures the same share of Δ_B as the same-kind basis at every k (0.41 / 0.65 / 0.84). The difference is in what that share contains, not how much of it there is.

## Per-host S
| host | full | meanD_host | cs05 | cs2 | xdlr16_sm | xdlr64_sm | tp16 | tp64 | tpD64 | dlr64_sm | rand64_sm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1fb5651c | 13 | 13 | 13 | 13 | 10 | 12 | 13 | 12 | 12 | 9 | 0 |
| 264c458d | 10 | 13 | 12 | 12 | 10 | 8 | 10 | 8 | 9 | 5 | 1 |
| 4bcbaf15 | 11 | 13 | 13 | 11 | 7 | 8 | 9 | 10 | 10 | 7 | 0 |
| 75642418 | 7 | 0 | 0 | 0 | 4 | 3 | **6** | 3 | 2 | 0 | 0 |
| 2c9118bb | 5 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 8ae85754 | 4 | 0 | 0 | 0 | 4 | 3 | **6** | 4 | 5 | 3 | 0 |
| 1c7158b6 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2a4f596d | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

cs0 is 0 at every host by construction; cs1 equals meanD_host at every host.

## Reading, with its limits
1. **Putting the round kind into the basis makes Δ_B low-rank (XDELTA_LOWRANK:16).**
   - With the same energy share as M7's same-kind basis, the cross-kind basis restores the round-specificity. At k = 64, J_round drops from 18 to 7, and frac rises from 0.72 to 0.97. At k = 16, S goes from 17 to 36.
   - This confirms the M7 reading. The same-kind basis lacked the directions along which the round source pushes the host away from conflict, and a basis that contains ROUND-minus-host-new differences has them.
   - k = 4 is not enough (S 13; J 32 / 27, not specific), so the round-specific part needs more than a handful of directions. S is not monotone in k (36 at 16, 34 at 64). This is within the noise of a 104-cell count.
   - Limit: the basis is built from other donors' ROUND captures, so "low-rank" here means low-rank in a pool that already contains the contrast direction. It is not a basis-free statement.
2. **A common part plus a contrast vector suffices, and the contrast need not be the cell's own (TWOPART:16, POOLED_CONTRAST_SUFFICES).**
   - tp16's main rows are M7 dlr16_sm's main rows bitwise (J_main 51). Adding the donor's own ROUND − new contrast to the round source alone cuts J_round from 38 to 7, which gives S 44. That is the highest S of any arm short of full, and it reaches more hosts than any pooled arm (5 of the 6 hosts full repairs at ≥ 4).
   - With the pooled contrast instead (tpD64), S is 38 against 37 for the own contrast at the same k. So the round contrast that does the work is shared across donors, not cell-specific.
3. **On the common shift, half the pooled contrast already gives the repair, and the effect is strongly non-additive (CS_SUFFICIENT:0.5, CONTRAST_NONADDITIVE).**
   - The common shift alone (cs0) moves both sources toward conflict equally (J 28 / 28, dM +0.35 each).
   - Adding ∓ ¼c to the two sources (cs05) separates them to J 39 / 1. S 38 is almost the full meanD_host value, but the SPEC margin is at the threshold (frac 0.75; 2/14 splits move s\* to 1).
   - From s = 0.5 to 2, S stays at 36–39 while C grows from 0.16 to 1.15. The repair saturates and the extra contrast only drives the round source further away from conflict.
   - The same 2c gap moves C by 0.069 on the plain host (M7 rcD) and by 1.149 on the common shift: 16.7×. The contrast is only read once the common shift is present. This is a measurement of the gain, not yet of the mechanism behind it.
   - Limits: the cs arms are effectively 8 host replicates and repair only the 3 hosts that meanD_host repairs. They are not size-matched (0.61–0.63 of full). The SPEC criterion at cs05 passes at exactly 0.75.
4. **What still separates these arms from full.**
   - All the pooled arms (meanD_host, cs*) are 0 at hosts 75642418, 2c9118bb and 8ae85754. The cell-specific low-rank arms (xdlr, tp) recover part of 75642418 and 8ae85754. So on those hosts the cell's own common part is needed, while the contrast can still be pooled.
   - Host 2c9118bb (full 5) is almost untouched by every factored arm. Hosts 1c7158b6 and 2a4f596d are repaired by nothing in M3–M8.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.
- Most of S comes from three hosts (1fb5651c, 264c458d, 4bcbaf15); per-host S is the honest unit for the pooled arms.

## Where the M1–M8 chain now stands
- M1: the span's L11 representation carries a signed, round-specific conflict evaluation.
- M2: L11 full attention writes it.
- M3: heads 8–14 write it together, with head 10 most necessary.
- M4: the write reads mainly from the other messages and the state header, not the partner vote.
- M5: the context-wide (BULK) part carries the evaluation in its direction, and a third donor's BULK keeps 51/51.
- M6: one pooled donor BULK component repairs 39/104; not captured by a ≤ 64-dimensional raw basis.
- M7: the repair splits into a conflict-raising part common to both source kinds and a small round contrast that does nothing alone.
- **M8:**
  - The repair factors as a **16-dimensional common part plus one shared contrast vector**: tp16 S 44 of 51, with the contrast pooled over donors working as well as the cell's own.
  - Δ_B itself is low-rank (16) once the basis contains the round kind.
  - The contrast acts **multiplicatively with the common shift**: 17× larger effect on the margin than on the plain host, and saturating from a quarter of its pooled size per source.

## Suggested M9 (not frozen)
- **Gain map:** a 2-D grid of common-shift scale t ∈ {0, ¼, ½, 1} × contrast scale s ∈ {0, ½, 1} on meanD_host's construction, per host. This gives the shape of the non-additivity (threshold vs product) rather than one ratio.
- **Where the contrast is read:** apply the pooled contrast at one head group at a time (M3's heads 8–14, head 10 alone) on top of the common shift, to see whether the gating sits in the same heads that write the evaluation.
- **Contrast inside the common subspace:** split c into its projection on the xdlr16 / dlr16 basis and the orthogonal rest, and test tpD16 with each part, to see whether the active contrast is aligned with the common part.
- Pending separately: replication of the M2/M3 chain on SecJev-0.8B.
