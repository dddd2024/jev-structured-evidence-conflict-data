# kev-4B second-model feasibility (CPU only, 2026-10-27)

This addresses audit item P1-1 (external validity). No model forward was run for this check.

## Model

| Item | Value |
|---|---|
| Assets | `~/wjc/kev4b-assets-20261002/` (29 official files, re-hash verified 2026-10-02) |
| Adapter | kev-4B adapter `jaredpalmer/kev-4b@139fdd94` (LoRA r16, fixed FP32 pointer head, head_dim 256, artifact temperature 2.406) |
| Base | Qwen/Qwen3.5-4B-Base `1001bb4d` |
| Architecture | Hybrid: 32 layers, hidden size 2560, full attention every 4th layer (3, 7, …, 31) |
| Training | General typed-decision model (banking77, BoolQ, AG News, MNLI, SST-5, Yelp, TREC, DBpedia, Amazon, IMDB, plus programmatic policy data) |

**Not trained on SecJev or twins_streamlet consensus scenes.** Its behaviour on this task is unknown.

## Checks

| Check | Result |
|---|---|
| Base `tokenizer.json` SHA-256 equals SecJev-0.8B's base tokenizer (`fe000e3e…`) | identical |
| Compatible kev source: `~/wjc/kev08b-smoke-20261001-153041/code/kev` (`checkpoint.py` 8c8642…, `model.py` 2ff3b2…) equals kev-4B's preserved source pins | identical |
| Fresh encode of all 124 × 3 Stage-A arms with kev-4B source and tokenizer, compared with the frozen G2 witness token SHAs | **372 / 372 identical** |
| Prior loads on this server | CPU FP32 (`kev4b-adapter-fixed-head-gated40-v2-20261005-task7`, 80 backbone forwards); GPU pointer pilot (`kev4b-P4-gpu-pointer-pilot-20261004-D8R4M6`) |
| Memory | BF16 base 9.3 GB, so FP32 ≈ 18.6 GB plus adapter on the 24 GB GPU; tight but expected to fit for 4 rows × ~750 tokens |

## Implication

Every G2 manifest (spans, widths, token gates) is valid input for kev-4B unchanged. A kev-4B screen can reuse the
frozen Stage-A manifest (378 calls, 128/128/122).

## Still needed

1. A kev-4B runner variant. It needs its own model-identity pins, the kev-4B source path, and the 32-layer geometry for
   later patch layers.
2. A CPU self-test of that runner.
3. The user's explicit GPU approval.
