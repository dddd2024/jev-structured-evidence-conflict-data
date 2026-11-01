#!/usr/bin/env python3
"""A461-MECH-M20 R1 analysis (CPU only; frozen before any M20 forward): natural-path necessity of the L11 append-span
write in the recognizing donors. Rules: m20_design.json -> preregistered_analysis."""
import argparse, collections, json, statistics, sys
from pathlib import Path


def L(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def ma(qs):
    q = {x["id"]: dict(zip(x["keys"], x["logits"])) for x in qs}
    c, a = q["conflicting_vote"], q["certificate_action"]
    return c["true"] - c["false"], a["reject_conflict"] - max(a["accept"], a["wait"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true")
    a = ap.parse_args()
    D = json.loads(a.design.read_text("utf8"))
    rows = L(a.raw)
    m1 = {(x["target_scene"], x["target_arm"]): x for x in L(a.m1_raw) if x["capture"]}
    donors, hosts = D["selection"]["donors"], D["selection"]["hosts"]
    gd = dict(donors)
    base = {x["target_scene"]: x for x in rows if x.get("capture") and x["target_arm"] == "new" and x["source_kind"] == "donor"}
    gate = {"donor_baselines": len(base),
            "donor_baselines_eq_M1": sum(base[d]["questions"] == m1[(d, "new")]["questions"] for d in base if (d, "new") in m1),
            "patch_rows": collections.Counter(x["patch"]["arm"] for x in rows if x.get("patch"))}
    gate["pass"] = (gate["donor_baselines"] == 14 == gate["donor_baselines_eq_M1"]
                    and gate["patch_rows"] == {"full_host": 104, "full_ctrl": 104, "bulk_host": 104, "bulk_ctrl": 104,
                                               "bulk_round_self": 14, "bulk_hostmean": 14})
    gate["patch_rows"] = dict(gate["patch_rows"])
    nat = {d: ma(base[d]["questions"]) for d in base}
    joint_d = {d for d, (M, A) in nat.items() if M > 0 and A > 0}
    P = collections.defaultdict(dict)
    for x in rows:
        if x.get("patch"):
            P[x["patch"]["arm"]][(x["donor"], x["host"])] = x

    def stats(arm, keep=lambda d: True):
        rr = {k: v for k, v in P[arm].items() if keep(k[0])}
        out = {"n": len(rr)}
        cl = [ma(v["questions"])[0] <= 0 for k, v in rr.items()]
        jl = [not (lambda M, A: M > 0 and A > 0)(*ma(v["questions"])) for k, v in rr.items() if k[0] in joint_d]
        out["C_loss"] = sum(cl) / len(cl) if cl else None
        out["J_loss"] = sum(jl) / len(jl) if jl else None
        out["median_dM"] = round(statistics.median(ma(v["questions"])[0] - nat[k[0]][0] for k, v in rr.items()), 4) if rr else None
        out["median_dA"] = round(statistics.median(ma(v["questions"])[1] - nat[k[0]][1] for k, v in rr.items()), 4) if rr else None
        return out

    def verdict(h_arm, c_arm, keep=lambda d: True):
        sh, sc = stats(h_arm, keep), stats(c_arm, keep)
        cells = [k for k in P[h_arm] if keep(k[0]) and k in P[c_arm]]
        lower = [ma(P[h_arm][k]["questions"])[0] < ma(P[c_arm][k]["questions"])[0] for k in cells]
        frac = sum(lower) / len(lower) if lower else 0
        per_d = collections.defaultdict(list)
        for k, l_ in zip(cells, lower):
            per_d[k[0]].append(l_)
        maj = sum(sum(v) * 2 > len(v) for v in per_d.values())
        diff = (sh["C_loss"] or 0) - (sc["C_loss"] or 0)
        v = ("NEC" if diff >= 0.40 and frac >= 0.75 and maj >= 10 else "NOT_NEC" if diff < 0.10 else "NEC_PARTIAL")
        return v, {"C_loss_diff": round(diff, 4), "frac_dM_host_lt_ctrl": round(frac, 4), "donors_majority": maj,
                   "host": sh, "ctrl": sc}

    vf, df = verdict("full_host", "full_ctrl")
    vb, db = verdict("bulk_host", "bulk_ctrl")
    verdicts = {"full": vf.replace("NEC", "NEC_FULL", 1) if vf != "NOT_NEC" else "NOT_NEC_FULL",
                "bulk": vb.replace("NEC", "NEC_BULK", 1) if vb != "NOT_NEC" else "NOT_NEC_BULK"}
    logo = {}
    for g in sorted(set(gd.values())):
        keep = lambda d, g=g: gd[d] != g
        logo[g] = {"full": verdict("full_host", "full_ctrl", keep)[0], "bulk": verdict("bulk_host", "bulk_ctrl", keep)[0]}
    per_host = {}
    for h, _ in hosts:
        per_host[h[:8]] = {arm: (lambda rr: sum(ma(v["questions"])[0] <= 0 for v in rr) / len(rr) if rr else None)(
            [v for k, v in P[arm].items() if k[1] == h]) for arm in ("full_host", "bulk_host")}
    if not gate["pass"]:
        verdicts = {k: "INCONSISTENT" for k in verdicts}
    res = {"schema": "JEV_A461_MECH_M20_ANALYSIS_V1", "fake_dry_run": a.fake_dry_run, "consistency_gate": gate,
           "verdicts": verdicts, "detail_full": df, "detail_bulk": db,
           "per_donor_arms": {arm: stats(arm) for arm in ("bulk_round_self", "bulk_hostmean")},
           "donor_native": {d[:8]: {"M": round(M, 4), "A": round(A, 4)} for d, (M, A) in nat.items()},
           "joint_donors": len(joint_d), "per_host_C_loss": per_host,
           "leave_one_donor_group_out": logo,
           "logo_stability": {k: sum(v[k] == (vf if k == "full" else vb) for v in logo.values()) for k in ("full", "bulk")},
           "rules": D["preregistered_analysis"]}
    o = a.out.expanduser().resolve()
    o.mkdir(parents=True, exist_ok=False)
    (o / "m20_analysis.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("consistency_gate", "verdicts", "detail_full", "detail_bulk", "per_donor_arms",
                                          "logo_stability")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
