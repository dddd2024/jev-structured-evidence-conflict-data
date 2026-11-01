# Claim → evidence map

**Paths.** Paths are relative to
`research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/`. "Prereg" means the decision rule was committed
in the stage's design file and analysis script before that stage's GPU run. "Exploratory" means the analysis was chosen
after seeing data.

**Readouts.** M = logit(conflicting_vote=true) − logit(false). A = logit(reject_conflict) − max(logit(accept),
logit(wait)).

**Units and baselines.** The statistical unit is the source group. Cells share donors and hosts, so all counts are
descriptive. Every baseline is an archived earlier-stage row, and every capture forward re-runs that row and equals it
bitwise.

**Earlier-round evidence.** Claims C0a and C0b cite the earlier rounds as reported in manuscript v5.2 (audited:
`2649a4b`, `a7bcb1d`, `35909bf`). They are not re-derived here.

## C0a — Recognition failure: background, earlier rounds

Appended conflicts were recognized in 1 of 20 confirmation scenes and in 1 qualified of 36 donor-round scenes.
Pre-existing conflicts were recognized in 6 of 6.

## C0b — Key-side readout localization: background, earlier rounds

25 of 26 pairs are key-side dominant. The reconstruction gate passed 224/224.

## C1 — Rarity at scale

**Statement.** Appended conflicts are missed in most scenes.

**Stage A** (frozen `1f773ef`, review `6991391`; run `7e9afe1`). `G2_STAGE_A_GPU_R1/G2_STAGE_A_ANALYSIS_R1/stage_a_analysis.json`:

| Key | Value |
|---|---|
| `C_rate` | old 0.145 / new 0.113 / SA 0.097 |
| `strict_qualified` | 4 / 124 |
| `qualified_source_groups` | 3 |
| `median_delta_new_minus_old` | +0.11 |

**Stage D** (D1 screen; run `01f46ef`). `stage_d_analysis.json` → `D1`: 0 strict donors in 47 scenes.

**Status.** Prereg strict rule (Stage-A admission draft; Stage-D design).

**Falsifier.** A high recognition rate on new arms.

## C2 — Specificity at layer 11

**Statement.** The recognized span carries content beyond dose, position and token form.

**Stage B** (`b0ed9d2` → `f79e30e`). `stage_b_analysis.json` → `summary.restoration_L11`:

| Control | Median dM | Cells won by main |
|---|---|---|
| Main arm | +1.82 | — |
| SA-sham | +0.36 | 16/16 |
| Permuted | +0.68 | 16/16 |
| Whole-span norm-matched random | +1.36 | 9/16 |

Preregistered restoration rule: 9/16 cells supportive across all groups. The cells-won column is an exploratory
breakdown.

**Stage C** (`4732f47` → `8c5608c`). `stage_c_analysis.json` → `H1_dose_matched_restoration_L11`:

| Key | Value |
|---|---|
| `supportive` | 16/16 |
| `content_specific` | true |
| `median_dM` | main +1.82 / dose-matched +0.31 |
| `median_main_minus_max_dose` | +1.24 |

The 64 layer-11 rows replicate Stage-B rows bitwise (runner-enforced).

**Status.** Prereg (H1: ≥10/16 cells, all donor groups, positive median gap).

**Falsifier.** The dose-matched random arm wins.

## C3 — Window

**Statement.** The span is read in layers 11–12 and is gone by layer 13.

**Stage C.** `H2_layers`, median dM of the main arm:

| Direction | L11 | L12 | L13 | L14 |
|---|---|---|---|---|
| Restoration | +1.82 | +0.63 | +0.06 | +0.04 |
| Suppression | −6.18 | −1.06 | −0.06 | −0.05 |

`boundary_layer` = 13. Stage B adds supporting results: layer 15 is about 0, and layer 7 is non-specific.

**Status.** Prereg (H2 boundary rule).

## C4 — Locus

**Statement.** A missed conflict is encoded like a duplicate vote.

**Stages B and C, suppression.** Main −6.18 vs donor-side SA-sham −6.45. The main arm is stronger in only 7/16 cells.
The preregistered Stage-B suppression rule **failed**, and that failure is the evidence here. Dose-matched noise gives
−0.26, and the main arm beats it in 16/16 cells (`H1b`).

**Stage C, H3 projection.** FFF median 0.09 vs held-out donors 0.12–0.48. AUC is 0.84 at layer 11, so the
**preregistered threshold is not met**; AUC is 0.90 at layer 12.

**Status.** Prereg. The SA-sham-equivalence reading is interpretive.

**Falsifier.** The main arm suppresses far more than the SA-sham.

## C5 — Readout repair

**Statement.** An implanted recognized span flips the host's own conflict read.

**Stage D** (`3baf794` → `01f46ef`). `stage_d_analysis.json` → `D2_layers.11`:

| Key | Value |
|---|---|
| Specific flips | 10/32 |
| Flips: main / SA-sham / dose | 11 / 1 / 1 |
| Donor groups | 3 |
| Host groups | 7 |

**Status.** Prereg flip counts. The preregistered *action* criterion is void by construction (erratum).

**Robustness (exploratory).** Without the run-140 donor: 3/24 specific flips, across 2 donor and 2 host groups.

## C6 — Decision repair

**Statement.** An implanted recognized span in the action row flips the decision to `reject_conflict`.

**Stage E** (`027c04a` → `d7b55c4`). `stage_e_analysis.json` → `summary.L11_action`:

| Key | Value |
|---|---|
| `specific_reject` | 10/32 |
| Rejects: main / SA-sham / dose | 11 / 1 / 0 |
| Donor groups | 3 |
| Host groups | 6 |
| `verdict` | ACTION_LEVEL_CORRECTION |
| `reachability_violations_scope_action` | 0 |
| `baseline_capture_rows_equal_stage_a` | true |
| `cross_row_max_absdiff` | 0.0 |

`L12_all`: 0/32.

**Status.** Prereg (≥2 donor groups and ≥2 host groups).

**Robustness (exploratory).** Without the run-140 donor: 4/24 cells, across 2 donor and 2 host groups.

## Integrity (all stages)

**Determinism and isolation.**
- Every capture equals its Stage-A row bitwise.
- Stage C replicates Stage B bitwise on 64 rows.
- In Stage E, the main and SA-sham action logits are bitwise identical between scopes (32/32).

**GPU ledger.** Total 2,191 G2 calls:

| Stage | Calls |
|---|---|
| A | 378 |
| B | 464 |
| C | 696 |
| D | 349 |
| E | 304 |

Reservations equal the receipts. There were 0 denied pre-hook calls and one attempt per stage. Each stage has an
admission file with the user's verbatim approval.

**Re-analysis.** All five frozen analysis scripts reproduce the archived analysis JSONs from the archived raw data (see
`REANALYSIS_CHECK.md`).
