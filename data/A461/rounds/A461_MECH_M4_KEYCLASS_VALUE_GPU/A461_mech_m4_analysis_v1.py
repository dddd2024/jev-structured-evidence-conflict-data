#!/usr/bin/env python3
"""A461-MECH-M4 R1 analysis: applies the rules frozen in m4_design.json (written before the GPU run).
Key-class arms (target host new; sources donor new = main, donor ROUND = round) and the partner value swap
(source donor new; targets host new = main, host ROUND = round). The consistency gate compares the full arm with
the M3 all-heads arm (pinned M3 raw), bitwise."""
import argparse, collections, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "7ec989c0f70d3fcead4b64b035a32b6655110575"
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
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M3 baseline and bitwise identity checks")
    a = ap.parse_args()
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
    base = {(x["target_scene"], x["target_arm"]): ra(x["questions"])[0] for x in raw
            if x["capture"] and x["source_kind"] == "host"}
    m3base = {x["target_scene"]: ra(x["questions"])[0] for x in m3
              if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    if {h: base[(h, "new")] for h in hosts} != m3base and not a.fake_dry_run:
        raise SystemExit("host new baselines differ from M3")
    arm = collections.defaultdict(dict)    # arm -> (d, h, main|round) -> (dM, J)
    qrows = collections.defaultdict(dict)
    for x in raw:
        if x["patch"]:
            M, J = ra(x["questions"])
            k = (x["donor"], x["host"], x["source_kind"])
            arm[x["patch"]["arm"]][k] = (M - base[(x["host"], x["target_arm"])], J)
            qrows[x["patch"]["arm"]][k] = x["questions"]
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
                "SPEC": frac >= 0.75 and maj >= 10,   # as M2/M3, also under leave-one-group-out (13 groups)
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    classes = list(design["base_classes"]) + ["ROUNDVOTES"]

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sf = T["full"]["S"]
        suf = [c for c in classes if Sf > 0 and T[f"only_{c}"]["S"] >= Sf / 2 and T[f"only_{c}"]["SPEC"]]
        nec = [c for c in classes if Sf > 0 and T[f"drop_{c}"]["S"] <= Sf / 2]
        B = sorted({c for c in suf + nec if c != "ROUNDVOTES"})
        if 1 <= len(B) <= 2:
            v = "LOCUS:" + "+".join(B)
        elif not B and "ROUNDVOTES" in suf + nec:
            v = "LOCUS:ROUNDVOTES"
        else:
            v = "DIFFUSE"
        tv = T["vswap_PARTNER"]
        vv = ("V_STRONG" if Sf > 0 and tv["S"] >= Sf / 2 and tv["SPEC"]
              else "V_PARTIAL" if Sf > 0 and tv["S"] >= Sf / 4 and tv["SPEC"] else "V_NONE")
        return T, {"SUF": suf, "NEC": nec, "B": B, "verdict": v, "value_swap": vv}

    T, V = verdict(cells)
    m3S = sum(m3all[(d, h, "main")][1] and not m3all[(d, h, "round")][1] for d, h in cells)
    bitwise = sum(qrows["full"][k] == m3all[k][2] for k in m3all)
    gate = {"S_full": T["full"]["S"], "S_M3_all": m3S, "full_rows_bitwise_eq_M3": bitwise,
            "pass": T["full"]["S"] == m3S == 51 and bitwise == 208}
    if a.fake_dry_run:
        gate["pass_fake_dry_run_not_applicable"] = True
    final = V["verdict"] if gate["pass"] else "INCONSISTENT_WITH_M3"
    final_v = V["value_swap"] if gate["pass"] else "INCONSISTENT_WITH_M3"
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = {"verdict": vv["verdict"], "value_swap": vv["value_swap"], "B": vv["B"]}
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}
    same = {tuple(c) for c in design["same_author_cells"]}
    strat = {}
    for lab, cs in (("same_author", [c for c in cells if c in same]), ("diff_author", [c for c in cells if c not in same])):
        strat[lab] = {n: {k: stats(arm[n], cs)[k] for k in ("S", "J_main", "J_round", "frac_main_gt_round", "n_cells")}
                      for n in ("full", "only_PARTNER", "drop_PARTNER", "vswap_PARTNER")}
    # descriptive: class contribution norms (row 0 mean over span), donors vs hosts, new arm
    norms = {x["capture"]["tag"]: x["class_contribution_norm_mean"] for x in raw if x["capture"]}
    cn = {c: {"donors_median": round(statistics.median(norms[f"new:{d[:12]}"][c] for d in gd), 6),
              "hosts_median": round(statistics.median(norms[f"new:{h[:12]}"][c] for h in hosts), 6)}
          for c in design["base_classes"]}
    res = {"schema": "JEV_A461_MECH_M4_ANALYSIS_V1", "table": T, "consistency_gate": gate, "class_rules": V,
           "verdict": final, "value_swap": final_v, "leave_one_donor_group_out": logo, "per_host_S": per_host,
           "author_strata": strat, "class_contribution_norms": cn, "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m4_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "class_rules": V, "verdict": final, "value_swap": final_v,
                      "S": {n: T[n]["S"] for n in names}, "SPEC": {n: T[n]["SPEC"] for n in names}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
