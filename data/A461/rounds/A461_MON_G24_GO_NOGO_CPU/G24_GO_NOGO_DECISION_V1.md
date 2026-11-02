# A461-MON-G2.4: CPU go/no-go for the last bounded mechanism package (2026-11-01)

**Why.** Re-audit `ee23782` (CONDITIONAL_CONTINUE / HOLD_UNBOUNDED_GPU) allows one last bounded package, if it first
passes a CPU-only go/no-go against five gates (§IV.A):
1. an orthogonal relation-validity counterfactual beyond M23's partner-round edit;
2. a natural-mediation test (within-scene conflict vs twin state swap) on which competing mechanisms predict different
   outcomes.

The user chose "The CPU go/no-go" over an immediate pivot. **CPU only: tokenizer loaded once, existing M23 captures
read, no model load, no GPU forward.**

**Script and outputs.** `A461_mon_g24_go_nogo_cpu_v1.py` (sha256 `eae3ca75…`), run on `REDACTED_RESEARCH_HOST` with the frozen
corpus, the Stage-A oracles and the M18 design. Outputs are in `G24_OUT_R1/`.

## Evidence

### A. Is there a clean orthogonal relation edit?
For each of the 124 scenes, the candidate edits to the appended author's earlier vote for the candidate block (the
*partner* vote) are listed below. The appended vote is always kept byte-identical at the same position and length.

| edit | what it does | constructible (gates as G2.3) | problem |
|---|---|---|---|
| PARTNER_ROUND | partner → non-candidate round | 124/124, 17/17 groups | already run (M23) |
| PARTNER_BLOCK (G2.3) | partner → **the appended vote's block** | 124/124 | **Confounded.** In 124/124 scenes the partner then equals the appended vote, so the appended vote becomes a re-vote, the duplicate (SA) form that both scorers already treat as benign (kev-4B rejects 0/124 SA scenes). Form and validity change together. |
| PARTNER_BLOCK_OTHER (new) | partner → a third block (neither the candidate nor the appended block) | **1/124**, 1 group | 120/124 scenes contain no third block |
| PARTNER_AUTHOR (G2.3) | partner → a non-supporting validator | 23/124, 7/17 groups; kev-4B MISSED 9 (7 groups), RECOGNIZED 14 (6 groups) | Small and group-concentrated |
| PARTNER_LATE | partner received after the deadline | 0 (G1.0: 0 late votes in the corpus) | Out of distribution |
| PARTNER_DROP | delete the partner vote | — | Shifts every later position and the span position, so it is not position-matched |

### B. Is there room for a within-scene conflict-vs-twin state swap?
The table compares the relative L2 distance between each scene's conflict and twin states with the median distance to
other scenes' conflict states. Values are medians over 124 scenes.

| feature | kev-4B within / between (ratio) | SecJev within / between (ratio) |
|---|---|---|
| L11 span attention write | 0.063 / 0.328 (0.19) | 0.124 / 0.348 (0.35) |
| L11 span residual | 0.027 / 0.171 (0.16) | 0.075 / 0.290 (0.26) |
| decision-position state (L31 / L23) | 0.014 / 0.027 (0.50) | 0.009 / 0.025 (0.35) |
| **pairs whose reject decision differs (conflict vs twin)** | **11 / 124** | **1 / 124** |
| pairs whose action differs at all | 15 | 15 |

The states differ measurably, so a swap would move something. But on the native safety endpoint (reject or not), only
11 kev-4B pairs and 1 SecJev pair are discordant. A swap can change the decision only where the two decisions differ.
Elsewhere it can move only margins, and the margin difference runs *against* validity: the twin's conflict margin is
higher in 88/124 and 101/124 pairs.

## Gate assessment (ee23782 §IV.A)

| gate | assessment | verdict |
|---|---|---|
| 1. A falsifiable gain over the closest prior work | A swap result would locate a small context difference, which is not a gain over Yan et al. / Buzato et al. (path patching; gold vs counterfactual evidence patching). The orthogonal-edit result would at best replicate M23's behavioural finding | **FAIL** |
| 2. Competing mechanisms with different predictions on the native endpoint | H-FORM (the readout follows the appended item's form) and H-CTX (the span state carries a context-sensitive signal that the readout uses) differ only on the 11 (kev-4B) / 1 (SecJev) discordant pairs. That is too few to decide between them: with 11 pairs in at most a handful of groups, any outcome is UNKNOWN | **FAIL** |
| 3. Realistic execution (clean, orthogonal, Gold-valid, enough coverage) | No orthogonal edit with coverage. PARTNER_BLOCK is form-confounded, PARTNER_BLOCK_OTHER covers 1/124, PARTNER_AUTHOR covers 23/124 (7 groups), LATE is out of distribution, and DROP is not position-matched | **FAIL** |
| 4. A closed three-action safety endpoint | Feasible in principle (the existing runners log all three actions against Gold) | PASS |
| 5. Residual information value | Either outcome leaves the paper's claim unchanged: behavioural non-robustness stands, and the mechanism stays NOT_IDENTIFIED | **FAIL** |

## Decision: **NO-GO → PIVOT_TO_PAPER**

- No mechanism GPU stage is started. The deep-mechanism route (M-series) is **closed** for this paper.
- The closure rests on identifiability and coverage limits found on CPU, not on lack of budget or authorization. Under
  ee23782 §IV.C, "the remaining mechanism hypotheses cannot form an informative, distinguishable, feasible test".
- This does **not** show that a mechanism is unfindable. It shows that this task's scene distribution supports no
  clean orthogonal relation edit, and that the scorers' decisions have too few discordant pairs for a decision-level
  mediation test.
- **These facts go into the paper's limitations:**
  - the constructibility table in §A;
  - the discordance counts in §B.
- **What the paper carries forward (path A of audit `4acf7de`):**
  - the M23 behavioural non-robustness on one matched edit;
  - the G2 conditional transplant effects;
  - the local kev-4B mechanism stages;
  - the three-action safety results;
  - all reported with group-level uncertainty, an availability statement, and the wording fixes listed in `4acf7de`.
