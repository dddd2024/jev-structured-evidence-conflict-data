# A461_G5_G2_STAGE_A_GPU_SCREEN_RUNNER_G0_V3 — incremental L2 packet (answers L2 REJECT 277fdb7)

Status: **L1 COMPLETE 46/46 PASS, 0 GPU, 0 native forwards.** This is one incremental L2 request for the new release candidate.
It is not a GPU admission. No real GPU admission file exists; every GPU-shaped admission used in L1 is synthetic, labelled `l1_synthetic_not_an_authorization`, and exercised only up to `--pre-model-gate-only`.

## Exact blobs

| file | git blob |
|---|---|
| `A461_g5_g2_stage_a_gpu_screen_runner_g0_v3.py` (runner, new file; V2 `b0b9f6ee` stays as reviewed) | `b78da9c0476f0558cd77fa9771c04d020830dede` |
| `A461_g5_g2_fake_kev_model_v1.py` (adds `sigkill@N`) | `4f9fef35c23725d0ab71948fc93e222e935e7b03` |
| `A461_g5_g2_stage_a_l1_tests_v2.py` | `06fcd8c7b920fbfc9fd0124e93866334fadb87e1` |
| manifest / roster / questions (unchanged) | `01ca5390` / `1bc84bf5` / `66c1f95e` |
| pinned model identity digest (`identity_digest(MODEL_IDENTITY)`) | in `L1_test_receipt.json` → `model_identity_sha256` |

The server copies hash to the same blobs. Tested command: `python3 A461_g5_g2_stage_a_l1_tests_v2.py --repo-root ~/wjc/jev-checkout --out ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1/G2_STAGE_A_L1V2_RUN2`, using the kev08b venv (Python 3.12). Every runner subprocess ran with `CUDA_VISIBLE_DEVICES=""`.

## Findings → fix → L1 evidence

| finding | fix in V3 | L1 tests (group) |
|---|---|---|
| **P0-1** gpu CLI could swap manifest/roster/questions blobs and the batch plan; no ≤128 per batch | `gpu_pin_gate()` (gpu backend, full and pre-model): the given blobs must equal the pins; `expect_total == 378` and `expect_batches == [128,128,122]`; no `--quota-root`. The admission must be mode `GPU` and bind `frozen_inputs` == pins, `approved_batch_plan == [128,128,122]`, 378 / 3, `model_identity_sha256`, review PASS on this blob, and user approval. In **every** mode `batch_plan()` requires each cap ≤ `RUN_CAP=128`, and `batch_guard` uses `min(planned, 128)`. A full gpu run's out dir must be a direct child of `G2_STAGE_A_GPU_RUNS` | `gpu_admission_pre_model`: **reviewer's 134/122/122 re-partition** (same 124 scenes, byte-identical roster/questions blobs) refused; manifest-only override refused; plan-only override (128,122,128) refused; quota-root override refused; admission plan / frozen_inputs / runner blob / identity digest / no user approval each refused; an L1_FAKE admission on the gpu backend refused; a 134/122/122 plan on the **fake** backend refused by the cap; a full gpu run outside the runs root refused with nothing created |
| **P0-2** consumed quota came from caller JSON (default 0); a new out dir could reuse the approval | `QuotaLedger`: one append-only, fsync'd `ledger.jsonl` per `admission_id` under the fixed `G2_STAGE_A_QUOTA_LEDGER`, held under an exclusive `flock` for the whole attempt. **Every call is reserved before `model.forward`.** Pre-hook calls that no reservation covers are charged as `unreserved_physical`. Consumed = ledger only; a caller value that differs is refused as stale. Before each attempt, `reconcile_ledger()` checks every `*/attempt_manifest.json` of this admission in the runs root. An unknown dir (ledger lost or stale), a ledgered dir that is missing, or saved call rows exceeding reservations all **fail closed** | `durable_quota_ledger`, all using the **same approval with different out dirs**: after a complete run, `consumed=0` is refused as stale and a plain reuse is refused; partial (throw at 4) is charged 4, a resume within a 15-call approval completes, and a 3rd attempt is refused; **SIGKILL inside call 5** leaves no receipt and no close, but the ledger holds 5 and the next attempt is refused and reports the unclosed prior attempt; ledger removed → refused; ledgered dir renamed → refused; 3 reservations deleted from the ledger → refused (11 rows > 8); lock held by another process → refused. The cap tests show the ledger charges 127+1 unreserved = 128, etc. |
| **P1-1** checkpoint/base/source not hash-pinned | `MODEL_IDENTITY` pins per-root digests over per-file SHA-256 for: the checkpoint dir (28 files), the base model+tokenizer dir (8 files, incl. 1.75 GB safetensors), and the kev source (`kev/**/*.py` + `pyproject.toml` + `uv.lock`, 26 files). The pins were computed twice on the server, identically. They are verified before any load (gpu, full and pre-model) and persisted in the receipt | `well_formed_gpu_admission_reaches_pre_model_gate` (observed == pinned), `model_identity_verify_unit` (tampering any of the 3 roots is refused), `admission_model_identity_mismatch_refused` |
| **P1-2** L1 never drove a well-formed GPU admission up to the load | `--pre-model-gate-only` runs every gpu gate (pins, identity, read-only ledger reconcile, 372 token + tuple gates), then exits before torch import and model load | `well_formed_gpu_admission_reaches_pre_model_gate`: COMPLETE, model_loads 0, CUDA not initialized, the real GPU ledger is untouched; plus the 12 negative cases above |

V2 behaviour is kept and re-tested: replay inheritance and negative cases; full fake path on the real 378 manifest (128/128/122, 378 reservations); replay bitwise pass and fail; per-batch cap+1 refused before the model in each of the 3 batches; FORWARD_FAILED vs INVALID_OUTPUT; path guards. Across 32 runner receipts: gpu_model_loads=0, CUDA never initialized; the real `G2_STAGE_A_GPU_RUNS` / `G2_STAGE_A_QUOTA_LEDGER` roots were never created.

## Disclosed

- One fix inside this L1 cycle: RUN1 (43/46) showed that when reconciliation itself refused, the finalizer hit a missing `quota_ledger` key and wrote **no receipt**. Fixed: the key is created before reconciling and the finalizer is defensive. RUN2 is 46/46. Both logs are on the server.
- The GPU load branch (checkpoint load, torch flags) is unchanged from G0/V2. L1 does not execute it (by design); the pre-model gate stops right before it.
- Pre-model mode reads the ledger without locking or writing. Only a full run takes the lock and writes.
- Committed evidence omits the fake raw logits and the fixture repos (still on the server).

## After L2

An L2 PASS bound to `b78da9c0` would let me ask the user for a fresh approval of 378 calls / 128+128+122. A real `admission_id` would then be written, and the run would go to `G2_STAGE_A_GPU_RUNS/` with the ledger in `G2_STAGE_A_QUOTA_LEDGER/`. Then strict qualification analysis (<2 donors → HOLD), then L3.
