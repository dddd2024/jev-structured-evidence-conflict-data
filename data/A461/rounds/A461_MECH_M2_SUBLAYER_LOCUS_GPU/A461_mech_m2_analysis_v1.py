#!/usr/bin/env python3
"""A461-MECH-M2 R1 analysis: applies the rules frozen in m2_design.json (written before the GPU run).
Resid L11 (main and round) comes from the pinned M1 raw rows, as the design states."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_M1_RAW = "298c7cdfab634cd6a6a9122fac90d41c87219c21"


def ra(qs):
    q = {x["id"]: x for x in qs}
    c, a = q["conflicting_vote"], q["certificate_action"]
    M = c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]
    L = dict(zip(a["keys"], a["logits"]))
    return M, (M > 0 and L["reject_conflict"] - max(L["accept"], L["wait"]) > 0)


def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true", help="self-test output only: skip the M1 baseline identity check")
    a = ap.parse_args()
    blob = subprocess.run(["git", "hash-object", str(a.m1_raw)], capture_output=True, text=True, check=True).stdout.strip()
    if blob != BLOB_M1_RAW:
        raise SystemExit("M1 raw pin")
    design = json.loads(a.design.read_text("utf8"))
    raw, m1 = jsonl(a.raw), jsonl(a.m1_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    base = {x["target_scene"]: ra(x["questions"])[0] for x in raw if x["capture"] and x["source_kind"] == "host"}
    m1base = {x["target_scene"]: ra(x["questions"])[0] for x in m1 if x["capture"] and x["source_kind"] == "host"}
    if base != m1base and not a.fake_dry_run:
        raise SystemExit("host baselines differ from M1")
    arm = collections.defaultdict(dict)   # (comp, L) -> (d, h, src) -> (dM, J)
    for x in raw:
        if x["patch"]:
            M, J = ra(x["questions"])
            arm[(x["patch"]["component"], x["layer"])][(x["donor"], x["host"], x["source_kind"])] = (M - base[x["host"]], J)
    for x in m1:
        if x["patch"] and x["cross_group"] and x["source_kind"] in ("main", "round"):
            M, J = ra(x["questions"])
            arm[("resid", 11)][(x["donor"], x["host"], x["source_kind"])] = (M - base[x["host"]], J)
    cells = sorted({(d, h) for (d, h, _s) in arm[("resid", 11)]})
    if len(cells) != 104 or any(len(v) != 208 for v in arm.values()):
        raise SystemExit("cell census")

    def stats(key, cs=cells):
        v = arm[key]
        S = sum(v[(d, h, "main")][1] and not v[(d, h, "round")][1] for d, h in cs)
        gt = [v[(d, h, "main")][0] > v[(d, h, "round")][0] for d, h in cs]
        g = collections.defaultdict(list)
        for (d, h), b in zip(cs, gt):
            g[gd[d]].append(b)
        maj = sum(sum(b) * 2 > len(b) for b in g.values())
        frac = sum(gt) / len(gt)
        return {"S": S, "J_main": sum(v[(d, h, "main")][1] for d, h in cs), "J_round": sum(v[(d, h, "round")][1] for d, h in cs),
                "frac_main_gt_round": round(frac, 4), "groups_majority": maj, "SPEC": frac >= 0.75 and maj >= 10,
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4)}

    def verdict(cs=cells):
        T = {f"{c}_L{L}": stats((c, L), cs) for (c, L) in sorted(arm)}
        S11 = T["resid_L11"]["S"]
        L_f = next((L for L in (7, 8, 9, 10, 11) if T[f"resid_L{L}"]["S"] >= S11 / 2 and T[f"resid_L{L}"]["SPEC"]), None)
        writers = {}
        for L in (8, 9, 10, 11):
            ref = T[f"resid_L{L}"]["S"]
            writers[L] = {c: T[f"{c}_L{L}"]["S"] >= ref / 2 and T[f"{c}_L{L}"]["SPEC"] and ref > 0 for c in ("mixer", "mlp")}
        L_ref = max(L_f, 8) if L_f is not None else None
        if L_ref is None:
            v = "NO_FORMATION_LAYER (resid L11 itself fails the rule)"
        else:
            w = writers[L_ref]
            v = ("BOTH_SUFFICIENT" if w["mixer"] and w["mlp"] else "MIXER_WRITER" if w["mixer"]
                 else "MLP_WRITER" if w["mlp"] else "NEITHER_ALONE")
        return T, L_f, L_ref, writers, v
    T, L_f, L_ref, writers, v = verdict()
    logo = {}
    for g in sorted(set(gd.values())):
        _T, lf, lr, _w, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {"L_f": lf, "L_ref": lr, "verdict": vv}
    hosts = sorted({h for _d, h in cells})
    per_host = {h[:12]: {k: stats(tuple([k.split("_L")[0], int(k.split("_L")[1])]), [c for c in cells if c[1] == h])["S"]
                         for k in T} for h in hosts}
    res = {"schema": "JEV_A461_MECH_M2_ANALYSIS_V1", "table": T, "L_f": L_f, "L_ref": L_ref,
           "writers": {str(k): w for k, w in writers.items()}, "verdict": v,
           "leave_one_donor_group_out": logo, "per_host_S": per_host, "rules": design["preregistered_analysis"]}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m2_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("table", "L_f", "L_ref", "writers", "verdict")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
