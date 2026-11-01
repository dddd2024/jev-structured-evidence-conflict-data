#!/usr/bin/env python3
"""Derive assemble_v7.py from assemble_v6.py: narrowed claims per paper audit 64faaee (P0-1, P0-2, P1-2) and the
P2-1 input-path fix. Every replaced span must occur exactly once."""
import io

s = io.open("assemble_v6.py", encoding="utf8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:100])
    s = s.replace(old, new)


# ---- P2-1: accept the packaged input name as well ----
rep('''v5 = io.open("generate_v5.js", encoding="utf8").read().split("\\n")''',
    '''import os
_v5 = "generate_v5.js" if os.path.exists("generate_v5.js") else "generate_v5_input.js"   # package ships the _input name
v5 = io.open(_v5, encoding="utf8").read().split("\\n")''')
rep('''HEAD = \'\'\'/* Generate manuscript v6 (v5.2 + G2 causal-specificity, failure-locus and repair results). All G2 numbers come from
   numbers_v6.json, produced by extract_numbers_v6.py from the archived analysis JSONs and receipts. */\'\'\'''',
    '''HEAD = \'\'\'/* Generate manuscript v7 (v6 narrowed per paper audit 64faaee: candidate-explanation wording, joint C-and-A repair,
   multi-mediator and detection-to-refusal prior work). All G2 numbers come from numbers_v7.json, produced by
   extract_numbers_v7.py from the archived analysis JSONs, raw logits and receipts. */\'\'\'''')
rep('''const N = require("./numbers_v6.json");''', '''const N = require("./numbers_v7.json");
const JT = N.joint;''')

# ---- title / byline ----
rep('''text: "Missed When Added, Repaired When Implanted: Specific Cross-Group Causal Evidence for an Encoding Failure of Appended Conflicts in a Security-Typed Language-Model Scorer"''',
    '''text: "Missed When Added, Repaired When Implanted: Controlled Cross-Group Span Transplants Repair Missed Appended Conflicts in a Security-Typed Language-Model Scorer"''')
rep('''text: "Anonymous draft (v6; the v5.2 audit extended with five preregistered G2 causal stages)"''',
    '''text: "Anonymous draft (v7; v6 revised after an independent paper-level audit: claims narrowed, joint endpoint added)"''')

# ---- abstract: second half rewritten ----
rep('''(iii) Locus: replacing a donor's recognized span with a host's missed-conflict span suppresses recognition as much as the host's non-conflict duplicate span (the main arm is stronger in only ${C.H1b.main_beats_sasham}/16 cells), while dose-matched noise barely moves it; a preregistered projection test separates missed from recognized scenes with AUC ${C.H3.auc_L11.toFixed(2)} at layer 11 (short of its 0.9 threshold; ${C.H3.auc_L12.toFixed(2)} at layer 12). (iv) Repair: in ${D.n_hosts} near-threshold hosts from ${D.n_host_groups} further groups, implanting a recognized span into the host's own missed-conflict span flips the conflict readout in ${D11.specific_flip}/${D11.cells} cells with neither control flipping, across all ${D11.host_groups} host groups; implanting it into the certificate-action row alone flips the decision to reject_conflict in ${E11a.specific_reject}/${E11a.cells} cells (controls: ${E11a.rejects.sasham} and ${E11a.rejects.doserand} rejections) across all ${E11a.donor_groups} donor groups and ${E11a.host_groups} of ${D.n_host_groups} host groups, with every other question row bitwise unchanged. We read this as specific, cross-group causal evidence that the scorer's failure on appended conflicts is an encoding failure at the appended span by mid-depth that is repairable by implanting a recognized encoding, and we state its ceilings: one donor (${TOPG}) contributes ${RB.top_donor_E_rejects} of the ${E11a.specific_reject} decision repairs (without it, ${RB.E_without_top.specific}/${RB.E_without_top.cells} cells across two donor and two host groups remain); four donors from three previously used source groups; one model; one simulator family; constructed edits; non-independent cells; one missed preregistered threshold; and one documented design erratum.`),''',
    '''(iii) Suppression: replacing a donor's recognized span with a host's missed-conflict span lowers recognition about as much as the host's non-conflict duplicate span (the main arm is stronger in only ${C.H1b.main_beats_sasham}/16 cells), while dose-matched noise barely moves it; a preregistered projection test did not meet its layer-11 threshold (AUC ${C.H3.auc_L11.toFixed(2)} < 0.9). (iv) Repair: in ${D.n_hosts} near-threshold hosts from ${D.n_host_groups} further groups, implanting a recognized span into the host's own missed-conflict span flips the conflict readout in ${D11.specific_flip}/${D11.cells} cells with neither control flipping; implanted into the certificate-action row alone it flips the decision to reject_conflict in ${E11a.specific_reject}/${E11a.cells} cells (controls: ${E11a.rejects.sasham} and ${E11a.rejects.doserand}), with every other question row bitwise unchanged. When every row is patched, the readout and the decision are repaired together in ${JT.L11_main.JOINT}/${JT.L11_main.cells} cells (controls 0), ${JT.L11_main.by_donor_group["run-140"]} of them from a single donor. The supported claim is therefore interventional and bounded: natural span activations of recognized scenes are causally sufficient, beyond sham, permutation and dose-matched controls, to raise the conflict readout across groups and - for a subset of near-threshold scenes and strongly donor-dependent - to produce the rule-mandated decision. An encoding failure at the appended span is the explanation most consistent with the evidence, but it is not uniquely identified: whole-span transplants do not separate encoding from downstream use or multi-mediator interactions. Further ceilings: four donors from three previously used source groups, one model, one simulator family, constructed edits, non-independent cells and one documented design erratum.`),''')

rep('''(ii) Window: the span dependence is strong at layer 11, weaker at layer 12 and absent by layer ${C.H2_boundary} in both directions.''',
    '''(ii) Window: outputs are sensitive to transplants at the span positions at layer 11, less at layer 12, and barely from layer ${C.H2_boundary} on, in both directions.''')

# ---- intro contributions: narrowed third/fourth ----
rep('''Third, layer profiles, suppression controls and a capture-based projection test locate the failure at the encoding of the appended span, not in either readout. Fourth, implanting a recognized encoding repairs both the conflict readout and, when placed in the decision row itself, the certificate action - the behavioral endpoint the scorer exists to produce.''',
    '''Third, layer profiles, suppression controls and a capture-based projection test constrain where the failure can lie; they favor, but do not uniquely identify, a failure to encode the appended conflict at its span. Fourth, implanting a recognized span repairs the conflict readout and, placed in the decision row itself, the certificate action - the behavioral endpoint the scorer exists to produce - in a donor-dependent subset of near-threshold scenes.''')

# ---- related work: replace G2 paragraph ----
start = s.index("RELATED_ADD = '''")
end = s.index("'''", start + len("RELATED_ADD = '''")) + 3
s = s[:start] + '''RELATED_ADD = \'\'\'  p(`Several recent lines bear directly on the G2 results. Lepori, Mozer and Ghandeharioun (2024) attribute contextualization errors to timing; Lepori et al. (2026) find novel in-context semantics encoded but not deployed; Abdelsalam et al. (2026) localize, by residual-stream patching, where misleading code comments override execution semantics. Chu, Sun and Weng (2026) decompose LLM refusal into upstream detection heads, stabilizing safety neurons and downstream refusal heads across six models and steer it by circuit-guided weight scaling; our setting differs (a typed scorer with independent question rows and executable rule gold, appended evidence rather than harmful prompts), but their detection-to-decision decomposition is the closest published analogue of our conflict-readout and decision-row results, and we do not claim a comparable circuit. Methodologically, activation patching can create illusory localization through dormant or off-manifold pathways (Makelov, Lange and Nanda, 2023), its conclusions depend on corruption and metric choices (Zhang and Nanda, 2024), and its natural-indirect-effect estimand mixes in interaction terms with other mediators (Vaidyanathan et al., 2026), so a single transplant cannot uniquely localize a mechanism; path-isolating methods such as IPE (Brunello et al., 2025) are the natural next step and are not attempted here. We therefore transplant whole residual span states from natural forward passes of real scenes, compare every main arm with an in-distribution sham, a permutation and a random direction matched to its per-position perturbation size, and state mechanism language only as a candidate explanation. To our knowledge, no prior work tests a missed-evidence failure in a security-typed scorer with cross-group transplants under dose-matched controls, or repairs such a scorer's decision by patching the decision row's own copy of the evidence span with bitwise verification that the other rows are untouched.`),\'\'\'''' + s[end:]

# ---- 4.7 window wording ----
rep('''h("4.7  Window: the readout stops depending on the span between layers 12 and 13", HeadingLevel.HEADING_2),''',
    '''h("4.7  Window: sensitivity to the span falls between layers 12 and 13", HeadingLevel.HEADING_2),''')
rep('''Within this backbone, then, the appended span is read out in a narrow mid-depth window: at layer 7 any large perturbation disrupts, and by layer 13 the readout no longer consults the span positions.`),''',
    '''Within this backbone, then, outputs are sensitive to transplants at the appended-span positions in a narrow mid-depth window: at layer 7 any large perturbation disrupts, and from layer 13 on, replacing the span outputs barely moves the readout. This is a statement about sensitivity at this patch site; it does not show that later layers ignore information derived from the span, which may already have been routed to other positions.`),''')

# ---- 4.8 locus wording ----
rep('''h("4.8  Locus: a missed conflict is encoded like a duplicate vote", HeadingLevel.HEADING_2),''',
    '''h("4.8  Locus: a missed conflict's span substitutes like a duplicate vote", HeadingLevel.HEADING_2),''')
rep('''Read together, the host's span for an appended conflict acts like its span for a harmless duplicate vote.''',
    '''Read together, under this intervention the host's span for an appended conflict substitutes like its span for a harmless duplicate vote; near-equality of two transplant effects is an observation about substitution, not direct evidence of how the host encodes the conflict in its own forward pass.''')

# ---- 4.9: joint table after the erratum paragraph ----
rep('''Repairs are unevenly distributed across donors (${TOPG}: ${RB.top_donor_E_rejects} of ${E11a.specific_reject}); Section 5 reports an exploratory leave-one-donor-out check.`),''',
    '''Repairs are unevenly distributed across donors (${TOPG}: ${RB.top_donor_E_rejects} of ${E11a.specific_reject}); Section 5 reports an exploratory leave-one-donor-out check.`),
  p(`Row-wise sufficiency is not the same as a coherent typed decision. Table 5 reports, for the all-row setting, how often the conflict readout and the decision are repaired together in the same forward pass. The joint repair is specific - neither control produces a single joint repair - but it is concentrated: ${JT.L11_main.by_donor_group["run-140"]} of the ${JT.L11_main.JOINT} joint repairs come from the ${TOPG} donor and ${JT.L11_main.by_donor_group["run-338"] || 0} from run-338, while the two run-212 donors produce none; removing the ${TOPG} donor leaves ${JT.L11_main_lodo["run-140:90dbf6d6"]}/24 (exploratory). Because the action row can be repaired with the conflict row untouched (action-only setting), these results show that each row is separately sensitive to the implanted span; they do not establish that the decision is mediated by the conflict readout, nor a single shared mechanism.`),
  caption("Table 5. Joint repair in the same forward (Stage E, all question rows patched, 4 donors x 8 hosts). C = conflict readout true; R = decision reject_conflict."),
  table(
    ["Layer, arm", "C repaired", "R repaired", "C and R together", "Joint by donor group"],
    [
      ["L11, main (donor recognized span)", `${JT.L11_main.C}/32`, `${JT.L11_main.R}/32`, `${JT.L11_main.JOINT}/32`, Object.entries(JT.L11_main.by_donor_group).map(([k, v]) => k + " " + v).join(", ")],
      ["L11, SA-sham", `${JT.L11_sasham.C}/32`, `${JT.L11_sasham.R}/32`, `${JT.L11_sasham.JOINT}/32`, "-"],
      ["L11, dose-matched random", `${JT.L11_doserand.C}/32`, `${JT.L11_doserand.R}/32`, `${JT.L11_doserand.JOINT}/32`, "-"],
      ["L12, main", `${JT.L12_main.C}/32`, `${JT.L12_main.R}/32`, `${JT.L12_main.JOINT}/32`, "-"],
    ],
    [30, 14, 14, 16, 26]
  ),''')

# ---- discussion paragraph 1 rewritten ----
start = s.index("  p(`The v5 account - a key-side localization")
end = s.index("`),", start) + 3
s = s[:start] + '''  p(`The v5 account - a key-side localization plus a one-donor signed sensitivity - left open whether the appended-span representation carries conflict information specifically, where the failure lies, and whether it matters for the decision. G2 answers the first and third within its ceilings and narrows the second. The recognized span carries content-specific information: across three donor groups and four host groups it outperforms its own duplicate-vote span, its permutation, and a random perturbation of exactly its size. It matters for the decision: implanted into the decision row's own copy of the span, it produces the rule-mandated rejection in a donor-dependent subset of near-threshold scenes without touching the conflict row. On the locus, the evidence favors an encoding account - a missed conflict's span substitutes like a duplicate vote, missed scenes project weakly onto the conflict direction, and a recognized span placed at layers 11-12 is used - over a pure timing account or an encode-but-don't-use account. But whole-span transplants replace many tokens of high-dimensional state at once; they cannot separate a missing conflict feature from downstream decoding, routing or context interaction, and a transplant's effect also contains interactions with other mediators (Vaidyanathan et al., 2026). We therefore present encoding failure as the leading candidate explanation, not an identified mechanism, and treat path-isolating analyses and semantically matched negative controls (a span from a scene the model reads as a conflict but whose own content is a duplicate vote; a conflict span the model does not recognize) as the tests that could decide it.`),''' + s[end:]
rep('''The coherent reading is an encoding failure''', '''The coherent reading is an encoding failure''') if False else None

# ---- limitations additions ----
rep('''Cross-model replication, observed (non-constructed) evidence streams and deployment relevance remain open.`),''',
    '''Joint repair of readout and decision in the same forward is ${JT.L11_main.JOINT}/32 and almost entirely from one donor (${JT.L11_main_lodo["run-140:90dbf6d6"]}/24 without it). A decision-class confound is not yet excluded: a donor span may carry a reject-associated state rather than the specific author-round-block conflict relation. Cross-model replication, observed (non-constructed) evidence streams and deployment relevance remain open.`),''')

# ---- references ----
rep('''  ref("[21] A461-G5-G2 evidence chain''', '''  ref("[22] Chu, K.-L., Sun, C.-E., Weng, T.-W. From Detection to Refusal: Safer LLMs via Circuit-Guided Weight Scaling. Findings of EMNLP 2026, pp. 34657-34680."),
  ref("[23] Vaidyanathan, S., Arbour, D., Mueller, A., Niekum, S., Jensen, D. The Curse of Multiple Mediators: Hidden Interaction Effects in Activation Patching. arXiv:2606.27510, 2026."),
  ref("[24] Brunello, N., Cerutti, A., Sassella, A., Carman, M. J. IPE: Isolating Path Effects for Improving Latent Circuit Identification. BlackboxNLP 2025, pp. 528-536."),
  ref("[21] A461-G5-G2 evidence chain''')

# ---- output names ----
rep('''out = out.replace('text: "Appended-Conflict Recognition Audit (v5.2, pilot update)"', 'text: "Missed When Added, Repaired When Implanted (v6)"')''',
    '''out = out.replace('text: "Appended-Conflict Recognition Audit (v5.2, pilot update)"', 'text: "Missed When Added, Repaired When Implanted (v7)"')''')
rep('''out = out.replace('fs.writeFileSync("A461_G5_audit_paper_draft_v5_2.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v6.docx", buf)')
assert 'A461_G2_paper_draft_v6.docx' in out and '(v6)"' in out
io.open("generate_v6.js", "w", encoding="utf8", newline="\\n").write(out)
print("generate_v6.js written", len(out))''',
    '''out = out.replace('fs.writeFileSync("A461_G5_audit_paper_draft_v5_2.docx", buf)', 'fs.writeFileSync("A461_G2_paper_draft_v7.docx", buf)')
assert 'A461_G2_paper_draft_v7.docx' in out and '(v7)"' in out
io.open("generate_v7.js", "w", encoding="utf8", newline="\\n").write(out)
print("generate_v7.js written", len(out))''')
io.open("assemble_v7.py", "w", encoding="utf8", newline="\n").write(s)
print("assemble_v7.py written")
