# A461-MECH-M20 R1: is the L11 append-span write necessary for the donors' own recognition? (natural-path necessity; preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. The user asked for the high standard ("按照高标准的来", 2026-10-31). The plan agreed then is M20 necessity, then M21 causal readout, then an M22 second-model replication, and only then the paper package. Run under the 2026-10-30 grant and the standing GPU authorization (policy V2): 488 kev-4B forwards in 4 batches (3 × 128 + 104).

**Why:** acceptance gate 1 of A612 (P1) asks for mediation necessity on natural behaviour. M1–M5 established only one direction, sufficiency: a recognizing donor's L11 write, or its context-read (BULK) part, repairs failing hosts. M20 runs the interchange in the other direction, inside the donors' own forward.

## Arms (L11 `o_proj` input at the donor's append span, every question row; target = the donor's new arm)
Per cross-group cell (donor d, host h), 104 cells:
- `full_host`: the whole L11 span write of host h.
- `full_ctrl`: the whole write of another recognizing donor d′. d′ is the next donor in roster order whose group differs from d's and h's.
- `bulk_host`: d's BULK part replaced by h's.
- `bulk_ctrl`: d's BULK part replaced by d′'s.

Per donor, 14 rows each:
- `bulk_round_self`: d's own ROUND-source BULK.
- `bulk_hostmean`: the mean of the cross-group hosts' BULK.

Captures: the 44 of M1–M16 (bitwise equal to M1).

**Baselines:**
- All 14 donors recognise natively (M > 0).
- 10 of them are JOINT (M > 0 and A > 0).

## Rules (coded in the design JSON)
- **C_loss:** the share of cells whose patched donor has M ≤ 0.
- **J_loss:** the same for JOINT, over the 10 JOINT donors' cells.
- **NEC_FULL:**
  - C_loss(full_host) − C_loss(full_ctrl) ≥ 0.40;
  - dM(full_host) < dM(full_ctrl) in ≥ 75% of paired cells;
  - a per-cell majority in ≥ 10 of 14 donors.
- **NOT_NEC_FULL:** the C_loss difference is < 0.10.
- **NEC_FULL_PARTIAL:** otherwise.
- **NEC_BULK:** the same rule, on `bulk_host` vs `bulk_ctrl`.
- **Reported:** the per-donor arms, per host, and leave one donor group out.
- **Gate:**
  - the 36 M1 capture readouts bitwise (runner);
  - the 14 donor baselines equal M1;
  - rows per arm as frozen.
  - Otherwise INCONSISTENT.

## Research contract ([standard V1](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §2–§5)
**Level:** an interchange intervention on *natural recognition*. This is the standard's §3.3 "local necessity", and with M1–M5 it gives a two-directional causal role at L11. It is still not the natural error path in the failing hosts.

**Controls:** each host-sourced arm has a donor-sourced arm of the same kind as control. That separates "any foreign write disrupts recognition" from "a non-recognizer's write does".

**False veto:** not applicable, since every target is a conflict. Its counterpart was measured in M17.

**What the result decides:**
- **NEC:** Tier A of the consolidation is upgraded to a two-directional causal role at L11, read from context.
- **NOT_NEC:** recognition in the donors is redundant across paths; Tier A stays one-directional.
- **Either way:** the paper's mechanism chain is fixed at L11.

**What it cannot show:**
- why the failing hosts produce a not-conflict write (M18 shows the conflict is decodable there);
- generality beyond kev-4B (M22).

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m20_freeze_v1.py` (CPU; reads the M16 design and M1 raw) |
| manifest blob | `22b761f2a55c69fa7b971678cb641f7979846712` (488 rows) |
| design blob | `8571841b8216ee13404bd0a16f5ad329421ebb80` |
| runner blob | `52d8e74805814d7eac8e679f5bae3cefe4b5eaa8`. It is the M17 runner dee985df with the plan, pins and names changed, and no patch-field or numeric-path change. Two lint warnings (an unused local and an unused import) are inherited unchanged from M17 |
| self-test | `A461_mech_m20_selftest_v1.py` (blob `d681499d`); result below |
| analysis | `A461_mech_m20_analysis_v1.py` (blob `38953cfe`), written before the run |

## Self-test
**R1 (`M20_SELFTEST_R1/`, 2026-10-31 23:41 +08): 13/13 PASS**, with zero GPU loads. It covers:
- preflight on the real 488-row manifest;
- the fake full path: 44 captures and 88 class files, sha and shapes;
- class contributions that sum to the `o_proj` input;
- **interchange wiring as frozen in 444/444 patch rows**;
- **identities:**
  - `full` with the donor's own write is a bitwise no-op;
  - `bulk` with its own BULK is a no-op up to 3.8e-6;
- the M17 refusal and admission tests.

The analysis dry run exits 0 with INCONSISTENT, as it must: fake logits are not M1's.
