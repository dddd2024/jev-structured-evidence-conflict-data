#!/usr/bin/env python3
"""Derive generate_v11.js from generate_v10.js (package V4), revising v10 per paper audit 02a2b73
(PAPER_AUDIT_REVISE_REQUIRED, P0x2 / P1x6 / P2x2):

P0-1  M18/M22 labels are collinear with the arm: M-E narrowed to "new-missed and benign states are linearly separable,
      above the token surface"; the G2.3 same-span counterfactual is reported as constructible, not run.
P0-2  M19/M21 cover the decision token only, and a random push is equally inert: M-F narrowed to "the tested
      decision-token steering does not produce selective repair"; gamma 32's 20 action changes are stated.
P1-1  L11 claims stated as local conditional sufficiency and partial interventional necessity in these 14 x 8 scenes;
      head and layer heterogeneity and the 5 M20 survivors are named.
P1-2  M22 stated as a same-family, same-scene re-test.
P1-3  Three-action safety table (Table S1) per model and arm, from the raw logits.
P1-4  Novelty stated as a task-specific instantiation of known phenomenon classes.
P1-5  The 22/22 recompute is described as deterministic re-computation, not independent replication; M17 v1.1 marked as
      a post-run analysis correction.
P1-6  M17 covers four repair families, not every repair.
P2-1  M20: 5 survivors.  P2-2  M21: no "moves no decision".
Numbers: numbers_v8.json (G2) and numbers_mech_v2.json (extract_numbers_mech_v2.py). Every replaced span must occur
exactly once.  Run inside PAPER_CLAIM_PACKAGE_V5/:
    python v11_edits.py ../PAPER_CLAIM_PACKAGE_V4/generate_v10.js generate_v11.js"""
import io, sys

s = io.open(sys.argv[1], encoding="utf8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:120])
    s = s.replace(old, new)


rep("/* Generate manuscript v10 (", "/* Generate manuscript v11 (v10 narrowed per paper audit 02a2b73; numbers_mech_v2.json). v10 was (")
rep('const M = require("./numbers_mech_v1.json");', '''const M = require("./numbers_mech_v2.json");
const S3 = M.safety3, M21c = M.M21.action_changes;''')
rep('"Anonymous draft (v10; v9 extended with a preregistered mechanism route on kev-4B and a second-model replication of its monitor stage)"',
    '"Anonymous draft (v11; v10 narrowed after an independent paper-level audit of the mechanism route)"')
rep('"Missed When Added, Repaired When Implanted (v10)"', '"Missed When Added, Repaired When Implanted (v11)"')
rep('fs.writeFileSync("A461_G2_paper_draft_v10.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v11.docx", buf)')

# ---- abstract (P0-1, P0-2, P1-1) ----
rep('''trace the kev-4B mechanism: the span state at layer 11 carries a round-keyed conflict verdict''',
    '''probe the kev-4B mechanism locally: the span state at layer 11 carries a round-sensitive conflict signal''')
rep('''written by full-attention heads 8-14 from the bulk of the context; replacing that read with the round-changed one removes recognition in''',
    '''whose transplant is conditionally sufficient in these hosts and is written mainly by layer-11 attention from the bulk of the context; replacing that read with the round-changed one removes recognition in''')
rep('''In the missed scenes the conflict is nonetheless linearly decodable from the appended span (held-out AUROC ${f3(M18s.AUROC)}; SecJev ${f3(M22s.AUROC)}) and from the state that feeds the decision head, yet steering that state along the conflict direction moves no decision. The failure is therefore best described as a conflict that is represented but not used, not as a missing encoding; this revises our earlier candidate account.''',
    '''Held-out linear probes separate missed appended-conflict states from benign ones above the token surface (AUROC ${f3(M18s.AUROC)}; SecJev ${f3(M22s.AUROC)}), but every positive is an appended-conflict row, so this separability does not by itself show that conflict validity is encoded; a same-span counterfactual that would test it is constructible in all scenes and has not been run. Steering the decision-token state along a conflict direction produced no selective repair. "Represented but not used" is therefore a candidate explanation, which replaces our earlier "missing encoding" candidate; neither is identified.''')

# ---- contributions (P1-6, P0) ----
rep('''identifies what the transplant supplies - a round-keyed verdict written by layer-11 attention heads, sufficient in hosts and necessary in most recognizing donors - measures the false veto of every repair, and shows with a second scorer that the conflict is present but unused at the decision in the scenes the models miss.''',
    '''characterizes what the transplant supplies - a round-sensitive signal written mainly by layer-11 attention, locally and conditionally sufficient in these hosts and partly necessary in 9 of 14 recognizing donors - measures the false veto of four representative repair families, and reports, on two scorers of one family, a probe separability of missed-conflict states that is consistent with, but does not establish, a conflict that is represented but not used.''')

rep('`${M.M3.verdict} (heads 8-14 cooperate; head 10 most necessary)`', '`${M.M3.verdict} (head 10 by rule; heads 8, 9, 14 at threshold)`')

# ---- 4.12 (P1-5) ----
rep('''and replayed earlier stages' anchor rows bitwise.''',
    '''and replayed earlier stages' anchor rows bitwise. A deterministic re-computation of all 22 frozen analyses from the archived inputs reproduces every reported number; it re-runs our own scripts and is not an independent replication.''')

# ---- 4.13 (P1-1) ----
rep('''h("4.13  What the transplant supplies: a round-keyed verdict written at layer 11 (Tier A)", HeadingLevel.HEADING_2),''',
    '''h("4.13  What the transplant supplies: a round-sensitive signal written at layer 11 (Tier A; local, conditional)", HeadingLevel.HEADING_2),''')
rep('''The span state therefore carries a signed evaluation of whether the appended vote conflicts, which answers the class-prototype confound of the earlier audit for this locus.''',
    '''In these 14 donors and 8 hosts the span state therefore carries a signed, round-sensitive signal about whether the appended vote conflicts, which answers the class-prototype confound of the earlier audit for this locus; the validator, block and vote fields are not separated.''')
rep('''No single head suffices (best S ${M.M3.S_best_single_head} against ${M.M3.S_all} for all heads); dropping head 10 cuts S to ${M.M3.S_drop10} and dropping heads 8, 9 or 14 to ${M.M3.S_drop8_9_14.join(", ")}: heads 8-14 cooperate, with head 10 the most necessary.`),''',
    '''No single head suffices (best S ${M.M3.S_best_single_head} against ${M.M3.S_all} for all heads); dropping head 10 cuts S to ${M.M3.S_drop10} and dropping heads 8, 9 or 14 to ${M.M3.S_drop8_9_14.join(", ")}. By the preregistered rule only head 10 is necessary; heads 8, 9 and 14 sit at the threshold and join in 8 of 14 splits, so we do not claim a sparse or unique writer circuit.`),''')

# ---- 4.14 (P1-6, P1-5, P2-1) ----
rep('''False veto (M17). The same patches were applied''',
    '''False veto (M17). Four representative repair families - the own-donor patch and three pooled arms - were applied''')
rep('''The transplanted state is therefore a carried verdict that downstream rows apply without re-checking the round; implanted into a benign scene it can veto it. Under v1 of the frozen M17 analysis the gate failed on a lookup bug; v1.1 changes only that lookup and is reported as a deviation.`),''',
    '''Implanted into a benign scene, the transplanted state can therefore veto it. The other repair variants and doses of M1-M16 were not tested for false veto. M17 is a post-run analysis correction: the frozen v1 analysis failed its consistency gate on a lookup bug, and v1.1, written after the run, changes only that lookup.`),''')
rep('''The round-keyed layer-11 read is thus sufficient in hosts and necessary in most recognizers, but recognition is partly redundant: the donors with the largest margins survive every swap.`),''',
    '''${M.M20.round_self.survivors} of the ${M.M20.round_self.n} donors keep recognition under the round-self swap. In these scenes the round-sensitive layer-11 read is thus locally sufficient in hosts and partly necessary in recognizers; recognition is partly redundant, and other routes are not identified.`),''')

# ---- 4.15 (P0-1, P0-2) ----
rep('''h("4.15  In the missed scenes the conflict is present but not used", HeadingLevel.HEADING_2),''',
    '''h("4.15  Missed-conflict states are linearly separable; tested decision-token steering does not repair", HeadingLevel.HEADING_2),''')
rep('''The appended conflict is therefore represented in the scenes the model misses; the miss is not a failure to form it.`),''',
    '''These numbers show that, in this constructed data, missed appended-conflict states and benign states are linearly separable above the token surface. They do not show that conflict validity is what the probe reads: every positive is an appended-conflict ("new") row and every negative a non-new row, so arm, Gold, message form and role vary together. A CPU check (G2.3) shows that a same-span counterfactual exists in all 124 scenes and 17 source groups: the appended vote is kept byte-identical and only the round of the author's earlier vote changes (one token), which moves Gold away from reject_conflict. Scoring these twins with the frozen probes would separate conflict validity from arm; that GPU stage has not been run.`),''')
rep('''both leave the decision unchanged: repair is ${M21m.push_L31_b20.REPAIR} of ${M.M21.counts.MISSED} missed rows at the strongest push, and only the 32x gain at layer 31 moves any decision (${Math.round(M21m.gain_L31_g32.REPAIR * M.M21.counts.MISSED)} repair against a ${pc(M21m.gain_L31_g32.FV)}% false veto).''',
    '''produce no selective repair: repair is ${M21m.push_L31_b20.REPAIR} of ${M.M21.counts.MISSED} missed rows at the strongest push, and the 32x gain at layer 31 changes ${M.M21.action_changes_total.gain_L31_g32} of 620 actions - ${M21c.gain_L31_g32.repair} repair, ${M21c.gain_L31_g32.new_false_veto} new false vetoes, ${M21c.gain_L31_g32.lost_recognition} lost recognition and ${M21c.gain_L31_g32.other_change} other change. A random push of the same 20% size is about as inert as the conflict push, so the null is not specific to the conflict direction.''')
rep('''The intervention reaches only the decision token; the head also reads the option tokens, which this test cannot reach.`),''',
    '''The intervention reaches only the decision token at two layers; the head also reads the option tokens, which this test cannot reach. The result is therefore that the tested steering fails, not that the decision circuit ignores conflict information.`),''')
rep('''Revised candidate account. Sections 4.7-4.8 favored a failure to encode the appended conflict at its span''',
    '''Candidate account (not identified). Sections 4.7-4.8 favored a failure to encode the appended conflict at its span''')
rep('''M18 and M22 show that the information is nonetheless linearly recoverable from the missed span and from the decision state.''',
    '''M18 and M22 show that missed-conflict states are nonetheless linearly separable from benign ones, at the span and at the decision state.''')
rep('''The two observations are compatible: what the missed span lacks is the conflict in the form that downstream rows read - the round-keyed verdict that the layer-11 heads write in recognizing scenes (Section 4.13) - not the information itself. We therefore replace "missing encoding" with "represented but not used": the conflict is present but neither written into the read form at the span nor read at the decision. Decodability by a supervised probe does not show that the model uses a feature, and the causal half of this account (M19-M21) is kev-4B only.`),''',
    '''If that separability reflects conflict validity - which the G2.3 twins would test - the two observations are compatible with a candidate account in which the missed span lacks the round-sensitive signal that layer-11 attention writes in recognizing scenes (Section 4.13), rather than the information itself. We state "represented but not used" only as this candidate, replacing the earlier "missing encoding" candidate. Neither is identified: the probe labels are confounded with the arm, and the steering tests reach one token on one model.`),''')

# ---- 4.16 (P1-2) and new 4.17 safety table (P1-3) ----
rep('''h("4.16  A second scorer: the monitor stage replicates on SecJev-0.8B", HeadingLevel.HEADING_2),''',
    '''h("4.16  A second kev-family checkpoint: the monitor stage on SecJev-0.8B (same scenes)", HeadingLevel.HEADING_2),''')
rep('''The present-but-unused statement thus holds on both scorers at the level of decodability; the interventions of M1-M21 were run on kev-4B only.''',
    '''The separability therefore replicates on a second kev-family checkpoint, on the same 124 scenes and 17 source groups; this is a same-family re-test, not an independent replication, and it carries the same arm confound. The interventions of M1-M21 were run on kev-4B only.''')
rep('''we report the monitor as a safety demonstration, not as a contribution.`),
''',
    '''we report the monitor as a safety demonstration, not as a contribution.`),

  h("4.17  Safety endpoint: three-action errors by arm", HeadingLevel.HEADING_2),
  p(`The scorers' typed decision has three values, and errors are not only missed conflicts. Table S1 counts, for each model and arm (124 scenes, 17 source groups each), the missed conflicts, the false vetoes (reject_conflict on a scene whose Gold is accept or wait) and the accept/wait swaps; a swap from wait to accept is an acceptance without sufficient evidence. kev-4B's errors outside the new arm are mostly such acceptances, and its false vetoes are confined to wrong-round and outsider votes; SecJev false-vetoes every benign arm, including legal scenes, and swaps accept and wait often. A deterministic rule engine makes none of these errors on this simulator. These are S2 characterizations of two scorers on constructed scenes, not deployment rates, and the repairs of Sections 4.13-4.14 are not a defence.`),
  caption(`Table S1. Native three-action errors per arm (rows of 124 scenes). FV = reject_conflict on accept/wait Gold; swap = accept<->wait; groups = source groups (of 17) with at least one false veto.`),
  table(
    ["Model / arm", "Missed conflict", "False veto (groups)", "Accept/wait swaps", "Correct"],
    ["kev4b", "secjev"].flatMap(m => ["new", "old", "SA", "ROUND", "OUTSIDER"].map(a => [
      `${m === "kev4b" ? "kev-4B" : "SecJev"} / ${a}`, `${S3[m][a].missed_conflict}`,
      `${S3[m][a].false_veto} (${S3[m][a].groups_with_false_veto})`, `${S3[m][a].accept_wait_swap}`, `${S3[m][a].correct}`])),
    [28, 18, 20, 18, 16]
  ),

''')

# ---- discussion (P0) ----
rep('''the mechanism route (Sections 4.13-4.16) revises it to a conflict that is represented but not written into the form downstream rows read, and not read at the decision.''',
    '''the mechanism route (Sections 4.13-4.16) weakens it, and we now hold "represented but not used" only as a competing candidate: the probe evidence for it is confounded with the arm, and the tested steering covers one token. Neither candidate is identified.''')

# ---- limitations (P0-1, P1-2, P1-4, P1-5) ----
rep('''A supervised probe needs rule-labelled data, and a deterministic rule engine solves this task exactly, so the monitor is a diagnostic, not a defence.`),''',
    '''A supervised probe needs rule-labelled data, and a deterministic rule engine solves this task exactly, so the monitor is a diagnostic, not a defence. The probe labels coincide with the arm (every positive is a new row); the same-span counterfactual that would remove this confound (G2.3) is constructible but not run. The readout nulls lack direction specificity (a random push is equally inert). M22 re-tests one kev-family checkpoint on the same scenes. The 22/22 re-computation re-runs our own analysis scripts. The mechanism stages instantiate known phenomenon classes - activation patching, steering nulls and decodable-but-unused features - in a security-typed scorer with rule gold; their novelty is task-specific, not methodological.`),''')

# ---- reproducibility ----
rep('''compares each output with the committed JSON (PAPER_CLAIM_PACKAGE_V4).`),''',
    '''compares each output with the committed JSON (PAPER_CLAIM_PACKAGE_V4). v11 (PAPER_CLAIM_PACKAGE_V5) reads numbers_mech_v2.json, which adds the three-action table, the M21 action changes and the G2.3 coverage (research/rounds/A461_MON_G23_CONTEXT_COUNTERFACTUAL_CPU); the M1-M22 capture tensors are released as private GitHub Release assets (tag a461-mech-captures-m1-m22-v1).`),''')

io.open(sys.argv[2], "w", encoding="utf8", newline="\n").write(s)
print("ok", len(s))
