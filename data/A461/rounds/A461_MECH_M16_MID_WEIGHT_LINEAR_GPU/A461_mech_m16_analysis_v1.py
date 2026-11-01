#!/usr/bin/env python3
"""A461-MECH-M16 R1 analysis: applies the rules frozen in m16_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm, the meanD_host arm with the M6 pooled-donor arm, abc_s0375 / csc29_s0375 on the 6
subset cells with the M15 rows of the same name (which equal M14's abc_s0375 bitwise) and mw0_s0375 with this run's
abc_s0375 (pinned raw rows, bitwise). The w family reads w = 0 from the pinned M14 abc_<s> rows and w = 1 from the
pinned M15 csc29_<s> rows; the linear predictions are read from the design, frozen before the run. Derived from the
M15 analysis (83d1c5a4)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "c061686a5a3271e2b06f418f213bce81fa3ff05a"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M14_RAW = "d2ac9f4221728d309300cbf617385ad79925eb0b"
BLOB_M15_RAW = "b6807b136acd3a00944705fae50b5d910946cf16"
VERDICTS = ("lin_by_host", "w_linear", "ws_by_host", "wc_by_host", "dissoc_by_host")
SUBSET = ("abc_s0375", "csc29_s0375", "mw0_s0375")
SIZES = ((0.25, "_s025"), (0.375, "_s0375"), (0.5, "_s05"))
WS = ((-1.0, "M16", "mwm1{}"), (-0.5, "M16", "mwm05{}"), (0.0, "M14", "abc{}"), (0.5, "M16", "mwp05{}"),
      (1.0, "M15", "csc29{}"), (1.5, "M16", "mwp15{}"))
TEST_W = (-1.0, -0.5, 0.5, 1.5)
M14_REF = tuple(f"abc{x}" for _s, x in SIZES)
M15_REF = ("full", "meanD_host", "abc_s0375") + tuple(f"csc29{x}" for _s, x in SIZES)


def trend(v, pre):
    if len(set(v)) == 1:
        return f"{pre}_NO_EFFECT"
    if all(x >= y for x, y in zip(v, v[1:])) and v[0] > v[-1]:
        return f"{pre}_OPPOSES"
    if all(x <= y for x, y in zip(v, v[1:])) and v[0] < v[-1]:
        return f"{pre}_SUPPORTS"
    k = v.index(max(v))
    if (all(x <= y for x, y in zip(v[:k + 1], v[1:k + 1])) and all(x >= y for x, y in zip(v[k:], v[k + 1:]))
            and v[0] < v[k] and v[-1] < v[k]):
        return f"{pre}_PEAKED"
    return f"{pre}_MIXED"


def ma(qs):
    q = {x["id"]: x for x in qs}
    c, a = q["conflicting_vote"], q["certificate_action"]
    M = c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]
    L = dict(zip(a["keys"], a["logits"]))
    A = L["reject_conflict"] - max(L["accept"], L["wait"])
    return M, A, (M > 0 and A > 0)


def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def r2(obs, pred):
    mu = statistics.fmean(obs)
    ss = sum((o - mu) ** 2 for o in obs)
    return round(1 - sum((o - p) ** 2 for o, p in zip(obs, pred)) / ss, 4) if ss > 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m6-raw", required=True, type=Path)
    ap.add_argument("--m14-raw", required=True, type=Path)
    ap.add_argument("--m15-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 / M14 / M15 baseline check")
    a = ap.parse_args()
    for p_, b_, n_ in ((a.design, BLOB_DESIGN, "design"), (a.m3_raw, BLOB_M3_RAW, "M3 raw"),
                       (a.m6_raw, BLOB_M6_RAW, "M6 raw"), (a.m14_raw, BLOB_M14_RAW, "M14 raw"),
                       (a.m15_raw, BLOB_M15_RAW, "M15 raw")):
        if blob(p_) != b_:
            raise SystemExit(f"{n_} pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    preds = design["linear_predictions"]
    raw, m3, m6, m14, m15 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw), jsonl(a.m14_raw), jsonl(a.m15_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    hb = lambda rows_: {x["target_scene"]: ma(x["questions"])[0] for x in rows_
                        if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    base, m3base, m14base, m15base = hb(raw), hb(m3), hb(m14), hb(m15)
    if (base != m3base or base != m14base or base != m15base) and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3 / M14 / M15")

    def load(rows_, base_, names_=None):   # arm -> (d, h, src) -> (dM, J, M, A, questions)
        out_ = collections.defaultdict(dict)
        for x in rows_:
            if x["patch"] and (names_ is None or x["patch"]["arm"] in names_):
                M, A, J = ma(x["questions"])
                out_[x["patch"]["arm"]][(x["donor"], x["host"], x["source_kind"])] = (
                    M - base_[x["host"]], J, M, A, x["questions"])
        return out_
    arm = load(raw, base)
    m3r, m6r = load(m3, m3base, ("all",)), load(m6, m3base, ("meanD_host",))
    m14r, m15r = load(m14, m14base, M14_REF), load(m15, m15base, M15_REF)
    dnorm, wstat = collections.defaultdict(dict), collections.defaultdict(set)
    for x in raw:
        if x["patch"]:
            dnorm[x["patch"]["arm"]][(x["donor"], x["host"], x["source_kind"])] = x["span_stats"]["delta_norm_mean"]
            if x["patch"].get("shift_pos_weight"):
                st_ = x["alpha_stats"]
                wstat[x["patch"]["arm"]].add((st_["shift_weight_min"], st_["shift_weight_max"],
                                              tuple(st_["shift_weight_listed"])))
    allnames = [n for n, _op, _cl, _ex in design["arms"]]
    names = [n for n in allnames if n not in SUBSET]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(allnames)
            or any(len(arm[n]) != (12 if n in SUBSET else 208) for n in allnames)
            or len(m3r["all"]) != 208 or len(m6r["meanD_host"]) != 208
            or any(len(m14r[n]) != 208 for n in M14_REF)
            or any(len(m15r[n]) != (12 if n == "abc_s0375" else 208) for n in M15_REF)
            or sorted(preds) != sorted(n for n in names if n.startswith("mw"))):
        raise SystemExit("cell census")
    src = {"M16": arm, "M14": m14r, "M15": m15r}

    def stats(v, cs):
        S = sum(v[(d, h, "main")][1] and not v[(d, h, "round")][1] for d, h in cs)
        gt = [v[(d, h, "main")][0] > v[(d, h, "round")][0] for d, h in cs]
        g = collections.defaultdict(list)
        for (d, h), b in zip(cs, gt):
            g[gd[d]].append(b)
        maj = sum(sum(b) * 2 > len(b) for b in g.values())
        frac = sum(gt) / len(gt)
        return {"S": S, "J_main": sum(v[(d, h, "main")][1] for d, h in cs),
                "J_round": sum(v[(d, h, "round")][1] for d, h in cs),
                "frac_main_gt_round": round(frac, 4), "groups_majority": maj, "n_cells": len(cs),
                "SPEC": frac >= 0.75 and maj >= 10,
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    pk = lambda d, h, sk: f"{d[:12]}|{h[:12]}|{sk}"
    Jp = lambda v: v[0] > 0 and v[1] > 0

    def attrib(v, cs, pr=None):
        get = (lambda d, h, sk: (v[(d, h, sk)][2], v[(d, h, sk)][3])) if pr is None else (lambda d, h, sk: tuple(pr[pk(d, h, sk)]))
        mj = [(d, h) for d, h in cs if Jp(get(d, h, "main"))]
        return {"main_J": len(mj), "round_J_among_main_J": sum(Jp(get(d, h, "round")) for d, h in mj),
                "S": sum(not Jp(get(d, h, "round")) for d, h in mj),
                "round_M_pos": sum(get(d, h, "round")[0] > 0 for d, h in cs),
                "round_A_pos": sum(get(d, h, "round")[1] > 0 for d, h in cs),
                "main_median_M": round(statistics.median(get(d, h, "main")[0] for d, h in cs), 4),
                "main_median_A": round(statistics.median(get(d, h, "main")[1] for d, h in cs), 4),
                "round_median_M": round(statistics.median(get(d, h, "round")[0] for d, h in cs), 4),
                "round_median_A": round(statistics.median(get(d, h, "round")[1] for d, h in cs), 4)}

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        SUF = {n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"] for n in names}
        C = {n: T[n]["median_dM_contrast"] for n in names}
        resp = []
        for h in hosts:
            hc = [c for c in cs if c[1] == h]
            if h[:8] in design["responsive_hosts"] and hc:
                resp.append((h, hc))
        lin, ws, wc, dis, detail = {}, {}, {}, {}, {}
        for h, hc in resp:
            agree = {"all": [], "interp": [], "extrap": []}
            dS, eM, eA, oM, oA, pM, pA = {}, [], [], [], [], [], []
            fam, att = {}, {}
            for s_, x in SIZES:
                Sv, Cv = [], []
                for w_, r_, t_ in WS:
                    n = t_.format(x)
                    st_ = stats(src[r_][n], hc)
                    Sv.append(st_["S"])
                    Cv.append(st_["median_dM_contrast"])
                    att[f"{w_:+g}{x}"] = {"observed": attrib(src[r_][n], hc)}
                    if w_ in TEST_W:
                        pr = preds[n]
                        att[f"{w_:+g}{x}"]["predicted"] = attrib(None, hc, pr)
                        Sp = att[f"{w_:+g}{x}"]["predicted"]["S"]
                        dS[f"{w_:+g}{x}"] = st_["S"] - Sp
                        for d, hh in hc:
                            for sk in ("main", "round"):
                                ob = src[r_][n][(d, hh, sk)]
                                pv = pr[pk(d, hh, sk)]
                                ag = ob[1] == Jp(pv)
                                agree["all"].append(ag)
                                agree["interp" if w_ == 0.5 else "extrap"].append(ag)
                                oM.append(ob[2]); oA.append(ob[3]); pM.append(pv[0]); pA.append(pv[1])
                                eM.append(abs(ob[2] - pv[0])); eA.append(abs(ob[3] - pv[1]))
                fam[x] = {"S": Sv, "C": Cv, "WS": trend(Sv, "WS"), "WC": trend(Cv, "WC")}
            ag = {k: round(sum(v) / len(v), 4) for k, v in agree.items()}
            mx = max(abs(v) for v in dS.values())
            mxi = max(abs(v) for k, v in dS.items() if k.startswith("+0.5"))
            mxe = max(abs(v) for k, v in dS.items() if not k.startswith("+0.5"))
            lin[h[:8]] = ("LINEAR_HOLDS" if ag["all"] >= 0.95 and mx <= 1
                          else "LINEAR_FAILS" if ag["all"] < 0.90 or mx >= 3 else "LINEAR_APPROX")
            ws[h[:8]] = {x: fam[x]["WS"] for _s, x in SIZES}
            wc[h[:8]] = {x: fam[x]["WC"] for _s, x in SIZES}
            infs = [x for _s, x in SIZES if fam[x]["WS"] != "WS_NO_EFFECT"]
            dis[h[:8]] = ("UNINFORMATIVE" if not infs
                          else "S_C_DISSOCIATE" if all(fam[x]["WC"] == "WC_SUPPORTS"
                                                       and fam[x]["WS"] in ("WS_OPPOSES", "WS_PEAKED") for x in infs)
                          else "S_C_ALIGNED" if all(fam[x]["WS"][3:] == fam[x]["WC"][3:] in ("SUPPORTS", "OPPOSES")
                                                    for x in infs)
                          else "S_C_MIXED")
            detail[h[:8]] = {"family": fam, "agree": ag, "dS": dS, "max_abs_dS": mx, "max_abs_dS_interp": mxi,
                             "max_abs_dS_extrap": mxe, "R2_M": r2(oM, pM), "R2_A": r2(oA, pA),
                             "median_abs_err_M": round(statistics.median(eM), 4),
                             "median_abs_err_A": round(statistics.median(eA), 4), "attribution": att}
        ls = list(lin.values())
        wl = ("W_LINEAR_NO_RESPONSIVE_HOST" if not ls else "W_LINEAR_HOLDS" if all(v == "LINEAR_HOLDS" for v in ls)
              else "W_LINEAR_FAILS" if any(v == "LINEAR_FAILS" for v in ls) else "W_LINEAR_APPROX")
        fmt = lambda d_: ",".join(f"{h}={v}" for h, v in sorted(d_.items()))
        fmt2 = lambda d_: ",".join(f"{h}=" + "/".join(f"{x[1:]}:{v[x][3:]}" for _s, x in SIZES) for h, v in sorted(d_.items()))
        return T, {"SUF": SUF, "C": C, "responsive_hosts": [h[:8] for h, _ in resp],
                   "lin_by_host": "LIN_BY_HOST:" + fmt(lin), "w_linear": wl,
                   "ws_by_host": "WS_BY_HOST:" + fmt2(ws), "wc_by_host": "WC_BY_HOST:" + fmt2(wc),
                   "dissoc_by_host": "DISSOC_BY_HOST:" + fmt(dis), "detail": detail}

    T, V = verdict(cells)
    S3 = stats(m3r["all"], cells)["S"]
    bw3 = sum(arm["full"][k][4] == m3r["all"][k][4] for k in m3r["all"])
    bw6 = sum(arm["meanD_host"][k][4] == m6r["meanD_host"][k][4] for k in m6r["meanD_host"])
    bw15 = {n: sum(arm[n][k][4] == m15r[n][k][4] for k in arm[n]) for n in ("abc_s0375", "csc29_s0375")}
    bw14 = sum(arm["abc_s0375"][k][4] == m14r["abc_s0375"][k][4] for k in arm["abc_s0375"])
    bwmw0 = sum(arm["mw0_s0375"][k][4] == arm["abc_s0375"][k][4] for k in arm["mw0_s0375"])
    wok = all(wstat[n] == {(min(w_, 1.0), max(w_, 1.0), (w_,))} for n, _op, _cl, ex in design["arms"]
              for w_ in [ex.get("mw")] if w_ is not None)
    gate = {"S_full": T["full"]["S"], "S_M3_all": S3, "full_rows_bitwise_eq_M3": bw3,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bw6,
            "subset_rows_bitwise_eq_M15": bw15, "abc_s0375_rows_bitwise_eq_M14": bw14,
            "mw0_rows_bitwise_eq_abc_s0375": bwmw0, "shift_weights_as_planned": wok,
            "pass": (T["full"]["S"] == S3 == 51 and bw3 == 208 and T["meanD_host"]["S"] == 39 and bw6 == 208
                     and all(bw15[n] == len(arm[n]) == 12 for n in bw15) and bw14 == 12 and bwmw0 == 12 and wok)}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6_M14_M15") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS}
        logo[g]["agree"] = {h: v["agree"]["all"] for h, v in vv["detail"].items()}
        logo[g]["max_abs_dS"] = {h: v["max_abs_dS"] for h, v in vv["detail"].items()}
        logo[g]["SUF"] = sorted(n for n, b in vv["SUF"].items() if b)
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
    per_host_C = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["median_dM_contrast"] for n in names}
                  for h in hosts}
    size = {n: round(statistics.median(dnorm[n][k] / dnorm["full"][k] for k in dnorm[n]), 4) for n in allnames}

    res = {"schema": "JEV_A461_MECH_M16_ANALYSIS_V1", "table": T, "consistency_gate": gate,
           "rules_applied": V, "verdicts": final, "leave_one_donor_group_out": logo, "per_host_S": per_host,
           "per_host_C": per_host_C, "median_change_norm_rel_full": size,
           "predicted_S_by_host": design["predicted_S_by_host"], "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m16_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final,
                      "detail": {h: {k: v[k] for k in ("family", "agree", "dS", "max_abs_dS", "R2_M", "R2_A",
                                                       "median_abs_err_M", "median_abs_err_A")}
                                 for h, v in V["detail"].items()},
                      "S": {n: T[n]["S"] for n in names}, "SPEC": {n: T[n]["SPEC"] for n in names},
                      "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
