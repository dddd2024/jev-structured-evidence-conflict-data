# Re-analysis check (2026-10-27)

Each frozen stage analysis script was re-run on the archived raw data. The output was compared with the archived
analysis JSON.

| Stage | Script | Where it ran | Result |
|---|---|---|---|
| A | `A461_g5_g2_stage_a_analysis_v1.py` | Local (Windows, Python, `-I`), from repo files | JSON semantically identical |
| B | `A461_g5_g2_stage_b_analysis_v1.py` | Local, from repo files | JSON semantically identical |
| C | `A461_g5_g2_stage_c_analysis_v1.py` | Server (venv Python 3.12, CPU only), from GPU-run captures | `cmp` byte-identical |
| D | `A461_g5_g2_stage_d_analysis_v1.py` | Local, from repo files | JSON semantically identical |
| E | `A461_g5_g2_stage_e_analysis_v1.py` | Local, from repo files | JSON semantically identical |

"Semantically identical" means the parsed JSON objects are equal. Local byte comparison is not meaningful, because the
working copy uses CRLF line endings under `core.autocrlf`.

The manuscript's G2 numbers come from `extract_numbers_v6.py`. That script also asserts that every stage's ledger
reservations equal its receipt's physical calls (2,191 in total).
