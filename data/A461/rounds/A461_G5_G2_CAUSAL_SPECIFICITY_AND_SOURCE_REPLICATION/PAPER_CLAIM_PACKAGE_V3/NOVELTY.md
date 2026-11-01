# Novelty against the closest prior work (V3)

## Comparison table (added after audit `d9d3338`, P1-2; also Table R1 in manuscript v9)

Activation patching is a standard method. What differs here is the failure studied, the gold, the controls and the
endpoint.

| Work | Setting and failure | Intervention | Endpoint | Relation to this study |
|---|---|---|---|---|
| Abdelsalam et al. (2026) | Code models; misleading comments override execution semantics | Token-aligned residual-stream patching | Code-semantics prediction | Same method family; a different failure (a misleading cue, not missed appended evidence) |
| Chu, Sun & Weng (2026) | Six LLMs; detection of harmful input and refusal | Circuit identification and weight scaling | Refusal behaviour | The closest detection-to-decision analogue; we identify no circuit and edit no weights |
| Lepori et al. (2024; 2026) | Contextualization timing; in-context semantics encoded but not used | Mechanistic analyses and interventions | Task answers | Alternative accounts that our evidence disfavors but does not exclude |
| Makelov et al. (2023); Zhang & Nanda (2024); Vaidyanathan et al. (2026) | Critiques of patching methodology | — | Limits on interpretation | Why we claim sufficiency only, use natural states with sham, permutation and dose controls, and identify no mechanism |
| This study | Two kev-family typed scorers; missed appended policy evidence, with executable rule gold | Whole-span natural-state transplant across source groups; SA-sham, permutation, per-position dose-matched random | Conflict readout and typed decision in the same forward pass | One constructed simulator family; no circuit, no identified mechanism, no attack claim |

Literature was checked on 2026-10-27, and again after audit `64faaee`, which named three missing works (added below as [22]-[24]). The search covered web results for activation patching of evidence updates,
patching of contextualization and representation use, and causal studies of guardrail decisions. It extended the 16
references of v5.2, whose own novelty constraints were locked at `b11f8ca`.

## Comparison with the closest prior work

### SecJev [1]

- **What it shows:** It defines the model, the typed rows and the pointer heads.
- **What A461 adds:** SecJev never tests an evidence-addition property or any internal causal account.

### One Word Opens the Gate [2]

- **What it shows:** Attacker-controlled irrelevant text flips typed guardrails.
- **What A461 adds:** Our evidence comes from the honest system and is policy-relevant, with gold recomputed per arm. We
  repair the failure rather than exploit it.

### Tang et al., ICML 2026 [3]

- **What it shows:** Models aggregate state changes non-incrementally at query time.
- **What A461 adds:** In this scorer the query side is inert (v5). G2 places the failure at the encoding of the appended
  span and repairs it causally.

### Racing Thoughts (Lepori, Mozer, Ghandeharioun 2024) [17]

- **What it shows:** Contextualization errors come from timing: an entity is read before it is formed.
- **What A461 adds:** The readout is sensitive to the span at layers 11–12 (SecJev) and 11–15 (kev-4B), and a
  recognized span placed there is used. This argues against a pure timing account. It does not prove one is absent.

### LMs Struggle to Use Representations Learned In-Context (Lepori et al. 2026) [18]

- **What it shows:** Novel semantics are encoded but not deployed.
- **What A461 adds:** A candidate for the opposite dissociation. The missed conflict's span behaves like a duplicate
  vote and never repairs when transplanted (0/48 SecJev, 0/40 kev-4B), while a recognized span is used by both readouts.
  We do not claim to have identified the encoding failure.

### Mechanistic Lens on Semantic Conflicts (Abdelsalam et al. 2026) [19]

- **What it shows:** Residual-stream patching locates where misleading code comments override semantics.
- **What A461 adds:** A different domain and failure type (omission of new evidence, not misleading cues). We add
  cross-group transplants, dose-matched controls and a repair of the behavioural decision.

### Interpretability illusion for subspace patching (Makelov, Lange, Nanda 2023) [20]

- **What it shows:** Subspace patches can act through dormant, off-manifold pathways.
- **What A461 adds:** We transplant whole natural span states from real scenes, not subspace directions. Every main arm
  is compared against an in-distribution sham, a permutation, and a random direction of the same per-position size.

### Best practices of activation patching (Zhang & Nanda 2024) [5]

- **What it shows:** Patching conclusions depend on the corruption method and the metric.
- **What A461 adds:** We use preregistered metrics, which are counts over cells with fixed rules. Our controls include
  the dose-matched corruption that their recommendations motivate.

### From Detection to Refusal (Chu, Sun & Weng, Findings of EMNLP 2026) [22]

- **What it shows:** LLM refusal decomposes into upstream detection heads, stabilizing safety neurons and downstream
  refusal heads, across six models, and it can be steered by circuit-guided weight scaling. This is the closest
  published analogue of our conflict-readout and decision-row results.
- **What A461 adds:** Our setting differs: a typed scorer with independent question rows and executable rule gold, and
  appended evidence rather than harmful prompts. We do not claim a comparable circuit. We transplant natural activations of recognized
  *evidence* between scenes under dose and sham controls. We separate recognition from decision class (Stage F), and we
  repair a typed decision that a rule oracle defines.

### The Curse of Multiple Mediators (Vaidyanathan et al., arXiv:2606.27510, 2026) [23]

- **What it shows:** The natural-indirect-effect estimand of activation patching mixes in interaction terms with other
  mediators, so a single patch cannot uniquely localize a mechanism.
- **What A461 adds:** This is a caveat that applies to us, not a contrast. We claim sufficiency of a whole-span state at
  one layer, not the absence of other mediators. Stage-E action-row and all-row patches are reported separately, and we
  do not claim a C→A mediation chain.

### IPE: Isolating Path Effects (Brunello et al., BlackboxNLP 2025) [24]

- **What it shows:** Path-specific effects are isolated to improve circuit identification.
- **What A461 adds:** We do not identify paths or circuits. Our unit is the evidence span's residual state, and our
  contribution is the controlled cross-group transplant and its behavioural endpoint.

### The A461 v5.2 pilot (this line) [16]

- **What it shows:** One donor, two hosts and two layers. The effect was 2/4 supportive, with no flips and no
  suppression controls.
- **What A461 adds:** G2 has 4 donors × 12 hosts across 13 groups; dose-matched, sham and permutation controls in both
  directions; a layer window; a locus test; and readout and decision repair.

## Novelty delta (claimed; narrowed in V2 and again in V3)

Within the works we checked, we found none that does the following:

1. **Specific sufficiency.**
   - **The finding.** In typed scorers with executable rule oracles, the natural mid-depth state of a *recognized*
     appended policy-relevant evidence span is causally sufficient to repair the conflict readout and the decision of
     some near-threshold hosts that missed it.
   - **What "specific" means.** The effect exceeds token form, position and per-position perturbation size. It is not
     a claim about which part of the span's content carries the effect.
   - **Where it holds:
     - across source groups;
     - beyond sham, permutation and dose-matched random controls;
     - in the same forward pass;
     - in two kev-family models. On kev-4B: 14/14 donor groups, top group 13%, unrecognized sources 0/40. Counts are
       over crossed cells that share hosts.
2. **A source-category contrast.** Among the source categories tested, only strictly recognized appended-conflict
   spans produce specific repair. These categories all fail to repair:

   | Category | SecJev | kev-4B |
   |---|---|---|
   | Missed appended conflicts | 0/48 | 0/40 |
   | Class-matched duplicate-vote spans (exploratory) | 0/72 | — |
   | Conflicts recognized via a pre-existing conflict | 0/72 | — |

   The categories also differ in source content, context and source–host relation. This contrast therefore does not
   isolate recognition as the deciding factor. It is a novel set of semantic negative controls, not a single-factor
   identification.
3. **The depth window is bounded per model by preregistered layer profiles.** On kev-4B the window was chosen on
   scenes disjoint from the replication. The source groups overlap, so this is a hold-out by scene, not by group. SecJev's window is layers 11–12, ending by 13. kev-4B's is layers 11–15, inert
   from 19.

## Not claimed

- Novelty of activation patching as a method.
- That the failure is identified as an encoding failure (it is the leading candidate).
- That recognition, as opposed to source content, context or host interaction, is what decides repair.
- A rule-binding or witness-binding mechanism.
- A C→A mediation chain, or a shared mechanism between the two readouts.
- Generality beyond the kev family and this simulator family.
- Key-only or component-level mediation.
- Any attack, attacker reachability or deployment relevance.
