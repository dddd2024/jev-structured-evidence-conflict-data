#!/usr/bin/env python3
"""Tiny CPU torch stand-in for the kev hybrid DecisionModel (Stage-B self-test).

Same surface the Stage-B runner touches: .hybrid, .lm (an nn.Module whose
forward pre-hook counts physical calls), .lm.base_model.model.layers (24
nn.Modules with forward hooks, output [rows, T, D]), .forward(enc) in kev row
form (one causal row per question = state tokens + that question's branch),
returning one logits tensor per question sized by its options. Layers mix
causally (running mean), so a span patch at layer L changes later positions
and therefore the readout; identity patches are bitwise no-ops. Deterministic,
float32, CPU, no weights on disk, no network.

FAKE_FAULT=doublefire@N : call N runs the LM a second time (extra physical LM
call) - the runner's pre-hook gate must refuse it before the LM body.
"""
import os
import types

import torch
from torch import nn

D = 64
N_LAYERS = 24


class FakeLayer(nn.Module):
    def __init__(self, i):
        super().__init__()
        g = torch.Generator().manual_seed(1000 + i)
        self.w = nn.Parameter(torch.randn(D, D, generator=g) / D ** 0.5, requires_grad=False)

    def forward(self, h):
        t = torch.arange(1, h.shape[1] + 1, dtype=h.dtype).view(1, -1, 1)
        return h + 0.5 * torch.tanh((h.cumsum(dim=1) / t) @ self.w)


class FakeInner(nn.Module):
    def __init__(self, n_layers=N_LAYERS):
        super().__init__()
        self.layers = nn.ModuleList([FakeLayer(i) for i in range(n_layers)])


class FakeLM(nn.Module):
    def __init__(self, n_layers=N_LAYERS):
        super().__init__()
        self.base_model = types.SimpleNamespace(model=FakeInner(n_layers))
        self.inner = self.base_model.model  # registers the layers as submodules
        self.freq = torch.linspace(0.001, 0.5, D)

    def forward(self, ids):
        h = torch.sin(ids.to(torch.float32).unsqueeze(-1) * self.freq)
        for layer in self.base_model.model.layers:
            h = layer(h)
        return h


class FakePatchModel(nn.Module):
    def __init__(self, n_layers=N_LAYERS):
        super().__init__()
        self.hybrid = True
        self.lm = FakeLM(n_layers)
        g = torch.Generator().manual_seed(7)
        self.head = nn.Parameter(torch.randn(D, 8, generator=g), requires_grad=False)
        self.fault = os.environ.get("FAKE_FAULT", "none")
        self.calls = 0

    def forward(self, enc):
        self.calls += 1
        ids, seg = enc["ids"], enc["seg"]
        S = [t for t, s in zip(ids, seg) if s == 0]
        rows, ends = [], []
        for k in range(1, len(enc["decide_idx"]) + 1):
            br = [t for t, s in zip(ids, seg) if s == k]
            rows.append(S + br)
            ends.append(len(S) + len(br) - 1)
        L = max(len(r) for r in rows)
        x = torch.zeros((len(rows), L), dtype=torch.long)
        for i, r in enumerate(rows):
            x[i, :len(r)] = torch.tensor(r)
        h = self.lm(x)
        if self.fault == "doublefire@%d" % self.calls:
            h = self.lm(x)
        return [h[i, e] @ self.head[:, :len(oi)] for i, (e, oi) in enumerate(zip(ends, enc["opt_idx"]))]
