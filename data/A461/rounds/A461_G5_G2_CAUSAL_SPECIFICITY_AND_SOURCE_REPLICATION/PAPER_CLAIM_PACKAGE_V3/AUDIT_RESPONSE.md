# Response to paper audit `d9d3338` (`PAPER_AUDIT_REVISE_REQUIRED`, P0×1 / P1×3) on package V2

**Scope.**
- The audit's verdict is not changed or reinterpreted here.
- No GPU was used, and no numbers changed. Manuscript v9 still reads `numbers_v8.json`.
- The response to the first audit (`64faaee`) stays in `PAPER_CLAIM_PACKAGE_V2/AUDIT_RESPONSE.md`.

All manuscript edits are in `v9_edits.py`. It derives `assemble_v9.py` from `assemble_v8.py`, and every replaced span
is asserted to occur exactly once.

## P0 — "recognition, not content" inference exceeds the controls

**v9 manuscript.**
- **§4.10.** The heading is now "Semantic controls: among the source categories tested, only recognized
  appended-conflict spans repair".
- **§4.10 closing sentences.** They now state:
  - only strictly recognized appended-conflict spans produce specific joint repair;
  - missed appended conflicts, pre-existing-conflict sources and duplicate-vote sources do not;
  - the categories differ in source content, context and source–host relation as well as recognition, so recognition
    is not isolated and content is not shown to be irrelevant.
- **Exploratory class-matched comparison.** It now "suggests, for these hosts" that a class state is "not by itself
  sufficient".
- **Introduction, fifth contribution.** It is rewritten in the same narrowed form.
- **§5 Discussion.** The claim that the evidence favours encoding over a "content- or decision-class-only account" is
  removed. The text now says that a content- or context-based contribution is not excluded.
- **§5 Boundaries and §6 Limitations.** Both now say that the semantic controls compare source categories rather than
  isolating recognition. §6 also notes that the witness-binding controls were not run.

**Package.**
- **`NOVELTY.md`, delta item 2.** It is now "A source-category contrast", explicitly not a single-factor
  identification.
- **`NOVELTY.md`, delta item 1.** It is renamed "Specific sufficiency". "Specific" is defined as beyond token form,
  position and per-position dose, and explicitly not a claim about which content carries the effect. This removes the
  audit's noted contradiction between items 1 and 2.
- **`CLAIMS_EVIDENCE_MAP.md`, C8.** It is restated as source-category dependence. The frozen hypothesis label
  `H_F2_recognition_matters` is kept, with a note that it names the hypothesis.
- **`NOVELTY.md`, "Not claimed".** Two items are added:
  - that recognition rather than content, context or host interaction decides repair;
  - any rule-binding or witness-binding mechanism.

## P1-1 — Stale single-model text and an unsupported causal attribution

**Single-model text, now two kev-family checkpoints.**
- **§5 Boundaries.** It now reads "two kev-family checkpoints (SecJev-0.8B and kev-4B), one constructed simulator
  family". It also disclaims cross-architecture and cross-family generality.
- **§6 Limitations.** It now opens with "Two kev-family checkpoints and one simulator family".
- **Layer coverage.** The sentence on untested layers is scoped to SecJev, since kev-4B was scanned at layers 3–27.

**Causal attributions, now observed differences with the cause not isolated.**
- **§4.11.** "The severe miss rate is therefore specific to the SecJev specialist" now reads: "not shared by kev-4B;
  the two scorers differ in size, training objective and data, so the cause of the difference is not isolated".
- **§5.** "The donor concentration is therefore a property of the SecJev specialist's rare recognitions" now reads:
  "In kev-4B, then, the transplant effect is not tied to one donor. Why SecJev's repairs concentrate in one donor is
  not isolated…".

## P1-2 — Comparison with the closest prior work

**v9 §2.**
- **Table R1** compares Abdelsalam et al. (2026), Chu, Sun & Weng (2026), Lepori et al. (2024; 2026), the
  method-critique papers (Makelov et al. 2023; Zhang & Nanda 2024; Vaidyanathan et al. 2026) and this study. The
  columns are setting and failure, intervention, endpoint, and relation.
- **Text.** It states that activation patching itself is standard.
- **"To our knowledge" sentence.** It is replaced by "Within the works we checked…".

**Package.** The same table opens `NOVELTY.md`.

## P1-3 — Independence of the replication

**Fact checked.** The six K-B scan-donor groups (run-121, -140, -154, -169, -181, -212) are all among the 14 K-C donor
groups. This was checked from the frozen designs.

**v9 changes.**
- **Abstract.** It now says "donor and host scenes disjoint from the scan (source groups overlap)" and "cells share
  hosts, so these are descriptive counts, not rates over independent tasks".
- **Contributions.** They now say "scenes disjoint from the replication (the source groups overlap)".
- **§4.11 and the Table 6 caption.** They now say "held out by scene, not by source group", "source groups
  overlapping", and that the 104 cells share 8 hosts, so counts are descriptive.
- **§5 and §6.** They repeat the scene-level hold-out.

**Package.** `CLAIMS_EVIDENCE_MAP.md` K3 and `NOVELTY.md` item 3 state the same.

## Also corrected while revising

- **Reference [21] and §7.** They now cover Stages A–F, the kev-4B stages and packages V1–V3, instead of A–E and V1.
- **Capture tensors in §7.** They are now described as released assets, not "on the authorized server".
