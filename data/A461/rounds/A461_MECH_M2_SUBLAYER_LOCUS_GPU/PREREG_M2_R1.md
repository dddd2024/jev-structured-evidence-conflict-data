# A461-MECH-M2 R1 — layer-wise and sublayer locus of the span conflict evaluation (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 2532 kev-4B forwards in 20 batches (19 × 128 + 100).
**Parent:** M1 R1 (c235549, REL_SUPPORTED). At L11 the donor's append span carries a signed conflict evaluation: the original-vote span repairs 53/104 cells, the round-changed span 1/104, and the latter pushes hosts toward no-conflict.

## Question
Where does that evaluation enter the span, and so where does a failing host fall short?
- **F (formation):** which residual layer first carries a repair-sufficient, round-specific evaluation?
- **W (writer):** within L8–L11, is it written by the **token mixer** (linear attention L8–L10, full attention L11; context → span) or by the **MLP** (span-local computation)?

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m2_freeze_v1.py` |
| manifest blob | `1c8922b9acc9225be35a3270a099fc104a85781f` |
| design blob | `f76b58a6ac4a64622ab6ee02c239b8fe02c96ac2` (the rules below are coded under `preregistered_analysis`) |
| runner blob | `6fdc11a18d068da79aa26286fe3f82a5cfb3c471` |
| self-test | R2 15/15 PASS |
| analysis | `A461_mech_m2_analysis_v1.py`, written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, G1.0 counterfactuals `06ee06d7` |

**Self-test R1 (record).** It failed 1 test on a stale assertion copied from K-C (`layers == [11]`). The runner, manifest and design were unchanged; only the test was corrected.

**Self-test checks added in M2:**
- identity: each component patched with the host's own captured output gives bitwise-unchanged logits (6/6);
- addressing: resid, mixer and mlp patches give distinct outputs;
- capture identity: ROUND captures match the G1.0 token SHAs.

## Design
- **Units:** the same 104 cross-group cells as M1; all question rows; host new span.
- **Captures:** donor new, donor ROUND and host new, with all 32 layer outputs plus mixer/MLP outputs at L8–L11. Readouts must equal the M1 captures bitwise.
- **Arms:** each run with source = donor new (main) and donor ROUND (round):
  - `resid` at L7, L8, L9, L10 (L11 = M1 pinned);
  - `mixer` and `mlp` at L8, L9, L10, L11.
- **Sublayer patch semantics:** replace only that sublayer's output at the span positions with the donor's own output for that sublayer. The rest of the layer and all later layers are recomputed in host context.

## Rules (coded in the design JSON)
- **S(c, L):** cells where main is JOINT and round is not.
- **SPEC(c, L):** dM_main > dM_round in ≥ 75% of cells, and in a majority of cells for ≥ 10/14 donor groups.
- **L_f:** the smallest L ∈ 7..11 with S(resid, L) ≥ ½ S(resid, 11) and SPEC(resid, L).
- **SUFFICIENT_WRITER(X, L):** S(X, L) ≥ ½ S(resid, L) and SPEC(X, L).
- **Verdict at L_ref = max(L_f, 8):**
  - MIXER_WRITER — only the mixer is a sufficient writer;
  - MLP_WRITER — only the MLP is;
  - BOTH_SUFFICIENT — both are;
  - NEITHER_ALONE — neither is.
- **Always reported:** the full per-layer table, leave-one-donor-group-out, per host, and all nulls.

## Interpretation fixed in advance
- **MIXER_WRITER:** the evaluation enters the span through token mixing at L_ref. The failing host's deficit lies in what its mixer brings into the span: retrieval or routing from context, not span-local computation.
- **MLP_WRITER:** the donor span's own MLP output carries the evaluation. The deficit lies in span-local nonlinear computation, or in its inputs.
- **NEITHER_ALONE:** the evaluation needs both sublayers, or their interaction (cf. the multiple-mediator caveat, Vaidyanathan et al. 2026).
- **Limit:** a sublayer patch shows sufficiency, not necessity; no ablation is run. Attention heads and paths inside the mixer are not resolved. This is one model (kev-4B) and one simulator family.
