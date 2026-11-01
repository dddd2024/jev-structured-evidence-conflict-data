# A461-MECH-M4 R1: where the L11 conflict write reads from, and whether the host lacks the partner's values (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 2956 kev-4B forwards in 24 batches (23 × 128 + 12).

**Parent:** M3 R1 (e9d9746).
- The donor's L11 `o_proj` input at the host's append span repairs 51/104 cells round-specifically.
- Heads 8–14 cooperate in it; head 10 is the most necessary.
- Span-to-partner attention is round-gated only weakly, and alike in donors and hosts. By the M3 rule, the hosts' deficit is in what the heads read, not in where they look.

## Question
Per head, the `o_proj` input at a span query *i* is `gate_i ⊙ Σ_j p_ij v_j`, which is exactly linear in the keys *j* it reads. So the repairing write splits into the contributions of disjoint **key classes**.

- **K (where the repairing write comes from).** In the host, replace only the donor's contribution of one class:
  - `only_C` = host − host_C + donor_C;
  - or everything but that class, `drop_C` = donor − donor_C + host_C;
  - `full` = the M3 all-heads patch, which serves as a bitwise anchor.
- **V (does the host lack the partner's values?).** Keep the host's own L11 attention and gate, and read the **donor's L11 values at the 33 partner positions**. The partner item is 33 tokens in every scene, so its positions align token for token.
  - main target: host new;
  - round target: host ROUND, where the swap must not create a conflict that is not there.

## Two facts fixed by the data before the run
1. **Every key before the span is identical between a scene's new and ROUND arms.** The ROUND arm changes only the appended vote's `round` field, so the PARTNER, ROUND_PEERS, OTHER_ITEMS and CONTEXT keys and values are bitwise the same in both sources. Any round-specificity of `only_C` for a pre-span class must therefore come through the donor's span-side attention and gate, not from round information in those keys.
2. **The `round` field is rendered at the end of the span.** In the fake-model smoke run, span queries 0–28 are causally identical between new and ROUND, and only the last two differ. On kev-4B this holds by the same causality. So round-specific information can enter the span's L11 write only at its final positions.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m4_freeze_v1.py` (CPU + tokenizer only; cross-checks M3's token classes) |
| manifest blob | `5ce91077510e09b815f390bda761bd9efa8fa244` |
| design blob | `7ec989c0f70d3fcead4b64b035a32b6655110575` (rules under `preregistered_analysis`; classes under `key_classes`; 48 same-author cells under `same_author_cells`) |
| runner blob | `e3821ccb747f8e336740fb78229a1928dcaccdc4` (derived from the M3 runner a285df3d by checked substitutions) |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (M3's, unchanged; blob 725928dc) |
| self-test | `A461_mech_m4_selftest_v1.py` (blob `3a501cf2`; derived from the M3 self-test): **PASS 15/15** in `M4_SELFTEST_R1/`. Source = target identity holds for every op (full bitwise; others ≤ 7.6e-6); class additivity 4.5e-7 |
| analysis | `A461_mech_m4_analysis_v1.py` (blob `4761341a3b719919199e05947b33107de377c510`), written before the run; dry-run end to end on the fake output (fake verdict INCONSISTENT_WITH_M3, as expected for a non-kev model) |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, G1.0 counterfactuals `06ee06d7` |

## Design
**Captures (44).** Donor new and ROUND (14 + 14); host new and ROUND (8 + 8). Each capture records:
- the L11 `o_proj` input at the span;
- its five class contributions, recomputed at a pre-hook from the module's own q/k/v. The run fails closed unless they sum to the forward's own `o_proj` input within 1e-3 relative;
- the span-to-partner attention and the partner values.

The 36 captures that M1 also made must replay M1 bitwise.

**Key classes (frozen, tokenizer-derived; together they partition the keys before the span end):**
- PARTNER: the 33-token conflict-partner vote item;
- ROUND_PEERS: other authors' candidate-round votes;
- OTHER_ITEMS: every other received message before the span;
- SELF: the span itself;
- CONTEXT: every other key, i.e. the state header;
- ROUNDVOTES = PARTNER + ROUND_PEERS.

**Patches (2912).** Over the 104 cross-group cells:
- 13 key-class arms × 2 sources (donor new, donor ROUND), each targeting host new: `full`, `only_C` and `drop_C` for the 5 base classes, and `only_` / `drop_ROUNDVOTES`;
- `vswap_PARTNER` × 2 targets (host new, host ROUND), with source donor new.

The 208 `full` rows must equal M3's all-heads rows bitwise.

## Rules (coded in the design JSON)
- **S and SPEC:** as in M3.
  - Key-class arms: S counts cells where the main-source patch is JOINT and the round-source patch is not.
  - Value swap: S_V counts cells where the swap into host new is JOINT and the swap into host ROUND is not.
- **Consistency gate:** S(full) = S_M3(all) = 51, and the 208 full rows are bitwise equal to M3's. Otherwise the verdict is **INCONSISTENT_WITH_M3** and no locus claim is made.
- **Class rules:** SUF(C) iff S(only_C) ≥ ½ S(full) and SPEC. NEC(C) iff S(drop_C) ≤ ½ S(full).
- **Locus verdict:** let B be the base classes in SUF ∪ NEC.
  - **LOCUS:⟨B⟩** if 1 ≤ |B| ≤ 2;
  - **LOCUS:ROUNDVOTES** if B is empty and ROUNDVOTES is in SUF ∪ NEC;
  - otherwise **DIFFUSE**.
- **Value swap:**
  - **V_STRONG** iff S_V ≥ ½ S(full) and SPEC;
  - **V_PARTIAL** iff S_V ≥ ¼ S(full) and SPEC;
  - otherwise **V_NONE**.
- **Always reported:** leave-one-donor-group-out of both verdicts; per-host S; same-author vs different-author strata (descriptive); class contribution norms.

## Interpretation fixed in advance
- **V_STRONG or V_PARTIAL:** the host's own attention and gate are enough once it is given the donor's partner values. The host's deficit is then in the partner's **value representation**, built upstream in host context, consistent with M2's repair from residual states at L7–L10.
- **V_NONE with PARTNER in B:** the donor's partner contribution repairs only together with the donor's own span-side attention and gate. The host's span-side read of the partner is then also deficient, even though its attention mass is similar (M3).
- **SELF or CONTEXT in B:** the repairing write is not read from the conflict evidence (the partner and the round votes).
- **Confound:** the value swap also carries the donor's partner *content* (author, block, received differ across scenes). It is therefore not a pure swap of the context-built representation. The same-author cells (48/104) are reported separately, descriptively.
- **Limits:**
  - Class patches show sufficiency and within-patch necessity, not necessity in the unpatched host.
  - One model, one simulator family.
  - The 104 cells share donors and hosts, so counts are decision rules, not independent tests.
