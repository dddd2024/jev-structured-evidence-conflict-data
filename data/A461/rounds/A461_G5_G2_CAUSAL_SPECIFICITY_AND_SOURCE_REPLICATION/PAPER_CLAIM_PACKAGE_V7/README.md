# A461 paper-level claim package V7

**Status: `UNVERIFIED_PAPER_READY_CLAIM`. The paper-level audit was triggered on 2026-11-01 with the user's approval.**
Asked "Trigger a paper-level audit on package V7?", the user answered:

> Trigger audit

The package content is that of `101aa84` (SHA256SUMS `3301acc`). Only this status line changed.
- V7 is the one-time, text-only revision that paper audit `8dd4528` asked for. That audit judged package V6
  (`PAPER_AUDIT_REVISE_REQUIRED`, P0×2 / P1×5 / P2×2) and left novelty at `NOVELTY_NOT_YET_PASS`.
- The audit independently recounted the M23 raw outputs and found them correct.
- No GPU forward was run for V7.
- Any new audit is triggered only with the user's go-ahead.
- The V3 scoped PASS (`4b27c9b`) for the G2 transplant claims stands.

## The claim (manuscript v13, 30 pages)

**Title.** *Missed When Valid, Vetoed When Not: Two Typed Language-Model Scorers' Conflict Decisions Are Not Robust to
the Validity of an Appended Vote.*

1. **Behaviour (M-H).** On a matched same-span counterfactual (one edit family, partner round), the scorers' decisions
   are mostly not robust to the appended vote's validity.
   - Where kev-4B rejects the conflict, it rejects the no-conflict twin in 37/40 scenes; SecJev does so in 14/14.
   - Twin false vetoes are 45/124 (14/17 groups) and 15/124 (9/17 groups).
   - The twins' full reject / accept / wait outcome is 45 / 72 / 7 and 15 / 56 / 53.

   This is behaviour, not an identified internal mechanism.
2. **Transplants (G2; numbers unchanged).** Readout-positive layer-11 span states causally drive the readout and the
   decision across source groups, beyond the sham, permutation and dose controls. They are not identified with a
   shortcut judgment.
3. **Mechanism (kev-4B, local).** The signal is sensitive to the appended vote's own round and is written mainly by
   layer-11 attention. It is locally sufficient and partly necessary (9/14), and the repairs veto benign scenes.
4. **Probes (M-E).** No detector meets the preregistered validity-tracking gate (ARM_SHORTCUT). This is not proof that
   validity is unrepresented: SecJev's L11 span write orders the conflict above its twin in 94.5% of missed scenes.

**Not claimed.**
- That the scorers never use the partner relation.
- A mechanism of the miss, or a shortcut circuit.
- Any generality beyond this edit family, these 124 scenes and the kev family.
- A defence.

## Changes from V6
- **Manuscript v13** (`v13_edits.py` applied to V6's `generate_v12.js`): the title, abstract, introduction,
  terminology, §4.15, §4.16, §4.18, discussion, limitations and reproducibility are narrowed. The related work adds four
  close prior works named by the audit (refs [27]–[30]).
- **Numbers.** `numbers_mech_v4.json` (`extract_numbers_mech_v4.py`) adds the twins' three-action table, the
  source-group spread, the quorum-change twins and the edit-family status.
- **Documents.**
  - [AUDIT_RESPONSE.md](AUDIT_RESPONSE.md): a response to `8dd4528`, and the stale V6 line is fixed.
  - `CLAIMS_EVIDENCE_MAP.md`: M-H and M-E narrowed.
  - `LIMITATIONS_AND_ERRATA.md`: a V7 section, including the NOT_INDEPENDENTLY_VERIFIED items.
  - `NOVELTY.md`: the audit's competition matrix.
  - `REPRODUCE.md`: a new §8.

## Contents
| File | Purpose |
|---|---|
| `A461_G2_paper_draft_v13.docx` / `.pdf` | Manuscript v13 |
| [AUDIT_RESPONSE.md](AUDIT_RESPONSE.md) | Responses to `02a2b73` (V5), M23 (V6) and `8dd4528` (V7) |
| [CLAIMS_EVIDENCE_MAP.md](CLAIMS_EVIDENCE_MAP.md) | C1–C8, K1–K3, M-A to M-H |
| [LIMITATIONS_AND_ERRATA.md](LIMITATIONS_AND_ERRATA.md) | Limitations and errata |
| [NOVELTY.md](NOVELTY.md) | `NOVELTY_NOT_YET_PASS`; competition matrix |
| [REPRODUCE.md](REPRODUCE.md), [REANALYSIS_CHECK.md](REANALYSIS_CHECK.md), `recompute_mech_v1.py`, `RECOMPUTE_MECH_R1/` | Reproduction |
| [CAPTURES.md](CAPTURES.md), `CAPTURES_SHA256SUMS`, `MECH_CAPTURES_SHA256SUMS`, `verify_captures_v1.py` | Capture releases |
| `extract_numbers_mech_v4.py`, `numbers_mech_v4.json`, `numbers_v8.json`, `v13_edits.py`, `generate_v13.js` | Numbers and manuscript generation |
| `SHA256SUMS` | Hashes over the committed bytes |
