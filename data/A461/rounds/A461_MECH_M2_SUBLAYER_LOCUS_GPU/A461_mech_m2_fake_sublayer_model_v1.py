#!/usr/bin/env python3
"""Tiny CPU stand-in for the kev-4B hybrid DecisionModel with Qwen3.5-shaped decoder layers (M2 self-test).

Same surface as A461_g5_g2_fake_patch_model_v1.FakePatchModel, plus the sublayer structure the M2 runner
hooks: every layer has .mlp and either .linear_attn (returns a tensor) or, on every 4th layer, .self_attn
(returns (out, weights)), combined as h = h + mixer(norm(h)); h = h + mlp(norm(h)). Mixers mix causally
(running mean), so a span patch changes later positions. Deterministic float32 CPU, no weights on disk.

FAKE_FAULT=doublefire@N : call N runs the LM a second time (the runner's pre-hook gate must refuse it).
"""
import os
import types

import torch
from torch import nn

D = 64


def _w(seed):
    g = torch.Generator().manual_seed(seed)
    return nn.Parameter(torch.randn(D, D, generator=g) / D ** 0.5, requires_grad=False)


def _norm(h):
    return h / (h.pow(2).mean(-1, keepdim=True) + 1e-6).sqrt()


class FakeMixer(nn.Module):
    def __init__(self, seed, tuple_out):
        super().__init__()
        self.w = _w(seed)
        self.tuple_out = tuple_out

    def forward(self, h):
        t = torch.arange(1, h.shape[1] + 1, dtype=h.dtype).view(1, -1, 1)
        out = 0.5 * torch.tanh((h.cumsum(dim=1) / t) @ self.w)
        return (out, None) if self.tuple_out else out


class FakeMLP(nn.Module):
    def __init__(self, seed):
        super().__init__()
        self.w = _w(seed)

    def forward(self, h):
        return 0.3 * torch.tanh(h @ self.w)


class FakeLayer(nn.Module):
    def __init__(self, i):
        super().__init__()
        full = i % 4 == 3
        if full:
            self.self_attn = FakeMixer(1000 + i, True)
        else:
            self.linear_attn = FakeMixer(1000 + i, False)
        self.mlp = FakeMLP(5000 + i)

    def forward(self, h):
        mixed = self.self_attn(_norm(h))[0] if hasattr(self, "self_attn") else self.linear_attn(_norm(h))
        h = h + mixed
        return h + self.mlp(_norm(h))


class FakeInner(nn.Module):
    def __init__(self, n_layers):
        super().__init__()
        self.layers = nn.ModuleList([FakeLayer(i) for i in range(n_layers)])


class FakeLM(nn.Module):
    def __init__(self, n_layers):
        super().__init__()
        self.base_model = types.SimpleNamespace(model=FakeInner(n_layers))
        self.inner = self.base_model.model
        self.freq = torch.linspace(0.001, 0.5, D)

    def forward(self, ids):
        h = torch.sin(ids.to(torch.float32).unsqueeze(-1) * self.freq)
        for layer in self.base_model.model.layers:
            h = layer(h)
        return h


class FakePatchModel(nn.Module):
    def __init__(self, n_layers=32):
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
