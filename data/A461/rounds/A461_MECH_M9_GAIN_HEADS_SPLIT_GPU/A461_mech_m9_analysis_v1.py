#!/usr/bin/env python3
"""A461-MECH-M9 R1 analysis: applies the rules frozen in m9_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm, the meanD_host arm with the M6 pooled-donor arm and the cs0 / cs05 / cs1 / cs2 arms
with the M8 arms of the same name (pinned raw rows, bitwise, and their S values); g0_2 against the M7 rcD rows is
reported. Derived from the M8 analysis (a09ce224)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "fe91481e42e5cf33f20cd7c98dba16caf177268c"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M7_RAW = "0383fccf01ad027ae14c59c8fc9830f1d398219e"
BLOB_M8_RAW = "997c9b71054ee2adec472a5410705068511650aa"
VERDICTS = ("gain_shape", "gain_tmin", "contrast_heads", "contrast_subspace")
M8_S = {"cs0": 0, "cs05": 38, "cs1": 39, "cs2": 36}


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
    ap.add_argument("--m7-raw", required=True, type=Path)
    ap.add_argument("--m8-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 baseline check")
    a = ap.parse_args()
    for p_, b_, n_ in ((a.design, BLOB_DESIGN, "design"), (a.m3_raw, BLOB_M3_RAW, "M3 raw"),
                       (a.m6_raw, BLOB_M6_RAW, "M6 raw"), (a.m7_raw, BLOB_M7_RAW, "M7 raw"),
                       (a.m8_raw, BLOB_M8_RAW, "M8 raw")):
        if blob(p_) != b_:
            raise SystemExit(f"{n_} pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m6, m7, m8 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw), jsonl(a.m7_raw), jsonl(a.m8_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    hb = lambda rows_: {x["target_scene"]: ra(x["questions"])[0] for x in rows_
                        if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    base, m3base, m7base, m8base = hb(raw), hb(m3), hb(m7), hb(m8)
    if (base != m3base or base != m7base or base != m8base) and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3 / M7 / M8")
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
    m7r, m8r = ref(m7, m7base, ("rcD",)), ref(m8, m8base, tuple(M8_S))
    names = [n for n, _op, _cl, _ex in design["arms"]]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values())
            or len(m3r["all"]) != 208 or len(m6r["meanD_host"]) != 208 or len(m7r["rcD"]) != 208
            or any(len(m8r[n]) != 208 for n in M8_S)):
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
                "SPEC": frac >= 0.75 and maj >= 10,   # as M2-M8, also under leave-one-group-out (13 groups)
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    tg, sg = design["t_grid"], design["s_grid"]
    gname = lambda tn, sn: f"cs{sn}" if tn == "1" else f"g{tn}_{sn}"

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        SUF = {n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"] for n in names}
        C = {n: T[n]["median_dM_contrast"] for n in names}
        L, Q = {}, {}
        for sn, _sv in sg[2:]:     # s = 1, 2
            den = C[gname("1", sn)] - C[gname("0", sn)]
            L[sn] = round((C[gname("05", sn)] - C[gname("0", sn)]) / den, 4) if den > 0 else None
            Q[sn] = round((C[gname("025", sn)] - C[gname("0", sn)]) / den, 4) if den > 0 else None
        Ls = list(L.values())
        if any(x is None for x in Ls):
            gv = "GAIN_UNDEFINED"
        elif all(0.3 <= x <= 0.7 for x in Ls):
            gv = "GAIN_BILINEAR"
        elif all(x > 0.7 for x in Ls):
            gv = "GAIN_EARLY_SATURATING"
        elif all(x < 0.3 for x in Ls):
            gv = "GAIN_LATE_THRESHOLD"
        else:
            gv = "GAIN_MIXED"
        ts = next((tv for tn, tv in tg if SUF[gname(tn, "1")]), None)
        tv_ = f"GAIN_TMIN:{ts}" if ts is not None else "GAIN_TMIN_NONE"
        w, r_ = SUF["chW"], SUF["chR"]
        hv = ("CONTRAST_EITHER_HEAD_SET" if w and r_ else "CONTRAST_IN_WRITER_HEADS" if w else
              "CONTRAST_OUTSIDE_WRITER_HEADS" if r_ else "CONTRAST_NEEDS_ALL_HEADS")
        if SUF["ch10"]:
            hv += "+H10"
        null_ok = T["crand16_sm"]["S"] <= 5 and not T["crand16_sm"]["SPEC"]
        p_, q_ = SUF["cpar16_sm"], SUF["cperp16_sm"]
        if not p_ and not q_:
            pv = "CONTRAST_NOT_SPLITTABLE"
        else:
            pv = ("CONTRAST_BOTH_PARTS" if p_ and q_ else "CONTRAST_IN_COMMON_SUBSPACE" if p_
                  else "CONTRAST_OUTSIDE_COMMON_SUBSPACE") + ("" if null_ok else "_UNRESOLVED")
        return T, {"SUF": SUF, "C": C, "L": L, "Q": Q, "t_star": ts, "split_null_holds": null_ok,
                   "gain_shape": gv, "gain_tmin": tv_, "contrast_heads": hv, "contrast_subspace": pv}

    T, V = verdict(cells)
    S3 = stats(m3r["all"], cells)["S"]
    bw3 = sum(qrows["full"][k] == m3r["all"][k][2] for k in m3r["all"])
    bw6 = sum(qrows["meanD_host"][k] == m6r["meanD_host"][k][2] for k in m6r["meanD_host"])
    bw8 = {n: sum(qrows[n][k] == m8r[n][k][2] for k in m8r[n]) for n in M8_S}
    S8 = {n: stats(m8r[n], cells)["S"] for n in M8_S}
    rc = {"g0_2_rows_bitwise_eq_M7_rcD": sum(qrows["g0_2"][k] == m7r["rcD"][k][2] for k in m7r["rcD"]),
          "S_M7_rcD": stats(m7r["rcD"], cells)["S"], "C_M7_rcD": stats(m7r["rcD"], cells)["median_dM_contrast"],
          "S_g0_2": T["g0_2"]["S"], "C_g0_2": T["g0_2"]["median_dM_contrast"]}
    gate = {"S_full": T["full"]["S"], "S_M3_all": S3, "full_rows_bitwise_eq_M3": bw3,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bw6,
            "cs_rows_bitwise_eq_M8": bw8, "S_cs": {n: T[n]["S"] for n in M8_S}, "S_M8_cs": S8,
            "pass": (T["full"]["S"] == S3 == 51 and bw3 == 208 and T["meanD_host"]["S"] == 39 and bw6 == 208
                     and all(bw8[n] == 208 and T[n]["S"] == S8[n] == M8_S[n] for n in M8_S))}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6_M8") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS + ("L", "Q", "t_star", "split_null_holds")}
        logo[g]["SUF"] = sorted(n for n, b in vv["SUF"].items() if b)
    grid = {f"t={tn}": {f"s={sn}": ({"S": T[gname(tn, sn)]["S"], "C": T[gname(tn, sn)]["median_dM_contrast"],
                                     "J": [T[gname(tn, sn)]["J_main"], T[gname(tn, sn)]["J_round"]],
                                     "SUF": V["SUF"][gname(tn, sn)]} if (tv or sv) else None)
                        for sn, sv in sg} for tn, tv in tg}
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
    med = lambda v, f: round(statistics.median(x[f] for x in v), 4)
    c_sum = {n: dict({"energy_share_median": med(v, "energy_share"),
                      "energy_share_min": round(min(x["energy_share"] for x in v), 4)},
                     **({"alpha_median_of_medians": med(v, "alpha_median"),
                         "alpha_max": round(max(x["alpha_max"] for x in v), 4),
                         "capped_share_mean": round(statistics.mean(x["capped_share"] for x in v), 4)}
                        if "alpha_median" in v[0] else {}))
             for n, v in sorted(cstat.items())}
    size = {n: round(statistics.median(dnorm[n][k] / dnorm["full"][k] for k in dnorm["full"]), 4) for n in names}

    res = {"schema": "JEV_A461_MECH_M9_ANALYSIS_V1", "table": T, "grid": grid, "consistency_gate": gate,
           "rules_applied": V, "verdicts": final, "m7_rcD_replay": rc,
           "leave_one_donor_group_out": logo, "per_host_S": per_host, "contrast_stats": c_sum,
           "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m9_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final, "L": V["L"], "Q": V["Q"], "m7_rcD_replay": rc,
                      "S": {n: T[n]["S"] for n in names}, "SPEC": {n: T[n]["SPEC"] for n in names},
                      "contrast_stats": c_sum, "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
