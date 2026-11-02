# A461 handoff addendum (2026-11-01, ~11:00 +08:00)

This updates [A461_MECH_HANDOFF_20261101.md](A461_MECH_HANDOFF_20261101.md). Its decisions and gotchas still apply. **M20, M21 and M22 are all done; the high-standard experimental plan is complete.**

| stage | commits | headline |
|---|---|---|
| M21 readout | bc61ce9 / 0a4ce0a | NOT_READABLE at L19 and L31. A 20% \|h\| push along the held-out mean-difference direction moves the missed margin by ≤ 0.07 (a repair needs ≈ 0.9) and moves it toward accept; random pushes are about as inert. Only the decide token was steered; the head also reads the option tokens |
| M22 SecJev | 40c0f59 / 1e897c7 | M18 replicates on SecJev-0.8B: ENCODED_AT_L11 (0.964) + ABOVE_SURFACE, GENERIC_MATCHES, MONITOR_USEFUL (57% at 1.5% FV). The best detector is the L11 span residual (90% at 0.9%). Natural false veto 8.9 / 8.9 / 8.1 / 5.6% (old / SA / ROUND / OUTSIDER) |

**M22 prereg deviation before commit:** the WIP analysis (db90bbcb) crashed on the fake dry run, because the fake head rejects every row and leaves no MISSED or BENIGN rows. The verdict lines were made None-safe (5225412d) before the prereg commit. This is documented in the prereg.

## Final mechanism and failure statement
1. The conflict is decodable early (M18), on both models (M22).
2. At L11, round-keyed context read by heads 8–14 is sufficient in hosts (M1–M5) and necessary in most donors (M20, partial). This is kev-4B only.
3. In missed scenes the conflict is present at the decision position but is not read: it is near orthogonal to the head gradient, and neither gain (M19) nor a 20% push (M21) moves the decision. The causal half is kev-4B only; decodability holds on both models.

## Next: the paper package
- v10 manuscript, CLAIMS_EVIDENCE_MAP, LIMITATIONS (all failed and edge criteria; no independent scene distribution; the causal half is kev-4B only), NOVELTY, a recompute script, and the V3 P1/P2 leftovers.
- **Ask the user** before the capture release and before the final audit.
