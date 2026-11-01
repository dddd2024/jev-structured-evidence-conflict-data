# A461-MECH-M7 R1: is the donor-minus-host BULK difference low-rank, one mean-difference direction, or a donor-free round contrast? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 2748 kev-4B forwards in 22 batches (21 × 128 + 60).

**Parent:** M6 R1 (18aae99). Both verdicts below held in 14/14 leave-one-donor-group-out splits.
- **SHARED_DONOR_COMPONENT.** The BULK part (OTHER_ITEMS + CONTEXT key-class contributions of the L11 span write), pooled over 12 other donors, repairs hosts round-specifically: meanD_host 39, meanD_donor 57.
- **The host-pool null is not empty.** The pooled BULK of other hosts repairs 17, fully round-specific, at a similar change norm. At host level this is 3 hosts against about 1.3.
- **NOT_LOWRANK_LE64.** The cell's Δ_B projected on the top-64 directions of other donors' *raw* BULK contributions repairs 10. The basis was uncentred and the projection was not rescaled (change 0.55 of full).

## Questions
1. Is the repairing part of Δ_B low-rank in a basis of **other donors' differences to the same host**, at matched size?
2. Was M6's lr64 failure a **size** effect?
3. Does **one fixed mean-difference vector** (pooled donor BULK minus pooled host BULK) repair hosts?
4. Does the **new-vs-ROUND contrast** of pooled BULK, with no repairing donor involved, produce the round-specific pattern?

Definitions:
- All arms patch the L11 `o_proj` input at the 31 span positions of host new, in every question row.
- Sources: donor new (main) and donor ROUND (round). X_B is the BULK part of capture X, and Δ_B = donor_B − host_B, from the same source kind.
- Pools are as in M6 (checked equal to the M6 design). Pool_D(d, h) is the 12 donors from neither the donor's nor the host's group. Pool_H(d, h) is the other hosts outside the donor's group (5–7).
- **Rescaling ("_sm"):** per row and span position, α = min(‖Δ_B‖ / ‖P Δ_B‖, 10), where P is the arm's projection. The patch is host + α·P Δ_B. α, the energy ‖P Δ_B‖/‖Δ_B‖ and the share of positions capped at 10 are recorded.

| arm | patch | question |
|---|---|---|
| `full` | the M3 all-heads patch | bitwise anchor (S 51) |
| `meanD_host` | host − host_B + mean_{Pool_D} p_B, as in M6 | bitwise anchor of the M6 rows (S 39) |
| **`dlr{k}_sm`**, k ∈ {1, 4, 16, 64} | host + α U_kU_kᵀ Δ_B. U_k is the top-k right singular vectors of {p_B(a) − h_B(a) : p ∈ Pool_D, a ∈ new, ROUND}: 744 vectors of the other donors' differences to the same host | Q1 |
| `dlr64` | the same at k = 64, not rescaled | comparison with M6's lr64 (10) |
| **`lr64_sm`** | M6's raw-basis lr64 projection (same basis tags and order), rescaled | Q2 |
| **`rand64_sm`** | host + Q Q^T Δ_B rescaled to exactly ‖Δ_B‖, with Q a seeded random orthonormal 64-frame per cell | null for Q1–Q3 |
| **`mdir1`**, `mdir2` | host + s·(mean_{Pool_D} p_B(src) − mean_{Pool_H} h'_B(src)), s = 1, 2 | Q3 |
| **`rcH`** | host + σ·(mean_{Pool_H} h'_B(ROUND) − mean_{Pool_H} h'_B(new)), with σ = −1 for the main source and +1 for the round source | Q4: other hosts' round contrast |
| `rcD` | the same with Pool_D | Q4: other donors' round contrast |

- The Δ basis contains −h_B in every vector. It is donor-free (Pool_D never holds d) but host-specific, and it is fit on both arms.
- `mdir1` − `meanD_host` = host_B − mean_H B: mdir1 replaces the host's own BULK reference by the pooled hosts' BULK.
- The rc arms use the cell's donor only through the pool exclusion. Their main and round patches are mirror images (∓ the same contrast), so S(rc) asks whether subtracting the contrast gives JOINT while adding it does not.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m7_freeze_v1.py` (blob `dec6fec0`; CPU + tokenizer only). Derived from the M6 freeze; it cross-checks the M3, M4 and M6 key classes, the M6 pools and the wiring of the M6 meanD_host rows |
| manifest blob | `17ee5d66a9c28f91d6c8d7abfc5b4bb3e2c53f6a` |
| design blob | `f7d5318c1bfe24521831cc322be08bd6ed08fa17`: rules under `preregistered_analysis` |
| runner blob | `ba50db52993c3daf950287ab787ab8276cc2cac4`, derived from the M6 runner 79c10a67 by checked substitutions |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m7_selftest_v1.py` (blob `cd6cb207`), derived from the M6 self-test: **PASS 16/16** in `M7_SELFTEST_R1/`. Rescaled-arm size gate max rel err 2.6e-6. Identities: the full patch with the host as source and a mean difference of a capture with itself are bitwise no-ops; at the fake model's full width (64), mdir with plus = donor and minus = host (5.7e-6), dlr64_sm (4.0e-6) and lr64_sm (4.8e-6) all equal host + Δ_B. Analysis dry run end to end on the fake output (fake verdict INCONSISTENT_WITH_M3_M6, as expected); a one-cell fake smoke run passed before |
| analysis | `A461_mech_m7_analysis_v1.py` (blob `7c4f9169`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, M6 design `43967513`, M6 raw `2147311c`, G1.0 counterfactuals `06ee06d7` |

## Design
- **Captures:** 44, as in M4–M6. They are fail-closed on class additivity, and 36 must replay M1 bitwise.
- **Patches:** 13 arms × 2 sources × 104 cells = 2704.
- **Gates checked in the run:**
  - the 208 `full` rows must equal M3 bitwise;
  - the 208 `meanD_host` rows must equal M6 bitwise.
- **Size gate:** every rescaled row's change must equal α‖P Δ_B‖ per row and span position, within 1e-3 relative (fail-closed).

## Rules (coded in the design JSON)
- **S, SPEC:** as in M2–M6. **SUF(arm)** iff S(arm) ≥ ½ S(full) and SPEC(arm).
- **NULL** holds iff S(rand64_sm) ≤ 5 and not SPEC(rand64_sm).
- **Consistency gate:** S(full) = 51 with 208 rows bitwise equal to M3, and S(meanD_host) = 39 with 208 rows bitwise equal to M6. Otherwise every verdict is INCONSISTENT_WITH_M3_M6.
- **Delta low-rank (Q1):** k\* is the smallest k with SUF(dlr{k}_sm).
  - **DELTA_LOWRANK:k\*** if NULL holds;
  - **DELTA_LOWRANK_UNRESOLVED:k\*** if NULL fails;
  - **NOT_DELTA_LOWRANK_LE64** if there is no k\*.
- **M6 size (Q2):** **LR64_SIZE_LIMITED** if SUF(lr64_sm), else **LR64_BASIS_LIMITED**.
- **Mean difference (Q3):** s\* is the smallest s ∈ {1, 2} with SUF(mdir{s}).
  - **MEANDIFF_DIRECTION:s\*** if NULL holds;
  - **MEANDIFF_UNRESOLVED:s\*** if NULL fails;
  - **NOT_MEANDIFF** otherwise.
- **Round contrast (Q4):**
  - **RC_GENERIC** if SUF(rcH);
  - **RC_DONOR_POOL_ONLY** if SUF(rcD) and not SUF(rcH);
  - **RC_INSUFFICIENT** otherwise.
  - The median dM of each rc source is always reported.
- **Always reported:**
  - the per-arm table and per-host S;
  - leave-one-donor-group-out of every verdict;
  - energy, α and capped share of the subspace arms;
  - the median change norm of every arm relative to `full`.

## Interpretation fixed in advance
- **DELTA_LOWRANK:k:** the repairing part of the cell's donor-minus-host BULK difference lies in a k-dimensional subspace of *other* donors' differences to the same host, at matched size. A random 64-subspace at that size does not repair.
- **NOT_DELTA_LOWRANK_LE64:** not even a 64-dimensional difference subspace carries it.
- **LR64_SIZE_LIMITED:** M6's lr64 failure was a size effect. **LR64_BASIS_LIMITED:** it was the raw basis.
- **MEANDIFF_DIRECTION:s:**
  - One fixed position-wise vector per source kind, the pooled donor BULK minus the pooled host BULK, added to the host repairs it round-specifically.
  - The shared component is then a donor-vs-host difference, not the donor's absolute BULK.
- **Round contrast:**
  - **RC_GENERIC:** the new-vs-ROUND contrast of other hosts' BULK alone gives the round-specific JOINT pattern, so the round contrast needs no repairing donor.
  - **RC_DONOR_POOL_ONLY:** only the donors' contrast does.
  - **RC_INSUFFICIENT:** the contrast alone is not enough.
- **Limits:**
  - The mdir and rc arms vary with the donor only through the pool exclusion, so they are close to 8 host-level replicates. Per-host S is the honest unit there.
  - The mdir and rc arms are not size-matched; their change norms are reported.
  - A rescaled arm at large α (capped at 10) is off-distribution; α and the capped share are reported.
  - The cells share donors and hosts, so the counts are preregistered decision rules, not independent tests.
  - One model (kev-4B) and one simulator family.
