# A461-MECH-M4 R1: result (where the L11 conflict write reads from)

**Run:**
- 2956/2956 kev-4B forwards in 24 batches; 0 denied.
- The 36 M1 replays and all 208 `full` rows are bitwise equal to M1 and M3 (`bitwise_vs_m1` and `bitwise_vs_m3: checked`).
- Elapsed 4362 s. Raw blob `46274e8eb6fa917414dc416a69d5a61da56c24da`.
- The run follows prereg 4c8de7a under the standing GPU authorization. The pre-model gate passed, and there was a single ledger attempt.

**Readout validity:** at all 44 captures, the five class contributions sum to the forward's own `o_proj` input within 2.1e-6 (gate: 1e-3 relative), and the readout reconstruction is exact. The captures (102 MB) stay on the server under `M4_GPU_RUNS/ATTEMPT_R1/captures`. Their hashes are in the raw rows.

**Analysis:** `A461_mech_m4_analysis_v1.py` (blob 4761341a, frozen before the run). Output: `M4_ANALYSIS_R1/m4_analysis.json`.

## Preregistered outcome
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51 = S_M3(all); 208/208 full rows bitwise equal to M3 |
| SUF (a class alone suffices) | none |
| NEC (drop class ⇒ S ≤ 25.5) | **OTHER_ITEMS, CONTEXT** |
| **locus verdict** | **LOCUS:CONTEXT+OTHER_ITEMS**; same in 14/14 leave-one-donor-group-out splits |
| **value swap** | **V_NONE** (S_V = 0); same in 14/14 splits |

## Table (S out of 104; frac = share of cells with dM_main > dM_round)
| arm | S | frac | SPEC | median dM main / round |
|---|---|---|---|---|
| full (M3 all-heads) | 51 | 0.99 | ✓ | +0.35 / −0.37 |
| drop SELF | 47 | 0.99 | ✓ | +0.35 / −0.46 |
| drop PARTNER | 41 | 1.00 | ✓ | +0.31 / −0.48 |
| drop ROUND_PEERS | 40 | 0.99 | ✓ | +0.27 / −0.31 |
| drop ROUNDVOTES | 35 | 0.99 | ✓ | +0.22 / −0.45 |
| drop CONTEXT | **23** | 0.74 | ✗ | +0.33 / +0.19 |
| drop OTHER_ITEMS | **8** | 0.93 | ✓ | +0.18 / −0.04 |
| only OTHER_ITEMS | 14 | 0.45 | ✗ | +0.17 / +0.22 |
| only CONTEXT | 5 | 0.82 | ✓ | +0.06 / −0.05 |
| only ROUNDVOTES / ROUND_PEERS / PARTNER | 2 / 1 / 1 | 0.83–0.85 | ✓ | ≤ +0.10 |
| only SELF | 0 | 0.62 | ✗ | ≈ 0 |
| **vswap PARTNER** (host attention and gate, donor partner values) | **0** | 0.71 | ✗ | +0.06 / +0.03 |

**Strata:** in the same-author cells (48) and the different-author cells (56) alike, vswap S = 0 and only_PARTNER S ≤ 1. drop_PARTNER keeps 17/24 and 24/27 of the full repairs respectively.

## Reading, with its limits
1. **The repairing write is not a read of the conflict-partner vote.**
   - Removing the donor's partner contribution keeps 41/51 repairs, all fully round-specific (frac 1.00).
   - The partner contribution alone repairs 1 cell.
   - Giving the host the donor's partner values under the host's own attention repairs none, whether or not the authors match.
   - This revises the reading drawn from M3. M3's DONOR_GATED + HOST_GATED rule pointed to "what the heads read, the partner's values". By M4's preregistered rule, the partner's values are not what the host lacks (V_NONE).
2. **What is necessary is the part read from the bulk of the state:** the other received messages (drop → 8/51) and, at the threshold, the state header (drop → 23/51, frac 0.74).
   - Neither is sufficient alone. only_OTHER_ITEMS moves the margin up for both sources alike (frac 0.45), so it carries no round signal by itself.
   - The round-specific repair needs the donor's write as a whole: a broad context read combined with the class-wide contrast.
3. **Where the round-specificity comes from.**
   - Every key before the span is token-identical between the donor's new and ROUND sources, and the round token sits at the end of the span. So the specificity must arise from the donor's span-side queries and gates over these shared keys.
   - Every pre-span only_C arm except OTHER_ITEMS is round-specific in direction (frac 0.82–0.85, SPEC) but tiny in size: it shifts the direction without carrying a decision.
   - The ROUND source writes an active "no conflict" signal: median dM_round is −0.37 for full, and −0.48 when the partner part is dropped.
4. **Caveat: necessity tracks size.** OTHER_ITEMS and CONTEXT are the largest contributions (median norms about 4.7 and 3.5, against about 1.2–1.9 for PARTNER, ROUND_PEERS and SELF). They also hold most of the attention mass (M3: REST ≈ 0.70). Removing a large part of the donor's write may lose the repair partly through magnitude rather than specific content. M4 cannot separate those two explanations.
5. **Descriptive:** the PARTNER contribution's norm is larger in donors than in hosts (median 1.77 vs 1.22), but swapping it does not help.
6. **Host heterogeneity persists.** Host 2a4f596d is still never repaired; host 1c7158b6 gets 1 repair.

**General limits:**
- One model (kev-4B, LoRA) and one simulator family.
- Class patches show sufficiency and within-patch necessity, not necessity in the unpatched host.
- The 104 cells share 14 donors and 8 hosts, so the counts are preregistered decision rules, not independent tests.

## Where the M1–M4 chain now stands
- M1: the span's L11 representation carries a signed, round-specific conflict evaluation.
- M2: L11 full attention writes it.
- M3: heads 8–14 write it together, with head 10 most necessary; attention to the partner is similar in hosts and donors.
- M4: that write is read mainly from the other messages and the state header, not from the partner vote, and the host does not lack the partner's values.
- The working hypothesis is now that the evaluation is a **context-wide summary keyed by the span's own round** (the round token comes last), not a pairwise lookup between the appended vote and its partner.
- A natural next test is a magnitude-matched control that separates "large context read" from "specific context content":
  - only_OTHER_ITEMS rescaled to the norm of the donor write;
  - a swap of OTHER_ITEMS contributions from a third, unrelated donor;
  - plus a test of the hypothesis on SecJev-0.8B.
