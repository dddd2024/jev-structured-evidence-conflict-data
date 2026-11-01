#!/usr/bin/env python3
"""A461-MECH-M6 R1 analysis: applies the rules frozen in m6_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm and the xdonor_BULK arm with the M5 third-donor arm (pinned raw rows), bitwise."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "43967513c3dbcad74dd7b024b67a16463f456ffc"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M5_RAW = "f03ce4e96e6eb4ea76b43d9627bad62c87ca8c4d"


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
    ap.add_argument("--m5-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 baseline check")
    a = ap.parse_args()
    if blob(a.design) != BLOB_DESIGN:
        raise SystemExit("design pin")
    if blob(a.m3_raw) != BLOB_M3_RAW:
        raise SystemExit("M3 raw pin")
    if blob(a.m5_raw) != BLOB_M5_RAW:
        raise SystemExit("M5 raw pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m5 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m5_raw)
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
    m5xd = {(x["donor"], x["host"], x["source_kind"]): x for x in m5 if x["patch"] and x["patch"]["arm"] == "xdonor_BULK"}
    names = [n for n, _op, _cl, _ex in design["arms"]]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values())
            or len(m3all) != 208 or len(m5xd) != 208):
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
                "SPEC": frac >= 0.75 and maj >= 10,   # as M2-M4, also under leave-one-group-out (13 groups)
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    ks, rks = design["ks"], design["rand_ks"]

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        suf = lambda n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"]
        SUF = {n: suf(n) for n in names}
        if SUF["meanD_host"] and not SUF["meanH_host"]:
            sv = "SHARED_DONOR_COMPONENT"
        elif SUF["meanD_host"] and SUF["meanH_host"]:
            sv = "GENERIC_CONTEXT_SHIFT"
        elif SUF["meanD_donor"]:
            sv = "SHARED_NEEDS_DONOR_REST"
        else:
            sv = "NOT_SHARED_BY_AVERAGE"
        kstar = next((k for k in ks if SUF[f"lr{k}"]), None)
        if kstar is None:
            lv, null = "NOT_LOWRANK_LE64", None
        else:
            null = f"rand{max(kstar, 4)}"
            ok = T[null]["S"] <= 5 and not T[null]["SPEC"]
            lv = (f"LOWRANK:{kstar}" if ok else f"LOWRANK_UNRESOLVED:{kstar}")
        return T, {"SUF": SUF, "shared": sv, "lowrank": lv, "k_star": kstar, "null_arm": null}

    T, V = verdict(cells)
    m3S = sum(m3all[(d, h, "main")][1] and not m3all[(d, h, "round")][1] for d, h in cells)
    bitwise = sum(qrows["full"][k] == m3all[k][2] for k in m3all)
    bitwise5 = sum(qrows["xdonor_BULK"][k] == m5xd[k]["questions"] for k in m5xd)
    gate = {"S_full": T["full"]["S"], "S_M3_all": m3S, "full_rows_bitwise_eq_M3": bitwise,
            "S_xdonor": T["xdonor_BULK"]["S"], "xdonor_rows_bitwise_eq_M5": bitwise5,
            "pass": T["full"]["S"] == m3S == 51 and bitwise == 208 and T["xdonor_BULK"]["S"] == 51 and bitwise5 == 208}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M5") for k in ("shared", "lowrank")}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in ("shared", "lowrank", "k_star")}
        logo[g]["SUF"] = sorted(n for n, b in vv["SUF"].items() if b)
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
    alpha_sum = {n: {"energy_median_of_medians": round(statistics.median(x["median"] for x in v), 4),
                     "energy_min": round(min(x["min"] for x in v), 4),
                     "basis_sv_share_median": round(statistics.median(x["basis_sv_share_k"] for x in v), 4)}
                 for n, v in sorted(alpha.items())}
    size = {n: round(statistics.median(dnorm[n][k] / dnorm["full"][k] for k in dnorm["full"]), 4) for n in names}

    res = {"schema": "JEV_A461_MECH_M6_ANALYSIS_V1", "table": T, "consistency_gate": gate, "rules_applied": V,
           "shared_verdict": final["shared"], "lowrank_verdict": final["lowrank"],
           "leave_one_donor_group_out": logo, "per_host_S": per_host, "subspace_energy": alpha_sum,
           "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m6_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "rules_applied": V, "shared_verdict": final["shared"],
                      "lowrank_verdict": final["lowrank"], "S": {n: T[n]["S"] for n in names},
                      "SPEC": {n: T[n]["SPEC"] for n in names}, "subspace_energy": alpha_sum,
                      "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
