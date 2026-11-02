# Capture tensors (G2 stages released; mechanism stages M1–M22 server-side)

The span-state captures (float16 `.pt`) are published as GitHub Release assets of the private repository
`dddd2024/jev`. Anyone with repository access can download them. Both release tags point at `5ef7a16`, the commit that
archived the last GPU stage. The model weights are not included.

## Releases

| Release tag | Asset | Bytes | Files | Used by |
|---|---|---|---|---|
| `a461-g2-captures-stage-c-v1` | `captures_stage_C_A461_G2.tar` | 378,542,080 | 248 | Stage-C H3 (frozen analysis reads the tensors) |
| `a461-g2-captures-def-k4b-v1` | `captures_STAGE_D_A461_G2.tar` | 24,432,640 | 16 | capture checks |
| `a461-g2-captures-def-k4b-v1` | `captures_STAGE_E_A461_G2.tar` | 97,566,720 | 16 | capture checks, cross-row identity |
| `a461-g2-captures-def-k4b-v1` | `captures_STAGE_F_A461_G2.tar` | 243,906,560 | 40 | capture checks, cross-row identity |
| `a461-g2-captures-def-k4b-v1` | `captures_K4B_KB_A461_G2.tar` | 203,192,320 | 10 | capture checks, cross-row identity |
| `a461-g2-captures-def-k4b-v1` | `captures_K4B_KC_A461_G2.tar` | 833,075,200 | 41 | capture checks, cross-row identity |

The bundle SHA-256 values are in `CAPTURES_SHA256SUMS`. GitHub reports the same digest for each asset.

## Bundle contents

Each bundle contains:
- `ATTEMPT_R1/captures/*.pt`;
- the stage's `ATTEMPT_R1_CAPTURES_SHA256.txt`, which is also archived in the repo under
  `G2_*_GPU_R1/G2_*_GPU_RUNS/`.

## Chain of custody

1. **Verified at source.** On `REDACTED_RESEARCH_HOST`, every member file was checked with `sha256sum -c` against the stage's
   archived per-file list, and the bundle was hashed.
2. **Copied and re-hashed.** Each bundle was copied to the uploading machine and hashed again; the hashes matched.
3. **Uploaded and checked.** After upload, the asset digest that GitHub reported matched.
4. **Re-checked from the bundles.** On 2026-10-27:
   - each bundle was extracted into a fresh directory;
   - `verify_captures_v1.py` passed for all six stages (371 files);
   - the frozen Stage-C analysis, run on captures extracted from the release bundle, reproduced the archived
     `stage_c_analysis.json` byte for byte.

   See [REANALYSIS_CHECK.md](REANALYSIS_CHECK.md).

## Not released

- **Stage B and the two screens** (Stage A and the kev-4B screen) wrote no captures; their analyses use logits only.
- **Model weights and base checkpoints.** Both identities are pinned by hash in the runners.

## Dependencies

- Python ≥ 3.10.
- torch ≥ 2.1, CPU only, to load the tensors.
- The checks above were run with Python 3.12 and torch 2.8.

## Mechanism stages M1–M22 (V4): not released

The mechanism-stage captures stay on the GPU server, under `<work dir>/M<i>_GPU_RUNS/ATTEMPT_R1/captures/`. Each stage's
`SHA256SUMS`, committed in its `M<i>_GPU_R1/` folder (the copy from the run), lists every capture file with its SHA-256,
so a later release can be checked file by file. **Publishing them as a release is outward-facing and has not been done.
It needs the user's go-ahead.**

| Stage | Bytes | Files | Needed to recompute |
|---|---|---|---|
| M1 | 1,015,890,946 | 50 | — |
| M2 | 914,344,840 | 72 | — |
| M3 | 90,545,816 | 88 | M3 analysis |
| M4–M16, M20 (each) | 106,617,592 | 88 | M5 analysis (M5 only) |
| M17 | 145,394,328 | 120 | — |
| M18 | 275,127,020 | 620 | M18 analysis |
| M19 | 26,566,044 | 620 | M19 analysis |
| M21 | 26,566,044 | 620 | M21 analysis |
| M22 | 116,621,292 | 620 | M22 analysis |

The total is about 4.1 GB. The analyses of M3, M5, M18, M19, M21 and M22 read captures; the rest read only the committed
raw logits. M19 and M21 also read the pinned kev-4B head (`head.pt`, sha256 `dd633435…`). `recompute_mech_v1.py` was run
on the server, where all of these exist.
