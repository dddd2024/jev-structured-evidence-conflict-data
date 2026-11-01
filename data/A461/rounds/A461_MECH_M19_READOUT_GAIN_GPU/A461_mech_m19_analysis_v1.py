#!/usr/bin/env python3
"""A461-MECH-M19 R1 analysis (CPU only, torch; frozen before any M19 forward). Rules: m19_design.json ->
preregistered_analysis. Readout-gain verdicts per layer from the op rows; readout geometry from the replay captures
(post-final-norm <decide> and option states) and the pinned head weights: per row, the head's exact gradient of
z_reject - z_accept with respect to the <decide> state, against a held-out probe direction fit on those same
head-input states (leave one source group out)."""
import argparse, collections, hashlib, json, math, random, sys
from pathlib import Path

import torch

ARMS_ORDER = ["probe_L19_g2", "probe_L19_g4", "probe_L19_g8", "probe_L31_g2", "probe_L31_g4", "probe_L31_g8",
              "random_L19_g8", "random_L31_g8"]
BENIGN_ARMS = ("old", "SA", "ROUND", "OUTSIDER")


def L(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def act(qs):
    a = next(q for q in qs if q["id"] == "certificate_action")
    return a["keys"][max(range(len(a["keys"])), key=lambda i: a["logits"][i])]


def amargin(qs):
    a = dict(zip(*(lambda q: (q["keys"], q["logits"]))(next(q for q in qs if q["id"] == "certificate_action"))))
    return a["reject_conflict"] - max(a["accept"], a["wait"])


def cp_upper(k, n, alpha=0.05):
    if k >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(100):
        p = (lo + hi) / 2
        cdf = sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))
        lo, hi = (p, hi) if cdf > alpha else (lo, p)
    return round(hi, 4)


def fit_probe(X, y):   # the M18 probe spec
    mu, sd = X.mean(0), X.std(0).clamp_min(1e-6)
    Z = (X - mu) / sd
    w = torch.zeros(Z.shape[1], dtype=torch.float64, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([w, b], max_iter=200, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(Z @ w + b, y.double(), reduction="sum") + 0.5 * (w @ w)
        loss.backward()
        return loss
    opt.step(closure)
    return w.detach() / sd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--captures", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m18-raw", required=True, type=Path)
    ap.add_argument("--head-pt", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--fake-dry-run", action="store_true")
    a = ap.parse_args()
    D = json.loads(a.design.read_text("utf8"))
    rows = L(a.raw)
    m18 = {r["forward_index"]: r for r in L(a.m18_raw)}
    rep = {(r["target_scene"], r["target_arm"]): r for r in rows if not r.get("op")}
    ops = [r for r in rows if r.get("op")]
    m18_by = {(r["target_scene"], r["target_arm"]): r for r in m18.values()}
    gate = {"rows": len(rows), "expected": D["total"], "replays": len(rep), "op_rows": len(ops),
            "replay_bitwise_m18": sum(rep[k]["questions"] == m18_by[k]["questions"] for k in rep if k in m18_by),
            "op_conditions": dict(collections.Counter(r["condition"] for r in ops))}
    gate["pass"] = (gate["rows"] == gate["expected"] == 5580 and gate["replays"] == 620 == gate["replay_bitwise_m18"]
                    and gate["op_conditions"] == {c: 620 for c in ARMS_ORDER})
    nat = {k: act(r["questions"]) for k, r in rep.items()}
    sets = {k: ("MISSED" if k[1] == "new" and nat[k] != "reject_conflict" else
                "RECOGNIZED" if k[1] == "new" else
                "NATIVE_FV" if nat[k] == "reject_conflict" else "BENIGN") for k in rep}
    grp = {k: r["source_group"] for k, r in rep.items()}
    groups = sorted(set(grp.values()))
    by_arm = collections.defaultdict(dict)
    for r in ops:
        by_arm[r["condition"]][(r["target_scene"], r["target_arm"])] = r

    def measures(cond, keys):
        rr = by_arm[cond]
        mi = [k for k in keys if sets[k] == "MISSED"]
        be = [k for k in keys if sets[k] == "BENIGN"]
        rc = [k for k in keys if sets[k] == "RECOGNIZED"]
        rej = lambda k: act(rr[k]["questions"]) == "reject_conflict"
        out = {"REPAIR": sum(map(rej, mi)) / len(mi) if mi else None,
               "FV": sum(map(rej, be)) / len(be) if be else None,
               "RECOGNIZED_kept": sum(map(rej, rc)) / len(rc) if rc else None}
        for a_ in BENIGN_ARMS:
            b_ = [k for k in be if k[1] == a_]
            out[f"FV_{a_}"] = sum(map(rej, b_)) / len(b_) if b_ else None
        return out

    allk = list(rep)
    point = {c: measures(c, allk) for c in ARMS_ORDER}
    for c in ARMS_ORDER:
        rr = by_arm[c]
        point[c]["median_dA_missed"] = round(statistics_median([amargin(rr[k]["questions"]) - amargin(rep[k]["questions"])
                                                                for k in allk if sets[k] == "MISSED"]), 4)
        point[c]["median_dA_benign"] = round(statistics_median([amargin(rr[k]["questions"]) - amargin(rep[k]["questions"])
                                                                for k in allk if sets[k] == "BENIGN"]), 4)
        fvg = sum(any(act(rr[k]["questions"]) == "reject_conflict" for k in allk if grp[k] == g and sets[k] == "BENIGN")
                  for g in groups)
        point[c]["fv_groups"] = {"groups_with_fv": fvg, "of": len(groups), "cp95_upper": cp_upper(fvg, len(groups))}
    by_g = collections.defaultdict(list)
    for k in allk:
        by_g[grp[k]].append(k)
    rng = random.Random(20261031)
    boots = [[k for g in (rng.choice(groups) for _ in groups) for k in by_g[g]] for _ in range(a.boot)]
    ci = {}
    for c in ARMS_ORDER:
        for mname in ("REPAIR", "FV"):
            v = sorted(x for x in (measures(c, b)[mname] for b in boots) if x is not None)
            ci[f"{c}|{mname}"] = [round(v[int(0.025 * len(v))], 4), round(v[int(0.975 * len(v)) - 1], 4)] if v else None
    verdicts = {}
    for Lr in (19, 31):
        sel = [g for g in (2, 4, 8) if (point[f"probe_L{Lr}_g{g}"]["REPAIR"] or 0) >= 0.5]
        clean = [g for g in sel if all((point[f"probe_L{Lr}_g{g}"][f"FV_{a_}"] or 0) <= 0.05 for a_ in BENIGN_ARMS)]
        rnd = point[f"random_L{Lr}_g8"]["REPAIR"] or 0
        v = ("READOUT_GAIN_INERT" if not sel else
             "READOUT_GAIN_REPAIRS" if clean and rnd <= 0.10 else
             "READOUT_GAIN_NONSELECTIVE" if not clean else "READOUT_GAIN_REPAIRS_BUT_RANDOM_TOO")
        verdicts[f"L{Lr}"] = v + ("|RANDOM_ALSO_REPAIRS" if rnd > 0.10 else "")
        verdicts[f"L{Lr}_clean_gammas"] = clean
    # readout geometry (reported): head-input space
    geo = {"status": "NOT_COMPUTED"}
    try:
        hp = torch.load(a.head_pt, map_location="cpu", weights_only=True)
        H = {k: v.double() for k, v in hp["head"].items()}
        caps = {k: torch.load(a.captures / r["capture_file"]["name"], weights_only=True) for k, r in rep.items()}
        X = torch.stack([caps[k]["decide"].double() for k in allk])
        ok_dim = X.shape[1] == H["q.weight"].shape[1]
        if ok_dim:
            y = torch.tensor([k[1] == "new" for k in allk])
            gidx = [grp[k] for k in allk]
            cos_rows = []
            for g in groups:
                tr = [i for i, gg in enumerate(gidx) if gg != g]
                te = [i for i, gg in enumerate(gidx) if gg == g]
                w = fit_probe(X[tr], y[tr])
                u = w / w.norm()
                for i in te:
                    k = allk[i]
                    keys = caps[k]["opt_keys"]
                    O = caps[k]["opts"].double()
                    kk = O @ H["k.weight"].T + H["k.bias"]
                    dk = kk[keys.index("reject_conflict")] - kk[keys.index("accept")]
                    grad = H["q.weight"].T @ dk          # d(z_rej - z_acc) / d h_decide, up to the positive scale
                    cos_rows.append((sets[k], float(grad @ u / grad.norm())))
            med = lambda s_: round(statistics_median([c for ss, c in cos_rows if ss == s_]), 4)
            geo = {"status": "COMPUTED", "median_cos_probe_vs_head_gradient": {s_: med(s_) for s_ in
                                                                              ("MISSED", "RECOGNIZED", "BENIGN")},
                   "note": "cos > 0: moving along the held-out conflict direction raises z_reject - z_accept"}
        else:
            geo = {"status": "DIM_MISMATCH (fake model)"}
    except Exception as err:
        geo = {"status": f"NOT_COMPUTED: {type(err).__name__}: {str(err)[:120]}"}
    if not gate["pass"]:
        verdicts = {k: "INCONSISTENT" for k in verdicts}
    res = {"schema": "JEV_A461_MECH_M19_ANALYSIS_V1", "fake_dry_run": a.fake_dry_run, "consistency_gate": gate,
           "verdicts": verdicts, "measures": point, "ci95_group_bootstrap": ci,
           "counts": dict(collections.Counter(sets.values())), "readout_geometry": geo,
           "head_pt_sha256": hashlib.sha256(a.head_pt.read_bytes()).hexdigest() if a.head_pt.exists() else None,
           "rules": D["preregistered_analysis"]}
    o = a.out.expanduser().resolve()
    o.mkdir(parents=True, exist_ok=False)
    (o / "m19_analysis.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"gate": gate, "verdicts": verdicts, "measures": point, "ci": ci, "counts": res["counts"],
                      "readout_geometry": geo}, indent=1))
    return 0


def statistics_median(v):
    v = sorted(v)
    n = len(v)
    return float("nan") if not n else (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2)


if __name__ == "__main__":
    sys.exit(main())
