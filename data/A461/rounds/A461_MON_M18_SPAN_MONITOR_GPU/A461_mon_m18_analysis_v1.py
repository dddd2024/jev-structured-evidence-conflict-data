#!/usr/bin/env python3
"""A461-MON-M18 R1 analysis (CPU only, torch float64; frozen before any M18 forward). Rules: m18_design.json ->
preregistered_analysis. Leave-one-source-group-out held-out scores for every detector; operating thresholds from an
inner leave-one-group-out over each outer fold's training groups; group bootstrap for every metric."""
import argparse, collections, json, math, random, sys
from pathlib import Path

import torch

LAYERS = ["emb", "L3", "L7", "L11", "L15", "L19", "L23", "L27", "L31"]
WRITER = list(range(8, 15))


def L(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def act(qs):
    a = next(q for q in qs if q["id"] == "certificate_action")
    return a["keys"][max(range(len(a["keys"])), key=lambda i: a["logits"][i])]


def margins(qs):
    d = {q["id"]: dict(zip(q["keys"], q["logits"])) for q in qs}
    c, a = d["conflicting_vote"], d["certificate_action"]
    return c["true"] - c["false"], a["reject_conflict"] - max(a["accept"], a["wait"])


def fit_probe(X, y):
    mu, sd = X.mean(0), X.std(0).clamp_min(1e-6)
    Z = (X - mu) / sd
    w = torch.zeros(Z.shape[1], dtype=torch.float64, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([w, b], max_iter=200, line_search_fn="strong_wolfe")
    yy = y.double()

    def closure():
        opt.zero_grad()
        loss = torch.nn.functional.binary_cross_entropy_with_logits(Z @ w + b, yy, reduction="sum") + 0.5 * (w @ w)
        loss.backward()
        return loss
    opt.step(closure)
    w_, b_ = w.detach(), b.detach()
    return lambda Xt: ((Xt - mu) / sd) @ w_ + b_


def fit_whiten(Xb, k=15):
    mu = Xb.mean(0)
    _u, s, vh = torch.linalg.svd(Xb - mu, full_matrices=False)
    k = min(k, vh.shape[0])
    scale = (s[:k] / math.sqrt(max(1, Xb.shape[0] - 1))).clamp_min(1e-12)
    V = vh[:k].T
    return lambda Xt: (((Xt - mu) @ V) / scale).norm(dim=1)


def quant(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, math.ceil(q * len(v)) - 1)] if v else float("inf")


def auroc(pos, neg):
    if not pos or not neg:
        return None
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    i = 0
    rsum = 0.0
    while i < len(allv):
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]:
            j += 1
        r = (i + j + 1) / 2
        rsum += r * sum(1 for t in allv[i:j] if t[1] == 1)
        i = j
    n1, n0 = len(pos), len(neg)
    return (rsum - n1 * (n1 + 1) / 2) / (n1 * n0)


def cp_upper(k, n, alpha=0.05):
    """one-sided Clopper-Pearson upper bound for k successes in n (bisection on the binomial cdf)"""
    if k >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(100):
        p = (lo + hi) / 2
        cdf = sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))
        lo, hi = (p, hi) if cdf > alpha else (lo, p)
    return round(hi, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--captures", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--fake-dry-run", action="store_true")
    a = ap.parse_args()
    torch.set_num_threads(int(__import__("os").environ.get("OMP_NUM_THREADS", "4")))
    D = json.loads(a.design.read_text("utf8"))
    rows = L(a.raw)
    gate = {"rows": len(rows), "expected": D["total"],
            "token_sha_ok": sum(r["token_ids_sha256"] == D["scenes"][r["target_scene"]]["arms"][r["target_arm"]]["token_ids_sha256"]
                                for r in rows),
            "max_cross_row": max(r["cross_row_max_absdiff"] for r in rows)}
    gate["pass"] = (gate["rows"] == gate["expected"] == gate["token_sha_ok"] and gate["max_cross_row"] == 0.0)
    feats = collections.defaultdict(list)
    for r in rows:
        f = torch.load(a.captures / r["capture_file"]["name"], weights_only=True)
        ck_names = f["names"] == LAYERS
        if not ck_names:
            raise SystemExit("layer names differ")
        at = f["attn11_span"].double().mean(0)
        hd = at.shape[0] // 16
        feats["SPAN_ATTN11"].append(at)
        feats["SPAN_ATTN11_W"].append(at[WRITER[0] * hd:(WRITER[-1] + 1) * hd])
        for i, n in enumerate(LAYERS):
            feats[f"SPAN_RESID_{n}"].append(f["span_mean"][i].double())
            feats[f"LAST_RESID_{n}"].append(f["last"][i].double())
        M, A = margins(r["questions"])
        feats["NATIVE_M"].append(torch.tensor([M], dtype=torch.float64))
        feats["NATIVE_A"].append(torch.tensor([A], dtype=torch.float64))
    X = {k: torch.stack(v) for k, v in feats.items()}
    y = torch.tensor([r["gold_action"] == "reject_conflict" for r in rows])
    actn = [act(r["questions"]) for r in rows]
    grp = [r["source_group"] for r in rows]
    arm = [r["target_arm"] for r in rows]
    missed = [arm[i] == "new" and actn[i] != "reject_conflict" for i in range(len(rows))]
    recog = [arm[i] == "new" and actn[i] == "reject_conflict" for i in range(len(rows))]
    benign = [arm[i] != "new" and actn[i] != "reject_conflict" for i in range(len(rows))]
    natural_fv = collections.Counter(arm[i] for i in range(len(rows)) if arm[i] != "new" and actn[i] == "reject_conflict")
    groups = sorted(set(grp))
    det = {}
    for k in X:
        if k.startswith("NATIVE"):
            det[k] = ("native", k)
        else:
            det["PROBE:" + k] = ("probe", k)
    for k in ("LAST_RESID_L11", "LAST_RESID_L31", "SPAN_ATTN11"):
        det["WHITEN:" + k] = ("whiten", k)

    def scorer(kind, k, tr):
        Xk = X[k]
        if kind == "native":
            return lambda idx: Xk[idx, 0]
        if kind == "probe":
            f = fit_probe(Xk[tr], y[tr])
            return lambda idx: f(Xk[idx])
        bt = [i for i in tr if benign[i]]
        f = fit_whiten(Xk[bt])
        return lambda idx: f(Xk[idx])

    held = {d: [None] * len(rows) for d in det}
    thr = {d: {} for d in det}
    for g in groups:
        te = [i for i in range(len(rows)) if grp[i] == g]
        tr = [i for i in range(len(rows)) if grp[i] != g]
        for d, (kind, k) in det.items():
            s = scorer(kind, k, tr)(te)
            for i, v in zip(te, s.tolist()):
                held[d][i] = v
            inner = []   # inner leave-one-group-out over the training groups: out-of-sample BENIGN scores
            for g2 in groups:
                if g2 == g:
                    continue
                te2 = [i for i in tr if grp[i] == g2 and benign[i]]
                if not te2:
                    continue
                tr2 = [i for i in tr if grp[i] != g2]
                inner += scorer(kind, k, tr2)(te2).tolist()
            thr[d][g] = {"FV5": quant(inner, 0.95), "FV1": quant(inner, 0.99)}
    flags = {d: {op: [held[d][i] > thr[d][grp[i]][op] for i in range(len(rows))] for op in ("FV5", "FV1")} for d in det}

    def metrics(d, idx):
        pos = [held[d][i] for i in idx if missed[i]]
        neg = [held[d][i] for i in idx if benign[i]]
        m = {"AUROC": auroc(pos, neg)}
        for op in ("FV5", "FV1"):
            fm = [flags[d][op][i] for i in idx if missed[i]]
            fb = [flags[d][op][i] for i in idx if benign[i]]
            m[f"TPR_missed@{op}"] = sum(fm) / len(fm) if fm else None
            m[f"FPR@{op}"] = sum(fb) / len(fb) if fb else None
            for a_ in ("old", "SA", "ROUND", "OUTSIDER"):
                fa = [flags[d][op][i] for i in idx if benign[i] and arm[i] == a_]
                m[f"FPR_{a_}@{op}"] = sum(fa) / len(fa) if fa else None
            fr = [flags[d][op][i] for i in idx if recog[i]]
            m[f"TPR_recognized@{op}"] = sum(fr) / len(fr) if fr else None
        return m

    allidx = list(range(len(rows)))
    point = {d: metrics(d, allidx) for d in det}
    by_g = collections.defaultdict(list)
    for i in allidx:
        by_g[grp[i]].append(i)
    rng = random.Random(20261031)
    boots = [[i for g in (rng.choice(groups) for _ in groups) for i in by_g[g]] for _ in range(a.boot)]
    span = "PROBE:SPAN_ATTN11"
    generic = [d for d in det if d.startswith("PROBE:LAST_RESID_") or d in ("WHITEN:LAST_RESID_L11", "WHITEN:LAST_RESID_L31",
                                                                          "NATIVE_A", "NATIVE_M")]
    calib = {d: (point[d]["FPR@FV5"] is not None and point[d]["FPR@FV5"] <= 0.10) for d in det}
    cal_generic = [d for d in generic if calib[d]]
    G = max(cal_generic or ["NATIVE_A"], key=lambda d: (point[d]["TPR_missed@FV5"] or 0, d))
    surf = "PROBE:SPAN_RESID_emb"

    def ci(fn):
        v = sorted(x for x in (fn(b) for b in boots) if x is not None)
        return [round(v[int(0.025 * len(v))], 4), round(v[int(0.975 * len(v)) - 1], 4)] if v else None
    au = lambda d: (lambda b: metrics(d, b)["AUROC"])
    cis = {"AUROC_span": ci(au(span)), "AUROC_surface": ci(au(surf)),
           "AUROC_span_minus_surface": ci(lambda b: (lambda m1, m2: None if m1 is None or m2 is None else m1 - m2)(
               metrics(span, b)["AUROC"], metrics(surf, b)["AUROC"])),
           "TPR5_span_minus_G": ci(lambda b: (lambda m1, m2: None if m1 is None or m2 is None else m1 - m2)(
               metrics(span, b)["TPR_missed@FV5"], metrics(G, b)["TPR_missed@FV5"])),
           "TPR5_span": ci(lambda b: metrics(span, b)["TPR_missed@FV5"]),
           "TPR1_span": ci(lambda b: metrics(span, b)["TPR_missed@FV1"])}
    A_span, A_surf = point[span]["AUROC"], point[surf]["AUROC"]
    v1 = ("ENCODED_AT_L11" if A_span >= 0.90 and cis["AUROC_span"][0] >= 0.80 else
          "NOT_ENCODED_AT_L11" if A_span <= 0.70 else "PARTIAL")
    v1s = ("ABOVE_SURFACE" if A_span - A_surf >= 0.05 and cis["AUROC_span_minus_surface"][0] > 0 else
           "SURFACE_SUFFICES" if A_surf >= A_span - 0.02 else "SURFACE_UNRESOLVED")
    t_span, t_G = point[span]["TPR_missed@FV5"], point[G]["TPR_missed@FV5"]
    v2 = ("SPAN_MISCALIBRATED" if not calib[span] else
          "LOCATION_ADVANTAGE" if t_span - t_G >= 0.10 and cis["TPR5_span_minus_G"][0] > 0 else
          "GENERIC_MATCHES" if t_G >= t_span - 0.02 else "UNRESOLVED")
    if calib[span] and not cal_generic:
        v2 = v2 + "|NO_CALIBRATED_GENERIC"
    p1 = point[span]
    v3 = ("MONITOR_USEFUL" if (p1["TPR_missed@FV1"] or 0) >= 0.5 and all(
        (p1[f"FPR_{a_}@FV1"] or 0) <= 0.05 for a_ in ("old", "SA", "ROUND", "OUTSIDER")) else "NOT_USEFUL_AT_FV1")
    fp_groups = {op: sum(any(flags[span][op][i] for i in by_g[g] if benign[i]) for g in groups) for op in ("FV5", "FV1")}
    verdicts = {"V1_encoded": v1, "V1_surface": v1s, "V2_location": v2,
                "V2_novelty": {"LOCATION_ADVANTAGE": "NOVELTY_DELTA_SURVIVES",
                               "GENERIC_MATCHES": "INFRASTRUCTURE_VALIDATION_ONLY"}.get(v2.split("|")[0], "UNRESOLVED"),
                "V3_useful": v3, "best_generic": G,
                "calibrated": sorted(d for d in det if calib[d])}
    if not gate["pass"]:
        verdicts = {k: "INCONSISTENT" for k in verdicts}
    res = {"schema": "JEV_A461_MON_M18_ANALYSIS_V1", "fake_dry_run": a.fake_dry_run, "consistency_gate": gate,
           "verdicts": verdicts, "ci95_group_bootstrap": cis, "metrics": point,
           "span_monitor_false_positive_groups": {op: {"groups_with_fp": fp_groups[op], "of": len(groups),
                                                       "cp95_upper_group_rate": cp_upper(fp_groups[op], len(groups))}
                                                  for op in fp_groups},
           "counts": {"missed": sum(missed), "recognized": sum(recog), "benign": sum(benign),
                      "natural_false_veto_by_arm": dict(natural_fv), "groups": len(groups)},
           "layer_profile_AUROC": {k: {n: point[f"PROBE:{k}_{n}"]["AUROC"] for n in LAYERS} for k in ("SPAN_RESID", "LAST_RESID")},
           "thresholds": thr, "rules": D["preregistered_analysis"]}
    o = a.out.expanduser().resolve()
    o.mkdir(parents=True, exist_ok=False)
    (o / "m18_analysis.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"gate": gate, "verdicts": verdicts, "ci": cis, "counts": res["counts"],
                      "span": point[span], "best_generic": [G, point[G]], "surface": point[surf],
                      "layer_profile_AUROC": res["layer_profile_AUROC"],
                      "fp_groups": res["span_monitor_false_positive_groups"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
