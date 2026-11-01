#!/usr/bin/env python3
"""Derive generate_v10.js from generate_v9.js (package V3): add the mechanism route M1-M22 (sections 4.12-4.16,
Table M1), revise the candidate explanation from "missing encoding" to "present but not used" (M18, M21, M22), and
extend the abstract, contributions, discussion, limitations and reproducibility sections.

Every G2 number still comes from numbers_v8.json; every mechanism number comes from numbers_mech_v1.json
(extract_numbers_mech_v1.py). Nothing numeric is typed here. Every replaced span must occur exactly once.
Run inside PAPER_CLAIM_PACKAGE_V4/:  python v10_edits.py ../PAPER_CLAIM_PACKAGE_V3/generate_v9.js generate_v10.js"""
import io, sys

s = io.open(sys.argv[1], encoding="utf8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:100])
    s = s.replace(old, new)


rep("""/* Generate manuscript v9 (""",
    """/* Generate manuscript v10 (v9 + the mechanism route M1-M22 on kev-4B with a SecJev-0.8B replication of the monitor stage;
   candidate explanation revised from a missing encoding to a present-but-unused conflict). Mechanism numbers come from
   numbers_mech_v1.json (extract_numbers_mech_v1.py). v9 was (""")
rep('''const N = require("./numbers_v8.json");''',
    '''const N = require("./numbers_v8.json");
const M = require("./numbers_mech_v1.json");
const f3 = x => x.toFixed(3);
const pc = x => (100 * x).toFixed(1);
const M18s = M.M18.det["PROBE:SPAN_ATTN11"], M18L = M.M18.det["PROBE:LAST_RESID_L31"], M18e = M.M18.det["PROBE:SPAN_RESID_emb"];
const M22s = M.M22.det["PROBE:SPAN_ATTN11"], M22r = M.M22.det["PROBE:SPAN_RESID_L11"], M22L = M.M22.det["PROBE:LAST_RESID_L23"], M22e = M.M22.det["PROBE:SPAN_RESID_emb"];
const M17FV = M.M17.FV, M21m = M.M21.measures;''')
rep('''text: "Anonymous draft (v9; v8 revised after a second independent paper-level audit: claims about recognition narrowed, related-work comparison added)"''',
    '''text: "Anonymous draft (v10; v9 extended with a preregistered mechanism route on kev-4B and a second-model replication of its monitor stage)"''')

# ---- abstract: candidate explanation revised, mechanism sentence added ----
rep('''to produce the rule-mandated readout and decision; a missing conflict encoding at the appended span is the explanation most consistent with the evidence but is not uniquely identified, and the scorers, scenes and edits come from one constructed simulator family.`),''',
    '''to produce the rule-mandated readout and decision. A further ${Object.keys(M.forwards).length} preregistered stages (${M.forwards_total.toLocaleString("en-US")} forwards) trace the kev-4B mechanism: the span state at layer 11 carries a round-keyed conflict verdict (changing only the vote's round turns ${M.M1.J_main}/${M.M1.cells} joint repairs into ${M.M1.J_round}), written by full-attention heads 8-14 from the bulk of the context; replacing that read with the round-changed one removes recognition in ${Math.round(M.M20.round_self.C_loss * M.M20.round_self.n)}/${M.M20.round_self.n} recognizing donors, though a failing host's read removes it in only about a fifth of cells. In the missed scenes the conflict is nonetheless linearly decodable from the appended span (held-out AUROC ${f3(M18s.AUROC)}; SecJev ${f3(M22s.AUROC)}) and from the state that feeds the decision head, yet steering that state along the conflict direction moves no decision. The failure is therefore best described as a conflict that is represented but not used, not as a missing encoding; this revises our earlier candidate account. The scorers, scenes and edits come from one constructed simulator family.`),''')

# ---- introduction: contributions ----
rep('''Third, layer profiles, suppression controls and a capture-based projection test constrain where the failure can lie; they favor, but do not uniquely identify, a failure to encode the appended conflict at its span.''',
    '''Third, layer profiles, suppression controls and a capture-based projection test constrain where the failure can lie; on their own they favored a failure to encode the appended conflict at its span, a reading that the mechanism route below revises.''')
rep('''with the analysis window chosen on scenes disjoint from the replication (the source groups overlap).`),''',
    '''with the analysis window chosen on scenes disjoint from the replication (the source groups overlap). Sixth, a preregistered mechanism route on kev-4B (${Object.keys(M.forwards).length} stages, Sections 4.12-4.16) identifies what the transplant supplies - a round-keyed verdict written by layer-11 attention heads, sufficient in hosts and necessary in most recognizing donors - measures the false veto of every repair, and shows with a second scorer that the conflict is present but unused at the decision in the scenes the models miss.`),''')

# ---- new sections 4.12-4.16 after Table 6's note ----
anchor = '''  h("5  Discussion", HeadingLevel.HEADING_1),'''
NEW = r'''  h("4.12  Mechanism route: design and evidence tiers", HeadingLevel.HEADING_2),
  p(`After the paper-level claim above, we ran a preregistered mechanism route on kev-4B: ${Object.keys(M.forwards).length - 1} kev-4B stages and one SecJev-0.8B stage (${M.forwards_k4b.toLocaleString("en-US")} and ${M.forwards.M22} native forwards; about ${M.gpu_hours} GPU hours). Every stage froze its design, manifest and analysis script on CPU, passed a fake-model self-test and a pre-model gate, ran in a single ledger attempt with no denied calls, and replayed earlier stages' anchor rows bitwise. Unless stated otherwise the unit is the K-C cross-group cell (14 donors x 8 hosts, ${M.M1.cells} cells), every verdict is reported with its leave-one-donor-group-out stability, and the round control is the donor's own scene with only the appended vote's round changed to a non-candidate round, which turns the vote into a non-conflict at the same token form. The specific repair count S counts cells repaired jointly by the main donor and not by its round control. Table M1 lists every stage and its preregistered verdict. Results that hold across hosts and donor groups (M1-M5) form Tier A; results from pooled-donor arms that repair only 3 of 8 hosts (M6-M11) form Tier B; host-specific or downgraded results (M12-M16) form Tier C and are not used for the claims below.`),
  caption(`Table M1. Mechanism stages (kev-4B unless marked) and their preregistered verdicts. All counts are over cells that share hosts; per-host counts are the honest unit for M6-M17.`),
  table(
    ["Stage", "Question", "Preregistered verdict(s)", "Forwards"],
    [
      ["M1", "Is the span state a relation (round) verdict or a class token?", `${M.M1.verdict_round}; ${M.M1.verdict_role}`, `${M.forwards.M1}`],
      ["M2", "Which sublayer writes it?", `${M.M2.verdict} at L${M.M2.L_f}`, `${M.forwards.M2}`],
      ["M3", "Which heads?", `${M.M3.verdict} (heads 8-14 cooperate; head 10 most necessary)`, `${M.forwards.M3}`],
      ["M4", "What do the heads read?", `${M.M4.verdict}; ${M.M4.value_swap}`, `${M.forwards.M4}`],
      ["M5", "Size or direction of the read?", `${M.M5.verdict}; ${M.M5.content}`, `${M.forwards.M5}`],
      ["M6-M11", "Pooled decomposition (3/8 hosts)", "shared donor component; common shift + small round contrast, non-additive; contrast via writer heads at the round token; subspace UNRESOLVED", `${["M6", "M7", "M8", "M9", "M10", "M11"].reduce((a, k) => a + M.forwards[k], 0)}`],
      ["M12-M16", "Positions, fields, tilt, linearity", `host-specific; ${M.verdicts.M16.w_linear}`, `${["M12", "M13", "M14", "M15", "M16"].reduce((a, k) => a + M.forwards[k], 0)}`],
      ["M17", "False veto of the repairs on benign hosts", `full ${M.M17.arm_verdicts.full}; meanD ${M.M17.arm_verdicts.meanD}; cs0 ${M.M17.arm_verdicts.cs0}; abc05 ${M.M17.arm_verdicts.abc05}`, `${M.forwards.M17}`],
      ["M18", "Is the conflict decodable in missed scenes?", `${M.M18.verdicts.V1_encoded}, ${M.M18.verdicts.V1_surface}; ${M.M18.verdicts.V2_location}; ${M.M18.verdicts.V3_useful}`, `${M.forwards.M18}`],
      ["M19", "Does gain along the probe direction drive the readout?", `L19 ${M.M19.verdicts.L19}; L31 ${M.M19.verdicts.L31}`, `${M.forwards.M19}`],
      ["M20", "Is the L11 read necessary in recognizing donors?", `${M.M20.verdicts.full}; ${M.M20.verdicts.bulk}`, `${M.forwards.M20}`],
      ["M21", "Does a high-energy conflict direction drive the readout?", `L19 ${M.M21.verdicts.L19}; L31 ${M.M21.verdicts.L31}`, `${M.forwards.M21}`],
      ["M22 (SecJev)", "Does M18 replicate on the second scorer?", `${M.M22.verdicts.V1_encoded}, ${M.M22.verdicts.V1_surface}; ${M.M22.verdicts.V2_location}; ${M.M22.verdicts.V3_useful}`, `${M.forwards.M22}`],
    ],
    [12, 36, 40, 12]
  ),

  h("4.13  What the transplant supplies: a round-keyed verdict written at layer 11 (Tier A)", HeadingLevel.HEADING_2),
  p(`Relation, not token class (M1). Changing only the round of the donor's appended vote - same author, same position, same token form - turns the transplant from repair into suppression: joint repairs fall from ${M.M1.J_main} to ${M.M1.J_round} of ${M.M1.cells} cells, the main arm beats the round arm in ${pc(M.M1.frac_main_gt_round)}% of cells with a majority in ${M.M1.groups_majority}/14 donor groups, and the round arm pushes hosts toward "no conflict" (median dM ${s(M.M1.median_dM_round)} against ${s(M.M1.median_dM_main)}). Changing the author instead keeps the repair (${M.M1.J_okalt} joint). The span state therefore carries a signed evaluation of whether the appended vote conflicts, which answers the class-prototype confound of the earlier audit for this locus.`),
  p(`Writer (M2-M3). The donor's layer-${M.M2.L_f} full-attention output alone reproduces the repair (S ${M.M2.S_mixer_L11}; the whole residual gives ${M.M2.S_resid_L11}); no span MLP patch at layers 8-11 exceeds S ${M.M2.S_mlp_max}. A weaker round-specific signal is already present in the layer 7-10 residual (S ${M.M2.S_resid_L7_L10.join(", ")}), and two of fourteen splits move the formation layer to 8, so layer 11 is the main but not the only writer. No single head suffices (best S ${M.M3.S_best_single_head} against ${M.M3.S_all} for all heads); dropping head 10 cuts S to ${M.M3.S_drop10} and dropping heads 8, 9 or 14 to ${M.M3.S_drop8_9_14.join(", ")}: heads 8-14 cooperate, with head 10 the most necessary.`),
  p(`What the heads read (M4-M5). Splitting the write by key class, removing the reads of the other vote items or of the context costs most of the repair (S ${M.M4.S_drop_OTHER_ITEMS} and ${M.M4.S_drop_CONTEXT} of ${M.M4.S_full}), while removing the read of the conflict partner keeps ${M.M4.S_drop_PARTNER}, and giving the host the donor's partner values repairs ${M.M4.S_vswap_PARTNER}. The bulk read acts by direction, not size: the donor-minus-host bulk direction at the host's own size repairs ${M.M5.S_dir_BULK} of ${M.M5.S_full}, a random direction of the same size ${M.M5.S_dir_RAND}, and a third, unrelated donor's bulk part ${M.M5.S_xdonor_BULK}. The verdict is thus composed from the whole context rather than copied from the partner vote, and its useful part transfers across scenes.`),
  p(`Pooled arms (Tier B, M6-M11) decompose the repair on the three hosts where pooled vectors work at all into a large common shift, which flips the round control as often as the conflict, and a small round contrast that is read only on top of that shift, through the writer heads and at the round-value token. Most of any pooled repair is therefore a non-specific threshold push; repair counts on this task overstate conflict-specific signal unless they are read against the round control. The later position, tilt and linearity stages (Tier C, M12-M16) are host-specific; M16's preregistered linearity criterion failed (${M.verdicts.M16.w_linear}), and we do not use them.`),

  h("4.14  Safety side: false veto of the repairs and natural-path necessity", HeadingLevel.HEADING_2),
  p(`False veto (M17). The same patches were applied to each host's benign variants - the duplicate vote (SA), the wrong-round vote (ROUND) and an outsider's vote (OUTSIDER), ${M.M17.cells_per_arm} cells each. The own-donor patch ("full", ${M.M17.R.full} repairs on the conflict) makes ${M17FV["full@SA"]} SA and ${M17FV["full@ROUND"]} ROUND cells reject as well, and is NONSELECTIVE by the preregistered rule; the pooled donor mean rejects ${M17FV["meanD@ROUND"]} wrong-round votes. The two contrast-carrying pooled arms (cs0 and abc05, ${M.M17.R.cs0} repairs each) leave SA and ROUND untouched but reject ${M17FV["cs0@OUTSIDER"]} and ${M17FV["abc05@OUTSIDER"]} outsider votes, all on one host. The transplanted state is therefore a carried verdict that downstream rows apply without re-checking the round; implanted into a benign scene it can veto it. Under v1 of the frozen M17 analysis the gate failed on a lookup bug; v1.1 changes only that lookup and is reported as a deviation.`),
  p(`Necessity (M20). In the 14 recognizing donors, we replaced the bulk part of their own layer-11 write with the one computed from their own round-changed scene, whose context is token-identical except for the round. The conflict margin falls in every donor (median dM ${s(M.M20.round_self.median_dM)}) and recognition is lost in ${Math.round(M.M20.round_self.C_loss * M.M20.round_self.n)} of ${M.M20.round_self.n}. A failing host's write is only partly disruptive: it removes recognition in ${pc(M.M20.full.host_C_loss)}% (full) and ${pc(M.M20.bulk.host_C_loss)}% (bulk) of cells, against ${pc(M.M20.full.ctrl_C_loss)}% and ${pc(M.M20.bulk.ctrl_C_loss)}% for donor-to-donor controls (${M.M20.verdicts.full}, ${M.M20.verdicts.bulk}; both stable in ${M.M20.logo.full}/14 splits). The round-keyed layer-11 read is thus sufficient in hosts and necessary in most recognizers, but recognition is partly redundant: the donors with the largest margins survive every swap.`),

  h("4.15  In the missed scenes the conflict is present but not used", HeadingLevel.HEADING_2),
  p(`Decodability (M18). Across the 124 Stage-A scenes x five arms, a linear probe trained on other source groups separates kev-4B's ${M.M18.counts.missed} missed equivocations from ${M.M18.counts.benign} benign scenes with AUROC ${f3(M18s.AUROC)} [${M.M18.ci_AUROC_span.join(", ")}] from the layer-11 span write, against ${f3(M18e.AUROC)} for the span's token embeddings, and with AUROC ${f3(M18L.AUROC)} from the layer-31 state that feeds the decision head. Unsupervised whitening monitors are blind (AUROC ${f3(M.M18.det["WHITEN:LAST_RESID_L31"].AUROC)}), and the model's own margins are weak (${f3(M.M18.det.NATIVE_A.AUROC)} / ${f3(M.M18.det.NATIVE_M.AUROC)}). The appended conflict is therefore represented in the scenes the model misses; the miss is not a failure to form it.`),
  p(`Readout (M19, M21). Amplifying each row's own deviation along the held-out probe direction at the decision token (M19, gain up to 32x) and, because that direction carries under one percent of the residual norm, pushing along the high-energy class-mean difference by up to 20% of the residual norm (M21) both leave the decision unchanged: repair is ${M21m.push_L31_b20.REPAIR} of ${M.M21.counts.MISSED} missed rows at the strongest push, and only the 32x gain at layer 31 moves any decision (${Math.round(M21m.gain_L31_g32.REPAIR * M.M21.counts.MISSED)} repair against a ${pc(M21m.gain_L31_g32.FV)}% false veto). The conflict direction is near orthogonal to the head's reject-minus-accept gradient (median cosine ${M.M21.cos_median.MISSED} in missed rows). The preregistered verdicts are ${M.M19.verdicts.L31} (M19) and ${M.M21.verdicts.L31} (M21) at both layers tested, 19 and 31. The intervention reaches only the decision token; the head also reads the option tokens, which this test cannot reach.`),
  p(`Revised candidate account. Sections 4.7-4.8 favored a failure to encode the appended conflict at its span, because a missed span substitutes like a duplicate vote and projects weakly onto the donor-derived conflict direction. M18 and M22 show that the information is nonetheless linearly recoverable from the missed span and from the decision state. The two observations are compatible: what the missed span lacks is the conflict in the form that downstream rows read - the round-keyed verdict that the layer-11 heads write in recognizing scenes (Section 4.13) - not the information itself. We therefore replace "missing encoding" with "represented but not used": the conflict is present but neither written into the read form at the span nor read at the decision. Decodability by a supervised probe does not show that the model uses a feature, and the causal half of this account (M19-M21) is kev-4B only.`),

  h("4.16  A second scorer: the monitor stage replicates on SecJev-0.8B", HeadingLevel.HEADING_2),
  p(`M22 reran the frozen M18 design on SecJev-0.8B, with the 372 old / new / SA forwards bitwise equal to SecJev's own Stage-A rows. All four preregistered verdicts replicate: ${M.M22.verdicts.V1_encoded} (AUROC ${f3(M22s.AUROC)} [${M.M22.ci_AUROC_span.join(", ")}]) and ${M.M22.verdicts.V1_surface} (embeddings ${f3(M22e.AUROC)}), ${M.M22.verdicts.V2_location}, and ${M.M22.verdicts.V3_useful}. SecJev misses ${M.M22.counts.missed} of 124 equivocations with a different failure profile (accept or wait), yet its decision state still decodes the conflict (AUROC ${f3(M22L.AUROC)}) while its own margins are at chance (${f3(M.M22.det.NATIVE_A.AUROC)} / ${f3(M.M22.det.NATIVE_M.AUROC)}). The best detector is the layer-11 span residual: ${pc(M22r.TPR1)}% of missed equivocations at ${pc(M22r.FPR1)}% held-out false veto (kev-4B's layer-31 decision-state probe: ${pc(M18L.TPR1)}% at ${pc(M18L.FPR1)}%). Unlike kev-4B, which rejects ${M.M18.counts.natural_false_veto_by_arm.ROUND || 0} wrong-round and ${M.M18.counts.natural_false_veto_by_arm.OUTSIDER || 0} outsider votes but no legal or duplicate ones, SecJev natively rejects ${M.M22.counts.natural_false_veto_by_arm.old} legal, ${M.M22.counts.natural_false_veto_by_arm.SA} duplicate, ${M.M22.counts.natural_false_veto_by_arm.ROUND} wrong-round and ${M.M22.counts.natural_false_veto_by_arm.OUTSIDER} outsider votes of 124 each. The present-but-unused statement thus holds on both scorers at the level of decodability; the interventions of M1-M21 were run on kev-4B only. Because generic last-token probes match the mechanism-located monitor on both scorers, we report the monitor as a safety demonstration, not as a contribution.`),

'''
rep(anchor, NEW + anchor)

# ---- discussion: the encoding paragraph ----
rep('''On the locus, the evidence favors an encoding account''',
    '''On the locus, the G2 evidence alone favored an encoding account''')
rep('''We therefore present encoding failure as the leading candidate explanation, not an identified mechanism.''',
    '''We presented encoding failure as the leading candidate explanation in v9; the mechanism route (Sections 4.13-4.16) revises it to a conflict that is represented but not written into the form downstream rows read, and not read at the decision.''')

# ---- limitations ----
rep('''kev-4B margins are small, so its flips are less informative than its contrasts.`),''',
    '''kev-4B margins are small, so its flips are less informative than its contrasts.`),
  p(`Mechanism route. The interventions (M1-M21) are kev-4B only; SecJev replicates only the decodability and monitor stage (M22), on the same 124 scenes, so no independent scene distribution is tested. Tier A rests on 14 donors and 8 hosts; pooled arms repair 3 of 8 hosts, two hosts are essentially never repaired, and the Tier C stages are host-specific. Preregistered criteria that failed or sat on an edge are kept in the record: the formation layer moves to 8 in 2/14 splits (M2), only head 10 meets the sparse-writer rule (M3), the low-rank and mean-difference criteria fail (M6-M7), the random-frame split null fails three times so the subspace verdict stays unresolved (M9-M11), the preregistered tilt sizes sit at floor or ceiling (M13), the location gain holds in 7/14 splits (M15), and linearity fails (M16). M17's frozen analysis had a lookup bug fixed in v1.1 as a documented deviation. Necessity is partial (M20), and the readout tests reach only the decision token at two layers (M19, M21). A supervised probe needs rule-labelled data, and a deterministic rule engine solves this task exactly, so the monitor is a diagnostic, not a defence.`),''')

# ---- reproducibility ----
rep('''the claim-to-evidence map and reproduction commands are in PAPER_CLAIM_PACKAGE_V3.`),''',
    '''the claim-to-evidence map and reproduction commands are in PAPER_CLAIM_PACKAGE_V3.`),
  p(`v10 additions: the mechanism stages live in research/rounds/A461_MECH_M1 ... M21 and A461_MON_M18 / M22, each with its preregistration committed before its GPU run, admission, self-test, pre-model gate receipt, per-batch receipts, raw FP32 logits and frozen analysis output (${M.forwards_total.toLocaleString("en-US")} forwards in all, no denied calls). Section 4.12-4.16 numbers are generated by extract_numbers_mech_v1.py from those archived files, and recompute_mech_v1.py re-runs all 22 frozen analyses on the archived raw rows and captures and compares each output with the committed JSON (PAPER_CLAIM_PACKAGE_V4).`),''')

rep('"Missed When Added, Repaired When Implanted (v9)"', '"Missed When Added, Repaired When Implanted (v10)"')
rep('fs.writeFileSync("A461_G2_paper_draft_v9.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v10.docx", buf)')
io.open(sys.argv[2], "w", encoding="utf8", newline="\n").write(s)
print("ok", len(s))
