# A461 paper-level claim package V5

**Status: `UNVERIFIED_PAPER_READY_CLAIM`.** This is the one-time revision that paper audit `02a2b73` asked for. The audit
judged package V4 (`PAPER_AUDIT_REVISE_REQUIRED`, P0×2 / P1×6 / P2×2) and set novelty to `NOVELTY_NOT_YET_PASS`.

- The audit said this revision does not automatically trigger a new audit. Any further audit is triggered only with the
  user's go-ahead.
- The V3 scoped PASS (`4b27c9b`) for the G2 transplant claims stands.

## What changed from V4

A point-by-point response is in [AUDIT_RESPONSE.md](AUDIT_RESPONSE.md).

- **Manuscript v11** (28 pages): v10 narrowed to the claims the audit allows, plus a new §4.17 and Table S1 (three-action
  safety errors).
- **Mechanism claims, narrowed** (`CLAIMS_EVIDENCE_MAP.md`):

  | Claim | V5 statement |
  |---|---|
  | M-A / M-B | A round-sensitive layer-11 signal, written mainly by attention from the bulk context. It is **locally and conditionally sufficient** in these 14 donors × 8 hosts. Only head 10 meets the writer rule; there is no unique circuit. |
  | M-D | **Four representative repair families** were checked for false veto. Necessity is **partial and interventional**: 9 of 14 donors lose recognition and 5 keep it. |
  | M-E | Missed appended-conflict states and benign states are **linearly separable above the token surface**, on two kev-family checkpoints on the same scenes. The labels are **confounded with the arm**, so validity encoding is not claimed. |
  | M-F | **The tested decision-token steering produced no selective repair.** The null is not direction-specific, and γ32 changed 20 actions. |
  | M-G (new) | Native three-action errors per model and arm (Table S1). |

- **Candidate explanation.** "Represented but not used" is now only a candidate, replacing "missing encoding". Neither is
  identified.
- **G2.3 (CPU check for P0-1).** A same-span, Gold-varying twin is constructible in **124/124 scenes and 17/17 source
  groups**. The appended vote is byte-identical, one partner-round token changes, and Gold moves off `reject_conflict`
  (`research/rounds/A461_MON_G23_CONTEXT_COUNTERFACTUAL_CPU/`). **Not run on GPU.**
- **Captures released.** The M1–M22 capture tensors are private GitHub Release assets (`a461-mech-captures-m1-m22-v1`,
  user-approved on 2026-11-01; see `CAPTURES.md`).
- **Novelty.** `NOVELTY.md` sets the status to `NOVELTY_NOT_YET_PASS` and adds a strict competition matrix.
- **Erratum.** In `M20_RESULT_R1.md`, the four donors listed as keeping recognition are now marked as examples; there
  are 5 survivors.

## Open decision for the user

The one experiment that could restore a stronger M-E is a GPU stage (about 124 forwards per model) that scores the G2.3
twins with the frozen M18 / M22 probes.

- If the probes score the twins like benign rows, the separability tracks conflict validity, not the arm.
- If they score them like `new` rows, it is an arm shortcut.

It is not part of this revision.

## Contents

| File | Purpose |
|---|---|
| `A461_G2_paper_draft_v11.docx` / `.pdf` | Manuscript v11 |
| [AUDIT_RESPONSE.md](AUDIT_RESPONSE.md) | Point-by-point response to `02a2b73` |
| [CLAIMS_EVIDENCE_MAP.md](CLAIMS_EVIDENCE_MAP.md) | V4's map, with M-A to M-F narrowed and M-G added |
| [LIMITATIONS_AND_ERRATA.md](LIMITATIONS_AND_ERRATA.md) | V4's list plus a V5 section |
| [NOVELTY.md](NOVELTY.md) | Competition matrix and `NOVELTY_NOT_YET_PASS` |
| [REPRODUCE.md](REPRODUCE.md), [REANALYSIS_CHECK.md](REANALYSIS_CHECK.md) | Reproduction (§6 is new) and the 22/22 deterministic re-computation |
| [CAPTURES.md](CAPTURES.md), `CAPTURES_SHA256SUMS`, `MECH_CAPTURES_SHA256SUMS`, `verify_captures_v1.py` | G2 and mechanism capture releases |
| `extract_numbers_mech_v2.py`, `numbers_mech_v2.json` | Every mechanism number in v11 |
| `v11_edits.py`, `generate_v11.js`, `numbers_v8.json` | Regenerate v11 from V4's `generate_v10.js` |
| `recompute_mech_v1.py`, `RECOMPUTE_MECH_R1/` | Unchanged from V4 |
| `SHA256SUMS` | Hashes of every file, computed over the committed bytes |
