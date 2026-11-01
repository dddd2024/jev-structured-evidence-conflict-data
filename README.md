# A461 Structured Evidence Conflict — Experiment Data

Public research-data archive for the **A461 structured-evidence conflict / appended-vote validity** experiments on **kev-4B** and **SecJev-0.8B**.

## Available data

- [`data/A461/M23/`](data/A461/M23/) — an initial curated data release: preregistered plan; frozen inputs and exact 248-row manifests per model; 248 raw native-output rows per model; analysis JSON; experiment and analysis source code; self-tests; result report.
- [`MANIFEST.json`](MANIFEST.json) — source-to-public file mapping and Git blob hashes. Each transferred file's Git blob hash was checked against its original in the private research repository.

The M23 experiment compares valid appended conflicts and matched non-conflicting twin cases, with an identical appended span and a changed preceding contextual token. Scene groups are generated in the synthetic `twins_streamlet` setting.

## Publication status and limitations

**PARTIAL PUBLIC RELEASE — not a complete backup of A461.** The preceding G2 and M1–M22 data are not yet included in this repository. The original M23 hidden-state tensor captures (`.pt`) remain on the research server and are **not** included in this release. M23 manifest and raw-score rows may refer to those missing captures and earlier-stage inputs.

This snapshot allows direct inspection of model logits, frozen row manifests, and published analysis but does **not** yet provide a fully self-contained reconstruction or complete rerun of every experiment.

## Provenance and redistribution

Original source: private `dddd2024/jev`, `research/rounds/A461_MON_M23_TWIN_PROBE_GPU/`. Files listed in the manifest were copied byte-for-byte, as verified by matching Git blob identifiers.

Model weights, private keys, execution-machine logs, and third-party datasets with unclear redistribution rights are not included. Original licenses and access terms for model weights and third-party datasets remain applicable; their inclusion is not implied.

## Guide

- `M23_FREEZE_R1/m23[k|s]_manifest.jsonl`: frozen run entries (248 per model)
- `M23K_GPU_R1/raw_native_logits_m23k.jsonl`: kev-4B raw outputs (248 rows)
- `M23S_GPU_R1/raw_native_logits_m23s.jsonl`: SecJev-0.8B raw outputs (248 rows)
- `M23[K|S]_ANALYSIS_R1/*.json`: reported analyses
- `PREREG_M23_R1.md` and `M23_RESULT_R1.md`: frozen test and results

These files are provided as a research record, including negative and confounded findings. A partial release should not be cited as a complete, independently re-run dataset.
