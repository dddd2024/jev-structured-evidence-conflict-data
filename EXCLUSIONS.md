# A461 public archive publication boundaries

- 1,798 A461 round files have exactly matching Git blobs with the private source, including the two original M19/M21 derived-direction tensors and additional original mechanism handoff records.
- 187 round files were published with private-machine identifiers removed, including three mechanism handoff records and one quota ledger. Original and public SHA-256 digests are recorded in `MIGRATION_MANIFEST.json`.
- 24 historical DOCX/PDF manuscript drafts are kept private by author decision (2026-11-02); they are not experimental data or protocols. All 24 paths are listed in `MIGRATION_MANIFEST.json`.
- 127 additional original experiment protocol and research-context files are mirrored under `data/A461/context`, documented in `CONTEXT_MANIFEST.json`.

- All 28 original capture tar archives (G2 and M1-M22) are mirrored byte-for-byte to this repository's Releases, plus the M23 captures newly bundled from the research server (see `CAPTURE_INVENTORY.json`).
- 292 server-only run records are published under `data/A461/server_supplement` (91 with machine paths redacted; original and published SHA-256 in `SERVER_SUPPLEMENT_MANIFEST.json`).
- Not published: 4,553 runner self-test / L1 test outputs (~470 MB) produced on fake or deliberately tampered models to validate runners before GPU admission, and their test-capture tensors. They are not experimental observations; each is listed with size and git blob in `SERVER_SUPPLEMENT_MANIFEST.json`.

Private originals remain untouched. This archive is not a redistribution license for model weights or third-party datasets.
