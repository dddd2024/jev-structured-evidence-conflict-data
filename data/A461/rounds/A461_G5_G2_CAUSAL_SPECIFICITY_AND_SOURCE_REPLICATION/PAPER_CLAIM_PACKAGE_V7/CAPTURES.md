# Capture tensors (G2 and mechanism stages M1–M22, all released)

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

## Mechanism stages M1–M22: released (V5)

- **Release:** `a461-mech-captures-m1-m22-v1`, private, targeting `f9d22f1`, published 2026-11-01 with the user's
  approval.
- **Assets:** one tar per stage, `captures_M<i>_A461_MECH.tar`, plus `MECH_CAPTURES_SHA256SUMS`.
- **Size:** 4,042 files, about 4.1 GB in all.
- **Not included:** model weights and the pinned kev-4B `head.pt`, which M19 and M21 need.

**Bundle contents:**
- `ATTEMPT_R1/captures/*.pt`;
- `ATTEMPT_R1/ATTEMPT_R1_CAPTURES_SHA256.txt`, which is also committed as `research/rounds/<stage>/M<i>_GPU_R1/ATTEMPT_R1_CAPTURES_SHA256.txt`
  (commit `f9d22f1`).

**Chain of custody:**
1. **Verified at source.** On `REDACTED_RESEARCH_HOST`, every member file was checked with `sha256sum -c` against the stage's run
   `SHA256SUMS` (captures entries), and the file count was checked against the list. The bundle was then hashed.
2. **Copied and re-hashed.** The bundles were copied to the uploading machine and re-hashed: 22/22 match.
3. **Uploaded and checked.** GitHub's reported asset digest equals `MECH_CAPTURES_SHA256SUMS` for 22/22 bundles.

| Stage | Files | Bytes (tar) |
|---|---|---|
| M1 | 50 | 1,015,951,360 |
| M2 | 72 | 914,421,760 |
| M3 | 88 | 90,634,240 |
| M4–M16, M20 (each) | 88 | 106,711,040 |
| M17 | 120 | 145,510,400 |
| M18 | 620 | 275,732,480 |
| M19 | 620 | 27,054,080 |
| M21 | 620 | 27,054,080 |
| M22 | 620 | 117,268,480 |

Bundle SHA-256 values are in `MECH_CAPTURES_SHA256SUMS`.

The captures are needed to recompute M3, M5, M18, M19, M21 and M22; the other analyses read only the committed raw logits.
