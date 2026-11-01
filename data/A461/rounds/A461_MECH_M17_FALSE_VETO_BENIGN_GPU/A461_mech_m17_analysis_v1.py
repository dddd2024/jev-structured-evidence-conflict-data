#!/usr/bin/env python3
"""A461-MECH-M17 R1 analysis (CPU only; frozen before any M17 forward): false veto of the M3-M16 repairing patches
on the benign variants (SA, ROUND, OUTSIDER) of the 8 hosts. Rules: m17_design.json -> preregistered_analysis."""
import argparse, collections, json, statistics, sys
from pathlib import Path

ARMS = ("full", "meanD", "cs0", "abc05")
TARGETS = ("SA", "ROUND", "OUTSIDER")
PINNED = {"full": ("M3", "all"), "meanD": ("M6", "meanD_host"), "cs0": ("M8", "cs0"), "abc05": ("M14", "abc_s05")}


def L(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def q(qs):
    return {x["id"]: dict(zip(x["keys"], x["logits"])) for x in qs}


def act(qs):
    a = q(qs)["certificate_action"]
    return max(a, key=a.get)


def MA(qs):
    d = q(qs)
    c, a = d["conflicting_vote"], d["certificate_action"]
    return c["true"] - c["false"], a["reject_conflict"] - max(a["accept"], a["wait"])


def med(v):
    return round(statistics.median(v), 4) if v else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    for n in ("m3", "m6", "m8", "m14"):
        ap.add_argument(f"--{n}-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true")
    a = ap.parse_args()
    D = json.loads(a.design.read_text("utf8"))
    rules = D["preregistered_analysis"]
    rows = L(a.raw)
    pin_raw = {"M3": L(a.m3_raw), "M6": L(a.m6_raw), "M8": L(a.m8_raw), "M14": L(a.m14_raw)}
    pin_by_fi = {k: {x["forward_index"]: x for x in v} for k, v in pin_raw.items()}
    donors, hosts = D["selection"]["donors"], D["selection"]["hosts"]
    gd, gh = dict(donors), dict(hosts)
    gold = {k: v["certificate_action"] for k, v in D["benign_gold"].items()}
    caps = {(x["target_arm"], x["target_scene"]): x for x in rows if x.get("capture")}
    base = {k: act(x["questions"]) for k, x in caps.items()}
    base_ma = {k: MA(x["questions"]) for k, x in caps.items()}
    P = {}
    for x in rows:
        if x.get("patch"):
            P[(x["patch"]["arm"], x["donor"], x["host"], x["source_kind"])] = x

    # ---------- consistency gate ----------
    anchors = collections.Counter()
    for x in rows:
        if x.get("patch") and x.get("direction") == "anchor":
            ref = x.get("anchor_of") or {}
            r_ = pin_by_fi.get(ref.get("stage"), {}).get(ref.get("forward_index"))
            if r_ is not None and r_["donor"] == x["donor"] and r_["host"] == x["host"] \
                    and r_["source_kind"] == x["source_kind"] and r_["questions"] == x["questions"]:
                anchors[x["patch"]["arm"]] += 1
    tok_ok = sum(caps.get((T, h)) is not None and caps[(T, h)]["token_ids_sha256"]
                 == D["benign_spans"][f"{T}:{h[:12]}"]["token_ids_sha256"] for T in TARGETS for h, _ in hosts)
    base_new_ok = all(base.get(("new", h)) == D["host_new_baseline_action"][h[:12]] for h, _ in hosts)
    gate = {"anchor_rows_bitwise": dict(anchors), "benign_capture_token_sha_ok": tok_ok,
            "host_new_baseline_action_as_M1": base_new_ok}
    gate["pass"] = (dict(anchors) == {"full": 12, "meanD_host": 12, "cs0": 12, "abc_s05": 12} and tok_ok == 24
                    and base_new_ok)

    # ---------- repair reference from the pinned rows (all 104 cells) ----------
    pin_rows = {arm: {(x["donor"], x["host"], x["source_kind"]): x for x in pin_raw[st]
                      if x["patch"] and x["patch"]["arm"] == pa} for arm, (st, pa) in PINNED.items()}

    def evaluate(keep):
        """keep(donor) -> bool; returns the full verdict block on the kept cells"""
        cells = [(d, h) for d, _ in donors for h, _ in hosts if gd[d] != gh[h] and keep(d)]
        rep = {}
        for arm in ARMS:
            rr = [(d, h) for d, h in cells if act(pin_rows[arm][(d, h, "main")]["questions"]) == "reject_conflict"
                  and base[("new", h)] != "reject_conflict"]
            rep[arm] = {"R": len(rr), "R_h": {h[:8]: sum(1 for _d, hh in rr if hh == h) for h, _ in hosts}}
        fv, verdict, per_arm = {}, {}, {}
        for arm in ARMS:
            for T in TARGETS:
                name = f"{arm}@{T}"
                n_fv = n_fvr = n_fvj = n_off = n_off0 = 0
                fv_h = collections.Counter()
                dM, dA, gt = [], [], []
                for d, h in cells:
                    b, (bM, bA) = base[(T, h)], base_ma[(T, h)]
                    xm = P[(name, d, h, "main")]
                    am, (Mm, Am) = act(xm["questions"]), MA(xm["questions"])
                    if am == "reject_conflict" and b != "reject_conflict":
                        n_fv += 1
                        fv_h[h[:8]] += 1
                    if Mm > 0 and Am > 0 and not (bM > 0 and bA > 0):
                        n_fvj += 1
                    n_off += am != gold[f"{T}:{h[:12]}"]
                    n_off0 += b != gold[f"{T}:{h[:12]}"]
                    dM.append(Mm - bM)
                    dA.append(Am - bA)
                    xr = P.get((name, d, h, "round"))
                    if xr is not None:
                        if act(xr["questions"]) == "reject_conflict" and b != "reject_conflict":
                            n_fvr += 1
                        gt.append(Am > MA(xr["questions"])[1])
                R = rep[arm]["R"]
                v = ("FV_NONE" if n_fv <= 5 and max(fv_h.values(), default=0) < 7 else
                     "FV_AS_REPAIR" if n_fv >= R / 2 else "FV_PARTIAL")
                verdict[name] = v
                fv[name] = {"FV": n_fv, "FV_round": n_fvr if gt else None, "FVJ": n_fvj, "R": R,
                            "FV_h": {h[:8]: fv_h.get(h[:8], 0) for h, _ in hosts},
                            "off_gold_patched": n_off, "off_gold_unpatched": n_off0,
                            "median_dM_main": med(dM), "median_dA_main": med(dA),
                            "frac_A_main_gt_round": round(sum(gt) / len(gt), 4) if gt else None, "verdict": v}
            vs = [verdict[f"{arm}@{T}"] for T in TARGETS]
            per_arm[arm] = ("SELECTIVE" if all(v == "FV_NONE" for v in vs) else
                            "NONSELECTIVE" if sum(v == "FV_AS_REPAIR" for v in vs) >= 2 else "MIXED")
        host_sel = {}
        for hp in D["responsive_hosts"]:
            for arm in ARMS:
                Rh = rep[arm]["R_h"][hp]
                fvh = [fv[f"{arm}@{T}"]["FV_h"][hp] for T in TARGETS]
                host_sel[f"{hp}|{arm}"] = ("HOST_UNINFORMATIVE" if Rh < 7 else
                                           "HOST_SELECTIVE" if max(fvh) <= 1 else
                                           "HOST_NONSELECTIVE" if max(fvh) >= Rh / 2 else "HOST_MIXED")
        return {"cells": len(cells), "repair": rep, "false_veto": fv, "fv_verdicts": verdict, "arm_verdicts": per_arm,
                "host_selectivity": host_sel}

    allres = evaluate(lambda d: True)
    logo = {}
    for g in sorted(set(gd.values())):
        r_ = evaluate(lambda d, g=g: gd[d] != g)
        logo[g] = {"arm_verdicts": r_["arm_verdicts"], "fv_verdicts": r_["fv_verdicts"],
                   "FV": {k: v["FV"] for k, v in r_["false_veto"].items()},
                   "R": {k: v["R"] for k, v in r_["repair"].items()}}
    stab = {k: sum(v["arm_verdicts"][k] == allres["arm_verdicts"][k] for v in logo.values()) for k in ARMS}
    unpatched = {f"{T}:{h[:8]}": {"action": base[(T, h)], "gold": gold[f"{T}:{h[:12]}"],
                                  "M": round(base_ma[(T, h)][0], 4), "A": round(base_ma[(T, h)][1], 4)}
                 for T in TARGETS for h, _ in hosts}
    unpatched_new = {h[:8]: {"action": base[("new", h)], "M": round(base_ma[("new", h)][0], 4),
                             "A": round(base_ma[("new", h)][1], 4)} for h, _ in hosts}
    if not gate["pass"]:
        tag = "INCONSISTENT_WITH_M3_M6_M8_M14"
        verdicts = {"arm_verdicts": {k: tag for k in ARMS}, "fv_verdicts": {k: tag for k in allres["fv_verdicts"]},
                    "host_selectivity": {k: tag for k in allres["host_selectivity"]}}
    else:
        verdicts = {k: allres[k] for k in ("arm_verdicts", "fv_verdicts", "host_selectivity")}
    out = {"schema": "JEV_A461_MECH_M17_ANALYSIS_V1", "fake_dry_run": a.fake_dry_run, "consistency_gate": gate,
           "verdicts": verdicts, "false_veto": allres["false_veto"], "repair_reference": allres["repair"],
           "design_repair_reference_matches": allres["repair"] == D["repair_reference"],
           "unpatched_benign": unpatched, "unpatched_host_new": unpatched_new,
           "leave_one_donor_group_out": logo, "logo_arm_verdict_stability": stab, "rules": rules}
    o = a.out.expanduser().resolve()
    o.mkdir(parents=True, exist_ok=False)
    (o / "m17_analysis.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "verdicts": verdicts,
                      "FV": {k: (v["FV"], v["FV_round"], v["R"]) for k, v in allres["false_veto"].items()},
                      "logo_stability": stab}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
