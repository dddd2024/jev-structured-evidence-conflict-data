# A461-MECH-G1.0 — CPU gate preregistration (frozen before execution)

**Status:** FROZEN_BEFORE_RUN. CPU only: tokenizer loads only, 0 model loads, 0 GPU forwards.
**Parent:** `research_governance/JEV_A461_POSTPASS_MECHANISM_PRIMARY_ROUTE_20261027_V1.md` (M1), `research/experiments/A461_MECH_G1_CAUSAL_ROUTE_VS_ENCODING_CPU_GATE_V1.md`.
**Script:** `A461_mech_g10_cpu_gate_v1.py` (this directory). The output receipt records its SHA256.

## Frozen inputs
- Corpus `~/wjc/a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz`, SHA256 `2920e1c9…ca56`.
- Stage-A roster blob `1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8` (172 candidates).
- K-C design blob `cd4cd9e5632cfa1b8aa476b94a332e3705af2f0f`; K-C FP32 raw blob `19d3a06c27953b1f2b4dcd2770394d28741a69fd`.
- Helper module `A461_g5_g2_stage_a_cpu_freeze_v1.py` (oracle1/oracle2/encoding helpers), last commit `7061693c`.

## Part I — identity (blocking)
For each of the 172 roster scenes: recover the state from the raw corpus by `sha256(canon(state))`. Rebuild old/new/SA by appending the declared messages. Recompute both oracle implementations; they must agree with each other and with the roster. Re-encode all three arms; token-id SHA must equal the roster. The 22 K-C scenes (14 donors + 8 hosts) must pass every check; any failure is NOT_ADMITTED.

## Part II — single-field witness counterfactuals (blocking)
For each K-C scene, build appended-message variants. Each variant differs from the frozen conflict message in **exactly one field**; every other field stays identical. A variant is valid only if:
- its token delta equals the frozen width W;
- the trailing state suffix is preserved;
- the branch (question) token segments are identical to the old arm;
- both oracles agree on the designed Gold.

| cell | field changed | designed Gold |
|---|---|---|
| OK_ALT | author → another supporter | conflict, reject_conflict |
| ROUND | round → non-candidate round | = oracle_old (no conflict) |
| NONSUP | author → in-validator-set non-supporter | = oracle_old |
| LATE | received → > decision_time | = oracle_old (reported; OOD-flagged) |
| OUTSIDER | author → not in validator_set | = oracle_old (reported; OOD-flagged) |

Search order is deterministic: values sorted by closeness to the frozen value, then lexicographically. The first value that passes is used.

**Admission rule:** ROUND, NONSUP and OK_ALT must each be constructible for at least 10 of the 14 K-C donor source groups **and** at least 6 of the 8 K-C hosts. Otherwise the gate is NOT_ADMITTED, the failing cells are listed, and no cell is redefined. LATE/OUTSIDER do not count toward admission. The script reports a corpus census of late and non-validator messages to judge whether they are out of distribution.

## Part III — host-coordinate role audit of the existing K-C cells (descriptive, no threshold)
For each of the 104 cross-group cells, substitute the donor's appended message into the host's old state and recompute Gold (`gold_sub`). Record the role features in host coordinates:
- whether the author is in the host's validator set;
- whether the author is a host supporter;
- whether the round equals the host's candidate round;
- whether the block differs from the host's candidate block;
- whether the received time is within the host deadline;
- the number of span token positions that differ between the donor and host spans.

SPECIFIC_JOINT is computed as in the K-C prereg (main JOINT and neither SA-sham nor dose JOINT; C = M>0, R = logit(reject) − max(accept, wait) > 0).

**Interpretation rule, fixed in advance.** If the patched span carries a witness that the host binds in host coordinates, repairs should concentrate in cells where `gold_sub` = conflict. If the repair rates are similar in both strata, the effect does not depend on host-coordinate role validity of the transplanted labels. That is evidence against a pure label-binding account at the patch site, and it is compatible with H-CLS or a precomputed relation/flag state. This part is diagnostic: cells share donors and hosts, so counts are reported per source group and no test of independence is claimed.
