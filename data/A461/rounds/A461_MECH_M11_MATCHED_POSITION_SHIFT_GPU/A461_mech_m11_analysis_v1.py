#!/usr/bin/env python3
"""A461-MECH-M11 R1 analysis: applies the rules frozen in m11_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm, the meanD_host arm with the M6 pooled-donor arm and the cs1 / chR_sm / cpar16_sm /
cperp16_sm / cpos29 / cpos30 / sh2930 / sh0_28 arms with the M10 arms of the same name (pinned raw rows, bitwise, and
their S values). The split null pools M10's five random frames (pinned M10 raw) with the five run here. Derived from
the M10 analysis (e0f28aac)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "53d2bc8d89098c8e3434be9f11851bc459e1389a"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M10_RAW = "755c74e1d722cdd0429916a13608fd60c647bb53"
VERDICTS = ("position_sm", "amplitude_only", "pos29_smin", "pos30_smin", "shift_sm", "shift2930_umin",
            "split_by_host", "contrast_subspace")
M10_S = {"cs1": 39, "chR_sm": 0, "cpar16_sm": 27, "cperp16_sm": 39, "cpos29": 39, "cpos30": 3, "sh2930": 0, "sh0_28": 13}
M10_NULL = ("crand16_sm",) + tuple(f"crand16_sm_s{i}" for i in range(1, 5))
NULL10 = tuple("m10:" + n for n in M10_NULL) + tuple(f"crand16_sm_s{i}" for i in range(5, 10))
POS29_DOSE = (("cpos29_s025", 0.25), ("cpos29_s05", 0.5), ("cpos29", 1.0))
POS30_DOSE = (("cpos30", 1.0), ("cpos30_s2", 2.0), ("cpos30_s4", 4.0))
SHIFT_DOSE = (("sh2930", 1.0), ("sh2930_u2", 2.0), ("sh2930_u4", 4.0))


def ra(qs):
    q = {x["id"]: x for x in qs}
    c, a = q["conflicting_vote"], q["certificate_action"]
    M = c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]
    L = dict(zip(a["keys"], a["logits"]))
    return M, (M > 0 and L["reject_conflict"] - max(L["accept"], L["wait"]) > 0)


def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def four(a_, b_, names):
    """2 x 2 verdict on a_, b_: names = (a only, b only, both, neither)."""
    return names[2] if a_ and b_ else names[0] if a_ else names[1] if b_ else names[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m6-raw", required=True, type=Path)
    ap.add_argument("--m10-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 / M10 baseline check")
    a = ap.parse_args()
    for p_, b_, n_ in ((a.design, BLOB_DESIGN, "design"), (a.m3_raw, BLOB_M3_RAW, "M3 raw"),
                       (a.m6_raw, BLOB_M6_RAW, "M6 raw"), (a.m10_raw, BLOB_M10_RAW, "M10 raw")):
        if blob(p_) != b_:
            raise SystemExit(f"{n_} pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m6, m10 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw), jsonl(a.m10_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    hb = lambda rows_: {x["target_scene"]: ra(x["questions"])[0] for x in rows_
                        if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    base, m3base, m10base = hb(raw), hb(m3), hb(m10)
    if (base != m3base or base != m10base) and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3 / M10")
    arm = collections.defaultdict(dict)    # arm -> (d, h, main|round) -> (dM, J)
    qrows = collections.defaultdict(dict)
    cstat = collections.defaultdict(list)
    sstat = collections.defaultdict(list)  # shift-factor stats
    dnorm = collections.defaultdict(dict)  # arm -> (d, h, src) -> mean change norm at the span
    for x in raw:
        if x["patch"]:
            M, J = ra(x["questions"])
            k = (x["donor"], x["host"], x["source_kind"])
            arm[x["patch"]["arm"]][k] = (M - base[x["host"]], J)
            qrows[x["patch"]["arm"]][k] = x["questions"]
            dnorm[x["patch"]["arm"]][k] = x["span_stats"]["delta_norm_mean"]
            if x.get("contrast_stats"):
                cstat[x["patch"]["arm"]].append(x["contrast_stats"])
            if x.get("alpha_stats"):
                sstat[x["patch"]["arm"]].append(x["alpha_stats"])

    def ref(rows_, base_, names_):
        out_ = collections.defaultdict(dict)
        for x in rows_:
            if x["patch"] and x["patch"]["arm"] in names_:
                M, J = ra(x["questions"])
                out_[x["patch"]["arm"]][(x["donor"], x["host"], x["source_kind"])] = (M - base_[x["host"]], J,
                                                                                       x["questions"])
        return out_
    m3r, m6r = ref(m3, m3base, ("all",)), ref(m6, m3base, ("meanD_host",))
    m10r = ref(m10, m10base, tuple(M10_S) + M10_NULL)
    names = [n for n, _op, _cl, _ex in design["arms"]]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values())
            or len(m3r["all"]) != 208 or len(m6r["meanD_host"]) != 208
            or any(len(m10r[n]) != 208 for n in tuple(M10_S) + M10_NULL)):
        raise SystemExit("cell census")
    for n in M10_NULL:   # M10's random frames join the null (same host baselines, checked above)
        arm["m10:" + n] = {k: v[:2] for k, v in m10r[n].items()}

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
                "SPEC": frac >= 0.75 and maj >= 10,   # as M2-M10, also under leave-one-group-out (13 groups)
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    all_arms = names + list(NULL10[:5])

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in all_arms}
        Sf = T["full"]["S"]
        SUF = {n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"] for n in all_arms}
        C = {n: T[n]["median_dM_contrast"] for n in all_arms}
        pv = four(SUF["cpos29_n30"], SUF["cpos30_n29"], ("POSITION29_SPECIFIC", "AMPLITUDE_DRIVEN",
                                                         "BOTH_POSITIONS_ACT_AT_SWAPPED_NORM", "P30_INERT_AT_P29_NORM"))
        amp = "AMPLITUDE_ONLY_EXCLUDED" if not SUF["cpos30_n29"] else "AMPLITUDE_ONLY_NOT_EXCLUDED"
        smin = lambda dose: next((v_ for n_, v_ in dose if SUF[n_]), None)
        p29, p30, um = smin(POS29_DOSE), smin(POS30_DOSE), smin(SHIFT_DOSE)
        lv = four(SUF["sh2930_tm"], SUF["sh2930_pt"], ("SHIFT_LOCAL_AT_TOTAL_NORM", "SHIFT_LOCAL_AT_TOKEN_NORM",
                                                       "SHIFT_LOCAL_SUFFICES", "SHIFT_NEEDS_CONTEXT_POSITIONS"))
        rS = [T[n]["S"] for n in NULL10]
        null_ok = statistics.median(rS) <= 5 and not any(T[n]["SPEC"] for n in NULL10)
        sv = four(SUF["cpar16_sm"], SUF["cperp16_sm"], ("CONTRAST_IN_COMMON_SUBSPACE", "CONTRAST_OUTSIDE_COMMON_SUBSPACE",
                                                        "CONTRAST_BOTH_PARTS", "CONTRAST_NOT_SPLITTABLE"))
        if sv != "CONTRAST_NOT_SPLITTABLE" and not null_ok:
            sv += "_UNRESOLVED"
        byhost = {}
        for h in hosts:
            hc = [c for c in cs if c[1] == h]
            if not hc or stats(arm["cs1"], hc)["S"] * 2 <= len(hc):
                continue
            nmax = max(stats(arm[n], hc)["S"] for n in NULL10)
            sp, sq = stats(arm["cperp16_sm"], hc)["S"], stats(arm["cpar16_sm"], hc)["S"]
            byhost[h[:8]] = {"verdict": four(sp > nmax, sq > nmax, ("OUTSIDE", "INSIDE", "BOTH", "NEITHER")),
                             "S_perp": sp, "S_par": sq, "null_max": nmax, "n_cells": len(hc),
                             "null_S": {n: stats(arm[n], hc)["S"] for n in NULL10}}
        sbh = "SPLIT_BY_HOST:" + ",".join(f"{h}={v['verdict']}" for h, v in sorted(byhost.items()))
        fmt = lambda v_: "NONE" if v_ is None else v_
        return T, {"SUF": SUF, "C": C, "null_S": dict(zip(NULL10, rS)), "null_S_median": statistics.median(rS),
                   "null_S_max": max(rS), "split_null10_holds": null_ok, "split_by_host_detail": byhost,
                   "position_sm": pv, "amplitude_only": amp, "pos29_smin": f"POS29_SMIN:{fmt(p29)}",
                   "pos30_smin": f"POS30_SMIN:{fmt(p30)}", "shift_sm": lv, "shift2930_umin": f"SHIFT2930_UMIN:{fmt(um)}",
                   "split_by_host": sbh, "contrast_subspace": sv}

    T, V = verdict(cells)
    S3 = stats(m3r["all"], cells)["S"]
    bw3 = sum(qrows["full"][k] == m3r["all"][k][2] for k in m3r["all"])
    bw6 = sum(qrows["meanD_host"][k] == m6r["meanD_host"][k][2] for k in m6r["meanD_host"])
    bw10 = {n: sum(qrows[n][k] == m10r[n][k][2] for k in m10r[n]) for n in M10_S}
    S10 = {n: stats(m10r[n], cells)["S"] for n in M10_S}
    gate = {"S_full": T["full"]["S"], "S_M3_all": S3, "full_rows_bitwise_eq_M3": bw3,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bw6,
            "m10_rows_bitwise_eq_M10": bw10, "S_m10_arms": {n: T[n]["S"] for n in M10_S}, "S_M10": S10,
            "pass": (T["full"]["S"] == S3 == 51 and bw3 == 208 and T["meanD_host"]["S"] == 39 and bw6 == 208
                     and all(bw10[n] == 208 and T[n]["S"] == S10[n] == M10_S[n] for n in M10_S))}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6_M10") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS + ("null_S", "null_S_median", "split_null10_holds")}
        logo[g]["SUF"] = sorted(n for n, b in vv["SUF"].items() if b)
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in all_arms} for h in hosts}
    med = lambda v, f: round(statistics.median(x[f] for x in v), 4)
    c_sum = {}
    for n, v in sorted(cstat.items()):
        c_sum[n] = {"energy_share_median": med(v, "energy_share"),
                    "energy_share_min": round(min(x["energy_share"] for x in v), 4)}
        for f in ("alpha_median", "alpha_median_nz"):
            if f in v[0]:
                c_sum[n][f + "_of_rows"] = med(v, f)
        if "alpha_max" in v[0]:
            c_sum[n].update(alpha_max=round(max(x["alpha_max"] for x in v), 4),
                            capped_share_mean=round(statistics.mean(x["capped_share"] for x in v), 4))
        if "alpha_rows" in v[0]:
            ar = [u for x in v for u in x["alpha_rows"]]
            c_sum[n].update(alpha_rows_min=round(min(ar), 4), alpha_rows_max=round(max(ar), 4))
    s_sum = {n: {f: {"median": med(v, f), "min": round(min(x[f] for x in v), 4), "max": round(max(x[f] for x in v), 4)}
                 for f in v[0]} for n, v in sorted(sstat.items())}
    size = {n: round(statistics.median(dnorm[n][k] / dnorm["full"][k] for k in dnorm["full"]), 4) for n in names}

    res = {"schema": "JEV_A461_MECH_M11_ANALYSIS_V1", "table": T, "consistency_gate": gate,
           "rules_applied": V, "verdicts": final, "leave_one_donor_group_out": logo, "per_host_S": per_host,
           "contrast_stats": c_sum, "shift_stats": s_sum, "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m11_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final, "null_S": V["null_S"],
                      "split_by_host": V["split_by_host_detail"],
                      "S": {n: T[n]["S"] for n in all_arms}, "SPEC": {n: T[n]["SPEC"] for n in all_arms},
                      "contrast_stats": c_sum, "shift_stats": s_sum, "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
