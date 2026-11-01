# Response to paper audit `64faaee` (`PAPER_AUDIT_REVISE_REQUIRED`) on package V1 (`e5de4b7`)

The audit's verdict is not changed or reinterpreted here. Each item below states what was done and where the evidence
is. Whether V2 resolves each item is for the next audit to judge.

## P0-1 — Exclusive "encoding failure" claim

**Action.** The claim is narrowed to an interventional one: the natural span states of recognized appended conflicts
are causally sufficient beyond sham, permutation and dose-matched controls. Encoding failure is now the leading
*candidate* explanation and is not identified. The narrowing runs through:
- the v7/v8 title, abstract, §4.7 (now patch-site sensitivity, not "no longer consults"), §4.8 and §5;
- `CLAIMS_EVIDENCE_MAP.md` C4;
- `NOVELTY.md`.

Two further changes:
- H3 at layer 11 is reported as not met, and layer 12 is no longer substituted for it.
- The Vaidyanathan et al. interaction caveat was added.

**New evidence bearing on the candidate.** Recognition dependence (C8):
- spans of appended conflicts the model missed never repair (SecJev 0/48, H-F2 met; kev-4B 0/40, K-C4 met);
- class-matched spans 0/72 (exploratory);
- TTT conflict spans 0/72.

**Evidence.**
- Stage F: `3c31764` → `6a19924`.
- kev-4B K-C: `3a6173f`/`84bc6f4` → `5ef7a16`.

## P0-2 — Joint C∩A endpoint and donor dominance

**Joint endpoint.**
- SecJev: in-forward joint repair is reported as Table 5, 8/32 main, 0 for the controls. It is labelled exploratory,
  and leave-one-donor-out leaves 1/24.
- kev-4B: the joint endpoint was preregistered as K-C3. Specific joint repair is 53/104 from 14/14 donor groups (top
  group 13.2%). Leave-one-group-out gives 46–52, from ≥ 13 groups. SA-sham and dose give 0 joint.

**Text change.** The paper states that row-wise sufficiency does not establish C→A mediation.

**Evidence.**
- `numbers_v8.json` → `joint` and `KC`.
- `k4b_kc_analysis.json`.
- Table 6.

## P1-1 — External validity

**Action.** A second kev-family scorer was added: kev-4B, a general typed-decision model that was not trained on these
scenes.
- **Inputs.** The frozen inputs carry over unchanged: 372/372 token SHAs match.
- **Screen.** 44/124 strict donors; miss rate 63.7%, against SecJev's 88.7%.
- **Window.** Chosen by a preregistered layer scan on disjoint scenes.
- **Replication.** All four preregistered K-C criteria are met.

**Remaining limit.** Both models are kev family on one simulator family (`LIMITATIONS_AND_ERRATA.md`).

## P1-2 — Missing prior work

**Action.** Chu, Sun & Weng (Findings of EMNLP 2026), Vaidyanathan et al. (arXiv:2606.27510) and Brunello et al. IPE
(BlackboxNLP 2025) were added to the related work and the discussion (v7 onwards) and to `NOVELTY.md`. The novelty
statement is narrowed to "within the works we checked".

## P1-3 — Decision-class prototype confound

**Action.** Stage F (preregistered) transplanted three kinds of span into the same 8 near-threshold hosts:

| Span | Joint repair |
|---|---|
| Class-matched duplicate-vote spans from scenes read as conflict-and-reject (TTT SA) | 0/72 |
| Conflict spans recognized only through a pre-existing conflict (TTT new) | 0/72 |
| Recognized donor spans | 8/32 |

**Outcome as preregistered.**
- H-F1 is uninformative, because neither TTT arm repairs. This is reported as not met, together with its fallback
  label.
- H-F3 is not met.
- The 8/32 vs 0/72 comparison is exploratory.

**Evidence.** `G2_STAGE_F_GPU_R1/STAGE_F_RESULT_NOTE.md`.

**Not done.** The witness-binding controls the audit suggested were not run:
- reversed witness;
- same class but not satisfying the host's witness relation;
- matched author/round/block.

Following the audit's alternative, no rule-binding mechanism is claimed. The claim stays at the level of the
recognized appended-evidence span state. The paper's wording also stops short of "positive-class prototype". The
reason is that class-matched spans do not repair, which argues against a class-only account but does not establish
binding.

## P1-4 — Capture access

**Action.** Executed. Six capture bundles (371 tensors) are published as release assets of `dddd2024/jev`, with their
digests. From the extracted bundles:
- `verify_captures_v1.py` passes on all six;
- the frozen Stage-C analysis reproduces byte for byte.

**Evidence.** `CAPTURES.md` and `REANALYSIS_CHECK.md`.

## P2-1 — `generate_v5.js` vs `generate_v5_input.js`

**Action.** The assemblers accept either name. `generate_v5_input.js` ships in this package, and the regeneration chain
was re-run from a clean copy.

## P2-2 — Stage-C reproduction paths

**Action.** Corrected. `REPRODUCE.md` §2 gives repo-relative paths from the release bundle. The same sequence was run
on the server with the server's directory layout (`REANALYSIS_CHECK.md`).
