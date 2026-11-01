# Limitations, missed criteria and errata

## Scope ceilings

- **Model and data.** One checkpoint (SecJev-0.8B), one simulator family (twins_streamlet DEV) and constructed,
  rule-valid edits. There is no cross-model replication and no observed evidence stream.
- **Donors.** There are 4 strict donors, from 3 source groups (run-140, run-212 ×2, run-338). All three groups were used
  by earlier A461 rounds for other scenes; groups that have never been used do not exist. The roster is exhausted:
  171 of the 171 W31/W34 candidates were screened.
- **Hosts.** Hosts come from 10 further groups. The Stage-B hosts sit near M = −11, so no restoration can flip them.
- **Statistics.** Cells share donors and hosts, so every count is descriptive. No p-values or confidence intervals are
  claimed for the G2 causal counts.
- **Layers.** Patching covered layers 7 and 11–15. Captures cover all 24 layers.
- **Not tested.** Key-only or component-level mediation is not tested.
- **Ceiling on the task itself.** A deterministic rule engine solves this task exactly.

## Donor concentration (exploratory analysis, not preregistered)

| Analysis | All donors | Without run-140 donor (90dbf6) |
|---|---|---|
| Stage-E decision repair, layer 11, action row | 10/32 specific (run-140 donor: 6) | 4/24, 2 donor groups, 2 host groups |
| Stage-D readout repair, layer 11 | 10/32 specific (run-140 donor: 7) | 3/24, 2 donor groups, 2 host groups |
| Stage-C dose specificity, layer 11 | 16/16 | 12/12 (and 12/12 for every other removal) |

- **Distance to threshold.** The repaired cells do not differ in host distance from the threshold. The median baseline
  A is −1.60 for repaired cells and −1.69 for unrepaired cells.
- **Robustness.** The specificity claim (C2) is robust to dropping any donor. The repair claims (C5, C6) hold across
  groups but depend strongly on one donor.

## Preregistered outcomes that did not support the hypothesis

These are reported unchanged.

- **Stage B.** The suppression rule failed, giving the verdict ONE_DIRECTION_ONLY_RESTORATION.
- **Stage C, H3.** The projection AUC at layer 11 was 0.84, short of the 0.9 threshold. The threshold is not met.
- **Stage D.** The verdict was NO_BEHAVIOURAL_CORRECTION. See the erratum below.

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

### Governance

The per-runner L2 review was retired by the user's policy V2 (`e4727a4`, A461 amendment `b7183ff`). No historical
review is presented as PASS.
