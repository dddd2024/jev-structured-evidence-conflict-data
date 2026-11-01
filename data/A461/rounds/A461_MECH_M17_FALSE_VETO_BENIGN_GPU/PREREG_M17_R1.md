# A461-MECH-M17 R1: do the repairing L11 patches also make benign hosts reject? (false-veto control; preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Requested by the user on 2026-10-31 ("False-veto control"), after the M1–M16 consolidation (350fa77), where it was listed as the most informative open item. It runs under the 2026-10-30 grant and the standing GPU authorization (policy V2): 2292 kev-4B forwards in 18 batches (17 × 128 + 116).

## Question
- **What M1–M16 did:** every patch targeted host new, the conflicting scene. The source-matched round control showed that a non-conflict *source* does not repair.
- **What was never tested:** whether the repairing patches make a *benign host* reject. That is a false veto (standard V1 §2: "benign / no-conflict negative controls … so that repairing a missed rejection is not just a higher rejection tendency").
- **What M17 does:** it applies four of the repairing patches, unchanged, to three benign variants of the same 8 hosts. Each variant carries a 31-token appended vote at exactly the span of host new.

## Benign targets and Gold
For every host, the three variants differ from host new only inside the span (token-checked in the freeze). Their source-internal Gold is the same as the host's original scene: `accept` on 6 hosts and `wait` on 1fb5651c and 1c7158b6, with `conflicting_vote` false. `reject_conflict` is never correct on them.

| target | appended vote | source |
|---|---|---|
| SA | an existing vote sent again (duplicate) | roster `declared_edit_sa` (the Stage-A sham arm) |
| ROUND | host new's vote, with the round set to a non-candidate round | G1.0 counterfactual |
| OUTSIDER | host new's vote, with the author set to a non-validator | G1.0 counterfactual |

ROUND and OUTSIDER are near misses: conflict-shaped votes that the rule must not count. SA is a plain duplicate.

## Arms
All arms patch the L11 `o_proj` input at the 31 span positions in every question row, on all 104 cross-group cells. The sources are donor new (main) and donor ROUND (round).

| arm | patch | repair on host new (pinned rows): R = main rejects where host new did not |
|---|---|---|
| `full@T` | the M3 all-heads patch (the donor's own write) | 61 (M3) |
| `meanD@T` | the M6 pooled-donor BULK arm | 39 (M6) |
| `cs0@T` | the M8 common shift alone (contrast 0; main == round, so main rows only) | 39 (M8) |
| `abc05@T` | the M14 AB arm at s ½ (shift at 0–12 + 29–30, c at 29) | 39 (M14) |

- **Anchors on host new:** the four arms on M14's 6 subset cells, both sources (48 rows). They must equal M3, M6, M8 and M14 bitwise.
- **Captures:** 60 in all. These are the 44 of M1–M16 plus host SA and host OUTSIDER (16).
- **Classes of the benign captures:** host new's. Every key before the span is token-identical, and the span's field layout is checked.

## Research contract ([standard V1](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §2–§5)
- **Safety endpoint and level:**
  - The endpoint is the native typed `certificate_action` against source-internal Gold.
  - The primary measure is the false-veto count: benign targets moved to `reject_conflict`.
  - Level S1–S2: an artificial intervention scored on the native action. No deployment claim, and no attacker-reachability claim (researchers editing the simulator are not attackers).
- **What it adds:** the first false-veto measurement of the M-line, for the patches that carry Tier A (`full`) and Tier B (`meanD`, `cs0`, `abc05`) of the consolidation.
- **Mechanism question it also answers:** does the downstream re-check the L11 span's evaluation against the host's context, or apply it to whatever vote sits there?
- **Novelty delta:** small. Activation patching that overrides a decision is expected to be unselective. What is not known is whether this route's repairs are conditional on a real conflict, and that decides how the paper may describe them.
- **What the result decides:**
  - **`full` NONSELECTIVE:**
    - Tier A is reworded: the L11 span state is a carried verdict, applied downstream without a context re-check.
    - The repair is verdict injection, not the enabling of the host's own relation check.
    - The paper states the false-veto cost and makes no defence or diagnostic-use claim for the patch.
  - **`full` SELECTIVE:** the downstream checks the vote against context. That strengthens Tier A as a context-conditional evaluation.
  - **Pooled arms NONSELECTIVE:** Tier B is a threshold push. It is DOWNGRADED to "not conflict-conditional" (§3.6). `cs0` is expected to be nonselective, since M8 cs0 flipped main and round alike.
  - **Any outcome:** this ends the false-veto gap for these arms. No further M-line GPU stage follows without a new, decisive question.
- **What it cannot show:**
  - a natural mechanism;
  - effects on other benign kinds (insufficient-evidence scenes with Gold `wait` are covered only on 2 hosts);
  - generality beyond kev-4B and twins_streamlet DEV.

## Pins
| item | value |
|---|---|
| freeze | `A461_mech_m17_freeze_v1.py` (blob `96328ac9…`, CPU + tokenizer only). It checks the pins; that each benign variant equals host new outside the span; the span field layout; benign Gold ≠ reject and = the old scene's Gold; that the anchor and benign patch fields equal the pinned rows' fields (benign: all fields but the target); pools = M6's; the plan; and rows per arm. It computes the repair reference from the pinned rows |
| manifest blob | `8b3c015224e5725d7c8ac0b3849f657478d3649b` |
| design blob | `cc30174fae2a783d288455bc883a6b185f19a9d3`: rules under `preregistered_analysis`, benign Gold under `benign_gold`, repair reference under `repair_reference` |
| runner blob | `dee985df0a515d04c0f9d341912db433c320970a`. It is the M16 runner 2886a05c with the plan, pins and names changed; OUTSIDER encoded like ROUND; and patch targets allowed in (new, SA, ROUND, OUTSIDER). No patch field or numeric path is changed |
| self-test | `A461_mech_m17_selftest_v1.py` (blob `92da1360…`), result below |
| analysis | `A461_mech_m17_analysis_v1.py` (blob `97bc445e…`), written before the run |
| inputs | as M16, plus M8 raw / design, M14 raw / design and M16 raw / design |

## Rules (coded in the design JSON)
- **Readouts:**
  - M = conflict margin;
  - A = logit(reject_conflict) − max(accept, wait);
  - action = argmax;
  - JOINT = M > 0 ∧ A > 0.
- **FV(arm, T):** the number of cells where the main-source patch of T gives `reject_conflict` and T's in-run unpatched capture does not.
  - FV_round: the same for the round source.
  - FVJ: the same by JOINT.
  - FV_h: per host.
- **R(arm):** the same count for the arm's main-source patch of host new, from the pinned M3 / M6 / M8 / M14 rows on all 104 cells.
- **Per arm and T:**
  - **FV_NONE:** FV ≤ 5 and no host has FV_h ≥ 7.
  - **FV_AS_REPAIR:** FV ≥ R / 2.
  - **FV_PARTIAL:** otherwise.
- **Per arm:**
  - **SELECTIVE:** FV_NONE on all three T.
  - **NONSELECTIVE:** FV_AS_REPAIR on ≥ 2 of 3 T.
  - **MIXED:** otherwise.
- **Per responsive host (1fb5651c, 264c458d, 4bcbaf15) and arm:**
  - **HOST_UNINFORMATIVE:** R_h < 7.
  - **HOST_SELECTIVE:** every FV_h ≤ 1.
  - **HOST_NONSELECTIVE:** some FV_h ≥ R_h / 2.
  - **HOST_MIXED:** otherwise.
- **Consistency gate:** all of the following must hold, otherwise every verdict is INCONSISTENT and no claim is made.
  - The anchors are bitwise equal to M3, M6, M8 and M14 (12 rows each).
  - The 24 benign captures carry their frozen token sha.
  - Host new's unpatched action equals M1's.
- **Always reported:**
  - unpatched benign action against Gold;
  - FV, FV_round, FVJ, R, FV_h, R_h;
  - median dM and dA;
  - off-Gold changes of any kind;
  - the share of cells with A_main > A_round on benign targets;
  - leave one donor group out of every verdict.

## Self-test
- **R2 (`M17_SELFTEST_R2/`, 2026-10-31 15:54 +08):**
  - **16/16 PASS**, with runner, manifest and self-test unchanged, zero GPU loads, and 24 CPU threads.
  - The analysis dry run on fake logits exits 0. Every verdict is INCONSISTENT_WITH_M3_M6_M8_M14, as it must be.
- **R1 (`M17_SELFTEST_R1_FAILED_FAKE_NONDETERMINISM/`, 15:23): FAILED 15/16. Kept.**
  - **The failing check:** in the fake model, the first forward of the run (a donor-new capture) had a cross-row span difference of 3.4e-5, above the test's 1e-6 bound, and its logits differed from M16's fake run of the identical input by 1.8e-4.
  - **Why it is not a runner problem:**
    - The other 43 captures shared with M16's self-test were bit-identical to it.
    - The same capture gave 0.0 in all eight earlier self-tests (M10–M16).
    - It gave 0.0 again in R2.
    - The runner's capture path is unchanged from M16.
  - **Reading:** first-call numerical nondeterminism of the multi-threaded CPU fake model, not a runner defect.
  - **Protection on the GPU:** the runner fails closed unless the 36 M1 capture readouts are bitwise equal.
- **Decision:** R2 was a re-run of identical code, not a fix. The run is admitted on R2.
