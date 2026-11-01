#!/usr/bin/env python3
"""Tiny CPU stand-in for the kev-4B hybrid DecisionModel with a Qwen3.5-shaped full-attention module (M3 self-test).

Same surface as A461_mech_m2_fake_sublayer_model_v1.FakePatchModel, but every 4th layer's .self_attn is a gated
grouped-query attention with the attributes and call convention the M3 runner reads: q_proj (query and gate
interleaved per head), k_proj, v_proj, o_proj (no bias), q_norm, k_norm, head_dim, scaling; called as
self_attn(hidden_states=..., position_embeddings=(cos, sin)); this module defines apply_rotary_pos_emb (partial
rotary) like transformers' modeling_qwen3_5. 16 query heads x 4 dims in 4 KV groups (D = 64), so the M3
manifest's head arms address it unchanged. Deterministic float32 CPU, explicit causal softmax.

FAKE_FAULT=doublefire@N : call N runs the LM a second time (the runner's pre-hook gate must refuse it).
"""
import os
import types

import torch
from torch import nn

D, H, KV, HD, ROT = 64, 16, 4, 4, 2


def _w(seed, i=D, o=D):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(i, o, generator=g) / i ** 0.5


def _lin(seed, i, o):
    m = nn.Linear(i, o, bias=False)
    m.weight.data = _w(seed, i, o).T.contiguous()
    m.requires_grad_(False)
    return m


def _norm(h):
    return h / (h.pow(2).mean(-1, keepdim=True) + 1e-6).sqrt()


class RMS(nn.Module):
    def forward(self, x):
        return _norm(x)


def rotate_half(x):
    x1, x2 = x[..., : x.shape[-1] // 2], x[..., x.shape[-1] // 2:]
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(q, k, cos, sin, unsqueeze_dim=1):
    cos, sin = cos.unsqueeze(unsqueeze_dim), sin.unsqueeze(unsqueeze_dim)
    r = cos.shape[-1]
    q_rot, q_pass = q[..., :r], q[..., r:]
    k_rot, k_pass = k[..., :r], k[..., r:]
    return (torch.cat([q_rot * cos + rotate_half(q_rot) * sin, q_pass], -1),
            torch.cat([k_rot * cos + rotate_half(k_rot) * sin, k_pass], -1))


class FakeAttention(nn.Module):
    def __init__(self, seed):
        super().__init__()
        self.head_dim = HD
        self.scaling = HD ** -0.5
        self.num_key_value_groups = H // KV
        self.q_proj = _lin(seed, D, H * HD * 2)
        self.k_proj = _lin(seed + 1, D, KV * HD)
        self.v_proj = _lin(seed + 2, D, KV * HD)
        self.o_proj = _lin(seed + 3, H * HD, D)
        self.q_norm, self.k_norm = RMS(), RMS()

    def forward(self, hidden_states, position_embeddings, **kwargs):
        B, T, _ = hidden_states.shape
        q, gate = torch.chunk(self.q_proj(hidden_states).view(B, T, -1, HD * 2), 2, dim=-1)
        gate = gate.reshape(B, T, -1)
        q = self.q_norm(q.reshape(B, T, -1, HD)).transpose(1, 2)
        k = self.k_norm(self.k_proj(hidden_states).view(B, T, -1, HD)).transpose(1, 2)
        v = self.v_proj(hidden_states).view(B, T, -1, HD).transpose(1, 2)
        q, k = apply_rotary_pos_emb(q, k, *position_embeddings)
        k = k.repeat_interleave(self.num_key_value_groups, dim=1)
        v = v.repeat_interleave(self.num_key_value_groups, dim=1)
        sc = (q @ k.transpose(-1, -2)) * self.scaling
        sc = sc.masked_fill(torch.ones(T, T, dtype=torch.bool).triu(1), float("-inf"))
        out = (sc.softmax(-1) @ v).transpose(1, 2).reshape(B, T, -1) * torch.sigmoid(gate)
        return self.o_proj(out), None


class FakeMixer(nn.Module):
    def __init__(self, seed):
        super().__init__()
        self.w = nn.Parameter(_w(seed), requires_grad=False)

    def forward(self, hidden_states):
        t = torch.arange(1, hidden_states.shape[1] + 1, dtype=hidden_states.dtype).view(1, -1, 1)
        return 0.5 * torch.tanh((hidden_states.cumsum(dim=1) / t) @ self.w)


class FakeMLP(nn.Module):
    def __init__(self, seed):
        super().__init__()
        self.w = nn.Parameter(_w(seed), requires_grad=False)

    def forward(self, h):
        return 0.3 * torch.tanh(h @ self.w)


class FakeLayer(nn.Module):
    def __init__(self, i):
        super().__init__()
        if i % 4 == 3:
            self.self_attn = FakeAttention(1000 + 10 * i)
        else:
            self.linear_attn = FakeMixer(1000 + 10 * i)
        self.mlp = FakeMLP(5000 + i)

    def forward(self, h, pe):
        if hasattr(self, "self_attn"):
            mixed, _ = self.self_attn(hidden_states=_norm(h), position_embeddings=pe)
        else:
            mixed = self.linear_attn(hidden_states=_norm(h))
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
        self.freq = torch.linspace(0.001, 0.5, D)

    def forward(self, ids):
        B, T = ids.shape
        h = torch.sin(ids.to(torch.float32).unsqueeze(-1) * self.freq)
        ang = torch.arange(T, dtype=torch.float32).view(1, T, 1) * torch.tensor([0.05]).view(1, 1, 1)
        ang = torch.cat([ang, ang], -1).expand(B, T, ROT)
        pe = (ang.cos(), ang.sin())
        for layer in self.base_model.model.layers:
            h = layer(h, pe)
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
