#!/usr/bin/env python3
"""A461-MECH-M10 R1 analysis: applies the rules frozen in m10_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm, the meanD_host arm with the M6 pooled-donor arm and the cs1 / chW / ch10 / chR /
cpar16_sm / cperp16_sm / crand16_sm arms with the M9 arms of the same name (pinned raw rows, bitwise, and their S
values). Derived from the M9 analysis (59badbec)."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "f127d850223174f8ef10997c8539a2c348102b89"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"
BLOB_M9_RAW = "c74e5117da511f7d0be1503746b752f1a41c62b8"
VERDICTS = ("contrast_heads_sm", "contrast_position", "shift_location", "contrast_subspace", "gain_tfine")
M9_S = {"cs1": 39, "chW": 39, "ch10": 25, "chR": 0, "cpar16_sm": 27, "cperp16_sm": 39, "crand16_sm": 7}
RANDS = ("crand16_sm",) + tuple(f"crand16_sm_s{i}" for i in range(1, 5))


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
    """2 x 2 verdict on SUF(a_), SUF(b_): names = (a only, b only, both, neither)."""
    return names[2] if a_ and b_ else names[0] if a_ else names[1] if b_ else names[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m6-raw", required=True, type=Path)
    ap.add_argument("--m9-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 / M9 baseline check")
    a = ap.parse_args()
    for p_, b_, n_ in ((a.design, BLOB_DESIGN, "design"), (a.m3_raw, BLOB_M3_RAW, "M3 raw"),
                       (a.m6_raw, BLOB_M6_RAW, "M6 raw"), (a.m9_raw, BLOB_M9_RAW, "M9 raw")):
        if blob(p_) != b_:
            raise SystemExit(f"{n_} pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3, m6, m9 = jsonl(a.raw), jsonl(a.m3_raw), jsonl(a.m6_raw), jsonl(a.m9_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    hb = lambda rows_: {x["target_scene"]: ra(x["questions"])[0] for x in rows_
                        if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    base, m3base, m9base = hb(raw), hb(m3), hb(m9)
    if (base != m3base or base != m9base) and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3 / M9")
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
    m3r, m6r, m9r = ref(m3, m3base, ("all",)), ref(m6, m3base, ("meanD_host",)), ref(m9, m9base, tuple(M9_S))
    names = [n for n, _op, _cl, _ex in design["arms"]]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values())
            or len(m3r["all"]) != 208 or len(m6r["meanD_host"]) != 208 or any(len(m9r[n]) != 208 for n in M9_S)):
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
                "SPEC": frac >= 0.75 and maj >= 10,   # as M2-M9, also under leave-one-group-out (13 groups)
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    tfine = [(f"g{tn}_1", tv) for tn, tv in design["t_fine"]] + [("cs1", 1.0)]

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        SUF = {n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"] for n in names}
        C = {n: T[n]["median_dM_contrast"] for n in names}
        hv = four(SUF["chW_sm"], SUF["chR_sm"], ("CONTRAST_SM_IN_WRITER_HEADS", "CONTRAST_SM_OUTSIDE_WRITER_HEADS",
                                                 "CONTRAST_SM_EITHER_HEAD_SET", "CONTRAST_SM_NEEDS_ALL_HEADS"))
        hv += ("+H10" if SUF["ch10_sm"] else "") + ("+WX10" if SUF["chWx10_sm"] else "")
        pv = four(SUF["cpos29"], SUF["cpos30"], ("CONTRAST_AT_P29", "CONTRAST_AT_P30", "CONTRAST_AT_EITHER_POSITION",
                                                 "CONTRAST_NEEDS_BOTH_POSITIONS"))
        lv = four(SUF["sh2930"], SUF["sh0_28"], ("SHIFT_AT_CONTRAST_POSITIONS", "SHIFT_AT_OTHER_POSITIONS",
                                                 "SHIFT_AT_EITHER", "SHIFT_NEEDS_ALL_POSITIONS"))
        rS = [T[n]["S"] for n in RANDS]
        null_ok = statistics.median(rS) <= 5 and not any(T[n]["SPEC"] for n in RANDS)
        sv = four(SUF["cpar16_sm"], SUF["cperp16_sm"], ("CONTRAST_IN_COMMON_SUBSPACE", "CONTRAST_OUTSIDE_COMMON_SUBSPACE",
                                                        "CONTRAST_BOTH_PARTS", "CONTRAST_NOT_SPLITTABLE"))
        if sv != "CONTRAST_NOT_SPLITTABLE" and not null_ok:
            sv += "_UNRESOLVED"
        ts = next((tv for n, tv in tfine if SUF[n]), None)
        return T, {"SUF": SUF, "C": C, "null_S": dict(zip(RANDS, rS)), "null_S_median": statistics.median(rS),
                   "null_S_max": max(rS), "split_null5_holds": null_ok, "t_star_fine": ts,
                   "contrast_heads_sm": hv, "contrast_position": pv, "shift_location": lv, "contrast_subspace": sv,
                   "gain_tfine": f"GAIN_TFINE:{ts}" if ts is not None else "GAIN_TFINE_NONE"}

    T, V = verdict(cells)
    S3 = stats(m3r["all"], cells)["S"]
    bw3 = sum(qrows["full"][k] == m3r["all"][k][2] for k in m3r["all"])
    bw6 = sum(qrows["meanD_host"][k] == m6r["meanD_host"][k][2] for k in m6r["meanD_host"])
    bw9 = {n: sum(qrows[n][k] == m9r[n][k][2] for k in m9r[n]) for n in M9_S}
    S9 = {n: stats(m9r[n], cells)["S"] for n in M9_S}
    gate = {"S_full": T["full"]["S"], "S_M3_all": S3, "full_rows_bitwise_eq_M3": bw3,
            "S_meanD_host": T["meanD_host"]["S"], "meanD_host_rows_bitwise_eq_M6": bw6,
            "m9_rows_bitwise_eq_M9": bw9, "S_m9_arms": {n: T[n]["S"] for n in M9_S}, "S_M9": S9,
            "pass": (T["full"]["S"] == S3 == 51 and bw3 == 208 and T["meanD_host"]["S"] == 39 and bw6 == 208
                     and all(bw9[n] == 208 and T[n]["S"] == S9[n] == M9_S[n] for n in M9_S))}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3_M6_M9") for k in VERDICTS}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in VERDICTS + ("null_S", "null_S_median", "split_null5_holds", "t_star_fine")}
        logo[g]["SUF"] = sorted(n for n, b in vv["SUF"].items() if b)
    tgrid = {f"t={tv}": {"arm": n, "S": T[n]["S"], "C": T[n]["median_dM_contrast"],
                         "J": [T[n]["J_main"], T[n]["J_round"]], "SUF": V["SUF"][n]} for n, tv in tfine}
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
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
                            capped_share_mean=round(statistics.mean(x["capped_share"] for x in v), 4),
                            zero_part_share_median=med(v, "zero_part_share"))
    pos_pairs = [a_["energy_share"] + b_["energy_share"] for a_, b_ in zip(cstat["cpos29"], cstat["cpos30"])]
    pos_sum = {"p29_plus_p30_share_min": round(min(pos_pairs), 6), "p29_plus_p30_share_max": round(max(pos_pairs), 6)}
    size = {n: round(statistics.median(dnorm[n][k] / dnorm["full"][k] for k in dnorm["full"]), 4) for n in names}

    res = {"schema": "JEV_A461_MECH_M10_ANALYSIS_V1", "table": T, "t_fine": tgrid, "consistency_gate": gate,
           "rules_applied": V, "verdicts": final, "leave_one_donor_group_out": logo, "per_host_S": per_host,
           "contrast_stats": c_sum, "position_energy": pos_sum, "median_change_norm_rel_full": size, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m10_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": final, "null_S": V["null_S"], "t_fine": tgrid,
                      "S": {n: T[n]["S"] for n in names}, "SPEC": {n: T[n]["SPEC"] for n in names},
                      "contrast_stats": c_sum, "position_energy": pos_sum,
                      "median_change_norm_rel_full": size}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
