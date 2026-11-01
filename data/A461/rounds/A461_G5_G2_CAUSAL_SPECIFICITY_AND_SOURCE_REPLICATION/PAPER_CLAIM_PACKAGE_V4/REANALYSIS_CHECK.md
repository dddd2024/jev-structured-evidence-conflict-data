# Re-analysis check (V4): mechanism route M1–M22

V3's re-analysis of the nine G2 stages is unchanged; see `../PAPER_CLAIM_PACKAGE_V3/REANALYSIS_CHECK.md`.

## Run

- **When:** 2026-11-01, on the GPU server (CPU only, no model load).
- **Python:** 3.12.12. Thread counts were OMP / MKL 24, as in the original analyses.
- **Script:** `recompute_mech_v1.py` (sha256 `00095ea8…`), identical on the server and in this package.
- **Analysis scripts and expected JSONs:** taken from the repository working copy at `8064066`, uploaded as a bundle.
- **Inputs:** the server's archived raw rows, captures, freeze inputs and the pinned kev-4B head.
- **Comparison:** each output against the committed `m<i>_analysis.json`, as parsed JSON with exact equality. M17 is
  compared against v1.1, its analysis of record.
- **Report:** `RECOMPUTE_MECH_R1/RECOMPUTE_MECH.json`, with the console log in `RECOMPUTE_MECH_R1.log`.

## Result: ALL_EQUAL (22/22)

| Stages | Status | Seconds |
|---|---|---|
| M1–M17, M20 (raw logits only, plus captures for M3 and M5) | EQUAL, 0 differing keys | 0.1–2.8 each |
| M18 (kev-4B monitor, 10,000 group-bootstrap draws) | EQUAL | 2281 |
| M19 (readout gain) | EQUAL | 265 |
| M21 (readout push) | EQUAL | 327 |
| M22 (SecJev monitor) | EQUAL | 957 |

**What this shows.** Every mechanism verdict and number cited in v10 reproduces bit for bit from the archived GPU
outputs. That includes the bootstrap CIs and the probe fits, which use float64, seeded resampling and LBFGS.

**What it does not show.**
- It does not re-run any GPU forward. Those are covered by each stage's bitwise anchor replays.
- It does not check the captures' release integrity, because the captures are not released (`CAPTURES.md`).
