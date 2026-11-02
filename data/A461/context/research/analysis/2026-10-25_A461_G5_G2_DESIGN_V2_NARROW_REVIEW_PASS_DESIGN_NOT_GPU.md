# A461-G5-G2 DESIGN_V2 — independent narrow delta review

**Date:** 2026-10-25. **Verdict:** `PASS_V2_DESIGN_DELTA / NOT_ADMITTED_GPU`. This resolves the previous design review's four P0 *at the written-design level only*. It does **not** authorize an experiment, certify frozen full-token pairs, certify real donor recognition, or validate a GPU runner.

## Anchored source and prior review

- Request: Issue #2 [comment 6400272206](https://github.com/dddd2024/jev/issues/2#issuecomment-6400272206); submission commit **`ef5ed996a2aefb58f6f7a5765d9ee5a69732b045`**.
- New frozen design: `research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/A461_G5_G2_DESIGN_V2.json`, Git blob **`095838f18fdd98a5b282a12615d44c99dc2d31af`**.
- Superseded draft: `G2_CPU_FEASIBILITY_REAL/g2_design_draft.json` blob `94fdfd295ed28ed9b20e503570ea2083f204cfcb`.
- Prior independent review: `research/analysis/2026-10-25_A461_G5_G2_CPU_FEASIBILITY_AND_DESIGN_INDEPENDENT_REVIEW_V1_HOLD_GPU.md`, commit `458c698015044d51de138b00cbff986cb9839f93`.
- Archived CPU inventory unchanged: **797** DEV source scenes, **713** unused scene SHAs, **189** oracle-constructible candidate pairs, only **180** same-standalone-block-width candidates in **28** groups; all **42/42** DEV run groups historically touched.

## All four earlier P0 design changes verified

1. **Cohort denominator and probabilities:** V2 uses **2/56 descriptive** across G3's 20 appended-conflict T2 + G5-V2's 36 T2 and explicitly excludes G3's 6 T3 existing-conflict contrasts. It correctly distinguishes this descriptive recognition frequency from a strict donor qualification rate. Independent arithmetic of its IID binomial *illustration* at `p=2/56`:
   ```
   n      E[K]       P(K>=2)
   56     2.000      0.598916
   62     2.214      0.654234
   93     3.321      0.849009
   124    4.429      0.938465
   180    6.429      0.988994
   ```
   JSON values round correctly to 3 decimals. This is **not** a scientifically justified independent-Bernoulli power estimate; source-group clustering and arm eligibility can lower actual discovery probability. The design now states no guaranteed donor and conditions further work on qualifying positives. **P0-1 CLOSED at design stage.**
2. **Width and full-request alignment:** V2 explicitly separates 189 CPU-legal constructs from **180** preliminary equal-block-width candidates (155 accept/25 wait) and excludes the 9 fallback unequal-width cases from its confirmatory pool. Requires G5-grade **full native encoded old/new/SA token IDs**, identical trailing suffixes, exact appended-span positions/growth and dynamically resolved C question row before admission. Merely matching block-label token widths is not called sufficient. **P0-2 CLOSED in the protocol; real token tests NOT YET EXECUTED.**
3. **Source-group scope:** V2 acknowledges **zero never-used groups** among 42 historical DEV groups; tier-2 means unused scenes in groups not used in the three-row G5 pilot (run83/run114/run182). Checked archived rows: excluding pilot-trio groups gives **172** same-block-width candidates across **26** prior-study run groups, while 8 in pilot-trio groups are tier-3 exploration. This is weaker than an unseen-group external replication, and the new prose correctly restricts its claims. **P0-3 CLOSED as a claim-scope revision.**
4. **Two separately admitted budgets:** V2 now explicitly distinguishes **Stage-A donor discovery** = `N*3 native forwards + replays`, individually frozen batches <=128, from **Stage-B intervention** = `F(H,L)=4+4H+8HL` based on its enumerated 3 donor captures + donor baseline + 4 host setup forwards + four restoration conditions and four suppression conditions per host/layer. Independent arithmetic:
   ```
   H=2,L=2: 44; H=4,L=2: 84; H=4,L=3: 116; H=6,L=2: 124.
   N=62: 186 screening primary forwards => >=2 batches, before replays.
   N=124: 372 screening primary forwards => >=3 batches, before replays.
   N=180: 540 screening primary forwards => >=5 batches, before replays.
   ```
   The formula is **a transparent planning enumeration, not a traced GPU physical ledger**. Additional layer-specific identities, runtime retries, replay or multiple-donor captures would require explicit accounting. **P0-4 CLOSED as protocol arithmetic correction; implementation admission still HOLD.**

## Remaining execution-admission conditions (not new design P0s)

**G2 Stage-A donor search is NOT_ADMITTED:**
- Freeze *which* 172 tier-2 candidates and scene/source-group strata belong to discovery vs held-out confirmation before any inference; decide whether pilot-group tier3 cases are excluded, and report exact per-batch count and full-request tokenizer gates.
- A three-arm old/new/SA screening plan of N pairs needs actual ordered input hashes, tokenizer/Gold parity, physical forward plan, bounded retries/replications and exact replay count, **with batch-specific new GPU approval**. The paper's 2/56 descriptive rate does not assure a qualified donor, and screening itself is not an independent confirmatory test.
- Specify clear outcomes if Stage-A finds **0 or 1** new strictly qualified donors. The V2 Stage-B gate demands **>=2** but the stop list explicitly names only 0; 1 should be an explicit `HOLD_INSUFFICIENT_DONORS` result, not silently proceed.

**G2 Stage-B patching is NOT_ADMITTED:**
- Trigger only after new donor qualification, actual source scene disjointness, full native token+suffix gates, and a new preregistered suppression/restoration control comparison.
- The Stage-B formula assumes **one donor context per stated setup**, whereas V2 requests at least **two new donors**. Explicitly define one run per donor or a multiple-donor complete call graph including captures/baselines for each donor. Do not quietly call `F(H,L)` a whole-study budget.
- Freeze the complete 1:1 `model.forward` graph, site/layer/condition and seeds, identity/baseline checks and fail-closed archive contract; independent reviewer PASS must bind code blob, source SHA and per-run budget. Only after this plus fresh **user explicit GPU authorization** can real GPU execute. V2 itself says NOT_AUTHORIZED.

**Scientific upper bound:** source reuse ledger proves fresh scenes inside historical groups, not line-wide unseen groups; no independent Key/Q component mediation is shown by whole-backbone activation patches.

## Conclusion

**`PASS_V2_DESIGN_DELTA`**: the earlier four P0 **protocol** blockers are fixed to an auditable planning state. **`NOT_ADMITTED_GPU`**: no Stage-A or Stage-B run is allowed on this review alone; the next deliverable is a small CPU-only Stage-A exact frozen roster + preflight + budget ledger for narrow independent code/source admission. Preserve V1 and V2 verbatim. No need to rerun G5 or revise v5.2 because of this design review.
