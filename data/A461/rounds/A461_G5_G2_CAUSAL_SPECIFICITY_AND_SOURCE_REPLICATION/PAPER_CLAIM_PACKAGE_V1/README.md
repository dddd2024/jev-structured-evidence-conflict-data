# A461 paper-level claim package V1

**Status: `UNVERIFIED_PAPER_READY_CLAIM`.** This package triggers the single independent paper-level audit defined in
`research_governance/2026-10-27_JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2.md`. It is not an independently
verified result.

## The claim

On SecJev-0.8B, a security-typed 0.8B scorer, the failure to recognize an appended equivocation vote is an **encoding
failure at the appended span by mid-depth**. Three findings support this:

1. **The span carries content.** A recognized encoding of the span at layer 11 carries content-specific conflict
   information across source groups.
2. **The failure is in encoding.** A missed conflict's span behaves like a harmless duplicate vote.
3. **Implanting a recognized encoding repairs the decision.** Putting it into the certificate-action row alone flips
   the decision to the rule-mandated `reject_conflict`, specifically and across groups. Every other question row stays
   bitwise untouched.

The novelty is defined against prior work in [NOVELTY.md](NOVELTY.md). The full scope and ceilings are in
[LIMITATIONS_AND_ERRATA.md](LIMITATIONS_AND_ERRATA.md).

## Contents

| File | Purpose |
|---|---|
| `A461_G2_paper_draft_v6.docx` / `.pdf` | Manuscript v6. Sections 1-4.4 are v5.2 verbatim; Sections 3.4 and 4.5-4.9 are new; the abstract, discussion, limitations, reproducibility and references are rewritten. |
| [CLAIMS_EVIDENCE_MAP.md](CLAIMS_EVIDENCE_MAP.md) | Each claim, mapped to its stage, commit, archived file, JSON key and value, preregistration status, and falsifier. |
| [NOVELTY.md](NOVELTY.md) | Direct comparison with the closest prior work (literature checked on 2026-10-27). |
| [REPRODUCE.md](REPRODUCE.md) | CPU re-analysis commands (verified), manuscript regeneration, and the full GPU re-run procedure. |
| [LIMITATIONS_AND_ERRATA.md](LIMITATIONS_AND_ERRATA.md) | Ceilings, missed preregistered criteria, errata, and known weak points for the auditor. |
| `numbers_v6.json` | The single source of every G2 number in the manuscript, extracted from archived artifacts. |
| `extract_numbers_v6.py`, `assemble_v6.py`, `generate_v6.js` | The scripts that regenerate `numbers_v6.json` and the manuscript. |
| `REANALYSIS_CHECK.md` | Result of re-running all five frozen analysis scripts on the archived raw data. |

## Weak points the authors flag for the auditor

1. **Donor concentration.** One donor (twins_streamlet:run-140) supplies 6 of the 10 decision repairs and 7 of the 10
   readout repairs. Without it, decision repair keeps 4/24 cells across two donor and two host groups. That is the
   preregistered cross-group rule's minimum. The leave-one-donor-out analysis is exploratory.
2. **Few donors.** There are only 4 strict donors, from 3 source groups that earlier rounds had already used for other
   scenes. The constructible roster is exhausted (171 scenes screened).
3. **One model, one simulator family, constructed edits.** No cross-model replication exists.
4. **A preregistered threshold was missed.** The encoding projection test failed its layer-11 threshold
   (AUC 0.84 < 0.9; 0.90 at layer 12).
5. **A preregistered criterion was unattainable.** Stage D's action criterion could not be met by construction. It is
   documented as an erratum, and Stage E corrected the design before running.
