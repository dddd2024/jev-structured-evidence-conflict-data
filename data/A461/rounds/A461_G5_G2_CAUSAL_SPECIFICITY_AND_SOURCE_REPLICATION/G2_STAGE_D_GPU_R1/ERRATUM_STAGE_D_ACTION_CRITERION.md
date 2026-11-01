# Stage-D erratum: the preregistered action criterion was structurally unattainable

**Fact (verified on the raw rows):** in all 192 D2 patch rows, the logits of every question other than
`conflicting_vote` (certificate_action, evidence_level, quorum) are bitwise identical to the unpatched Stage-A
baseline of the same host arm.

**Cause (design error by the research agent, not a model result):** the kev hybrid backbone runs in row form:
each question is an independent causal row (state tokens + that question's branch). Stage-B/C/D patch hooks
overwrite the appended span only in the `conflicting_vote` row (`h[c_idx, s0:s1]`). The certificate_action row
keeps its own unpatched copy of the state, so its output cannot change under these patches. The preregistered
`SPECIFIC_REJECT` condition, and therefore the `BEHAVIOURAL_CORRECTION` verdict, could never be met. The same holds
for the `action_changes_main` statistics in Stage-B/C, which were reported descriptively as 0.

**Consequences:**
- The preregistered D2 verdict `NO_BEHAVIOURAL_CORRECTION` stands as computed. It is not evidence that the action
  pathway ignores the conflict representation, and it must not be cited as such.
- The readout-level results are unaffected: at L11, 10/32 specific C flips across all 3 donor groups and all 7
  host groups (each control flips 1/32); at L12, 3/32.
- An action-level test requires patching the action row's own copy of the span (or all rows). That needs a new,
  separately frozen design.
