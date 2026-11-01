# A461-MON-M22 R1: second-model replication of M18 on SecJev-0.8B (preregistered before any GPU forward)

**Status:** FROZEN; committed before the GPU run. This is part of the high-standard plan ("按照高标准的来", 2026-10-31). It answers A612 acceptance gate P1-4, which asks for at least a second frozen white-box model. It runs under the 2026-10-30 grant and the standing GPU authorization (policy V2): 620 SecJev-0.8B forwards in 5 batches (4 × 128 + 108).

## What is replicated
[M18](../A461_MON_M18_SPAN_MONITOR_GPU/M18_RESULT_R1.md) on kev-4B (c56729c) found:
- (a) the conflict is linearly decodable at the append span and at the decision position, even in the missed scenes, above the token surface;
- (b) the L11 span monitor is useful, but a generic last-token probe matches it;
- (c) whitening is blind and the native margins are weak;
- (d) the model false-vetoes about 5% of near-miss votes.

M22 runs **the same frozen design** on SecJev-0.8B:
- **Model:** Qwen3.5-0.8B base, the SecJev LoRA and the pointer head. It has 24 layers, full attention at 3, 7, 11, 15, 19 and 23, and hidden size 1024.
- **Scenes and arms:** the same 124 Stage-A scenes × old / new / SA / ROUND / OUTSIDER. The states, spans and token sha are those of M18; the tokenizer is shared and the 372 Stage-A token sha already match across the models.
- **Anchors:** the 372 old / new / SA forwards must equal SecJev's own Stage-A raw rows bitwise. The runner fails closed otherwise.
- **Layers:** residuals after SecJev's full-attention layers.
- **Whitening:** at L11 and at the last layer, L23.
- **Writer-head feature:** dropped. Heads 8–14 were identified on kev-4B and have no SecJev counterpart.

**What is not replicated:**
- **M1's round-binding transplant.** SecJev has only 4 strict donors in 3 source groups (Stage A), too few for the 14-donor design. Its Stage E / F results (joint repair concentrated in one donor; 0/48 for unrecognized sources) remain the SecJev evidence on that side.
- **M17 and M19 to M21.** These are intervention stages and would need SecJev-specific directions and captures. They are out of scope for this replication, and their results are stated as kev-4B only.

## Rules
The M18 rules apply unchanged except for the layer lists, and are coded in the design JSON:
- **Labels and sets:** as M18.
- **Split:** leave one source group out, with inner-LOGO thresholds at FV5 / FV1.
- **Probes:** the same spec.
- **Verdicts V1 to V3:** the same thresholds. G is the best *calibrated* generic detector among the last-token probes at every layer, whitening at L11 / L23, and the native A / M.

**Replication reading, fixed in advance:**
- **V1 ENCODED_AT_L11 + ABOVE_SURFACE on SecJev:** "the conflict is present but not acted on" holds on both models. SecJev's failure mode is different (55.7% false accept + 33.1% wait), so the agreement is informative.
- **NOT_ENCODED:** the H-READ statement is kev-4B only, and the paper says so.
- **V2:** the monitor's novelty status on SecJev, reported as is.
- **Natural false veto:**
  - SecJev's rates on all four benign arms, compared with its Stage-A 8.9% on old / SA.
  - The FV-calibrated monitor thresholds must be read against that higher base rate.

## Research contract ([standard V1](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md))
- **Level:** S2. The endpoint is the native action against source-internal Gold.
- **Generality claim:** two frozen white-box models of one family (kev) on one simulator family. This is not cross-architecture.
- **Not a new scene distribution:** the same 124 scenes. A612 asks for an "independent scene distribution re-test" as well, and that is not covered here. It is stated as a limitation.

## Pins
| item | value |
|---|---|
| freeze | `A461_mon_m22_freeze_v1.py` (CPU). It reuses the M18 design and manifest, re-anchors to SecJev's Stage-A raw rows (372/372 token sha equal) and sets SecJev's layers. A re-freeze reproduced both blobs byte-for-byte |
| manifest blob | `c06d08ad1ebf9268bde44fc73ac21db0439ca542` (620 rows) |
| design blob | `759a4c83a5f205d9c606094502a5be07a33792e4` |
| runner blob | `caf75530060b7981b744c27e3aee74d5a5ce79b0`. It is the M18 runner with three changes: the SecJev Stage-A runner module (g0_v4, b675e9d5) for identity, ledger and safety; SecJev's model load; and layers / names / pins. The hooks and per-forward body are unchanged |
| self-test | `A461_mon_m22_selftest_v1.py` (blob `d0b3d121`); result below |
| analysis | `A461_mon_m22_analysis_v1.py` (blob `5225412d`), the M18 analysis with SecJev's layer list and without the writer-head feature, written before the run. Its verdict lines are None-safe (see the self-test) |
| model identity | SecJev identity digest `5f62d083…` (g0_v4 `MODEL_IDENTITY`) |

## Self-test
**R1 (`M22_SELFTEST_R1/`, 2026-11-01 01:22 +08): 13/13 PASS**, with zero GPU loads and runner `caf75530`. It covers:
- preflight on the real 620-row manifest (token and span gates);
- the fake full path: 620 rows and 620 feature files;
- the saved last-token state after L23, times the fake head, reproduces the `certificate_action` logits (the PASS message says "layer 31", a stale string from M18; the code reads `L23`);
- the round token lies inside the span in 124/124 scenes;
- refusals: a tampered manifest, a tampered Stage-A raw row, an extra LM call, approval reuse, and the GPU admission gates (pre-model gate, tampered manifest, plan override, run outside the runs root).

**R0 (kept as `M22_SELFTEST_R0_FAILED_FAKE_HEADS/`): 9/13, FAIL.**
- **Cause:** a defect in the runner's check against the self-test fixture. The fake model is 16 heads × 4 wide, while the runner checked the L11 `o_proj` input width as SecJev's 8 heads × 256. The full path then failed, and three tests that depend on it failed with it.
- **Fix:** the runner reads the `o_proj` input width from the module. On the GPU it separately requires SecJev's width, 8 × 256 = 2048. The new runner blob is `caf75530`.

**Analysis dry run.**
- With the WIP analysis blob `db90bbcb` (commit 2beb2c1), the dry run on the fake logits **crashed** (exit 1, `TypeError` in the V1 line).
- The fake head picks `reject_conflict` in every row, so there are no MISSED and no BENIGN rows and the span AUROC is undefined. M18's fake data happened to contain both sets.
- **Fix, before this commit:** the V1 / V1-surface / V2 lines return `UNDEFINED` when a metric is undefined, instead of crashing. The thresholds and rules are unchanged. The new blob is `5225412d`.
- The rerun exits 0, and every verdict is INCONSISTENT, as it must be: the fake cross-row difference is 1.9e-6, not 0.
