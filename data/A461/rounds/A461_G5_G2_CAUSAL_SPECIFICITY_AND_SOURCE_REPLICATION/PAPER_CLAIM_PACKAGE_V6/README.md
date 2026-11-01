# A461 paper-level claim package V6

**Status: `UNVERIFIED_PAPER_READY_CLAIM`. The paper-level audit was triggered on 2026-11-01 with the user's approval.**
Asked "Trigger a paper-level audit on package V6?", the user answered:

> Trigger audit

The package content is that of `fd58722` (SHA256SUMS `2b537ba`). Only this status line changed.
- V6 is the full reframe after the preregistered same-span twin test (M23). It follows the V5 revision for paper audit
  `02a2b73` (`PAPER_AUDIT_REVISE_REQUIRED`).
- Any new audit is triggered only with the user's go-ahead.
- The V3 scoped PASS (`4b27c9b`) covered the G2 transplant claims as v9 worded them. V6 keeps those results but changes
  what they are said to mean (below).

## The claim, reframed (manuscript v12, 29 pages)

**Title.** *Missed When Valid, Vetoed When Not: Two Typed Language-Model Scorers Judge an Appended Equivocation Vote by
Its Form, and Transplanted Span States Carry That Judgment.*

1. **Behaviour (headline; M23, claim M-H).** Neither scorer checks what makes the appended vote a conflict, namely
   that its author has already voted for the candidate block in that round.
   - Keep the appended vote byte-identical and move only the earlier vote, so no conflict exists. Where kev-4B rejects
     the conflict, it rejects the twin in **37/40** scenes; SecJev does so in **14/14**.
   - They false-veto **45/124** and **15/124** legitimate twins.
   - Removing the double vote *raises* the conflict margin in the scenes they miss.
2. **Transplants (G2; C1–C8, K1–K3; unchanged numbers).** The layer-11 appended-span state of a readout-positive
   ("recognized") scene, transplanted across source groups, repairs the readout and decision beyond sham, permutation and
   dose controls (kev-4B 53/104 cells, 14/14 donor groups). Readout-negative spans never repair. What is transplanted is
   the state behind a form-driven readout.
3. **Mechanism (kev-4B; M-A to M-D).** The signal is sensitive to the appended vote's own round and is written mainly
   by layer-11 attention from the bulk of the context. It is locally sufficient and partly necessary (9/14). The repairs
   veto benign scenes.
4. **Probes and safety (M-E to M-G).** Probe separability is form (ARM_SHORTCUT, both models). Decision-token steering
   does not repair. Table S1 gives the three-action errors, and §4.18 the twin false vetoes.

**Withdrawn.**
- "Missing encoding" (v9) and "represented but not used" (v10–v11).
- Any reading of "recognized" as a validity check.

**Not claimed.**
- A mechanism of the miss.
- A defence.
- Generality beyond these 124 scenes and the kev family.
- That any internal state separates validity from form. This is untested, although SecJev's L11 span write is partly
  context-sensitive.

## Changes from V5
- **Manuscript v12** (`v12_edits.py` applied to V5's `generate_v11.js`):
  - new title, abstract and contributions;
  - a §3.4 terminology paragraph;
  - G2 headings say "readout-positive";
  - §4.10 caveat, a new §4.18 with Table T1, revised §4.15 / §4.16, discussion, limitations and reproducibility;
  - a shortcut-learning related-work paragraph with refs [25] and [26].
- **`numbers_mech_v3.json`** adds M23 (`extract_numbers_mech_v3.py`).
- **Documents.** `CLAIMS_EVIDENCE_MAP.md` (M-E decided, M-H new, terminology), `LIMITATIONS_AND_ERRATA.md` and
  `NOVELTY.md` (shortcut-learning row; V6 delta), `REPRODUCE.md` §7, and `AUDIT_RESPONSE.md` (V6 update).

## Contents
| File | Purpose |
|---|---|
| `A461_G2_paper_draft_v12.docx` / `.pdf` | Manuscript v12 |
| [AUDIT_RESPONSE.md](AUDIT_RESPONSE.md) | Response to `02a2b73`, plus the V6 update |
| [CLAIMS_EVIDENCE_MAP.md](CLAIMS_EVIDENCE_MAP.md) | C1–C8, K1–K3, M-A to M-H |
| [LIMITATIONS_AND_ERRATA.md](LIMITATIONS_AND_ERRATA.md) | Limitations and errata, including the V6 section |
| [NOVELTY.md](NOVELTY.md) | Competition matrix; `NOVELTY_NOT_YET_PASS` |
| [REPRODUCE.md](REPRODUCE.md), [REANALYSIS_CHECK.md](REANALYSIS_CHECK.md), `recompute_mech_v1.py`, `RECOMPUTE_MECH_R1/` | Reproduction and the M1–M22 deterministic re-computation |
| [CAPTURES.md](CAPTURES.md), `CAPTURES_SHA256SUMS`, `MECH_CAPTURES_SHA256SUMS`, `verify_captures_v1.py` | Capture releases (G2 and M1–M22). The M23 captures are on the server |
| `extract_numbers_mech_v3.py`, `numbers_mech_v3.json`, `numbers_v8.json`, `v12_edits.py`, `generate_v12.js` | Numbers and manuscript generation |
| `SHA256SUMS` | Hashes over the committed bytes |
