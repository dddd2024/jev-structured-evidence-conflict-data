# A461-MECH-M5 R1: size vs direction vs content of the L11 conflict write (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 2540 kev-4B forwards in 20 batches (19 × 128 + 108).

**Parent:** M4 R1 (f5bbf87). The donor's L11 span write (51/104 repairs) splits exactly into key-class contributions.
- Dropping the partner's part keeps 41/51 repairs. The partner part alone repairs 1. The partner value swap repairs 0 (V_NONE).
- Dropping OTHER_ITEMS (→ 8) or CONTEXT (→ 23) loses the repair: verdict LOCUS:CONTEXT+OTHER_ITEMS.
- **Caveat:** OTHER_ITEMS and CONTEXT are also the largest contributions. M4 cannot tell size from content.

## Question
A class contribution is a vector at the 31 span positions (16 heads × 256). It can be rescaled, and it can be moved across scenes because the span width is 31 everywhere. Let BULK = OTHER_ITEMS + CONTEXT, and let Δ = donor − host. M5 tests:
- **B (BULK together):**
  - `only_BULK` = host − host_B + donor_B;
  - `drop_BULK` = donor − donor_B + host_B.
- **D (direction at matched size):** `dir_C` = host + α_C · Δ_C, with α_C set per row and span position so that ‖α_C Δ_C‖ = ‖Δ_full‖. Every direction arm therefore changes the host exactly as much as the full patch does. C ranges over PARTNER, ROUND_PEERS, OTHER_ITEMS, CONTEXT, SELF, ROUNDVOTES and BULK.
- **R (null):** `dir_RAND` = host + ‖Δ_full‖ · u, where u is a seeded unit-Gaussian direction per span position, fixed per cell and shared by the main and round sources.
- **X (content):** `xdonor_BULK` = donor − donor_B + third_B. The third donor comes from neither the donor's nor the host's group, and its arm (new or ROUND) is the source's. Each of the 14 donors serves as third 7–8 times.
- **full:** the M3 all-heads patch, serving as a bitwise anchor.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m5_freeze_v1.py` (CPU + tokenizer only; derived from the M4 freeze, and cross-checks the M4 key classes) |
| manifest blob | `cfa937d1b73427b9ccac1cd6493c8de38838af3e` |
| design blob | `26126568cce05db149d815b2faf3090e5e84c27b` (rules under `preregistered_analysis`; the third donors under `third_donor`) |
| runner blob | `f9d36a69e675610cf5fea51926959a2708be47f4` (derived from the M4 runner e3821ccb by checked substitutions) |
| fake model | `A461_mech_m3_fake_attention_model_v1.py` (unchanged; blob 725928dc) |
| self-test | `A461_mech_m5_selftest_v1.py` (blob `ce6df5f5`; derived from the M4 self-test): **PASS 16/16** in `M5_SELFTEST_R1/`. Matched-size gate max rel err 2.7e-7; direction over all classes = full (α median 1.0, logits ≤ 7.2e-6); analysis dry-run end to end on the fake output (fake verdict INCONSISTENT_WITH_M3, as expected) |
| analysis | `A461_mech_m5_analysis_v1.py` (blob `f1bd26a33908ac15d1716576bf941029d9da8e35`), written before the run |
| inputs | roster `1bc84bf5`, M1 design `f3852efc`, M1 raw `298c7cdf`, M3 design `7445c13b`, M3 raw `a8c0fa6b`, M4 design `7ec989c0`, G1.0 counterfactuals `06ee06d7` |

## Design
- **Captures:** 44, as in M4. The class contributions must sum to the forward's own `o_proj` input (fail-closed), and 36 captures must replay M1 bitwise.
- **Patches:** 12 arms × 2 sources (donor new = main, donor ROUND = round) × 104 cells = 2496, all targeting host new. The 208 `full` rows must equal M3 bitwise.
- **Matched-size gate:** for every `dir_*` and `dir_RAND` row, ‖patch − host‖ must equal ‖donor − host‖ per row and span position within 1e-3 relative (fail-closed). α statistics are recorded in every row.

## Rules (coded in the design JSON)
- **S, SPEC:** as in M2–M4.
- **Consistency gate:** S(full) = S_M3(all) = 51, and the 208 full rows are bitwise equal to M3's. Otherwise INCONSISTENT_WITH_M3.
- **BULK:**
  - BULK_SUF iff S(only_BULK) ≥ ½ S(full) and SPEC;
  - BULK_NEC iff S(drop_BULK) ≤ ½ S(full).
- **Direction:** DIR_SUF(C) iff S(dir_C) ≥ ½ S(full) and SPEC.
- **Null:** RAND_NULL iff S(dir_RAND) ≤ 5 and not SPEC.
- **Verdict:**
  - if not RAND_NULL: **MAGNITUDE_SUFFICES**, and no direction claim is made;
  - else, with D = {C : DIR_SUF(C)}:
    - **PARTNER_DIRECTION** if PARTNER or ROUNDVOTES is in D and no BULK-side class (OTHER_ITEMS, CONTEXT, BULK) is;
    - **BULK_DIRECTION** if a BULK-side class is in D and neither PARTNER nor ROUNDVOTES is;
    - **BOTH_DIRECTIONS** if both kinds are in D;
    - **SELF_DIRECTION** if D = {SELF};
    - **NO_SINGLE_DIRECTION** if D is empty.
  - Completion rule, fixed here before the run: any other D (for example {ROUND_PEERS}, or SELF with ROUND_PEERS) is labelled **OTHER_DIRECTION:⟨D⟩**.
- **Content:** XD_HOLDS iff S(xdonor_BULK) ≥ ½ S(full) and SPEC; otherwise XD_FAILS.
- **Always reported:**
  - leave-one-donor-group-out of every verdict;
  - per-host S;
  - α statistics;
  - per-cell geometry of Δ_C (norm ratio and cosine to Δ_full), from the capture files.

## Interpretation fixed in advance
- **Size effect.** M4's necessity of OTHER_ITEMS / CONTEXT is a size effect in either case:
  - RAND_NULL holds and BULK_DIRECTION does not;
  - a non-BULK class repairs at matched size.

  **PARTNER_DIRECTION** means the partner direction carries the evaluation and was only too small in M4.
- **BULK_DIRECTION with RAND_NULL:** the context-wide read carries the round-specific evaluation in its *direction*, not just its size.
- **NO_SINGLE_DIRECTION:** the evaluation is a combination across classes.
- **XD_HOLDS:** the BULK part need not come from the same scene as the rest of the donor's write, so it acts as a generic "donor-like context" component. **XD_FAILS:** the donor's own context content matters.
- **α can be large** for a small class difference (SELF, PARTNER). A large rescaling can push the state off-distribution, so a failed dir_C at large α is weaker evidence than one at α ≈ 1–2.
- **Round-specificity:** every key before the span is identical in a scene's new and ROUND arms, and the round token is at the span's end. So round-specificity in the pre-span classes comes from the donor's span-side queries and gates.
- **Limits:**
  - One model, one simulator family.
  - The 104 cells share donors and hosts, so counts are decision rules, not independent tests.
