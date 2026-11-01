# Claim → evidence map (V3)

**Paths.** Paths are relative to
`research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/`. "Prereg" means the decision rule was committed
in the stage's design file and analysis script before that stage's GPU run. "Exploratory" means the analysis was chosen
after seeing data.

**Readouts.**
- M = logit(conflicting_vote=true) − logit(false).
- A = logit(reject_conflict) − max(logit(accept), logit(wait)).
- C = M > 0, R = A > 0, JOINT = C ∧ R in the same forward pass.

**Units and baselines.** The statistical unit is the source group. Cells share donors and hosts, so all counts are
descriptive. Every baseline is an archived earlier-stage row, and every capture forward re-runs that row and equals it
bitwise.

**Earlier-round evidence.** Claims C0a and C0b cite the earlier rounds as reported in manuscript v5.2 (audited:
`2649a4b`, `a7bcb1d`, `35909bf`). They are not re-derived here.

**What changed from V1.**
- C4 is narrowed to a candidate locus.
- C7 (joint repair), C8 (recognition dependence) and K1–K3 (kev-4B) are new.

**What changed in V3 (audit `d9d3338`).**
- C8 is restated as a source-category contrast. It does not isolate recognition.
- K2 and K3 state that the hold-out is by scene: source groups overlap between K-B and K-C.

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

## C4 — Locus (candidate, not identified)

**Statement (narrowed in V2).** In transplant suppression, a missed conflict's span behaves like a duplicate-vote span. Together with C8, this makes an encoding failure the leading *candidate* explanation. It is not identified: H3 at layer 11 was not met, and layer 12 is not substituted for it.

**Stages B and C, suppression.** Main −6.18 vs donor-side SA-sham −6.45. The main arm is stronger in only 7/16 cells.
The preregistered Stage-B suppression rule **failed**, and that failure is the evidence here. Dose-matched noise gives
−0.26, and the main arm beats it in 16/16 cells (`H1b`).

**Stage C, H3 projection.** FFF median 0.09 vs held-out donors 0.12–0.48. AUC is 0.84 at layer 11, so the
**preregistered threshold is not met**; AUC is 0.90 at layer 12.

**Status.** Prereg. The SA-sham-equivalence reading is interpretive.

**Falsifier.** The main arm suppresses far more than the SA-sham.

## C5 — Readout repair

**Statement.** An implanted recognized span flips the host's own conflict readout.

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


## C7 — Joint repair in the same forward (SecJev; added after audit P0-2)

**Statement.** In one forward pass, a recognized span implanted into every row flips both the conflict readout
(C = M > 0) and the decision (R = A > 0) of a near-threshold host.

**Source: Stage E raw logits** (`d7b55c4`), recomputed by `extract_numbers_v8.py`. The values are in
`numbers_v8.json` → `joint`.

| Arm (layer 11, all rows) | C | R | JOINT | Donor groups of JOINT |
|---|---|---|---|---|
| Main | 11/32 | 11/32 | **8/32** | run-140: 7, run-338: 1 |
| SA-sham | 1/32 | 1/32 | 0/32 | — |
| Dose-matched random | 2/32 | 2/32 | 0/32 | — |
| Main, layer 12 | 3/32 | 0/32 | 0/32 | — |

**Status.** Exploratory: it was not a preregistered Stage-E endpoint, and is reported in v7 because the audit asked for
it.

**Robustness.** Leaving out donor run-140 leaves 1/24 (`joint.L11_main_lodo`). The cross-group generality of joint
repair is therefore claimed only from kev-4B (K3).

## C8 — Source-category dependence (Stage F, SecJev; K-C4, kev-4B)

**Statement (narrowed in V3).** Among the source categories tested, only strictly recognized appended-conflict spans
produce specific joint repair. Missed appended conflicts, conflicts recognized through a pre-existing conflict, and
duplicate-vote sources do not.

These categories differ in recognition, and also in source content, context and source–host relation. So recognition
is not isolated as the single factor, and content is not shown to be irrelevant. The preregistered hypothesis label
`H_F2_recognition_matters` is kept as frozen; it names the hypothesis, not an identification.

**Stage F** (frozen `3c31764`; run `6a19924`). `G2_STAGE_F_GPU_R1/G2_STAGE_F_ANALYSIS_R1/stage_f_analysis.json` →
`joint`:

| Source kind (layer 11, all rows, 8 near-threshold hosts) | JOINT | Prereg role |
|---|---|---|
| Donor new (recognized appended conflict; bitwise = Stage E) | 8/32 | reference |
| FFF new (appended conflict, missed; 6 new groups) | **0/48** | H-F2 |
| TTT SA (duplicate vote in a scene read as conflict-and-reject: class-matched) | 0/72 | H-F1 |
| TTT new (conflict recognized via a pre-existing conflict; 5 new groups) | 0/72 | H-F1, H-F3 |
| Donor SA | 0/32 | — |

**Verdicts.**

| Hypothesis | Rule | Met |
|---|---|---|
| `H_F2_recognition_matters` | fff_new ≤ 2 and donor_new − fff_new ≥ 5 | **true** |
| `H_F1_content_beyond_class` | — | false; uninformative, because neither TTT arm repairs (`STAGE_F_RESULT_NOTE.md`) |
| `H_F3_source_diversity` | — | false |

The class-matched comparison (8/32 vs 0/72) is exploratory.

**kev-4B, K-C4** (frozen `3a6173f`; analysis `84bc6f4`; run `5ef7a16`). `G2_K4B_KC_GPU_R1/G2_K4B_KC_ANALYSIS_R1/k4b_kc_analysis.json`:

| Key | Value |
|---|---|
| `K_C4_recognition` | true |
| `joint_rate_unrecognized` | 0.0 (0/40) |
| `joint_rate_main` | 0.51 |

**Falsifier.** Unrecognized spans repair at a rate comparable to recognized spans.

## K1 — kev-4B behaviour on the frozen inputs

**Source.** kev-4B screen (runner `f118ea59`, `dbe2f0e`; run `fd4bf13`).
`G2_K4B_STAGE_A_GPU_R1/G2_K4B_STAGE_A_ANALYSIS_R1/stage_a_analysis.json`:

| Key | Value |
|---|---|
| `C_rate` | old 0.008 / new 0.363 / SA 0.000 |
| `strict_qualified` | 44 / 124 |
| `qualified_source_groups` | 14 |
| `median_delta_new_minus_old` | +1.12 |

The frozen script and strict rule are the same as SecJev's Stage A. Inputs are identical: all 372 token SHAs match.
The 6 replays are bitwise equal.

**Status.** Prereg rule, applied to a second model.

**Implication.** The severity of the miss is model-specific (SecJev 88.7%, kev-4B 63.7% missed).

## K2 — kev-4B window

**Source.** K-B (frozen `66fa292`, rule in `A461_g5_g2_k4b_kb_analysis_v1.py`; run `3a6173f`). 6 donors × 4 hosts,
23 cross-group cells per layer. `G2_K4B_KB_GPU_R1/G2_K4B_KB_ANALYSIS_R1/k4b_kb_analysis.json` → `profile`:

| Layer | 3 | 7 | 11 | 15 | 19 | 23 | 27 |
|---|---|---|---|---|---|---|---|
| Median main − dose dM | −0.97 | −0.83 | **+0.64** | +0.54 | −0.00 | +0.00 | +0.00 |
| Share main > dose | 4% | 9% | 87% | 96% | 9% | 78% | 74% |

The shares at layers 23 and 27 sit on effects of about 0.003 or less, so they are noise around zero. The rule is the
argmax of the median gap, with ties going to the lower layer: `window_layer` = 11.

**Status.** Prereg.

**Caveat.** At layer 15 the share is higher but the gap is smaller (see README, weak point 4).

## K3 — kev-4B cross-group replication of specificity and joint repair

**Source.** K-C (frozen `3a6173f`; analysis `84bc6f4`, committed before any K-B or K-C result; run `5ef7a16`). 14 donors
(one per donor group) × 8 near-threshold hosts, all disjoint from K-B, at layer 11. 104 cross-group cells.
`k4b_kc_analysis.json`:

| Criterion | Key | Value | Met |
|---|---|---|---|
| K-C1 dose specificity | `main_eval.share_main_gt_dose`, `groups_majority_main_gt_dose` | 0.913; 14/14 | yes |
| K-C2 sham specificity | `main_eval.share_main_gt_sham` | 1.0 | yes |
| K-C3 joint generality | `main_eval.specific_joint`, `specific_joint_groups`, `specific_joint_top_group_share` | 53; 14; 0.132 | yes |
| K-C4 recognition | see C8 | 0/40 | yes |

**Flips (C / R / JOINT)** (`flips_cross_group`):

| Arm | C | R | JOINT |
|---|---|---|---|
| Main | 65 | 62 | 53 |
| SA-sham | 0 | 0 | 0 |
| Dose | 12 | 5 | 0 |
| Unrecognized | 0 | 0 | 0 |

**Leave one donor group out** (`leave_one_donor_group_out`): 46–52 specific joint repairs, from ≥ 13 groups. 7/8 hosts
are repaired.

**Status.** Prereg (all four criteria).

**Independence.**
- **Scenes.** K-C scenes are disjoint from K-B's.
- **Source groups.** The six K-B scan-donor groups are among the 14 K-C donor groups (`k4b_kb_design.json` →
  `scan_donors`; `k4b_kc_design.json` → `replication_donors`). The hold-out is therefore by scene.
- **Hosts.** The 104 cells share 8 hosts, so the counts are descriptive. They are not rates over independent tasks.

**Falsifier.** The dose or sham arm matches the main arm, or the repairs come from fewer than 7 groups.

## Integrity (all stages)

**Determinism and isolation.**
- Every capture equals its earlier-stage row bitwise; this is runner-enforced.
- Stage C replicates Stage B bitwise (64 rows).
- Stage F's donor rows equal Stage E's bitwise (64).
- kev-4B K-B and K-C captures equal kev-4B screen rows bitwise.
- In all-row captures, the span state is identical across question rows (cross-row max absdiff 0.0). This was
  re-verified from the released tensors by `verify_captures_v1.py` (`REANALYSIS_CHECK.md`).

**GPU ledger.** Total 3,628 G2 calls (`numbers_v8.json` → `ledger`):

| Model | Stage | Calls |
|---|---|---|
| SecJev | A | 378 |
| SecJev | B | 464 |
| SecJev | C | 696 |
| SecJev | D | 349 |
| SecJev | E | 304 |
| SecJev | F | 296 |
| kev-4B | screen | 378 |
| kev-4B | K-B | 346 |
| kev-4B | K-C | 417 |

For every stage:
- reservations equal physical calls;
- 0 calls were unreserved;
- 0 pre-hook calls were denied;
- there was one attempt.

**Admissions.**
- Stages A–F and the kev-4B screen carry the user's verbatim per-stage approvals.
- K-B carries a per-stage approval.
- K-C carries the standing authorization (`GOVERNANCE_AMENDMENT_20261027_STANDING_GPU_AUTHORIZATION.md`).
