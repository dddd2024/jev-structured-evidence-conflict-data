# Capture access plan (audit item P1-4)

**Problem.** The Stage C, D and E capture tensors (float16 span states) exist only on the authorized server. GitHub
holds only their SHA-256 lists, so an external reviewer cannot recompute H3, or any analysis that depends on the
tensors.

**Proposed delivery.** This will be executed together with `PAPER_CLAIM_PACKAGE_V2`, before the next paper-level claim.

1. **Bundle per stage.** Build `captures_stage_{C,D,E,F}.tar` on the server. Each bundle contains the `.pt` files and
   their `SHA256` list, which must equal the archived `ATTEMPT_R1_CAPTURES_SHA256.txt`. Approximate sizes:

   | Stage | Size |
   |---|---|
   | C | 362 MB |
   | D | about 25 MB |
   | E | about 100 MB |
   | F | about 250 MB |

2. **Publish as release assets.** Upload the bundles as GitHub Release assets of the private repository `dddd2024/jev`,
   on a tag tied to the package-V2 commit. Anyone with repository access, including the auditor, can download them.
   The model weights are not included. The captures are hidden states of public scenes from a public checkpoint, and
   contain no credentials.
3. **Reviewer recomputation (CPU, no model).** `REPRODUCE_V2.md` gives commands that, after extracting a bundle,
   verify the SHA-256 values and re-run `A461_g5_g2_stage_c_analysis_v1.py` (H3). An additional script will recompute
   the cross-row identity and per-cell span statistics directly from the tensors.
4. **Dependencies.** Python ≥ 3.10 and torch ≥ 2.1 (CPU), used only to load the `.pt` tensors. The exact versions used
   are recorded in the package.

**Status.** Planned, not executed. The upload adds data to the user's own private repository, and will be done as part
of package V2.
