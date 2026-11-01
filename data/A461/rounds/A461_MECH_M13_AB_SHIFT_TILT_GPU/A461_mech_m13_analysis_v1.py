#!/usr/bin/env python3
"""A461-MECH-M13 R1 analysis: applies the rules frozen in m13_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm, the meanD_host arm with the M6 pooled-donor arm and the cs1 / cs_s05 / cs_s025 /
cpar16_sm / sh_fBLOCK / sh_xAUTH / sh_xBLOCK arms with the M12 arms of the same name (pinned raw rows, bitwise, and
their S values). Derived from the M12 analysis (13d27379)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "900b1f0595ab30f45cc07264a14280bf2f8c222a"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M12_RAW = "cc79f23a0dc6d80ec17bdad0fed54f710291dbe4"
VERDICTS = ("shift_ab", "shift_ab_c29", "shift_ab_s05", "shift_ab_needed", "ab_location", "ab_by_host",
            "tilt_s1", "tilt_s05", "tilt_s0375", "rem_role", "rem_null_by_host", "rem_null")
M12_S = {"cs1": 39, "cs_s05": 38, "cs_s025": 13, "cpar16_sm": 27, "sh_fBLOCK": 18, "sh_xAUTH": 26, "sh_xBLOCK": 20}
TILT = {"s1": ("rem_m1", "cs1", "rem_p1"), "s05": ("rem_m1_s05", "cs_s05", "rem_p1_s05"),
        "s0375": ("rem_m1_s0375", "cs_s0375", "rem_p1_s0375")}
NULLS = {s_: tuple(f"rnull_{s_}_{i}" for i in range(1, 6)) for s_ in ("s05", "s0375")}


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
    ap.add_argument("--m12-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 / M12 baseline check")
    a = ap.parse_args()
    for p_, b_, n_ in ((a.design, BLOB_DESIGN, "design"), (a.m3_raw, BLOB_M3_RAW, "M3 raw"),
                       (a.m6_raw, BLOB_M6_RAW, "M6 raw"), (a.m12_raw, BLOB_M12_RAW, "M12 raw")):
        if blob(p_) != b_:
            raise SystemExit(f"{n_} pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m6, m12 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw), jsonl(a.m12_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    hb = lambda rows_: {x["target_scene"]: ra(x["questions"])[0] for x in rows_
                        if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    base, m3base, m12base = hb(raw), hb(m3), hb(m12)
    if (base != m3base or base != m12base) and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3 / M12")
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
    m12r = ref(m12, m12base, tuple(M12_S))
    names = [n for n, _op, _cl, _ex in design["arms"]]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values())
            or len(m3r["all"]) != 208 or len(m6r["meanD_host"]) != 208
            or any(len(m12r[n]) != 208 for n in M12_S)):
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
        resp = []
        for h in hosts:
            hc = [c for c in cs if c[1] == h]
            if hc and hs("cs1", hc) * 2 > len(hc):
                resp.append((h, hc))
        S = {n: T[n]["S"] for n in names}
        loc = ("AB_LOCATION_UNRESOLVED" if not SUF["sh_fAB"]
               else "AB_LOCATION_NOT_SPECIFIC" if SUF["sh_fKR"] or SUF["sh_fRR"]
               else "AB_LOCATION_SPECIFIC" if S["sh_fAB"] > max(S["sh_fKR"], S["sh_fRR"]) else "AB_LOCATION_UNRESOLVED")
        abh = "AB_BY_HOST:" + ",".join(f"{h[:8]}={hs('sh_fAB', hc)}/{hs('cs1', hc)}" for h, hc in resp)
        tilt, tS = {}, {}
        for k_, (nm, n0, np_) in TILT.items():
            sm, s0, sp = S[nm], S[n0], S[np_]
            tS[k_] = {"lam-1": sm, "lam0": s0, "lam+1": sp, "C": [C[nm], C[n0], C[np_]]}
            tilt[k_] = ("TILT_NO_EFFECT" if sm == s0 == sp else "TILT_OPPOSES" if sm >= s0 >= sp and sm > sp
                        else "TILT_SUPPORTS" if sm <= s0 <= sp and sm < sp else "TILT_MIXED")
        tS["lam+2"] = {"s1": S["rem_p2"], "s05": S["rem_p2_s05"], "C": [C["rem_p2"], C["rem_p2_s05"]]}
        tv = set(tilt.values())
        role = ("REM_NO_EFFECT" if tv == {"TILT_NO_EFFECT"}
                else "REM_OPPOSES" if "TILT_OPPOSES" in tv and tv <= {"TILT_OPPOSES", "TILT_NO_EFFECT"}
                else "REM_SUPPORTS" if "TILT_SUPPORTS" in tv and tv <= {"TILT_SUPPORTS", "TILT_NO_EFFECT"}
                else "REM_MIXED")
        byhost, flags = {}, []
        for h, hc in resp:
            row = {"n_cells": len(hc)}
            for k_, ns_ in NULLS.items():
                N = [hs(n, hc) for n in ns_]
                add, rmv = hs(TILT[k_][2], hc), hs(TILT[k_][0], hc)
                va = "HARM_BEYOND_NULL" if add < min(N) else "LESS_HARM_THAN_NULL" if add > max(N) else "AT"
                vr = "REMOVAL_BEYOND_NULL" if rmv > max(N) else "REMOVAL_BELOW_NULL" if rmv < min(N) else "AT"
                row[k_] = {"null_S": N, "add_S": add, "remove_S": rmv, "add": va, "remove": vr}
                flags += [va, vr]
            byhost[h[:8]] = row
        rnh = "REM_NULL_BY_HOST:" + ",".join(f"{h}=" + ",".join(f"{k_}:{v[k_]['add']}/{v[k_]['remove']}" for k_ in NULLS)
                                             for h, v in sorted(byhost.items()))
        fs = set(flags)
        beyond, rev = fs & {"HARM_BEYOND_NULL", "REMOVAL_BEYOND_NULL"}, fs & {"LESS_HARM_THAN_NULL", "REMOVAL_BELOW_NULL"}
        rnull = ("REM_DIRECTION_NO_RESPONSIVE_HOST" if not flags else "REM_DIRECTION_NOT_SPECIFIC" if fs == {"AT"}
                 else "REM_DIRECTION_SPECIFIC" if beyond and not rev else "REM_DIRECTION_REVERSED" if rev and not beyond
                 else "REM_DIRECTION_MIXED")
        yn = lambda b, y, n_: y if b else n_
        return T, {"SUF": SUF, "C": C, "responsive_hosts": [h[:8] for h, _ in resp],
                   "shift_ab": yn(SUF["sh_fAB"], "SHIFT_AB_SUFFICES", "SHIFT_AB_INSUFFICIENT"),
                   "shift_ab_c29": yn(SUF["sh_fAB_c29"], "SHIFT_AB_C29_SUFFICES", "SHIFT_AB_C29_INSUFFICIENT"),
                   "shift_ab_s05": yn(SUF["sh_fAB_s05"], "SHIFT_AB_S05_SUFFICES", "SHIFT_AB_S05_INSUFFICIENT"),
                   "shift_ab_needed": yn(not SUF["sh_xAB"], "SHIFT_AB_NEEDED", "SHIFT_AB_NOT_NEEDED"),
                   "ab_location": loc, "ab_by_host": abh,
                   "tilt_s1": tilt["s1"], "tilt_s05": tilt["s05"], "tilt_s0375": tilt["s0375"], "tilt_S": tS,
                   "rem_role": role, "rem_null_by_host": rnh, "rem_null_detail": byhost, "rem_null": rnull,
                   "null_S_pooled": {n: S[n] for ns_ in NULLS.values() for n in ns_}}

    T, V = verdict(cells)
    S3 = stats(m3r["all"], cells)["S"]
    bw3 = sum(qrows["full"][k] == m3r["all"][k][2] for k in m3r["all"])
    bw6 = sum(qrows["meanD_host"][k] == m6r["meanD_host"][k][2] for k in m6r["meanD_host"])
    bw12 = {n: sum(qrows[n][k] == m12r[n][k][2] for k in m12r[n]) for n in M12_S}
    S12 = {n: stats(m12r[n], cells)["S"] for n in M12_S}
    gate = {"S_full": T["full"]["S"], "S_M3_all": S3, "full_rows_bitwise_eq_M3": bw3,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bw6,
            "m12_rows_bitwise_eq_M12": bw12, "S_m12_arms": {n: T[n]["S"] for n in M12_S}, "S_M12": S12,
            "pass": (T["full"]["S"] == S3 == 51 and bw3 == 208 and T["meanD_host"]["S"] == 39 and bw6 == 208
                     and all(bw12[n] == 208 and T[n]["S"] == S12[n] == M12_S[n] for n in M12_S))}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6_M12") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS + ("tilt_S",)}
        logo[g]["SUF"] = sorted(n for n, b in vv["SUF"].items() if b)
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
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
    size = {n: round(statistics.median(dnorm[n][k] / dnorm["full"][k] for k in dnorm["full"]), 4) for n in names}

    res = {"schema": "JEV_A461_MECH_M13_ANALYSIS_V1", "table": T, "consistency_gate": gate,
           "rules_applied": V, "verdicts": final, "leave_one_donor_group_out": logo, "per_host_S": per_host,
           "contrast_stats": c_sum, "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m13_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final, "tilt_S": V["tilt_S"],
                      "rem_null_detail": V["rem_null_detail"],
                      "S": {n: T[n]["S"] for n in names}, "SPEC": {n: T[n]["SPEC"] for n in names},
                      "contrast_stats": c_sum, "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
