# Stage-F result note (preregistered outcomes reported as computed)

| Hypothesis | Preregistered rule | Result | Status |
|---|---|---|---|
| H-F1 content beyond decision class | JOINT(ttt_new) - JOINT(ttt_sa) >= 5 and >= 2x | 0 vs 0 | **NOT MET**; label CONSISTENT_WITH_POSITIVE_CLASS_REPRESENTATION (rule fallback) |
| H-F2 recognition matters | JOINT(fff_new) <= 2 and donor_new - fff_new >= 5 | 0/48 vs 8/32 | **MET** |
| H-F3 source diversity | ttt_new JOINT from >= 3 source and >= 3 host groups | 0 groups | **NOT MET** |

Integrity: 296/296 calls, 0 denied, host baselines read neither C nor R, 40 captures bitwise == Stage-A/Stage-D rows,
64 donor rows bitwise == Stage-E rows (runner-enforced on GPU).

**Why H-F1 is uninformative as written (design note, not a reinterpretation).** The rule assumed TTT new spans
(recognized conflict content in scenes with a pre-existing conflict) would repair hosts, and asked whether TTT SA spans
(duplicate-vote content in the same conflict-read scenes) repair as well. Neither repairs (0/72 each), so the contrast
cannot reach its threshold and the rule returns its fallback label. That label is therefore not evidence for a
class-prototype account.

**Exploratory, not preregistered as a decision rule.** Class-matched, content-mismatched spans (ttt_sa: the SA arm
itself reads C true and chooses reject_conflict) produce 0/72 joint repairs, against 8/32 for recognized donor spans.
The decision-class state carried by a span is therefore not sufficient for repair in these hosts.

**Interpretation boundary.** Repair is produced only by spans of *appended* conflicts that the model recognized (the
FTF donors). It is not produced by conflict spans it missed (fff_new), nor by spans from scenes recognized through a
pre-existing conflict (ttt_new). The effect remains concentrated in the run-140 donor (7/8 joint).
