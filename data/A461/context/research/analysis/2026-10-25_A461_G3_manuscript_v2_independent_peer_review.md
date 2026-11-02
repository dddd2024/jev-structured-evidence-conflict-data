# Independent paper-level review of A461-G3 manuscript v2

Date: 2026-10-25. Verdict: **MAJOR REVISION — substantial, real behavioral observation; manuscript as written is NOT ready to claim a fully preregistered, control-validated, causally specific full paper.** This report is a secondary read-only audit (no new model forwards).

## Reviewed artifacts and method

- Manuscript: `research/rounds/A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE/manuscript_draft_v2.docx`, Git blob SHA1 `f89e91ece8529a9de70626d355cdc92464af8e4a`; independently extracted and inspected 98 nonempty paragraphs of `word/document.xml`, including abstract, Sections 1–7, Tables 1–2 and references. The reviewed title is *Missed When Added, Recognized When Present: A Preregistered, Oracle-Validated Counterfactual Audit of Appended-Conflict Recognition in a Security-Typed Language-Model Scorer*.
- G3 native `G1C_REAL_20261025/raw_native_logits_109_requests.jsonl`, Git blob SHA1 `7a55817abea0f15a4162b620a412a18564b315f4`: 109 real native inference rows (26 old, 26 treatment, 26 N1B, 6 N1, 9 SA, 6 TS, 6 RO, 4 replay).
- G3 `G0C_REAL_20261025/pair_rows.jsonl`, Git blob SHA1 `8de45fc200d0e37be676f172d844b3ab2c6c23c7` (79 edits); `token_audit.jsonl`, SHA1 `2c5b932ae9e36d5e5380eff558f0437424a39261` (79).
- G3 `G2C_REAL_20261025/per_pair_heads.jsonl` SHA1 `e33e75ae24816768661bb99bc52ae501356114c5` (26 pairs); checked against independently parsed logits and Gold.
- G3 frozen `research/experiments/2026-10-25_A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE_PROTOCOL_V1.json` Git blob SHA1 `993628d0e8c566453681af0fbcbd2b571c0bb653`; checked-in CPU generator `A461_g3_conflict_gate_cpu_v1.py` Git blob SHA1 `b62b9996c3daa46b578af9b22bc9252bfb061906`.
- Related independent raw-data audits: `research/analysis/2026-10-25_A461_G3_post_execution_independent_evidence_contract_audit_v1.md` and accompanying JSON (commits `3c559a7`/`a66493d`).

External literature rechecked: Tang et al., *Do Language Models Track Entities Across State Changes?* (ICML 2026, https://proceedings.mlr.press/v306/tang26ah.html); SecJev (https://arxiv.org/abs/2610.03073); *One Word Opens the Gate* (https://arxiv.org/abs/2610.12292); LGMT (https://www.sciencedirect.com/science/article/pii/S0950705126010506). This verifies substantial overlapping *methods/phenomena*, not an exact duplication of the specific appended Streamlet conflict experiment.

## What is valid

1. **Actual G3 real data exist:** G1C reports 109/109 FP32 native forwards and 4/4 bit-identical replay; G0C and independent verifier have PASS receipts; data are committed. This is not a paper-only or CPU-only result.
2. T2 has 20 previously untouched run groups, 1 T2 experiment per group; recognition in clean-old→conflicted sense is 1/20 overall, and 1/17 conditional on initially correct old C=false. Treatment-new C=true without initial-state qualification is 4/20 because 3 other arms had false-positive C=true already on the clean old arm (run211/run212/run328).
3. T3 six examples, each new C=true, but two T3 groups also appear among the twenty T2 groups and T3 starts with existing conflict. Correct T3 actions are 4/6; two show action-integrator inconsistency.
4. The observations plausibly support a narrower publishable *behavioral case study*: a specific security-typed scorer frequently misses policy-relevant cross-message conflict under lawful appended evidence, despite successful reading of some pre-existing conflicts. Internal circuit causation, deployment significance and transfer are **not shown**.

## Blocking findings / mandated manuscript edits

### P0 — False assertion of fully matched/legitimate neutral controls

The manuscript Abstract, §3.4, Table 2 and §5 state N1B author-swap neutrals are token-matched for every pair and support excluding form/author confounds. Direct pair+token+validator-set audit:

| Subset | matched and legal | denominator |
|---|---:|---:|
| T2 wait→reject | 10 | 10 |
| T2 accept→reject | **3** | **10** |
| All T2 | **13** | **20** |
| All T2+T3 | **19** token matched | **26** |

The seven invalid accept N1B rows (run140, 212, 283, 328, 330, 337, 351) substitute `z_neutral_outside_set`, outside `validator_set`, and are **not treatment-token-count matched**. Their oracle Gold is invariant because that message is not a recognized validator, not because it is a valid fresh-validator vote. Both contract defects must be disclosed; invalid rows cannot contribute to the strict matched-author comparison.

Among the 13 genuinely valid/matched T2 pairs, treatment and N1B C predictions are actually identical **13/13**, despite opposite Gold C labels: for N1B C=false and treatment C=true. The model is failing to differentiate semantic states, not successfully distinguishing semantics from formatting. Among those 13, 12 have clean old C=false; 11 also have a correct neutral C=false; **0/11** new treatment C becomes true. The single clean old C false→true pair run338 has **neutral C=true incorrectly** even though its neutral is valid/token-matched; it is not a clean semantic-specificity success. State these as exploratory subgroup observations, not newly preregistered confirmatory tests.

### P0 — SHAM chronology breaches and incomplete counterfactual coverage

All **6/6 SHAM_TS** and **6/6 SHAM_RO** arms have `received_messages` that are not nondecreasing in `received` (timestamp order), contradicting a validity criterion enforced on the input corpus by the generator. The former adds a message with earlier received time at the end; the latter reverses message order. Their oracle Gold can remain the same while input source/format contract is invalid. They may be reframed as **out-of-distribution format stress tests**, never valid same-source chronology-preserving controls. Moreover 9/9 SHAM-SA are in T2 wait cell, zero in accept cell; and all 6 N1 state-token SHA values match their corresponding N1B exactly, so N1 does not provide independent control variation. The §4.2/§5 claim that token-length, author identity, arrival time and order factors are ruled out is **not supported**. Also TS/RO preserve the *treatment Gold* rather than the old Gold; distinguish treatment-format perturbation from Gold-invariant neutral relative to baseline.

### P0 — Baseline correctness is mislabeled in Abstract/§4.3

Manuscript: “3/20 rejection, below persist-at-old-decision baseline (16/20 would be correct by doing nothing)” and “majority-class baseline 10/20”. Checked G2 script's 16/20 counts **new model predictions equal to old Gold** (model under-response); it does not compute old-decision predictions' correctness on new Gold. All 20 T2 source Gold actions change to reject_conflict; a policy that truly persists the old Gold actions scores **0/20** on new Gold. The 10/20 is merely the old-Gold class distribution, not an independently evaluated new-state classifier baseline. Remove comparative claim, relabel 16/20 as *persisting old prediction / equals old Gold* and provide meaningful baselines evaluated on same new Gold, disclosing degenerate class balance: constant reject scores 20/20 on all deliberately conflict-created new arms (not useful as a deployable baseline).

### P1 — Fisher exact: nominal arithmetic okay, causal/comparability and independence not

The nominal two-sided Fisher exact test on `[[1,19],[6,0]]` is indeed `p=3.0404e-5`. However the numerator in T2 is an old C=false→new C=true *transition*, while T3 counts new C=true on already-conflicted states; the estimands differ. Two T3 run groups overlap T2 (20+6=24 distinct groups, not 26 independent observations); moreover they originate from nonidentical old states. Removing the two overlapping T3 groups leaves 1/20 vs 4/4, nominal Fisher `p=4.7054e-4`, but source/baseline imbalance persists. Alternatively comparing the same *new C=true* outcome yields T2 4/20 vs T3 6/6 and `p=9.1213e-4` (still observational and confounded). Predeclared contrasts must use consistent binary endpoints, appropriate group-aware uncertainty and proper qualifiers. For 1/17 clean-old recognition, two-sided exact 95% Clopper-Pearson interval ≈0.15%–28.69%; for T3 6/6 ≈54.07%–100%. Claiming “properly powered confirmation” lacks an a-priori power calculation; prefer “independent-group confirmation sample” without implying generalization to TEST or other models.

### P1 — `evidence_level` normalization code error

`A461_g3_g2c_analysis_v1.py` `norm()` maps string `"0"` and `"1"` into booleans and leaves `"2"` as string; comparing against Gold integer `2` wrongly marks all correctly predicted level-2 outputs as incorrect. Direct original logits parsed with integer casts restore new-arm E accuracy: T2 wait 0/10; T2 accept **1/10**; T3 **4/6** (G2 per-pair logged 0/10, 0/10, 0/6). Update aggregate, all affected narratives/tables and scripts; preserve old incorrect artifact and add signed erratum.

### P1 — Frozen 106-forward stage vs real 109-forward run; generator mismatch

Frozen G3 protocol V1 sets stage forward budget **106** (absolute cap 128). Current GitHub G0C constructor `SHAM_CAP=6` emits no more than 6 SA, 6 TS, 6 RO, and thus at most 106 planned old+edit+replay forwards. Real G0C has **9 SA**, G1C used **109**; admission receipt asserts 109 had been frozen in V1, but V1 is 106. Genuine real model results are unaffected, but exact executed source is not derivable from the checked-in constructor; provenance/chronology and preregistration claims in §3.2/§3.4/§7 must be reconciled or qualified. This does not mean exceeding the 128 absolute cap; it does mean the stage's preregistered 106 number was not followed. Do not rewrite history to conceal it.

### P1 — “Relational-binding failure” is a mechanism hypothesis, not an established mechanism

No hidden-state or pointer-path localization, bidirectional activation patching, source-message attribution, or cross-model replication. Behavioral contrast cannot establish that model “represents conflicts already present but fails to bind appended votes to author–block–round relation” as a causal architecture fact; especially since 6/6 T3 starts with conflict, old state differs, and two T3 actions are wrong despite C=true. Rephrase as “behavior consistent with a relational evidence-integration failure” and preserve independent head/action errors.

## Literature contribution screen

SecJev already provides the security scorer, typed output interface and Streamlet scenes; Tang et al. (ICML 2026) already provides multi-operation state tracking and concrete mechanistic evidence for failures; LGMT provides logic-grounded metamorphic evaluation, and One Word Opens the Gate scrutinizes typed decision guardrails plus deterministic policy ceilings. A461 has a *potential specific delta*: source-local oracle-checked **Gold-changing** appended evidence in a security rule with separate C/Q/A readouts, old-C-clean conditioning and format/author controls. No strong claim of first discovery or new white-box internal mechanism follows without additional novelty comparisons and clean controls.

## Reviewer decision / submission tier

- **Not ready as submitted** for a strong full-length peer-reviewed security/ML paper; multiple P0 incorrect claims in abstract, results and method.
- **Potentially viable as a carefully qualified exploratory workshop/short empirical case study** after factual corrections and adequate discussion of source/protocol constraints. No acceptance odds estimated.
- **For a mechanism-centered full paper**, repair G3 controls and provenance and preregister a *new* source-contract-valid matched/factorial confirmation on truly fresh run groups, plus independent head-to-action analysis and bidirectional white-box intervention. The same old Gold and new Gold must be the target for baselines; hold author/timing/order valid and match rendering length/position as feasible; report nested source groups and conditional recognition explicitly. If the task is only a measurement-method paper, demonstrate methodological benefit across further model/scene axes rather than claim neural causation.

## Next exact task and gate

Name: `A461_G3_POSTHOC_SOURCE_AND_METRIC_ERRATUM`. **No GPU required** to begin. Must fix P0 manuscript fact errors, publish the corrected per-arm report/neutral match roster and E integer parse, reveal actual executed generator/hash and 106-vs-109 chronology, publish conservative descriptive sensitivity analyses, then independently audit manuscript v3. Thereafter name/freeze a *new* confirmation or causal experiment only following new prior-art G−1 gate, power and source-contract validity check; new GPU work is not represented as done.

### Bottom line

**Real and meaningful observed behavioral phenomenon, but the manuscript's present “complete paper-grade” inference does not survive primary-source audit.** The right verdict is **MAJOR REVISION**, not “no result”, not “proven new internal mechanism”, and not “ready for submission”.
