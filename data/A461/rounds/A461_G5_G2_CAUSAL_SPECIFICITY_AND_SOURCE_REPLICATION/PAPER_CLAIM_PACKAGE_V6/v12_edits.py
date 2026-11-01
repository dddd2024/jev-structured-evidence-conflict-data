#!/usr/bin/env python3
"""Derive generate_v12.js from generate_v11.js (package V5): full reframe after M23 (same-span twins, prereg 5bd58f6,
result 543b259). Both scorers' conflict judgment follows the appended vote's form, not its validity; the probes read
the same form (ARM_SHORTCUT, both models); "represented but not used" is withdrawn; "recognized" is defined as
readout-positive. New title, abstract, contributions, terminology paragraph, section 4.18 with Table T1, revised 4.10,
4.15, 4.16, discussion, limitations and reproducibility. Numbers: numbers_v8.json (G2) and numbers_mech_v3.json.
Every replaced span must occur exactly once.
    python v12_edits.py ../PAPER_CLAIM_PACKAGE_V5/generate_v11.js generate_v12.js"""
import io, sys

s = io.open(sys.argv[1], encoding="utf8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:120])
    s = s.replace(old, new)


def rep_line(prefix, new):
    """replace the whole source line whose stripped text starts with prefix (must be unique)"""
    global s
    lines = s.split("\n")
    hit = [i for i, x in enumerate(lines) if x.strip().startswith(prefix)]
    assert len(hit) == 1, (len(hit), prefix[:100])
    lines[hit[0]] = new
    s = "\n".join(lines)


rep("/* Generate manuscript v11 (", "/* Generate manuscript v12 (full reframe after M23: the scorers judge the appended vote's form, not its validity; numbers_mech_v3.json). v11 was (")
rep('const M = require("./numbers_mech_v2.json");', '''const M = require("./numbers_mech_v3.json");
const TW = M.M23.models, TK = TW.k, TS = TW.s;
const tdet = (m, d) => m.detectors[d];''')
rep('"Missed When Added, Repaired When Implanted: Recognized-Evidence Span Transplants Repair Missed Appended Conflicts Across Source Groups in Two Typed Language-Model Scorers"',
    '"Missed When Valid, Vetoed When Not: Two Typed Language-Model Scorers Judge an Appended Equivocation Vote by Its Form, and Transplanted Span States Carry That Judgment"')
rep('"Anonymous draft (v11; v10 narrowed after an independent paper-level audit of the mechanism route)"',
    '"Anonymous draft (v12; reframed after a preregistered same-span twin test)"')
rep('"Missed When Added, Repaired When Implanted (v11)"', '"Missed When Valid, Vetoed When Not (v12)"')
rep('fs.writeFileSync("A461_G2_paper_draft_v11.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v12.docx", buf)')

# ---------------- abstract ----------------
rep_line("p(`When new policy-relevant evidence arrives in a security decision context", '''  p(`Appending one valid equivocation vote to a structured consensus scene - a vote for another block, in the candidate round, by a validator who has already voted for the candidate block - makes reject_conflict the rule-mandated decision. We ask whether two kev-family typed scorers check what makes such a vote a conflict: SecJev-0.8B, a security specialist, and kev-4B, a general typed-decision model never trained on these scenes. They do not. The appended vote leaves SecJev's conflict readout false in ${pct(A.missed_rate_new)}% of ${A.scenes} preregistered scenes and kev-4B's in ${pct(K4.missed_rate_new)}%. In a preregistered same-span twin test we keep the appended vote byte-identical and move only the author's earlier vote to another round, so that no conflict exists: the scorers still reject the twin in ${TK.twin_rejected_in_recognized} of the ${TK.recognized} scenes in which kev-4B rejected the conflict and in ${TS.twin_rejected_in_recognized} of ${TS.recognized} for SecJev, false-vetoing ${TK.native.twin_false_veto}/124 and ${TS.native.twin_false_veto}/124 legitimate twins, and removing the double vote raises, rather than lowers, the conflict margin in the scenes they miss. Their conflict judgment follows the appended vote's form - a vote for another block in the candidate round, unlike a duplicate vote - not its validity. Within that frame we ask what the internal state behind a positive readout does. Across nine preregistered G2 stages (${N.ledger_total_g2.toLocaleString("en-US")} forwards), the natural layer-11 appended-span state of a readout-positive ("recognized") donor scene, transplanted into a scene from another source group, raises the conflict margin beyond sham, permutation and dose-matched controls (SecJev ${C.H1.supportive}/${C.H1.cells} cells) and repairs the readout and the decision together (kev-4B ${KC.spec_joint}/${KC.cells} cross-group cells from all ${KC.spec_joint_groups} donor groups; controls 0), while spans from readout-negative scenes never repair (${F.joint.fff_new}/${F.cells.fff_new}; ${KC.unrec.JOINT}/${KC.unrec.cells}). A preregistered mechanism route on kev-4B (${M.forwards_total.toLocaleString("en-US")} forwards) finds that this state carries a signal sensitive to the appended vote's own round (changing only that round turns ${M.M1.J_main}/${M.M1.cells} joint repairs into ${M.M1.J_round}), written mainly by layer-11 attention from the bulk of the context, locally sufficient in hosts and partly necessary in ${Math.round(M.M20.round_self.C_loss * M.M20.round_self.n)}/${M.M20.round_self.n} donors - and that implanting it vetoes benign scenes too. Linear probes that separate missed conflicts from benign scenes (held-out AUROC ${f3(M18s.AUROC)}; SecJev ${f3(M22s.AUROC)}) flag the no-conflict twins as often as the conflicts (preregistered verdict ARM_SHORTCUT for every detector on both models): they read the same form. The scorers, scenes and edits come from one constructed simulator family; a deterministic rule engine solves the task exactly, and nothing here is a defence.`),''')

# ---------------- introduction ----------------
rep_line("p(`This version adds the causal program that the v5 pilot could only motivate.", '''  p(`This version reframes the paper around its last preregistered test. The contributions are four. First, behavior: a screen of all remaining constructible scenes bounds how rarely the appended conflict is flagged (${A.strict} strict readout-positive donors in ${N.screened_total} scenes), and a same-span twin test (Section 4.18) shows that, where the scorers do flag it, they flag the vote's form rather than its validity - they reject no-conflict twins almost as often, and false-veto legitimate scenes that share the form. Second, transplants (G2, Sections 4.5-4.11): the natural layer-11 appended-span state of a readout-positive scene is causally sufficient, across source groups and beyond sham, permutation and dose-matched controls, to produce the rule-mandated readout and decision in a host that missed the conflict, and spans of readout-negative scenes never are; kev-4B replicates the repair across fourteen donor groups with the window chosen on disjoint scenes. Third, mechanism (kev-4B, Sections 4.12-4.14): that state carries a signal sensitive to the appended vote's own round, written mainly by layer-11 attention from the bulk of the context, locally sufficient in hosts and partly necessary in recognizing donors; four representative repair families were checked for false veto, and the own-donor patch vetoes benign scenes as readily as it repairs. Fourth, probes and safety (Sections 4.15-4.18): linear probes trained on these scenes separate missed conflicts from benign scenes on both scorers but read the same form (they flag the twins), steering the decision state along their direction does not repair, and per-arm three-action errors (Table S1) and twin false vetoes quantify the safety cost. Terminology: we keep the preregistered word "recognized" for donors whose conflict readout is true on the appended vote and false on the original and duplicate-vote scenes; Section 4.18 shows that this readout is not validity-sensitive, so "recognized" means readout-positive throughout.`),''')

# ---------------- related work: shortcut learning ----------------
rep('''  p(`Several recent lines bear directly on the G2 results.''',
    '''  p(`Shortcut learning - models that succeed on a benchmark by keying on a feature correlated with the label rather than on the intended rule (Geirhos et al., 2020; McCoy, Pavlick and Linzen, 2019) - is the closest frame for our behavioral finding: in this simulator, the form of an appended vote (another block, candidate round, not a duplicate) is correlated with equivocation in the natural data, and both scorers' conflict judgment follows it. Probing work warns that a probe may decode a label-correlated feature rather than the intended variable; our same-span twins are a direct control for that in this task.`),
  p(`Several recent lines bear directly on the G2 results.''')
rep('''  ref("[21] A461-G5-G2 evidence chain''', '''  ref("[25] Geirhos, R., Jacobsen, J.-H., Michaelis, C., Zemel, R., Brendel, W., Bethge, M., Wichmann, F. A. Shortcut Learning in Deep Neural Networks. Nature Machine Intelligence 2, 665-673, 2020."),
  ref("[26] McCoy, R. T., Pavlick, E., Linzen, T. Right for the Wrong Reasons: Diagnosing Syntactic Heuristics in Natural Language Inference. ACL 2019."),
  ref("[21] A461-G5-G2 evidence chain''')

# ---------------- method: terminology ----------------
rep('''  h("3.5  Semantic controls and the second scorer", HeadingLevel.HEADING_2),''',
    '''  p(`Terminology. A donor is "recognized" (strict) if its conflict readout is true on the scene with the appended vote and false on the original scene and on the duplicate-vote scene; the preregistrations use this word, and we keep it. It names a readout pattern, not a validity check: the same-span twins of Section 4.18 show that both scorers return the same readout when the appended vote is not a conflict. Read "recognized" as "readout-positive" throughout.`),
  h("3.5  Semantic controls and the second scorer", HeadingLevel.HEADING_2),''')

# ---------------- G2 headings ----------------
rep('h("4.6  Specificity: the recognized span carries content beyond dose, position and token form"',
    'h("4.6  Specificity: the readout-positive span carries content beyond dose, position and token form"')
rep('h("4.9  Repair: implanting a recognized encoding flips the readout and the decision"',
    'h("4.9  Repair: implanting a readout-positive span state flips the readout and the decision"')
rep('h("4.10  Semantic controls: among the source categories tested, only recognized appended-conflict spans repair"',
    'h("4.10  Semantic controls: among the source categories tested, only readout-positive appended-vote spans repair"')
rep('''It is consistent with an encoding account and constrains, but does not exclude, content- or context-based accounts.`),''',
    '''It constrains, but does not exclude, content- or context-based accounts. Section 4.18 adds that the scorers' positive readout is itself not validity-sensitive, so this is a contrast between readout-positive and readout-negative sources, not between conflicts the model checked and conflicts it did not.`),''')

# ---------------- Table M1 row ----------------
rep('''      ["M22 (SecJev)", "Does M18 replicate on the second scorer?",''',
    '''      ["M23 (both)", "Do the probes and the scorers track validity or form? (same-span twins)", `kev-4B and SecJev: ARM_SHORTCUT on every detector`, `${M.M23.forwards_total}`],
      ["M22 (SecJev)", "Does M18 replicate on the second scorer?",''')

# ---------------- 4.15 / 4.16 ----------------
rep('h("4.15  Missed-conflict states are linearly separable; tested decision-token steering does not repair", HeadingLevel.HEADING_2),',
    'h("4.15  Missed-conflict states are linearly separable - by form - and tested decision-token steering does not repair", HeadingLevel.HEADING_2),')
rep('''A CPU check (G2.3) shows that a same-span counterfactual exists in all 124 scenes and 17 source groups: the appended vote is kept byte-identical and only the round of the author's earlier vote changes (one token), which moves Gold away from reject_conflict. Scoring these twins with the frozen probes would separate conflict validity from arm; that GPU stage has not been run.`),''',
    '''Section 4.18 removes this confound with same-span twins: the probes flag the no-conflict twins as often as the conflicts, so the separability follows the appended item's form.`),''')
rep_line("p(`Candidate account (not identified).", '''  p(`What this leaves of the earlier candidate accounts. Sections 4.7-4.8 favored a failure to encode the appended conflict at its span; v10 replaced it with "represented but not used". Section 4.18 withdraws the second: the probes that suggested a represented conflict read the vote's form, and the scorers' own readout does not depend on the double vote. Neither candidate is supported. What remains is a narrower statement: in the scenes the scorers miss, the form that drives their readout elsewhere is present but does not trigger it, and in the scenes they flag, the readout is triggered by the form whether or not a conflict exists.`),''')
rep('''this is a same-family re-test, not an independent replication, and it carries the same arm confound.''',
    '''this is a same-family re-test, not an independent replication, and it carries the same arm confound, which Section 4.18 resolves for both models.''')
rep('''Because generic last-token probes match the mechanism-located monitor on both scorers, we report the monitor as a safety demonstration, not as a contribution.''',
    '''Generic last-token probes match the mechanism-located monitor on both scorers, and Section 4.18 shows that both detect the vote's form, so the monitor is not a validity monitor.''')

# ---------------- new 4.18 after Table S1 ----------------
rep('''  h("5  Discussion", HeadingLevel.HEADING_1),''', '''  h("4.18  Same-span twins: the scorers and the probes track the vote's form, not its validity", HeadingLevel.HEADING_2),
  p(`For each of the 124 scenes we built a twin that keeps the scene and the appended vote byte-identical and moves only the appended author's earlier vote for the candidate block to the nearest non-candidate round (exactly one token, before the span), so that the author no longer double-votes and Gold becomes accept (102) or wait (22); both oracles agree, and the twin is constructible in every scene and source group. A preregistered stage (M23, ${M.M23.forwards.k} kev-4B and ${M.M23.forwards.s} SecJev forwards) replayed the 124 appended-conflict scenes - bitwise equal to M18 / M22 in logits and captures - and ran the twins with the same read-only captures; the M18 / M22 probes were refit exactly (the refit reproduces their held-out AUROC) and scored the held-out group's rows.`),
  p(`The scorers. Where kev-4B rejects the appended conflict (${TK.recognized} scenes), it also rejects the twin in ${TK.twin_rejected_in_recognized}, and its conflict readout is positive on ${TK.twin_C_pos_in_recognized} twins (${TK.new_C_pos_in_recognized} conflicts); SecJev rejects ${TS.twin_rejected_in_recognized} of ${TS.recognized} twins where it rejects the conflict. Where they miss the conflict, removing the double vote raises the conflict margin (median ${s(TK.median_dM_twin_minus_new_missed)} kev-4B, ${s(TS.median_dM_twin_minus_new_missed)} SecJev). Across all twins kev-4B false-vetoes ${TK.native.twin_false_veto}/124 and SecJev ${TS.native.twin_false_veto}/124 legitimate scenes. Neither scorer's conflict judgment depends on the element that defines an equivocation.`),
  p(`The probes. With arm, form and span held fixed and only validity flipped, no probe separates conflict from twin. On the missed scenes the preregistered span monitor flags ${pc(tdet(TK, "PROBE:SPAN_ATTN11")["twin_flag@FV5"])}% of kev-4B's twins (conflicts ${pc(tdet(TK, "PROBE:SPAN_ATTN11")["new_flag@FV5"])}%) and ${pc(tdet(TS, "PROBE:SPAN_ATTN11")["twin_flag@FV5"])}% of SecJev's (${pc(tdet(TS, "PROBE:SPAN_ATTN11")["new_flag@FV5"])}%), and the twins score like conflicts rather than like benign scenes (twin-vs-benign AUROC ${tdet(TK, "PROBE:SPAN_ATTN11").AUROC_twin_vs_parent_benign} and ${tdet(TS, "PROBE:SPAN_ATTN11").AUROC_twin_vs_parent_benign}). Every detector on both models meets the preregistered ARM_SHORTCUT rule (Table T1). The one partial exception is SecJev's layer-11 span write, which scores the conflict above its twin in ${pc(tdet(TS, "PROBE:SPAN_ATTN11").paired_frac_new_gt_twin)}% of missed scenes but still flags most twins.`),
  caption(`Table T1. Same-span twin test (M23), missed scenes (kev-4B ${TK.missed_scenes}, SecJev ${TS.missed_scenes}). AUROC_pair: conflict vs its own twin (0.5 = indistinguishable; CI from source-group bootstrap). Flags at the parent's FV5 operating point. Verdict rule: VALIDITY_TRACKED needs AUROC_pair >= 0.80 (CI lower >= 0.65) and twin flags <= 25%; ARM_SHORTCUT if AUROC_pair <= 0.65 or twin flags >= 50%.`),
  table(
    ["Model / detector", "AUROC_pair (CI)", "Twins flagged", "Conflicts flagged", "Verdict"],
    [["k", TK], ["s", TS]].flatMap(([m, T]) => T.primary.map(d => [
      `${m === "k" ? "kev-4B" : "SecJev"} / ${d.replace("PROBE:", "")}`,
      `${f3(tdet(T, d).AUROC_pair)} [${tdet(T, d).ci_AUROC_pair.join(", ")}]`,
      `${pc(tdet(T, d)["twin_flag@FV5"])}%`, `${pc(tdet(T, d)["new_flag@FV5"])}%`, T.verdicts[d]])),
    [30, 22, 16, 16, 16]
  ),
  p(`Scope: one twin family (partner round; a partner-author family was constructible in only 23 scenes), the same 124 scenes, two kev-family checkpoints. The G2 transplant results stand as interventions; what changes is what the transplanted state is: the state behind a form-driven positive readout, which a host applies downstream - including, as M17 showed, to scenes with no conflict.`),

  h("5  Discussion", HeadingLevel.HEADING_1),''')

# ---------------- discussion ----------------
rep_line("p(`The v5 account - a key-side localization plus a one-donor signed sensitivity", '''  p(`The question the paper began with - does a trained typed scorer encode new policy-relevant evidence, and if not, can its decision be repaired from the inside - has a sharper answer than the one we set out to defend. The scorers do not check the relation that makes the appended vote a conflict. Where they flag it, they flag a form that equivocations share with legitimate scenes, and they flag the legitimate scenes too; where they miss it, the defining double vote does not help (removing it raises the margin). The v5 key-side localization and the G2 transplants are best read in that light. The readout-positive span carries content-specific information - it beats its own duplicate-vote span, a permutation and a random perturbation of exactly its size, across source groups - and implanting it produces the rule-mandated readout and decision in hosts that missed the conflict. What it carries is the state behind a form-driven positive readout, sensitive to the appended vote's own round (M1) and written mainly by layer-11 attention from the bulk of the context; downstream rows apply it without re-checking (M17). The earlier candidate accounts - a missing encoding (v9) and a represented-but-unused conflict (v10-v11) - are both withdrawn: the first was never identified, and the evidence for the second was a probe confound that the twins remove. Whole-span transplants cannot separate a feature from its downstream decoding and interactions (Vaidyanathan et al., 2026), and the transplanted state is real causal content; but in this task that content is a judgment about form.`),''')
rep('''so the contribution is a mechanistic account of how a trained scorer fails and how that failure can be causally repaired, not an argument for model-based decisions.`),''',
    '''so the contribution is an account of what two trained scorers check - and fail to check - and of what their internal conflict state does when moved between scenes, not an argument for model-based decisions. For safety the implication is direct: these scorers both miss real equivocations and veto legitimate scenes that look like them, and neither repairs nor probes trained on arm-correlated labels fix that.`),''')

# ---------------- limitations ----------------
rep('''The probe labels coincide with the arm (every positive is a new row); the same-span counterfactual that would remove this confound (G2.3) is constructible but not run.''',
    '''The probe labels coincide with the arm; the same-span twins (M23) resolve this as ARM_SHORTCUT for one twin family (partner round) on the same 124 scenes; a partner-author family was constructible in only 23 scenes and was not run. That the scorers' positive readout is form-driven is shown on these scenes; whether it holds on other scene families is untested.''')

# ---------------- reproducibility ----------------
rep('''the M1-M22 capture tensors are released as private GitHub Release assets (tag a461-mech-captures-m1-m22-v1).`),''',
    '''the M1-M22 capture tensors are released as private GitHub Release assets (tag a461-mech-captures-m1-m22-v1). v12 (PAPER_CLAIM_PACKAGE_V6) reads numbers_mech_v3.json, which adds the M23 same-span twin test (research/rounds/A461_MON_M23_TWIN_PROBE_GPU; preregistration 5bd58f6, result 543b259).`),''')

# ---------------- leftovers ----------------
rep("A preregistered mechanism route on kev-4B (${M.forwards_total.toLocaleString(\"en-US\")} forwards)", "A preregistered mechanism route on kev-4B (${M.forwards_k4b.toLocaleString(\"en-US\")} forwards)")
rep("and implanting a recognized encoding there is sufficient to produce the rule-mandated decision.", "and implanting a readout-positive span state there is sufficient to produce the rule-mandated decision.")
rep("we treat it as consistent with, not as proof of, the encoding account.", "we treat it as consistent with, not as proof of, the encoding account considered at the time, which Sections 4.15 and 4.18 withdraw.")

rep("${TOTAL_FWD.toLocaleString(\"en-US\")} native FP32 forward passes across fourteen GPU stages and two models", "${(TOTAL_FWD + M.forwards_total + M.M23.forwards_total).toLocaleString(\"en-US\")} native FP32 forward passes across ${14 + Object.keys(M.forwards).length + 2} GPU runs and two models")
io.open(sys.argv[2], "w", encoding="utf8", newline="\n").write(s)
print("ok", len(s))
