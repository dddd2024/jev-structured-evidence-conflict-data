# Response to paper audit `02a2b73` (V5 revision; V6 update at the end) (V4, `PAPER_AUDIT_REVISE_REQUIRED`, P0×2 / P1×6 / P2×2)

The audit asked for a one-time revision. It does not require a GPU run, and it does not re-trigger an audit on its own.
V5 is that revision:

- **Manuscript v11** (`v11_edits.py` applied to V4's `generate_v10.js`).
- **Numbers from `numbers_mech_v2.json`.**
- **A CPU constructibility check for P0-1 (G2.3).**
- **The M1–M22 capture release**, approved by the user on 2026-11-01.

No GPU forward was run, and no frozen data, Gold or result changed. Where we accept a point, the text now states the
narrower claim the audit allows.

| Item | Accepted? | Change |
|---|---|---|
| **P0-1** M18/M22 labels collinear with arm | Yes | **Text.** Abstract, contributions, §4.15, §4.16, the limitations and `CLAIMS_EVIDENCE_MAP` M-E now say only "missed appended-conflict and benign states are linearly separable above the token surface". They state the confound explicitly. The §4.15 heading no longer says "present but not used". **New CPU check G2.3** (`research/rounds/A461_MON_G23_CONTEXT_COUNTERFACTUAL_CPU/`, commit `e2b407d`): a same-span, Gold-varying twin is constructible in **124/124 scenes and 17/17 source groups**. The appended vote is kept byte-identical; only the author's earlier partner vote changes round (exactly one token, before the span); Gold moves from `reject_conflict` to accept/wait. It answers the audit's request at the constructibility level. **The GPU stage that scores the twins with the frozen probes has not been run.** It needs the user's scope decision, and until it runs the narrowed wording stands. |
| **P0-2** M19/M21 null is decision-token only; random push also inert | Yes | M-F now reads "the tested decision-token steering produced no selective repair". §4.15 states the following. γ32 at L31 changed 20 of 620 actions: 1 repair, 17 new false vetoes, 1 lost recognition and 1 other change. A random push of the same size is about as inert, so the null lacks direction specificity. The option tokens are not reached. "Represented but not used" is held only as a candidate, replacing "missing encoding"; neither is identified. |
| **P1-1** L11 claims local and conditional | Yes | §4.13 heading and text say "local, conditional", for these 14 donors × 8 hosts. Only head 10 meets the sparse-writer rule; heads 8 / 9 / 14 are at threshold, and no unique writer circuit is claimed (also Table M1). The formation-layer edge (2/14) is kept. M20 is "partly necessary in 9 of 14", with **5 survivors** named, and the fields are not separated. |
| **P1-2** M22 is a same-family re-test | Yes | §4.16 heading and text: "a second kev-family checkpoint, same 124 scenes and 17 groups; a same-family re-test, not an independent replication, with the same arm confound". |
| **P1-3** Three-action safety, not one reject number | Yes | **New §4.17 and Table S1.** It gives, per model and arm, missed conflicts, false vetoes with group counts, accept/wait swaps and correct counts, all computed from the raw logits by `extract_numbers_mech_v2.py`. Examples: kev-4B 83 accept + 1 wait on new, 13/496 benign false vetoes, 34 accept/wait swaps; SecJev 69 + 41 on new, 39/496 false vetoes, 104 swaps. The rule baseline and the non-deployment status are stated. |
| **P1-4** Novelty is an instantiation | Yes | Limitations and `NOVELTY.md`: the mechanism stages instantiate known phenomenon classes in a security-typed scorer with rule gold. `NOVELTY.md` has a strict competition matrix including Ma et al. (EMNLP 2026), and the status is set to the audit's `NOVELTY_NOT_YET_PASS`. |
| **P1-5** 22/22 is not independent; M17 post-run fix | Yes | §4.12, `README`, `REANALYSIS_CHECK`: "deterministic re-computation with our own scripts, not an independent replication". M17 v1.1 is marked "post-run analysis correction" in §4.14 and the limitations, distinct from M22's pre-run fix. The captures are now released (tag `a461-mech-captures-m1-m22-v1`), so an independent verifier no longer needs server access. The pinned `head.pt` is still not released (model asset). |
| **P1-6** M17 covers four families | Yes | Contributions, §4.14, `README`, `CLAIMS` M-D: "four representative repair families"; the other M1–M16 variants and doses are NOT_TESTED. |
| **P2-1** M20 survivors 5, not 4 | Yes | §4.14 and `CLAIMS` M-D say 5 of 14 (`numbers_mech_v2.json` → `M20.round_self.survivors`). M20_RESULT_R1 listed four examples; the list is now labelled as examples. |
| **P2-2** "steering moves no decision" | Yes | Removed from the abstract and §4.15; replaced by the action-change counts above. |
| Checklist 6: DOCX/PDF check | Done | We checked v11's rendered text for unresolved values (none) and checked the new pages and Table S1 visually. Independent verification of the tensors is left to the auditor; the captures are now downloadable. |
| Checklist 7: constructibility before any stronger claim | Done | G2.3 (above). |

**What remains unchanged.** The V3 G2 claims and their numbers (`numbers_v8.json`); every frozen verdict of M1–M22; the
evidence-level ceiling (S2 + diagnostic, no defence).

## V6 update (M23 run; full reframe)

**P0-1 is now decided by experiment, not only narrowed.**
- With the user's go-ahead, M23 (prereg `5bd58f6`) scored the G2.3 same-span twins with the refit M18 / M22 probes.
- The verdict is ARM_SHORTCUT for every detector on both models: the separability follows the appended item's form.

**The scorers themselves also judge by form.**
- They reject the twins in 37 of 40 (kev-4B) and 14 of 14 (SecJev) scenes where they reject the conflict.
- They false-veto 45/124 and 15/124 legitimate twins.

**What v12 changes.**
- The paper is reframed around this result: new title and abstract, contributions, a terminology paragraph defining
  "recognized" as readout-positive, a new §4.18 with Table T1, a revised discussion, and the claim map's new M-H.
- "Represented but not used" is withdrawn.
- The G2 transplant results stand as interventions on the state behind a form-driven readout.
- No new audit had been triggered when this section was written. (Status as of 2026-11-01: V6 was then audited, in `8dd4528`; see the V7 response below.)

# Response to paper audit `8dd4528` (V6, `PAPER_AUDIT_REVISE_REQUIRED`, P0×2 / P1×5 / P2×2): package V7, manuscript v13

This revision is text only, as the user chose ("Text-only revision"), and no GPU forward was run. The audit
independently recounted the M23 raw outputs and confirmed them. Every item below is about scope, wording or reporting.

| Item | Accepted? | Change in v13 / V7 |
|---|---|---|
| **P0-1** "does not check / ignores / never depends" overreaches | Yes | **Title:** *Missed When Valid, Vetoed When Not: Two Typed Language-Model Scorers' Conflict Decisions Are Not Robust to the Validity of an Appended Vote*. **Abstract:** "They do not" becomes "on a matched counterfactual, their decisions mostly do not follow it". "Form, not validity" becomes "consistent with a form cue … not robust to validity; behavior on one matched counterfactual, not an identified internal mechanism". **§4.18 and §5:** each absolute statement is replaced by a statement of non-robustness on one edit family, with the minority of differing scenes counted (kev-4B 3 and 8, SecJev 1). A scan of v13 for the listed phrases finds 0 occurrences. |
| **P0-2** ARM_SHORTCUT ≠ "validity never represented" | Yes | "No probe separates" becomes "no probe meets the preregistered validity-tracking gate". The abstract, contributions and §4.18 state SecJev's L11 span-write partial context sensitivity: conflict > twin in 94.5% of missed scenes, AUROC_pair 0.698. §4.18 says that ARM_SHORTCUT is a verdict about validity specificity at the operating threshold, not about the absence of relation information. §4.15 says the twin test does not establish the converse. |
| **P1-1** The transplanted state is not shown to be a shortcut judgment | Yes | §4.18 scope and §5: the transplanted state is the state of readout-positive scenes. We do not identify it with a shortcut judgment, because no experiment swapped the conflict's and the twin's states. "Carry that judgment" is removed from the title. |
| **P1-2** Novelty: new close prior work | Yes | Related work and references [27]–[30] add Yan et al. (ICML 2026), Buzato et al. (EMNLP 2026), Feng et al. (C2PO, Findings ACL 2026) and TrustJev (arXiv 2610.34826), as identified by the audit, and state our addition against them. `NOVELTY.md` adds a matrix with the columns prior question / counterfactual / causal isolation / security endpoint / what A461 adds. The status stays `NOVELTY_NOT_YET_PASS`. |
| **P1-3** Units and denominators | Yes | §4.18: false vetoes fall in **14/17** (kev-4B) and **9/17** (SecJev) source groups. The 40 and 14 conditional denominators are named as such. The counts are described as descriptive, not error rates. |
| **P1-4** The twins' full three-action outcome | Yes | §4.18 and claim M-H: reject / accept / wait is **45 / 72 / 7** (kev-4B) and **15 / 56 / 53** (SecJev) against Gold accept 102 / wait 22. SecJev swaps accept and wait in 34 twins. All values come from `numbers_mech_v4.json` → `M23.models.*.twin_confusion`. |
| **P1-5** Reproducibility ceiling | Yes | Limitations (v13 §6) and `LIMITATIONS_AND_ERRATA.md` state that the M23 captures are server-side, `head.pt` is not released, the 22/22 recompute uses our own scripts, and the PDF layout has not been independently checked. These are marked NOT_INDEPENDENTLY_VERIFIED. |
| **P2-1** Edit families; quorum changes | Yes | §4.18 scope: PARTNER_ROUND was run on 124 scenes; PARTNER_BLOCK (constructible 124) and PARTNER_AUTHOR (constructible 23) were **not run**. The 4 quorum-change twins (Gold accept → wait) are named; their native actions are reported in `numbers_mech_v4.json`. |
| **P2-2** Stale snapshot lines | Yes | The V6 "No new audit has been triggered" line is dated and points here. The historical M-E text in the claim map is labelled historical. |

No preregistered experiment, raw datum, Gold label or verdict changed. The V3 scoped PASS and every historical file are
kept.
