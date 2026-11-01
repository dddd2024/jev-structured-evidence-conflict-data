# Novelty against the closest prior work (V5)

**Status after audit `02a2b73`: `NOVELTY_NOT_YET_PASS`.** The mechanism stages are a task-specific instantiation of known
phenomenon classes. The strict competition matrix below lists what is new and what is not.

## Competition matrix (V5)

| Prior work | What it already shows | What this study has that it does not | What this study does not add |
|---|---|---|---|
| Lepori et al., ACL 2026 | In-context representations encoded but not deployed | A security-typed scorer with executable rule gold, where the missed decision is a safety error | The phenomenon class itself. Our separability is arm-confounded and our steering null is decision-token only |
| Chu et al., Findings EMNLP 2026 | A detection → refusal circuit across 6 models, steered by weight scaling | Source-matched round-only control (M1), and a false-veto check on four repair families (M17) | Any circuit identification; any cross-model mechanism; any safety improvement |
| Ma et al., EMNLP 2026 (spatial lexical bias) | Correct relation readable but the decision wrong; patch and neuron localization | The same pattern on a typed-decision security task, with held-out source groups | A localized neuron or circuit; replication across tasks |
| Vaidyanathan et al., arXiv:2606.27510 | Patching estimands mix mediator interactions | We report the M8 non-additivity as an instance | A resolution of the multi-mediator problem |
| Zhang & Nanda 2024; Makelov et al. 2023 | Patching localization depends on metric and corruption; illusions | Preregistered metrics with source-matched controls | New methodology |

**The smallest delta we still claim.** On one constructed simulator with rule gold:
- a same-token-form, round-only change reverses the layer-11 transplant effect (M1);
- the transplant is locally and conditionally sufficient and partly necessary (M20);
- the repairs come with measured false vetoes (M17), and three-action errors are measured per arm (Table S1).

All of this is on kev-4B, except the separability, which is two kev-family checkpoints on the same scenes.

**What changed in V4.**
- The mechanism route M1–M22 is added (section "Mechanism route" below).
- The candidate explanation is revised from a missing encoding to a conflict that is represented but not used (M18,
  M21, M22). The Lepori et al. (2026) row and note change accordingly.
- The V3 audit's (`4b27c9b`) non-blocking items are fixed: the two stale sentences under Tang et al. and Chu, Sun &
  Weng (P1-Editorial-1), and the unclosed `**` in "Where it holds" (P2).

## Comparison table (added after audit `d9d3338`, P1-2; also Table R1 in manuscript v9)

Activation patching is a standard method. What differs here is the failure studied, the gold, the controls and the
endpoint.

| Work | Setting and failure | Intervention | Endpoint | Relation to this study |
|---|---|---|---|---|
| Abdelsalam et al. (2026) | Code models; misleading comments override execution semantics | Token-aligned residual-stream patching | Code-semantics prediction | Same method family; a different failure (a misleading cue, not missed appended evidence) |
| Chu, Sun & Weng (2026) | Six LLMs; detection of harmful input and refusal | Circuit identification and weight scaling | Refusal behaviour | The closest detection-to-decision analogue; we identify no circuit and edit no weights |
| Lepori et al. (2024; 2026) | Contextualization timing; in-context semantics encoded but not used | Mechanistic analyses and interventions | Task answers | Timing: disfavored, not excluded. Encoded-but-not-used: the mechanism route (M18, M21, M22) finds the same form of failure in a security-typed scorer |
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
- **What A461 adds:** In this scorer the query side is inert (v5). G2 establishes interventional sensitivity of the
  appended span and repairs the decision causally. The failure is not identified as an encoding deficiency: the
  mechanism route finds the conflict linearly decodable in the missed scenes but not used (M18, M21, M22).

### Racing Thoughts (Lepori, Mozer, Ghandeharioun 2024) [17]

- **What it shows:** Contextualization errors come from timing: an entity is read before it is formed.
- **What A461 adds:** The readout is sensitive to the span at layers 11–12 (SecJev) and 11–15 (kev-4B), and a
  recognized span placed there is used. This argues against a pure timing account. It does not prove one is absent.

### LMs Struggle to Use Representations Learned In-Context (Lepori et al. 2026) [18]

- **What it shows:** Novel semantics are encoded but not deployed.
- **What A461 adds (revised in V4):** The same form of dissociation, in a security-typed scorer with rule gold. In the
  scenes both scorers miss, a held-out probe decodes the appended conflict from the span (AUROC 0.993 kev-4B, 0.964
  SecJev) and from the decision state, above the token surface, yet steering the decision state along the conflict
  direction moves no decision (M19, M21, kev-4B). The missed span still never repairs when transplanted (0/48 SecJev,
  0/40 kev-4B): it lacks the round-keyed verdict that the layer-11 heads write in recognizing scenes (M1–M5, M20), not
  the information itself. Novelty of the phenomenon class is therefore small; the delta is the task, the held-out
  source-group design and the link to interventions.

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
  *evidence* between scenes under dose and sham controls. We compare strictly recognized appended-conflict donors with
  class-matched, content- and context-different sources; the contrast does not isolate recognition. We repair a typed
  decision that a rule oracle defines.

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
   - **Where it holds:**
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
- That the failure is an encoding failure. V3 called it the leading candidate; the mechanism route revises it (the
  conflict is represented but not used), and that account is itself decodability plus kev-4B interventions, not an
  identified circuit.
- That recognition, as opposed to source content, context or host interaction, is what decides repair.
- A rule-binding or witness-binding mechanism.
- A C→A mediation chain, or a shared mechanism between the two readouts.
- Generality beyond the kev family and this simulator family.
- Key-only or component-level mediation.
- Any attack, attacker reachability or deployment relevance.

## Mechanism route (V4; M1–M22)

Full stage list and verdicts: manuscript v10 Table M1 and `CLAIMS_EVIDENCE_MAP.md` M-A to M-F.

**Prior art.**
- Interchange interventions, activation patching both ways and causal abstraction are standard. Zhang & Nanda (2024)
  and Makelov et al. (2023) warn that localization depends on metric, corruption and off-manifold paths.
- Mean-difference steering and representation engineering are standard, as is the observation that linearly decodable
  features need not be used.
- Last-token error probes and "knows more than it says" probes (A612 index) cover the monitor's phenomenon class;
  whitening monitors (2512.03994) are unsupervised OOD detectors.

**Deltas that survive.**
1. **M1:** a same-token-form, round-only change reverses the causal effect of the appended span's layer-11 state
   (53 → 1 joint repairs of 104; main > round in 104/104 cells, 14/14 groups). The state carries a relation-validity
   verdict, not a token class.
2. **M2–M5, M20:** that verdict is written by layer-11 attention heads 8–14 from the bulk context, by direction, and
   transfers across scenes. It is sufficient in hosts and necessary in 9/14 recognizing donors. Necessity is partial:
   recognition is redundant in the strongest donors. The result is two-directional, preregistered, on a safety relation.
3. **M17:** every repair is measured for false veto on benign variants of the same hosts. The own-donor patch is
   NONSELECTIVE; the contrast-carrying pooled arms are selective on duplicate and wrong-round votes.
4. **M18, M21, M22:** the missed conflict is decodable but not used, on two scorers at the decodability level and on
   kev-4B causally at the decision token.

**Deltas that do not survive.**
- The mechanism-located monitor: generic last-token probes match it on both scorers (preregistered GENERIC_MATCHES), so
  it is infrastructure validation only.
- The pooled-vector line (M6–M16): host-limited (3/8 hosts), with the subspace unresolved and the tilt host-specific.

**Status.** Small to moderate. The phenomenon classes (patching, steering nulls, decodable-but-unused) are known. The
deltas are the preregistered two-directional round-keyed result with false-veto controls, and the present-but-unused
statement on a security-typed scorer with rule gold, replicated at the decodability level on a second scorer.
