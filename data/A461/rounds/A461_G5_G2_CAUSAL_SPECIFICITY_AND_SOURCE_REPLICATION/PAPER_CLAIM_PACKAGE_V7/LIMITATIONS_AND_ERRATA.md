# Limitations, missed criteria and errata (V7)

## Scope ceilings

- **Models.** Two kev-family checkpoints:
  - SecJev-0.8B (24 layers);
  - kev-4B (Qwen3.5-4B-Base with a kev adapter, 32 layers).

  They share the tokenizer, the typed row format and the kev training recipe, so the replication is within the kev
  family, not across architectures or vendors.
- **Data.** One simulator family (twins_streamlet DEV) and constructed, rule-valid edits. There is no observed evidence
  stream.
- **SecJev donors.** There are 4 strict donors, from 3 source groups (run-140, run-212 ×2, run-338). All three groups were used
  by earlier A461 rounds for other scenes; groups that have never been used do not exist. The roster is exhausted:
  171 of the 171 W31/W34 candidates were screened.
- **kev-4B donors.** kev-4B has 44 strict donors from 14 groups. K-B used 6 donors and K-C used 14 (one per group),
  all disjoint.
- **SecJev hosts.** Hosts come from 10 further groups. The Stage-B hosts sit near M = −11, so no restoration can flip them.
- **Statistics.** Cells share donors and hosts, so every count is descriptive. No p-values or confidence intervals are
  claimed for the G2 causal counts.
- **Layers.**
  - SecJev: patching covered layers 7 and 11–15, and captures cover all 24 layers.
  - kev-4B: patching covered full-attention layers 3–27 (K-B) and layer 11 (K-C).
- **kev-4B margins.**
  - Hosts sit close to threshold: the artifact temperature is 2.41, and most |M| < 2.5.
  - Flips are therefore cheap. Even the dose arm flips C in 12/104 cells and R in 5/104, though never jointly.
  - Specificity is carried by the paired margin contrasts (K-C1, K-C2).
- **Not tested.** Key-only or component-level mediation is not tested.
- **Semantic controls compare source categories (V3, audit `d9d3338`).** The Stage-F and K-C4 sources differ in
  recognition, source content, context and source–host relation at once. Recognition is not isolated as the factor
  that decides repair.
- **Scene-level hold-out.** kev-4B's K-B scan and K-C replication use disjoint scenes, but the six scan-donor groups
  reappear among the 14 K-C donor groups.
- **Cause of the model differences not isolated.** SecJev and kev-4B differ in size, training objective, data and
  recognition rate. Their differences in miss rate and in donor concentration are observed, with the cause not
  isolated.
- **Non-target readout movement (exploratory).**
  - In K-C, `evidence_level` changes in 24/104 cross-group cells, all of them among the joint repairs.
  - Whether these changes are gold-correct has not been checked.
  - They are therefore reported neither as a positive result nor as damage.
- **Witness-binding controls not tested.** Reversed witness, same-class-but-wrong-witness, and matched
  author/round/block controls were not run. No rule-binding mechanism is claimed.
- **Ceiling on the task itself.** A deterministic rule engine solves this task exactly.

## Donor concentration (exploratory analysis, not preregistered)

| Analysis | All donors | Without run-140 donor (90dbf6) |
|---|---|---|
| Stage-E decision repair, layer 11, action row | 10/32 specific (run-140 donor: 6) | 4/24, 2 donor groups, 2 host groups |
| Stage-D readout repair, layer 11 | 10/32 specific (run-140 donor: 7) | 3/24, 2 donor groups, 2 host groups |
| Stage-C dose specificity, layer 11 | 16/16 | 12/12 (and 12/12 for every other removal) |
| Stage-E joint C∩R repair, layer 11, all rows | 8/32 (run-140 donor: 7) | 1/24 |
| kev-4B K-C specific joint repair, layer 11 | 53/104 from 14 groups (top group 13.2%) | 46–52 for every single-group removal |

- **Distance to threshold.** The repaired cells do not differ in host distance from the threshold. The median baseline
  A is −1.60 for repaired cells and −1.69 for unrepaired cells.
- **Robustness on SecJev.** The specificity claim (C2) is robust to dropping any donor. The repair claims (C5, C6, C7)
  depend strongly on one donor.
- **Robustness on kev-4B.** The cross-group generality of repair is claimed from kev-4B (K3), where no group dominates.

## Preregistered outcomes that did not support the hypothesis

These are reported unchanged.

- **Stage B.** The suppression rule failed, giving the verdict ONE_DIRECTION_ONLY_RESTORATION.
- **Stage C, H3.** The projection AUC at layer 11 was 0.84, short of the 0.9 threshold. The threshold is not met.
- **Stage D.** The verdict was NO_BEHAVIOURAL_CORRECTION. See the erratum below.
- **Stage F, H-F1 (content beyond decision class).** Not met.
  - The rule compared TTT new spans with TTT SA spans. Neither repairs (0/72 each), so the contrast cannot reach its
    threshold.
  - The rule returned its fallback label, CONSISTENT_WITH_POSITIVE_CLASS_REPRESENTATION. That label is not evidence for
    a class-prototype account.
  - The class-matched comparison against donor spans is exploratory.
- **Stage F, H-F3 (source diversity from TTT scenes).** Not met (0 groups).
- **kev-4B K-B.** The window rule (largest median main − dose gap) chose layer 11. Layer 15 has a smaller gap (0.54 vs
  0.64) but a higher dose share (96% vs 87%). K-C was run only at the rule's layer.

## Errata and process corrections (this line)

### Stage D action criterion (`01f46ef`, `ERRATUM_STAGE_D_ACTION_CRITERION.md`)

- **What happened.** Stage B–D patches overwrote only the conflict row. In kev row form each question is its own causal
  row, so the action output could not change. The verdict NO_BEHAVIOURAL_CORRECTION is therefore uninformative about
  the action pathway.
- **Correction.** Stage E was redesigned with per-row patching before it ran.
- **Same artefact in earlier stages.** The descriptive "action changes = 0" reported in Stages B and C has the same
  cause.

### Runner engineering reviews (pre-GPU)

Independent reviews rejected three successive runner versions before any G2 forward pass:

| Review | Problems found |
|---|---|
| `3c4721d` | Replay rows were missing fields; there was no per-batch cap |
| `277fdb7` | The GPU plan was overridable; there was no durable quota ledger |
| `0c676ab` | Cap and reservation were not enforced at the LM hook; manifest bijection; fsync |

All of these were fixed in runner V4 (`ee1e021`), which every later stage imports.

### Self-test catches

- Stage B: a row-construction KeyError after a successful forward.
- Stage E: raw rows were missing their scope labels, and a test message printed constants instead of counts.

All were fixed before the GPU runs.

### Measurement slips in the authors' own reporting, corrected before archiving

- A diagnostic merged two seeds onto one dictionary key.
- A misread printout ordering of donor action margins.
- Neither affected archived results.

### Errors in the revision (v7/v8), caught before archiving

- **Unverified claim, removed.** A draft sentence attributed repairs to host distance from threshold. The extracted
  medians (−1.60 vs −1.69) do not support it.
- **Wrong union.** The host-group union was miscounted, and is corrected to 10.
- **Wrong review count.** The count of runner reviews is corrected to three.
- **Stale counts.** Stale stage counts ("eleven", "ten") are corrected to nine G2 stages and fourteen GPU stages.
- **Hard-coded numbers.** These were replaced by `numbers_v8.json` values.
- **Overstated wording.** "exactly" and "no longer consults" were narrowed.

### Self-test catches in Stage F and the kev-4B runners (all before their GPU runs)

- Raw rows were missing the scope, rows, source_kind and cross_group fields.
- A fake admission listed the wrong batch count.
- A seed KeyError occurred for identity rows.
- The Stage-F analysis asserted something that only held for the real model. It was replaced by a reported check.

### Errors found by audit `d9d3338` and corrected in v9

- **The recognition inference was overstated.** The §4.10 title, the contributions, §5 and the NOVELTY delta said
  recognition "not content" decides repair.
- **Stale single-checkpoint text.** "One 0.8B checkpoint" survived in §5 and §6.
- **Causal attributions without isolation.** The miss-rate difference and the donor concentration were attributed to
  "the SecJev specialist".
- **The replication was implied to be independent of source group.**

All are corrected; see `AUDIT_RESPONSE.md`.

### Governance

- **L2 review retired.** The per-runner L2 review was retired by the user's policy V2 (`e4727a4`, A461 amendment
  `b7183ff`). No historical review is presented as PASS.
- **Standing GPU authorization.** From 2026-10-27, the user's standing GPU authorization
  (`GOVERNANCE_AMENDMENT_20261027_STANDING_GPU_AUTHORIZATION.md`) replaced per-stage approval. K-C is the only stage
  run under it.
- **Execution safeguards unchanged.** These all stayed in place for K-C:
  - freeze before run;
  - CPU self-test;
  - fixed budget with batches ≤ 128;
  - durable ledger;
  - pins;
  - bitwise replays.

## Mechanism route M1–M22 (added in V4)

### Scope ceilings
- **One model for the interventions.** M1–M21 are on kev-4B only. SecJev-0.8B replicates only the decodability and
  monitor stage (M22), on the same 124 scenes. No independent scene distribution is tested; A612 asks for one.
- **Hosts and donors.** Tier A rests on 14 donors × 8 hosts. Pooled arms (M6–M16) repair only 3 of 8 hosts; host
  2a4f596d is never repaired by any arm, and 1c7158b6 essentially never. Tier C (M12–M16) is host-specific and is not
  used for claims.
- **Necessity is partial (M20).** The round-self swap removes recognition in 9/14 donors. A failing host's write removes
  it in only 20–26% of cells, and the strongest donors survive every swap. Other routes to recognition are not
  identified.
- **The readout tests reach only the decision token** at layers 19 and 31 (M19, M21). The head also reads the option
  tokens. M21's random 20% push is about as inert as the conflict push, so "not read" is a statement about this token and
  dose.
- **Decodability is not use.** M18 and M22 use supervised probes trained on rule labels. The present-but-unused account
  is decodability on two scorers plus kev-4B decision-token interventions, not an identified circuit.
- **Monitor.** It needs rule-labelled data, and a deterministic rule engine solves the task exactly. At FV1 its false
  positives fall in 2/17 (kev-4B) and 4/17 (SecJev) source groups; the one-sided 95% bound on the group rate is
  32.6% / 46.1%. It is a diagnostic, not a defence, and its location advantage did not survive (GENERIC_MATCHES on both).
- **Repairs veto benign scenes (M17).** The own-donor patch rejects 36/104 duplicate and 43/104 wrong-round votes. No
  repair is presented as a safety improvement.
- **Captures.** The M1–M22 capture tensors stay on the server, with hashes in each stage's `SHA256SUMS`. They are not
  in a public release. Releasing them is outward-facing and needs the user's go-ahead (`CAPTURES.md`).

### Preregistered criteria that failed or sat on an edge
| Stage | Criterion | Outcome |
|---|---|---|
| M2 | Formation layer L_f = 11 | 2/14 splits move it to 8 (NEITHER_ALONE there) |
| M3 | Sparse writer | Only head 10 is in H\* by rule; heads 8 / 9 / 14 miss by 0.5–1.5 cells and join in 8/14 splits |
| M4 | Size vs content of the bulk read | NEC tracks size; resolved by M5's matched size |
| M6 | Low rank ≤ 64 | NOT_LOWRANK on the raw basis; M7 shows this is partly size, mostly basis |
| M7 | Δ-basis low rank, mean difference, contrast alone | All fail; MEANDIFF was nearly forced by design |
| M8 / M11 / M12 | s = ½ sufficiency | SPEC at frac exactly 0.75; 2/14 splits move the threshold to 1 |
| M9 / M10 / M11 | Split null (1, 5 and 10 random frames) | **Fails** each time → the subspace verdict stays UNRESOLVED |
| M9 | Gain shape | GAIN_MIXED |
| M13 | Tilt at an off-ceiling size | The preregistered size was at floor or ceiling on every host |
| M14 | AB threshold | MIXED; the tilt opposes by S on 264c458d and supports on 4bcbaf15 |
| M15 | Q1 split | GAIN_LOC_ONLY in only 7/14 splits |
| M16 | Linearity of the middle shift | **W_LINEAR_FAILS** |
| M20 | Necessity (NEC) | Only NEC_PARTIAL for full and bulk (C_loss difference 0.13 / 0.18 < 0.40) |
| M19 / M21 | Readout drivable along the conflict direction | INERT / NOT_READABLE at L19 and L31 |
| M18 / M22 | Location advantage of the mechanism-located monitor | GENERIC_MATCHES on both scorers |

### Errata and deviations
- **M17 analysis v1 → v1.1.** The frozen v1 looked up `anchor_of` in the raw rows, but the runner copies it only into the
  manifest. The gate failed, and every verdict read INCONSISTENT. v1.1 changes only that lookup; it is the analysis of
  record, and the deviation is documented in `M17_RESULT_R1.md`.
- **M22 analysis, before the prereg commit.** The WIP analysis crashed on the fake-data dry run, where the fake head
  rejects every row and no MISSED/BENIGN rows exist. The verdict lines were made None-safe, with no rule change, and the
  fix was documented in the prereg before any GPU forward.
- **Self-test failures caught before GPU runs.** M16 (a test bug), M17 (fake-model nondeterminism), M19 (fake width) and
  M22 (fake head count). Each was fixed, rerun and kept as `*_FAILED_*` in its stage folder.
- **Revised candidate explanation.** V3 called an encoding failure the leading candidate (C4). M18 / M22 withdraw it
  (see `CLAIMS_EVIDENCE_MAP.md` C4 and M-E).

## V5 additions (audit `02a2b73`)
- **Arm confound in M18 / M22 (P0-1).** The probe labels coincide with the arm. The separability is not evidence that
  conflict validity is encoded. The same-span twin test (G2.3) is constructible in all scenes but has not been run.
- **Readout null lacks direction specificity (P0-2).** A random push of equal size is about as inert. Only the decision
  token at two layers was steered. γ32 at L31 changed 20 actions, including 17 new false vetoes.
- **Same-family re-test (P1-2).** M22 uses a second kev-family checkpoint on the same 124 scenes and 17 groups. It is
  not an independent environment, architecture or mechanism replication.
- **Three-action errors (P1-3).** Errors include acceptances without sufficient evidence (wait→accept) and, for SecJev,
  false vetoes on every benign arm. See Table S1 and claim M-G.
- **Novelty (P1-4).** The audit sets `NOVELTY_NOT_YET_PASS`. The mechanism stages are a task-specific instantiation of
  known phenomenon classes.
- **Re-computation (P1-5).** The 22/22 recompute re-runs the authors' scripts. The pinned `head.pt` (needed by M19 / M21)
  is a model asset and is not released.
- **False-veto coverage (P1-6).** M17 covers four repair families. The rest are NOT_TESTED.
- **M20 (P2-1).** 5 of 14 donors keep recognition under the round-self swap. `M20_RESULT_R1.md` lists four of them as
  examples.

## V6 additions (M23 and the reframe)
- **"Recognized" is a readout, not a check.** M23 shows that both scorers' positive conflict readout does not depend on
  the double vote. The G2 claims C1–C8 and K1–K3 stay as interventional statements about readout-positive span states.
  Their "recognition" wording is read as readout-positive, and the paper says so in its terminology paragraph (§3.4).
- **Withdrawn candidate accounts.**
  - "Missing encoding" (v9) was never identified.
  - "Represented but not used" (v10–v11) rested on probe separability, which M23 shows is form-driven.
  - No mechanism of the miss is claimed.
- **M23 scope.**
  - One twin family (partner round).
  - The same 124 scenes and the same two kev-family checkpoints.
  - The probes were refit on the parent data, not trained with twins as negatives. Whether any internal state separates
    validity from form is untested. SecJev's L11 span write is partly context-sensitive (new > twin in 95% of missed
    scenes), and this is reported, not preregistered.
- **Title and framing changed after the result.** The v12 title and abstract were rewritten after M23. M23's own
  interpretation was fixed in its prereg before the run. The reframe of the G2 sections is an editorial consequence,
  not a preregistered analysis.

## V7 additions (audit `8dd4528`)
- **M23 is behavioural, on one edit family.** It does not identify the scorers' internal computation. PARTNER_BLOCK
  (constructible 124) and PARTNER_AUTHOR (constructible 23) were not run. In 4 twins the edit also removes quorum
  (Gold accept → wait).
- **ARM_SHORTCUT is a threshold verdict.** It does not show that validity is never represented. SecJev's L11 span write
  is partly context-sensitive.
- **The transplanted G2 state is not identified with a shortcut judgment.** No within-scene conflict-vs-twin state swap
  was run.
- **Units.** 124 scenes in 17 source groups, from one simulator. The twin false vetoes span 14/17 (kev-4B) and 9/17
  (SecJev) groups. The conditional denominators (40, 14) are small and selected by the scorers' own behaviour.
- **NOT_INDEPENDENTLY_VERIFIED (per audit `8dd4528`):**
  - the M23 server-side captures;
  - the pinned kev-4B `head.pt`, which is not released;
  - tensor-level probe AUROCs and bootstrap CIs, which the audit did not recompute;
  - the rendered DOCX/PDF layout.

  The 22/22 M1–M22 recompute used the authors' own scripts.
