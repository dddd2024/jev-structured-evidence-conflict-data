# Re-analysis check (V2, 2026-10-27)

Every frozen analysis script was re-run on the archived data, and its output was compared with the archived analysis
output. The commands are in [REPRODUCE.md](REPRODUCE.md).

## Frozen analyses

| Stage | Script | Where it ran | Result |
|---|---|---|---|
| A | `A461_g5_g2_stage_a_analysis_v1.py` | Local, repo files | JSON and per-scene JSONL semantically identical |
| B | `A461_g5_g2_stage_b_analysis_v1.py` | Local, repo files | Semantically identical |
| C | `A461_g5_g2_stage_c_analysis_v1.py` | Server, CPU; captures extracted from the **release bundle** into a fresh directory | `cmp` byte-identical |
| D | `A461_g5_g2_stage_d_analysis_v1.py` | Local, repo files | Semantically identical |
| E | `A461_g5_g2_stage_e_analysis_v1.py` | Local, repo files | Semantically identical |
| F | `A461_g5_g2_stage_f_analysis_v1.py` | Local, repo files | Semantically identical |
| kev-4B screen | `A461_g5_g2_stage_a_analysis_v1.py` | Local, repo files | JSON and per-scene JSONL semantically identical |
| kev-4B K-B | `A461_g5_g2_k4b_kb_analysis_v1.py` | Local, repo files | Semantically identical |
| kev-4B K-C | `A461_g5_g2_k4b_kc_analysis_v1.py` | Local, repo files | Semantically identical |

**Environments.**
- Local: Windows, Python 3.13, run with `python -I`.
- Server: venv Python 3.12 with torch 2.8, CPU only.

"Semantically identical" means the parsed JSON objects, or each JSONL line, are equal. Local byte comparison is not
meaningful, because the working copy uses CRLF line endings under `core.autocrlf`.

## Capture checks (`verify_captures_v1.py`, server, from the extracted release bundles)

| Stage | Raw rows | Capture rows = files | Cross-row identity checked | Result |
|---|---|---|---|---|
| C | 696 | 248 | — (runner recorded no cross-row field) | PASS |
| D | 349 | 16 | — (runner recorded no cross-row field) | PASS |
| E | 304 | 16 | 16 | PASS |
| F | 296 | 40 | 40 | PASS |
| kev-4B K-B | 346 | 10 | 10 | PASS |
| kev-4B K-C | 417 | 41 | 41 | PASS |

The server raw logs the verifier read are byte-equal (SHA-256) to the committed raw logs at `5ef7a16`.

## Manuscript numbers and generator

Starting from a clean copy of this package, these steps were run:

1. `extract_numbers_v8.py` reproduced `numbers_v8.json` (parsed-equal). It asserts that reservations equal physical
   calls for all 9 stages: 3,628 in total.
2. `v7_edits.py` → `v8_edits.py` → `assemble_v8.py` reproduced `assemble_v7.py`, `assemble_v8.py` and `generate_v8.js`.
   These are identical up to line endings.
