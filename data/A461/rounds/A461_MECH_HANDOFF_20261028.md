# A461 mechanism route — handoff (2026-10-28, night)

**State at handoff:**
- The M5 GPU run is going on `REDACTED_RESEARCH_HOST`, with about 45 minutes left at handoff.
- A server-side watcher runs the frozen M5 analysis automatically when the run exits, and only if the receipt says COMPLETE.
- Nothing else is running.
- The final paper-level audit has **not** been triggered; it needs the user's go-ahead.

## Chain so far (all preregistered, self-tested, bitwise-anchored)
| stage | prereg / result | finding |
|---|---|---|
| M1 | c235549 | The L11 append-span representation carries a signed, round-specific conflict evaluation (REL_SUPPORTED) |
| M2 | 3d561c9 / ca949e7 | The writer is L11 full attention (MIXER_WRITER@L11): the donor's L11 `self_attn` output at the span repairs 51/104 cells round-specifically; the MLP never does |
| M3 | 342e559 / e9d9746 | Heads 8–14 cooperate in that write; head 10 is most necessary (prereg verdict SPARSE_HEADS, H\*={10}, from NEC only). Span-to-partner attention is weakly round-gated, and alike in hosts and donors |
| M4 | 4c8de7a / f5bbf87 | The write splits exactly into key-class contributions. Necessary: OTHER_ITEMS (drop → 8) and CONTEXT (drop → 23), verdict LOCUS:CONTEXT+OTHER_ITEMS. The partner part is neither necessary (drop keeps 41/51) nor sufficient (1/51). Partner value swap: V_NONE (0). Caveat: the necessary classes are the largest ones |
| M5 | 7187842 / *pending* | Size vs direction vs content: `only_BULK` / `drop_BULK`; `dir_C` = class directions rescaled to the full patch's size; `dir_RAND` null; `xdonor_BULK` (BULK from a third donor) |

Fixed facts (data):
- **Pre-span keys are shared.** Every key before the span is token-identical between a scene's new and ROUND arms. The round token sits at the span end.
- **Uniform widths.** The span is 31 tokens and the partner item 33 tokens in every scene.
- **Persistent non-repair.** Host 2a4f596d is never repaired, in any stage.

## Resume M5 (next session)
1. On the server (`ssh REDACTED_RESEARCH_HOST`, `cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1`):
   - `cat M5_AFTER_RUN.done` should read `analysis exit 0 …`;
   - check `M5_GPU_RUNS/ATTEMPT_R1/execution_receipt.json`: status `COMPLETE_A461_MECH_M5`, `physical_forwards` 2540, `bitwise_vs_m1` and `bitwise_vs_m3` = `checked`;
   - check that `M5_ANALYSIS_R1/m5_analysis.json` exists.
   - If `.done` is missing, the watcher is still waiting (`pgrep -af M5_after_run`). If it reads "not COMPLETE", read the receipt's `error_message` and the run log `M5_GPU_R1.log`.
   - The run's pid was 380814; the watcher is `M5_after_run.sh`.
2. Fetch the outputs into `research/rounds/A461_MECH_M5_MAGNITUDE_DIRECTION_GPU/`, as for M4:
   - `M5_GPU_R1/`: everything in `M5_GPU_RUNS/ATTEMPT_R1/` except `captures/`, plus `M5_GPU_R1.log` and the pre-model gate receipt;
   - `M5_ANALYSIS_R1/m5_analysis.json`;
   - verify with `SHA256SUMS`.
   - The captures (about 100 MB) stay on the server.
3. Write `M5_RESULT_R1.md`, modelled on `../A461_MECH_M4_KEYCLASS_VALUE_GPU/M4_RESULT_R1.md`:
   - the preregistered outcome table (gate, BULK_SUF/NEC, D, RAND_NULL, verdict, content);
   - the full per-arm table;
   - α statistics, with a warning about large α (SELF and PARTNER differences are small, so α can be ≫ 1);
   - Δ geometry, per-host S, and leave-one-group-out.
4. Commit and push, then update memory (`a461-g2-stage-a-status.md`, `MEMORY.md`).

## M6 options by M5 outcome (choose after reading M5; not frozen)
| M5 outcome | suggested M6 |
|---|---|
| MAGNITUDE_SUFFICES (random direction repairs) | Size test: host + β·(host's own L11 write) or random directions at graded sizes. Is the conflict decision a threshold on write magnitude? |
| PARTNER_DIRECTION | Split the partner contribution into token groups (author / block / kind / received / round fields) at matched size |
| BULK_DIRECTION + XD_HOLDS | A generic "donor-like context" component. Patch the **mean donor BULK direction** into every host, and do a low-rank (PCA over donors) version of it |
| BULK_DIRECTION + XD_FAILS | The scene's own context content matters. Per-item decomposition of OTHER_ITEMS: earlier-round votes, same-round non-vote items, and so on |
| NO_SINGLE_DIRECTION | Pairwise class combinations at matched size |

Independent of M5:
- replicate the M2/M3 chain on SecJev-0.8B (long-pending);
- or pause and write M1–M5 up as the paper's mechanism section.

## How each stage was built (reuse)
- **Derivation.** Each stage's freeze, runner and self-test is derived from the previous stage by a checked-substitution script; every `rep()` asserts its match count. Derive scripts live in the session scratchpad and are not committed; the derived files are, with their blobs pinned.
- **Freeze.** Derive the freeze, run it on the server (CPU + tokenizer) into `M?_FREEZE_R1`, and pin the manifest and design blobs in the runner.
- **Smoke test.** Before the full self-test, run a one-cell fake manifest (44 captures + one cell's patches) with `--backend fake --allow-manifest-blob --expect-batches N --quota-root`, under `OMP_NUM_THREADS=8`.
- **Self-test.** About 20–40 min on CPU. Then dry-run the analysis with `--fake-dry-run` on `M?_SELFTEST_R1/T2_fullpath`.
- **Admission and commit.** Write the admission from the previous one, carrying the standing-authorization quote verbatim. Commit the prereg bundle *before* the GPU run. Run the pre-model gate. Create `M?_GPU_RUNS/` (the runner refuses if the parent is missing). Launch with `setsid nohup … & disown`.
- **Throughput.** About 1.45–1.5 s per call on GPU.

## Gotchas
- **Thread limit.** The server's per-user limit is `ulimit -u` = 256 and nproc = 64. Two torch processes at once exhaust it (`libgomp: Thread creation failed`), so self-tests cap OpenMP/MKL threads at 8. GPU runs are single-process and unaffected.
- **Blob identity.** The local repo is a sparse checkout with CRLF conversion. Verify blobs with `git hash-object`, and use `git cat-file` for exact bytes.
- **Push retries.** Push from this machine sometimes fails on a TLS handshake; retry.
- **Python.** Use the venv python `~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3` (3.12), not the system 3.8. All outputs go under `~/wjc`.
- **Governance.** Standing GPU authorization since 2026-10-27; there is no per-experiment approval. Ask the user only before the final paper-level audit and before anything outward-facing.
