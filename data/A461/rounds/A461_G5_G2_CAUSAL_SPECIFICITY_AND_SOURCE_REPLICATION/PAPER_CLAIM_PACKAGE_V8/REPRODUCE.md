# Reproduction (V8)

All paths are relative to
`research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/` unless stated otherwise. Every command in
sections 1–3 was run on 2026-10-27; the results are in [REANALYSIS_CHECK.md](REANALYSIS_CHECK.md).

## 1. CPU re-analysis from the archived raw data (8 of 9 stages; Python 3.8+ and the standard library only)

```bash
SA=G2_STAGE_A_GPU_R1/G2_STAGE_A_GPU_RUNS/ATTEMPT_R1/raw_native_logits_stage_a.jsonl
python A461_g5_g2_stage_a_analysis_v1.py --run-dir G2_STAGE_A_GPU_R1/G2_STAGE_A_GPU_RUNS/ATTEMPT_R1 \
  --ledger G2_STAGE_A_GPU_R1/G2_STAGE_A_QUOTA_LEDGER/A461_G5_G2_STAGE_A_GPU_20261027_R1/ledger.jsonl --out /tmp/A
python A461_g5_g2_stage_b_analysis_v1.py --raw G2_STAGE_B_GPU_R1/G2_STAGE_B_GPU_RUNS/ATTEMPT_R1/raw_native_logits_stage_b.jsonl \
  --design G2_STAGE_B_FREEZE_R1/stage_b_design.json --out /tmp/B
python A461_g5_g2_stage_d_analysis_v1.py --run-dir G2_STAGE_D_GPU_R1/G2_STAGE_D_GPU_RUNS/ATTEMPT_R1 --stage-a-raw $SA \
  --design G2_STAGE_D_FREEZE_R1/stage_d_design.json --out /tmp/D
python A461_g5_g2_stage_e_analysis_v1.py --run-dir G2_STAGE_E_GPU_R1/G2_STAGE_E_GPU_RUNS/ATTEMPT_R1 --stage-a-raw $SA \
  --design G2_STAGE_E_FREEZE_R1/stage_e_design.json --out /tmp/E
python A461_g5_g2_stage_f_analysis_v1.py --run-dir G2_STAGE_F_GPU_R1/G2_STAGE_F_GPU_RUNS/ATTEMPT_R1 \
  --design G2_STAGE_F_FREEZE_R1/stage_f_design.json --out /tmp/F
# kev-4B: the screen uses the same frozen Stage-A script and rule
python A461_g5_g2_stage_a_analysis_v1.py --run-dir G2_K4B_STAGE_A_GPU_R1/G2_K4B_STAGE_A_GPU_RUNS/ATTEMPT_R1 \
  --ledger G2_K4B_STAGE_A_GPU_R1/G2_K4B_STAGE_A_QUOTA_LEDGER/A461_G5_G2_K4B_STAGE_A_GPU_20261027_R1/ledger.jsonl --out /tmp/K4A
python A461_g5_g2_k4b_kb_analysis_v1.py --run-dir G2_K4B_KB_GPU_R1/G2_K4B_KB_GPU_RUNS/ATTEMPT_R1 --out /tmp/KB
python A461_g5_g2_k4b_kc_analysis_v1.py --run-dir G2_K4B_KC_GPU_R1/G2_K4B_KC_GPU_RUNS/ATTEMPT_R1 \
  --design G2_K4B_KC_FREEZE_R1/k4b_kc_design.json --out /tmp/KC
```

**Check.** Compare each output with the matching archived `G2_*_GPU_R1/G2_*_ANALYSIS_R1/*.json`, parsing both as JSON.
A byte comparison fails locally because the working copy uses CRLF line endings under `core.autocrlf`.

## 2. Capture tensors (Stage C H3 and the capture checks; needs torch ≥ 2.1, CPU)

**Download.** The tensors are GitHub Release assets of `dddd2024/jev`. See [CAPTURES.md](CAPTURES.md) for tags and
digests.

```bash
gh release download a461-g2-captures-stage-c-v1 --repo dddd2024/jev --dir caps
gh release download a461-g2-captures-def-k4b-v1 --repo dddd2024/jev --dir caps
(cd caps && sha256sum -c ../PAPER_CLAIM_PACKAGE_V4/CAPTURES_SHA256SUMS)
```

**Stage C, H3.** Extract the bundle so that `ATTEMPT_R1/captures/` sits next to the archived Stage-C run files, then
run the frozen script:

```bash
mkdir -p /tmp/C_run && tar xf caps/captures_stage_C_A461_G2.tar -C /tmp/C_run
cp G2_STAGE_C_GPU_R1/G2_STAGE_C_GPU_RUNS/ATTEMPT_R1/* /tmp/C_run/ATTEMPT_R1/ 2>/dev/null
python A461_g5_g2_stage_c_analysis_v1.py --run-dir /tmp/C_run/ATTEMPT_R1 \
  --stage-a-raw G2_STAGE_A_GPU_R1/G2_STAGE_A_GPU_RUNS/ATTEMPT_R1/raw_native_logits_stage_a.jsonl \
  --stage-a-per-scene G2_STAGE_A_GPU_R1/G2_STAGE_A_ANALYSIS_R1/stage_a_per_scene.jsonl \
  --design G2_STAGE_C_FREEZE_R1/stage_c_design.json --out /tmp/C
```

**Capture checks for any stage** (C, D, E, F, K4B_KB, K4B_KC):

```bash
S=STAGE_F; r=stage_f; T=captures_${S}_A461_G2.tar
# or STAGE_D/stage_d, STAGE_E/stage_e, K4B_KB/k4b_kb, K4B_KC/k4b_kc; for Stage C: S=STAGE_C; r=stage_c; T=captures_stage_C_A461_G2.tar
mkdir -p /tmp/cap_$S && tar xf caps/$T -C /tmp/cap_$S
python PAPER_CLAIM_PACKAGE_V3/verify_captures_v1.py --raw G2_${S}_GPU_R1/G2_${S}_GPU_RUNS/ATTEMPT_R1/raw_native_logits_$r.jsonl \
  --captures /tmp/cap_$S/ATTEMPT_R1/captures --sha-list /tmp/cap_$S/ATTEMPT_R1_CAPTURES_SHA256.txt
```

The verifier checks four things:
- each tensor's SHA against the raw row and the SHA list;
- the dtype and shape;
- the cross-row identity of all-row captures;
- that the files and raw rows match one to one.

## 3. Manuscript numbers and document

Run these inside `PAPER_CLAIM_PACKAGE_V3/`. The `assemble_v7.py`, `assemble_v8.py`, `assemble_v9.py` and
`generate_v9.js` shipped here are the outputs of the steps below, which reproduce them exactly.

```bash
python extract_numbers_v8.py <jev repo root> numbers_v8.json   # every G2 number, from archived artifacts and raw logits;
                                                                # asserts reservations == physical calls for all 9 stages
python v7_edits.py       # assemble_v6.py -> assemble_v7.py
python v8_edits.py       # assemble_v7.py -> assemble_v8.py
python v9_edits.py       # assemble_v8.py -> assemble_v9.py (audit d9d3338 text revisions; no number changes)
python assemble_v9.py    # generate_v5_input.js + numbers -> generate_v9.js
node generate_v9.js      # writes A461_G2_paper_draft_v9.docx (needs the docx npm package)
```

The PDF was exported from the docx with Microsoft Word.

## 4. Full GPU re-run (authorized server only)

**Environment.**
- Python: `~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3` (3.12, torch 2.8 cu128).
- SecJev identity: pinned in runner V4 (`b675e9d5`).
- kev-4B identity: pinned in `f118ea59` and verified before load:
  - checkpoint: 16 files;
  - base: 13 files;
  - kev source (`kev08b-smoke/code`): 4 files.

**Stage runners and budgets.**

| Stage | Runner (blob) | Manifest (blob) | Calls | Batches |
|---|---|---|---|---|
| A | `A461_g5_g2_stage_a_gpu_screen_runner_g0_v4.py` (`b675e9d5`) | `01ca5390` | 378 | 128/128/122 |
| B | `A461_g5_g2_stage_b_gpu_runner_v1.py` (`2ff96b38`) | `363351fd` | 464 | 4 × 116 |
| C | `A461_g5_g2_stage_c_gpu_runner_v1.py` (`2ba9fef9`) | `f2f8f024` | 696 | 124/124/112/112/112/112 |
| D | `A461_g5_g2_stage_d_gpu_runner_v1.py` (`5ba88abb`) | `be9bcba2` | 349 | 71/70/112/96 |
| E | `A461_g5_g2_stage_e_gpu_runner_v1.py` (`23a5a3a3`) | `aa8c77b7` | 304 | 88/72/72/72 |
| F | `A461_g5_g2_stage_f_gpu_runner_v1.py` (`5a7067f8`) | `d44e2ed4` | 296 | 104/64/64/64 |
| kev-4B screen | `A461_g5_g2_k4b_stage_a_screen_runner_v1.py` (`f118ea59`) | `01ca5390` | 378 | 128/128/122 |
| kev-4B K-B | `A461_g5_g2_k4b_kb_runner_v1.py` (`954a131b`) | `8673c64d` | 346 | 128/128/90 |
| kev-4B K-C | `A461_g5_g2_k4b_kc_runner_v1.py` (`478bdc1f`) | `b07cc4c6` | 417 | 128/128/128/33 |

**Procedure for each stage.**
1. Write an admission file in the format of the archived `admission_*_gpu_R1.json`, with a **new** `admission_id`. The
   durable ledger refuses to reuse one.
2. Run `--pre-model-gate-only`.
3. Run the full stage with `--out` under the stage's `*_GPU_RUNS/` directory.

**Expected result.** Every capture and baseline must equal the archived earlier-stage logits bitwise, or the runner
stops. This holds on the same GPU and software stack. Cross-hardware bitwise identity is not claimed.

## 5. Mechanism route M1–M22 and manuscript v10 (added in V4)

**Re-run all 22 frozen analyses (CPU; torch for M3, M5, M18, M19, M21 and M22).** Run this where the GPU work
directory holds the raw rows, captures and freeze inputs, which today is the GPU server:

```bash
python PAPER_CLAIM_PACKAGE_V4/recompute_mech_v1.py --rounds <jev repo>/research/rounds \
  --work <GPU work dir> --out /tmp/RECOMPUTE_MECH
```

- It runs each stage's committed analysis script on the archived inputs.
- It compares each output with the committed `M<i>_ANALYSIS_R1/m<i>_analysis.json` as parsed JSON, using exact
  equality. For M17 the comparison is with `M17_ANALYSIS_R1_V1_1/`.
- It writes `RECOMPUTE_MECH.json` and exits 0 only if all 22 are EQUAL.
- The result of the 2026-11-01 run is in `REANALYSIS_CHECK.md`.

The 16 stages that read only raw logits (M1, M2, M4, M6–M17, M20) also re-run without captures, given the committed raw
rows. Their inputs are in each stage's `M<i>_GPU_R1/` and `M<i>_FREEZE_R1/`.

**Manuscript v10.** Run inside `PAPER_CLAIM_PACKAGE_V4/`, with Node and the `docx` package:

```bash
python extract_numbers_mech_v1.py <jev repo root> numbers_mech_v1.json   # every mechanism number, from archived JSONs and receipts
python v10_edits.py ../PAPER_CLAIM_PACKAGE_V3/generate_v9.js generate_v10.js
node generate_v10.js                                                       # writes A461_G2_paper_draft_v10.docx
soffice --headless --convert-to pdf A461_G2_paper_draft_v10.docx
```

`generate_v10.js` reads `numbers_v8.json` (G2; copied unchanged from V3) and `numbers_mech_v1.json` (mechanism).

## 6. Manuscript v11 and the V5 additions

Run inside `PAPER_CLAIM_PACKAGE_V5/`:

```bash
python extract_numbers_mech_v2.py <jev repo root> numbers_mech_v2.json   # v1 + three-action table, M21 action changes, M20 survivors, G2.3
python v11_edits.py ../PAPER_CLAIM_PACKAGE_V4/generate_v10.js generate_v11.js
node generate_v11.js                                                       # writes A461_G2_paper_draft_v11.docx
```

**G2.3 constructibility check (CPU, tokenizer only).** Run on the server with the frozen corpus:
`research/rounds/A461_MON_G23_CONTEXT_COUNTERFACTUAL_CPU/A461_mon_g23_ctx_cf_cpu_v1.py`. The command line is in that
folder's `G23_RESULT_V1.md`.

**Mechanism captures.** These are in the private release `a461-mech-captures-m1-m22-v1`: one tar per stage, plus
`MECH_CAPTURES_SHA256SUMS` (see `CAPTURES.md`). With them, `recompute_mech_v1.py` runs off the server. Point `--work` at a
directory holding the extracted `M<i>_GPU_RUNS/ATTEMPT_R1/` trees, the freeze inputs and the raw rows. M19 and M21
additionally need the pinned kev-4B `head.pt`, which is not released.

## 7. M23 and manuscript v12

- **M23.** Freeze, runners, self-tests and analysis are in `research/rounds/A461_MON_M23_TWIN_PROBE_GPU/` (derive script
  `A461_mon_m23_derive_v1.py`; command lines in its launchers). The analysis needs the M18 / M22 captures, which are in
  the release, and the M23 captures, which are on the server.
- **Manuscript v12.** Run inside `PAPER_CLAIM_PACKAGE_V6/`:

  ```bash
  python extract_numbers_mech_v3.py <jev repo root> numbers_mech_v3.json
  python v12_edits.py ../PAPER_CLAIM_PACKAGE_V5/generate_v11.js generate_v12.js
  node generate_v12.js
  ```

## 8. Manuscript v13

Run inside `PAPER_CLAIM_PACKAGE_V7/`:

```bash
python extract_numbers_mech_v4.py <jev repo root> numbers_mech_v4.json
python v13_edits.py ../PAPER_CLAIM_PACKAGE_V6/generate_v12.js generate_v13.js
node generate_v13.js
```

## 9. Manuscript v14

Run inside `PAPER_CLAIM_PACKAGE_V8/`:

```bash
python extract_numbers_mech_v5.py <jev repo root> numbers_mech_v5.json   # v4 + source-group cluster-bootstrap CIs
python v14_edits.py ../PAPER_CLAIM_PACKAGE_V7/generate_v13.js generate_v14.js
node generate_v14.js
```
