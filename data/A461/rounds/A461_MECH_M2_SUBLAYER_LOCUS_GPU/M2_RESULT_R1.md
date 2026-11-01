# A461-MECH-M2 R1 — result: **MIXER_WRITER at L11** (the full-attention layer)

**Run:** `COMPLETE_A461_MECH_M2`. 2532/2532 physical calls in 20 batches; 0 denied. `bitwise_vs_m1: checked`, so all 36 captures reproduce M1 bitwise (enforced at run time, fail-closed). The host baselines equal M1's (checked by the analysis). Elapsed 3737 s.
**Rule source:** `m2_design.json` (blob `f76b58a6`) and `A461_mech_m2_analysis_v1.py`, both written and committed before the run (3d561c9). Raw blob `e1c4b34fcef9221a98e8209f6bbff3f6536b15d4`. The 873 MB of captures stay on the server (`~/wjc/a461-g5-minimal-patch-pilot-20261025-v1/M2_GPU_RUNS/ATTEMPT_R1/captures`, SHA256SUMS in `M2_GPU_R1/`).

## Main table (104 cross-group cells; S = main JOINT and round not JOINT)

| arm | L7 | L8 | L9 | L10 | L11 |
|---|---|---|---|---|---|
| resid S | 20 ✓ | 24 ✓ | 20 ✓ | 21 ✓ | **52 ✓** (M1) |
| mixer S | — | 0 ✗ | 4 ✗ | 9 ✗ | **51 ✓** |
| mlp S | — | 0 ✗ | 2 ✗ | 3 ✗ | 1 ✗ |

✓/✗ = SPEC (dM_main > dM_round in ≥ 75% of cells, and in a majority of cells for ≥ 10/14 groups).

**Arms with a strong round contrast:**

| arm | frac main > round | median dM main / round |
|---|---|---|
| resid L7–L10 | 0.83–0.86 | ≈ −0.3 / −1.1 |
| mixer L11 | 0.99 | +0.35 / −0.37 |
| resid L11 | 1.00 | +0.38 / −1.13 |

**Arms with no round contrast:**

| arm | frac main > round | JOINT main / round |
|---|---|---|
| mixer L8 | 0.25 | 14 / 16 |
| mixer L9 | 0.55 | 18 / 16 |
| mixer L10 | 0.60 | 20 / 14 |
| mlp, all layers | 0.20–0.55 | ≤ 7 / ≤ 7 |

- **L_f = 11.** S(resid, L) at L7–L10 is 20–24, below the threshold of 26 (½ of 52), although every one of those arms passes SPEC.
- **L_ref = 11.** The mixer is a sufficient writer there (51 ≥ 26 and SPEC); the MLP is not (1).
- **Verdict: MIXER_WRITER.**

## Robustness (preregistered reporting)

**Leave-one-donor-group-out.**
- 12/14 drops keep **MIXER_WRITER**.
- Dropping run-181 or run-344 moves L_f to 8 (resid L8 then just reaches ½ S(resid, 11)). The verdict at L_ref = 8 becomes **NEITHER_ALONE**.
- So the *writer* finding at L11 is stable. The *formation layer* sits on a threshold edge: under those two drops an early residual already carries about half of the L11 repair.

**Per host (S of mixer L11 vs resid L11).**

| host | mixer L11 | resid L11 |
|---|---|---|
| 1c7158b6 | 1 | 1 |
| 1fb5651c | 13 | 5 |
| 264c458d | 10 | 8 |
| 2a4f596d | 0 | 0 |
| 2c9118bb | 5 | 5 |
| 4bcbaf15 | 11 | 9 |
| 75642418 | 7 | 12 |
| 8ae85754 | 4 | 12 |

- One host (2a4f596d) cannot be repaired by any arm.
- The mixer exceeds the residual on 3 hosts and falls short on 2.

**Descriptive, not preregistered: cell overlap.**
- The mixer L11 and resid L11 S sets share 35 cells (51 and 52 each). The two patches are not identical interventions: the resid patch also carries the donor's L0–L10 span residual, while the mixer patch recomputes the residual in host context and adds only the donor's attention output.
- The early resid arms are almost subsets of resid L11 (L7 18/20, L8 22/24, L9 18/20, L10 18/21).

## Interpretation (applying the preregistered reading)

1. **What the failing host is missing is the L11 full-attention output at the span.** Take the donor's own L11 `self_attn` output and keep everything else from the host (the host's L0–L10 residual and its L11 MLP, recomputed). That repair is the same size as the full L11 residual patch (51 vs 52 cells), with the same round specificity (frac 0.99). The round-changed attention output does not repair, and pushes M negative (median −0.37). So the conflict evaluation is **written into the span by L11 full attention reading from context**. The span-local MLP (L8–L11) is never a sufficient writer.
2. **Linear attention at L8–L10 writes no round-specific evaluation.** Patching those mixers does perturb the host (JOINT 14–20 in both main and round), but main and round have no direction (frac 0.25–0.60). It is non-specific perturbation, not evaluation.
3. **The early residual (L7–L10) already carries a weaker round-specific signal.** S is 20–24, frac 0.83–0.86, round dM about −1.1: the round span lowers M markedly. That signal does not come from the L8–L10 sublayer outputs (neither of which is SPEC), so it is in the L≤7 residual the span carries in. This fits the story that the span's token identity / early representation already encodes "this vote is for a different round". Turning it into a repair-strength evaluation needs the attention step at L11.
4. **Combined with G1.0 and M1:** the repair comes from computation in the donor context (G1.0). The L11 span carries a signed, round-specific evaluation (M1). That evaluation is fetched by L11 full attention from the context into the span (M2). The miss in failing hosts is therefore at least partly a **retrieval/routing failure**: in host context the L11 attention does not move the conflict-relevant evidence into the appended vote span.

## Limits (fixed in advance; added to after the results)
- **Sufficiency, not necessity.** No ablation was run, so the claim that L11 attention is *necessary* is not tested.
- **Heads are not resolved.** It is not known which heads, nor which context positions are attended to (the candidate block's existing votes? the validator set?). That is M3's job: head-level patching plus the attention-weight difference donor vs host.
- **The L_f threshold edge.** 2/14 LOGO drops turn it into L_f = 8 / NEITHER_ALONE. "Formation at L11" should be stated as "repair-strength evaluation appears at L11; a weaker round-specific signal already exists at L≤7".
- Counts are cells that share donors and hosts; they are descriptive decision rules, not independent tests. One model (kev-4B), one simulator family (twins_streamlet), 14 donors × 8 hosts.
