# A461-G5 post-freeze independent pre-execution audit: scene exclusion and patch host alignment

Date: 2026-10-25. **Status: STOP / MUST AMEND before launching G5 patching.** CPU-only re-analysis of committed GitHub records; **zero new model forwards**, no external tool actions. This is an append-only erratum / pre-execution review; do not overwrite frozen G5 V1 protocol or original raw files.

## Verified latest progress

- G4-G0A/B/C/D metadata/tokenizer/algebra complete, commit `e586a080`.
- G4-G1R completed archival of **56 readout-analysis request rows**, `224/224` 4-head Q/K logit reconstructions and 26 pair decompositions, commit `cf25773`; 25/26 pairs have largest absolute *signed margin-change component* on pointer-key side. **Exact bilinear accounting, not upstream causal mediation.**
- G4 `G1R_REAL_20261025/execution_receipt.json` (Git blob `91998b5b35ed084b424fc0ecae4189aa259f94d3`) says `FAIL_A461_G4_G1R` due `NameError: name 'hook' is not defined` during cleanup, after 56 forward calls. There is a nonempty frozen analysis and a result memo describing completion. Clearly distinguish *archived analytic output and reconstruction checks* from **successful process termination**. The result memo mentions multiple full-forward attempts; reconcile aggregate GPU consumption, not only the last 56-call ledger.
- G5-G1S donor search completed **112 physical forward calls** over 36 pairs plus 4 replays, commit `3b474fb`. Original reported 1 qualified donor (run83), 4 partial, 31 failed, and SA neutral matching 33/36. The real donor remains qualified after the duplicate-scene correction below.
- G5 patching protocol was **frozen for blind review**, commit `9684e37`; no patching outputs appear under `research/rounds/A461_G5_DONOR_RESOLUTION_AND_PATCHING/` as of review. No blind-review verdict read.

## P0: scene-level G3 exclusion was ineffective in actual G5 constructor

Source `research/rounds/A461_G5_DONOR_RESOLUTION_AND_PATCHING/A461_g5_construction_v1.py` (Git blob `a7a25047f708030ff3c6173cc0988b1aaf70b19d`), lines 100–110 inserts **16-character suffixes** of G3 `pair_key` into `excl`:

```python
excl.add(r["pair_key"].split(":", 1)[1])
```

But lines 134–140 compare **64-character SHA-256** of full source-state canonical JSON to `excl`:

```python
if hx(canon(rec["state"])) in excl:
    continue
```

The two formats cannot match. A428 full-SHA exclusions do work, but G3 exclusions **do not**. The reported `g3_pairs_excluded:26` in G5 census is only a count of inserted truncated identifiers; it does **not** prove the scenes were removed.

Independent full original-state reconstruction from the archived `new` rows (remove their single appended treatment event) on G3 and G5 finds **7/36 G5 pairs whose original states are byte/semantic canonical-identical to G3 original states**, with *identical pair_key* in all 7 and **identical treatment event in five of seven**. These are:

| Source group | Pair key short | Old state reused | New treatment identical |
|---|---|---|---|
| run181 | `T2_WAIT_TO_REJECT:2844afec594fb8fe` | yes | yes |
| run279 | `T2_WAIT_TO_REJECT:8569abcac4d9db01` | yes | yes |
| run140 | `T2_ACCEPT_TO_REJECT:1f44a51c2d56e453` | yes | yes |
| run211 | `T2_ACCEPT_TO_REJECT:e07def56c83846ab` | yes | no (different conflicting block) |
| run212 | `T2_ACCEPT_TO_REJECT:d74b45028314ec60` | yes | yes |
| run283 | `T2_ACCEPT_TO_REJECT:733c199a6bb6e22b` | yes | yes |
| run328 | `T2_ACCEPT_TO_REJECT:e2ccd95e3d406bfe` | yes | no (different conflicting block) |

Sources pinned:
- G3 `G0C_REAL_20261025/pair_rows.jsonl` Git blob `8de45fc200d0e37be676f172d844b3ab2c6c23c7` (26 original pairs)
- G5 `G0D_CONS_REAL/pair_rows.jsonl` Git blob `3d8fba0e041ea37b22ee4c3c64593f2ccb6f3131` (36 pairs).

G5 36 original pair outcomes: **1 qualified / 4 partial / 31 failed**, and 33/36 treatment-vs-SA length-matched.
- Duplicate 7: **0 qualified / 3 partial / 4 failed**, length-matched 7/7.
- Unique-original-state G5 29: **1 qualified / 1 partial / 27 failed**, length-matched **26/29**.

Thus the finding of *one* strict positive donor is **not invalidated** by this particular duplication (donor `T2_WAIT_TO_REJECT:433890d19a90625e`, `run83`, is among unique G5 scenes and SA is length-matched); the claims “all G5 scenes unseen relative to G3” and “36 independent new construction scenes” are FALSE. The total unique G3+G5 initial scenes is **26+29=55**, not 62. Existing source run groups are still reused and must never be claimed unseen independent groups.

**Immediate remediation:** fix exclusion to store `hx(canon(original_state))` full SHA-256 from a reliable archived original-state reconstruction or compare identical full old-state digests; rerun CPU G0 census and independent verifier; do not retroactively modify G5 raw results; publish an erratum and sensitivity reanalysis excluding overlap. Because G5 is an exploratory donor search, preserving the 1 valid donor is permissible with full disclosure; any confirmation claim must use independent fresh groups.

## P0: patching V1 references a non-existent host appended span

`research/experiments/2026-10-25_A461_G5_PATCHING_PROTOCOL_V1.json` (Git blob `5fba6d724cf81eb27ca25c73645fbfba79e3a5b9`) defines `span = [first_divergence_vs_its_own_old_arm, state_len_new)`, i.e. positions occupied by the **appended vote in the new input**. Its `sufficiency_direction` then asks to patch a **host old-arm row** at “the host's appended-span positions” with donor NEW states. But `host old-arm` has no appended vote. In a typical real archived host, G5 `G1S_REAL/render_token_lengths.json` lists `old=536` vs `new=570` (+34); no 34-token append span exists within the old state's state segment. Those indices cannot be treated as semantic-aligned vote tokens in the old host. Relative linear span mapping across 33/34 widths does not fix *missing source-side tokens*.

**Immediate remediation:** use host's schema-valid **SA-neutral appended arm** as a same-scene target host, with identical event count and Gold=false; compare new conflict donor→SA host restoration, donor SA→treatment failure suppression, identical-SA replay, random-shuffle and token-position controls; all source and token anchoring must be rerendered independently. Alternatively formulate an explicit **token insertion counterfactual** with its own independently tested semantics, rather than treating the old state's nonexistent span as patchable. Select only matched-token SA hosts; G5 has 33/36 matching, and the first five wait + first five accept failed cases by row ID happen to be 10/10 matched, but selection should be formalized and verified rather than inferred in protocol text.

## P1: claim boundary and next gate

- G4 exact decomposition establishes that most *changes* in the C margin correspond algebraically to the candidate-end K difference; it is **not yet a causal localization of the upstream relation-binding failure** and cannot by itself exclude other representations.
- One positive donor, reusing the same development source family and reused historical group, remains insufficient for robust cross-group mechanism transfer and publishable general mechanism inference.
- Independent blind-review verdict for G5 V1 was not present in retrieved commits. **G5 patching is frozen as a *proposal*, not admitted/executed**.
- New patching should rerun CPU anchor/donor metadata checks and present independent review a **revised version**, preserving original V1 and explicit corrected stage budgets (84 + 88 were planned; no G5 patching forward happened here).

## Decision

**Progress:** G4 readout measurement achieved, G5 exploratory donor-resolution achieved; **G5 actual bidirectional causal intervention has not started**. **STOP_G5_PATCHING_V1_BEFORE_GPU** pending exclusion and host-span fixes, independent review and recalculated admissions. This finding does not discard A461; it prevents an avoidable invalid causal claim.
