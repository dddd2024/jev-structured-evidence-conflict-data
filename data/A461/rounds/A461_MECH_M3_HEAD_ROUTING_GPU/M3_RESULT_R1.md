# A461-MECH-M3 R1: result (head-level routing at L11)

**Run:**
- 7740/7740 kev-4B forwards in 61 batches; 0 denied.
- The 36 M1 replays are bitwise equal (`bitwise_vs_m1: checked`).
- Elapsed 11394 s. Raw blob `a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c`.
- The run follows prereg 342e559 under the standing GPU authorization.
- One earlier launch was refused before any forward or quota use, because the runs root did not exist (`M3_GPU_R1/M3_GPU_R1_refused_no_runs_root.log`).

**Readout validity:**
- At all 44 captures, the attention readout reconstructs the forward's own `o_proj` input with max abs error 0.0, and the four rows agree exactly.
- The captures (87 MB) stay on the server under `M3_GPU_RUNS/ATTEMPT_R1/captures`. Their hashes are in `M3_GPU_R1/raw_native_logits_m3.jsonl`.

**Analysis:** `A461_mech_m3_analysis_v1.py` (blob 38d2b4cf, frozen before the run). Output: `M3_ANALYSIS_R1/m3_analysis.json`.

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(all) = 51 = S_M2(mixer, L11); main JOINT agreement 104/104; max \|ΔdM\| vs M2 6e-6 |
| SUF (single head sufficient) | none |
| NEC (drop h ⇒ S ≤ 25.5) | **{10}** |
| GSUF (KV group sufficient) | none |
| **verdict** | **SPARSE_HEADS**, H\* = {10} (from NEC) |
| A1 | DONOR_GATED (14/14), HOST_GATED (8/8) ⇒ preregistered reading: *host deficit in what the heads carry, not where they look* |
| A2 | median partner mass of head 10, new arm: donors 0.136, hosts 0.110; 0 hosts below the donor minimum |

## What the table says (descriptive)
| arm | S | frac(main > round) | SPEC |
|---|---|---|---|
| all 16 heads | 51 | 0.99 | ✓ |
| best single head (head 8) | 3 | 0.68 | ✗ |
| any other single head | 0–1 | — | — |
| group 2 (heads 8–11) | 11 | 0.79 | ✓ |
| group 3 (heads 12–15) | 10 | 0.28 | ✗ |
| groups 0, 1 | 0 | — | ✗ |
| drop 10 | **16** | 0.73 | ✗ |
| drop 8 / 9 / 14 | 26 / 27 / 27 | 0.72 / 0.95 / 0.93 | ✗ / ✓ / ✓ |
| drop 13 / 12 | 32 / 41 | 0.95 / 0.98 | ✓ |
| drop of heads 0–7, 11, 15 | 45–50 | ≥ 0.98 | ✓ |

## Reading, with its limits
1. **The writer is a cooperative set of heads, not one head.**
   - No single head and no single KV group reproduces the repair (best single head S = 3; best group S = 11).
   - The verdict SPARSE_HEADS comes only from necessity.
2. **Head 10 is the robust core.** Removing it from an otherwise full patch cuts S from 51 to 16 and destroys round-specificity (frac 0.73).
   - It is in H\* under every leave-one-donor-group-out (14/14).
3. **The necessary set beyond head 10 sits at the threshold.**
   - Heads 8, 9 and 14 miss the ½ S(all) cut by 0.5–1.5 cells (26–27 vs 25.5). Leave-one-group-out adds them to H\* in 8/14 splits ({8,10}, {9,10}, {8,10,14}).
   - Head 13's drop (32) also costs more than half of what head 10's does.
   - The honest summary: the L11 conflict write needs heads 8–14 (KV groups 2–3), with head 10 most necessary. "Sparse = 1 head" overstates it.
4. **Attention routing is round-gated, but weakly, and equally in hosts and donors.**
   - Span-to-partner mass of head 10 is higher in the new (conflicting) arm than in ROUND for every donor and every host.
   - The difference is small: D ≈ 0.00007–0.027, on a mass of about 0.13. A uniform spread over the partner item would give about 0.08.
   - Hosts look at the partner about as much as donors.
   - So by the preregistered rule, the hosts' failure is **not** a routing failure at L11. The deficit lies in what heads 8–14 read out of the partner and peers (values built upstream), consistent with M2's resid L7–L10 repair.
   - Caveat: attention mass is correlational. A head can attend without using what it reads, and A1 says nothing about value content.
5. **Host heterogeneity persists.**
   - Host 2a4f596d is never repaired (S = 0 for every arm), as in M2.
   - Under drop 10, only host 1fb5651c keeps most of its repair (13 → 10).

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- Head patches show sufficiency and within-patch necessity, not necessity in the unpatched host.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.

## Next step suggested by this result
The open question has moved upstream: **what in the partner/peer values does the host lack?** A value-side experiment (M4) would patch, in host context:
- the donor's L11 K/V at the PARTNER positions only, against the ROUND-peer and REST positions;
- with the query side left the host's.

That separates "values at the partner carry the conflict" from "values elsewhere", using heads 8–14 as the readout.
