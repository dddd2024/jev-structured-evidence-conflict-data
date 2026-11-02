# A461 Structured-Evidence Conflict — Public Experimental Archive

Research-data mirror for the A461 experiments on the typed model scorers **kev-4B** and **SecJev-0.8B**.

## Experimental files

- [`data/A461/rounds/`](data/A461/rounds/) — curated copy of all A461-prefixed experiment directories, covering G3–G5, G2 follow-up, M1–M23, and CPU controls.
- [`data/A461/M23/`](data/A461/M23/) — the earlier M23 first release, retained for link stability.
- [`MIGRATION_MANIFEST.json`](MIGRATION_MANIFEST.json) — original paths, full SHA-256 checksums, complete exclusions, and original source commit.
- [`EXCLUSIONS.md`](EXCLUSIONS.md) — why some files are withheld.
- [`data/A461/context/research/experiments/`](data/A461/context/research/experiments/) — **14 original A461 experiment protocols, runbooks, and design drafts**.
- [`data/A461/context/research/analysis/`](data/A461/context/research/analysis/) — 98 associated independent research analyses, source audit scripts and receipts.
- [`data/A461/context/research/literature/`](data/A461/context/research/literature/) and [`data/A461/context/research/literature_preflight/`](data/A461/context/research/literature_preflight/) — literature and preregistration gate materials; plus two governance records under `data/A461/context/research_governance/`.
- [`CONTEXT_MANIFEST.json`](CONTEXT_MANIFEST.json) — SHA-256 provenance list for these 127 additional exact-copy research files.

**Dataset status:** 1,980 of 2,004 A461 round files published: 1,796 original-byte copies (including M19/M21 derived-direction tensors) and 184 machine-identifier-redacted copies. The remaining 24 are manuscript drafts (DOCX/PDF), withheld pending publication review. In addition, 127 original protocol, audit, literature and governance files are available under `data/A461/context/`. Large original activation captures are not yet confirmed in public Releases. The private repository and server originals remain unchanged.

**Hidden-state captures:** Very large float16 `.pt` captures are distributed separately when cleared and uploaded, via [GitHub Releases](../../releases). Do not infer their availability from entries in the raw JSONL files.

## Provenance and interpretation

The original experimental repository is private `dddd2024/jev` at commit `03302ef7867606d2cec527ec0aa8a5abdd0257ee`. All copied files are unchanged; per-file SHA-256 digests are recorded in the manifest. The data includes raw model scores and original preregistrations as well as failures and negative controls. Not every causal or deployment-security hypothesis was established; check the individual reports and qualification limits.

No original model checkpoint or weights, unreviewed third-party material, secrets, or private infrastructure details are deliberately published. This repository does not grant rights to third-party models, third-party datasets, or unlicensed code.

## Reproduction

Individual rounds provide original scripts, frozen manifests, JSONL native scores, JSON summaries and available SHA lists. Some scripts reference unavailable original model checkpoints, omitted capture tensors, or withheld execution metadata. Consequently, score-level reanalysis may be possible where frozen inputs are present, but **end-to-end full model re-execution is not guaranteed** from this public copy alone.
