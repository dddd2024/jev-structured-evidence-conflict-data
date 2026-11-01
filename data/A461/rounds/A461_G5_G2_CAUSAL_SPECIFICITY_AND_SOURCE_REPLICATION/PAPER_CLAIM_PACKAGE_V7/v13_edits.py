#!/usr/bin/env python3
"""Derive generate_v13.js from generate_v12.js (package V6), narrowing v12 per paper audit 8dd4528
(PAPER_AUDIT_REVISE_REQUIRED, P0x2 / P1x5 / P2x2). Text only; no new GPU run.

P0-1  "do not check / does not depend / ignores" -> behavioral non-robustness on one matched counterfactual, not an
      internal mechanism; the title is narrowed accordingly.
P0-2  ARM_SHORTCUT != "validity never represented": "no probe separates" -> "no probe meets the preregistered
      validity-tracking gate"; SecJev's L11 span write partial context sensitivity is stated prominently.
P1-1  the transplanted state is not identified with a shortcut judgment.
P1-2  new close prior work (named by the audit) in related work and references.
P1-3  source-group spread (14/17, 9/17) and conditional denominators.
P1-4  twins' full three-action outcome and accept/wait swaps.
P1-5  reproducibility ceiling (M23 captures server-side, head.pt unreleased, recompute = own scripts).
P2-1  edit families executed / not run; the 4 quorum-change twins.
Numbers: numbers_v8.json and numbers_mech_v4.json. Every replaced span must occur exactly once.
    python v13_edits.py ../PAPER_CLAIM_PACKAGE_V6/generate_v12.js generate_v13.js"""
import io, sys

s = io.open(sys.argv[1], encoding="utf8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:120])
    s = s.replace(old, new)


rep("/* Generate manuscript v12 (", "/* Generate manuscript v13 (v12 narrowed per paper audit 8dd4528; numbers_mech_v4.json). v12 was (")
rep('const M = require("./numbers_mech_v3.json");', 'const M = require("./numbers_mech_v4.json");')
rep('"Missed When Valid, Vetoed When Not: Two Typed Language-Model Scorers Judge an Appended Equivocation Vote by Its Form, and Transplanted Span States Carry That Judgment"',
    '"Missed When Valid, Vetoed When Not: Two Typed Language-Model Scorers\' Conflict Decisions Are Not Robust to the Validity of an Appended Vote"')
rep('"Anonymous draft (v12; reframed after a preregistered same-span twin test)"',
    '"Anonymous draft (v13; v12 narrowed after an independent paper-level audit)"')
rep('"Missed When Valid, Vetoed When Not (v12)"', '"Missed When Valid, Vetoed When Not (v13)"')
rep('fs.writeFileSync("A461_G2_paper_draft_v12.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v13.docx", buf)')

# ---------------- abstract ----------------
rep("never trained on these scenes. They do not. The appended vote leaves",
    "never trained on these scenes. On a matched counterfactual, their decisions mostly do not follow it. The appended vote leaves")
rep("false-vetoing ${TK.native.twin_false_veto}/124 and ${TS.native.twin_false_veto}/124 legitimate twins,",
    "false-vetoing ${TK.native.twin_false_veto}/124 (in ${TK.twin_fv_groups} of ${TK.groups} source groups) and ${TS.native.twin_false_veto}/124 (${TS.twin_fv_groups} of ${TS.groups}) legitimate twins,")
rep("and removing the double vote raises, rather than lowers, the conflict margin in the scenes they miss. Their conflict judgment follows the appended vote's form - a vote for another block in the candidate round, unlike a duplicate vote - not its validity.",
    "and removing the double vote raises, rather than lowers, the median conflict margin in the scenes they miss. On this edit family their decisions are consistent with a form cue - a vote for another block in the candidate round, unlike a duplicate vote - and are not robust to the vote's validity; this describes behavior on one matched counterfactual, not an identified internal mechanism.")
rep("flag the no-conflict twins as often as the conflicts (preregistered verdict ARM_SHORTCUT for every detector on both models): they read the same form.",
    "flag most no-conflict twins, and no detector on either model meets the preregistered validity-tracking gate (verdict ARM_SHORTCUT); SecJev's layer-11 span write nonetheless scores the conflict above its twin in ${pc(tdet(TS, \"PROBE:SPAN_ATTN11\").paired_frac_new_gt_twin)}% of missed scenes, so the test does not show that validity is never represented.")

# ---------------- introduction ----------------
rep("and a same-span twin test (Section 4.18) shows that, where the scorers do flag it, they flag the vote's form rather than its validity - they reject no-conflict twins almost as often, and false-veto legitimate scenes that share the form.",
    "and a same-span twin test (Section 4.18) shows that, where the scorers do flag it, their rejections are mostly not robust to the vote's validity - they reject no-conflict twins almost as often, and false-veto legitimate scenes that share the form.")
rep("linear probes trained on these scenes separate missed conflicts from benign scenes on both scorers but read the same form (they flag the twins),",
    "linear probes trained on these scenes separate missed conflicts from benign scenes on both scorers, but none meets a preregistered validity-tracking gate on the twins (they flag most of them), with partial context sensitivity in SecJev's layer-11 span write;")
rep("Section 4.18 shows that this readout is not validity-sensitive, so \"recognized\" means readout-positive throughout.",
    "Section 4.18 shows that this readout is mostly not robust to the vote's validity, so \"recognized\" means readout-positive throughout.")

# ---------------- related work ----------------
rep("in this simulator, the form of an appended vote (another block, candidate round, not a duplicate) is correlated with equivocation in the natural data, and both scorers' conflict judgment follows it.",
    "in this simulator, the form of an appended vote (another block, candidate round, not a duplicate) is correlated with equivocation in the natural data, and on our matched edit both scorers' decisions are largely consistent with it. Recent work studies such shortcuts mechanistically - path patching of a shortcut circuit (Yan et al., 2026), gold-versus-counterfactual supporting evidence with activation patching (Buzato et al., 2026), and disentangling bias shortcuts (Feng et al., 2026) - and structured policy and evidence supervision has been proposed for scorers of this family (TrustJev, 2026); against these, our addition is a security-typed vote rule with executable gold, byte-identical same-span counterfactuals in every scene and source group, three-action safety outcomes, and causal transplants of the scorers' own readout-positive states, not a new method.")
rep('''  ref("[25] Geirhos''', '''  ref("[27] Yan et al. Spurious Rewards Paradox. ICML 2026 (PMLR v306). https://proceedings.mlr.press/v306/yan26f.html"),
  ref("[28] Buzato et al. On the Role of Supporting Evidence in LLM Reasoning. EMNLP 2026. https://aclanthology.org/2026.emnlp-main.1562/"),
  ref("[29] Feng et al. C2PO: Diagnosing and Disentangling Bias Shortcuts in LLMs. Findings of ACL 2026. https://aclanthology.org/2026.findings-acl.1226/"),
  ref("[30] TrustJev. arXiv:2610.34826, 2026."),
  ref("[25] Geirhos''')

# ---------------- terminology ----------------
rep("the same-span twins of Section 4.18 show that both scorers return the same readout when the appended vote is not a conflict.",
    "the same-span twins of Section 4.18 show that both scorers mostly return the same readout when the appended vote is not a conflict.")

# ---------------- 4.15 / 4.16 ----------------
rep("the probes flag the no-conflict twins as often as the conflicts, so the separability follows the appended item's form.",
    "the probes flag most no-conflict twins and none meets the validity-tracking gate, so on this edit the separability is largely explained by the appended item's form.")
rep("the probes that suggested a represented conflict read the vote's form, and the scorers' own readout does not depend on the double vote. Neither candidate is supported.",
    "the probe evidence for it does not survive the twin test, and the scorers' own readout is mostly not robust to the double vote. Neither candidate is supported, and the twin test does not establish the converse - that validity is never represented (Section 4.18).")
rep("in the scenes they flag, the readout is triggered by the form whether or not a conflict exists.",
    "in the scenes they flag, the readout mostly stays positive when the conflict is removed.")
rep("and Section 4.18 shows that both detect the vote's form, so the monitor is not a validity monitor.",
    "and Section 4.18 shows that neither meets the validity-tracking gate, so the monitor is not a validity monitor.")

# ---------------- 4.18 ----------------
rep('h("4.18  Same-span twins: the scorers and the probes track the vote\'s form, not its validity", HeadingLevel.HEADING_2),',
    'h("4.18  Same-span twins: the scorers\' decisions and the probes are not robust to the vote\'s validity", HeadingLevel.HEADING_2),')
rep("Neither scorer's conflict judgment depends on the element that defines an equivocation.`),",
    '''On this matched edit, neither scorer's decisions reliably follow the element that defines an equivocation; the twins differ from the conflicts in a minority of scenes (kev-4B rejects ${TK.recognized - TK.twin_rejected_in_recognized} fewer twins where it rejects the conflict, and ${TK.twin_rejected_where_new_missed} twins where it misses it; SecJev ${TS.twin_rejected_where_new_missed}). The twins' full three-action outcome is reject / accept / wait ${TK.twin_pred_totals.reject_conflict} / ${TK.twin_pred_totals.accept} / ${TK.twin_pred_totals.wait} for kev-4B and ${TS.twin_pred_totals.reject_conflict} / ${TS.twin_pred_totals.accept} / ${TS.twin_pred_totals.wait} for SecJev, against Gold accept 102 / wait 22; the false vetoes fall in ${TK.twin_fv_groups} and ${TS.twin_fv_groups} of ${TK.groups} source groups, and SecJev also swaps accept and wait in ${TS.twin_accept_wait_swap} twins. In ${TK.quorum_change_twins.n} scenes moving the partner vote also removes quorum, so Gold becomes wait rather than accept. The scene counts share 17 source groups, and the 40 and 14 conditional denominators are the scenes each scorer happened to reject; these are descriptive counts on constructed scenes, not error rates. This describes behavior on one matched edit, not the scorers' internal computation.`),''')
rep("With arm, form and span held fixed and only validity flipped, no probe separates conflict from twin.",
    "With arm, form and span held fixed and only validity flipped, no probe meets the preregistered validity-tracking gate.")
rep("The one partial exception is SecJev's layer-11 span write, which scores the conflict above its twin in ${pc(tdet(TS, \"PROBE:SPAN_ATTN11\").paired_frac_new_gt_twin)}% of missed scenes but still flags most twins.`),",
    "This does not show that validity is never represented. SecJev's layer-11 span write scores the conflict above its twin in ${pc(tdet(TS, \"PROBE:SPAN_ATTN11\").paired_frac_new_gt_twin)}% of missed scenes (AUROC_pair ${f3(tdet(TS, \"PROBE:SPAN_ATTN11\").AUROC_pair)}), so some context information reaches it; it fails the gate because it still flags most twins at the operating threshold. ARM_SHORTCUT is a verdict about validity specificity at that threshold, not about the absence of relation information.`),")
rep("Scope: one twin family (partner round; a partner-author family was constructible in only 23 scenes), the same 124 scenes, two kev-family checkpoints. The G2 transplant results stand as interventions; what changes is what the transplanted state is: the state behind a form-driven positive readout, which a host applies downstream - including, as M17 showed, to scenes with no conflict.`),",
    "Scope: one twin family was run (partner round, 124 scenes); a partner-block family is constructible in all 124 scenes and a partner-author family in 23, and neither was run; the same 124 scenes; two kev-family checkpoints. The G2 transplant results stand as interventions on the state of readout-positive scenes, which a host applies downstream - including, as M17 showed, to scenes with no conflict. We do not identify that state with a shortcut judgment: no experiment swapped the conflict's and the twin's states within a scene.`),")

# ---------------- discussion ----------------
rep("The scorers do not check the relation that makes the appended vote a conflict. Where they flag it, they flag a form that equivocations share with legitimate scenes, and they flag the legitimate scenes too; where they miss it, the defining double vote does not help (removing it raises the margin).",
    "On a matched same-span counterfactual, the scorers' decisions are mostly not robust to the relation that makes the appended vote a conflict. Where they flag it, they mostly flag the no-conflict twin too; where they miss it, removing the double vote raises the median margin. This is behavior on one edit family; it does not show that the scorers never use the relation internally.")
rep("What it carries is the state behind a form-driven positive readout,", "What it carries is the state of a readout-positive scene - a readout that, on this edit, is not robust to validity -")
rep("and the transplanted state is real causal content; but in this task that content is a judgment about form.",
    "and the transplanted state is real causal content; we do not identify that content with a shortcut judgment, because no experiment swapped the conflict's and the twin's states.")
rep("and neither repairs nor probes trained on arm-correlated labels fix that.",
    "on these scenes, and neither the repairs nor probes trained on arm-correlated labels fix that.")

# ---------------- limitations ----------------
rep("That the scorers' positive readout is form-driven is shown on these scenes; whether it holds on other scene families is untested.",
    "That the scorers' positive readout is not robust to validity is shown for one edit family on these scenes; whether it holds for the partner-block and partner-author families, or on other scene families, is untested. Reproducibility ceiling: the M23 captures remain on the server, the kev-4B head file needed by M19 / M21 is not released, the 22/22 re-computation re-runs our own scripts, and the rendered document layout has not been independently checked.")

# ---------------- reproducibility ----------------
rep("preregistration 5bd58f6, result 543b259).`),",
    "preregistration 5bd58f6, result 543b259). v13 (PAPER_CLAIM_PACKAGE_V7) reads numbers_mech_v4.json, which adds the twins' three-action table, source-group spread and quorum-change scenes.`),")

io.open(sys.argv[2], "w", encoding="utf8", newline="\n").write(s)
print("ok", len(s))
