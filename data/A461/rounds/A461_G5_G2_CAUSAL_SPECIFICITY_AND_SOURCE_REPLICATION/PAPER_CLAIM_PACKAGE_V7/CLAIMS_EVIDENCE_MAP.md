# Claim → evidence map (V7)

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

**What changed in V7 (audit `8dd4528`).**
- **M-H** is narrowed to behavioural non-robustness on one matched counterfactual. It adds the twins' three-action
  outcome, the source-group spread and the edit-family status.
- **M-E:** ARM_SHORTCUT is a validity-specificity verdict, not proof that validity is unrepresented. The SecJev L11
  partial sensitivity is stated.
- Numbers come from `numbers_mech_v4.json`.

**What changed in V6 (M23, full reframe).**
- **New claim M-H, the headline behavioural result.** Both scorers' conflict judgment follows the appended vote's
  form, not its validity (same-span twins).
- **M-E restated.** The probe separability is form or arm: preregistered ARM_SHORTCUT on every detector, both models.
  "Represented but not used" is withdrawn.
- **Terminology.** Throughout C1–C8, K1–K3 and M-A to M-D, "recognized" means readout-positive: the conflict readout is
  true on the appended vote and false on the original and duplicate scenes. It is not a validity check.
- Numbers come from `numbers_mech_v3.json`.

**What changed in V5 (audit `02a2b73`).**
- M-A, M-B and M-D are stated as local and conditional, for these 14 donors × 8 hosts. M-D covers four repair families and
  names M20's 5 survivors.
- M-E is narrowed to linear separability, and the arm confound is stated. The G2.3 same-span counterfactual is
  constructible (124/124 scenes, 17/17 groups) but has not been run.
- M-F is narrowed to "the tested decision-token steering produced no selective repair".
- M-G (three-action safety) is new.
- Numbers come from `numbers_mech_v2.json`.

**What changed in V4.**
- Claims M-A to M-F (mechanism route M1–M22) are added at the end, with stage, commit, archived JSON key and falsifier.
  Their numbers are extracted by `extract_numbers_mech_v1.py` into `numbers_mech_v1.json`.
- C4 is revised: the candidate explanation is no longer a missing encoding (M18, M21, M22).

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

**Statement (narrowed in V2, revised in V4).** In transplant suppression, a missed conflict's span behaves like a duplicate-vote span. In V3, together with C8, this made an encoding failure the leading *candidate* explanation; H3 at layer 11 was not met, and layer 12 is not substituted for it. **V4:** M18 and M22 (claim M-E) show that the appended conflict is linearly decodable from the missed span with a held-out probe. The two findings are compatible: the missed span lacks the round-keyed verdict in the form downstream rows read (M-A, M-B), not the information. The encoding-failure candidate is withdrawn in favour of "represented but not used".

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

# Mechanism route M1–M22 (added in V4)

**Paths.** Stage folders are `research/rounds/A461_MECH_M<i>_*` and `research/rounds/A461_MON_M18_*` / `A461_MON_M22_*`.
JSON keys refer to `M<i>_ANALYSIS_R1/m<i>_analysis.json` (M17: `M17_ANALYSIS_R1_V1_1/`). Every stage is preregistered:
design, manifest and analysis script were committed before its GPU run.

**Unit.** Unless stated, the unit is the K-C cross-group cell (14 donors × 8 hosts, 104 cells). Cells share hosts, so counts are descriptive. Every verdict is reported with its leave-one-donor-group-out (LOGO) stability. S = cells repaired jointly by the main donor and not by its round control (same scene, only the vote's round changed to a non-candidate round).

**Recompute.** `recompute_mech_v1.py` re-runs all 22 frozen analyses on the archived raw rows and captures and compares every output with the committed JSON (`REANALYSIS_CHECK.md`, section V4).

## M-A — The layer-11 span state carries a round-sensitive conflict signal (Tier A; local, conditional on these 14 × 8 scenes)

| Stage (prereg → result) | Key | Value |
|---|---|---|
| M1 (227c628 → c235549) | `verdict_round`; `cross_group.J_main` / `J_round` / `J_okalt` | REL_SUPPORTED; 53 / 1 / 66 of 104 |
| M1 | `cross_group.frac_dM_main_gt_round`; `groups_majority_main_gt_round` | 1.0; 14 |

**Falsifier.** The round arm repairs about as often as the main arm.

## M-B — Writer, read and direction (Tier A; local, conditional)

| Stage | Key | Value |
|---|---|---|
| M2 (3d561c9 → ca949e7) | `verdict`; `L_f`; `table.mixer_L11.S`; max `table.mlp_L8..11.S` | MIXER_WRITER; 11; 51; 3 |
| M2 | `table.resid_L7..10.S` | 20, 24, 20, 21 (weaker round-specific signal before L11) |
| M3 (342e559 → e9d9746) | `verdict`; `table.all.S`; max `table.head*.S`; `table.drop10.S`; `table.drop8/9/14.S` | SPARSE_HEADS; 51; 3; 16; 26 / 27 / 27 |
| M4 (4c8de7a → f5bbf87) | `verdict`; `value_swap`; `table.drop_OTHER_ITEMS/CONTEXT/PARTNER.S` | LOCUS:CONTEXT+OTHER_ITEMS; V_NONE; 8 / 23 / 41 of 51 |
| M5 (7187842 → 695f4fe) | `verdict`; `content`; `table.dir_BULK/dir_RAND/xdonor_BULK.S` | BULK_DIRECTION; XD_HOLDS; 48 / 1 / 51 of 51 |

**Edge criteria.** M2: two of 14 LOGO splits move the formation layer to 8. M3: only head 10 meets the sparse-writer rule;
heads 8 / 9 / 14 sit at threshold, and no unique or sparse writer circuit is claimed. M4: CONTEXT and OTHER_ITEMS both matter,
so the validator / block / vote fields are not separated.

**Falsifier.** Random directions of the same size repair as often as the bulk direction.

## M-C — Pooled decomposition (Tier B, 3 of 8 hosts) and Tier C

M6–M16 verdicts are in each JSON's `verdicts` (M6: `shared_verdict`, `lowrank_verdict`) and in manuscript Table M1. The
pooled arms repair only hosts 1fb5651c, 264c458d and 4bcbaf15. Tier C (M12–M16) is host-specific. M16's preregistered
`verdicts.w_linear` is W_LINEAR_FAILS. **These are not used for the paper's claims.** Failed criteria are listed in
`LIMITATIONS_AND_ERRATA.md`.

## M-D — False veto of four representative repair families; partial interventional necessity

| Stage | Key | Value |
|---|---|---|
| M17 (84bd0a0 → dfa3aac; analysis v1.1) | `verdicts.arm_verdicts` | full NONSELECTIVE; meanD, cs0, abc05 MIXED (14/14 LOGO) |
| M17 | `false_veto["full@SA"].FV`, `["full@ROUND"].FV`, `["meanD@ROUND"].FV` | 36, 43, 24 of 104 |
| M17 | `false_veto["cs0@OUTSIDER"].FV`, `["abc05@OUTSIDER"].FV` | 11, 9 of 104 (all on host 1fb5651c) |
| M20 (c286b38 → 8b87ff9) | `verdicts.full` / `bulk` | NEC_FULL_PARTIAL / NEC_BULK_PARTIAL (14/14 LOGO) |
| M20 | `per_donor_arms.bulk_round_self.C_loss`, `.n` | 0.643 of 14: 9 donors lose recognition, **5 keep it** |
| M20 | `detail_full.host.C_loss` / `ctrl.C_loss`; `detail_bulk.host` / `ctrl` | 0.202 / 0.067; 0.260 / 0.077 |

**Coverage.** M17 tests four repair families (`full`, `meanD`, `cs0`, `abc05`). The other repair variants and doses of
M1–M16 are NOT_TESTED for false veto.

**Post-run analysis correction.** M17 v1 (frozen) failed its gate on a lookup bug (`anchor_of` is only in the manifest).
v1.1 was written after the run, changes only that lookup, and is the analysis of record (`M17_RESULT_R1.md`).

**Falsifier.** For M20, the round-self swap removes recognition no more often than donor-to-donor controls.

## M-E — Missed appended-conflict and benign states are linearly separable above the token surface, by the appended item's form (two kev-family checkpoints, same scenes; M23 ARM_SHORTCUT)

| Stage | Key | kev-4B (M18, ebd82ff → c56729c) | SecJev (M22, 40c0f59 → 1e897c7) |
|---|---|---|---|
| V1 | `verdicts.V1_encoded`, `V1_surface` | ENCODED_AT_L11, ABOVE_SURFACE | ENCODED_AT_L11, ABOVE_SURFACE |
| span write | `metrics["PROBE:SPAN_ATTN11"].AUROC`; `ci95_group_bootstrap.AUROC_span` | 0.993 [0.985, 0.998] | 0.964 [0.924, 0.989] |
| surface | `metrics["PROBE:SPAN_RESID_emb"].AUROC` | 0.816 | 0.805 |
| decision state | `metrics["PROBE:LAST_RESID_L31"]` / `["PROBE:LAST_RESID_L23"]` AUROC | 0.990 | 0.978 |
| native margins | `metrics.NATIVE_A` / `NATIVE_M` AUROC | 0.64 / 0.73 | 0.55 / 0.50 |
| V2, V3 | `verdicts.V2_location`, `V3_useful` | GENERIC_MATCHES, MONITOR_USEFUL | GENERIC_MATCHES, MONITOR_USEFUL |
| natural false veto | `counts.natural_false_veto_by_arm` | ROUND 7, OUTSIDER 6 | old 11, SA 11, ROUND 10, OUTSIDER 7 |

**Deviation.** M22's analysis verdict lines were made None-safe before the prereg commit (blob 5225412d) after the
fake-data dry run crashed. Rules and thresholds are unchanged.

**Confound (audit `02a2b73` P0-1; historical V5 text below, superseded by the M23 paragraph).** Every positive is a `new` row and every negative a non-`new` row, so arm, Gold,
message form and role vary together. M-E therefore does **not** claim that conflict validity is encoded.

**Decided by M23 (prereg `5bd58f6`, result `543b259`)**, as a validity-specificity verdict. No detector meets the VALIDITY_TRACKED gate, but this does not show that validity is never represented: SecJev's `SPAN_ATTN11` has conflict > twin in 94.5% of missed scenes (AUROC_pair 0.698). The frozen probes, refit exactly, flag the same-span
no-conflict twins as often as the conflicts. Preregistered verdict ARM_SHORTCUT for every detector on both models
(`numbers_mech_v3.json` → `M23.models.*.verdicts`). The separability follows the appended item's form.

**Constructibility (historical).** G2.3 (`research/rounds/A461_MON_G23_CONTEXT_COUNTERFACTUAL_CPU/G23_RESULT_V1.md`, commit
`e2b407d`): `PARTNER_ROUND` twins keep the appended span byte-identical and change one partner-round token, moving Gold
off `reject_conflict`. They are constructible in 124/124 scenes and 17/17 groups (`numbers_mech_v2.json` → `G23`). Not
run on GPU.

**Falsifier.** The span probe does not beat the token-embedding probe (V1_surface fails). For a validity reading: the
frozen probes score the G2.3 twins like `new` rows.

## M-F — The tested decision-token steering produced no selective repair (kev-4B)

| Stage | Key | Value |
|---|---|---|
| M19 (50227eb → f2256e8) | `verdicts.L19` / `L31` | READOUT_GAIN_INERT / READOUT_GAIN_INERT |
| M21 (bc61ce9 → 0a4ce0a) | `verdicts.L19` / `L31` | NOT_READABLE / NOT_READABLE |
| M21 | `measures.push_L31_b20.REPAIR`; `measures.gain_L31_g32.REPAIR` / `FV` | 0; 0.012 / 0.035 |
| M21 | `readout_geometry.median_cos_probe_vs_head_gradient.MISSED` | −0.062 |

**Scope.** These are decision-token interventions at layers 19 and 31. The head also reads the option tokens. A random
push of the same size is about as inert, so the null is not specific to the conflict direction. γ32 at L31 changed 20 of
620 actions (`numbers_mech_v2.json` → `M21.action_changes`): 1 repair, 17 new false vetoes, 1 lost recognition and 1
other change. M-F does not claim that the decision circuit ignores conflict information. "Represented but not used"
is a candidate only.

**Falsifier.** A push or gain along the conflict direction repairs at least half the missed rows.

## Mechanism ledger

Per-stage physical forwards are in `numbers_mech_v1.json` → `forwards`. That gives 86,758 in total: kev-4B 86,138
(M1–M21) and SecJev 620 (M22). Every stage had 0 denied pre-hook calls and a single ledger attempt; all were run under
the standing GPU authorization.

## M-G — Native three-action errors (S2 safety endpoint; added in V5)

`numbers_mech_v2.json` → `safety3`, computed from the M18 / M22 raw logits (argmax of `certificate_action` against
`gold_action`). This is manuscript Table S1.

| Model | New: missed (accept / wait) | Benign false vetoes (of 496) | Accept/wait swaps (of 496) |
|---|---|---|---|
| kev-4B | 84 (83 / 1) | 13: ROUND 7, OUTSIDER 6 | 34 |
| SecJev | 110 (69 / 41) | 39: old 11, SA 11, ROUND 10, OUTSIDER 7 | 104 |

A deterministic rule engine makes none of these errors on this simulator. These are not deployment rates.

## M-H — On a matched same-span counterfactual, both scorers' conflict decisions are mostly not robust to the appended vote's validity (M23; added in V6, narrowed in V7)

Source: `research/rounds/A461_MON_M23_TWIN_PROBE_GPU/` (prereg `5bd58f6`, result `543b259`); `numbers_mech_v3.json` →
`M23`. The twins keep the appended vote byte-identical and move only the author's earlier candidate vote to another round,
so Gold is accept / wait (G2.3; 124/124 scenes, 17/17 groups).

| | kev-4B | SecJev-0.8B |
|---|---|---|
| scenes where `new` is rejected | 40 | 14 |
| twin also rejected there | **37** | **14** |
| twin conflict readout C > 0 there (`new`: same count) | 36 (36) | 14 (14) |
| median twin − new conflict margin, missed scenes | +0.297 | +0.575 |
| twin false veto, all 124 | **45** | **15** |
| probe verdicts (all detectors) | ARM_SHORTCUT | ARM_SHORTCUT |

**Additional reporting (V7).**

| | kev-4B | SecJev-0.8B |
|---|---|---|
| Twin reject / accept / wait (Gold: accept 102 / wait 22) | 45 / 72 / 7 | 15 / 56 / 53 |
| Source groups (of 17) with a twin false veto | 14 | 9 |
| Twin accept ↔ wait swaps | 3 | 34 |
| Twin rejected where `new` was missed | 8 of 84 | 1 of 110 |
| Quorum-change twins (Gold accept → wait) | 4 | 4 |

Edit families: PARTNER_ROUND was run. PARTNER_BLOCK (constructible 124/124) and PARTNER_AUTHOR (23/124) were not run.

**What M-H does not claim.** That the scorers never use the partner relation internally. M-H is behaviour on one
matched edit.

**Falsifier.** In the scenes where they reject the conflict, the scorers reject the twins far less often than the
conflicts.

**Scope.** One twin family (partner round). A partner-author family was constructible in only 23 scenes and was not run.
Same 124 scenes; two kev-family checkpoints.
