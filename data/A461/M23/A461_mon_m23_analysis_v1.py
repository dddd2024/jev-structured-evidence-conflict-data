#!/usr/bin/env python3
"""A461-MON-M23 analysis (CPU, torch float64; frozen before any M23 forward). Answers V4 audit 02a2b73 P0-1.

Per model (kev-4B: parent M18; SecJev-0.8B: parent M22), refit the parent's probes EXACTLY as the parent analysis did
(same features, same probe spec, same labels: Gold reject_conflict over all parent rows; leave one source group out;
operating thresholds FV5 / FV1 from an inner leave-one-group-out over the training groups' BENIGN rows). Score the
held-out group's M23 rows: the 124 `new` replays and their 124 same-span TWINs (partner vote moved to a non-candidate
round; appended span byte-identical; Gold accept / wait).

Consistency gate (else every verdict INCONSISTENT): 248 rows; every M23 `new` row's logits and capture tensors equal the
parent's `new` row bitwise; every TWIN's emb-layer span mean equals its `new` row's; the refit reproduces the parent's
held-out AUROC for the primary detector.

Primary unit: the MISSED scenes (parent native action on `new` != reject_conflict). Per detector:
  AUROC_pair   = AUROC(new-missed scores vs their TWINs' scores)
  twin_flag@FV5 / @FV1 = share of those TWINs flagged at the parent's operating thresholds
  new_flag@FV5 = share of the new-missed rows flagged
  paired_frac  = share of missed scenes with score(new) > score(TWIN)
  group bootstrap (resample source groups) for AUROC_pair and twin_flag@FV5
Verdict per detector (rules fixed here):
  VALIDITY_TRACKED  AUROC_pair >= 0.80 and its CI lower bound >= 0.65 and twin_flag@FV5 <= 0.25
  ARM_SHORTCUT      AUROC_pair <= 0.65 or twin_flag@FV5 >= 0.50
  PARTIAL           otherwise
Primary detectors: PROBE:SPAN_ATTN11 (the preregistered M18 / M22 monitor) and PROBE:LAST_RESID_<last layer> (the
state the decision head reads). Reported: PROBE:SPAN_RESID_L11, the parent's best generic, and the surface probe.
Also reported: the native action on TWINs (false veto = reject_conflict on accept / wait Gold)."""
import argparse, collections, json, math, random, sys
from pathlib import Path

import torch

LAYERS = {"k": ["emb", "L3", "L7", "L11", "L15", "L19", "L23", "L27", "L31"],
          "s": ["emb", "L3", "L7", "L11", "L15", "L19", "L23"]}
LAST = {"k": "L31", "s": "L23"}
BEST_GENERIC = {"k": "PROBE:LAST_RESID_L19", "s": "PROBE:LAST_RESID_L11"}   # parent verdicts (M18 / M22)


def L(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def act(qs):
    a = next(q for q in qs if q["id"] == "certificate_action")
    return a["keys"][max(range(len(a["keys"])), key=lambda i: a["logits"][i])]


def fit_probe(X, y):   # the M18 / M22 probe spec, verbatim
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


def quant(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, math.ceil(q * len(v)) - 1)] if v else float("inf")


def auroc(pos, neg):
    if not pos or not neg:
        return None
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    i, rsum = 0, 0.0
    while i < len(allv):
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]:
            j += 1
        rsum += (i + j + 1) / 2 * sum(1 for t in allv[i:j] if t[1] == 1)
        i = j
    n1, n0 = len(pos), len(neg)
    return (rsum - n1 * (n1 + 1) / 2) / (n1 * n0)


def feats(rows, capdir, layers):
    F = collections.defaultdict(list)
    for r in rows:
        f = torch.load(Path(capdir) / r["capture_file"]["name"], weights_only=True)
        if f["names"] != layers:
            raise SystemExit("layer names differ")
        F["SPAN_ATTN11"].append(f["attn11_span"].double().mean(0))
        for i, n in enumerate(layers):
            F[f"SPAN_RESID_{n}"].append(f["span_mean"][i].double())
            F[f"LAST_RESID_{n}"].append(f["last"][i].double())
    return {k: torch.stack(v) for k, v in F.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["k", "s"], required=True)
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--captures", required=True, type=Path)
    ap.add_argument("--parent-raw", required=True, type=Path)
    ap.add_argument("--parent-captures", required=True, type=Path)
    ap.add_argument("--parent-analysis", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--fake-dry-run", action="store_true")
    a = ap.parse_args()
    k, layers = a.model, LAYERS[a.model]
    D = json.loads(a.design.read_text("utf8"))
    P, Mr = L(a.parent_raw), L(a.raw)
    pa = json.loads(a.parent_analysis.read_text("utf8"))
    pnew = {r["target_scene"]: r for r in P if r["target_arm"] == "new"}
    mnew = {r["target_scene"]: r for r in Mr if r["target_arm"] == "new"}
    mtw = {r["target_scene"]: r for r in Mr if r["target_arm"] == "TWIN"}
    gate = {"rows": len(Mr), "expected": D["total"], "new": len(mnew), "twin": len(mtw),
            "new_logits_bitwise_parent": sum(mnew[s]["questions"] == pnew[s]["questions"] for s in mnew if s in pnew)}
    eq_cap = same_span = 0
    for s in mnew:
        fm = torch.load(a.captures / mnew[s]["capture_file"]["name"], weights_only=True)
        fp = torch.load(a.parent_captures / pnew[s]["capture_file"]["name"], weights_only=True)
        eq_cap += all(torch.equal(fm[x], fp[x]) for x in ("span_mean", "last", "attn11_span"))
        if s in mtw:
            ft = torch.load(a.captures / mtw[s]["capture_file"]["name"], weights_only=True)
            same_span += bool(torch.equal(fm["span_mean"][0], ft["span_mean"][0]))
    gate.update(new_captures_bitwise_parent=eq_cap, twin_emb_span_equal=same_span)

    XP, XM = feats(P, a.parent_captures, layers), feats(Mr, a.captures, layers)
    yP = torch.tensor([r["gold_action"] == "reject_conflict" for r in P])
    aP = [act(r["questions"]) for r in P]
    armP = [r["target_arm"] for r in P]
    benignP = [armP[i] != "new" and aP[i] != "reject_conflict" for i in range(len(P))]
    gP, gM = [r["source_group"] for r in P], [r["source_group"] for r in Mr]
    groups = sorted(set(gP))
    dets = {"PROBE:SPAN_ATTN11": "SPAN_ATTN11", f"PROBE:LAST_RESID_{LAST[k]}": f"LAST_RESID_{LAST[k]}",
            "PROBE:SPAN_RESID_L11": "SPAN_RESID_L11", BEST_GENERIC[k]: BEST_GENERIC[k].split(":")[1],
            "PROBE:SPAN_RESID_emb": "SPAN_RESID_emb"}
    primary = ["PROBE:SPAN_ATTN11", f"PROBE:LAST_RESID_{LAST[k]}"]
    heldP = {d: [None] * len(P) for d in dets}
    heldM = {d: [None] * len(Mr) for d in dets}
    thr = {d: {} for d in dets}
    for g in groups:
        tr = [i for i in range(len(P)) if gP[i] != g]
        teP = [i for i in range(len(P)) if gP[i] == g]
        teM = [i for i in range(len(Mr)) if gM[i] == g]
        for d, fk in dets.items():
            f = fit_probe(XP[fk][tr], yP[tr])
            for i, v in zip(teP, f(XP[fk][teP]).tolist()):
                heldP[d][i] = v
            if teM:
                for i, v in zip(teM, f(XM[fk][teM]).tolist()):
                    heldM[d][i] = v
            inner = []
            for g2 in groups:
                if g2 == g:
                    continue
                te2 = [i for i in tr if gP[i] == g2 and benignP[i]]
                if te2:
                    tr2 = [i for i in tr if gP[i] != g2]
                    inner += fit_probe(XP[fk][tr2], yP[tr2])(XP[fk][te2]).tolist()
            thr[d][g] = {"FV5": quant(inner, 0.95), "FV1": quant(inner, 0.99)}
    missedP = [armP[i] == "new" and aP[i] != "reject_conflict" for i in range(len(P))]
    rep_auroc = {d: auroc([heldP[d][i] for i in range(len(P)) if missedP[i]],
                          [heldP[d][i] for i in range(len(P)) if benignP[i]]) for d in dets}
    pa_m = pa.get("metrics", {})
    gate["parent_auroc_reproduced"] = {d: (pa_m.get(d, {}).get("AUROC") is not None
                                          and abs(rep_auroc[d] - pa_m[d]["AUROC"]) < 1e-9) for d in dets}
    gate["pass"] = (gate["rows"] == gate["expected"] == 248 and gate["new"] == gate["twin"] == 124
                    and gate["new_logits_bitwise_parent"] == 124 and eq_cap == 124 and same_span == 124
                    and all(gate["parent_auroc_reproduced"][d] for d in primary))

    idxM = {(Mr[i]["target_scene"], Mr[i]["target_arm"]): i for i in range(len(Mr))}
    missed_sc = sorted(s for s in pnew if act(pnew[s]["questions"]) != "reject_conflict")
    grp_sc = {s: pnew[s]["source_group"] for s in pnew}

    def metrics(d, scenes):
        sn = [heldM[d][idxM[(s, "new")]] for s in scenes]
        st = [heldM[d][idxM[(s, "TWIN")]] for s in scenes]
        flag = lambda s, arm, op: heldM[d][idxM[(s, arm)]] > thr[d][grp_sc[s]][op]
        n = len(scenes)
        return {"scenes": n, "AUROC_pair": auroc(sn, st),
                "paired_frac_new_gt_twin": sum(x > y for x, y in zip(sn, st)) / n if n else None,
                "median_paired_diff": sorted(x - y for x, y in zip(sn, st))[n // 2] if n else None,
                **{f"twin_flag@{op}": sum(flag(s, "TWIN", op) for s in scenes) / n if n else None for op in ("FV5", "FV1")},
                **{f"new_flag@{op}": sum(flag(s, "new", op) for s in scenes) / n if n else None for op in ("FV5", "FV1")},
                "AUROC_twin_vs_parent_benign": auroc(st, [heldP[d][i] for i in range(len(P)) if benignP[i]])}

    by_g = collections.defaultdict(list)
    for s in missed_sc:
        by_g[grp_sc[s]].append(s)
    gl = sorted(by_g)
    rng = random.Random(20261101)
    boots = [[s for g in (rng.choice(gl) for _ in gl) for s in by_g[g]] for _ in range(a.boot)]

    def ci(fn):
        v = sorted(x for x in (fn(b) for b in boots) if x is not None)
        return [round(v[int(0.025 * len(v))], 4), round(v[int(0.975 * len(v)) - 1], 4)] if v else None
    res_det, verdicts = {}, {}
    for d in dets:
        mm = metrics(d, missed_sc)
        mm["ci_AUROC_pair"] = ci(lambda b, d=d: metrics(d, b)["AUROC_pair"])
        mm["ci_twin_flag@FV5"] = ci(lambda b, d=d: metrics(d, b)["twin_flag@FV5"])
        mm["all_scenes"] = metrics(d, sorted(pnew))
        res_det[d] = mm
        A, lo, tf = mm["AUROC_pair"], (mm["ci_AUROC_pair"] or [None])[0], mm["twin_flag@FV5"]
        verdicts[d] = ("UNDEFINED" if A is None or tf is None else
                       "VALIDITY_TRACKED" if A >= 0.80 and lo is not None and lo >= 0.65 and tf <= 0.25 else
                       "ARM_SHORTCUT" if A <= 0.65 or tf >= 0.50 else "PARTIAL")
    if not gate["pass"]:
        verdicts = {d: "INCONSISTENT" for d in verdicts}
    nat = collections.Counter((mtw[s]["gold_action"], act(mtw[s]["questions"])) for s in mtw)
    native = {"twin_by_gold_pred": {f"{g}->{p}": n for (g, p), n in sorted(nat.items())},
              "twin_false_veto": sum(n for (g, p), n in nat.items() if p == "reject_conflict"),
              "new_rejected": sum(act(mnew[s]["questions"]) == "reject_conflict" for s in mnew),
              "twin_rejected_where_new_missed": sum(act(mtw[s]["questions"]) == "reject_conflict" for s in missed_sc),
              "twin_rejected_where_new_recognized": sum(act(mtw[s]["questions"]) == "reject_conflict"
                                                        for s in pnew if s not in missed_sc)}
    res = {"schema": "JEV_A461_MON_M23_ANALYSIS_V1", "model": k, "fake_dry_run": a.fake_dry_run,
           "consistency_gate": gate, "verdicts": verdicts, "primary": primary, "detectors": res_det,
           "missed_scenes": len(missed_sc), "missed_groups": len(gl), "native": native,
           "refit_parent_auroc": {d: rep_auroc[d] for d in dets},
           "rules": {"verdict": "VALIDITY_TRACKED iff AUROC_pair >= 0.80, CI lower >= 0.65 and twin_flag@FV5 <= 0.25; "
                                "ARM_SHORTCUT iff AUROC_pair <= 0.65 or twin_flag@FV5 >= 0.50; else PARTIAL; on MISSED scenes",
                     "interpretation_fixed_in_advance":
                         "VALIDITY_TRACKED on both primary detectors: M-E may say the separability tracks conflict validity "
                         "in context (same-span twins), not only the arm. ARM_SHORTCUT: M-E stays narrowed and the paper says "
                         "the separability is explained by the appended item's form / arm. PARTIAL or mixed: reported as is; "
                         "M-E stays narrowed with the partial result stated."}}
    o = a.out.expanduser().resolve()
    o.mkdir(parents=True, exist_ok=False)
    (o / f"m23{k}_analysis.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"gate": gate, "verdicts": verdicts, "native": native,
                      "primary": {d: {x: res_det[d][x] for x in ("AUROC_pair", "ci_AUROC_pair", "twin_flag@FV5", "new_flag@FV5",
                                                                  "paired_frac_new_gt_twin")} for d in primary}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
