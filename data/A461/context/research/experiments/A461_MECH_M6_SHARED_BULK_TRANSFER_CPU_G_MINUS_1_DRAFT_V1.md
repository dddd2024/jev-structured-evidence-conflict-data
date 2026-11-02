# A461-MECH-M6 | Shared BULK transfer and native specificity — CPU G−1 design draft V1

**Status:** DESIGN_DRAFT_ONLY. Not a frozen preregistration; no GPU admission, no runner, no quota allocation. This is the next mechanism-focused candidate after M5 R1. Do not overwrite M1–M5 frozen outcomes or run new GPU based solely on this draft.

## Grounded M5 baseline (2026-10-28; authoritative immutable result)
- Source: `research/rounds/A461_MECH_M5_MAGNITUDE_DIRECTION_GPU/M5_RESULT_R1.md` and `M5_ANALYSIS_R1/m5_analysis.json`; actual GPU receipt `M5_GPU_R1/execution_receipt.json`.
- 2,540/2,540 physical forwards in 20 batches; 208/208 full rows bitwise equal M3; class contribution and per-position norm-match gates passed.
- S(full)=51/104, S(only_BULK)=39, S(drop_BULK)=4, S(dir_BULK)=48, S(dir_RAND)=1, S(xdonor_BULK)=51; frozen verdict `BULK_DIRECTION + XD_HOLDS`; 14/14 leave-one-donor-group-out verdicts hold.
- `BULK = OTHER_ITEMS + CONTEXT`; it accounts for a median 0.787 of full-delta norm, cosine 0.779 with full delta, so 'BULK direction' is not an isolated semantic circuit.
- **Do not write 'same 51 cells transferred':** xdonor and full both have aggregate S=51, but per-host S differs (e.g. host 2c9118bb: 5→4; host 75642418: 7→8). Third donors were all selected from repairing donors and third-donor assignments are clustered.
- 104 cells reuse 14 donors and 8 hosts (each host 13 cells). Donor-only LOGO is not unseen-host replication; existing `research/literature/A557_20261029/A557_M5_crossed_host_dependence_audit.md` illustrates the fragility of group-only SPEC under a hypothetical perfectly host-correlated null. Its exact null count is NOT a measured p-value.
- A single seeded matched-size random direction gives S=1. This excludes that tested null, not the full random-direction distribution. Negative labels for PARTNER/SELF at very large scaling alpha are weaker evidence because of off-manifold intervention.

## Scientific question and falsifiable alternatives
Does a **shared, low-dimensional, round-conditioned donor-like L11 context-read component** explain transferable repairs, or is the M5 effect a host-/donor-dependent combination or a nonspecific refusal/readout artifact?

- H_shared: a vector or low-rank subspace trained on *disjoint donor groups* can produce source-specific rescue on *unseen hosts*, while an orthogonal matched-norm null cannot.
- H_conditional: the effect requires host- or donor-specific geometry, so a global mean/PCA basis fails or is brittle on held-out hosts.
- H_generic: any appropriately scaled broad attention/readout perturbation changes typed rejection, also on legal no-conflict Gold; then the 'conflict-reading' explanation is falsified.
- H_native: if a shared candidate is also necessary in the **native, unpatched model path** (not only sufficient when imported), targeted removal should selectively damage true conflict judgments; absence of this test precludes a native-path necessity claim.

## Literature / novelty gate before freeze
1. `TrustJev` (Xu et al., arXiv:2610.34826, 2026-10-26) already compares Jev/Kev/SecJev and supplies a policy–evidence defense; do not claim generic policy/evidence separation as new.
2. `MIB` (Mueller et al., ICML 2025, https://proceedings.mlr.press/v267/mueller25a.html) requires precise causal path/variable recovery, not merely steering success.
3. Mean-difference activation steering and refusal vectors are established techniques; e.g. Henniger et al., ICML 2026 Mech Interp Workshop (https://openreview.net/forum?id=qSmUharVw6), and `Causal evidence that language models use confidence to drive behaviour` (Nature Machine Intelligence, 2026; https://www.nature.com/articles/s42256-026-01293-x). Therefore a successful mean-BULK vector **alone is not paper-level novelty**.
4. Refresh sources and log exact paper claims before freezing; keep this an *identification/falsification* experiment.

## CPU G−1: required, no GPU
- Independently re-read original M5 per-cell raw logits, the 104 cell manifest and the frozen M5 analysis; produce a cell-level table identifying overlap, symmetric differences, true-conflict Gold and each host/donor/source id. Audit the M5 formal S and SPEC calculation without changing M5.
- Reconstruct source-specific `BULK` from captures under `~/wjc`, with model identity, span width=31, token IDs, head/position alignment, key-class reconstruction and hash checks. No private captures need be committed; record reproducible manifests/SHA and reproducible CPU summaries.
- Search the unused DEV corpus for **independent held-out host/source groups**, with verified Gold conflict and legal no-conflict cases; require no scene/group leakage into direction learning, hyperparameter choice, third-donor selection or final evaluation. If none qualify, STOP `NOT_ADMITTED_NO_INDEPENDENT_HOLDOUT`; do not treat 104 reused cells as a new validation set.
- Construct train-only donor-group splits and *source kind* labels (new vs ROUND). All PCA ranks, directions and norms come from training groups only; test donors/hosts are invisible during fitting. Precompute angle, norm, singular values and between-host heterogeneity.
- Gold-negative control must test legal, no-conflict cases, as well as true-conflict cases and the typed readouts (`conflicting_vote`, `certificate_action`). A simultaneous increase in false veto is a mandatory failure signal.
- Validate runner/analysis dry-run including exact per-position norm matching, sign reversal, no-op/sham, multi-seed random null, fail-closed numerical gates, input digests, and native no-patch identity before formal prereg. Fix a hard GPU forward cap only **after** matrix and case counts are frozen.

## Proposed GPU contrasts if G−1 PASS and independently preregistered
1. **Positive anchoring:** original donor-BULK, full L11 donor write, untouched host, identical/sham patch; reuse M5 anchors where exact inputs match.
2. **Transfer:** training-donor *mean BULK* per source kind substituted into held-out hosts, with geometry `mu_B(source,train) − B_host`; optionally matched-norm and unscaled variants. Never train on the target host/heldout group.
3. **Low rank:** prechosen PCA subspace(s) of training-donor BULK representations, ranks selected on training data, with identical matched-norm conditions; do not pick best rank on holdouts.
4. **Null/contrast:** host-own mean, source-kind swapped mean (ROUND on new, and vice versa), negative direction, multiple independently seeded matched-norm isotropic and covariance-matched controls, and an equal-dose unrelated-direction control.
5. **Native necessity/damage if technically identifiable:** remove/project out the frozen candidate from *native* L11 context write in already-correct host inputs; compare against norm-matched orthogonal removal. Keep sufficiency and necessity claims separate.

## Frozen *later* decision gates must discriminate
- Primary: **joint correct conflict readout and typed action** on unseen host/source-group Gold, with paired new-vs-ROUND contrast; not generic 'reject' frequency.
- Report paired per-cell effects but analyze by donor AND host clusters, with per-host plots and leave-one-host-out **and** leave-one-donor-group-out. Do not claim an iid n=104 p-value; only use exact randomization tests after justifying exchangeability.
- **Kill shared low-rank hypothesis** if it fails held-out hosts, if source-kind swap acts equally, or if matched controls produce similar effects.
- **Kill selective native mechanism** if negative Gold false-veto rises substantially, correct native decisions are indiscriminately damaged, or only donor-injection sufficiency is observed without native-path loss.
- Pre-register exact S/SPEC thresholds, independent units, seed list, dose range, alpha/off-manifold limits, Gold harm thresholds, and null multiple-testing treatment *before* GPU. No retrospective threshold changes.

## Scope and sequence
Current state: M5 **experiment completed**, M5 **final paper-level audit not requested**; this M6 document is a CPU-design draft, not an experiment execution or independent empirical validation. Priority: CPU G−1 and design review → frozen prereg and budget gate → eligible GPU run → independent scoped result audit. Keep all server files under `~/wjc`. Second-model (SecJev-0.8B) replication follows after a well-identified transferable mechanism rather than substituting model count for causal identification.
