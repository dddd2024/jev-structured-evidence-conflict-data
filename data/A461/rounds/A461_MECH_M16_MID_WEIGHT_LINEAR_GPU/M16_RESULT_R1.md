# A461-MECH-M16 R1: result (is M14's lower AB threshold the linear readout of the common shift at the middle span positions?)

Reported in the order of the [novelty × security-value standard](../../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §9.

## 1. Experiment and receipt
**Run:**
- 2992/2992 kev-4B forwards in 24 batches (23 × 128 + 48); 0 denied; one model load; elapsed 4467 s.
- `bitwise_vs_m1`, `bitwise_vs_m3` and `bitwise_vs_m6: checked`.
- Raw blob `1d74b63ba7e24fa47f6fe2cac1b967a9f141706e` (sha256 45ab768c…).
- The run follows prereg 996483a under the standing GPU authorization, extended on 2026-10-30 to autonomous stage design and execution. The pre-model gate passed and is saved as `M16_GPU_R1/pre_model_gate_receipt.json`. There was a single ledger attempt, and the receipt reads `COMPLETE_A461_MECH_M16`.

**Files:**
- The run's `SHA256SUMS` (115 entries, captures included) checks clean on the server.
- The 27 non-capture entries also check clean on the local copy.
- The captures (102 MB) stay on the server under `M16_GPU_RUNS/ATTEMPT_R1/captures`.
- `M16_GPU_R1/SHA256SUMS` lists the 29 kept files, including the run log and the pre-model gate receipt.

**Analysis:**
- Script: `A461_mech_m16_analysis_v1.py` (blob 7950fce0, frozen before the run).
- The server launch script ran it automatically after the receipt read COMPLETE (exit 0, 2026-10-31 13:47 +08:00).
- Output: `M16_ANALYSIS_R1/m16_analysis.json` (sha256 c6fea754…). The same analysis is printed in `analysis.log`.

## 2. Native safety endpoint and Gold
- **Endpoint:** the native typed `certificate_action` (reject_conflict vs accept / wait) jointly with the conflict margin M, on host new of the conflicting twins_streamlet DEV scenes.
- **Gold:** the source-internal executable rule; host new should be rejected.
- **Repair count:** S counts cells where the main-donor patch makes host new JOINT (M > 0 and A > 0) while the round-donor patch does not.
- **Intervention:** every effect is an L11 `o_proj`-input activation patch on host new. This is level **S1–S2** (artificial intervention scored on the native action), not S3 and not S4.

## 3. Main results and failed controls
| rule | value |
|---|---|
| consistency gate | **PASS**: S(full) = 51, 208/208 rows bitwise equal to M3; S(meanD_host) = 39, 208/208 bitwise equal to M6; `abc_s0375` and `csc29_s0375` 12/12 each bitwise equal to M15, `abc_s0375` 12/12 to M14; `mw0_s0375` 12/12 bitwise equal to `abc_s0375`; every dose row records its planned shift weights |
| **LIN_BY_HOST** | 1fb5651c **LINEAR_FAILS** (AGREE 0.978, max \|dS\| 4); 264c458d **LINEAR_HOLDS** (AGREE 0.994, max \|dS\| 1); 4bcbaf15 **LINEAR_FAILS** (AGREE 0.897, max \|dS\| 6) |
| **W_LINEAR (pooled)** | **W_LINEAR_FAILS** |
| WS_BY_HOST (S over w) | 1fb5651c SUPPORTS at every s; 264c458d OPPOSES at every s; 4bcbaf15 MIXED / SUPPORTS / SUPPORTS |
| WC_BY_HOST (C over w) | 1fb5651c SUPPORTS; 264c458d SUPPORTS; 4bcbaf15 MIXED at every s |
| **DISSOC_BY_HOST** | 1fb5651c S_C_ALIGNED; **264c458d S_C_DISSOCIATE**; 4bcbaf15 S_C_MIXED |

**Leave one donor group out (14 splits):**
- **Unchanged in 14/14:** W_LINEAR_FAILS, LIN_BY_HOST, DISSOC_BY_HOST and WC_BY_HOST.
- Ranges across splits: AGREE 0.976–0.983 / 0.993–0.997 / 0.889–0.906 and max |dS| 3–4 / 1 / 5–6, for 1fb5651c / 264c458d / 4bcbaf15.
- **WS_BY_HOST, 13/14:** in one split, 264c458d at s ½ reads NO_EFFECT, because S is flat at 13 / 12 with that group removed.
- **SUF:** `full`, `meanD_host`, `mwp05_s05` and `mwp15_s05` in 12/14 splits; only `full` and `meanD_host` in the other 2.

**Per host, S and C over w = −1, −½, 0, ½, 1, 3/2.** w = 0 and w = 1 are the pinned M14 `abc_<s>` and M15 `csc29_<s>` rows.
| host | s | S observed | S predicted at the four dose points | C |
|---|---|---|---|---|
| 264c458d | ¼ | 10 / 2 / 0 / 0 / 0 / 0 | 10 / 2 / · / 0 / · / 0 | −.034 → .028, rising |
| | ⅜ | 13 / 12 / 10 / 0 / 0 / 0 | 13 / 12 / · / 1 / · / 0 | −.030 → .063, rising |
| | ½ | 13 / 13 / 13 / 12 / 12 / 12 | 13 / 13 / · / 13 / · / 12 | .032 → .176, rising |
| 1fb5651c | ¼ | 0 / 0 / 5 / 13 / 13 / 13 | 0 / 0 / · / 13 / · / 13 | .097 → .200, rising |
| | ⅜ | 0 / **3** / 13 / 13 / 13 / 13 | 0 / **0** / · / 13 / · / 13 | .149 → .295, rising |
| | ½ | 0 / **4** / 13 / 13 / 13 / 13 | 0 / **0** / · / 13 / · / 13 | .202 → .381, rising |
| 4bcbaf15 | ¼ | **0 / 10** / 11 / **2** / 0 / **5** | **2 / 12** / · / **7** / · / **0** | −.003 / −.012 / −.011 / −.005 / .007 / .021 |
| | ⅜ | **0 / 8** / 13 / 13 / 13 / 13 | **2 / 13** / · / 13 / · / 12 | .040 / .028 / .027 / .034 / .054 / .083 |
| | ½ | **0 / 6** / 13 / 13 / 13 / 13 | **2 / 12** / · / 13 / · / 13 | .174 / .154 / .151 / .169 / .219 / .310 |

**Continuous fit of the linear prediction (reported, not a verdict):**
| host | R² of M | R² of A | median \|error\| of M / A | AGREE, interpolation (w = ½) / extrapolation |
|---|---|---|---|---|
| 264c458d | 0.906 | 0.986 | 0.011 / 0.009 | 0.974 / 1.000 |
| 1fb5651c | 0.974 | 0.803 | 0.015 / 0.034 | 1.000 / 0.970 |
| 4bcbaf15 | 0.868 | 0.894 | 0.023 / 0.031 | 0.936 / 0.885 |

**Where the predictions miss:** observed against predicted attribution, read from `rules_applied.detail.<host>.attribution`.
- **264c458d:**
  - The main source is JOINT in 13/13 cells at every w and s.
  - S is 13 minus the number of round sources with A > 0. That count rises with w as the linear prediction says, to within one cell everywhere.
- **1fb5651c:**
  - S is set by the main source's M crossing 0; the main median M lies within ±0.06 of 0 at w ≤ 0.
  - Below w = 0 the main source's M and A fall less than linearly. At w = −1, s ⅜, observed main median M is −0.025 against a predicted −0.061, and A is 0.237 against 0.170.
  - So at w = −½, 3 cells (s ⅜) and 4 cells (s ½) stay above M = 0 where the prediction put none.
- **4bcbaf15:**
  - Below w = 0 the main source's A falls faster than predicted: at w = −1, s ¼, it is −0.047 against −0.014. Main JOINT is then lost sooner (0 vs 2 at w = −1; 10, 8, 6 vs 12–13 at w = −½).
  - Above w = 1, the round source's A flattens instead of rising (s ¼: 0.020 at w = 1, 0.001 at w = 3/2, against a predicted 0.040). So 5 cells come back at w = 3/2 where the prediction gave 0.
  - At w = ½, s ¼, round median A is 0.015 against a predicted 0.000. With the cells packed near A = 0, that gap of about 0.015 moves S from a predicted 7 to an observed 2.

**Failed controls:** none. The consistency gate and every bitwise replay passed, and the new `shift_pos_weight` code path reproduces the AB arm bitwise on the GPU.

## 4. Causal level and scope
- **Evidence level:** S1–S2 intervention evidence on kev-4B and the twins_streamlet DEV simulator. There is no natural-error (S3) or deployment (S4) evidence.
- **Hosts:** all dose arms are pooled-donor arms. That is effectively 8 host replicates; 3 respond (1fb5651c, 264c458d, 4bcbaf15). The other 5 hosts give S 0 in every dose arm, as in M13–M15.
- **What M16 establishes:**
  1. **264c458d (preregistered LINEAR_HOLDS, S_C_DISSOCIATE).** The middle common shift moves each cell's M and A linearly in w; the AB / all-position difference is the threshold readout of that.
     - Lowering w lowers the round source's action margin more than it lowers the main source's margin.
     - So S rises as C falls. The arm that repairs most (w = −1, S 13 at s ⅜) carries the least contrast (C −0.030).
     - On this host, M14's lower AB threshold is therefore **not** evidence that the author and block lines carry the contrast.
  2. **1fb5651c and 4bcbaf15 (preregistered LINEAR_FAILS).** Linearity fails, mostly outside [0, 1]: below w = 0 on both, and above w = 1 on 4bcbaf15.
     - 1fb5651c is sublinear below w = 0.
     - 4bcbaf15 falls faster below 0 and flattens above 1.
     - Within [0, 1], AGREE is 1.000 on 1fb5651c and 0.936 on 4bcbaf15. The 4bcbaf15 interpolation miss is one s (¼), where an A error of about 0.015 flips 5 cells packed at the threshold.
- **Descriptive reading (not a verdict):** the M and A responses are close to linear in w, with R² 0.80–0.99 and median errors ≤ 0.034. S is a threshold count, and it amplifies small curvature wherever many cells sit near M = 0 or A = 0. Under the preregistered rule this still reads FAILS: the rule was set on S and JOINT agreement, deliberately.

## 5. Strongest prior art and the novelty delta
- **Prior art:** Zhang & Nanda (ICLR 2024), *Towards Best Practices of Activation Patching*. Localization conclusions depend on the metric, and thresholded or flip-count metrics can mislead. They recommend reporting signed logits.
- **What M16 adds:** a preregistered case of that warning, on a native safety action.
  - On 264c458d, a patch location that looked better by the repair count S (M14) is a linear common offset read through a threshold.
  - On that host, the repair count ranks arms opposite to the source-specific contrast C.
- **Size of the delta:** small and methodological. M16 adds no new mechanism.
- **Safety relevance of the delta:**
  - It is a concrete instance of the standard's §3.6 caution: an intervention that "repairs" more errors can do so by pushing the control source over the decision line less, not by carrying more source-specific signal.
  - For anyone evaluating activation-level defences on this kind of veto task, count-based repair metrics must be paired with a source-matched control and a continuous contrast measure.

## 6. Open decisive questions
- **False veto (unmeasured):** no M-line stage measures it. Every target is the conflicting host new, so it is unknown whether these patches would make benign hosts reject.
- **Non-responsive hosts:** 5 of 8 hosts are never repaired by any pooled-donor arm in M8–M16. Why is unknown.
- **4bcbaf15 curvature:** whether the curvature there is an interaction with the contrast, or saturation of the shift's effect. M16's design cannot separate these. Any outcome would change the description of one host and would not change the safety level.

## 7. Decision: KEEP / HOLD / DOWNGRADE / REJECT
**Preregistered branch: W_LINEAR_FAILS.** The prereg says to keep M14's location reading as CONDITIONAL and to design at most one stage that separates the interaction.

**Decision:**
- **DOWNGRADE (host-scoped):** M14's AB-threshold result as a location effect.
  - On 264c458d it is a linear readout-threshold effect (LINEAR_HOLDS, S_C_DISSOCIATE, 14/14 splits). It must not be described as evidence that the author and block lines carry the contrast.
  - On 1fb5651c and 4bcbaf15 the reading stays **CONDITIONAL**: linearity fails there, but mostly by curvature outside the M14–M15 interval.
- **STOP the position line; use none of the one allowed follow-up stage:**
  - Its information value is low. Either answer would only re-describe one host (4bcbaf15) that sits near ceiling at s ≥ ⅜.
  - It would not move the evidence level from S1–S2 or touch the false-veto gap.
- **Next work, with expected information value:**
  1. M1–M16 consolidation: the mechanism section of the paper must now carry the 264c458d downgrade and the S/C dissociation caution. This needs the user's go-ahead.
  2. A false-veto control on benign (non-conflicting) hosts: highest safety value. It needs a runner change to allow non-conflict targets, and a scope decision by the user.
  3. Why 5 of 8 hosts never respond.
- No paper-level audit has been run. The V3 PASS covers v9 only and predates M1–M16.
