# kev-4B Stage-A screen: result note

**Run.** User-approved run with runner `f118ea59` on manifest `01ca5390`. 378/378 calls in 128/128/122, 0 denied
pre-hook calls, 549 s. kev-4B loaded in FP32 with 17.1 GB peak allocated, model identity verified, and the 6 replays
were bitwise equal (runner-enforced).

**Inputs.** These are the frozen G2 Stage-A inputs, unchanged (124 W31 scenes × old/new/SA). The analysis uses the same
frozen script (`A461_g5_g2_stage_a_analysis_v1.py`) and the same strict rule.

| | SecJev-0.8B (Stage A) | kev-4B (general typed-decision model, never trained on SecJev scenes) |
|---|---|---|
| C true on old / new / SA arm | 14.5% / 11.3% / 9.7% | 0.8% / 36.3% / 0.0% |
| Strict donors (old F, new T, SA F) | 4 / 124, 3 groups | **44 / 124, 14 groups** |
| Median dM (new − old) | +0.11 | +1.12 (SA − old: +0.14) |
| Action reject_conflict on new arm | 14 / 124 | 40 / 124 |
| Pattern counts | FFF 101, TTT 9, TFF 7, FTF 4, TFT 2, FTT 1 | FFF 79, FTF 44, TTF 1 |

**Cross-model, per scene.**
- 31 scenes that SecJev missed (FFF) are strict donors on kev-4B.
- Of SecJev's 4 donors, 2 are also donors on kev-4B (run-338 `35253a26`, run-140 `90dbf6d6`). The two run-212 donors
  are FFF on kev-4B.

**Implications.**
1. **Model-specific severity.** The severe miss rate (88.7%) belongs to the SecJev-0.8B specialist. A larger general
   kev model still misses 63.7% of appended conflicts, but discriminates them cleanly from duplicates (0% SA false
   positives). The paper's behavioural claim must therefore be stated per model.
2. **Mechanism replication becomes possible.** 44 donors from 14 groups lift the donor-concentration ceiling
   (audit P0-2) for a kev-4B transplant/repair stage. kev-4B has 32 layers with full attention every 4th layer, so the
   patch window must be re-located; it cannot be assumed to be layer 11.
3. **Smaller margins.** kev-4B margins are small (artifact temperature 2.41; most |M| < 2.5). Near-threshold hosts
   are therefore common, and flips will be less informative than margin effects.
