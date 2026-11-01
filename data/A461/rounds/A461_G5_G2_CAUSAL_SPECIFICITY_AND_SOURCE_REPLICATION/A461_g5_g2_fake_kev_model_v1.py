#!/usr/bin/env python3
"""FakeModel for A461-G5-G2 Stage-A L1 tests (pure python; no torch, no GPU, no network).

Mimics the DecisionModel surface the Stage-A runner touches:
  - .hybrid = True
  - .lm with register_forward_pre_hook(fn) (physical call counting)
  - .forward(enc) -> list of 4 plain-float logit lists (one per question, in the
    real record's 3/2/3/2 option layout), a deterministic pure function of the
    encoded token ids, so replays match their primaries bitwise
  - .eval() / .requires_grad_() no-ops

Fault variants (env FAKE_FAULT) for L1 fault injection:
  none      - deterministic; replays match primaries bitwise
  callcount - logits additionally depend on the call counter (replays then
              MISMATCH their primaries; replay-bitwise-fail test)
  throw4    - raises RuntimeError on the 4th physical call (forward-throw test)
  nonfinite2- the 2nd physical call returns NaN logits (nonfinite gate test)
  doublefire@N - call N fires the lm pre-hooks twice (a hidden extra physical
              lm call), so the runner's per-batch physical cap must refuse the
              next manifest entry before the model is invoked
  sigkill@N - call N kills the process with SIGKILL after the pre-hooks fired
              (abrupt stop: no receipt, no attempt_close; ledger must still
              account the reserved call)
"""
import hashlib
import json
import os


class FakeLm:
    def __init__(self, counter):
        self._counter = counter
        self._hooks = []

    def register_forward_pre_hook(self, fn):
        self._hooks.append(fn)

        class _Handle:
            def remove(self_):
                self._hooks.remove(fn)
        return _Handle()

    def _fire(self):
        for fn in self._hooks:
            fn(self, None)


class FakeModel:
    def __init__(self):
        self.hybrid = True
        self._physical = [0]
        self.lm = FakeLm(self._physical)
        self.fault = os.environ.get("FAKE_FAULT", "none")
        self.forward_log = []

    def eval(self):
        return self

    def requires_grad_(self, flag):
        return self

    @property
    def physical_calls(self):
        return self._physical[0]

    def forward(self, enc):
        self._physical[0] += 1
        self.lm._fire()
        n = self._physical[0]
        if self.fault == "doublefire@%d" % n:
            self.lm._fire()
        if self.fault == "sigkill@%d" % n:
            import signal
            os.kill(os.getpid(), signal.SIGKILL)
        if self.fault == "throw4" and n == 4:
            raise RuntimeError("FAKE_FAULT throw4: synthetic forward failure on call 4")
        ids_hash = int(hashlib.sha256(json.dumps(enc["ids"], separators=(",", ":")).encode("utf-8")).hexdigest()[:12], 16)
        layout = [3, 2, 3, 2]  # certificate_action 3, conflicting_vote 2, evidence_level 3, quorum 2
        out = []
        for qi, k in enumerate(layout):
            base = (ids_hash >> (qi * 8)) & 0xFF
            vals = [((base + j * 3) % 17) - 8.0 for j in range(k)]
            if self.fault == "callcount":
                vals = [v + n * 0.5 for v in vals]
            if self.fault == "nonfinite2" and n == 2 and qi == 1:
                vals = [float("nan"), float("nan")]
            out.append(vals)
        self.forward_log.append(n)
        return out
