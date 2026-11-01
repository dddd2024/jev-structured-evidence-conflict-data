#!/usr/bin/env python3
"""Derive assemble_v8.py from assemble_v7.py: adds Stage F (semantic controls) and the kev-4B second-model stages
(screen, K-B layer scan, K-C replication); reframes title/abstract/discussion around two scorers. All new numbers are
read from numbers_v8.json (extract_numbers_v8.py). Every replaced span must occur exactly once."""
import io, re

s = io.open("assemble_v7.py", encoding="utf8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:100])
    s = s.replace(old, new)


def replace_block(name, new_body):
    """Replace the triple-quoted Python string assigned to `name` in the assembler."""
    global s
    start = s.index(f"{name} = '''")
    end = s.index("'''", start + len(f"{name} = '''")) + 3
    s = s[:start] + f"{name} = '''" + new_body + "'''" + s[end:]


rep('''const N = require("./numbers_v7.json");
const JT = N.joint;''', '''const N = require("./numbers_v8.json");
const JT = N.joint, F = N.F, K4 = N.K4, KB = N.KB, KC = N.KC;''')
rep("""/* Generate manuscript v7""", """/* Generate manuscript v8 (v7 + Stage-F semantic controls and the kev-4B second-model stages). Built from""")

# ---- title / byline / subtitle ----
rep('''text: "Missed When Added, Repaired When Implanted: Controlled Cross-Group Span Transplants Repair Missed Appended Conflicts in a Security-Typed Language-Model Scorer"''',
    '''text: "Missed When Added, Repaired When Implanted: Recognized-Evidence Span Transplants Repair Missed Appended Conflicts Across Source Groups in Two Typed Language-Model Scorers"''')
rep('''text: "Anonymous draft (v7; v6 revised after an independent paper-level audit: claims narrowed, joint endpoint added)"''',
    '''text: "Anonymous draft (v8; v7 extended with semantic negative controls and a second-model replication)"''')
rep('''native FP32 forward passes across ten GPU stages''', '''native FP32 forward passes across fourteen GPU stages and two models''')

# ---- abstract ----
replace_block("ABSTRACT", '''  h("Abstract", HeadingLevel.HEADING_1),
  p(`When new policy-relevant evidence arrives in a security decision context, does a trained typed scorer encode it - and if not, can its decision be repaired from the inside? We study two kev-family typed scorers on structured consensus scenes with executable rule oracles: SecJev-0.8B, a security specialist, and kev-4B, a general typed-decision model never trained on these scenes. Appending one valid equivocation vote - an edit that lawfully moves the gold to rejection - leaves SecJev's conflict readout false in ${pct(A.missed_rate_new)}% of ${A.scenes} preregistered scenes (${A.strict} strict recognitions; ${D.D1["31"].strict + D.D1["34"].strict} more in ${D.D1["31"].scenes + D.D1["34"].scenes}), and kev-4B's in ${pct(K4.missed_rate_new)}% of the same scenes (${K4.strict} strict recognitions in ${K4.groups} source groups, no false alarms on duplicate-vote controls). Across eleven preregistered, CPU-frozen GPU stages (${N.ledger_total_g2.toLocaleString("en-US")} native forwards) we transplant natural span activations between scenes from different source groups. In SecJev, a recognized donor's appended-span state at layer 11 raises a host's conflict margin beyond its own duplicate-vote state, a permutation and a random direction of identical per-position size in ${C.H1.supportive}/${C.H1.cells} cells; transplant sensitivity falls by layer ${C.H2_boundary}; implanted into a near-threshold host's own missed-conflict span it repairs the conflict readout (${D11.specific_flip}/${D11.cells} specific cells) and, placed in the certificate-action row alone, flips the decision to reject_conflict (${E11a.specific_reject}/${E11a.cells}); spans of conflicts the model missed never repair (${F.joint.fff_new}/${F.cells.fff_new}), nor do spans from scenes read as conflict but carrying a duplicate vote (${F.joint.ttt_sa}/${F.cells.ttt_sa}). SecJev's repairs, however, rest largely on one donor. kev-4B removes that ceiling: a layer scan on one set of scenes selects layer ${KB.window} by a preregistered rule, and on disjoint donors and hosts the recognized span beats dose-matched random in ${KC.share_dose}% of ${KC.cells} cross-group cells (majority in ${KC.groups_majority}/${KC.groups} donor groups) and SA-sham in ${KC.share_sham}%, jointly repairs readout and decision in ${KC.spec_joint}/${KC.cells} cells with neither control doing so, drawn from all ${KC.spec_joint_groups} donor groups (largest share ${KC.top_share}%), while unrecognized-conflict spans repair ${KC.unrec.JOINT}/${KC.unrec.cells}. The supported claim is interventional: natural span states of recognized appended conflicts are causally sufficient, beyond sham, permutation and dose-matched controls and across source groups and two scorers, to produce the rule-mandated readout and decision; a missing conflict encoding at the appended span is the explanation most consistent with the evidence but is not uniquely identified, and the scorers, scenes and edits come from one constructed simulator family.`),''')

# ---- intro contributions ----
rep('''Fourth, implanting a recognized span repairs the conflict readout and, placed in the decision row itself, the certificate action - the behavioral endpoint the scorer exists to produce - in a donor-dependent subset of near-threshold scenes.`),''',
    '''Fourth, implanting a recognized span repairs the conflict readout and, placed in the decision row itself, the certificate action - the behavioral endpoint the scorer exists to produce. Fifth, semantic negative controls separate recognition from content and from decision class, and a second, larger scorer (kev-4B) replicates the repair across fourteen donor groups with the analysis window chosen on disjoint scenes.`),''')

# ---- method 3.5 ----
rep('''so all counts are descriptive decision rules rather than p-values.`),''',
    '''so all counts are descriptive decision rules rather than p-values.`),
  h("3.5  Semantic controls and the second scorer", HeadingLevel.HEADING_2),
  p(`Stage F (SecJev, layer 11, every question row patched into the 8 near-threshold hosts; ${F.physical} forwards) adds spans that dissociate recognition, content and decision class: TTT scenes are read as conflicts on every arm, so their SA span is a duplicate vote inside a scene the model reads as conflict-and-reject (class-matched, content-mismatched), and their new span is conflict content recognized via a pre-existing conflict; FFF scenes contribute conflict spans the model did not recognize. TTT and FFF sources come only from groups holding no host or donor (${F.n_ttt_groups} and ${F.n_fff_groups} groups). The second scorer is kev-4B (Qwen3.5-4B-Base with a kev adapter, 32 layers, full attention every fourth layer), a general typed-decision model not trained on these scenes; its tokenizer is byte-identical and its compatible source reproduces all 372 frozen Stage-A token hashes, so every frozen input carries over unchanged. kev-4B was screened on the frozen Stage-A manifest (${K4.physical} forwards). Stage K-B scanned full-attention layers 3-27 with 6 donors and 4 hosts (${KB.physical} forwards) and fixed the replication layer by a preregistered rule (largest median main-minus-dose gap over cross-group cells). Stage K-C then used 14 donors (one per donor group) and 8 near-threshold hosts, all disjoint from the scan, with main, SA-sham and dose-matched random arms plus unrecognized-conflict sources (${KC.physical} forwards), under four preregistered criteria (K-C1 dose specificity, K-C2 sham specificity, K-C3 joint repair from >= 7 donor groups with no group above 30%, K-C4 recognition). Only cross-group cells enter the counts.`),''')

# ---- results 4.10 and 4.11 after Table 5 ----
rep('''    [30, 14, 14, 16, 26]
  ),''', '''    [30, 14, 14, 16, 26]
  ),

  h("4.10  Semantic controls: recognition, not content or decision class, carries the repair", HeadingLevel.HEADING_2),
  p(`In Stage F the recognized donor spans again repair readout and decision jointly in ${F.joint.donor_new}/${F.cells.donor_new} cells (bitwise replications of Stage E), while every other source repairs none: conflict spans the model missed ${F.joint.fff_new}/${F.cells.fff_new}, class-matched duplicate-vote spans from scenes read as conflict-and-reject ${F.joint.ttt_sa}/${F.cells.ttt_sa}, conflict spans from scenes recognized through a pre-existing conflict ${F.joint.ttt_new}/${F.cells.ttt_new}, and the donors' own duplicate-vote spans ${F.joint.donor_sa}/${F.cells.donor_sa}. The preregistered recognition hypothesis (H-F2) is met. The preregistered class-prototype contrast (H-F1: TTT conflict vs TTT duplicate spans) is not met because neither repairs, so it is uninformative as written; the exploratory comparison of recognized donor spans with class-matched spans (${F.joint.donor_new}/${F.cells.donor_new} vs ${F.joint.ttt_sa}/${F.cells.ttt_sa}) indicates that a decision-class state carried by a span is not sufficient for repair. H-F3 (donor diversity from TTT scenes) is not met. Only spans of appended conflicts that the model itself recognized repair - the result an encoding account predicts and a content-only or class-only account does not.`),

  h("4.11  A second scorer: kev-4B replicates the repair across fourteen donor groups", HeadingLevel.HEADING_2),
  p(`kev-4B recognizes appended conflicts far more often than SecJev on the same frozen scenes (conflict readout true on ${pct(100 * K4.C_rate.new)}% of new arms versus ${pct(100 * A.C_rate.new)}%; ${K4.strict} versus ${A.strict} strict donors; median margin change ${s(K4.median_dM_new_old)} versus ${s(A.median_dM_new_old)}) and never reads a duplicate vote as a conflict (${pct(100 * K4.C_rate.SA)}% on SA arms); ${K4.secjev_missed_now_donor} scenes that SecJev misses are kev-4B donors. The severe miss rate is therefore specific to the SecJev specialist, while kev-4B still misses ${pct(K4.missed_rate_new)}% of appended conflicts. On kev-4B the layer scan places the transplant-specific window at layers 11-15 (median main-minus-dose gap ${["3", "7", "11", "15", "19"].map(l => l + ": " + s(KB.profile[l].gap)).join(", ")}): at layers 3 and 7 the donor span lowers the margin, and from layer 19 on transplants are inert; the rule selects layer ${KB.window}. Table 6 reports the replication on fresh donors and hosts.`),
  caption(`Table 6. kev-4B replication at layer ${KC.layer} (14 donors, one per donor group, x 8 near-threshold hosts, all disjoint from the layer scan; ${KC.cells} cross-group cells). Joint = conflict readout true and decision reject_conflict in the same forward.`),
  table(
    ["Preregistered criterion", "Rule", "Result", "Met"],
    [
      ["K-C1 dose specificity", ">= 75% cells main > dose; majority in >= 10/14 groups", `${KC.share_dose}%; ${KC.groups_majority}/14 groups`, KC.K1 ? "yes" : "no"],
      ["K-C2 sham specificity", ">= 75% cells main > SA-sham", `${KC.share_sham}%`, KC.K2 ? "yes" : "no"],
      ["K-C3 joint generality", "specific joint from >= 7 groups; top group <= 30%", `${KC.spec_joint}/${KC.cells} from ${KC.spec_joint_groups} groups; top ${KC.top_share}%`, KC.K3 ? "yes" : "no"],
      ["K-C4 recognition", "unrecognized joint rate <= 1/4 of main", `${KC.unrec.JOINT}/${KC.unrec.cells} vs ${KC.joint_rate_main}%`, KC.K4 ? "yes" : "no"],
    ],
    [24, 34, 30, 12]
  ),
  note(`Flips in cross-group cells (C / R / joint): main ${KC.flips.main.C} / ${KC.flips.main.R} / ${KC.flips.main.JOINT}; SA-sham ${KC.flips.sasham.C} / ${KC.flips.sasham.R} / ${KC.flips.sasham.JOINT}; dose-matched random ${KC.flips.doserand.C} / ${KC.flips.doserand.R} / ${KC.flips.doserand.JOINT}. Median dM: main ${s(KC.medians.main.dM)}, SA-sham ${s(KC.medians.sasham.dM)}, dose ${s(KC.medians.doserand.dM)}. Leave-one-donor-group-out: ${KC.logo_min}-${KC.logo_max} specific joint repairs from at least ${KC.logo_min_groups} groups for every removal. ${KC.hosts_repaired}/${KC.hosts} hosts repaired. kev-4B hosts sit close to threshold (small margins, temperature 2.41), so flips are cheap; the dose and sham contrasts, not flip counts, carry K-C1 and K-C2. Captures replay the kev-4B screen bitwise; kev-4B loaded in FP32 (${K4.load_gb} GB).`),''')

# ---- discussion updates ----
rep('''On the locus, the evidence favors an encoding account - a missed conflict's span substitutes like a duplicate vote, missed scenes project weakly onto the conflict direction, and a recognized span placed at layers 11-12 is used - over a pure timing account or an encode-but-don't-use account.''',
    '''On the locus, the evidence favors an encoding account - a missed conflict's span substitutes like a duplicate vote, missed scenes project weakly onto the conflict direction, a recognized span placed at layers 11-12 is used, and in both scorers spans of conflicts the model missed never repair while recognized ones do (Stage F, K-C4) - over a pure timing account, an encode-but-don't-use account, or a content- or decision-class-only account.''')
rep('''The claim is therefore that an implanted recognized encoding is sufficient to repair the decision in a cross-group subset of near-threshold scenes, with sufficiency varying strongly between donors - not that every recognized encoding repairs every scene.`),''',
    '''In SecJev, then, sufficiency varies strongly between donors. kev-4B answers whether that dependence is intrinsic: with a window chosen on disjoint scenes, recognized spans from all fourteen donor groups repair, no group supplies more than ${KC.top_share}% of the specific joint repairs, and removing any group leaves at least ${KC.logo_min}. The donor concentration is therefore a property of the SecJev specialist's rare recognitions, not of the transplant effect.`),''')

# ---- limitations ----
rep('''Joint repair of readout and decision in the same forward is ${JT.L11_main.JOINT}/32 and almost entirely from one donor (${JT.L11_main_lodo["run-140:90dbf6d6"]}/24 without it). A decision-class confound is not yet excluded: a donor span may carry a reject-associated state rather than the specific author-round-block conflict relation. Cross-model replication, observed (non-constructed) evidence streams and deployment relevance remain open.`),''',
    '''In SecJev, joint repair is ${JT.L11_main.JOINT}/32 and almost entirely from one donor (${JT.L11_main_lodo["run-140:90dbf6d6"]}/24 without it); the cross-group generality claim rests on kev-4B. The decision-class confound is addressed only by the Stage-F class-matched control, and the preregistered H-F1 contrast was uninformative as written. Both scorers come from the kev family and share one constructed simulator family, so cross-family and observed-evidence validity remain open, as does deployment relevance. kev-4B margins are small, so its flips are less informative than its contrasts.`),''')

# ---- references unchanged; reproducibility addition ----
rep('''the claim-to-evidence map and reproduction commands are in PAPER_CLAIM_PACKAGE_V1.`),''',
    '''the claim-to-evidence map and reproduction commands are in PAPER_CLAIM_PACKAGE_V1.`),
  p(`v8 additions: Stage F design/runner 5a7067f8 3c31764, run 6a19924; kev-4B screen runner f118ea59 dbe2f0e, run fd4bf13; K-B runner 954a131b 66fa292, run and K-C freeze 3a6173f (K-C analysis script committed earlier, 84bc6f4); K-C run 5ef7a16 (standing user GPU authorization recorded in each admission). Physical ledger including these stages: SecJev G2 ${N.ledger_total_secjev_g2.toLocaleString("en-US")}, kev-4B ${N.ledger_total_k4b.toLocaleString("en-US")} (reservations equal to receipts in every stage).`),''')

# ---- stale counts from v6/v5 text ----
rep('''Across eleven preregistered, CPU-frozen GPU stages''', '''Across nine preregistered, CPU-frozen GPU stages''')
rep('''This version adds the causal program that the v5 pilot could only motivate. Five GPU stages, each designed, manifested and given a frozen analysis script before any forward pass, make four contributions.''',
    '''This version adds the causal program that the v5 pilot could only motivate. Nine GPU stages on two scorers, each designed, manifested and given a frozen analysis script before any forward pass, make five contributions.''')
rep('''G2 physical ledger (reservations, equal to every receipt): ${["A", "B", "C", "D", "E"].map(k => k + " " + N.ledger[k].reserved).join(", ")} = ${N.ledger_total_g2.toLocaleString("en-US")}''',
    '''G2 physical ledger (reservations, equal to every receipt): ${["A", "B", "C", "D", "E", "F", "K4", "KB", "KC"].map(k => k + " " + N.ledger[k].reserved).join(", ")} = ${N.ledger_total_g2.toLocaleString("en-US")}''')
rep('''capture tensors (Stages C-E) remain on the authorized server''', '''capture tensors (Stages C-F, K-B, K-C) remain on the authorized server''')
rep('''All numbers in Sections 3.4-4.9 are generated from the archived analysis JSONs by extract_numbers_v6.py;''',
    '''All numbers in Sections 3.4-4.11 are generated from the archived analysis JSONs, raw logits and ledgers by extract_numbers_v8.py;''')
rep('''out = out.replace('text: "Appended-Conflict Recognition Audit (v5.2, pilot update)"',''',
    '''out = out.replace("We report both instruments applied to one scorer across five preregistered GPU stages", "We report both instruments applied across five preregistered GPU stages in the earlier rounds (Sections 3.1-4.4), followed by nine preregistered G2 stages on two scorers (Sections 3.4-4.11)")
assert "followed by nine preregistered G2 stages" in out
out = out.replace('text: "Appended-Conflict Recognition Audit (v5.2, pilot update)"',''')

rep('''We therefore present encoding failure as the leading candidate explanation, not an identified mechanism, and treat path-isolating analyses and semantically matched negative controls (a span from a scene the model reads as a conflict but whose own content is a duplicate vote; a conflict span the model does not recognize) as the tests that could decide it.`),''',
    '''We therefore present encoding failure as the leading candidate explanation, not an identified mechanism. The semantically matched controls of Stage F and K-C4 (a span from a scene the model reads as a conflict but whose own content is a duplicate vote; conflict spans the model did not recognize) favor it; path-isolating analyses remain the test that could decide it.`),''')

# ---- outputs ----
rep('''out = out.replace('text: "Appended-Conflict Recognition Audit (v5.2, pilot update)"', 'text: "Missed When Added, Repaired When Implanted (v7)"')''',
    '''out = out.replace('text: "Appended-Conflict Recognition Audit (v5.2, pilot update)"', 'text: "Missed When Added, Repaired When Implanted (v8)"')''')
rep('''out = out.replace('fs.writeFileSync("A461_G5_audit_paper_draft_v5_2.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v7.docx", buf)')
assert 'A461_G2_paper_draft_v7.docx' in out and '(v7)"' in out
io.open("generate_v7.js", "w", encoding="utf8", newline="\\n").write(out)
print("generate_v7.js written", len(out))''',
    '''out = out.replace('fs.writeFileSync("A461_G5_audit_paper_draft_v5_2.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v8.docx", buf)')
assert 'A461_G2_paper_draft_v8.docx' in out and '(v8)"' in out
io.open("generate_v8.js", "w", encoding="utf8", newline="\\n").write(out)
print("generate_v8.js written", len(out))''')
io.open("assemble_v8.py", "w", encoding="utf8", newline="\n").write(s)
print("assemble_v8.py written")
