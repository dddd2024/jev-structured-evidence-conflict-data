# A461-MECH-M5 R1: result (size vs direction vs content of the L11 conflict write)

**Run:**
- 2540/2540 kev-4B forwards in 20 batches (19 × 128 + 108); 0 denied; one model load; elapsed 3747 s.
- `bitwise_vs_m1` and `bitwise_vs_m3: checked`: the 36 M1 replays and all 208 `full` rows are bitwise equal to M1 and M3.
- Raw blob `f03ce4e96e6eb4ea76b43d9627bad62c87ca8c4d`.
- The run follows prereg 7187842 under the standing GPU authorization. The pre-model gate passed (`COMPLETE_A461_MECH_M5_PRE_MODEL_GATE`), and there was a single ledger attempt (consumed 0 → 2540).

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate: the class contributions sum to the forward's own `o_proj` input.
- **Matched-size gate:** over all 1664 `dir_*` and `dir_RAND` rows, ‖patch − host‖ equals ‖donor − host‖ per row and span position within 6.0e-7 relative (gate: 1e-3).
- The captures (102 MB) stay on the server under `M5_GPU_RUNS/ATTEMPT_R1/captures`. All 88 capture files match the run's `SHA256SUMS` there. Every non-capture file was fetched here and verified against the same `SHA256SUMS`.

**Analysis:** `A461_mech_m5_analysis_v1.py` (blob f1bd26a3, frozen before the run), run automatically by the server watcher after the receipt read COMPLETE. Output: `M5_ANALYSIS_R1/m5_analysis.json` (sha256 ffbdce39…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51 = S_M3(all); 208/208 full rows bitwise equal to M3 |
| BULK_SUF (only_BULK ≥ 25.5 and SPEC) | **yes**: S = 39 |
| BULK_NEC (drop_BULK ≤ 25.5) | **yes**: S = 4 |
| RAND_NULL (dir_RAND ≤ 5 and not SPEC) | **yes**: S = 1, frac 0.44 |
| D = {C : DIR_SUF(C)} | **{BULK, OTHER_ITEMS}** |
| **verdict** | **BULK_DIRECTION**; same in 14/14 leave-one-donor-group-out splits |
| **content** | **XD_HOLDS** (S(xdonor_BULK) = 51, SPEC); same in 14/14 splits |

**Leave-one-donor-group-out:** D = {BULK} in 9 splits and {BULK, OTHER_ITEMS} in 5. dir_OTHER_ITEMS sits at the threshold, so its membership in D is fragile. The verdict does not depend on it, because BULK alone already makes it BULK_DIRECTION.

## Table (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority)
| arm | S | J main / round | frac | grp | SPEC | median dM main / round | α median (min–max) |
|---|---|---|---|---|---|---|---|
| full (M3 all-heads) | 51 | 58 / 7 | 0.99 | 14 | ✓ | +0.35 / −0.37 | — |
| **xdonor_BULK** | **51** | 57 / 6 | 0.98 | 14 | ✓ | +0.38 / −0.48 | — |
| **dir_BULK** | **48** | 48 / 0 | 0.99 | 14 | ✓ | +0.33 / −0.56 | 1.24 (0.35–3.6) |
| only_BULK | 39 | 39 / 0 | 0.99 | 14 | ✓ | +0.25 / −0.46 | — |
| dir_OTHER_ITEMS | 27 | 44 / 17 | 0.75 | 12 | ✓ (at threshold) | +0.35 / −0.08 | 1.53 (0.36–10.2) |
| dir_CONTEXT | 17 | 22 / 5 | 0.97 | 14 | ✓ | +0.12 / −0.34 | 2.56 (1.07–16.2) |
| dir_PARTNER | 9 | 19 / 11 | 0.65 | 11 | ✗ | +0.01 / −0.02 | 3.24 (0.53–103) |
| dir_ROUNDVOTES | 4 | 25 / 21 | 0.58 | 9 | ✗ | +0.17 / +0.11 | 2.03 (0.36–10.6) |
| dir_ROUND_PEERS | 4 | 26 / 23 | 0.43 | 4 | ✗ | +0.10 / +0.09 | 3.15 (0.44–40.4) |
| drop_BULK | 4 | 10 / 6 | 0.81 | 13 | ✓ | +0.12 / +0.03 | — |
| dir_RAND | 1 | 4 / 3 | 0.44 | 5 | ✗ | −0.01 / −0.02 | — |
| dir_SELF | 0 | 0 / 0 | 0.59 | 9 | ✗ | −0.05 / −0.09 | 3.85 (1.29–17.2) |

**α warning:** α is the median, over rows, of the per-position median rescaling; min and max are taken over rows. PARTNER, ROUND_PEERS and SELF differ little between donor and host, so their α runs up to 17–103. The failures of those arms at large α are weaker evidence than a failure at α ≈ 1–2, because a large rescaling can push the state off-distribution. The arms that pass (BULK, OTHER_ITEMS) have the smallest α (median 1.2–1.5).

## Δ geometry (per cell, from the captures; medians over the 104 cells)
| class C | ‖Δ_C‖ / ‖Δ_full‖ | cos(Δ_C, Δ_full) |
|---|---|---|
| BULK | 0.79 | 0.78 |
| OTHER_ITEMS | 0.63 | 0.65 |
| ROUNDVOTES | 0.50 | 0.50 |
| CONTEXT | 0.41 | 0.43 |
| ROUND_PEERS | 0.36 | 0.33 |
| PARTNER | 0.36 | 0.35 |
| SELF | 0.28 | 0.34 |

The class that repairs at matched size (BULK) is also the one best aligned with the full donor-minus-host change (cos 0.78). Part of what "BULK direction" means here is therefore "the direction that is most of Δ_full". See reading 2. The alignment does not explain everything: ROUNDVOTES is better aligned than CONTEXT (cos 0.50 vs 0.43), yet repairs less at matched size (4 vs 17) and is not round-specific.

## Per-host S
| host | full | only_BULK | drop_BULK | dir_BULK | dir_OI | dir_CTX | dir_PARTNER | xdonor_BULK | dir_RAND |
|---|---|---|---|---|---|---|---|---|---|
| 1fb5651c | 13 | 12 | 0 | 11 | 2 | 10 | 1 | 13 | 0 |
| 4bcbaf15 | 11 | 9 | 1 | 11 | 6 | 5 | 2 | 11 | 0 |
| 264c458d | 10 | 10 | 1 | 11 | 8 | 1 | 2 | 10 | 1 |
| 75642418 | 7 | 4 | 1 | 8 | 5 | 1 | 2 | 8 | 0 |
| 2c9118bb | 5 | 1 | 0 | 2 | 0 | 0 | 1 | 4 | 0 |
| 8ae85754 | 4 | 3 | 1 | 5 | 6 | 0 | 0 | 5 | 0 |
| 1c7158b6 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| 2a4f596d | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- Hosts differ in which BULK sub-part works at matched size. Host 1fb5651c is repaired by the CONTEXT direction (10) and hardly by OTHER_ITEMS (2); hosts 264c458d and 8ae85754 show the reverse. Only the combined BULK direction works across hosts.
- Host 2a4f596d is still never repaired by any arm.

## Reading, with its limits
1. **M4's necessity of OTHER_ITEMS / CONTEXT is not just a size effect.**
   - A random direction at exactly the full patch's size repairs 1/104 (RAND_NULL), and it is not round-specific (frac 0.44).
   - The donor-minus-host BULK direction, rescaled to the same size, repairs 48/51, with α near 1 (median 1.24). It is fully round-specific: J_round 0 and frac 0.99, in 14/14 groups.
   - Under the preregistered interpretation, the context-wide read carries the round-specific evaluation in its direction, not only its size.
2. **"Direction" is not "a small specific sub-component".**
   - BULK makes up most of Δ_full (norm ratio 0.79, cos 0.78). The single classes outside BULK do not repair at matched size: PARTNER 9, ROUNDVOTES 4, ROUND_PEERS 4, SELF 0, all not SPEC.
   - Neither sub-part of BULK is enough across hosts: OTHER_ITEMS reaches 27, right at the threshold; CONTEXT reaches 17.
   - The evaluation is therefore spread over the context-wide part of the write. It does not sit in the partner vote's direction (no PARTNER_DIRECTION, even when rescaled up to α ≈ 3).
   - The large-α caveat limits the negative result for PARTNER, ROUND_PEERS and SELF.
3. **The BULK component is generic, not scene-specific (XD_HOLDS).**
   - Replacing the donor's BULK part with a third, unrelated donor's BULK part (from a different group and scene, of the same source kind) keeps all 51 repairs and their round-specificity (frac 0.98, 14/14 groups).
   - Whatever the BULK contribution carries, it is a **donor-like context component** that transfers across scenes and groups. It does not encode the particular other messages or header of the donor's own scene.
   - The round-specificity transfers with it: a third donor's ROUND-source BULK still pushes the host toward no-conflict (median dM_round −0.48).
4. **Where the round-specificity comes from, revisited.** Every pre-span key is shared between a scene's new and ROUND arms, and the round token is last in the span. So the round contrast in BULK must come from how the donor's span queries and gates weight the same context, not from the context content. XD_HOLDS fits this: the scene-specific content can be swapped out, and the query-side "how to read the context" part is what carries over.
5. **The rest of the donor write helps but is not enough on its own.** only_BULK (host remainder + donor BULK) gives 39, against 51 for xdonor_BULK (donor remainder + third BULK). drop_BULK gives 4. The non-BULK classes add about 12 repairs on top of BULK, but they carry no decision without it.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.
- The third donors are themselves repairing donors, so XD_HOLDS shows the component is shared *among donors*. It does not show that any arbitrary scene's context would work.
- The dir_* arms rescale per span position, so a matched-size direction is not a natural activation.

## Where the M1–M5 chain now stands
- M1: the span's L11 representation carries a signed, round-specific conflict evaluation.
- M2: L11 full attention writes it.
- M3: heads 8–14 write it together, with head 10 most necessary.
- M4: the write reads mainly from the other messages and the state header, not the partner vote. The host does not lack the partner's values.
- **M5:** the context-wide (BULK) part carries the evaluation in its direction, not just its size: a random direction at full size gives 1, the BULK direction gives 48. The component is generic across donors: a third donor's BULK keeps 51/51.
- The working hypothesis is now a **shared, donor-like "conflict-reading" direction in the L11 context read**, keyed by the span's own round. It is not a scene-specific or partner-specific lookup.

## Suggested M6 (handoff table: BULK_DIRECTION + XD_HOLDS; not frozen)
- Patch the **mean donor BULK direction** (over the 14 donors, per source kind) into every host. Also patch a low-rank version: the top PCA components of the donor BULK writes.
- Test whether one shared direction (or a small subspace) reproduces the round-specific repair.
- Add a null: the mean BULK of the hosts' own writes, at matched size.
- Pending separately: replication of the M2/M3 chain on SecJev-0.8B.
