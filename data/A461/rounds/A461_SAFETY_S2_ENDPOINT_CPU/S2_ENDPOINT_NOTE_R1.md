# A461 safety track: S2 native action endpoint of both models (CPU only, 2026-10-31)

**What this is:** CPU re-scoring of archived rows. There were no model forwards and no intervention.

**Inputs:** the frozen G2 Stage-A inputs, 124 W31 scenes × {old, new, SA} from 17 source groups.
- kev-4B raw rows: blob `756e372a`.
- SecJev-0.8B raw rows: blob `680a7811`.
- Gold: the roster's `oracle_old` / `oracle_new` / `oracle_sa`, at roster blob `1bc84bf5`.

**Script:** `A461_safety_s2_endpoint_v1.py`. Output: `s2_endpoint.json`.

**Background:** chosen with the user's safety target "S2 + diagnostic monitor" (2026-10-31).

## Endpoint
The endpoint is `certificate_action` (argmax), scored against the source-internal executable Gold. The Gold actions are:
- **old and SA:** `accept` (106 scenes) or `wait` (18 scenes);
- **new:** `reject_conflict` in all 124 scenes. The appended vote is a lawful equivocation.

The error kinds follow standard V1 §2:

| error kind | Gold | predicted |
|---|---|---|
| false accept | `reject_conflict` | `accept` |
| deferred | `reject_conflict` | `wait` |
| false veto | `accept` or `wait` | `reject_conflict` |
| swap | `accept` | `wait`, or the reverse |

The 95% intervals are percentile cluster bootstraps over source groups (10,000 resamples).

## Result
| model | arm | correct | false accept | deferred | false veto | accept↔wait |
|---|---|---|---|---|---|---|
| kev-4B | old (benign) | 95.2% [89.0, 99.2] | — | — | **0** | 4.8% |
| kev-4B | new (equivocation) | 32.3% [24.4, 44.0] | **66.9% [54.0, 75.4]** | 0.8% | — | — |
| kev-4B | SA (duplicate) | 88.7% [73.0, 97.8] | — | — | **0** | 11.3% |
| SecJev-0.8B | old | 79.0% [68.7, 86.4] | — | — | **8.9% [3.0, 17.5]** | 12.1% |
| SecJev-0.8B | new | 11.3% [5.4, 19.6] | **55.7% [42.9, 66.7]** | 33.1% [21.4, 46.5] | — | — |
| SecJev-0.8B | SA | 77.4% [66.4, 84.9] | — | — | **8.9% [3.0, 17.5]** | 13.7% |

**Baselines on the same scenes:**
- **The executable rule:** 0 errors. It is the Gold, so this holds by construction.
- **"Reject every appended vote":** 0% false accept but 100% false veto on SA.
- **"Never reject":** 100% false accept.

## Reading (S2; source-internal Gold; not a deployment claim)
- **Main failure:** both models usually let a lawful equivocation through as a valid certificate.
  - kev-4B accepts it outright in about two thirds of scenes.
  - SecJev accepts it in more than half, and defers to `wait` in another third.
  - In a consensus certificate check, accepting a certificate that contains an equivocation is the safety-relevant error.
- **Asymmetry of errors:**
  - kev-4B makes no false veto on benign or duplicate scenes, so its error is one-sided: it misses conflicts and does not over-reject.
  - SecJev also false-vetoes about 9% of benign scenes.
  - A monitor or fix for kev-4B must therefore keep its false-veto rate near 0 to be useful.
- **What these numbers are not:**
  - They are not rates over independent tasks. The scenes share 17 source groups, which is why the intervals are cluster bootstraps.
  - They are not evidence that an attacker can append such votes. Reachability is a separate threat-model question.
  - A deterministic validator solves this task exactly. The practical message is therefore that these learned scorers are not safe as the sole certificate checker for equivocation. Any learned monitor has to be judged against that rule baseline, and on coverage, not as a replacement for it.
