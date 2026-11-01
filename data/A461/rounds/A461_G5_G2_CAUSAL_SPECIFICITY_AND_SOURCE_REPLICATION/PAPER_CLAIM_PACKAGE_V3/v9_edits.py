#!/usr/bin/env python3
"""Derive assemble_v9.py from assemble_v8.py, revising v8 per paper audit d9d3338 (PAPER_AUDIT_REVISE_REQUIRED, P0x1/P1x3).

P0:   the Stage-F / K-C4 contrast compares tested source categories; it does not isolate recognition from content,
      context or host interaction (section 4.10 title and text, contribution list, discussion).
P1-1: two kev-family checkpoints throughout sections 5 and 6; the cause of the SecJev/kev-4B differences is not isolated.
P1-2: a comparison table against the closest prior work (Table R1) in section 2.
P1-3: the kev-4B replication holds out scenes, not source groups; cells share hosts and are not independent tasks.
No numbers change: the generator still reads numbers_v8.json. Every replaced span must occur exactly once."""
import io

s = io.open("assemble_v8.py", encoding="utf8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:100])
    s = s.replace(old, new)


rep("""/* Generate manuscript v8 (v7 + Stage-F semantic controls and the kev-4B second-model stages). Built from""",
    """/* Generate manuscript v9 (v8 revised per paper audit d9d3338: recognition claim narrowed to tested source categories, two-checkpoint scope, related-work comparison table, scene-level hold-out). v8 was v7 + Stage-F semantic controls and the kev-4B second-model stages. Built from""")
rep('''text: "Anonymous draft (v8; v7 extended with semantic negative controls and a second-model replication)"''',
    '''text: "Anonymous draft (v9; v8 revised after a second independent paper-level audit: claims about recognition narrowed, related-work comparison added)"''')

# ---- abstract (P1-3) ----
rep('''a layer scan on one set of scenes selects layer ${KB.window} by a preregistered rule, and on disjoint donors and hosts the recognized span''',
    '''a layer scan on one set of scenes selects layer ${KB.window} by a preregistered rule, and on donor and host scenes disjoint from the scan (source groups overlap) the recognized span''')
rep('''while unrecognized-conflict spans repair ${KC.unrec.JOINT}/${KC.unrec.cells}. The supported claim''',
    '''while unrecognized-conflict spans repair ${KC.unrec.JOINT}/${KC.unrec.cells}; cells share hosts, so these are descriptive counts, not rates over independent tasks. The supported claim''')

# ---- contributions (P0, P1-3) ----
rep('''Fifth, semantic negative controls separate recognition from content and from decision class, and a second, larger scorer (kev-4B) replicates the repair across fourteen donor groups with the analysis window chosen on disjoint scenes.''',
    '''Fifth, semantic negative controls show that, among the source categories tested, only spans of appended conflicts the scorer strictly recognized produce specific repair; these categories also differ in source content and context, so recognition is not isolated as the single factor. A second kev-family scorer (kev-4B) replicates the repair across fourteen donor groups, with the analysis window chosen on scenes disjoint from the replication (the source groups overlap).''')

# ---- related work: comparison table (P1-2) ----
rep('''To our knowledge, no prior work tests a missed-evidence failure in a security-typed scorer with cross-group transplants under dose-matched controls, or repairs such a scorer's decision by patching the decision row's own copy of the evidence span with bitwise verification that the other rows are untouched.`),''',
    '''Activation patching itself is standard; Table R1 sets out what differs here. Within the works we checked, none tests a missed-evidence failure in a security-typed scorer with cross-group transplants under per-position dose-matched controls, or repairs such a scorer's typed decision in the same forward as its conflict readout.`),
  caption(`Table R1. Closest prior work and what this study adds. The patching method is not new; the differences are in the failure studied, the gold, the controls and the endpoint.`),
  table(
    ["Work", "Setting and failure", "Intervention", "Endpoint", "Relation to this study"],
    [
      ["Abdelsalam et al. (2026)", "Code models; misleading comments override execution semantics", "Token-aligned residual-stream patching", "Code-semantics prediction", "Same method family; different failure (misleading cue, not missed appended evidence)"],
      ["Chu, Sun & Weng (2026)", "Six LLMs; detection of harmful input and refusal", "Circuit identification and weight scaling", "Refusal behaviour", "Closest detection-to-decision analogue; we identify no circuit and edit no weights"],
      ["Lepori et al. (2024; 2026)", "Contextualization timing; in-context semantics encoded but not used", "Mechanistic analyses and interventions", "Task answers", "Alternative accounts our evidence disfavors but does not exclude"],
      ["Makelov et al. (2023); Zhang & Nanda (2024); Vaidyanathan et al. (2026)", "Method critiques of patching", "-", "Interpretation limits", "Why we claim sufficiency only, use natural states with sham, permutation and dose controls, and do not identify a mechanism"],
      ["This study", "Two kev-family typed scorers; missed appended policy evidence with executable rule gold", "Whole-span natural-state transplant across source groups; SA-sham, permutation, per-position dose-matched random", "Conflict readout and typed decision in the same forward", "One constructed simulator family; no circuit, no identified mechanism, no attack claim"],
    ],
    [16, 22, 22, 15, 25]
  ),''')

# ---- 4.10 (P0) ----
rep('''h("4.10  Semantic controls: recognition, not content or decision class, carries the repair", HeadingLevel.HEADING_2),''',
    '''h("4.10  Semantic controls: among the source categories tested, only recognized appended-conflict spans repair", HeadingLevel.HEADING_2),''')
rep('''indicates that a decision-class state carried by a span is not sufficient for repair.''',
    '''suggests that, for these hosts, a decision-class state carried by a span is not by itself sufficient for repair.''')
rep('''Only spans of appended conflicts that the model itself recognized repair - the result an encoding account predicts and a content-only or class-only account does not.`),''',
    '''Among the source categories tested, only strictly recognized appended-conflict spans produce specific joint repair; missed appended conflicts, conflicts recognized through a pre-existing conflict, and duplicate-vote sources do not. These categories differ in more than recognition - source content, context and the source-host relation also vary - so the contrast does not isolate recognition as the single factor and does not show that content is irrelevant. It is consistent with an encoding account and constrains, but does not exclude, content- or context-based accounts.`),''')

# ---- 4.11 (P1-1, P1-3) ----
rep('''The severe miss rate is therefore specific to the SecJev specialist, while kev-4B still misses''',
    '''The severe miss rate is therefore not shared by kev-4B; the two scorers differ in size, training objective and data, so the cause of the difference is not isolated. kev-4B still misses''')
rep('''Table 6 reports the replication on fresh donors and hosts.`),''',
    '''Table 6 reports the replication on donor and host scenes disjoint from the scan. The scan's donor groups reappear among the replication's fourteen donor groups, so the replication is held out by scene, not by source group.`),''')
rep('''(14 donors, one per donor group, x 8 near-threshold hosts, all disjoint from the layer scan; ${KC.cells} cross-group cells).''',
    '''(14 donors, one per donor group, x 8 near-threshold hosts; scenes disjoint from the layer scan, source groups overlapping; ${KC.cells} cross-group cells sharing the 8 hosts, so counts are descriptive).''')

# ---- discussion (P0, P1-1) ----
rep('''and in both scorers spans of conflicts the model missed never repair while recognized ones do (Stage F, K-C4) - over a pure timing account, an encode-but-don't-use account, or a content- or decision-class-only account.''',
    '''and in both scorers spans of conflicts the model missed never repair while recognized ones do (Stage F, K-C4) - over a pure timing account or an encode-but-don't-use account. The source categories compared differ in content and context as well as in recognition, so a content- or context-based contribution is not excluded.''')
rep('''The donor concentration is therefore a property of the SecJev specialist's rare recognitions, not of the transplant effect.`),''',
    '''In kev-4B, then, the transplant effect is not tied to one donor. Why SecJev's repairs concentrate in one donor is not isolated: the scorers differ in size, training and recognition rate, and SecJev offers only four donors.`),''')
rep('''p(`Boundaries. The causal statements are about one 0.8B checkpoint, one simulator family and synthetic but rule-valid edits. Donors are rare (4 strict in 171 scenes) and come from three source groups that earlier rounds had already used for other scenes, and the roster is exhausted, so donor diversity cannot be increased without new construction. Cells share donors and hosts, so counts are descriptive. The locus test missed its preregistered threshold at layer 11. We make no deployment, attacker-reachability or cross-model claim,''',
    '''p(`Boundaries. The causal statements are about two kev-family checkpoints (SecJev-0.8B and kev-4B), one constructed simulator family and synthetic but rule-valid edits. SecJev donors are rare (4 strict in 171 scenes) and come from three source groups that earlier rounds had already used for other scenes, and its roster is exhausted; kev-4B's replication is held out by scene, not by source group. Cells share donors and hosts, so counts are descriptive rather than rates over independent tasks. The locus test missed its preregistered threshold at layer 11, and the semantic controls compare source categories rather than isolating recognition. We make no deployment, attacker-reachability, cross-architecture or cross-family claim,''')

# ---- limitations (P1-1, P0, P1-3) ----
rep('''p(`One 0.8B checkpoint and one simulator family; constructed rather than observed edits. Four strict donors from three source groups,''',
    '''p(`Two kev-family checkpoints and one simulator family; constructed rather than observed edits. In SecJev, four strict donors from three source groups,''')
rep('''The decision-class confound is addressed only by the Stage-F class-matched control, and the preregistered H-F1 contrast was uninformative as written.''',
    '''The decision-class confound is addressed only by the Stage-F class-matched control, and the preregistered H-F1 contrast was uninformative as written. The semantic controls compare tested source categories that differ in recognition, content and context at once; they do not isolate recognition, and witness-binding controls (reversed or mismatched witnesses, matched author, round and block) were not run. kev-4B's layer scan and replication use disjoint scenes but overlapping source groups.''')

rep('''Layers outside 7 and 11-15 are untested by patching.''',
    '''In SecJev, layers outside 7 and 11-15 are untested by patching (kev-4B was scanned at full-attention layers 3-27).''')

# ---- reproducibility ----
rep('''capture tensors (Stages C-F, K-B, K-C) remain on the authorized server with their SHA-256 lists archived.''',
    '''capture tensors (Stages C-F, K-B, K-C) are released as private repository release assets (tags a461-g2-captures-stage-c-v1 and a461-g2-captures-def-k4b-v1) with bundle and per-file SHA-256 lists.''')
rep('''the claim-to-evidence map and reproduction commands are in PAPER_CLAIM_PACKAGE_V1.`),''',
    '''the claim-to-evidence map and reproduction commands are in PAPER_CLAIM_PACKAGE_V3.`),''')

rep('''(G2_STAGE_A-E freezes, runners, self-tests, GPU runs, quota ledgers, analyses, Stage-D erratum, PAPER_CLAIM_PACKAGE_V1).''',
    '''(G2 Stage A-F and kev-4B screen, K-B and K-C freezes, runners, self-tests, GPU runs, quota ledgers, analyses, Stage-D erratum, PAPER_CLAIM_PACKAGE_V1-V3).''')

# ---- outputs ----
rep('''out = out.replace('text: "Appended-Conflict Recognition Audit (v5.2, pilot update)"', 'text: "Missed When Added, Repaired When Implanted (v8)"')''',
    '''out = out.replace('text: "Appended-Conflict Recognition Audit (v5.2, pilot update)"', 'text: "Missed When Added, Repaired When Implanted (v9)"')''')
rep('''out = out.replace('fs.writeFileSync("A461_G5_audit_paper_draft_v5_2.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v8.docx", buf)')
assert 'A461_G2_paper_draft_v8.docx' in out and '(v8)"' in out
io.open("generate_v8.js", "w", encoding="utf8", newline="\\n").write(out)
print("generate_v8.js written", len(out))''',
    '''out = out.replace('fs.writeFileSync("A461_G5_audit_paper_draft_v5_2.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v9.docx", buf)')
assert 'A461_G2_paper_draft_v9.docx' in out and '(v9)"' in out
io.open("generate_v9.js", "w", encoding="utf8", newline="\\n").write(out)
print("generate_v9.js written", len(out))''')
io.open("assemble_v9.py", "w", encoding="utf8", newline="\n").write(s)
print("assemble_v9.py written")
