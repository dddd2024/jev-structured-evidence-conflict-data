#!/usr/bin/env python3
"""A461-MECH-M8 R1 analysis: applies the rules frozen in m8_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm and the meanD_host arm with the M6 pooled-donor arm (pinned raw rows, bitwise), and the
M7 replays dlr64_sm / rand64_sm with their M7 S values; the bitwise equality of the M7 replay rows is reported.
Derived from the M7 analysis (7c4f9169)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "14cee4c2cffe30d78338de8063c72110f223f0bb"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M7_RAW = "0383fccf01ad027ae14c59c8fc9830f1d398219e"
VERDICTS = ("xdelta_lowrank", "twopart", "contrast_source", "cshift", "nonadditivity")


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
    if blob(a.m7_raw) != BLOB_M7_RAW:
        raise SystemExit("M7 raw pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m6, m7 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw), jsonl(a.m7_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    hb = lambda rows_: {x["target_scene"]: ra(x["questions"])[0] for x in rows_
                        if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    base, m3base, m7base = hb(raw), hb(m3), hb(m7)
    if (base != m3base or base != m7base) and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3 / M7")
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
    m7r = collections.defaultdict(dict)
    for x in m7:
        if x["patch"]:
            M, J = ra(x["questions"])
            m7r[x["patch"]["arm"]][(x["donor"], x["host"], x["source_kind"])] = (M - m7base[x["host"]], J, x["questions"])
    names = [n for n, _op, _cl, _ex in design["arms"]]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values())
            or len(m3all) != 208 or len(m6md) != 208 or any(len(m7r[n]) != 208 for n in ("dlr16_sm", "dlr64_sm",
                                                                                          "rand64_sm", "rcD"))):
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
                "SPEC": frac >= 0.75 and maj >= 10,   # as M2-M7, also under leave-one-group-out (13 groups)
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    ks, tp_ks = design["ks"], design["tp_ks"]
    cs_s = [(f"cs{n}", s) for n, s in design["cs"]]

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        suf = lambda n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"]
        SUF = {n: suf(n) for n in names}
        null_ok = T["rand64_sm"]["S"] <= 5 and not T["rand64_sm"]["SPEC"]
        kx = next((k for k in ks if SUF[f"xdlr{k}_sm"]), None)
        if kx is None:
            xv = "NOT_XDELTA_LOWRANK_LE64"
        else:
            xv = f"XDELTA_LOWRANK:{kx}" if null_ok else f"XDELTA_LOWRANK_UNRESOLVED:{kx}"
        kt = next((k for k in tp_ks if SUF[f"tp{k}"]), None)
        if kt is None:
            tv = "NOT_TWOPART"
        else:
            tv = f"TWOPART:{kt}" if null_ok else f"TWOPART_UNRESOLVED:{kt}"
        if SUF["tpD64"]:
            cv = "POOLED_CONTRAST_SUFFICES"
        elif SUF["tp64"]:
            cv = "OWN_CONTRAST_NEEDED"
        else:
            cv = "CONTRAST_SOURCE_NA"
        ss = next((s for n, s in cs_s if s > 0 and SUF[n]), None)
        sv = f"CS_SUFFICIENT:{ss}" if ss is not None else "CS_NONE"
        c_cs2 = T["cs2"]["median_dM_contrast"]
        c_rc = stats(m7r["rcD"], cs)["median_dM_contrast"]
        nv = "CONTRAST_NONADDITIVE" if c_cs2 > 0 and c_cs2 >= 3 * abs(c_rc) else "CONTRAST_ADDITIVE_OR_WEAK"
        return T, {"SUF": SUF, "null_holds": null_ok, "k_star_xdelta": kx, "k_star_twopart": kt, "s_star": ss,
                   "C_cs2": c_cs2, "C_rcD_M7": c_rc, "xdelta_lowrank": xv, "twopart": tv, "contrast_source": cv,
                   "cshift": sv, "nonadditivity": nv}

    T, V = verdict(cells)
    m3S = sum(m3all[(d, h, "main")][1] and not m3all[(d, h, "round")][1] for d, h in cells)
    bitwise = sum(qrows["full"][k] == m3all[k][2] for k in m3all)
    bitwise6 = sum(qrows["meanD_host"][k] == m6md[k]["questions"] for k in m6md)
    m7S = {n: stats(m7r[n], cells)["S"] for n in ("dlr64_sm", "rand64_sm")}
    replay7 = {"dlr64_sm": sum(qrows["dlr64_sm"][k] == m7r["dlr64_sm"][k][2] for k in m7r["dlr64_sm"]),
               "rand64_sm": sum(qrows["rand64_sm"][k] == m7r["rand64_sm"][k][2] for k in m7r["rand64_sm"]),
               "tp16_main_vs_M7_dlr16_sm": sum(qrows["tp16"][(d, h, "main")] == m7r["dlr16_sm"][(d, h, "main")][2]
                                               for d, h in cells),
               "tp64_main_vs_M7_dlr64_sm": sum(qrows["tp64"][(d, h, "main")] == m7r["dlr64_sm"][(d, h, "main")][2]
                                               for d, h in cells),
               "tpD64_main_vs_M7_dlr64_sm": sum(qrows["tpD64"][(d, h, "main")] == m7r["dlr64_sm"][(d, h, "main")][2]
                                                for d, h in cells)}
    cs0_same = sum(qrows["cs0"][(d, h, "main")] == qrows["cs0"][(d, h, "round")] for d, h in cells)
    gate = {"S_full": T["full"]["S"], "S_M3_all": m3S, "full_rows_bitwise_eq_M3": bitwise,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bitwise6,
            "S_dlr64_sm": T["dlr64_sm"]["S"], "S_rand64_sm": T["rand64_sm"]["S"], "S_M7": m7S,
            "pass": (T["full"]["S"] == m3S == 51 and bitwise == 208 and T["meanD_host"]["S"] == 39 and bitwise6 == 208
                     and T["dlr64_sm"]["S"] == m7S["dlr64_sm"] == 24 and T["rand64_sm"]["S"] == m7S["rand64_sm"] == 1)}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6_M7") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS + ("k_star_xdelta", "k_star_twopart", "s_star", "null_holds")}
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

    res = {"schema": "JEV_A461_MECH_M8_ANALYSIS_V1", "table": T, "consistency_gate": gate, "rules_applied": V,
           "verdicts": final, "m7_replay_rows_bitwise": replay7, "cs0_main_eq_round_rows": cs0_same,
           "leave_one_donor_group_out": logo, "per_host_S": per_host, "subspace_stats": alpha_sum,
           "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m8_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final, "C_cs2": V["C_cs2"], "C_rcD_M7": V["C_rcD_M7"],
                      "m7_replay_rows_bitwise": replay7, "cs0_main_eq_round_rows": cs0_same,
                      "S": {n: T[n]["S"] for n in names}, "SPEC": {n: T[n]["SPEC"] for n in names},
                      "subspace_stats": alpha_sum, "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
