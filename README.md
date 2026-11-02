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
- [`data/A461/server_supplement/`](data/A461/server_supplement/) and [`SERVER_SUPPLEMENT_MANIFEST.json`](SERVER_SUPPLEMENT_MANIFEST.json) — run records present only on the original research server, from a blob-level audit of all 7,011 non-capture server files.
- [`CONTEXT_MANIFEST.json`](CONTEXT_MANIFEST.json) — SHA-256 provenance list for these 127 additional exact-copy research files.

**Dataset status:** 1,985 of 2,009 A461 round files published: 1,798 byte-identical copies (including M19/M21 original derived-direction tensors) and 187 private-machine-identifier-redacted copies. The remaining 24 are historical manuscript drafts (DOCX/PDF), withheld as non-data. A further 127 original protocol, audit, literature and governance files are available under `data/A461/context/`, and 292 additional run records found only on the original research server (launch scripts, logs, admissions, failed-attempt records) are under `data/A461/server_supplement/`. All raw activation captures (G2 stages C–F, K-B, K-C; M1–M23) are published as Release assets.

**Hidden-state captures:** float16 `.pt` span/decision-state captures are distributed as tar assets in [GitHub Releases](../../releases): `a461-g2-captures-stage-c-v1`, `a461-g2-captures-def-k4b-v1`, `a461-mech-captures-m1-m22-v1`, `a461-mech-captures-m23-v1` (31 assets, ~6.0 GB). Each tar contains its per-member `ATTEMPT_R1_CAPTURES_SHA256.txt`; tar-level SHA-256 digests and download URLs are in [`CAPTURE_INVENTORY.json`](CAPTURE_INVENTORY.json).

## Provenance and interpretation

The original experimental repository is private `dddd2024/jev` at commit `03302ef7867606d2cec527ec0aa8a5abdd0257ee`. All copied files are unchanged; per-file SHA-256 digests are recorded in the manifest. The data includes raw model scores and original preregistrations as well as failures and negative controls. Not every causal or deployment-security hypothesis was established; check the individual reports and qualification limits.

No original model checkpoint or weights, unreviewed third-party material, secrets, or private infrastructure details are deliberately published. This repository does not grant rights to third-party models, third-party datasets, or unlicensed code.

## Reproduction

Individual rounds provide original scripts, frozen manifests, JSONL native scores, JSON summaries and available SHA lists. Some scripts reference unavailable original model checkpoints, omitted capture tensors, or withheld execution metadata. Consequently, score-level reanalysis may be possible where frozen inputs are present, but **end-to-end full model re-execution is not guaranteed** from this public copy alone.
