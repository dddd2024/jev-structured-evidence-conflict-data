#!/usr/bin/env python3
"""A461-G4 G0D: pointer readout algebra dry-run (pure synthetic, zero model).

Two independent implementations of the SecJev PointerHead readout and of the
exact Delta-M decomposition identity must agree to <=1e-6 relative tolerance
on deterministic pseudo-random inputs, including candidate permutation
sanity. No model weights, no checkpoint, no forwards.

M_i = q_i . d_i / s with d_i = k_true_i - k_false_i, s = sqrt(dp) * T.
Delta_M = [(dq . d_old) + (q_old . dd) + (dq . dd)] / s.
"""
import argparse, hashlib, json, math, os, sys
from pathlib import Path


T_G = None


def impl_a(q_o, q_n, kT_o, kT_n, kF_o, kF_n, s):
    """Implementation A: vector decomposition per the frozen identity."""
    d_o = kT_o - kF_o
    d_n = kT_n - kF_n
    dq = q_n - q_o
    dd = d_n - d_o
    m_o = float(q_o @ d_o) / s
    m_n = float(q_n @ d_n) / s
    t1 = float(dq @ d_o) / s
    t2 = float(q_o @ dd) / s
    t3 = float(dq @ dd) / s
    return m_o, m_n, [t1, t2, t3], m_n - m_o


def impl_b(q_o, q_n, kT_o, kT_n, kF_o, kF_n, s):
    """Implementation B: explicit loop over dimensions, direct M only."""
    dp = len(q_o)
    m_o = sum((q_o[i] * (kT_o[i] - kF_o[i])) for i in range(dp)) / s
    m_n = sum((q_n[i] * (kT_n[i] - kF_n[i])) for i in range(dp)) / s
    return m_o, m_n


def impl_c_forward(q, kT, kF, s):
    """Implementation C: module order z=(k(h_opts) @ q(h_decide))*scale, T applied after."""
    return (float(kT @ q) - float(kF @ q)) / math.sqrt(256.0) / T_G


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--trials", type=int, default=64)
    a = ap.parse_args()
    out = a.out.expanduser().resolve(strict=False)
    ck = lambda v, m: (_ for _ in ()).throw(RuntimeError(m)) if not v else None
    ck(out.parent.is_dir() and not out.exists(), "new out dir")
    out.mkdir(mode=0o700)
    global T_G
    dp, T = 256, 1.0
    T_G = T
    s = math.sqrt(dp) * T
    seed = hashlib.sha256(b"A461-G4-G0D-dryrun").digest()
    results = []
    worst = 0.0
    for t in range(a.trials):
        g = hashlib.sha256(seed + t.to_bytes(4, "big")).digest()
        # deterministic uniform [-1,1) values from the digest stream
        def gen(n):
            vals, buf = [], b""
            while len(vals) < n:
                buf = hashlib.sha256(buf + g).digest()
                for i in range(0, 32, 4):
                    u = int.from_bytes(buf[i:i + 4], "big") / 2 ** 32
                    vals.append(2.0 * u - 1.0)
                    if len(vals) >= n:
                        break
            return vals
        v = gen(6 * dp)
        q_o = v[0:dp]; q_n = v[dp:2 * dp]
        kT_o = v[2 * dp:3 * dp]; kT_n = v[3 * dp:4 * dp]
        kF_o = v[4 * dp:5 * dp]; kF_n = v[5 * dp:6 * dp]
        import numpy as _np
        import numpy as np
        arr = lambda x: np.array(x, dtype=float)
        m_o_a, m_n_a, terms, dm_a = impl_a(arr(q_o), arr(q_n), arr(kT_o), arr(kT_n), arr(kF_o), arr(kF_n), s)
        q_o, q_n, kT_o, kT_n, kF_o, kF_n = arr(q_o), arr(q_n), arr(kT_o), arr(kT_n), arr(kF_o), arr(kF_n)
        m_o_b, m_n_b = impl_b(q_o, q_n, kT_o, kT_n, kF_o, kF_n, s)
        m_n_c = impl_c_forward(q_n, kT_n, kF_n, s)
        rel1 = abs(m_o_a - m_o_b) / max(1e-12, abs(m_o_a))
        rel2 = abs(m_n_a - m_n_b) / max(1e-12, abs(m_n_a))
        rel3 = abs(m_n_c - m_n_a) / max(1e-12, abs(m_n_a))
        recon = sum(terms) - dm_a  # must be 0 exactly by algebra; float rounding only
        rel4 = abs(recon) / max(1e-12, abs(dm_a)) if abs(dm_a) > 1e-9 else abs(recon)
        worst = max(worst, rel1, rel2, rel3, rel4)
        # candidate permutation sanity: swapping candidate order swaps M sign structure
        m_swap = (float(q_n @ kF_n) - float(q_n @ kT_n)) / s
        ck(abs(m_swap + m_n_a) < 1e-9, "permutation sanity failed")
        results.append({"trial": t, "M_old": m_o_a, "M_new": m_n_a,
                        "terms": terms, "delta": dm_a,
                        "rel_implAB_old": rel1, "rel_implAB_new": rel2,
                        "rel_forward_order_C": rel3, "rel_decomposition_residual": rel4})
    ck(worst <= 1e-6, f"tolerance exceeded: {worst}")
    out_doc = {"schema": "JEV_A461_G4_G0D_ALGEBRA_DRYRUN_V1",
               "pointer_dim": dp, "temperature": T, "scale_s": s,
               "trials": a.trials, "worst_relative_error": worst,
               "tolerance": 1e-6, "verdict": "PASS_ALL_IMPLEMENTATIONS_AGREE",
               "identity": "Delta_M = (dq.d_old + q_old.dd + dq.dd)/s verified exactly",
               "note": "synthetic inputs only; no model weights, no forwards",
               "trials_sample": results[:3]}
    with (out / "g0d_algebra_dryrun.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(out_doc, f, sort_keys=True, indent=2)
        f.write("\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        h = hashlib.sha256()
        with (out / "g0d_algebra_dryrun.json").open("rb") as f2:
            for b in iter(lambda: f2.read(1 << 20), b""):
                h.update(b)
        f.write(h.hexdigest() + "  g0d_algebra_dryrun.json\n")
    print(json.dumps({k: out_doc[k] for k in ("trials", "worst_relative_error", "verdict")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
