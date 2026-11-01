# Reproduction (V2 working copy; fixes audit P2-1 and P2-2)

All paths are relative to
`research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/`.

## 1. CPU re-analysis from the archived raw data (verified on 2026-10-27)

**Stages A, B, D and E** need Python 3.8+ and the standard library only.

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
```

Compare each output with the matching `G2_STAGE_*_GPU_R1/G2_STAGE_*_ANALYSIS_R1/*.json`. All four were equal on
2026-10-27.

**Stage C, H3** reads the capture tensors, which sit on the authorized server under
`~/wjc/a461-g5-minimal-patch-pilot-20261025-v1/G2_STAGE_C_GPU_RUNS/ATTEMPT_R1/captures/`. Their SHA-256 values are listed
in `G2_STAGE_C_GPU_R1/G2_STAGE_C_GPU_RUNS/ATTEMPT_R1_CAPTURES_SHA256.txt`. The recomputation needs torch and was
byte-identical on 2026-10-27:

```bash
# from this folder, after placing the Stage-C capture bundle (CAPTURES_ACCESS_PLAN.md) at
# G2_STAGE_C_GPU_R1/G2_STAGE_C_GPU_RUNS/ATTEMPT_R1/captures/
python A461_g5_g2_stage_c_analysis_v1.py --run-dir G2_STAGE_C_GPU_R1/G2_STAGE_C_GPU_RUNS/ATTEMPT_R1 \
  --stage-a-raw G2_STAGE_A_GPU_R1/G2_STAGE_A_GPU_RUNS/ATTEMPT_R1/raw_native_logits_stage_a.jsonl \
  --stage-a-per-scene G2_STAGE_A_GPU_R1/G2_STAGE_A_ANALYSIS_R1/stage_a_per_scene.jsonl \
  --design G2_STAGE_C_FREEZE_R1/stage_c_design.json --out <dir>
```

## 2. Manuscript numbers and document

```bash
# run inside PAPER_REVISION_V2_WORK/ (generate_v5_input.js, assemble_v6.py and the v7 scripts are in this folder)
python extract_numbers_v7.py <jev repo root> numbers_v7.json   # every G2 number, from archived artifacts and raw logits
python v7_edits.py                                              # derives assemble_v7.py from assemble_v6.py
python assemble_v7.py                                           # reads generate_v5.js or generate_v5_input.js
node generate_v7.js                                             # writes A461_G2_paper_draft_v7.docx (needs the docx npm package)
```

## 3. Full GPU re-run (authorized server only)

A GPU re-run requires the user's explicit approval of each stage's budget.

**Environment.**
- Python: `~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3` (3.12, torch 2.8 cu128).
- Model identity: pinned in runner V4 (`b675e9d5`) and verified before load.

**Stage runners and budgets.**

| Stage | Runner | Manifest | Calls | Batches |
|---|---|---|---|---|
| A | `A461_g5_g2_stage_a_gpu_screen_runner_g0_v4.py` (`b675e9d5`) | `01ca5390` | 378 | 128/128/122 |
| B | `A461_g5_g2_stage_b_gpu_runner_v1.py` (`2ff96b38`) | `363351fd` | 464 | 4 × 116 |
| C | `A461_g5_g2_stage_c_gpu_runner_v1.py` (`2ba9fef9`) | `f2f8f024` | 696 | 124/124/112/112/112/112 |
| D | `A461_g5_g2_stage_d_gpu_runner_v1.py` (`5ba88abb`) | `be9bcba2` | 349 | 71/70/112/96 |
| E | `A461_g5_g2_stage_e_gpu_runner_v1.py` (`23a5a3a3`) | `aa8c77b7` | 304 | 88/72/72/72 |

**Procedure for each stage.**
1. Write an admission file in the format of the archived `admission_stage_*_gpu_R1.json`, with a **new**
   `admission_id`. The durable ledger refuses to reuse one.
2. Run `--pre-model-gate-only`.
3. Run the full stage with `--out` under `G2_STAGE_*_GPU_RUNS/`.

**Expected result.** Every capture and baseline must equal the archived Stage-A logits bitwise, or the runner stops.
This holds on the same GPU and software stack. Cross-hardware bitwise identity is not claimed.
