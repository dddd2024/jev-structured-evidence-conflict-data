# A461 mechanism route M1–M16: consolidation (2026-10-31)

**Status:** document and CPU only. No new GPU run, no new verdict, and no paper-level audit. Every number below is copied from the stage result files and their archived analysis JSON. Where a later stage revises an earlier reading, the revision is stated.

**Purpose:**
- Fix what the 16 mechanism stages support, at which evidence level and over which hosts.
- List which preregistered criteria failed.
- State what the stages mean for the safety question.
- Name what is still missing before the paper-level audit.
- Follow the order of the [novelty × security-value standard](../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §9 at the level of the whole route.

**Requested by the user** on 2026-10-31 ("Yes, consolidate"), after M16.

## 1. What was run
- **Scale:** 16 preregistered stages, 70,338 kev-4B forwards in all, about 29.3 GPU hours.
- **Common protocol for every stage:**
  - a self-test on a fake model before any GPU forward;
  - a pre-model gate;
  - a single ledger attempt with 0 denied calls;
  - bitwise anchor replays of earlier stages (M1/K-C, M3 `full` 208 rows, and M6 `meanD_host` 208 rows from M7 on), all of which passed;
  - leave one donor group out (14 splits) for every verdict.
- **Captures:** the M1–M16 capture tensors stay on the server, with hashes archived in each stage's `SHA256SUMS`. They are not yet in a release (see §8).

| stage | prereg → result | forwards | raw blob | preregistered verdicts (LOGO stability) |
|---|---|---|---|---|
| M1 | 227c628 → c235549 | 498 | (K-C cells) | REL_SUPPORTED (round), ROLE_ABSTRACT (author); J_round 0–1 in every split |
| M2 | 3d561c9 → ca949e7 | 2532 | e1c4b34f | MIXER_WRITER@L11 (12/14; 2/14 move L_f to 8 → NEITHER_ALONE) |
| M3 | 342e559 → e9d9746 | 7740 | a8c0fa6b | SPARSE_HEADS, H\* = {10} by necessity (head 10 in 14/14; heads 8 / 9 / 14 join in 8/14); A1 DONOR_GATED + HOST_GATED |
| M4 | 4c8de7a → f5bbf87 | 2956 | 46274e8e | LOCUS:CONTEXT+OTHER_ITEMS; V_NONE (14/14) |
| M5 | 7187842 → 695f4fe | 2540 | f03ce4e9 | BULK_DIRECTION; XD_HOLDS; RAND_NULL holds (14/14) |
| M6 | df835a9 → 18aae99 | 2540 | 2147311c | SHARED_DONOR_COMPONENT; NOT_LOWRANK_LE64 (14/14) |
| M7 | 7725863 → edc49cb | 2748 | 0383fccf | NOT_DELTA_LOWRANK_LE64; LR64_BASIS_LIMITED; NOT_MEANDIFF; RC_INSUFFICIENT (14/14) |
| M8 | 2a4fea7 → d1d9125 | 3164 | 997c9b71 | XDELTA_LOWRANK:16; TWOPART:16; POOLED_CONTRAST_SUFFICES; CS_SUFFICIENT:0.5 (12/14, else 1.0); CONTRAST_NONADDITIVE (14/14) |
| M9 | 7124fd7 → da03730 | 4828 | c74e5117 | GAIN_MIXED; GAIN_TMIN:1.0; CONTRAST_IN_WRITER_HEADS; SPLIT_NULL **fails** → CONTRAST_OUTSIDE_COMMON_SUBSPACE_UNRESOLVED |
| M10 | 73784df → c4c4aeb | 5244 | 755c74e1 | CONTRAST_SM_IN_WRITER_HEADS+H10+WX10; CONTRAST_AT_P29; SHIFT_NEEDS_ALL_POSITIONS; SPLIT_NULL5 **fails**; GAIN_TFINE:0.8 (11/14) |
| M11 | b5d1756 → 76e6537 | 5244 | 393f0d6e | AMPLITUDE_ONLY_EXCLUDED; P30_INERT_AT_P29_NORM; SHIFT_NEEDS_CONTEXT_POSITIONS; SHIFT2930_UMIN:NONE; SPLIT_NULL10 **fails** |
| M12 | ee05402 → b72a451 | 7740 | cc79f23a | P30_OPPOSES (2-cell lead); FLIP_DOES_NOT_LOWER_THRESHOLD; SHIFT_FIELDS_NEEDED:BLOCK (12/14); SUFFICE:NONE; SUBSPACE_BELOW_COSINE (264c458d) |
| M13 | 3a24afb → ceeda48 | 7116 | cdbf677b | SHIFT_AB_SUFFICES / _C29_ / _S05_ (12/14); SHIFT_AB_NEEDED; AB_LOCATION_SPECIFIC; TILT_NO_EFFECT and REM_DIRECTION_NOT_SPECIFIC (floors and ceilings) |
| M14 | d686b4e → bf12ae7 | 6956 | d2ac9f42 | AB_THRESHOLD_MIXED; SHIFT_2930_NEEDED; AB_T05_INSUFFICIENT; TILT_OPPOSES (7/16) / SUPPORTS (5/16) → REM_MIXED; REM3_DIRECTION_MIXED by S; REM3C_DIRECTION_SPECIFIC by C |
| M15 | 103483a → 0e3339a | 5500 | b6807b13 | Q1_GAIN_LOC_ONLY (**7/14**); DOSE_OPPOSES; NULL24_S/C_DIRECTION_SPECIFIC; ROUND_A_RANK_264C 0/24 |
| M16 | 996483a → 454d2b9 | 2992 | 1d74b63b | **W_LINEAR_FAILS** (264c458d LINEAR_HOLDS + S_C_DISSOCIATE; 1fb5651c and 4bcbaf15 LINEAR_FAILS) |

## 2. Native safety endpoint and Gold
- **Endpoint:** the typed kev-4B readouts on host new of the conflicting twins_streamlet DEV scenes, as in K-C.
  - M = logit(conflicting_vote = true) − logit(false).
  - A = logit(reject_conflict) − max(logit(accept), logit(wait)).
  - JOINT = M > 0 ∧ A > 0 in the same forward pass.
- **Gold:** the source-internal executable rule. The appended valid equivocation vote makes `reject_conflict` correct.
- **Repair count:** S counts cells where the main-donor patch (donor new, a recognized appended conflict) makes the host JOINT, while the round-donor patch does not. The round donor is the same scene with only the vote's round changed to a non-candidate round, so it is not a conflict.
- **Evidence level:** S1–S2. The underlying error is a native action error against source-internal Gold (K1: kev-4B misses 63.7% of appended conflicts). Every M-stage effect is an artificial activation intervention on that error. None is an observation of the natural error path.

## 3. Main results by scope
The 104 cells cross 14 donors with 8 hosts. Rules on S are descriptive decision rules over shared hosts, not independent tests. From M6 on, most arms are pooled-donor arms, which act host by host: they are effectively 8 host replicates. Per-host S is therefore the honest unit, and claims are tiered by how many hosts carry them.

### Tier A: holds across hosts and donor groups (M1–M5, own-donor patches)
1. **The L11 span state carries a signed, round-specific conflict evaluation (M1).**
   - Changing only the donor vote's round turns repair (J 53) into suppression (J 1). dM_main > dM_round in 104/104 cells, with a majority in 14/14 groups. No host is repaired by the round arm in more than 1 cell.
   - The round arm actively pushes toward "no conflict": dM_round < 0 in 99/104 cells.
   - Changing the author keeps the repair (okalt J 66).
   - This separates relation validity from surface token form at the same position. It answers the V2 audit's H-CLS confound for this locus.
2. **L11 full attention writes it; the span MLP never does (M2).**
   - The donor's L11 `self_attn` output alone repairs 51/104 (resid L11: 52), with frac 0.99. MLP patches at L8–L11 give ≤ 3.
   - A weaker round-specific signal already sits in the L ≤ 7 residual (resid L7–L10: S 20–24, all SPEC). The formation layer is on a threshold edge (2/14 splits).
3. **Heads 8–14 write it together, and head 10 is most necessary (M3).**
   - No single head repairs: the best is S 3.
   - Dropping head 10 from the full patch cuts S from 51 to 16; dropping heads 8, 9 or 14 brings it to 26–27.
   - Span-to-partner attention mass is similar in hosts and donors. By the preregistered rule, the host deficit is not where the heads look.
4. **The write reads the bulk of the state, not the conflict partner (M4).**
   - Dropping OTHER_ITEMS leaves 8/51 repairs, and dropping CONTEXT leaves 23/51. Dropping PARTNER keeps 41/51.
   - Donor partner values under host attention repair 0 (V_NONE).
5. **The bulk part acts by direction, not size, and is generic across scenes (M5).**
   - The donor-minus-host BULK direction at matched size repairs 48/51. A random direction at the same size repairs 1.
   - A third, unrelated donor's BULK part keeps all 51 repairs (XD_HOLDS).

### Tier B: pooled decomposition, 3 of 8 hosts (M6–M11)
Pooled-donor arms repair hosts 1fb5651c, 264c458d and 4bcbaf15 (13/13 each) and none of the other five.

6. **A pooled donor BULK component repairs 3 hosts (M6).**
   - `meanD_host`, the mean of 12 other donors' BULK parts, gives S 39 with J_round 0.
   - The pooled *host* null gives 17: 13 on 1fb5651c and 4 on 264c458d. The donor/host difference rests on 264c458d and 4bcbaf15.
   - The round contrast is common to both pools; donors add the size of the main push.
7. **The repair splits into a common shift and a small pooled round contrast c, and is strongly non-additive (M7, M8).**
   - The common shift alone flips main and round alike (cs0: J 28 / 28). It is a pure threshold push.
   - c alone changes the host by 0.04 of `full` and repairs nothing (M7 rcD S 0).
   - On top of the shift, ∓ ½c already separates the sources (cs05: J 39 / 1). The same 2c gap moves C by 16.7× more on the shift than on the plain host.
   - The contrast that works is pooled, not the cell's own (tpD64 38 vs tp64 37). A cross-kind Δ basis of rank 16 recovers the specific repair (xdlr16_sm S 36).
8. **The shift is thresholded per host (M9, M10).**
   - At s = 1, half the shift gives essentially nothing (L(1) = 0.007). The fine grid switches hosts on one at a time: 1fb5651c at t ≤ 0.6, 264c458d at 0.8, 4bcbaf15 at 0.9.
9. **The contrast acts through the writer heads' slice and at the changed-token position.**
   - **Heads (M10):** at matched norm, any writer slice (heads 8–14, head 10 alone, or 8–14 without 10) repairs all three hosts. The non-writer slice gives S 0, with the sign reversed.
   - **Position (M10, M11):** c is nonzero only at positions 29 (the round value) and 30. c at 29 reproduces cs1. c at 30, scaled up to 29's norm, repairs 1 cell (AMPLITUDE_ONLY_EXCLUDED). Larger c₃₀ works against the repair.
10. **The shift must reach the context positions of the appended item (M10–M13).**
    - The shift at 29–30 alone flips nothing at any size up to 4×, while the specificity direction stays right.
    - Dropping the shift at the KIND, RECV or RKEY lines costs nothing (M12).
    - Dropping it at AUTH loses 4bcbaf15 (0/13). Dropping it at BLOCK loses 4bcbaf15 (1/13) and half of 264c458d (6/13).
    - Author plus block lines with c at 29 is sufficient at half the change norm of cs1 (M13 sh_fAB_c29: S 39). Other locations of similar size repair only 1fb5651c (AB_LOCATION_SPECIFIC).

### Tier C: host-specific, conditional or downgraded (M12–M16)
11. **The in-subspace tilt r of c opposes the specific repair on 264c458d.**
    - M12: cpar repairs 1 cell; its cosine-matched nulls repair 5–10.
    - M14–M15: on 264c458d at s 7/16, S falls monotonically in λ (12 → 2), outside all 24 random 3× tilts in both directions. The margin is 1 cell on the harm side (tied in 5/14 splits).
    - It works through the round source's action margin A: round cells with A > 0 go from 1 to 11.
    - **By C:** beyond the nulls on 1fb5651c and 264c458d in both directions; on 4bcbaf15 only in the removal direction (adding 3r is AT, rank 2 of 24).
    - **By S on 4bcbaf15:** the tilt goes the other way at 5/16 (TILT_SUPPORTS).
12. **M14's lower threshold under the AB shift is a readout-threshold effect on 264c458d (M15, M16).**
    - M15: the gain comes from where the shift sits, not from c₃₀ (Q1_GAIN_LOC_ONLY, only 7/14).
    - M16: the weight w of the shift at 13–28 moves M and A linearly on 264c458d (AGREE 0.994). Lowering w raises S while lowering C (S_C_DISSOCIATE), so S there ranks arms opposite to the contrast they carry.
    - On 1fb5651c and 4bcbaf15, linearity fails, mostly by curvature outside the M14–M15 interval. The location reading stays CONDITIONAL there.
13. **Position 30 is a weak opponent, not a gate (M12, M13).** At s ¼ the lead is 2 cells. Under the AB shift at s 1, c₃₀ costs 4bcbaf15 6 cells; zeroing it restores them.

### Host heterogeneity (unchanged since M5)
| host | full (own donor) | meanD_host (pooled) | tp16 (cell common part + own contrast) | reading |
|---|---|---|---|---|
| 1fb5651c | 13 | 13 | 13 | flips under almost any context-sized push, including the pooled host null and random tilts; weak evidence about direction |
| 264c458d | 10 | 13 | 10 | informative host for every Tier C verdict |
| 4bcbaf15 | 11 | 13 | 9 | informative; often at ceiling for s ≥ ⅜ |
| 75642418 | 7 | 0 | 6 | needs the cell's own common part |
| 8ae85754 | 4 | 0 | 6 | needs the cell's own common part |
| 2c9118bb | 5 | 0 | 0 | repaired only by the full own-donor patch |
| 1c7158b6 | 1 | 0 | 0 | essentially never repaired |
| 2a4f596d | 0 | 0 | 0 | never repaired by any arm in M1–M16 |

## 4. Preregistered criteria that failed or sit on an edge
These go into LIMITATIONS as stated. None is excluded from the summary.

| stage | criterion | outcome |
|---|---|---|
| M2 | formation layer L_f = 11 | 2/14 splits move it to 8 (NEITHER_ALONE there) |
| M3 | sparse writer | only head 10 is in H\* by rule; heads 8 / 9 / 14 miss by 0.5–1.5 cells and join in 8/14 splits |
| M4 | size vs content of the bulk read | NEC tracks size; resolved by M5 matched size |
| M6 | low-rank ≤ 64 | NOT_LOWRANK (raw basis); M7 shows that is partly size, mostly basis |
| M7 | Δ-basis low-rank, mean-difference, contrast-alone | all fail; MEANDIFF was nearly forced by design |
| M8 / M11 / M12 | s = ½ sufficiency | SPEC at frac exactly 0.75; 2/14 splits move the threshold to 1 |
| M9 / M10 / M11 | split null (1, 5 and 10 random frames) | **fails** each time (median S 7, max 11, mostly 1fb5651c) → subspace verdict stays _UNRESOLVED |
| M9 | gain shape | GAIN_MIXED, neither product nor fixed threshold |
| M13 | tilt at an off-ceiling size | the preregistered size was at floor or ceiling on every host |
| M14 | AB threshold | MIXED (1fb5651c higher); tilt opposes by S on 264c458d and supports on 4bcbaf15 |
| M15 | Q1 split | GAIN_LOC_ONLY in 7/14 splits only |
| M16 | linearity of the middle shift | **W_LINEAR_FAILS** (1fb5651c dS 4, 4bcbaf15 AGREE 0.897) |

## 5. What the route means for safety ([standard](../../research_governance/JEV_SCIENTIFIC_NOVELTY_SECURITY_VALUE_AND_DECISION_STANDARD_20261030_V1.md) §2–§3)
- **The security-relevant fact predates the M-line.** It is the S2 native error: kev-4B misses 63.7% of lawfully appended equivocation votes (SecJev 88.7%) at 0% false alarms on duplicate votes. The M-line explains where a repair can be injected, not why the natural forward pass fails.
- **Candidate account of the miss (not identified):**
  - What the failing host lacks at the appended span is the L11 writer heads' context-wide read. That read has a large common component plus a small round-specific contrast that only acts on top of it.
  - The host's routing to the partner is not the deficit (M3), and neither are the partner's values (M4).
  - This fits H-READ / composition at L11 better than "the partner relation is never encoded upstream". But M2's weaker L ≤ 7 round signal and the lack of any necessity test in the unpatched host leave H-ENC open.
- **§3.6 applies directly, and the route measured it:**
  - Most of every pooled repair is a non-specific threshold push. The common shift alone flips the non-conflict control as often as the conflict (cs0 28 / 28).
  - The specific part is c: about 0.04 of the full change, read only through the shift.
  - On 264c458d, the arm that repairs most carries the least contrast (M16).
  - Repair counts on this task therefore overstate how much conflict-specific signal an intervention adds. They must always be read next to the source-matched round control and the continuous contrast C.
- **False veto is unmeasured.** Every target is a conflicting host. The round control shows that a non-conflict *source* gives no repair. It does not show that the patch leaves *benign hosts* alone. The common shift moves both sources toward conflict, so a false-veto risk on benign hosts is plausible and untested.
- **No defence claim.** The repair reaches 3 of 8 hosts with pooled vectors and 7 of 8 with the full own-donor patch. A deterministic rule engine solves this task exactly. Any value is diagnostic (where in the network the conflict evaluation is formed and read), not protective.

## 6. Prior art and novelty delta
- **Activation patching:** Zhang & Nanda (ICLR 2024) warn that localization depends on the metric and on the corruption. M16 is a preregistered instance on a native safety action.
- **Steering and common shifts:** this literature shows that large additive shifts can flip behaviour. M8–M11 confirm this for the common shift (cs0) and keep it apart from the specific part.
- **Novelty delta that survives:**
  1. **M1:** a same-token-form, round-only change reverses the causal effect of the appended span's L11 state. This is a relation-validity effect, not surface form, and it holds over all 8 hosts and 14 groups.
  2. **M2–M5:** the evaluation is written by L11 attention heads 8–14 from the bulk context, by direction, and transfers across scenes.
  3. **M8–M13:** on the hosts where pooled vectors work at all (3 of 8), the repair decomposes into a non-specific threshold shift that must reach the author and block lines of the appended item, plus a low-rank pooled round contrast that acts at the round-value token through the writer heads.
- **Weakened deltas:** (3) is host-limited, and its subspace and tilt parts are unresolved or host-specific. M14's location result is downgraded on 264c458d.
- **Novelty status:** P1_CONDITIONAL / NOVELTY_NOT_YET_PASS, as in the parallel literature track (A582, A599). Nothing here raises it.
  - The A599 requirements remain open: natural-path mediation into the native action, both false accept and false veto, cluster-aware inference, held-out material, and a second model.

## 7. Open decisive questions
1. **False veto (S2 safety side):** do the M-line patches (`full`, `meanD_host`, `cs*`, the AB arms) make benign or insufficient-evidence hosts move to `reject_conflict`? Answering this needs a runner change to allow non-conflict targets, and a Gold for `accept` and `wait`.
2. **Natural-path necessity (needed for S3):** does ablating or mean-replacing the writer heads' bulk read at the appended span in the *unpatched* donor remove its correct recognition? No M-stage tested necessity outside a patch.
3. **Non-responsive hosts:** why 5 of 8 hosts never take a pooled repair, and why 2a4f596d takes none at all.
4. **Generality:** the whole route is one model (kev-4B LoRA), one simulator family, 14 donors and 8 hosts. M1 is the cheapest to repeat on SecJev-0.8B, or on held-out source groups.

## 8. Decision and what is left before the paper-level audit
**Decision for the mechanism route:**
- **KEEP:** Tier A (M1–M5), as interventional sufficiency at S1–S2.
- **CONDITIONAL:** Tier B, scoped to 3 of 8 hosts.
- **DOWNGRADE:** Tier C.
  - M14's AB threshold on 264c458d becomes a readout-threshold effect.
  - The subspace split stays UNRESOLVED.
  - The tilt is host-specific.
- **STOP:** deepening the pooled-vector line (positions, tilt, subspace). Its remaining questions concern 1–2 near-ceiling hosts and would not change the evidence level. This is standard §5's "no change to the paper claim" stop condition.

**Still missing before the paper claims the mechanism section, ordered by information value:**
1. **False-veto control on benign hosts.** It is the one experiment that could change the safety reading. It needs the user's scope decision and a runner change.
2. **Paper package update (v9 → v10):**
   - a mechanism section built from §3;
   - CLAIMS_EVIDENCE_MAP entries M1–M16 with JSON keys;
   - LIMITATIONS rows from §4;
   - a NOVELTY section from §6.
   This is CPU and text only.
3. **Raw-recompute script:** one CPU script that re-derives every verdict and number cited from the archived raw logits of M1–M16, plus a REANALYSIS_CHECK entry. CPU only.
4. **Capture archiving:** release the M1–M16 captures (as was done for G2) or state that they stay server-side, with their hashes. Publishing a release is outward-facing and needs the user's go-ahead.
5. **Leftover V3 audit items (P1/P2):** check whether any is affected by M1–M16, for example C4 "locus (candidate)" can now cite M1–M5.
6. **Optional, highest cost:**
   - natural-path necessity (§7.2);
   - an M1 replication on SecJev-0.8B or held-out groups (§7.4).

The paper-level audit is triggered only on the user's go-ahead, after the items the user chooses from this list are done.
