# A461-MECH-M7 R1: result (is the donor-minus-host BULK difference low-rank, one mean-difference direction, or a donor-free round contrast?)

**Run:**
- 2748/2748 kev-4B forwards in 22 batches (21 × 128 + 60); 0 denied; one model load; elapsed 4173 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`: the 36 M1 replays, the 208 `full` rows (vs M3) and the 208 `meanD_host` rows (vs M6) are bitwise equal.
- Raw blob `0383fccf01ad027ae14c59c8fc9830f1d398219e`.
- The run follows prereg 7725863 under the standing GPU authorization. The pre-model gate passed (`COMPLETE_A461_MECH_M7_PRE_MODEL_GATE`, saved as `M7_GPU_R1/pre_model_gate_receipt.json`), and there was a single ledger attempt (`A461_MECH_M7_GPU_20261029_R1`, 2748 reserved).

**Readout validity:**
- The 44 captures passed the fail-closed class-sum gate.
- **Size gate (all `_sm` arms and rand64_sm):** passed in the run (fail-closed at 1e-3 relative per row and span position).
- The captures (102 MB) stay on the server under `M7_GPU_RUNS/ATTEMPT_R1/captures`. All 88 capture files match the run's `SHA256SUMS` there. Every non-capture file was fetched here and verified against the same `SHA256SUMS`.

**Analysis:** `A461_mech_m7_analysis_v1.py` (blob 7c4f9169, frozen before the run), run automatically by the server launch script after the receipt read COMPLETE (exit 0). Output: `M7_ANALYSIS_R1/m7_analysis.json` (sha256 2e8f36c8…, identical on the server).

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51 = S_M3(all), 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 rows bitwise equal to M6 |
| NULL (rand64_sm S ≤ 5, not SPEC) | **holds**: S = 1 |
| k\* (smallest k with SUF(dlr{k}_sm)) | **none**: dlr64_sm reaches S = 24 (needs 25.5) and misses SPEC (frac 0.72, 13 groups) |
| **Q1 delta low-rank** | **NOT_DELTA_LOWRANK_LE64** |
| **Q2 M6 size** | **LR64_BASIS_LIMITED**: lr64_sm S = 19, SPEC, below 25.5 |
| s\* (SUF(mdir{s})) | **none**: mdir1 = mdir2 = 0 |
| **Q3 mean difference** | **NOT_MEANDIFF** |
| **Q4 round contrast** | **RC_INSUFFICIENT**: rcH 9 (not SPEC), rcD 0 |

All four verdicts are the same in 14/14 leave-one-donor-group-out splits, and in every split the SUF set is exactly {full, meanD_host}.

## Table (S out of 104; frac = share of cells with dM_main > dM_round; grp = donor groups with a majority)
| arm | S | J main / round | frac | grp | SPEC | median dM main / round | change norm / full |
|---|---|---|---|---|---|---|---|
| full (M3 all-heads) | 51 | 58 / 7 | 0.99 | 14 | ✓ | +0.35 / −0.37 | 1.00 |
| meanD_host (M6 anchor) | 39 | 39 / 0 | 1.00 | 14 | ✓ | +0.24 / −0.66 | 0.62 |
| **dlr64_sm** | **24** | 42 / 18 | 0.72 | 13 | ✗ | +0.23 / +0.03 | 0.78 |
| dlr64 (not rescaled) | 20 | 37 / 18 | 0.47 | 4 | ✗ | +0.20 / +0.24 | 0.65 |
| dlr16_sm | 17 | 51 / 38 | 0.54 | 7 | ✗ | +0.28 / +0.35 | 0.78 |
| dlr4_sm | 1 | 34 / 49 | 0.28 | 1 | ✗ | +0.15 / +0.31 | 0.78 |
| dlr1_sm | 2 | 52 / 51 | 0.23 | 1 | ✗ | +0.11 / +0.15 | 0.67 |
| **lr64_sm** | **19** | 21 / 2 | 0.97 | 14 | ✓ | +0.07 / −0.69 | 0.78 |
| rand64_sm (null) | 1 | 1 / 1 | 0.47 | 4 | ✗ | −0.03 / −0.01 | 0.78 |
| mdir1 | 0 | 0 / 5 | 0.06 | 0 | ✗ | +0.09 / +0.18 | 0.25 |
| mdir2 | 0 | 16 / 47 | 0.01 | 0 | ✗ | +0.22 / +0.40 | 0.51 |
| rcH | 9 | 9 / 0 | 0.50 | 4 | ✗ | −0.01 / −0.01 | 0.04 |
| rcD | 0 | 0 / 0 | 0.65 | 14 | ✗ | −0.08 / −0.16 | 0.04 |

M6 references: lr64 (raw basis, not rescaled) 10, SPEC, change 0.55.

## Subspace statistics (median over rows of the per-row median)
| arm | energy ‖PΔ_B‖/‖Δ_B‖ | energy min | basis sv share at k | α median | α max | capped share |
|---|---|---|---|---|---|---|
| dlr1_sm | 0.21 | 0.00 | 0.15 | 4.75 | 10.0 | 0.30 |
| dlr4_sm | 0.41 | 0.04 | 0.34 | 2.47 | 10.0 | 0.01 |
| dlr16_sm | 0.65 | 0.19 | 0.62 | 1.53 | 5.27 | 0 |
| dlr64_sm / dlr64 | 0.84 | 0.40 | 0.87 | 1.18 / 1 | 2.50 / 1 | 0 |
| lr64_sm (M6 basis) | 0.70 | 0.17 | 0.95 | 1.42 | 5.92 | 0 |
| rand64_sm | 0.12 | 0.09 | — | 8.05 | 11.18 (uncapped) | — |

The Δ basis is less concentrated than the raw basis (top-64 sv share 0.87 vs 0.95) but captures more of the cell's Δ_B (0.84 vs 0.70).

## Per-host S
| host | full | meanD_host | dlr64_sm | dlr64 | dlr16_sm | lr64_sm | rcH | rand64_sm |
|---|---|---|---|---|---|---|---|---|
| 1fb5651c | 13 | 13 | 9 | 9 | 8 | 2 | **9** | 0 |
| 264c458d | 10 | 13 | 5 | 2 | 0 | **10** | 0 | 1 |
| 4bcbaf15 | 11 | 13 | 7 | 7 | 5 | 1 | 0 | 0 |
| 75642418 | 7 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| 2c9118bb | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 8ae85754 | 4 | 0 | 3 | 2 | 4 | 5 | 0 | 0 |
| 1c7158b6 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2a4f596d | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

mdir1, mdir2 and rcD are 0 at every host; dlr1_sm and dlr4_sm are ≤ 2 at every host.

## Reading, with its limits
1. **The Δ basis recovers the main repair but loses the round-specificity (NOT_DELTA_LOWRANK_LE64).**
   - dlr64_sm is a near miss on both criteria (S 24 vs 25.5; frac 0.72 vs 0.75, 13 groups). But the failure mode is new: the main source repairs often (J_main 42), and the **round source repairs too** (J_round 18; median dM_round +0.03 against −0.37 for full).
   - At lower k this gets worse: dlr16_sm J 51 / 38, dlr1_sm J 52 / 51. The top directions of other donors' differences to the same host push the host toward conflict **for both source kinds**. They are a generic conflict-raising direction, not a round-specific one.
   - A probable reason is built into the design. The basis pairs are same-kind (p_B(a) − h_B(a)), so they contain the donor-vs-host difference but not the host's own new-vs-ROUND contrast. The cell's round Δ_B is donor_B(ROUND) − host_B(new), which does contain that contrast. The part of Δ_B that carries the round push toward no-conflict is therefore likely outside the basis. This is an interpretation, not a tested claim.
   - The random 64-subspace at the same size gives 1, so what dlr recovers is specific to the Δ basis.
   - Limits: dlr1_sm is off-distribution (α median 4.75, 30% of positions capped). dlr16_sm and dlr64_sm are not (α ≤ 5.3 and 2.5, no capping).
2. **M6's lr64 failure was partly size, mostly basis (LR64_BASIS_LIMITED by rule).**
   - Rescaled to ‖Δ_B‖, the raw-basis lr64 rises from 10 to 19 and stays fully round-specific (J_round 2, frac 0.97, 14 groups). The preregistered verdict is BASIS_LIMITED because 19 < 25.5.
   - lr64_sm changes the host by more than meanD_host (0.78 vs 0.62 of full) and still repairs half as much. So size does not explain the remaining gap. Its repair is concentrated at host 264c458d (10/13).
   - The two bases fail in opposite ways. The raw basis keeps the round contrast but loses the main push; the Δ basis keeps the main push but loses the round contrast.
3. **One pooled mean-difference vector does not repair (NOT_MEANDIFF), and this was close to forced by the design.**
   - mdir1 and mdir2 are 0 everywhere. mdir2 inverts the pattern (J 16 main / 47 round).
   - mdir subtracts Pool_H at the *same* source kind. Its main−round difference is the donor pool's round contrast minus the host pool's round contrast. M6 had already found the round contrast common to both pools, so this difference is small and mdir could hardly be SPEC. Q3 was a weak test of reading 4 of M6.
   - mdir1 also differs from meanD_host (39) in a way that matters: it keeps the host's own BULK and subtracts the *pooled* host BULK, while meanD_host replaces the host's own BULK. The host's own BULK is not well approximated by the pooled hosts' BULK.
4. **The round contrast alone is not enough (RC_INSUFFICIENT), but it matters in context.**
   - The pooled contrast is small: rcH and rcD change the host by 0.04 of full. rcH 9 is all at host 1fb5651c, which M6 already found is repaired by almost any averaged read. rcD 0.
   - By construction, the meanD_host round patch is its main patch plus c = mean_D B(ROUND) − mean_D B(new), and rcD patches host ∓ c. Inside meanD_host, c separates J 39 from J 0, and the median dM main and round differ by 0.90. In rcD, a gap of 2c around the plain host separates the median dM by only 0.08 and repairs nothing.
   - So the round contrast acts strongly only on top of the common BULK shift that meanD_host supplies. The effect is non-additive. This is a post-hoc reading of the preregistered arms.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- The pooled arms (mdir, rc, meanD_host) are close to 8 host-level replicates; per-host S is the honest unit there.
- The mdir and rc arms are not size-matched (0.04–0.51 of full).
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.
- Hosts 1c7158b6 and 2a4f596d are repaired by nothing in M3–M7.

## Where the M1–M7 chain now stands
- M1: the span's L11 representation carries a signed, round-specific conflict evaluation.
- M2: L11 full attention writes it.
- M3: heads 8–14 write it together, with head 10 most necessary.
- M4: the write reads mainly from the other messages and the state header, not the partner vote.
- M5: the context-wide (BULK) part carries the evaluation in its direction, and a third donor's BULK keeps 51/51.
- M6: one pooled donor BULK component repairs 39/104 (57 with the donor remainder); pooled host BULK repairs 17; not captured by a ≤ 64-dimensional raw basis.
- **M7:**
  - The repair splits into two parts that no tested low-rank or single-vector arm carries together.
  - A **conflict-raising part**, common to both source kinds, is well captured by a 16–64-dimensional basis of donor-minus-host differences.
  - A **round contrast** (ROUND vs new source) is small in norm and does nothing alone, but separates JOINT from non-JOINT once the common shift is present.
  - Rescaling M6's raw basis doubles its repair (10 → 19), but the raw basis remains limited.

## Suggested M8 (not frozen)
- **Cross-kind Δ basis:** fit U_k on p_B(a) − h_B(new) for a ∈ {new, ROUND}, matching how the cell's Δ_B is formed, so that the round contrast is in the basis. Size-matched, k ∈ {4, 16, 64}, with the same random null. This tests interpretation 1.
- **Two-part reconstruction:** host + P_k Δ_B(new-source part) ± c·(cell's own donor round contrast), at a few c. This tests whether a low-rank common part plus a single contrast vector is sufficient.
- **Contrast scaling on top of the common shift:** the meanD_host common part (host − host_B + ½(mean_D new + mean_D ROUND)) ∓ s·rcD contrast, s ∈ {0, ½, 1, 2}. This measures the non-additivity found in reading 4.
- Pending separately: replication of the M2/M3 chain on SecJev-0.8B.
