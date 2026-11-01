# A461 safety track: threat model and reachability (document only, 2026-10-31)

**What this is:** the threat model and reachability statement that standard V1 §2 requires. It covers who can change which field, through which entry point, what is authenticated, and whether the Gold is source-internal or a deployment authorization. It is a document only, with no experiment.

## The decision being scored
- **Inputs:** a twins_streamlet scene gives a node's state: the validator set, the candidate round, the decision time, and the `received_messages`, which are votes with author, block, kind, received time and round.
- **Question:** given that state, kev-4B and SecJev-0.8B answer typed questions. The safety-relevant one is `certificate_action` ∈ {accept, reject_conflict, wait}.
- **Gold:** the simulator's executable rule.
  - `reject_conflict` iff a validator in the set has two votes in the candidate round for different blocks, both received by the decision time (an equivocation).
  - Otherwise `accept` if the quorum holds, and `wait` if it does not.

## Adversary
- **Who:** a single Byzantine validator that is a member of the validator set. This is the standard BFT fault model.
- **Capability:** sign and send a second vote in the same round for a different block. This is exactly the appended-vote edit of every A461 stage: the `new` arm appends "author v, round r, block b′" to a state that already holds v's vote for b in round r.
- **What the attacker needs:** no write access beyond normal participation. An equivocating validator only sends votes it is entitled to sign. The edit is therefore a reachable input under the BFT fault model, not a researcher-only manipulation. The other edits are different:
  - the SA duplicate is the same vote re-sent, which is reachable but benign;
  - ROUND and OUTSIDER are near misses: wrong round, and a non-validator author.
- **Authentication:** the scene format carries no signatures. The study therefore assumes that the transport has already authenticated each vote's author. That is the setting in which equivocation evidence is valid in deployed BFT systems (e.g. CometBFT duplicate-vote evidence). An unauthenticated sender is the OUTSIDER case, whose Gold is not a conflict.

## Consequence of the error
- If such a scorer were the component that decides whether a certificate is valid, a false accept means the following:
  - an equivocation by one validator is not flagged;
  - the certificate is accepted;
  - no evidence is raised against the equivocating validator.
- In BFT protocols, catching equivocation is part of the safety argument. The error class is therefore safety-relevant, not merely an accuracy issue.
- The measured size (S2 note) is 66.9% false accept on kev-4B and 55.7% on SecJev-0.8B, with SecJev deferring another 33.1%.

## What is not claimed
- **No deployment:** no deployed system is known to use kev-4B or SecJev-0.8B as its certificate checker, and no deployment chain was examined. This is not S4: the Gold is source-internal (the simulator's rule), not a deployment authorization.
- **No novel attack:** the attacker needs no special crafting, because the equivocation is the plain protocol message. The failure is a coverage gap of the learned scorer, not an adversarial-example technique. Making appended votes harder to recognize, for example by optimizing their wording, is out of scope and not attempted.
- **No case for replacing the rule:** a deterministic check finds every equivocation in this task with no false veto. The practical recommendation is not to use these learned scorers as the sole equivocation check. A learned monitor (the diagnostic-monitor stage) is useful only as a check on the scorer, or where the scorer runs without the rule. It has to be judged against the rule and against generic monitors.
