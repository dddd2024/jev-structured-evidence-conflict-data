# A461-G5-G2 Stage-A CPU freeze V3 — independent source/data and width-amendment review

**Date:** 2026-10-26. **Verdict:** `PASS_CPU_ACTUAL_TOKEN_GATE_AND_LEDGER / HOLD_UNADOPTED_WIDTH_AMENDMENT / NOT_ADMITTED_GPU`.

**Review request:** [GitHub Issue #2 comment 6419925145](https://github.com/dddd2024/jev/issues/2#issuecomment-6419925145).
**Submission commit:** `7061693c5e2f296713828e3d5bd7221a4c6d87d5`.
**Scope:** completed CPU Stage-A candidate/width inventory only. This reviewer **did not** connect to the GPU server, rerun the native tokenizer independently, load the model, or perform new native forwards. No experimental donors have been model-qualified.

## Frozen exact evidence

| Artifact | Git blob |
|---|---|
| `research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/A461_g5_g2_stage_a_cpu_freeze_v1.py` | `b3549652c0c2a062c2670ee19048085c3f01aa19` |
| `G2_STAGE_A_CPU_FREEZE_REAL/stage_a_candidate_roster.json` | `1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8` |
| `G2_STAGE_A_CPU_FREEZE_REAL/width_profiles.jsonl` | `2be1a05d817adbc6c1c86d23f8b20f64b4570b59` |
| `G2_STAGE_A_CPU_FREEZE_REAL/stage_a_batching_plans.json` | `ef549dd7cc1168238bf5c60e174a0bcd4be256d9` |
| `G2_STAGE_A_CPU_FREEZE_REAL/execution_receipt.json` | `0d9030daa11bc40e703c09dfa3683ef499442cd4` |
| Existing G2 V2 protocol `A461_G5_G2_DESIGN_V2.json` | `095838f18fdd98a5b282a12615d44c99dc2d31af` |

## Verified facts

- CPU receipt: `COMPLETE_A461_G5_G2_STAGE_A_CPU_FREEZE`; **172** tier-2 scenes checked, **23,329** reported CPU encodings, **0** model loads, **0** new native forwards, GPU blocked. All scene/width profiles present; main roster **172** entries and reported **0** gate failures.
- Independently parsed all 172 roster rows and all 172 width profiles. For every frozen row the selected `frozen_width` appears in `common_widths`, both new/SA full-request native-token length deltas equal that width, span lengths equal width, source group matches, and dynamic C row index is **1**. Both frozen treatment/SA events have matching `received` timestamps in **172/172**.
- The **previously mandated exact +34** criterion succeeds for **26/172 scenes**, covering **8** groups. This is a concrete and important empirical limitation; previous per-block-token-width feasibility **was not** a full native request token-alignment gate.
- Common width possibilities per scene: `W31=171`, `W32=1`, `W33=157`, `W34=26`, `W35=1` (nonexclusive memberships). Frozen **single selected** `frozen_width`: `W31=145`, `W32=1`, `W34=26`. These sets must not be confused.
- **Potential cross-group donor-host pairing if one may choose any later per-scene common width**: independently enumerated **27,148 directed candidate pairs / 650 directed source-group pairs**, matching archived summary.
- However **using the concrete already frozen single witnesses**, with no later choice or re-render, **only 19,622 directed cross-group candidate pairs** have matching frozen widths (`W31=19,068`, `W34=554`, `W32=0`). The 27,148 claim is **width-profile theoretical** and assumes an eventual per-width witness can be frozen/revalidated; it is not a count of immediately executable pairings from the present 172 single-witness roster.
- One roster scene `980ea36bac02c82d2425a6cd87519d49bf1d4ba909354ffa13af0d2f47d7dc95`, `run-231`, has widths **[32,35]**, uniquely among profiles: it has **no cross-group donor/host partner** in this pool and should be classified exploratory/unpairable for the current Stage-B design. Hence at most **171 scenes** have plausible Stage-B partner pool at current available widths, though all 172 can be semantically screened as construction records.

## Admission-critical interpretation of the proposed V2.1 per-pair common-width policy

**Conditional scientific design judgment:** Relaxing *the fixed numeric width* 34 to a **predeclared matched width W**, with W identical for donor NEW/SA and host NEW/SA and full exact native-token/suffix/branch checks, is **methodologically conceivable**. An arbitrary fixed width of 34 is not itself known to cause the security effect. However this is **a change in the frozen protocol's experiment condition**, and cannot be retroactively adopted merely to enlarge the sample pool. It must be preregistered before any new model-derived selection.

**P0-A: source-arm choice and model donor qualification must stay on exactly the same frozen witness.** The present `stage_a_candidate_roster.json` captures only **one** rendered, SHA-pinned old/new/SA triple per scene (`frozen_width`). The alternative widths in `width_profiles.jsonl` are **integers and existence flags**, not full per-width `declared_edit`, native token SHAs, first-divergence anchors and candidate reads. If Stage-A qualifies a donor using frozen W31 then Stage-B uses an untested W33 or W34 variant, **recognition/qualification does not automatically transfer**. This would select interventions after examining outcomes and introduce different prompt/time/length semantics. Resolve before approval in one of two ways:
- **Option A:** use the **current frozen one-witness roster as-is**; Stage-B only pairs contexts with exactly matching `frozen_width` (19,622 theoretical ordered cross-group pairs before donor qualification), keep W strata and drop current W32 orphan from confirmatory pairing; or
- **Option B:** if leveraging 27,148 width-profile pairings, build a **per-width frozen complete witness roster**, containing for each scene/W legal NEW/SA event messages and all full-request IDs SHA, exact span coordinates, suffix/branch invariants. Select the W-specific **donor qualification arm before or in separately accounted inference**, and *only* patch a W version for which the donor actually qualified and which has a matching host. Count every extra donor old/new/SA observation in Stage-A's forward budget. W-stratify outcomes and preserve pair provenance.

**P0-B: cross-source/scene independence remains limited.** All 42 historical DEV run groups were touched in earlier A461 work. Tier-2's 26 groups only differ from **the G5 three-group pilot**, not from the research line as a whole; no “previously unseen run group” or full external validation claim is permitted.

**P0-C: admission deliverables are still plans, not a GPU executable.** `stage_a_batching_plans.json` specifies N62/N93/N124/N172 primary calls plus per-batch replay counts but **does not freeze exact scene-to-batch order, three-arm request hashes and real executable physical-forward 1:1 trace**. The plan's arithmetic is correctly feasible as a cap estimate: N26 78+2=80 in one capped batch; N62 186+4=190 over two; N93 279+6=285 over three; N124 372+6=378 over three; N172 516+10=526 over five (each max 128, subject to how intact triples are arranged). The true run must have concrete ordered job queues, stable deterministic seed, per-batch admission and user approval, replay identity, exact physical prehook accounting and failure receipt. No GPU may be started from this review alone.
- The G2 V2 design `Stage-B F(H,L)=4+4H+8HL` assumes one donor setup; multiple donors must have separately traced capture/setup/identity and controls. `>=2` new donors is a later gate; it does **not** imply discovery is completed.
- Candidate treatment/SA witness `received` timestamps happen to match in all frozen pairs; a V2.1 per-W roster must preserve this matched-timestamp property, gold legality and the same canonical event semantics.

## Required smallest next action

1. Version and commit `A461_G5_G2_DESIGN_V2_1` explicitly choosing **Option A** (one frozen W per scene) or **Option B** (per-width full witness roster and W-specific inference). Preserve V2 and all original CPU outputs immutably.
2. Freeze the chosen Stage-A N, independent pilot-relative confirmatory/ exploratory group strata, scene-to-batch order and exact old/new/SA request identities; require **full native token hashes for the W actually tested** and 1:1 physical forward plan within <=128 **including replays**. Remove current orphan W32 from Stage-B-confirmatory pairing unless an additional truly width-compatible source outside the pool is provided.
3. Targeted independent **GPU-admission** review on the new protocol plus actual runner/roster/budget artifacts, then fresh user GPU authorization (Stage-A discovery only). Log strict donor verdicts and use no Stage-B patching unless its separate admission and donor threshold are met.

**Final judgment:** CPU Stage-A source/token-gate work is a meaningful, valid **completed CPU artifact**, and revealed real width constraints. The proposed V2.1 relaxation is **not yet admitted** without binding per-width donor recognition, source control equivalence and the exact executable request ledger. No new model-qualified donor, no Stage-B mechanism evidence, and no new GPU call. Existing G5 pilot science unaffected.
