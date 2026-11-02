# A461-MON-G2.3: can the arm/Gold confound of M18/M22 be broken? (CPU constructibility check, 2026-11-01)

**Why.** V4 audit `02a2b73`, P0-1: in M18 and M22 every positive row is a `new` row and every negative is a non-`new` row.
So a probe could separate arms (format, role, position) rather than conflict validity. The audit asks either for a
within-arm, Gold-varying, format-matched counterfactual, or for M-E to be narrowed. This check answers the first
question at the constructibility level only. **CPU only: tokenizer loaded once, no model load, no GPU forward.**

**Design.**
- **Script:** `A461_mon_g23_ctx_cf_cpu_v1.py` (sha256 `c6e708b0…`). It ran on `REDACTED_RESEARCH_HOST` with the frozen corpus (sha
  pinned), the Stage-A oracles (helper as in G1.0), the M18 design, and the M18 / M22 raw rows (used only for the
  native sets).
- **What changes.** For each of the 124 M18 scenes, the appended `new` vote is kept unchanged. Only the context
  changes: the appended author's own earlier vote for the candidate block in the candidate round (the *partner* vote
  that makes the appended vote an equivocation).
- **Families.**
  - `PARTNER_ROUND`: the partner vote's round is set to the nearest non-candidate round.
  - `PARTNER_AUTHOR`: the partner vote's author is set to a validator who is not a supporter.
  - `PARTNER_BLOCK`: the partner vote's block is set to the appended vote's block.
- **Gates.**
  - Both oracles agree.
  - Gold is not `reject_conflict`, and there is no conflicting vote.
  - The total token length equals the `new` arm's.
  - The appended span's token ids and position equal the `new` arm's.
  - The question segments are unchanged.

## Result

Every scene has exactly one partner vote. Outputs: `G23_OUT_R1/receipt.json`, `G23_OUT_R1/ctx_counterfactuals.json`.

| family | scenes (of 124) | source groups (of 17) | Gold = old Gold | token positions changed |
|---|---|---|---|---|
| **PARTNER_ROUND** | **124** | **17** | 120 (4 go accept → wait: the author's support is lost and quorum drops) | **exactly 1, before the span, in 124/124** |
| PARTNER_BLOCK | 124 | 17 | 120 | exactly 1 in 124/124 |
| PARTNER_AUTHOR | 23 | 7 | 23 | exactly 1 (non-supporters are rare, as in G1.0's NONSUP) |

**PARTNER_ROUND coverage by native set:**
- kev-4B MISSED: 84/84, 16/16 groups.
- kev-4B RECOGNIZED: 40/40, 14/14 groups.
- SecJev MISSED: 110/110, 16/16 groups.

**What it shows.**
- A within-format, Gold-varying contrast exists in every scene and every source group.
- The appended span is **byte-identical and at the same position** in the `new` row and its `PARTNER_ROUND` twin.
- The twins differ by one round token in the earlier partner item, and Gold moves from `reject_conflict` to
  accept/wait.
- A span or decision-state probe that reads the appended vote's form or arm would score the twin like `new`. A probe
  that reads conflict validity in context would score it like a benign row.

**What it does not show.** Nothing about the model or the probes: no forward was run. Deciding P0-1 needs a GPU stage that
captures the same M18 / M22 features on the twins and scores them with the frozen, held-out probes. This is one forward
per twin, 124 per model.

**Caveat for that stage.** The partner round token sits before the span, so the span's own computation can see it. This
is intended: the question is whether the span state reflects the contextual relation. A single-token difference is
also the format-matched control the audit asks for.

**Decision.** P0-1 is **testable**. A preregistered GPU stage (M23) can test the same-arm, Gold-varying contrast in 124/124
scenes and 17/17 groups on both models. Until it runs, M-E is narrowed in the text, as the audit requires.
