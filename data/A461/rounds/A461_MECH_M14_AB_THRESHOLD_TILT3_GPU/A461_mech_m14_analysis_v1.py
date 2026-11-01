#!/usr/bin/env python3
"""A461-MECH-M14 R1 analysis: applies the rules frozen in m14_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm, the meanD_host arm with the M6 pooled-donor arm and the 4 M13 replay arms on the 6
subset cells with the M13 rows of the same name (pinned raw rows, bitwise). Q1 thresholds use the pinned M13 rows for
s = 1 and for the all-position shift. Derived from the M13 analysis (76489a54)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "87905a3c4d0a5786a25bbd974ef13c40f3f3c06b"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M13_RAW = "cdbf677bd2b89d487045b104af040f2e39fcf5a3"
VERDICTS = ("ab_smin_by_host", "ab_threshold", "shift_2930", "ab_t05", "tilt_s0437", "tilt_s0312", "rem_role",
            "tilt_by_host", "rem3_s", "rem3_c", "rem3_by_host")
SUBSET = ("sh_fAB_c29", "cs_s0375", "rem_p1", "rnull_s05_1")
M13_REF = ("cs1", "cs_s05", "cs_s0375", "cs_s025", "sh_fAB_c29") + SUBSET[2:]
SZ = ("s0437", "s0312")
LAMS = ("rem_m3_{}", "rem_m1_{}", "cs_{}", "rem_p1_{}", "rem_p3_{}")
MAJ = 7          # host S >= 7 of 13 cells: the per-host threshold rule (frozen)
NONE = 2.0       # SMIN of a host that no s repairs, ordered above s = 1


def tilt_rule(v):
    if len(set(v)) == 1:
        return "TILT_NO_EFFECT"
    if all(x >= y for x, y in zip(v, v[1:])) and v[0] > v[-1]:
        return "TILT_OPPOSES"
    if all(x <= y for x, y in zip(v, v[1:])) and v[0] < v[-1]:
        return "TILT_SUPPORTS"
    return "TILT_MIXED"


def pooled(flags, pre, empty):
    fs = set(flags)
    beyond, rev = fs & {"HARM_BEYOND_NULL", "REMOVAL_BEYOND_NULL"}, fs & {"LESS_HARM_THAN_NULL", "REMOVAL_BELOW_NULL"}
    return (empty if not flags else f"{pre}_NOT_SPECIFIC" if fs == {"AT"} else f"{pre}_SPECIFIC" if beyond and not rev
            else f"{pre}_REVERSED" if rev and not beyond else f"{pre}_MIXED")


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m6-raw", required=True, type=Path)
    ap.add_argument("--m13-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 / M13 baseline check")
    a = ap.parse_args()
    for p_, b_, n_ in ((a.design, BLOB_DESIGN, "design"), (a.m3_raw, BLOB_M3_RAW, "M3 raw"),
                       (a.m6_raw, BLOB_M6_RAW, "M6 raw"), (a.m13_raw, BLOB_M13_RAW, "M13 raw")):
        if blob(p_) != b_:
            raise SystemExit(f"{n_} pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m6, m13 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw), jsonl(a.m13_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    hb = lambda rows_: {x["target_scene"]: ra(x["questions"])[0] for x in rows_
                        if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    base, m3base, m13base = hb(raw), hb(m3), hb(m13)
    if (base != m3base or base != m13base) and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3 / M13")
    arm = collections.defaultdict(dict)    # arm -> (d, h, main|round) -> (dM, J)
    qrows = collections.defaultdict(dict)
    cstat = collections.defaultdict(list)
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

    def ref(rows_, base_, names_):
        out_ = collections.defaultdict(dict)
        for x in rows_:
            if x["patch"] and x["patch"]["arm"] in names_:
                M, J = ra(x["questions"])
                out_[x["patch"]["arm"]][(x["donor"], x["host"], x["source_kind"])] = (M - base_[x["host"]], J,
                                                                                       x["questions"])
        return out_
    m3r, m6r = ref(m3, m3base, ("all",)), ref(m6, m3base, ("meanD_host",))
    m13r = ref(m13, m13base, M13_REF)
    allnames = [n for n, _op, _cl, _ex in design["arms"]]
    names = [n for n in allnames if n not in SUBSET]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(allnames)
            or any(len(arm[n]) != (12 if n in SUBSET else 208) for n in allnames)
            or len(m3r["all"]) != 208 or len(m6r["meanD_host"]) != 208
            or any(len(m13r[n]) != 208 for n in M13_REF)):
        raise SystemExit("cell census")

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
                "SPEC": frac >= 0.75 and maj >= 10,   # as M2-M11, also under leave-one-group-out (13 groups)
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        SUF = {n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"] for n in names}
        C = {n: T[n]["median_dM_contrast"] for n in names}
        hs = lambda n, hc: stats(arm[n], hc)["S"]
        hc_ = lambda n, hc: stats(arm[n], hc)["median_dM_contrast"]
        h13 = lambda n, hc: stats(m13r[n], hc)["S"]
        resp = []
        for h in hosts:
            hc = [c for c in cs if c[1] == h]
            if hc and h13("cs1", hc) * 2 > len(hc):
                resp.append((h, hc))
        S = {n: T[n]["S"] for n in names}
        # Q1: per-host contrast-size thresholds of the AB shift (c at 29) and of the all-position shift
        smin = lambda f: min([s_ for s_, n in f if n >= MAJ] or [NONE])
        abm, flags_ab = {}, []
        for h, hc in resp:
            sa = smin([(0.25, hs("abc_s025", hc)), (0.375, hs("abc_s0375", hc)), (0.5, hs("abc_s05", hc)),
                       (1.0, h13("sh_fAB_c29", hc))])
            sc = smin([(0.25, h13("cs_s025", hc)), (0.375, h13("cs_s0375", hc)), (0.5, h13("cs_s05", hc)),
                       (1.0, h13("cs1", hc))])
            abm[h[:8]] = {"ab": sa, "cs": sc, "S_ab": [hs("abc_s025", hc), hs("abc_s0375", hc), hs("abc_s05", hc),
                                                       h13("sh_fAB_c29", hc)],
                          "S_cs": [h13("cs_s025", hc), h13("cs_s0375", hc), h13("cs_s05", hc), h13("cs1", hc)]}
            flags_ab.append((sa > sc) - (sa < sc))
        fmt = lambda x: "NONE" if x == NONE else f"{x:g}"
        abh = "AB_SMIN_BY_HOST:" + ",".join(f"{h}={fmt(v['ab'])}/{fmt(v['cs'])}" for h, v in sorted(abm.items()))
        abt = ("AB_THRESHOLD_SAME" if all(f == 0 for f in flags_ab)
               else "AB_THRESHOLD_LOWER" if all(f <= 0 for f in flags_ab)
               else "AB_THRESHOLD_HIGHER" if all(f >= 0 for f in flags_ab) else "AB_THRESHOLD_MIXED")
        # Q2: tilt dose over lam -3, -1, 0, +1, +3 at s 7/16 and 5/16, pooled and per host
        tilt, tS, tbh = {}, {}, {}
        for k_ in SZ:
            ns_ = [t.format(k_) for t in LAMS]
            tS[k_] = {"S": [S[n] for n in ns_], "C": [C[n] for n in ns_]}
            tilt[k_] = tilt_rule([S[n] for n in ns_])
            for h, hc in resp:
                tbh.setdefault(h[:8], {})[k_] = {"S": [hs(n, hc) for n in ns_], "C": [hc_(n, hc) for n in ns_],
                                                 "rule": tilt_rule([hs(n, hc) for n in ns_])}
        tv = set(tilt.values())
        role = ("REM_NO_EFFECT" if tv == {"TILT_NO_EFFECT"}
                else "REM_OPPOSES" if "TILT_OPPOSES" in tv and tv <= {"TILT_OPPOSES", "TILT_NO_EFFECT"}
                else "REM_SUPPORTS" if "TILT_SUPPORTS" in tv and tv <= {"TILT_SUPPORTS", "TILT_NO_EFFECT"}
                else "REM_MIXED")
        tbs = "TILT_BY_HOST:" + ",".join(f"{h}=" + ",".join(f"{k_}:{v[k_]['rule']}" for k_ in SZ)
                                         for h, v in sorted(tbh.items()))
        # Q2 null: rem_p3 / rem_m3 against the 8 3x random tilts, by S (informative pairs only) and by C
        detail, fS, fC = {}, [], []
        for h, hc in resp:
            row = {"n_cells": len(hc)}
            for k_ in SZ:
                nl = [f"rnull3_{k_}_{i}" for i in range(1, 9)]
                N, NC = [hs(n, hc) for n in nl], [hc_(n, hc) for n in nl]
                add, rmv = hs(f"rem_p3_{k_}", hc), hs(f"rem_m3_{k_}", hc)
                addc, rmvc = hc_(f"rem_p3_{k_}", hc), hc_(f"rem_m3_{k_}", hc)
                allv = N + [add, rmv]
                inf = not (all(v == 0 for v in allv) or all(v == len(hc) for v in allv))
                va = "HARM_BEYOND_NULL" if add < min(N) else "LESS_HARM_THAN_NULL" if add > max(N) else "AT"
                vr = "REMOVAL_BEYOND_NULL" if rmv > max(N) else "REMOVAL_BELOW_NULL" if rmv < min(N) else "AT"
                vac = "HARM_BEYOND_NULL" if addc < min(NC) else "LESS_HARM_THAN_NULL" if addc > max(NC) else "AT"
                vrc = "REMOVAL_BEYOND_NULL" if rmvc > max(NC) else "REMOVAL_BELOW_NULL" if rmvc < min(NC) else "AT"
                if inf:
                    fS += [va, vr]
                fC += [vac, vrc]
                row[k_] = {"informative_S": inf, "null_S": N, "add_S": add, "remove_S": rmv,
                           "add": va if inf else "UNINFORMATIVE", "remove": vr if inf else "UNINFORMATIVE",
                           "null_C": NC, "add_C": addc, "remove_C": rmvc, "add_by_C": vac, "remove_by_C": vrc}
            detail[h[:8]] = row
        rbh = "REM3_BY_HOST:" + ",".join(
            f"{h}=" + ",".join(f"{k_}:S {v[k_]['add']}/{v[k_]['remove']}|C {v[k_]['add_by_C']}/{v[k_]['remove_by_C']}"
                               for k_ in SZ) for h, v in sorted(detail.items()))
        yn = lambda b, y, n_: y if b else n_
        return T, {"SUF": SUF, "C": C, "responsive_hosts": [h[:8] for h, _ in resp],
                   "ab_smin_by_host": abh, "ab_smin_detail": abm, "ab_threshold": abt,
                   "shift_2930": yn(not SUF["ab_only_c29"], "SHIFT_2930_NEEDED", "SHIFT_2930_NOT_NEEDED"),
                   "ab_t05": yn(SUF["abc_t05"], "AB_T05_SUFFICES", "AB_T05_INSUFFICIENT"),
                   "q1_by_host": {h[:8]: {n: hs(n, hc) for n in ("abc_s05", "abc_s0375", "abc_s025", "ab_only_c29",
                                                                  "abc_t05")} for h, hc in resp},
                   "tilt_s0437": tilt["s0437"], "tilt_s0312": tilt["s0312"], "tilt_S": tS, "rem_role": role,
                   "tilt_by_host": tbs, "tilt_by_host_detail": tbh,
                   "rem3_s": pooled(fS, "REM3_DIRECTION", "REM3_DIRECTION_UNINFORMATIVE"),
                   "rem3_c": pooled(fC, "REM3C_DIRECTION", "REM3C_DIRECTION_NO_RESPONSIVE_HOST"),
                   "rem3_by_host": rbh, "rem3_detail": detail}

    T, V = verdict(cells)
    S3 = stats(m3r["all"], cells)["S"]
    bw3 = sum(qrows["full"][k] == m3r["all"][k][2] for k in m3r["all"])
    bw6 = sum(qrows["meanD_host"][k] == m6r["meanD_host"][k][2] for k in m6r["meanD_host"])
    bw13 = {n: sum(qrows[n][k] == m13r[n][k][2] for k in qrows[n]) for n in SUBSET}
    gate = {"S_full": T["full"]["S"], "S_M3_all": S3, "full_rows_bitwise_eq_M3": bw3,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bw6,
            "subset_rows_bitwise_eq_M13": bw13,
            "pass": (T["full"]["S"] == S3 == 51 and bw3 == 208 and T["meanD_host"]["S"] == 39 and bw6 == 208
                     and all(bw13[n] == len(qrows[n]) == 12 for n in SUBSET))}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6_M13") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS + ("tilt_S",)}
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

    res = {"schema": "JEV_A461_MECH_M14_ANALYSIS_V1", "table": T, "consistency_gate": gate,
           "rules_applied": V, "verdicts": final, "leave_one_donor_group_out": logo, "per_host_S": per_host, "per_host_C": per_host_C,
           "contrast_stats": c_sum, "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m14_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final, "tilt_S": V["tilt_S"],
                      "ab_smin_detail": V["ab_smin_detail"], "rem3_detail": V["rem3_detail"],
                      "S": {n: T[n]["S"] for n in names}, "SPEC": {n: T[n]["SPEC"] for n in names},
                      "contrast_stats": c_sum, "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
