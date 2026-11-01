# A461 paper-level claim package V8 (TMLR path)

**Status: `UNVERIFIED_PAPER_READY_CLAIM`. Not audited.** V8 carries out path A of paper audit `4acf7de` (V7,
`PAPER_AUDIT_REVISE_REQUIRED`, P0×1 / P1×4 / P2×2). It applies re-audit `ee23782`: the CPU go/no-go G2.4 came out
**NO-GO**, so the mechanism route is closed. The target venue is **TMLR**, as the user chose.

- No GPU forward was run.
- Novelty stays `NOVELTY_NOT_YET_PASS`.
- The mechanism is NOT_IDENTIFIED.
- The V3 scoped PASS (`4b27c9b`) for the G2 transplant claims stands.

## The paper (manuscript v14, 31 pages; DOCX build)

The title is unchanged from v13: *Missed When Valid, Vetoed When Not: Two Typed Language-Model Scorers' Conflict
Decisions Are Not Robust to the Validity of an Appended Vote.*

**Changes from v13:**
- **Related work.** The wording is narrowed: "a failure to act on appended relational evidence"; the query side is
  scoped to our decomposition; the counterfactual is described as "appended span byte-identical at the same position and
  length, one earlier token changed". §4.18 is corrected the same way.
- **§4.18 additions:**
  - source-group cluster-bootstrap CIs for the M23 rates, the benign false veto and the G2 joint repair;
  - SecJev's degenerate 14/14 with an exact bound;
  - **Table T2**, the twins' full Gold × prediction matrix.
- **§6** adds the G2.4 facts: no clean orthogonal partner edit, and too few discordant pairs for a state swap.
- **New §8, Availability.** It covers what is released and what is not, and what has and has not been verified.

The headline numbers, with 95% CIs from a source-group bootstrap:

| | kev-4B | SecJev |
|---|---|---|
| Appended conflict missed | 67.7% [55.7, 75.3] | 88.7% [80.0, 94.6] |
| Legitimate twin false-vetoed | 36.3% [27.8, 47.1] (14/17 groups) | 12.1% [6.7, 20.3] (9/17 groups) |
| Twin rejected where the conflict is rejected | 37/40 (92.5% [81.6, 100]) | 14/14 (exact lower bound 0.81) |

## Next steps for TMLR (not done in V8)
1. **Convert to TMLR LaTeX.** Use the official TMLR style file (an external download, which needs approval). The
   document is anonymized for review.
2. **Anonymize the repository link.** The current DOCX names the repository.
3. **Check submission requirements.** TMLR's policy on prior and concurrent submissions, the broader-impact statement,
   and the length recommendation (a shorter main text with an appendix is encouraged).

## Contents
| File | Purpose |
|---|---|
| `A461_G2_paper_draft_v14.docx` / `.pdf` | Manuscript v14 (content master for the TMLR version) |
| [AUDIT_RESPONSE.md](AUDIT_RESPONSE.md) | All responses, ending with `4acf7de` / `ee23782` |
| [CLAIMS_EVIDENCE_MAP.md](CLAIMS_EVIDENCE_MAP.md) | Claims, with a V8 reading rule and the CIs |
| [LIMITATIONS_AND_ERRATA.md](LIMITATIONS_AND_ERRATA.md) | Limitations, with a V8 section |
| [NOVELTY.md](NOVELTY.md) | The governing V8 statement; earlier sections marked ARCHIVAL — SUPERSEDED |
| [REPRODUCE.md](REPRODUCE.md), [REANALYSIS_CHECK.md](REANALYSIS_CHECK.md), `recompute_mech_v1.py`, `RECOMPUTE_MECH_R1/` | Reproduction |
| [CAPTURES.md](CAPTURES.md), `CAPTURES_SHA256SUMS`, `MECH_CAPTURES_SHA256SUMS`, `verify_captures_v1.py` | Capture releases |
| `extract_numbers_mech_v5.py`, `numbers_mech_v5.json`, `numbers_v8.json`, `v14_edits.py`, `generate_v14.js` | Numbers and manuscript generation |
| `SHA256SUMS` | Hashes over the committed bytes |
