# A461-MECH-M1 R1 — round-binding transplant test (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. Standing GPU authorization (policy V2); 498 kev-4B forwards.
**Parent:** G1.0 (`../A461_MECH_G1_RELATION_MATCH_CPU_GATE/G10_RESULT_V1.md`, fd79903). G1.0 was NOT_ADMITTED for its full 3-cell plan; this is a **new, narrower design** that uses only the cells G1.0 showed constructible (ROUND, OK_ALT: 14/14 groups, 8/8 hosts). It is not a rescue of G1.0, and NONSUP stays unavailable.

## Question
At L11, does the repairing append-span state carry a relation that the donor computed in context, or a generic "vote for another block" state?
- **H-REL:** the relation is that this vote conflicts with the same author's vote in the candidate round.
- **H-CLS:** any vote for another block produces a generic state.

## Pins
| item | value |
|---|---|
| freeze script | `A461_mech_m1_freeze_v1.py` |
| manifest blob | `8c92e36a700721bd0a1de7ef588302f1c5b4f686` |
| design blob | `f3852efc21e7b55fdc1b7370a867454730422913` (holds the coded rules below) |
| runner blob | `91db323cb75975554d6eb97f49aaf14e25547278` |
| self-test | 14/14 PASS (`M1_SELFTEST_R1/`) |
| analysis | `A461_mech_m1_analysis_v1.py`, written before the run |
| inputs | roster `1bc84bf5`, K-C design `cd4cd9e5`, K-C raw `19d3a06c`, G1.0 counterfactuals `06ee06d7` |
| model | kev-4B, runner module `f118ea59` |

## Design
- Units: the 14 K-C replication donors × the 8 K-C hosts; 104 cross-group cells.
- Patch site: L11, all question rows, written into the host's own new span.
- Captures (all 32 layers): donor new, donor ROUND, donor OK_ALT, host new.

| arm | patch source |
|---|---|
| main | donor new span; must replay K-C bitwise |
| round | donor ROUND span (round changed only; rule Gold: no conflict; ~1 token differs) |
| okalt | donor OK_ALT span (author → another supporter; still a conflict) |
| doserand_r | dose-matched random at the ROUND span's per-position distance |

## Rules
The rules are coded in the design JSON, field `preregistered_analysis`.
- **P0:** main patches and the donor/host new captures must be bitwise equal to K-C. The runner fails closed otherwise.
- **D:** each donor's own ROUND/OK_ALT readouts are reported first.
- **H-REL:** J_round ≤ ¼ J_main, AND dM_main > dM_round in ≥ 75% of cells, AND that holds in the majority of cells for ≥ 10/14 donor groups.
- **H-CLS:** J_round ≥ ½ J_main AND dM_main > dM_round in < 60% of cells.
- **Verdict:** REL_SUPPORTED if H-REL holds; CLS_SUPPORTED if H-CLS holds; otherwise GRADED_INTERMEDIATE.
- **Role:** J_okalt ≥ ½ J_main → ROLE_ABSTRACT; J_okalt ≤ ¼ J_main → AUTHOR_IDENTITY_SPECIFIC; otherwise INTERMEDIATE.
- **Always reported:** round vs doserand_r, leave-one-donor-group-out, per host, stratification by donor ROUND self-recognition, and all nulls.

## What each outcome would and would not show
- **REL_SUPPORTED:** the repairing state depends on the donor having bound the vote to the candidate round. It argues against a generic other-block prototype at the patch site (it rules out the H-CLS variant tested). It does **not** identify where that relation is read (that is M2) and does not prove an exclusive encoding failure.
- **CLS_SUPPORTED:** the repair does not need round binding. "Recognition" in the earlier source-category contrast would then be a recognition of form, not relation.
- **Confound:** if kev-4B's own donor forward still flags ROUND as a conflict, the round arm tests a "recognised-but-invalid" state. The stratification reports this.
