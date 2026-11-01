# Limitations, missed criteria and errata (V3)

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
