#!/usr/bin/env python3
"""A461-MECH-M5 R1 analysis: applies the rules frozen in m5_design.json (written before the GPU run).
All arms target host new; sources donor new = main, donor ROUND = round. The consistency gate compares the full
arm with the M3 all-heads arm (pinned M3 raw), bitwise. Descriptive geometry of the donor - host differences per
key class from the saved capture files (row 0)."""
import argparse, collections, hashlib, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "26126568cce05db149d815b2faf3090e5e84c27b"
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"


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
    ap.add_argument("--captures", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 baseline and bitwise identity checks")
    a = ap.parse_args()
    import torch
    if blob(a.design) != BLOB_DESIGN:
        raise SystemExit("design pin")
    if blob(a.m3_raw) != BLOB_M3_RAW:
        raise SystemExit("M3 raw pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m3 = jsonl(a.raw), jsonl(a.m3_raw)
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
    for x in raw:
        if x["patch"]:
            M, J = ra(x["questions"])
            k = (x["donor"], x["host"], x["source_kind"])
            arm[x["patch"]["arm"]][k] = (M - base[x["host"]], J)
            qrows[x["patch"]["arm"]][k] = x["questions"]
            if x["alpha_stats"]:
                alpha[x["patch"]["arm"]].append(x["alpha_stats"])
    m3all = {}
    for x in m3:
        if x["patch"] and x["patch"]["arm"] == "all":
            M, J = ra(x["questions"])
            m3all[(x["donor"], x["host"], x["source_kind"])] = (M - m3base[x["host"]], J, x["questions"])
    names = [n for n, _op, _cl in design["arms"]]
    cells = sorted({(d, h) for (d, h, _s) in arm["full"]})
    if (len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values())
            or len(m3all) != 208):
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

    dirc = design["dir_classes"]

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        half = lambda n: Sf > 0 and T[n]["S"] >= Sf / 2 and T[n]["SPEC"]
        bulk = {"BULK_SUF": half("only_BULK"), "BULK_NEC": Sf > 0 and T["drop_BULK"]["S"] <= Sf / 2}
        D = [c for c in dirc if half(f"dir_{c}")]
        rand_null = T["dir_RAND"]["S"] <= 5 and not T["dir_RAND"]["SPEC"]
        pside = bool({"PARTNER", "ROUNDVOTES"} & set(D))
        bside = bool({"OTHER_ITEMS", "CONTEXT", "BULK"} & set(D))
        if not rand_null:
            v = "MAGNITUDE_SUFFICES"
        elif pside and not bside:
            v = "PARTNER_DIRECTION"
        elif bside and not pside:
            v = "BULK_DIRECTION"
        elif pside and bside:
            v = "BOTH_DIRECTIONS"
        elif D == ["SELF"]:
            v = "SELF_DIRECTION"
        elif not D:
            v = "NO_SINGLE_DIRECTION"
        else:
            v = "OTHER_DIRECTION:" + "+".join(D)   # e.g. ROUND_PEERS alone; not named in the prereg verdict list
        xd = "XD_HOLDS" if half("xdonor_BULK") else "XD_FAILS"
        return T, dict(bulk, D=D, RAND_NULL=rand_null, verdict=v, content=xd)

    T, V = verdict(cells)
    m3S = sum(m3all[(d, h, "main")][1] and not m3all[(d, h, "round")][1] for d, h in cells)
    bitwise = sum(qrows["full"][k] == m3all[k][2] for k in m3all)
    gate = {"S_full": T["full"]["S"], "S_M3_all": m3S, "full_rows_bitwise_eq_M3": bitwise,
            "pass": T["full"]["S"] == m3S == 51 and bitwise == 208}
    final = {k: (V[k] if gate["pass"] else "INCONSISTENT_WITH_M3") for k in ("verdict", "content")}
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {k: vv[k] for k in ("verdict", "content", "D", "RAND_NULL", "BULK_SUF", "BULK_NEC")}
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
    alpha_sum = {n: {"median_of_medians": round(statistics.median(x["median"] for x in v), 4),
                     "max": round(max(x["max"] for x in v), 4), "min": round(min(x["min"] for x in v), 4)}
                 for n, v in sorted(alpha.items())}

    # ---------- descriptive geometry of donor - host differences (row 0, donor new vs host new) ----------
    caps = {x["capture"]["tag"]: x for x in raw if x["capture"]}
    loaded = {}

    def load(tag):
        if tag not in loaded:
            x = caps[tag]
            for k in ("capture_file", "class_file"):
                f = a.captures / x[k]["name"]
                if hashlib.sha256(f.read_bytes()).hexdigest() != x[k]["sha256"]:
                    raise SystemExit(f"capture file sha {tag}")
            loaded[tag] = (torch.load(a.captures / x["capture_file"]["name"], weights_only=True)[0].double(),
                           {k: t.double() for k, t in
                            torch.load(a.captures / x["class_file"]["name"], weights_only=True)["contrib"].items()})
        return loaded[tag]
    groups = {c: [c] for c in design["base_classes"]}
    groups.update(ROUNDVOTES=["PARTNER", "ROUND_PEERS"], BULK=design["bulk"])
    geo = collections.defaultdict(lambda: {"norm_ratio": [], "cos": []})
    for d, h in cells:
        xd, cd = load(f"new:{d[:12]}")
        xh, ch = load(f"new:{h[:12]}")
        df = xd - xh
        for c, cl in groups.items():
            dc = sum(cd[k] - ch[k] for k in cl)
            geo[c]["norm_ratio"].append(float((dc.norm(dim=-1) / df.norm(dim=-1)).mean()))
            geo[c]["cos"].append(float(torch.nn.functional.cosine_similarity(dc, df, dim=-1).mean()))
    geometry = {c: {"median_norm_ratio_to_full_delta": round(statistics.median(v["norm_ratio"]), 4),
                    "median_cos_to_full_delta": round(statistics.median(v["cos"]), 4)} for c, v in geo.items()}

    res = {"schema": "JEV_A461_MECH_M5_ANALYSIS_V1", "table": T, "consistency_gate": gate, "rules_applied": V,
           "verdict": final["verdict"], "content": final["content"], "leave_one_donor_group_out": logo,
           "per_host_S": per_host, "alpha": alpha_sum, "delta_geometry": geometry, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m5_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "rules_applied": V, "verdict": final["verdict"],
                      "content": final["content"], "S": {n: T[n]["S"] for n in names},
                      "SPEC": {n: T[n]["SPEC"] for n in names}, "alpha": alpha_sum, "delta_geometry": geometry},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
