#!/usr/bin/env python3
"""A461-MECH-M15 R1 analysis: applies the rules frozen in m15_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm, the meanD_host arm with the M6 pooled-donor arm and the 4 M14 replay arms on the 6
subset cells with the M14 rows of the same name (pinned raw rows, bitwise). The Q1 split reads AB29 from the pinned
M14 rows and ALL30 from the pinned M13 rows; the tilt dose and the 24-null test read lam -3, -1, 0, +1, +3 and nulls
1-8 from the pinned M14 rows. Derived from the M14 analysis (4dd14bbf)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "4288440cb835cb1e36211c949878428a2dba2ad2"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M13_RAW = "cdbf677bd2b89d487045b104af040f2e39fcf5a3"
BLOB_M14_RAW = "d2ac9f4221728d309300cbf617385ad79925eb0b"
VERDICTS = ("q1_smin_by_host", "c30_by_host", "loc_by_host", "q1_gain", "dose_s0437", "dose_by_host",
            "null24_by_host", "null24_s", "null24_c", "round_a_rank_264c")
SUBSET = ("abc_s0375", "rem_p3_s0437", "rnull3_s0437_1", "cs_s0312")
SIZES = ((0.25, "_s025"), (0.375, "_s0375"), (0.5, "_s05"))
M13_REF = ("cs1",) + tuple(f"cs{x}" for _s, x in SIZES)
NULL14 = tuple(f"rnull3_s0437_{i}" for i in range(1, 9))
NULL15 = tuple(f"rnull3_s0437_{i}" for i in range(9, 25))
M14_REF = (tuple(f"abc{x}" for _s, x in SIZES) + ("rem_m3_s0437", "rem_m1_s0437", "cs_s0437", "rem_p1_s0437",
                                                  "rem_p3_s0437", "cs_s0312") + NULL14)
DOSE = (("m3", -3, "M14", "rem_m3_s0437"), ("m2", -2, "M15", "rem_m2_s0437"), ("m1", -1, "M14", "rem_m1_s0437"),
        ("0", 0, "M14", "cs_s0437"), ("p1", 1, "M14", "rem_p1_s0437"), ("p2", 2, "M15", "rem_p2_s0437"),
        ("p3", 3, "M14", "rem_p3_s0437"))
INFORMATIVE_Q1 = ("264c458d", "4bcbaf15")   # the hosts where M14 found SMIN(AB29) < SMIN(ALL30) (frozen)
MAJ = 7          # host S >= 7 of 13 cells: the per-host threshold rule (frozen)
NONE = 1.0       # SMIN of a host that no s in 1/4, 3/8, 1/2 repairs, ordered above 1/2


def mono(v, pre):
    if len(set(v)) == 1:
        return f"{pre}_NO_EFFECT"
    if all(x >= y for x, y in zip(v, v[1:])) and v[0] > v[-1]:
        return f"{pre}_OPPOSES"
    if all(x <= y for x, y in zip(v, v[1:])) and v[0] < v[-1]:
        return f"{pre}_SUPPORTS"
    return f"{pre}_MIXED"


def pooled(flags, pre, empty):
    fs = set(flags)
    beyond = fs & {"HARM_BEYOND_NULL24", "REMOVAL_BEYOND_NULL24"}
    rev = fs & {"LESS_HARM_THAN_NULL24", "REMOVAL_BELOW_NULL24"}
    return (empty if not flags else f"{pre}_NOT_SPECIFIC" if fs == {"AT"} else f"{pre}_SPECIFIC" if beyond and not rev
            else f"{pre}_REVERSED" if rev and not beyond else f"{pre}_MIXED")


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m6-raw", required=True, type=Path)
    ap.add_argument("--m13-raw", required=True, type=Path)
    ap.add_argument("--m14-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 / M13 / M14 baseline check")
    a = ap.parse_args()
    for p_, b_, n_ in ((a.design, BLOB_DESIGN, "design"), (a.m3_raw, BLOB_M3_RAW, "M3 raw"),
                       (a.m6_raw, BLOB_M6_RAW, "M6 raw"), (a.m13_raw, BLOB_M13_RAW, "M13 raw"),
                       (a.m14_raw, BLOB_M14_RAW, "M14 raw")):
        if blob(p_) != b_:
            raise SystemExit(f"{n_} pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m6, m13, m14 = (jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw), jsonl(a.m13_raw),
                             jsonl(a.m14_raw))
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    hb = lambda rows_: {x["target_scene"]: ma(x["questions"])[0] for x in rows_
                        if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    base, m3base, m13base, m14base = hb(raw), hb(m3), hb(m13), hb(m14)
    if (base != m3base or base != m13base or base != m14base) and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3 / M13 / M14")

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
    m13r, m14r = load(m13, m13base, M13_REF), load(m14, m14base, M14_REF)
    cstat, dnorm = collections.defaultdict(list), collections.defaultdict(dict)
    for x in raw:
        if x["patch"]:
            dnorm[x["patch"]["arm"]][(x["donor"], x["host"], x["source_kind"])] = x["span_stats"]["delta_norm_mean"]
            if x.get("contrast_stats"):
                cstat[x["patch"]["arm"]].append(x["contrast_stats"])
    allnames = [n for n, _op, _cl, _ex in design["arms"]]
    names = [n for n in allnames if n not in SUBSET]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(allnames)
            or any(len(arm[n]) != (12 if n in SUBSET else 208) for n in allnames)
            or len(m3r["all"]) != 208 or len(m6r["meanD_host"]) != 208
            or any(len(m13r[n]) != 208 for n in M13_REF) or any(len(m14r[n]) != 208 for n in M14_REF)):
        raise SystemExit("cell census")
    src = {"M15": arm, "M14": m14r, "M13": m13r}

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

    def action(v, cs):
        return {"main_J": sum(v[(d, h, "main")][1] for d, h in cs),
                "round_M_pos": sum(v[(d, h, "round")][2] > 0 for d, h in cs),
                "round_A_pos": sum(v[(d, h, "round")][3] > 0 for d, h in cs),
                "round_median_A": round(statistics.median(v[(d, h, "round")][3] for d, h in cs), 4)}

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        SUF = {n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"] for n in names}
        C = {n: T[n]["median_dM_contrast"] for n in names}
        hs = lambda run, n, hc: stats(src[run][n], hc)["S"]
        hcC = lambda run, n, hc: stats(src[run][n], hc)["median_dM_contrast"]
        resp = []
        for h in hosts:
            hc = [c for c in cs if c[1] == h]
            if hc and hs("M13", "cs1", hc) * 2 > len(hc):
                resp.append((h, hc))
        # Q1 split: 2 x 2 per host (shift AB / all x c_30 off / on), SMIN over s in 1/4, 3/8, 1/2
        fam = {"AB29": ("M14", "abc{}"), "AB30": ("M15", "abc30{}"), "ALL29": ("M15", "csc29{}"),
               "ALL30": ("M13", "cs{}")}
        smin = lambda f: min([s_ for s_, n in f if n >= MAJ] or [NONE])
        sg = lambda x, y: (x > y) - (x < y)
        q1, c30h, loch = {}, {}, {}
        for h, hc in resp:
            Sv = {k: [hs(r_, t_.format(x), hc) for _s, x in SIZES] for k, (r_, t_) in fam.items()}
            sm = {k: smin([(s_, v_) for (s_, _x), v_ in zip(SIZES, Sv[k])]) for k in fam}
            c_ab, c_all = sg(sm["AB30"], sm["AB29"]), sg(sm["ALL30"], sm["ALL29"])
            l29, l30 = sg(sm["ALL29"], sm["AB29"]), sg(sm["ALL30"], sm["AB30"])
            c30h[h[:8]] = ("C30_COSTS" if c_ab > 0 and c_all > 0 else "C30_COSTS_UNDER_AB" if c_ab > 0 and c_all == 0
                           else "C30_COSTS_UNDER_ALL" if c_all > 0 and c_ab == 0
                           else "C30_NO_COST" if c_ab == 0 and c_all == 0 else "C30_MIXED")
            loch[h[:8]] = ("AB_LOWERS" if l29 > 0 and l30 > 0 else "AB_LOWERS_WITHOUT_C30" if l29 > 0 and l30 == 0
                           else "AB_LOWERS_WITH_C30" if l30 > 0 and l29 == 0
                           else "LOC_NO_EFFECT" if l29 == 0 and l30 == 0 else "LOC_MIXED")
            q1[h[:8]] = {"S": Sv, "SMIN": sm,
                         "C": {k: [hcC(r_, t_.format(x), hc) for _s, x in SIZES] for k, (r_, t_) in fam.items()}}
        fmt = lambda x: "NONE" if x == NONE else f"{x:g}"
        smh = "Q1_SMIN_BY_HOST:" + ",".join(f"{h}=" + "/".join(f"{k}:{fmt(v['SMIN'][k])}" for k in fam)
                                           for h, v in sorted(q1.items()))
        inf = [h for h in INFORMATIVE_Q1 if h in c30h]
        c30c = lambda h: c30h[h].startswith("C30_COSTS")
        locl = lambda h: loch[h].startswith("AB_LOWERS")
        gain = ("Q1_GAIN_NO_INFORMATIVE_HOST" if not inf
                else "Q1_GAIN_C30_ONLY" if all(c30c(h) and loch[h] == "LOC_NO_EFFECT" for h in inf)
                else "Q1_GAIN_LOC_ONLY" if all(locl(h) and c30h[h] == "C30_NO_COST" for h in inf)
                else "Q1_GAIN_BOTH" if all(c30c(h) and locl(h) for h in inf) else "Q1_GAIN_MIXED")
        # tilt dose at s 7/16 over lam -3 .. +3
        dS = [sum(src[r_][n][(d, h, "main")][1] and not src[r_][n][(d, h, "round")][1] for d, h in cs)
              for _t, _l, r_, n in DOSE]
        dC = [stats(src[r_][n], cs)["median_dM_contrast"] for _t, _l, r_, n in DOSE]
        dbh = {h[:8]: {"S": [hs(r_, n, hc) for _t, _l, r_, n in DOSE], "C": [hcC(r_, n, hc) for _t, _l, r_, n in DOSE]}
               for h, hc in resp}
        for v in dbh.values():
            v["rule"] = mono(v["S"], "DOSE")
        dbs = "DOSE_BY_HOST:" + ",".join(f"{h}={v['rule']}" for h, v in sorted(dbh.items()))
        # 24 nulls
        nulls = [("M14", n) for n in NULL14] + [("M15", n) for n in NULL15]
        detail, fS, fC, act = {}, [], [], {}
        for h, hc in resp:
            N = [hs(r_, n, hc) for r_, n in nulls]
            NC = [hcC(r_, n, hc) for r_, n in nulls]
            add, rmv = hs("M14", "rem_p3_s0437", hc), hs("M14", "rem_m3_s0437", hc)
            addc, rmvc = hcC("M14", "rem_p3_s0437", hc), hcC("M14", "rem_m3_s0437", hc)
            allv = N + [add, rmv]
            inf_ = not (all(v == 0 for v in allv) or all(v == len(hc) for v in allv))
            va = "HARM_BEYOND_NULL24" if add < min(N) else "LESS_HARM_THAN_NULL24" if add > max(N) else "AT"
            vr = "REMOVAL_BEYOND_NULL24" if rmv > max(N) else "REMOVAL_BELOW_NULL24" if rmv < min(N) else "AT"
            vac = "HARM_BEYOND_NULL24" if addc < min(NC) else "LESS_HARM_THAN_NULL24" if addc > max(NC) else "AT"
            vrc = "REMOVAL_BEYOND_NULL24" if rmvc > max(NC) else "REMOVAL_BELOW_NULL24" if rmvc < min(NC) else "AT"
            if inf_:
                fS += [va, vr]
            fC += [vac, vrc]
            detail[h[:8]] = {"n_cells": len(hc), "informative_S": inf_, "null_S": N, "add_S": add, "remove_S": rmv,
                             "add": va if inf_ else "UNINFORMATIVE", "remove": vr if inf_ else "UNINFORMATIVE",
                             "rank_nulls_le_add": sum(v <= add for v in N), "rank_nulls_ge_remove": sum(v >= rmv for v in N),
                             "null_C": NC, "add_C": addc, "remove_C": rmvc, "add_by_C": vac, "remove_by_C": vrc,
                             "rank_nullsC_le_add": sum(v <= addc for v in NC),
                             "rank_nullsC_ge_remove": sum(v >= rmvc for v in NC)}
            act[h[:8]] = {**{f"lam_{t_}": action(src[r_][n], hc) for t_, _l, r_, n in DOSE},
                          **{n: action(src[r_][n], hc) for r_, n in nulls}}
        nbh = "NULL24_BY_HOST:" + ",".join(f"{h}=S {v['add']}/{v['remove']}|C {v['add_by_C']}/{v['remove_by_C']}"
                                          for h, v in sorted(detail.items()))
        if "264c458d" in act:
            ac = act["264c458d"]
            ra_ = [ac[n]["round_A_pos"] for _r, n in nulls]
            rank = (f"ROUND_A_RANK_264C:ge_add={sum(v >= ac['lam_p3']['round_A_pos'] for v in ra_)}/24,"
                    f"le_remove={sum(v <= ac['lam_m3']['round_A_pos'] for v in ra_)}/24")
        else:
            rank = "ROUND_A_RANK_264C:NOT_RESPONSIVE"
        return T, {"SUF": SUF, "C": C, "responsive_hosts": [h[:8] for h, _ in resp],
                   "q1_smin_by_host": smh, "q1_detail": q1,
                   "c30_by_host": "C30_BY_HOST:" + ",".join(f"{h}={v}" for h, v in sorted(c30h.items())),
                   "loc_by_host": "LOC_BY_HOST:" + ",".join(f"{h}={v}" for h, v in sorted(loch.items())),
                   "q1_gain": gain, "dose_s0437": mono(dS, "DOSE"), "dose_S": dS, "dose_C": dC,
                   "dose_by_host": dbs, "dose_by_host_detail": dbh,
                   "null24_by_host": nbh, "null24_detail": detail,
                   "null24_s": pooled(fS, "NULL24_S_DIRECTION", "NULL24_S_DIRECTION_UNINFORMATIVE"),
                   "null24_c": pooled(fC, "NULL24_C_DIRECTION", "NULL24_C_DIRECTION_NO_RESPONSIVE_HOST"),
                   "round_action": act, "round_a_rank_264c": rank}

    T, V = verdict(cells)
    S3 = stats(m3r["all"], cells)["S"]
    bw3 = sum(arm["full"][k][4] == m3r["all"][k][4] for k in m3r["all"])
    bw6 = sum(arm["meanD_host"][k][4] == m6r["meanD_host"][k][4] for k in m6r["meanD_host"])
    m14sub = load(m14, m14base, SUBSET)
    bw14 = {n: sum(arm[n][k][4] == m14sub[n][k][4] for k in arm[n]) for n in SUBSET}
    gate = {"S_full": T["full"]["S"], "S_M3_all": S3, "full_rows_bitwise_eq_M3": bw3,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bw6,
            "subset_rows_bitwise_eq_M14": bw14,
            "pass": (T["full"]["S"] == S3 == 51 and bw3 == 208 and T["meanD_host"]["S"] == 39 and bw6 == 208
                     and all(bw14[n] == len(arm[n]) == 12 for n in SUBSET))}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6_M14") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS + ("dose_S",)}
        logo[g]["SUF"] = sorted(n for n, b in vv["SUF"].items() if b)
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
    per_host_C = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["median_dM_contrast"] for n in names}
                  for h in hosts}
    c_sum = {}
    for n, v in sorted(cstat.items()):
        c_sum[n] = {}
        for f in sorted(set().union(*(x.keys() for x in v))):
            vals = [x[f] for x in v if isinstance(x.get(f), (int, float)) and not isinstance(x.get(f), bool)]
            if vals:
                c_sum[n][f] = {"median": round(statistics.median(vals), 6), "min": round(min(vals), 9),
                               "max": round(max(vals), 9)}
            elif f == "pos_share_before":
                c_sum[n]["pos30_share_median"] = round(statistics.median(x[f]["30"] for x in v), 4)
    size = {n: round(statistics.median(dnorm[n][k] / dnorm["full"][k] for k in dnorm[n]), 4) for n in allnames}

    res = {"schema": "JEV_A461_MECH_M15_ANALYSIS_V1", "table": T, "consistency_gate": gate,
           "rules_applied": V, "verdicts": final, "leave_one_donor_group_out": logo, "per_host_S": per_host,
           "per_host_C": per_host_C, "contrast_stats": c_sum, "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m15_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final, "dose_S": V["dose_S"], "dose_C": V["dose_C"],
                      "q1_detail": V["q1_detail"], "null24_detail": V["null24_detail"],
                      "S": {n: T[n]["S"] for n in names}, "SPEC": {n: T[n]["SPEC"] for n in names},
                      "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
