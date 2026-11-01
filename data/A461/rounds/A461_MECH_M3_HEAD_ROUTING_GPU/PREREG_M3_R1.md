# A461-MECH-M3 R1 — head-level routing at the L11 full-attention layer (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 7740 kev-4B forwards in 61 batches (60 × 128 + 60).
**Parent:** M2 R1 (ca949e7), verdict MIXER_WRITER at L11:
- the donor's own L11 `self_attn` output at the append span repairs 51/104 host cells, round-specifically (frac 0.99);
- the MLP is never a sufficient writer;
- linear attention at L8–L10 is non-specific.

## Question
- **P (which heads):** which of the 16 L11 query heads (4 KV groups) carry the repair?
- **R (where they look):** do the span's L11 queries attend to the **conflict-partner vote**, and does that depend on the round? That vote is the same author's earlier vote in the candidate round, which is what makes the appended vote a conflict.
  - If the host's attention is round-gated like the donors', the host's deficit lies in what the heads carry, not where they look.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m3_freeze_v1.py` (CPU + tokenizer only) |
| manifest blob | `aad3cbddb3ec7cbbbdbada97fb51ab5080702cc4` |
| design blob | `7445c13bc36c45324b54c3b4ea2fcbee0c37fe77` (rules under `preregistered_analysis`; token classes under `token_classes`) |
| runner blob | `a285df3dcd64fad4f1a071f6f027601fe580ac09` (derived from the M2 runner 6fdc11a1 by checked substitutions) |
| fake model | `A461_mech_m3_fake_attention_model_v1.py`: Qwen3.5-shaped gated GQA, 16 × 4 in 4 groups |
| self-test | `A461_mech_m3_selftest_v1.py` (result in `M3_SELFTEST_R3/`). R1 and R2 are kept as records.<br>- R1 scored 12/15. The fake cross-row check demanded exact 0 where batched fp32 attention gives ≤ 2.4e-7; R2 allows ≤ 1e-6 (fake only; descriptive in the runner). Two children died without a receipt.<br>- R2 logged every child (13/15) and showed the cause: `libgomp: Thread creation failed`, from the server's 256-thread per-user limit with 64-thread OpenMP pools in parent and child.<br>- R3 caps the self-test's OpenMP/MKL threads at 8.<br>- The runner is unchanged throughout. |
| analysis | `A461_mech_m3_analysis_v1.py` (blob `38d2b4cfde81a880fbb7180384b769e6774cfbd5`), written before the run; dry-run on the self-test fake output end to end (fake verdict INCONSISTENT_WITH_M2, as expected for a non-kev model) |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M2 raw `e1c4b34f`, G1.0 counterfactuals `06ee06d7` |

## Design
**Captures (44).** Donor new and ROUND (14 + 14); host new and ROUND (8 + 8). The hosts' ROUND arms are new in M3. Each capture records:
- the L11 `o_proj` **input** at the span: the gated per-head attention output, 16 × 256;
- the L11 attention probabilities from every span query to every earlier key.
  - They are recomputed at a pre-hook from the module's own q/k/v.
  - The forward is untouched: 36 captures must equal M1 bitwise.
  - The run fails closed unless the readout reconstructs the forward's own `o_proj` input to ≤ 1e-3 relative.

**Head patches (7696).** In each of the 104 cross-group cells, the host's `o_proj` input at the span is replaced for a head subset with the donor's. Everything downstream is recomputed in host context. `o_proj` has no bias, so this is exactly the per-head contribution. There are 37 arms:
- `all`: all 16 heads; must reproduce M2 mixer_L11;
- `head h` × 16: one head;
- `drop h` × 16: all but one head;
- `group g` × 4: the 4 query heads that share a KV head.

Each arm runs with source = donor new (main) and donor ROUND (round).

**Token classes (frozen in the design, tokenizer-derived).**
- PARTNER: the partner vote's rendered item. Exactly one per scene. It is always before the span, because the appended vote is rendered last.
- ROUND_PEERS: other authors' candidate-round votes.
- SELF: the span itself.
- REST: everything else.

In the ROUND arm, PARTNER is the same message, which no longer conflicts.

## Rules (coded in the design JSON)
- **S, SPEC:** as in M2.
- **Consistency gate:** |S(all) − S_M2(mixer, 11)| ≤ 5, and main JOINT agrees with M2 in ≥ 98/104 cells. Otherwise the verdict is **INCONSISTENT_WITH_M2** and no head claim is made.
- **Per-head and per-group criteria:**
  - SUF(h): S(head h) ≥ ½ S(all) and SPEC.
  - NEC(h): S(drop h) ≤ ½ S(all), which is necessity *within the patch*.
  - GSUF(g): S(group g) ≥ ½ S(all) and SPEC.
- **Verdict:**
  - **SPARSE_HEADS** if 1 ≤ |SUF ∪ NEC| ≤ 3;
  - **BROAD_HEADS** if |SUF ∪ NEC| > 3;
  - otherwise **KV_GROUP_LOCAL** if some group passes GSUF;
  - otherwise **DISTRIBUTED**.
- **H\*** = SUF ∪ NEC. If that is empty, the heads of the GSUF groups. If still empty, the 3 heads with the largest S(head h), labelled exploratory.
- **A1 (round-gated partner attention).**
  - mP is the PARTNER mass, averaged over span queries and over H\*. D(s) = mP(new) − mP(ROUND) within each scene.
  - DONOR_GATED if D > 0 for ≥ 11/14 donors. HOST_GATED if D > 0 for ≥ 6/8 hosts.
- **A2:** mP(new) of donors vs hosts. Descriptive only.

## Interpretation fixed in advance
- **DONOR_GATED and HOST_GATED:** the host's L11 heads find the partner by round just as donors do. The failing host's deficit is in **what those heads carry**: the partner's value representation, built upstream.
- **DONOR_GATED, not HOST_GATED:** an attention-pattern (**routing**) failure in hosts.
- **Not DONOR_GATED:** span-to-partner attention at L11 does not explain the round-specific evaluation.
- **Limits:**
  - Head patches show sufficiency and within-patch necessity, not necessity in the unpatched host.
  - Attention mass is correlational: a head can attend without using what it reads.
  - One model, one simulator family.
  - Cells share donors and hosts, so counts are descriptive decision rules, not independent tests.
