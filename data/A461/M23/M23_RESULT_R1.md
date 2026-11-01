# A461-MON-M23 R1: result (do the M18 / M22 probes track conflict validity or the arm?)

Reported in the order of the [novelty × security-value standard](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §9.

## 1. Experiment and receipt
| | kev-4B (`M23K`) | SecJev-0.8B (`M23S`) |
|---|---|---|
| forwards | 248/248 in batches [128, 120]; 0 denied; 1 model load; 379 s | 248/248; 0 denied; 1 model load; 110 s |
| Stage-A anchors | `bitwise_vs_stage_a: checked` (124 `new` rows) | checked |
| raw blob | `7ffebade1d6339340a466bd5032f93f0a992ecc3` | `6e2d9a8e1beeac1507433ce3a68a0a4f23a3ddce` |
| analysis | `m23k_analysis.json` (sha256 `2a74eedb…`), exit 0 | `m23s_analysis.json` (`f09236e3…`), exit 0 |

- Run under prereg `5bd58f6` with the user's instruction "Run M23" and the standing GPU authorization.
- Both pre-model gates passed. Each run had a single ledger attempt.
- The run `SHA256SUMS` check clean on their non-capture entries. The captures stay on the server.
- **No deviation.**

## 2. Native safety endpoint and Gold
- **Rows.** The 124 Stage-A scenes, each as `new` (an appended valid equivocation; Gold `reject_conflict`) and as its
  G2.3 TWIN.
- **TWIN.** The same state and the byte-identical appended vote. The only change is that the appended author's earlier
  vote for the candidate block moves to a non-candidate round, so the author no longer double-votes. Gold is accept (102)
  or wait (22).
- **Unit.** The MISSED scenes (parent native action on `new` is not `reject_conflict`): kev-4B 84 in 16 groups, SecJev
  110 in 16 groups.
- **Level.** S1–S2.

## 3. Main results and failed controls
**Consistency gate: PASS on both models.**
- 248 rows.
- The 124 `new` rows equal the parent's (M18 / M22) bitwise, in both logits and capture tensors.
- Every TWIN's emb-layer span mean equals its `new` row's in 124/124 scenes.
- The refit reproduces the parent's held-out AUROC exactly, for every detector.

**Preregistered verdicts: ARM_SHORTCUT for every detector on both models, including both primary detectors.**

Columns: AUROC_pair = new-missed vs its own twin (CI); TWIN flagged and new flagged at FV5 (TWIN CI); new > TWIN = share of
scenes where the new row scores above its twin; TWIN vs benign = AUROC of twins against the parent's benign rows.

| detector | AUROC_pair (CI) | TWIN flagged @FV5 (CI) | new flagged @FV5 | new > TWIN | TWIN vs benign |
|---|---|---|---|---|---|
| **kev-4B: span write `SPAN_ATTN11`** (primary) | 0.450 [0.405, 0.492] | **0.976** [0.925, 1.0] | 0.952 | 0.24 | 0.996 |
| **kev-4B: decision state `LAST_RESID_L31`** (primary) | 0.405 [0.365, 0.457] | **0.929** [0.807, 0.990] | 0.964 | 0.39 | 0.985 |
| kev-4B: `SPAN_RESID_L11` | 0.415 | 1.000 | 1.000 | 0.12 | 0.998 |
| kev-4B: `LAST_RESID_L19` (parent's best generic) | 0.442 | 0.976 | 1.000 | 0.46 | 0.996 |
| kev-4B: surface `SPAN_RESID_emb` | 0.500 | 0.143 | 0.143 | 0.00 | 0.816 |
| **SecJev: span write `SPAN_ATTN11`** (primary) | 0.698 [0.642, 0.772] | **0.655** [0.520, 0.753] | 0.873 | 0.95 | 0.921 |
| **SecJev: decision state `LAST_RESID_L23`** (primary) | 0.468 [0.424, 0.510] | **0.873** [0.753, 0.967] | 0.864 | 0.36 | 0.972 |
| SecJev: `SPAN_RESID_L11` | 0.563 | 0.918 | 0.982 | 0.71 | 0.989 |
| SecJev: `LAST_RESID_L11` (parent's best generic) | 0.266 | 0.936 | 0.918 | 0.04 | 0.982 |
| SecJev: surface `SPAN_RESID_emb` | 0.500 | 0.109 | 0.109 | 0.00 | 0.805 |

**Reading.**
- The probes that separated missed conflicts from benign rows at AUROC 0.96–1.00 (M18 / M22) **flag the no-conflict twins
  as often as the conflicts**.
- The twins sit with the conflicts, not with the benign rows: twin-vs-benign AUROC is 0.92–1.00.
- The surface probe is unchanged by construction: the span tokens are identical.
- **The separability in M18 / M22 is therefore explained by the appended item's form or arm** (an appended vote for a
  non-candidate block in the candidate round), **not by whether the vote is an equivocation in context.**
- **Only one detector shows some context sensitivity: SecJev's L11 span write** (new > TWIN in 95% of scenes;
  AUROC_pair 0.70). It still flags 66% of twins at FV5 (30% at FV1, against 57% of new rows), so it is ARM_SHORTCUT by
  rule. This is reported, not preregistered.

**Native behaviour (reported; new in this stage).** The scorers themselves do not condition on the partner vote either.

| | recognized scenes (new rejected) | TWIN rejected there | TWIN conflict readout C > 0 there | missed scenes: median TWIN − new conflict margin |
|---|---|---|---|---|
| kev-4B | 40 | **37/40** | 36/40 (new: 36/40) | **+0.30** |
| SecJev | 14 | **14/14** | 14/14 (new: 14/14) | **+0.58** |

- On the twins, kev-4B false-vetoes 45/124 (33 accept-Gold, 12 wait-Gold) and SecJev 15/124.
- In the scenes the models "recognize", removing the double vote leaves both the conflict readout and the rejection in
  place.
- In the scenes they miss, removing it *raises* the conflict margin.
- Neither scorer's conflict judgment depends on the element that defines an equivocation, the author's earlier vote for
  the candidate block.

**Failed controls:** none. The surface probe behaves as constructed.

## 4. Causal level and scope
1. **Audit P0-1 is resolved against the stronger reading.**
   - With arm, form and span held fixed and only conflict validity flipped, neither the span probes nor the
     decision-state probes separate conflict from no-conflict.
   - M-E must say that the separability reflects the appended item's form or arm.
   - Under the interpretation fixed in advance, **"represented but not used" loses its main support.** The probes do not
     show that the conflict is represented.
2. **The models' "recognition" is form-driven.**
   - Within these scenes, both scorers flag an appended vote for a different block in the candidate round as a
     conflict whether or not its author has already voted for the candidate block.
   - This reframes what the G2 "recognized" donor spans carry. G2's transplant results stay interventional facts about
     those spans. But "recognition" there means the model's conflict readout, not a validity-sensitive judgment.
   - M1's round sensitivity concerns the appended vote's **own** round, a field inside the span, and it is consistent
     with this.
3. **Scope.** The same 124 scenes; two kev-family checkpoints; one twin family (partner round). A partner-author twin was
   constructible in only 23 scenes and was not run.

## 5. Strongest prior art and the novelty delta
- **Prior art:** shortcut learning and probe-confound literature (probes reading surface or arm features), and
  "right for the wrong reasons" analyses.
- **What M23 adds:** a preregistered same-span counterfactual that removes the arm confound in this task. It shows that
  both the probes and the scorers themselves track the appended item's form rather than equivocation validity.
- **Delta:** small for method. For the paper it is decisive: it removes an overclaim and replaces it with a sharper
  safety fact.

## 6. Safety reading
- **The scorers do not check equivocation; they react to a vote's form.** They miss most real equivocations, and they
  reject legitimate scenes that contain the same form: kev-4B false-vetoes 45/124 twins, SecJev 15/124. Recall the
  natural false veto on wrong-round / outsider votes was only 7 + 6 / 124 (kev-4B, M18).
- Probe monitors trained on arm-collinear labels inherit the same shortcut. **The preregistered span monitor flags
  66% (SecJev) to 98% (kev-4B) of the legitimate twins of missed scenes at FV5. It is not a validity monitor.**
- **Safety value:** S2 characterization, and stronger than before: a measured false-veto mode on legitimate scenes and a
  measured failure of the monitor's validity. There is no defence.

## 7. Open decisive questions
- Whether any internal state separates the twin from `new`. SecJev's L11 span write is partly context-sensitive. A probe
  trained *with* twins as negatives would test this, as a new stage.
- What G2's "recognized" spans carry beyond form, given that M1's round control acts on the span's own round field.

## 8. Decision
- **P0-1: ARM_SHORTCUT.** M-E is restated as "the separability reflects the appended item's form or arm, not
  equivocation validity". The "represented but not used" candidate is withdrawn as unsupported.
- **New S2 finding, kept:** both scorers' conflict judgments ignore the partner vote. The twin false veto is 45/124
  (kev-4B) and 15/124 (SecJev).
- **The monitor is downgraded** from "useful diagnostic" to "form detector; not validity-specific".
- **Next:** revise the paper package (v12) under these fixed interpretations.
