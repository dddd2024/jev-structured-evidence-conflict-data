# A461-MECH-M6 R1: result (is the repairing L11 BULK component shared across donors, and low-rank?)

**Run:**
- 2540/2540 kev-4B forwards in 20 batches (19 × 128 + 108); 0 denied; one model load; elapsed 3808 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m5: checked`: the 36 M1 replays, the 208 `full` rows (vs M3) and the 208 `xdonor_BULK` rows (vs M5) are bitwise equal.
- Raw blob `2147311c2cf913fad5b07033e43789bb61293611`.
- The run follows prereg df835a9 under the standing GPU authorization. The pre-model gate passed (`COMPLETE_A461_MECH_M6_PRE_MODEL_GATE`, saved as `M6_GPU_R1/pre_model_gate_receipt.json`), and there was a single ledger attempt (consumed 0 → 2540).

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- **Size gate (rand_k vs lr_k):** passed in the run (fail-closed at 1e-3 relative per row and span position).
- The captures (102 MB) stay on the server under `M6_GPU_RUNS/ATTEMPT_R1/captures`. All 88 capture files match the run's `SHA256SUMS` there. Every non-capture file was fetched here and verified against the same `SHA256SUMS`.

**Analysis:** `A461_mech_m6_analysis_v1.py` (blob 325699b5, frozen before the run), run automatically by the server watcher after the receipt read COMPLETE (exit 0). Output: `M6_ANALYSIS_R1/m6_analysis.json` (sha256 c8527ad8…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51 = S_M3(all), 208/208 rows bitwise equal to M3; S(xdonor_BULK) = 51, 208/208 rows bitwise equal to M5 |
| SUF(meanD_host) (S ≥ 25.5 and SPEC) | **yes**: S = 39 |
| SUF(meanH_host) | **no**: S = 17 (but SPEC; see below) |
| SUF(meanD_donor) | yes: S = 57 |
| **shared verdict** | **SHARED_DONOR_COMPONENT**; same in 14/14 leave-one-donor-group-out splits |
| k\* (smallest k with SUF(lr_k)) | **none**: lr64 reaches S = 10 |
| **low-rank verdict** | **NOT_LOWRANK_LE64**; same in 14/14 splits |

In every split the SUF set is exactly {full, xdonor_BULK, meanD_host, meanD_donor}.

## Table (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority)
| arm | S | J main / round | frac | grp | SPEC | median dM main / round | change norm / full |
|---|---|---|---|---|---|---|---|
| full (M3 all-heads) | 51 | 58 / 7 | 0.99 | 14 | ✓ | +0.35 / −0.37 | 1.00 |
| xdonor_BULK (M5 anchor) | 51 | 57 / 6 | 0.98 | 14 | ✓ | +0.38 / −0.48 | 0.98 |
| **meanD_donor** | **57** | 59 / 2 | 1.00 | 14 | ✓ | +0.40 / −0.45 | 0.87 |
| **meanD_host** | **39** | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.66 | 0.62 |
| **meanH_host** (null) | **17** | 17 / 0 | 1.00 | 14 | ✓ | +0.15 / −0.70 | 0.66 |
| lr64 | 10 | 13 / 3 | 0.90 | 12 | ✓ | +0.05 / −0.34 | 0.55 |
| lr16 | 1 | 10 / 11 | 0.43 | 2 | ✗ | +0.04 / +0.18 | 0.41 |
| lr4 | 0 | 0 / 0 | 0.20 | 2 | ✗ | +0.04 / +0.10 | 0.26 |
| lr1 | 0 | 0 / 0 | 0.32 | 1 | ✗ | +0.01 / +0.01 | 0.12 |
| rand64 | 0 | 1 / 4 | 0.34 | 2 | ✗ | −0.02 / +0.02 | 0.55 |
| rand16 | 1 | 1 / 1 | 0.40 | 2 | ✗ | +0.01 / +0.03 | 0.41 |
| rand4 | 0 | 0 / 0 | 0.46 | 4 | ✗ | −0.01 / +0.01 | 0.26 |

M5 references: only_BULK (host remainder + the cell's own donor BULK) 39; xdonor_BULK 51.

## Subspace energy (lr_k; rand_k rows carry the matched lr_k values)
| k | ‖U_kU_kᵀΔ_B‖ / ‖Δ_B‖ (median of per-row medians) | min | basis singular-value share at k |
|---|---|---|---|
| 1 | 0.14 | 0.00 | 0.51 |
| 4 | 0.32 | 0.02 | 0.67 |
| 16 | 0.50 | 0.08 | 0.85 |
| 64 | 0.70 | 0.17 | 0.95 |

## Per-host S
| host | full | xdonor_BULK | meanD_donor | meanD_host | meanH_host | lr64 | lr16 | rand16 |
|---|---|---|---|---|---|---|---|---|
| 1fb5651c | 13 | 13 | 13 | 13 | **13** | 1 | 0 | 1 |
| 264c458d | 10 | 10 | 13 | 13 | 4 | 7 | 1 | 0 |
| 4bcbaf15 | 11 | 11 | 13 | 13 | 0 | 0 | 0 | 0 |
| 75642418 | 7 | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| 2c9118bb | 5 | 4 | 5 | 0 | 0 | 0 | 0 | 0 |
| 8ae85754 | 4 | 5 | 5 | 0 | 0 | 2 | 0 | 0 |
| 1c7158b6 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2a4f596d | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

lr1, lr4, rand4 and rand64 are 0 at every host.

As the prereg warned, the averaged arms act host by host: meanD_host is 13/13 or 0/13 at every host, and meanH_host nearly so.

## Reading, with its limits
1. **One averaged donor BULK contribution, from other donors, carries the round-specific repair (SHARED_DONOR_COMPONENT).**
   - The mean of 12 other donors' BULK parts, put into the host's own write, repairs 39/104 with full round-specificity: J_round 0, frac 1.00, 14/14 groups. This equals only_BULK with the cell's own donor (M5: 39).
   - Put on top of the rest of the donor's write, it repairs 57/104, more than the donor's own full patch (51). At hosts 264c458d and 4bcbaf15 it repairs cells that the donor's own patch does not.
   - So the repairing BULK part does not need the cell's own donor, nor any single donor: one pooled direction per source kind does the job.
2. **The host-mean null is weaker, but not empty. This limits the "donor-like" reading.**
   - The averaged BULK of *other hosts* (non-repairing scenes) repairs 17/104. It is fully round-specific too (J_round 0, frac 1.00), at a similar change norm (0.66 vs 0.62 for meanD_host). So the gap from 39 is not a size effect.
   - At host level, the honest unit here, meanD_host fully repairs 3 hosts (1fb5651c, 264c458d, 4bcbaf15) and meanH_host 1 host fully (1fb5651c) plus 4/13 at 264c458d. Host 1fb5651c is repaired by *any* averaged context read. The donor/host-mean difference rests on two hosts, 264c458d and 4bcbaf15.
   - The round-specificity itself is not donor-specific. With the ROUND-source captures, every averaged arm pushes the host toward no-conflict (median dM_round −0.45 to −0.70), including the host mean. The round contrast is carried by the source kind of the averaged write. What donors add over hosts is the size of the *main* (new-source) push (+0.24 vs +0.15), which crosses the JOINT threshold at more hosts.
   - The SHARED_DONOR_COMPONENT verdict holds as preregistered. The supported claim is narrower: a pooled donor BULK component repairs more hosts than a pooled host BULK component at matched size, and the round contrast is common to both.
3. **The repairing part of Δ_B is not in a ≤ 64-dimensional subspace of donor BULK writes (NOT_LOWRANK_LE64).**
   - The top-64 basis of the other donors' raw BULK contributions captures 70% of the cell's Δ_B energy and 95% of the basis singular-value mass. Yet lr64 repairs only 10/104 (SPEC; 7 of them at host 264c458d). k ≤ 16 repairs nothing and is not round-specific.
   - The random-subspace nulls at matched size give 0–1. So the little that lr64 recovers is specific to that subspace, but most of the repair lies in the residual 30% of Δ_B's energy outside it.
   - **Limits of this negative:**
     - The basis is uncentred and fit on raw contributions, not on donor-minus-host differences. Its top components are likely shared mean or context directions that donor and host both contain, which Δ_B cancels.
     - lr_k is not rescaled: lr64 changes the host by 0.55 of the full patch, against 0.62 for meanD_host (39). Size alone may cost part of the repair.
     - So "not low-rank" applies to this basis. A low-rank Δ-basis is not ruled out.
4. **Putting 1 and 3 together.**
   - Averaging over 12 donors keeps the repair, while projection onto their top-64 raw directions loses it.
   - So donors agree on a mean BULK direction, but that direction is not dominant in the raw variance of their writes. This fits a small shared difference sitting on top of a large common context component.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The averaged arms are close to 8 host-level replicates, so 39 vs 17 is in effect 3 vs about 1.3 hosts.
- The pooled-mean arms are not size-matched to each other exactly; their change norms are reported (0.62 vs 0.66).
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.
- Hosts 1c7158b6 and 2a4f596d are repaired by nothing in M3–M6.

## Where the M1–M6 chain now stands
- M1: the span's L11 representation carries a signed, round-specific conflict evaluation.
- M2: L11 full attention writes it.
- M3: heads 8–14 write it together, with head 10 most necessary.
- M4: the write reads mainly from the other messages and the state header, not the partner vote.
- M5: the context-wide (BULK) part carries the evaluation in its direction, not just its size, and a third donor's BULK keeps 51/51.
- **M6:**
  - One pooled donor BULK component (12 other donors) gives 39/104 into the host, and 57/104 with the donor's remainder.
  - The pooled BULK of other hosts gives 17, at matched size.
  - The round contrast (ROUND-source pushes toward no-conflict) is common to donor and host pools.
  - The repairing part is not captured by a ≤ 64-dimensional raw-contribution basis.

## Suggested M7 (not frozen)
- **Centred Δ basis:** low-rank lr_k with U_k fit on other donors' Δ_B = donor_B − host_B, or on the donor-pool mean minus host-pool mean. Add a size-matched variant. This tests whether the donor-minus-host difference, rather than raw BULK, is low-rank, which reading 3 leaves open.
- **Mean-difference direction:** a single direction, mean_D(B) − mean_H(B), added to the host at a few scales, with its round-source counterpart. This is a one-vector test of reading 4.
- **Round contrast without donors:** host + (mean_H ROUND-source BULK − mean_H new-source BULK), to test whether the round contrast alone moves the host.
- Pending separately: replication of the M2/M3 chain on SecJev-0.8B.
