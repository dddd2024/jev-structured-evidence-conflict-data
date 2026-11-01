# Novelty against the closest prior work

Literature was checked on 2026-10-27. The search covered web results for activation patching of evidence updates,
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
- **What A461 adds:** The readout does consult the span at layers 11–12. A recognized encoding placed there is used.
  The missed span is not encoded as a conflict, so this is not a timing failure.

### LMs Struggle to Use Representations Learned In-Context (Lepori et al. 2026) [18]

- **What it shows:** Novel semantics are encoded but not deployed.
- **What A461 adds:** The opposite dissociation. The missed conflict is not encoded as a conflict (it substitutes for a
  duplicate vote), while a recognized encoding is deployed by two independent readers.

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

### The A461 v5.2 pilot (this line) [16]

- **What it shows:** One donor, two hosts and two layers. The effect was 2/4 supportive, with no flips and no
  suppression controls.
- **What A461 adds:** G2 has 4 donors × 12 hosts across 13 groups; dose-matched, sham and permutation controls in both
  directions; a layer window; a locus test; and readout and decision repair.

## Novelty delta (claimed)

To our knowledge, no prior work does any of the following:

1. Shows, in a security-typed scorer with executable rule oracles, that the failure to act on newly appended
   policy-relevant evidence is an encoding failure at the evidence span. The evidence is cross-group transplants under
   dose-matched controls, plus the equivalence of the missed span to a non-conflict span.
2. Repairs the scorer's actual decision by implanting a recognized evidence encoding into the decision row's own copy
   of the span, while verifying bitwise that every other question row is untouched.
3. Bounds where in depth a hybrid (DeltaNet and attention) backbone reads such evidence, at layers 11–12 with dependence
   ending by layer 13, using preregistered layer profiles.

## Not claimed

- Novelty of activation patching as a method.
- Generality beyond this model and simulator family.
- Key-only or component-level mediation.
- Any attack, attacker reachability or deployment relevance.
