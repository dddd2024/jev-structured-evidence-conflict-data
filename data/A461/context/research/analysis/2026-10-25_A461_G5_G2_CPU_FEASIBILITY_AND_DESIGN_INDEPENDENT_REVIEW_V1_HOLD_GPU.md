# A461-G5-G2 independent review: CPU constructibility PASS, GPU-design admission HOLD

**Date:** 2026-10-25. **Verdict:** `PASS_CPU_CENSUS_CONSTRUCTIBILITY_ONLY / REVISE_DESIGN_HOLD_GPU`. No GPU, no new model forwards, no new authorizations. Request: [Issue #2 CPU report 6399989194](https://github.com/dddd2024/jev/issues/2#issuecomment-6399989194). Baseline commit `b11f8caf6ab88ae65f4ec06da23dbb4ae45548ad`.

## Exact audited files

- CPU program `research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/A461_g5_g2_cpu_feasibility_v1.py` Git blob `0c0236b8208515b96491781bfe0ae01838902a07`.
- Result set `G2_CPU_FEASIBILITY_REAL/constructible_scenes.jsonl` blob `b3bd01b21ee0cd8215209b1130a931fef962b22a`, `scene_reuse_ledger.json` blob `a682ef3780eb34a7353af00d5a1fc0b2d3b2eeec`, `constructibility_inventory.json` blob `8c1b8be24eb42d46f1adb9ac888c42b663bb4d44`.
- GPU-design draft `G2_CPU_FEASIBILITY_REAL/g2_design_draft.json` blob `94fdfd295ed28ed9b20e503570ea2083f204cfcb`; receipt `execution_receipt.json` blob `3117d121cfafb94579afcc3da3f892d8cc1b5bf1`.
- G3 cohort census `A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE/G0C_REAL_20261025/census.json`; corrected G5 donor search V2.

**Method:** source/receipt and **all 189 candidate rows** independently parsed from GitHub and cross-tabulated with the **84 used-scene ledger entries**; source-audited gating and forward budget. No independent execution on actual DEV corpus/server during this review.

## What passed

- Archived census reports **797 DEV scenes**, **84 unique historical used-scene SHAs**, and **713 scene SHAs not reused**. Historical used entries span **all 42 known run groups**.
- Source output contains **189 oracle/chronology-legitimate constructed candidates across 30 groups**, with **163 accept / 26 wait**. This is useful CPU *construction* headroom, not verified native forward eligibility and **not** confirmed model-recognized donors.
- When conditioning on `same_width_block_available=true`, there are **180/189**, across **28 groups**, **155 accept / 25 wait**. If excluding the three G5 pilot groups (run83/114/182), there remain **172 eligible block-width candidates across 26 historical groups** (**149 accept / 23 wait**). Such scenes are fresh but their groups are **not** fully untouched historically.
- Draft proposes the important *scientific* additions: donor-side matched SA-sham/position permutation/norm-matched activation; restoration-side norm quantification; independent source selection and nonindependence disclosure; distinct later K/Q component attribution gate. All scientifically justified as **design choices**, not novel patching method claims.

## P0-A: qualification prior denominator excludes the wrong cohort

CPU source lines **28–30** hard-code `QUALIFIED_OBSERVED = {G3_confirmation: {pairs:26,qualified:1}, G5_V2_search:{pairs:36,qualified:1}}`. G3's 26 consist of **T2 appended-conflict: wait 10 + accept 10**, plus **T3 already-existing-conflict contrast: 6** (G3 census). T3 are not opportunities for *new appended recognition*. Thus `p=2/62` is not a commensurate empirical rate; at the unfiltered **descriptive T2 construction** level, numerator/denominator are `2/(20+36)=2/56≈3.57%`. The actual **strictly qualified** positive-donor criteria and eligible clean-baseline population differ between rounds and cannot necessarily be pooled at all. A conservative G5-V2-specific planning rate is `1/36` (uncertain, not a known rate).

Even treating `p=2/62` as an unrealistically stable independent Bernoulli rate, n=62 gives **E[K]=2** but **P(K≥2)=59.84%**, not a guarantee of ≥2. The (non-binding) binomial n for 95% chance ≥2 is **~146** under that favorable assumption. Under `p=2/56`, n=56 has the same approximate 60% issue. With uncertain rates and clustered run groups these probabilities are only illustrative, **not inferential power analysis**. The 189-candidate construction set **cannot guarantee** 2 qualified donors. Recompute p by matched eligibility strata; freeze a discovery batch schedule and a stop/fallback rule for zero/one donor, not only an expectation threshold.

## P0-B: 189 `constructible` are not 189 same-width admission candidates

CPU source lines **230–239** computes `same_w` from **standalone block-token length** (`tlen(block)`) and **falls back to a different-width block when `same_w` is empty**; source lines **249–259** sets `constructible=ok` without requiring `same_w`. Hence 9/189 candidates are not same-block-width; direct source rows confirm **180** have the width flag, not 189. Moreover `tlen(block)` alone is **not identical** to proving actual **fully rendered native request-token span equality**, suffix identity, and four typed question row alignment. Require G0 style full-request native tokenizer checks for each admitted donor/host three-arm roster, not standalone block-width approximation.

**Fix**: split census `oracle_legal_constructible=189` and `prelim_equal_block_width=180`; adopt `n <= 180` as the max preliminary aligned pool before further true native token gate; report wait/accept separately; never promote these to qualified donors without native model reads.

## P0-C: `source group` independence is currently mislabelled

Source ledger `used` spans **all 42/42 historical run groups**, while all 30 constructible groups (and all 28 width-matched groups) are contained in this historically-used set. In particular, *zero* totally unseen-run-group examples exist in the archived 797 DEV scene universe. This does **not** invalidate using *new scenes*, but cannot support `independent unseen source-group validation` relative to the entire A461 research archive.

- For a **limited held-out-scene within historical groups** replication, define exact donor/host disjoint groups and analyze/cluster by run ID; avoid claiming `new unseen groups`.
- For **strong new source-group replication**, obtain independently generated run groups outside the 42 existing groups, and hold them out of screening/protocol tuning. Existing DEV alone cannot satisfy that stronger claim.
- Relative to **G5 pilot groups only**, the CPU records can still supply the 172 preliminary equal-width candidates across 26 other groups; **clearly label this narrower notion**.

## P0-D: claimed patching-forward budget omits treatment conditions

Design draft `budget_formula_dynamic.per_config` declares `F(H,L)=4+5H+5HL` and explains `5HL` as `(2 restoration controls + 3 suppression controls) × H × L`. But **controls are not interventions**: this counts the 2+3 negative controls without the **main restoration treatment** and the **main suppression treatment**; draft separately promises a **restoration-side norm-matched random control**, also uncounted in its parenthetical. The calibration `G1=28=4+5·2+5·2·2−(norm controls absent)` is not an explicit physical-call trace and cannot certify the new plan.

A conservative **illustrative lower bound** under draft's own stated baseline capture list is
`3 donor captures + 1 donor baseline + 4H (host baseline, two captures, identity) + 8HL`:
- restoration: actual donor NEW → host SA + SA-sham + permutation + restoration norm matched = **4 conditions/host/layer**;
- suppression: actual host NEW → donor NEW + donor-side SA-sham + permutation + norm matched = **4 conditions/host/layer**.

So illustrative `4+4H+8HL`: **H2L2 = 44** (not 34), **H4L2 = 84** (not 64), **H4L3 = 116** (not 84), **H6L2 = 124** (not 94), *before* any additional distinct layer identity capture/control forward or QC baseline. Those values are **not a substitute authoritative budget**: only an enumerated, frozen, traced 1:1 planned `model.forward` list with stages/conditions/targets/layers/physical counters may establish admission.

### Separate unbudgeted donor discovery stage

Finding 2 new qualified donors **requires model inference**; CPU constructibility does not determine recognition. Even a proposed 62-pair 3-arm (old/new/SA) qualification scan means up to **186 native forwards**, already above the **128-per-run cap** and separate from patching. Screening all 180 preliminary width candidates at 3 arms is **540 forwards**, which would require stage-scoped, authorized, independently reviewed batches. Freeze screening rows, eligibility, early-stop semantics, pilot/confirmatory separation and per-batch budget; do **not** silently charge this work to patching `F(H,L)`.

## G2 admission path and stop conditions

1. **Keep CPU source census receipt PASS** (constructibility only), preserve all original rows. Create a versioned `G2_DESIGN_V2` clarifying 189 versus 180, independence definition, G3 T2+T3 stratification and probability caveats.
2. **Explicitly separate phases**: donor **GPU discovery** (new permission and max 128 per execution; 3-arm identification, frozen batches, fail-closed) and **GPU causal intervention** (only after qualified new donor(s) and fresh per-host gold/native token gate).
3. **Generate exact condition graph/traced budget** for both intervention directions and all four per-direction conditions, identity and all captures; preserve signed C-margin, classifications, off-target row integrity, seeds, norm matching, and the matched host/source schedule.
4. **Predefine replication endpoint and a real independence unit**: new scene within seen run group (weak) versus entirely unseen run groups (strong). Determine what will count as confirmation vs exploratory and do not reuse scene/source choices discovered on the same held-out confirmation group.
5. **No Key-only claims** unless a separate Pointer K/Q component-isolating experiment has passed its own controls. The draft's `Key-specific effect does not exceed cheap norm baseline` stop cannot serve as a Key-specific mechanism test without a Key-component intervention; scope it as a future separate experiment.

**Final:** `G2 CPU dataset feasibility = PASS at construction inventory level`, but **G2 GPU-designed protocol is NOT_ADMITTED**, with four independent P0 design blockers: denominator/selection power, width/native alignment, unseen-group interpretation, physical-call count (plus unsized discovery). Must fix with CPU-only amended plan and targeted re-review. Nothing here revokes the valid G5 pilot exploratory results or calls for rerunning G5.
