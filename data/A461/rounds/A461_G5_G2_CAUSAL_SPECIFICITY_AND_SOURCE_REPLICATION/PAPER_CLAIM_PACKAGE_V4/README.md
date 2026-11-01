# A461 paper-level claim package V4

**Status: `UNVERIFIED_PAPER_READY_CLAIM`. The final paper-level audit was triggered on 2026-11-01 with the user's
approval.** Asked "Trigger the final paper-level audit on package V4 now?", the user answered:

> Trigger audit

The package content is that of `9c641af`; only this status line changed.

- **V3** (`2fca4ef`, manuscript v9) passed the third independent audit (`4b27c9b`, `PAPER_AUDIT_PASS`, scoped). That pass
  covers the G2 claims as v9 states them.
- **V4 adds the mechanism route M1–M22.** This is 22 preregistered GPU stages: 86,138 kev-4B forwards and 620 SecJev
  forwards. V4 also revises v9's candidate explanation of the failure. Neither has been audited.

## What V4 adds to the claim

V3's claims C1–C8 and K1–K3 are unchanged, with the same numbers (`numbers_v8.json`). The exception is C4, whose
candidate explanation is revised (below). The mechanism claims are listed in full in `CLAIMS_EVIDENCE_MAP.md`, M-A to
M-F:

| Claim | Statement | Scope |
|---|---|---|
| M-A | The appended span's layer-11 state carries a **round-keyed conflict verdict**. Changing only the vote's round turns 53/104 joint repairs into 1. | kev-4B; 14 donor groups × 8 hosts |
| M-B | **Full-attention heads 8–14 at layer 11 write the verdict**, with head 10 the most necessary. They read the bulk of the context, not the conflict partner. The read acts by direction, not size, and transfers across scenes. | kev-4B (Tier A) |
| M-D | **Every repair is checked for false veto.** The own-donor patch is NONSELECTIVE (it vetoes 36/104 duplicate and 43/104 wrong-round votes). **The round-keyed read is necessary** for recognition in 9/14 recognizing donors. Necessity is partial: a failing host's write removes it in only 20–26% of cells. | kev-4B |
| M-E | **In the missed scenes the conflict is linearly decodable**, from the span and from the decision state, above the token surface. | kev-4B and SecJev-0.8B (M22 replicates M18) |
| M-F | **…but it is not used.** Gain or a 20%‖h‖ push along the conflict direction at the decision token moves no decision. | kev-4B; decision token, layers 19 and 31 |

**Revised candidate explanation.** v9 presented "missing encoding at the appended span" as the leading candidate. v10
replaces it with "represented but not used". The conflict is present in the missed scenes. It is not written into the
round-keyed form that downstream rows read, and it is not read at the decision. This is decodability on two scorers plus
kev-4B interventions, not an identified circuit.

**Not claimed (additions to V3's list).**
- Any intervention result on SecJev. M22 replicates only the decodability and monitor stage.
- An independent scene distribution.
- Novelty for the mechanism-located monitor. Generic probes match it on both scorers, so it is infrastructure only.
- Any defence or deployment benefit. Repairs veto benign scenes (M17), the monitor needs rule labels, and the
  deterministic rule solves the task.
- Conclusions from the pooled-vector line M6–M16. It is host-limited and Tier B/C.

## V3 audit leftovers (`4b27c9b`, non-blocking), all resolved in V4

| Item | Resolution |
|---|---|
| P1-Editorial-1: two stale sentences in `NOVELTY.md` (Tang et al.: "places the failure at the encoding"; Chu et al.: "separate recognition from decision class") | Replaced with the wording the audit asked for, and further updated for the revised account |
| P1-Editorial-2: do not present the joint repair as a whole-model safety correction | Unchanged and still disclosed: the `evidence_level` side effect stays in `LIMITATIONS_AND_ERRATA.md`. v10 adds that the repairs veto benign scenes (M17) and claims no safety improvement |
| P2: unclosed `**` in `NOVELTY.md` "Where it holds" | Fixed |

## Contents

| File | Purpose |
|---|---|
| `A461_G2_paper_draft_v10.docx` / `.pdf` | Manuscript v10. It is v9 plus sections 4.12–4.16, Table M1, a revised abstract, contributions, discussion, limitations and reproducibility. |
| [CLAIMS_EVIDENCE_MAP.md](CLAIMS_EVIDENCE_MAP.md) | V3's map, with C4 revised and M-A to M-F added (stage, commits, JSON keys, falsifiers). |
| [LIMITATIONS_AND_ERRATA.md](LIMITATIONS_AND_ERRATA.md) | V3's content plus the mechanism ceilings, every failed or edge preregistered criterion of M1–M22, and the M17 / M22 deviations. |
| [NOVELTY.md](NOVELTY.md) | V3's comparison, with the audit leftovers fixed and a mechanism-route section added. |
| [REPRODUCE.md](REPRODUCE.md) | V3's commands plus section 5: the mechanism recompute and manuscript v10. |
| [REANALYSIS_CHECK.md](REANALYSIS_CHECK.md) | Result of re-running all 22 mechanism analyses (V4). V3's G2 re-analysis is unchanged in package V3. |
| [CAPTURES.md](CAPTURES.md), `CAPTURES_SHA256SUMS`, `verify_captures_v1.py` | G2 capture releases (unchanged), plus the mechanism captures, which are server-side and unreleased. |
| `recompute_mech_v1.py` | Re-runs all 22 frozen mechanism analyses and compares them with the committed JSONs. |
| `extract_numbers_mech_v1.py`, `numbers_mech_v1.json` | Every mechanism number in v10, taken from archived JSONs and receipts. |
| `v10_edits.py`, `generate_v10.js`, `numbers_v8.json` | Regenerate v10 from V3's `generate_v9.js`. |
| `SHA256SUMS` | Hashes of every file in this package. |

## Weak points the authors flag for the auditor (additions to V3's list)

1. **The interventions are one model.** SecJev replicates only the monitor stage, on the same scenes.
2. **Necessity is partial, and recognition is redundant** in the strongest donors (M20).
3. **The readout null reaches only the decision token.** A random push of the same size is also nearly inert, so the
   decision state has little leverage at this dose in any direction (M21).
4. **The pooled-vector line failed several preregistered criteria** (split nulls ×3, low rank, linearity). Tier B is
   limited to 3/8 hosts, and Tier C is not used.
5. **Two analyses deviated from their frozen scripts.** M17 v1.1 fixes a lookup bug after the run. M22's None-safety fix
   was made before the run.
6. **The captures are not released.** Recomputing six stages needs server access until the user approves a release.
