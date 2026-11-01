# A461 paper-level claim package V3

**Status: `UNVERIFIED_PAPER_READY_CLAIM`. The final paper-level audit was triggered on 2026-10-27 with the user's
approval:**

> 同意：以 PAPER_CLAIM_PACKAGE_V3（2fca4ef）触发最终论文级独立审计。

The package content is that of `2fca4ef`; only this status line changed. This package answers the second paper audit, `d9d3338`
(`PAPER_AUDIT_REVISE_REQUIRED`, P0×1 / P1×3), on package V2. Per policy V2 and the standing-authorization amendment,
the next paper-level audit is triggered only with the user's go-ahead. Until an audit passes, the claim is
`UNVERIFIED_PAPER_READY_CLAIM`.

**What changed from V2.** The revision is text only: no new GPU run, and no number changed. Manuscript v9 still reads
`numbers_v8.json`. Packages V1 and V2 stay unchanged as audited.

## The claim (narrowed from V1, and again in V3)

We test two kev-family typed scorers on structured consensus scenes that have executable rule oracles:

- **SecJev-0.8B**, a security specialist.
- **kev-4B**, a general typed-decision model that was never trained on these scenes.

The edit appends one valid equivocation vote. This lawfully moves the gold label to `reject_conflict`, but both models
usually miss it:

| Model | Scenes where the appended conflict is missed | Strict recognitions |
|---|---|---|
| SecJev-0.8B | 88.7% | 4/124 |
| kev-4B | 63.7% | 44/124, from 14 source groups; 0% false alarms on duplicate votes |

The causal findings are interventional:

1. **Specific sufficiency.** This means beyond token form, position and dose. It is not a claim about which content
   carries the effect.
   - **What was done.** We took the natural layer-11 state of a recognized appended span and transplanted it into a
     scene from another source group.
   - **What it does.** It raises the host's conflict margin by more than three controls: the donor's own duplicate-vote
     span (SA-sham), a permutation, and a random direction with the same per-position size.
   - **Evidence.**
     - SecJev: 16/16 cells.
     - kev-4B: 91.3% of 104 cells beat the dose control, with a majority in 14/14 donor groups; 100% of cells beat the
       SA-sham.
2. **A mid-depth window.**
   - SecJev: sensitivity ends at layer 13.
   - kev-4B: the window is layers 11–15 and is inert from layer 19. The kev-4B window was chosen on scenes disjoint
     from those used in the replication. Source groups overlap, so the hold-out is by scene.
3. **Joint repair.** Implanting a recognized span into a near-threshold host's own missed-conflict span, in every
   question row, flips both the conflict readout and the decision to `reject_conflict` in the same forward pass.

   | Arm | SecJev | kev-4B |
   |---|---|---|
   | Main | 8/32, mostly one donor | 53/104 specific, from 14/14 donor groups (top group 13.2%; leave-one-group-out 46–52) |
   | SA-sham | 0 | 0 |
   | Dose-matched random | 0 | 0 |

4. **Source-category contrast.** Among the source categories tested, only strictly recognized appended-conflict spans
   repair. Spans of appended conflicts that the model itself missed never repair:
   - SecJev: 0/48.
   - kev-4B: 0/40.

   Two further SecJev controls (both exploratory) also give 0/72 each:
   - class-matched duplicate-vote spans from scenes the model reads as conflict-and-reject;
   - conflict spans recognized through a pre-existing conflict.

   The categories differ in content, context and source–host relation as well as recognition. Recognition is
   therefore not isolated as the deciding factor.

**Not claimed.**
- That the failure is *identified* as an encoding failure. We state this as the leading candidate explanation (H3 at
  layer 11 was not met).
- That recognition, rather than source content, context or host interaction, decides repair.
- A rule-binding mechanism. Witness-binding controls were not run.
- Component-level or key-only mediation.
- A C→A mediation chain.
- Generality beyond the kev family and this simulator family.
- Any attack relevance.

## What changed in V3 (audit `d9d3338`)

| Audit item | Change |
|---|---|
| P0 | The recognition inference is narrowed to a source-category contrast in v9 (§4.10 title and text, contributions, §5, §6), in `NOVELTY.md` and in `CLAIMS_EVIDENCE_MAP.md` C8. |
| P1-1 | §5 and §6 now cover two kev-family checkpoints. The differences between the models are stated as observed, with the cause not isolated. |
| P1-2 | Table R1 compares this study with the closest prior work (also at the top of `NOVELTY.md`). |
| P1-3 | The kev-4B hold-out is by scene, not by source group. Counts are over cells that share hosts and are descriptive. |

The details are in [AUDIT_RESPONSE.md](AUDIT_RESPONSE.md).

## What changed from V1 to V2

| | V1 (`e5de4b7`) | V2 |
|---|---|---|
| Models | SecJev-0.8B | + kev-4B (32 layers) |
| G2 GPU stages | 5 (2,191 calls) | 9 (3,628 calls; SecJev 2,487, kev-4B 1,141) |
| Endpoint | readout and action rows reported separately | joint C∩R in the same forward (Table 5, Table 6) |
| Donor concentration | 6/10 decision repairs from one donor | kev-4B: 14/14 groups, top 13.2% |
| Semantic controls | none | Stage F (unrecognized, class-matched, TTT sources) and K-C4 |
| Capture tensors | server only | GitHub Release assets with digests (`CAPTURES.md`) |
| Manuscript | v6 | v8 (20 pages) |

## Contents

| File | Purpose |
|---|---|
| `A461_G2_paper_draft_v9.docx` / `.pdf` | Manuscript v9 (21 pages). |
| [AUDIT_RESPONSE.md](AUDIT_RESPONSE.md) | Point-by-point response to audit `d9d3338`. The response to `64faaee` is in package V2. |
| [CLAIMS_EVIDENCE_MAP.md](CLAIMS_EVIDENCE_MAP.md) | Each claim, mapped to its stage, commit, archived JSON key and value, preregistration status, and falsifier. |
| [NOVELTY.md](NOVELTY.md) | Comparison table and per-work notes on the closest prior work, and the narrowed novelty delta. |
| [LIMITATIONS_AND_ERRATA.md](LIMITATIONS_AND_ERRATA.md) | Ceilings, preregistered criteria that were not met, and errata. |
| [REPRODUCE.md](REPRODUCE.md) | CPU re-analysis of all 9 stages, capture recomputation, manuscript regeneration, GPU re-run. |
| [REANALYSIS_CHECK.md](REANALYSIS_CHECK.md) | Result of re-running every frozen analysis on the archived data. |
| [CAPTURES.md](CAPTURES.md), `CAPTURES_SHA256SUMS` | Release tags and bundle digests for the capture tensors. |
| `verify_captures_v1.py` | CPU checker: tensor SHA, dtype and shape, cross-row identity, raw-row ↔ file bijection. |
| `numbers_v8.json` | The single source of every G2 number in v8 and v9. |
| `extract_numbers_v8.py`, `v7_edits.py`, `v8_edits.py`, `v9_edits.py`, `assemble_v6.py` to `assemble_v9.py`, `generate_v5_input.js`, `generate_v9.js` | Scripts that regenerate the numbers and the manuscript. |
| `SHA256SUMS` | Hashes of every file in this package. |

## Weak points the authors flag for the auditor

1. **SecJev joint repair still depends on one donor.** Leave-one-donor-out leaves 1/24. The cross-group generality of
   the joint repair rests on kev-4B (K-C3), not on SecJev.
2. **kev-4B hosts sit close to threshold.** Margins are small (temperature 2.41), so flips are cheap. K-C1 and K-C2
   are carried by margin contrasts against matched controls. Flip counts are reported but are not the primary evidence.
3. **Three of Stage F's preregistered hypotheses were not all met.**
   - H-F1 (the TTT-new vs TTT-SA contrast) is uninformative: neither arm repairs.
   - H-F3 (diversity of TTT sources) is not met.
   - Only H-F2 is met. Its frozen label is "recognition matters", but it compares source categories.

   The class-matched 0/72 comparison is exploratory.
4. **The kev-4B window rule chose layer 11; layer 15 had a higher dose share.** Layer 15 had 96% vs 87%, but a smaller
   median gap: 0.54 vs 0.64. The rule (largest median gap) was frozen in `66fa292` before the scan ran.
5. **The cross-group split is not a held-out model or data family.** It is two kev-family models on one simulator
   family, with constructed edits. All counts are descriptive; no p-values are claimed.
6. **SecJev's H3 encoding test at layer 11 failed its preregistered threshold** (AUC 0.84 < 0.9).
7. **The kev-4B replication is held out by scene, not by source group.** The six K-B scan-donor groups are among the
   14 K-C donor groups.
8. **Non-target readout movement (exploratory, not in the manuscript).**
   - In K-C, comparing main with SA-sham, the `evidence_level` argmax changes in 24 of the 104 cross-group cells
     (23 times 0→2, once 1→2), all of them among the 53 joint repairs.
   - `quorum` does not change.
   - The independent A520 CPU recheck found this, and it was confirmed from the raw logits. Whether these changes
     match the independent gold has not been checked.
