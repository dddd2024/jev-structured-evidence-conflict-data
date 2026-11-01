#!/usr/bin/env python3
"""A461-G5 V4 acceptance item (6): CPU mock hook test.

Asserts that a layer-output patch on the CONFLICT row (batch index 1 of a 4-row
batch) changes that row's downstream logits under a known perturbation, while
the other three rows stay fixed - the exact failure mode of runner V3 (which
patched row 0, the action row, and read row 1). Pure synthetic torch; no model.
"""
import json, math, sys
import torch
from torch import nn

OUT = sys.argv[1] if len(sys.argv) > 1 else "mock_patch_test.json"


class FakeLayer(nn.Module):
    def forward(self, x):
        return x + 1.0  # identity-plus: known, invertible


class FakeHead(nn.Module):
    def forward(self, x):
        return x.sum(dim=-1)  # scalar per row


def main():
    torch.manual_seed(0)
    B, L, D = 4, 12, 8
    layers = nn.ModuleList([FakeLayer() for _ in range(6)])
    head = FakeHead()
    x0 = torch.randn(B, L, D)
    # baseline: run the stack
    def run(x_in, patch=None, layer_idx=None):
        for i, lyr in enumerate(layers):
            if patch is not None and i == layer_idx:
                bi, start, states = patch
                x_in = x_in.clone()
                x_in[bi, start:start + states.shape[0], :] = states
            x_in = lyr(x_in)
        return head(x_in)
    base = run(x0)
    # donor "states": perturbed values at the conflict row's span
    donor_states = torch.randn(4, D) + 10.0
    C_ROW, START, W = 1, 4, 4
    patched = run(x0, (C_ROW, START, donor_states), 2)
    # assertions
    others_unchanged = all(torch.equal(base[r], patched[r]) for r in range(B) if r != C_ROW)
    c_changed = not torch.equal(base[C_ROW], patched[C_ROW])
    span_changed = not torch.equal(base[C_ROW, START:START + W], patched[C_ROW, START:START + W])
    outside_unchanged = torch.equal(base[C_ROW, :START], patched[C_ROW, :START]) and \
        torch.equal(base[C_ROW, START + W:], patched[C_ROW, START + W:])
    # reversal control: patching with the row's own states must be identity
    own = x0[C_ROW, START:START + W, :].clone()
    ident = run(x0, (C_ROW, START, own), 2)
    identity_ok = torch.equal(base[C_ROW], ident[C_ROW])
    result = {"schema": "JEV_A461_G5_MOCK_PATCH_TEST_V1",
              "C_ROW": C_ROW, "START": START, "W": W,
              "others_unchanged": bool(others_unchanged),
              "c_row_changed": bool(c_changed),
              "span_changed": bool(span_changed),
              "outside_span_unchanged": bool(outside_unchanged),
              "own_state_patch_is_identity": bool(identity_ok),
              "verdict": "PASS" if all([others_unchanged, c_changed, span_changed,
                                        outside_unchanged, identity_ok]) else "FAIL"}
    open(OUT, "w").write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
