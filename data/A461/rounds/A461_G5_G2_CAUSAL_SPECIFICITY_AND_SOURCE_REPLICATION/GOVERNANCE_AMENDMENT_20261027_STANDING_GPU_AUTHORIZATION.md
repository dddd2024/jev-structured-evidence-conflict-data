# A461 governance amendment: standing GPU authorization (2026-10-27)

**Source.** The user's instruction in chat, 2026-10-27, recorded verbatim:

> 还有现在的治理规则上不用每次实验都要向我请求了，只有最后你认为要最终审计的时候再请求

**Effect.** This amends the GPU-authorization step of policy V2 for this research line. Per-experiment user approval
of GPU runs is no longer requested. The research agent runs each experiment once it is ready, and asks the user only
when it judges the work ready for the final paper-level independent audit (the single audit trigger of policy V2,
unchanged).

**Unchanged.** These execution safeguards stay mandatory:
- every stage's design, manifest and analysis rule are frozen and committed before its GPU run;
- a CPU self-test runs before the GPU run;
- a fixed per-stage budget with batches of at most 128;
- a durable quota ledger with a reservation before every call, and an LM pre-hook gate;
- pinned inputs and model identity;
- bitwise replays against earlier stages;
- raw logits and receipts are archived;
- outputs go only under `~/wjc`.

Each admission file records this instruction as `user_gpu_approval_quote`, together with its time, under governance
`JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2`. Results are still reported to the user after each stage.
