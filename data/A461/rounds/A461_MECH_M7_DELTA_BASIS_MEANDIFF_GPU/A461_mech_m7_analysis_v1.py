#!/usr/bin/env python3
"""A461-MECH-M7 R1 analysis: applies the rules frozen in m7_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm and the meanD_host arm with the M6 pooled-donor arm (pinned raw rows), bitwise.
Derived from the M6 analysis (325699b5)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "f7d5318c1bfe24521831cc322be08bd6ed08fa17"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
VERDICTS = ("delta_lowrank", "m6_lr64_size", "meandiff", "round_contrast")


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
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 baseline check")
    a = ap.parse_args()
    if blob(a.design) != BLOB_DESIGN:
        raise SystemExit("design pin")
    if blob(a.m3_raw) != BLOB_M3_RAW:
        raise SystemExit("M3 raw pin")
    if blob(a.m6_raw) != BLOB_M6_RAW:
        raise SystemExit("M6 raw pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m6 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    base = {x["target_scene"]: ra(x["questions"])[0] for x in raw
            if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    m3base = {x["target_scene"]: ra(x["questions"])[0] for x in m3
              if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    if base != m3base and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3")
    arm = collections.defaultdict(dict)    # arm -> (d, h, main|round) -> (dM, J)
    qrows = collections.defaultdict(dict)
    alpha = collections.defaultdict(list)
    dnorm = collections.defaultdict(dict)  # arm -> (d, h, src) -> mean change norm at the span
    for x in raw:
        if x["patch"]:
            M, J = ra(x["questions"])
            k = (x["donor"], x["host"], x["source_kind"])
            arm[x["patch"]["arm"]][k] = (M - base[x["host"]], J)
            qrows[x["patch"]["arm"]][k] = x["questions"]
            dnorm[x["patch"]["arm"]][k] = x["span_stats"]["delta_norm_mean"]
            if x["alpha_stats"]:
                alpha[x["patch"]["arm"]].append(x["alpha_stats"])
    m3all = {}
    for x in m3:
        if x["patch"] and x["patch"]["arm"] == "all":
            M, J = ra(x["questions"])
            m3all[(x["donor"], x["host"], x["source_kind"])] = (M - m3base[x["host"]], J, x["questions"])
    m6md = {(x["donor"], x["host"], x["source_kind"]): x for x in m6 if x["patch"] and x["patch"]["arm"] == "meanD_host"}
    names = [n for n, _op, _cl, _ex in design["arms"]]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values())
            or len(m3all) != 208 or len(m6md) != 208):
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
                "SPEC": frac >= 0.75 and maj >= 10,   # as M2-M6, also under leave-one-group-out (13 groups)
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    ks = design["ks"]

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        suf = lambda n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"]
        SUF = {n: suf(n) for n in names}
        null_ok = T["rand64_sm"]["S"] <= 5 and not T["rand64_sm"]["SPEC"]
        kstar = next((k for k in ks if SUF[f"dlr{k}_sm"]), None)
        if kstar is None:
            dv = "NOT_DELTA_LOWRANK_LE64"
        else:
            dv = f"DELTA_LOWRANK:{kstar}" if null_ok else f"DELTA_LOWRANK_UNRESOLVED:{kstar}"
        sv = "LR64_SIZE_LIMITED" if SUF["lr64_sm"] else "LR64_BASIS_LIMITED"
        sstar = next((s for s in (1, 2) if SUF[f"mdir{s}"]), None)
        if sstar is None:
            mv = "NOT_MEANDIFF"
        else:
            mv = f"MEANDIFF_DIRECTION:{sstar}" if null_ok else f"MEANDIFF_UNRESOLVED:{sstar}"
        if SUF["rcH"]:
            rv = "RC_GENERIC"
        elif SUF["rcD"]:
            rv = "RC_DONOR_POOL_ONLY"
        else:
            rv = "RC_INSUFFICIENT"
        return T, {"SUF": SUF, "null_holds": null_ok, "k_star": kstar, "s_star": sstar, "delta_lowrank": dv,
                   "m6_lr64_size": sv, "meandiff": mv, "round_contrast": rv}

    T, V = verdict(cells)
    m3S = sum(m3all[(d, h, "main")][1] and not m3all[(d, h, "round")][1] for d, h in cells)
    bitwise = sum(qrows["full"][k] == m3all[k][2] for k in m3all)
    bitwise6 = sum(qrows["meanD_host"][k] == m6md[k]["questions"] for k in m6md)
    gate = {"S_full": T["full"]["S"], "S_M3_all": m3S, "full_rows_bitwise_eq_M3": bitwise,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bitwise6,
            "pass": T["full"]["S"] == m3S == 51 and bitwise == 208 and T["meanD_host"]["S"] == 39 and bitwise6 == 208}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS + ("k_star", "s_star", "null_holds")}
        logo[g]["SUF"] = sorted(n for n, b in vv["SUF"].items() if b)
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
    med = lambda v, f: round(statistics.median(x[f] for x in v), 4)
    alpha_sum = {n: {"energy_median_of_medians": med(v, "median"), "energy_min": round(min(x["min"] for x in v), 4),
                     "basis_sv_share_median": (med(v, "basis_sv_share_k") if v[0]["basis_sv_share_k"] is not None
                                               else None),
                     "alpha_median_of_medians": med(v, "alpha_median"),
                     "alpha_max": round(max(x["alpha_max"] for x in v), 4),
                     "capped_share_mean": round(statistics.mean(x["capped_share"] for x in v), 4)}
                 for n, v in sorted(alpha.items())}
    size = {n: round(statistics.median(dnorm[n][k] / dnorm["full"][k] for k in dnorm["full"]), 4) for n in names}

    res = {"schema": "JEV_A461_MECH_M7_ANALYSIS_V1", "table": T, "consistency_gate": gate, "rules_applied": V,
           "verdicts": final, "leave_one_donor_group_out": logo, "per_host_S": per_host, "subspace_stats": alpha_sum,
           "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m7_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final, "S": {n: T[n]["S"] for n in names},
                      "SPEC": {n: T[n]["SPEC"] for n in names}, "subspace_stats": alpha_sum,
                      "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
