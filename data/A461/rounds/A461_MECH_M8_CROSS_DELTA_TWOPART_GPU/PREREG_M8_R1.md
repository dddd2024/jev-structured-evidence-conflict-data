# A461-MECH-M8 R1: does a cross-kind Δ basis, a low-rank common part plus a round contrast, or the pooled contrast on the common shift carry the round-specific repair? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 3164 kev-4B forwards in 25 batches (24 × 128 + 92).

**Parent:** M7 R1 (edc49cb). All four verdicts below held in 14/14 leave-one-donor-group-out splits.
- **NOT_DELTA_LOWRANK_LE64.** A basis of other donors' *same-kind* differences to the host, {p_B(a) − h_B(a)}, recovers the main repair but loses the round-specificity. dlr64_sm gives S 24 with J_round 18 and frac 0.72; dlr16_sm gives J 51 / 38.
- **LR64_BASIS_LIMITED.** M6's raw basis, rescaled, gives 19 and stays fully round-specific.
- **NOT_MEANDIFF.** This test was close to forced by the design, since a same-kind subtraction cancels the round contrast.
- **RC_INSUFFICIENT.** The pooled round contrast c = mean_D B(ROUND) − mean_D B(new) is inert alone (rcD 0, change 0.04 of full). Inside meanD_host, the same contrast separates J 39 from J 0.

## Questions
1. **Cross-kind Δ basis.** The cell's Δ_B is donor_B(src) − host_B(new). If the basis is built the same way, {p_B(a) − h_B(new) : p ∈ Pool_D, a ∈ new, ROUND}, so that the round contrast is in it, is Δ_B low-rank at matched size?
2. **Two parts.** Is a k-dimensional common part of the donor-new difference, plus the donor's own new-vs-ROUND contrast on the round source, sufficient? Does the pooled contrast do as well?
3. **Contrast on the common shift.** On top of meanD_host's common part, at which scale does the pooled contrast give the round-specific repair? Is its effect non-additive, that is much larger there than on the plain host (M7 rcD)?

## Arms
Every arm patches the L11 `o_proj` input at the 31 span positions of host new, in every question row. Sources are donor new (main) and donor ROUND (round), and X_B is the BULK part (OTHER_ITEMS + CONTEXT) of capture X. Pools are as in M6/M7: Pool_D is the 12 donors outside both the donor's and the host's group. Rescaling is as in M7: α = min(‖Δ‖ / ‖PΔ‖, 10) per row and span position.

| arm | patch | role |
|---|---|---|
| `full` | the M3 all-heads patch | bitwise anchor (S 51) |
| `meanD_host` | host − h_B + mean_{Pool_D} p_B(src), as in M6 | bitwise anchor of the M6 rows (S 39) |
| `dlr64_sm` | the M7 arm (same-kind Δ basis, rescaled) | M7 replay (S 24) |
| `rand64_sm` | the M7 arm (seeded random 64-frame, same seed) | M7 replay (S 1); null |
| **`xdlr{k}_sm`**, k ∈ {4, 16, 64} | host + α U_kU_kᵀ Δ_B, where U_k is the top-k right singular vectors of {p_B(a) − h_B(new)} (744 vectors) | Q1 |
| `xdlr64` | the same at k = 64, not rescaled | Q1 |
| **`tp{k}`**, k ∈ {16, 64} | host + α U_kU_kᵀ Δ_B(new) [M7 same-kind basis], plus c_own = d_B(ROUND) − d_B(new) on the round source only | Q2 |
| **`tpD64`** | the same at k = 64 with the pooled contrast c = mean_D B(ROUND) − mean_D B(new) | Q2: contrast source |
| **`cs{s}`**, s ∈ {0, 0.5, 1, 2} | host − h_B + ½(mean_D B(new) + mean_D B(ROUND)), then − (s/2)c on the main source and + (s/2)c on the round source | Q3 |

- **tp main rows.** The main patch of tp{k} (scale 0 on its contrast) is exactly the M7 dlr{k}_sm main patch. So tp asks only what adding a contrast to the round source does.
- **The cs arms.**
  - At full width, tp's round patch is host + Δ_B(round), the M5 only_BULK round patch.
  - cs1 is meanD_host up to float rounding.
  - cs0 has identical main and round patches, so its S is 0 by construction. Its J count measures the common shift alone.
  - rcD (M7) is the same ∓c on the plain host. So C(cs2) against C(rcD) measures how much the base changes the contrast's effect.
- **Pooled arms.** The cs arms and the tpD64 contrast vary with the donor only through the pool exclusion. They are effectively 8 hosts.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m8_freeze_v1.py` (blob `fd2bcee5`; CPU + tokenizer only). Derived from the M7 freeze by checked substitutions. It cross-checks the M3, M4, M6 and M7 key classes, the M6/M7 pools, the wiring of the M6 meanD_host rows, the M7 dlr64_sm / rand64_sm patch fields, and the tp main patches against M7 dlr{k}_sm |
| manifest blob | `83d34f9e78187783aaeb5b89645a60bbae3c68e8` |
| design blob | `14cee4c2cffe30d78338de8063c72110f223f0bb`: rules under `preregistered_analysis` |
| runner blob | `7cd3ef9deb1803324939de0e598bccb83514ba6d`, derived from the M7 runner ba50db52 by checked substitutions. New ops are `twopart` and `cshift`; cross-kind pairs are allowed in the Δ basis |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m8_selftest_v1.py` (blob `8e04a1b2`): **PASS 16/16** in `M8_SELFTEST_R1/`. Runner size gate max rel err 3.1e-7. Identities: the full patch with the host as source and a zero-contrast two-part patch are bitwise no-ops on their reference; cs0 main == round bitwise; tp64 / tpD64 main == dlr64_sm main bitwise. At the fake width (64), xdlr64_sm (3.8e-6), dlr64_sm (4.0e-6) and a single-capture contrast shift (0) all equal host + Δ_B, and cs1 equals meanD_host (9.5e-6). Analysis dry run end to end on the fake output (fake verdict INCONSISTENT_WITH_M3_M6_M7, as expected) |
| analysis | `A461_mech_m8_analysis_v1.py` (blob `a09ce224`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, M6 design `43967513`, M6 raw `2147311c`, M7 design `f7d5318c`, M7 raw `0383fccf`, G1.0 counterfactuals `06ee06d7` |

## Design
- **Captures:** 44, as in M4–M7. They are fail-closed on class additivity, and 36 must replay M1 bitwise.
- **Patches:** 15 arms × 2 sources × 104 cells = 3120.
- **Gates checked in the run:**
  - the 208 `full` rows must equal M3 bitwise;
  - the 208 `meanD_host` rows must equal M6 bitwise.
- **Size gate:** applies to every rescaled projection, including the low-rank part of tp, fail-closed at 1e-3 relative.

## Rules (coded in the design JSON)
- **S, SPEC, SUF:** as in M2–M7. SUF(arm) iff S(arm) ≥ ½ S(full) and SPEC(arm).
- **NULL** holds iff S(rand64_sm) ≤ 5 and not SPEC(rand64_sm).
- **Consistency gate:** all of the following, otherwise every verdict is INCONSISTENT_WITH_M3_M6_M7.
  - S(full) = 51, with 208 rows bitwise equal to M3;
  - S(meanD_host) = 39, with 208 rows bitwise equal to M6;
  - S(dlr64_sm) = 24 and S(rand64_sm) = 1, as in M7.
- **M7 replay rows:** their bitwise equality is reported, not gated, because it depends on CPU SVD/QR reproducibility. The replay rows are dlr64_sm, rand64_sm, and the tp16/tp64/tpD64 main rows against M7 dlr16_sm/dlr64_sm.
- **Q1:** k\* is the smallest k ∈ {4, 16, 64} with SUF(xdlr{k}_sm).
  - **XDELTA_LOWRANK:k\*** if NULL holds;
  - **XDELTA_LOWRANK_UNRESOLVED:k\*** if NULL fails;
  - **NOT_XDELTA_LOWRANK_LE64** if there is no k\*.
- **Q2:** k\* is the smallest k ∈ {16, 64} with SUF(tp{k}).
  - **TWOPART:k\*** if NULL holds, **TWOPART_UNRESOLVED:k\*** if NULL fails, **NOT_TWOPART** if there is no k\*.
  - Contrast source: **POOLED_CONTRAST_SUFFICES** if SUF(tpD64); **OWN_CONTRAST_NEEDED** if SUF(tp64) and not SUF(tpD64); **CONTRAST_SOURCE_NA** otherwise.
- **Q3:** s\* is the smallest s ∈ {0.5, 1, 2} with SUF(cs{s}).
  - **CS_SUFFICIENT:s\*** if it exists, else **CS_NONE**.
  - Non-additivity uses C(arm) = the median over cells of dM_main − dM_round. **CONTRAST_NONADDITIVE** iff C(cs2) > 0 and C(cs2) ≥ 3 |C(rcD)|, with rcD taken from the pinned M7 rows. Otherwise **CONTRAST_ADDITIVE_OR_WEAK**.
- **Always reported:**
  - the per-arm table and per-host S;
  - leave-one-donor-group-out of every verdict;
  - energy, α and capped share;
  - the change norm of every arm relative to full;
  - the M7 replay bitwise counts;
  - the cs0 main == round row count.

## Interpretation fixed in advance
- **XDELTA_LOWRANK:k:** Δ_B, round contrast included, is carried by a k-dimensional subspace of other donors' differences to the host's new BULK, at matched size, while a random subspace at that size is not.
- **NOT_XDELTA_LOWRANK_LE64:** adding the round kind to the basis does not make Δ_B low-rank.
- **TWOPART:k:** a k-dimensional common part plus the donor's own round contrast suffices.
  - **POOLED_CONTRAST_SUFFICES:** the contrast need not be the cell's own.
  - **OWN_CONTRAST_NEEDED:** it must be.
- **CS_SUFFICIENT:s:** on the pooled common shift, the pooled contrast at scale s gives the round-specific repair.
- **CONTRAST_NONADDITIVE:** the same contrast moves the main-vs-round margin at least 3× more on the common shift than on the plain host.
- **Limits:**
  - The pooled arms are close to 8 host-level replicates, so per-host S is the honest unit.
  - The cs arms are not size-matched; their change norms are reported.
  - The counts are preregistered decision rules on shared donors and hosts, not independent tests.
  - One model (kev-4B) and one simulator family.
