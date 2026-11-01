#!/usr/bin/env python3
"""A461-MECH-M12 R1 analysis: applies the rules frozen in m12_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm, the meanD_host arm with the M6 pooled-donor arm and the cs1 / cpos29 / cpos29_s05 /
cpos29_s025 / cpar16_sm / cperp16_sm / sh2930 / sh0_28 arms with the M11 arms of the same name (pinned raw rows,
bitwise, and their S values). Derived from the M11 analysis (31dbc6fc)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "3b2ef50f3f45274249b1ed05dcc578d67807f173"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M11_RAW = "393f0d6e7d4a698db15f9217202039c52ad663a8"
VERDICTS = ("p30_weight", "wsmin_m1", "wsmin_0", "wsmin_p1", "wsmin_p2", "flip_lowers_threshold",
            "shift_fields_needed", "shift_fields_suffice", "cos_split_by_host", "cos_subspace")
M11_S = {"cs1": 39, "cpos29": 39, "cpos29_s05": 38, "cpos29_s025": 13, "cpar16_sm": 27, "cperp16_sm": 39,
         "sh2930": 0, "sh0_28": 13}
W_DOSE = {"m1": (("cw30_m1_s025", 0.25), ("cw30_m1_s05", 0.5), ("cw30_m1", 1.0)),
          "0": (("cpos29_s025", 0.25), ("cpos29_s05", 0.5), ("cpos29", 1.0)),
          "p1": (("cs_s025", 0.25), ("cs_s05", 0.5), ("cs1", 1.0)),
          "p2": (("cw30_p2_s05", 0.5), ("cw30_p2", 1.0))}
FIELDS = ("AUTH", "BLOCK", "KIND", "RECV", "RKEY")
NULLS = {p_: tuple(f"ccos_{p_}_s{i}" for i in range(1, 6)) for p_ in ("par", "perp")}


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
    ap.add_argument("--m11-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 / M11 baseline check")
    a = ap.parse_args()
    for p_, b_, n_ in ((a.design, BLOB_DESIGN, "design"), (a.m3_raw, BLOB_M3_RAW, "M3 raw"),
                       (a.m6_raw, BLOB_M6_RAW, "M6 raw"), (a.m11_raw, BLOB_M11_RAW, "M11 raw")):
        if blob(p_) != b_:
            raise SystemExit(f"{n_} pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m6, m11 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw), jsonl(a.m11_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    hb = lambda rows_: {x["target_scene"]: ra(x["questions"])[0] for x in rows_
                        if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    base, m3base, m11base = hb(raw), hb(m3), hb(m11)
    if (base != m3base or base != m11base) and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3 / M11")
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
    m11r = ref(m11, m11base, tuple(M11_S))
    names = [n for n, _op, _cl, _ex in design["arms"]]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values())
            or len(m3r["all"]) != 208 or len(m6r["meanD_host"]) != 208
            or any(len(m11r[n]) != 208 for n in M11_S)):
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
        sm, s0, sp = T["cw30_m1_s025"]["S"], T["cpos29_s025"]["S"], T["cs_s025"]["S"]
        pw = ("P30_OPPOSES" if sm > s0 >= sp and sm > sp else "P30_SUPPORTS" if sp > s0 >= sm and sp > sm
              else "P30_NO_EFFECT" if sm == s0 == sp else "P30_MIXED")
        smin = {w: next((v_ for n_, v_ in dose if SUF[n_]), None) for w, dose in W_DOSE.items()}
        fmt = lambda v_: "NONE" if v_ is None else v_
        flip = ("FLIP_LOWERS_THRESHOLD" if smin["m1"] is not None and (smin["0"] is None or smin["m1"] < smin["0"])
                else "FLIP_DOES_NOT_LOWER_THRESHOLD")
        need = [f for f in FIELDS if not SUF[f"sh_x{f}"]]
        suff = [f for f in FIELDS if SUF[f"sh_f{f}"]]
        byhost = {}
        for h in hosts:
            hc = [c for c in cs if c[1] == h]
            if not hc or stats(arm["cs1"], hc)["S"] * 2 <= len(hc):
                continue
            row = {"n_cells": len(hc)}
            for p_ in ("par", "perp"):
                ns = [stats(arm[n], hc)["S"] for n in NULLS[p_]]
                sp_ = stats(arm[f"c{p_}16_sm"], hc)["S"]
                row[p_] = {"S": sp_, "null_S": ns, "verdict": "BEYOND" if sp_ > max(ns) else "BELOW" if sp_ < min(ns)
                           else "AT"}
            byhost[h[:8]] = row
        csb = "COS_SPLIT_BY_HOST:" + ",".join(f"{h}=par:{v['par']['verdict']}/perp:{v['perp']['verdict']}"
                                              for h, v in sorted(byhost.items()))
        vs = [v[p_]["verdict"] for v in byhost.values() for p_ in ("par", "perp")]
        cv = ("SUBSPACE_NO_RESPONSIVE_HOST" if not vs else "SUBSPACE_EXPLAINED_BY_COSINE" if set(vs) == {"AT"}
              else "SUBSPACE_BEYOND_COSINE" if "BEYOND" in vs and "BELOW" not in vs
              else "SUBSPACE_BELOW_COSINE" if "BELOW" in vs and "BEYOND" not in vs else "SUBSPACE_COSINE_MIXED")
        return T, {"SUF": SUF, "C": C, "p30_S_at_s025": {"w-1": sm, "w0": s0, "w+1": sp},
                   "p30_weight": pw, "wsmin_m1": f"WSMIN(-1):{fmt(smin['m1'])}", "wsmin_0": f"WSMIN(0):{fmt(smin['0'])}",
                   "wsmin_p1": f"WSMIN(+1):{fmt(smin['p1'])}", "wsmin_p2": f"WSMIN(+2):{fmt(smin['p2'])}",
                   "flip_lowers_threshold": flip,
                   "shift_fields_needed": "SHIFT_FIELDS_NEEDED:" + (",".join(need) or "NONE"),
                   "shift_fields_suffice": "SHIFT_FIELDS_SUFFICE:" + (",".join(suff) or "NONE"),
                   "cos_split_by_host": csb, "cos_split_by_host_detail": byhost, "cos_subspace": cv,
                   "null_S_pooled": {n: T[n]["S"] for p_ in NULLS for n in NULLS[p_]}}

    T, V = verdict(cells)
    S3 = stats(m3r["all"], cells)["S"]
    bw3 = sum(qrows["full"][k] == m3r["all"][k][2] for k in m3r["all"])
    bw6 = sum(qrows["meanD_host"][k] == m6r["meanD_host"][k][2] for k in m6r["meanD_host"])
    bw11 = {n: sum(qrows[n][k] == m11r[n][k][2] for k in m11r[n]) for n in M11_S}
    S11 = {n: stats(m11r[n], cells)["S"] for n in M11_S}
    gate = {"S_full": T["full"]["S"], "S_M3_all": S3, "full_rows_bitwise_eq_M3": bw3,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bw6,
            "m11_rows_bitwise_eq_M11": bw11, "S_m11_arms": {n: T[n]["S"] for n in M11_S}, "S_M11": S11,
            "pass": (T["full"]["S"] == S3 == 51 and bw3 == 208 and T["meanD_host"]["S"] == 39 and bw6 == 208
                     and all(bw11[n] == 208 and T[n]["S"] == S11[n] == M11_S[n] for n in M11_S))}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6_M11") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS + ("p30_S_at_s025",)}
        logo[g]["SUF"] = sorted(n for n, b in vv["SUF"].items() if b)
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
    med = lambda v, f: round(statistics.median(x[f] for x in v), 4)
    c_sum = {}
    for n, v in sorted(cstat.items()):
        c_sum[n] = {"energy_share_median": med(v, "energy_share"),
                    "energy_share_min": round(min(x["energy_share"] for x in v), 4)}
        for f in ("cos_median", "alpha_median"):
            if f in v[0]:
                c_sum[n][f + "_of_rows"] = med(v, f)
        if "alpha_max" in v[0]:
            c_sum[n].update(alpha_max=round(max(x["alpha_max"] for x in v), 4),
                            capped_share_mean=round(statistics.mean(x["capped_share"] for x in v), 4))
        if "null_err" in v[0]:
            c_sum[n]["null_err_max"] = max(x["null_err"] for x in v)
        if "pos_share_before" in v[0]:
            c_sum[n]["pos30_share_median"] = round(statistics.median(x["pos_share_before"]["30"] for x in v), 4)
    size = {n: round(statistics.median(dnorm[n][k] / dnorm["full"][k] for k in dnorm["full"]), 4) for n in names}

    res = {"schema": "JEV_A461_MECH_M12_ANALYSIS_V1", "table": T, "consistency_gate": gate,
           "rules_applied": V, "verdicts": final, "leave_one_donor_group_out": logo, "per_host_S": per_host,
           "contrast_stats": c_sum, "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m12_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final, "p30_S_at_s025": V["p30_S_at_s025"],
                      "cos_split_by_host": V["cos_split_by_host_detail"],
                      "S": {n: T[n]["S"] for n in names}, "SPEC": {n: T[n]["SPEC"] for n in names},
                      "contrast_stats": c_sum, "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
