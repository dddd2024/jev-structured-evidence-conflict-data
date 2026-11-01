# A461-MECH-M6 R1: is the repairing L11 BULK component shared across donors, and low-rank? (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 2540 kev-4B forwards in 20 batches (19 × 128 + 108).

**Parent:** M5 R1 (695f4fe).
- **BULK_DIRECTION.** BULK is the OTHER_ITEMS + CONTEXT key-class part of the donor's L11 span write. Its donor-minus-host direction, rescaled to the full patch's size, repairs 48/104 round-specifically. A random direction of that size repairs 1.
- **XD_HOLDS.** Replacing the donor's BULK part with a third donor's keeps 51/51.
- **Caveats:**
  - BULK is most of Δ_full (cos 0.78).
  - The third donors are themselves repairing donors.

## Question
Is the repairing BULK part one **shared, donor-like component**, and does it live in a **low-dimensional subspace** learned from other donors?

Definitions:
- All arms patch the L11 `o_proj` input at the 31 span positions of host new, in every question row.
- Sources: donor new (main) and donor ROUND (round).
- X_B is the BULK part of capture X.
- Pool_D(d, h) is the 12 donors from neither the donor's group nor the host's group, so the pool never holds the cell's own donor.
- Pool_H(d, h) is the other hosts outside the donor's group (6–7).
- Pooled captures come from the same arm (new or ROUND) as the source.

| arm | patch | question |
|---|---|---|
| `full` | the M3 all-heads patch | bitwise anchor (S 51) |
| `xdonor_BULK` | donor − donor_B + third_B, wired as in M5 | bitwise anchor of the M5 rows (S 51) |
| **`meanD_host`** | host − host_B + mean_{p∈Pool_D} p_B | does one averaged donor BULK, from other donors, repair hosts? (M5 reference: only_BULK 39) |
| `meanD_donor` | donor − donor_B + mean_{p∈Pool_D} p_B | the same, keeping the donor's remainder (M5 reference: xdonor 51) |
| **`meanH_host`** | host − host_B + mean_{h'∈Pool_H} h'_B | null: the averaged BULK of *other hosts* |
| **`lr_k`**, k ∈ {1, 4, 16, 64} | host + U_k U_kᵀ (donor_B − host_B) | is the repairing part of Δ_B in a k-dimensional subspace? |
| **`rand_k`**, k ∈ {4, 16, 64} | host + Q_k Q_kᵀ Δ_B, rescaled per row and span position to ‖U_k U_kᵀ Δ_B‖ | null: a random k-subspace of the same size |

**Subspace.**
- U_k holds the top-k right singular vectors of the uncentred matrix of Pool_D's row-0 BULK contributions: 12 donors × both arms × 31 positions = 744 vectors of dimension 4096.
- The basis is fit on new and ROUND alike, so any round-specificity of lr_k comes from the cell's own Δ_B, not from the basis.
- Q_k is a seeded Gaussian k-frame, orthonormalized by QR. It is fixed per cell and shared by the main and round sources.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m6_freeze_v1.py` (blob `3e25c8da`; CPU + tokenizer only). Derived from the M5 freeze; it cross-checks the M3, M4 and M5 key classes, the M5 third donors and the wiring of the M5 xdonor rows |
| manifest blob | `314caf9336bf411f81771ab7f623432c3777de97` |
| design blob | `43967513c3dbcad74dd7b024b67a16463f456ffc`: rules under `preregistered_analysis`, pools under `pools` |
| runner blob | `79c10a6747f0862b7e30f878368087884d57309d`, derived from the M5 runner f9d36a69 by checked substitutions |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m6_selftest_v1.py` (blob `b0723196`), derived from the M5 self-test: **PASS 16/16** in `M6_SELFTEST_R1/`. rand_k size gate max rel err 7.3e-7. Identities: a pool holding only the donor = only_BULK (0.0), a pool holding only the third donor = xdonor_BULK (0.0), lr at full fake width = only_BULK (5.7e-6). Analysis dry run end to end on the fake output (fake verdict INCONSISTENT_WITH_M3_M5, as expected) |
| analysis | `A461_mech_m6_analysis_v1.py` (blob `325699b5`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, M5 design `26126568`, M5 raw `f03ce4e9`, G1.0 counterfactuals `06ee06d7` |

## Design
- **Captures:** 44, as in M4 and M5. They are fail-closed on class additivity, and 36 must replay M1 bitwise.
- **Patches:** 12 arms × 2 sources × 104 cells = 2496.
- **Gates checked in the run:**
  - the 208 `full` rows must equal M3 bitwise;
  - the 208 `xdonor_BULK` rows must equal M5 bitwise.
- **Size gate:** every rand_k row's change must equal lr_k's per row and span position, within 1e-3 relative (fail-closed).
- **Recorded per row:**
  - each lr_k and rand_k row records the energy fraction ‖U_k U_kᵀ Δ_B‖ / ‖Δ_B‖ and the basis's singular-value share at k. A rand_k row records the values of the lr_k it is matched to;
  - every row records its change norm.

## Rules (coded in the design JSON)
- **S, SPEC:** as in M2–M5.
- **SUF(arm)** iff S(arm) ≥ ½ S(full) and SPEC(arm).
- **Consistency gate:** S(full) = 51 with 208 rows bitwise equal to M3, and S(xdonor_BULK) = 51 with 208 rows bitwise equal to M5. Otherwise the verdict is INCONSISTENT_WITH_M3_M5.
- **Shared verdict:**
  - **SHARED_DONOR_COMPONENT** if SUF(meanD_host) and not SUF(meanH_host);
  - **GENERIC_CONTEXT_SHIFT** if SUF(meanD_host) and SUF(meanH_host);
  - **SHARED_NEEDS_DONOR_REST** if not SUF(meanD_host) and SUF(meanD_donor);
  - **NOT_SHARED_BY_AVERAGE** otherwise.
- **Low-rank verdict:**
  - k\* is the smallest k ∈ {1, 4, 16, 64} with SUF(lr_k);
  - the null arm is rand_max(k\*, 4), and it holds iff S ≤ 5 and not SPEC;
  - **LOWRANK:k\*** if k\* exists and the null holds;
  - **LOWRANK_UNRESOLVED:k\*** if k\* exists and the null fails;
  - **NOT_LOWRANK_LE64** if there is no k\*.
- **Always reported:**
  - the per-arm table;
  - per-host S;
  - leave-one-donor-group-out of both verdicts;
  - subspace energy;
  - the median change norm of every arm relative to `full`.

## Interpretation fixed in advance
- **SHARED_DONOR_COMPONENT:** an averaged donor BULK contribution, taken from other donors, gives hosts the round-specific repair, while the averaged BULK of other hosts does not. This points to a donor-like shared component, not scene content.
- **GENERIC_CONTEXT_SHIFT:** any averaged context read works, so M5's "donor-like" reading is not supported.
- **SHARED_NEEDS_DONOR_REST:** the averaged component works only together with the rest of the donor's write.
- **NOT_SHARED_BY_AVERAGE:** averaging destroys what a single third donor carries. For example, donors may agree in subspace but not in sign or in their position pattern.
- **LOWRANK:k:** the repairing part of Δ_B lies in a k-dimensional subspace learned from *other* donors, and a random k-subspace of the same size does not repair.
- **Limits:**
  - The pooled means change the host by their own size, which is not matched; their change norms are reported.
  - The pooled-mean arms vary with the donor only through the pool exclusion, so their 104 cells are close to 8 host-level replicates. Per-host S is the honest unit there.
  - The cells share donors and hosts, so the counts are preregistered decision rules, not independent tests.
  - One model (kev-4B) and one simulator family.
