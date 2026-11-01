#!/usr/bin/env python3
"""Derive generate_v14.js from generate_v13.js (package V7): PIVOT_TO_PAPER revision for TMLR (audit 4acf7de path A;
re-audit ee23782; CPU go/no-go G2.4 = NO-GO). Text and offline statistics only; no GPU.

4acf7de P1-2  related work: "dissociation between represented and appended relational evidence", "the query side is
              not where the failure lives", "byte-identical same-span counterfactuals" narrowed; §4.18 "keeps the scene
              ... byte-identical" corrected (only the appended span is byte-identical; one earlier token changes)
4acf7de P1-3  source-group cluster-bootstrap CIs (Table T2 notes; numbers_mech_v5.json -> cluster_ci)
4acf7de P2-1  full twin Gold x prediction matrix (Table T2)
4acf7de P1-4  availability statement
ee23782/G2.4  limitations: no clean orthogonal partner edit; too few discordant pairs for a state swap
    python v14_edits.py ../PAPER_CLAIM_PACKAGE_V7/generate_v13.js generate_v14.js"""
import io, sys

s = io.open(sys.argv[1], encoding="utf8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:120])
    s = s.replace(old, new)


rep("/* Generate manuscript v13 (", "/* Generate manuscript v14 (TMLR-path revision per audit 4acf7de and the G2.4 NO-GO; numbers_mech_v5.json). v13 was (")
rep('const M = require("./numbers_mech_v4.json");', '''const M = require("./numbers_mech_v5.json");
const CC = M.cluster_ci;
const ci = x => `${pc(x.point)}% [${pc(x.ci95[0])}, ${pc(x.ci95[1])}]`;''')
rep('"Anonymous draft (v13; v12 narrowed after an independent paper-level audit)"', '"Anonymous draft (v14; prepared for TMLR)"')
rep('"Missed When Valid, Vetoed When Not (v13)"', '"Missed When Valid, Vetoed When Not (v14)"')
rep('fs.writeFileSync("A461_G2_paper_draft_v13.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v14.docx", buf)')

# ---- related work (P1-2) ----
rep("our results are the security-policy analogue - a dissociation between represented and appended relational evidence - measured with oracle gold and matched controls,",
    "our results are a security-policy analogue - a failure to act on appended relational evidence - measured with oracle gold and matched controls,")
rep("showing that, in this scorer, the query side is not where the failure lives.",
    "showing that, in this scorer and under our decomposition, the query-side term changes little when the conflict is appended.")
rep("byte-identical same-span counterfactuals in every scene and source group,",
    "counterfactuals that keep the appended span byte-identical at the same position and length and change one earlier partner-round token, in every scene and source group,")

# ---- 4.18 wording (P1-2) ----
rep("we built a twin that keeps the scene and the appended vote byte-identical and moves only the appended author's earlier vote",
    "we built a twin that keeps the appended vote byte-identical at the same position and length and changes only the appended author's earlier vote")

# ---- Table T2 + cluster CIs after Table T1 (P1-3, P2-1) ----
rep("  p(`Scope: one twin family was run (partner round, 124 scenes);",
    '''  p(`Uncertainty. Scenes are nested in 17 source groups of unequal size (1-16 scenes), so we resample source groups (10,000 bootstrap draws). kev-4B misses the appended conflict in ${ci(CC.M23k.new_missed_rate)} of scenes and false-vetoes ${ci(CC.M23k.twin_false_veto_rate)} of twins; where it rejects the conflict it rejects the twin in ${ci(CC.M23k.twin_reject_given_new_reject)} (${CC.M23k.twin_reject_given_new_reject.clusters} groups). SecJev misses ${ci(CC.M23s.new_missed_rate)} and false-vetoes ${ci(CC.M23s.twin_false_veto_rate)} of twins; its 14/14 conditional count comes from ${CC.M23s.twin_reject_given_new_reject.clusters} groups and the bootstrap is degenerate (every resample gives 100%), so we report only the exact binomial one-sided 95% lower bound, 0.81, which ignores clustering. For comparison, the benign-arm false-veto rate on the original scenes (Table S1) is ${ci(CC.M18_benign_false_veto_rate)} for kev-4B and ${ci(CC.M22_benign_false_veto_rate)} for SecJev, and the G2 kev-4B joint repair rate is ${ci(CC.KC_main_joint_rate.by_donor_group)} resampling donor groups and ${ci(CC.KC_main_joint_rate.by_host)} resampling hosts. All intervals are descriptive for these constructed scenes.`),
  caption(`Table T2. Twins: Gold x native prediction (124 per model). Gold is accept (102) or wait (22); a reject_conflict prediction is a false veto.`),
  table(
    ["Model", "accept -> accept", "accept -> wait", "accept -> reject", "wait -> wait", "wait -> accept", "wait -> reject"],
    [["kev-4B", TK], ["SecJev", TS]].map(([m, T]) => [m, ...["accept->accept", "accept->wait", "accept->reject_conflict", "wait->wait", "wait->accept", "wait->reject_conflict"].map(x => `${T.twin_confusion[x] || 0}`)]),
    [16, 14, 14, 14, 14, 14, 14]
  ),
  p(`Scope: one twin family was run (partner round, 124 scenes);''')

# ---- limitations: G2.4 (ee23782) ----
rep("Reproducibility ceiling: the M23 captures remain on the server,",
    "A CPU check of further edits (G2.4) found no clean orthogonal alternative: moving the partner vote to the appended vote's block makes the appended vote a duplicate (a form both scorers treat as benign), moving it to a third block is possible in 1 of 124 scenes, and a non-supporting author in 23 scenes from 7 groups; and a within-scene swap of conflict and twin states could change the decision only in the 11 (kev-4B) and 1 (SecJev) pairs whose decisions differ. We therefore stopped the mechanism route; this is a limit of the scene distribution, not evidence that no mechanism can be found. Reproducibility ceiling: the M23 captures remain on the server,")

# ---- availability (P1-4) ----
rep('''  h("References", HeadingLevel.HEADING_1),''', '''  h("8  Availability", HeadingLevel.HEADING_1),
  p("Released with the paper (for review: through an anonymized link): every preregistration, design, manifest, runner, self-test and analysis script; all raw native logits and execution receipts; the capture tensors of the G2 and M1-M22 stages with per-file SHA-256 lists; the scripts that extract every number in this paper from those files and regenerate the manuscript; and the deterministic re-computation of all M1-M22 analyses. Not released: the model weights and the kev-4B decision-head file (model assets), and the M23 capture tensors (to be added; their per-file hashes are archived). Independent checks to date re-counted the raw native outputs of G2 and M23; tensor-level probe statistics and the rendered layout have not been independently verified."),

  h("References", HeadingLevel.HEADING_1),''')

rep("a partner-block family is constructible in all 124 scenes and a partner-author family in 23, and neither was run;",
    "a partner-block family is constructible in all 124 scenes but turns the appended vote into a duplicate (Section 6), and a partner-author family is constructible in 23; neither was run;")
io.open(sys.argv[2], "w", encoding="utf8", newline="\n").write(s)
print("ok", len(s))
