#!/usr/bin/env python3
"""A461-MECH-M3 R1 analysis: applies the rules frozen in m3_design.json (written before the GPU run).
Head-patch rules on the raw logits; attention readout from the saved L11 probability files (row 0) summarised
over the design's token classes. The consistency gate compares the all-heads arm with M2 mixer_L11 (pinned raw)."""
import argparse, collections, hashlib, json, statistics, subprocess, sys
from pathlib import Path

BLOB_DESIGN = "7445c13bc36c45324b54c3b4ea2fcbee0c37fe77"
BLOB_M2_RAW = "e1c4b34fcef9221a98e8209f6bbff3f6536b15d4"


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
    ap.add_argument("--m2-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fake-dry-run", action="store_true",
                    help="self-test output only: skip the M2 baseline identity check")
    a = ap.parse_args()
    import torch
    if blob(a.design) != BLOB_DESIGN:
        raise SystemExit("design pin")
    if blob(a.m2_raw) != BLOB_M2_RAW:
        raise SystemExit("M2 raw pin")
    design = json.loads(a.design.read_text("utf8"))
    rules = design["preregistered_analysis"]
    raw, m2 = jsonl(a.raw), jsonl(a.m2_raw)
    if len(raw) != design["total"]:
        raise SystemExit(f"rows {len(raw)} != {design['total']}")
    gd = dict(design["selection"]["donors"])
    hosts = [h for h, _ in design["selection"]["hosts"]]
    base = {x["target_scene"]: ra(x["questions"])[0] for x in raw
            if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
    m2base = {x["target_scene"]: ra(x["questions"])[0] for x in m2 if x["capture"] and x["source_kind"] == "host"}
    if base != m2base and not a.fake_dry_run:
        raise SystemExit("host baselines differ from M2")
    arm = collections.defaultdict(dict)   # arm -> (d, h, src) -> (dM, J)
    for x in raw:
        if x["patch"]:
            M, J = ra(x["questions"])
            arm[x["patch"]["arm"]][(x["donor"], x["host"], x["source_kind"])] = (M - base[x["host"]], J)
    m2mix = {}
    for x in m2:
        if x["patch"] and x["patch"]["component"] == "mixer" and x["layer"] == 11:
            M, J = ra(x["questions"])
            m2mix[(x["donor"], x["host"], x["source_kind"])] = (M - m2base[x["host"]], J)
    cells = sorted({(d, h) for (d, h, _s) in arm["all"]})
    names = [n for n, _ in design["arms"]]
    if len(cells) != 104 or sorted(arm) != sorted(names) or any(len(v) != 208 for v in arm.values()) or len(m2mix) != 208:
        raise SystemExit("cell census")
    heads = {n: hs for n, hs in design["arms"]}

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
                "frac_main_gt_round": round(frac, 4), "groups_majority": maj,
                "SPEC": frac >= 0.75 and maj >= 10,   # as M2, also under leave-one-group-out (13 groups)
                "median_dM_main": round(statistics.median(v[(d, h, "main")][0] for d, h in cs), 4),
                "median_dM_round": round(statistics.median(v[(d, h, "round")][0] for d, h in cs), 4),
                "median_dM_contrast": round(statistics.median(v[(d, h, "main")][0] - v[(d, h, "round")][0]
                                                              for d, h in cs), 4)}

    def verdict(cs):
        T = {n: stats(arm[n], cs) for n in names}
        Sall = T["all"]["S"]
        suf = [h for h in range(16) if T[f"head{h}"]["S"] >= Sall / 2 and T[f"head{h}"]["SPEC"] and Sall > 0]
        nec = [h for h in range(16) if T[f"drop{h}"]["S"] <= Sall / 2 and Sall > 0]
        gsuf = [g for g in range(4) if T[f"group{g}"]["S"] >= Sall / 2 and T[f"group{g}"]["SPEC"] and Sall > 0]
        sn = sorted(set(suf) | set(nec))
        v = ("SPARSE_HEADS" if 1 <= len(sn) <= 3 else "BROAD_HEADS" if len(sn) > 3
             else "KV_GROUP_LOCAL" if gsuf else "DISTRIBUTED")
        if sn:
            hstar, hsrc = sn, "SUF_u_NEC"
        elif gsuf:
            hstar, hsrc = sorted(h for g in gsuf for h in heads[f"group{g}"]), "GSUF_groups"
        else:
            rank = sorted(range(16), key=lambda h: (-T[f"head{h}"]["S"], -T[f"head{h}"]["median_dM_contrast"]))
            hstar, hsrc = sorted(rank[:3]), "TOP3_EXPLORATORY"
        return T, {"SUF": suf, "NEC": nec, "GSUF": gsuf, "verdict": v, "H_star": hstar, "H_star_source": hsrc}

    T, V = verdict(cells)
    m2S = sum(m2mix[(d, h, "main")][1] and not m2mix[(d, h, "round")][1] for d, h in cells)
    agree = sum(arm["all"][(d, h, "main")][1] == m2mix[(d, h, "main")][1] for d, h in cells)
    maxdiff = max(abs(arm["all"][k][0] - m2mix[k][0]) for k in m2mix)
    consistent = abs(T["all"]["S"] - m2S) <= 5 and agree >= 98
    gate = {"S_all": T["all"]["S"], "S_M2_mixer_L11": m2S, "main_JOINT_agreement": agree,
            "max_abs_dM_diff_vs_M2": round(maxdiff, 6), "pass": consistent}
    final = V["verdict"] if consistent else "INCONSISTENT_WITH_M2"
    logo = {}
    for g in sorted(set(gd.values())):
        _T, vv = verdict([c for c in cells if gd[c[0]] != g])
        logo[g] = vv
    per_host = {h[:12]: {n: stats(arm[n], [c for c in cells if c[1] == h])["S"] for n in names} for h in hosts}

    # ---------- attention readout ----------
    caps = {x["capture"]["tag"]: x for x in raw if x["capture"]}
    tc = design["token_classes"]
    if sorted(caps) != sorted(tc):
        raise SystemExit("capture tags != design token classes")
    mass = {}
    for tag, x in caps.items():
        c = tc[tag]
        if x["token_ids_sha256"] != c["token_ids_sha256"] or x["capture"]["span"] != c["span"]:
            raise SystemExit(f"token classes do not match the captured forward at {tag}")
        f = a.captures / x["attn_file"]["name"]
        if hashlib.sha256(f.read_bytes()).hexdigest() != x["attn_file"]["sha256"]:
            raise SystemExit(f"attention file sha {tag}")
        p = torch.load(f, weights_only=True).double()            # [heads, W, s1]
        s0, s1 = c["span"]
        idx = {"PARTNER": [k for lo, hi in c["partner"] for k in range(lo, hi)],
               "ROUND_PEERS": [k for lo, hi in c["round_peers"] for k in range(lo, hi)],
               "SELF": list(range(s0, s1))}
        m = {k: p[:, :, v].sum(-1).mean(-1) for k, v in idx.items()}   # [heads], mean over span queries
        m["REST"] = 1 - sum(m.values())
        mass[tag] = {k: [round(float(t), 6) for t in v] for k, v in m.items()}
    hstar = V["H_star"]

    def mP(tag, hs=None):
        hs = hstar if hs is None else hs
        return sum(mass[tag]["PARTNER"][h] for h in hs) / len(hs)
    donors = list(gd)
    D = {s: mP(f"new:{s[:12]}") - mP(f"ROUND:{s[:12]}") for s in donors + hosts}
    dpos, hpos = sum(D[s] > 0 for s in donors), sum(D[s] > 0 for s in hosts)
    a1 = {"D_donors": {s[:12]: round(D[s], 6) for s in donors}, "D_hosts": {s[:12]: round(D[s], 6) for s in hosts},
          "donors_positive": dpos, "hosts_positive": hpos, "DONOR_GATED": dpos >= 11, "HOST_GATED": hpos >= 6}
    a1["reading"] = ("host deficit in what the heads carry, not where they look" if a1["DONOR_GATED"] and a1["HOST_GATED"]
                     else "attention-pattern (routing) failure in hosts" if a1["DONOR_GATED"]
                     else "round-specific evaluation not explained by span-to-partner attention at L11")
    dn = [mP(f"new:{s[:12]}") for s in donors]
    hn = [mP(f"new:{s[:12]}") for s in hosts]
    a2 = {"median_mP_new_donors": round(statistics.median(dn), 6), "median_mP_new_hosts": round(statistics.median(hn), 6),
          "hosts_below_donor_min": sum(v < min(dn) for v in hn)}
    per_head_a1 = {h: {"donors_positive": sum(mP(f"new:{s[:12]}", [h]) > mP(f"ROUND:{s[:12]}", [h]) for s in donors),
                       "hosts_positive": sum(mP(f"new:{s[:12]}", [h]) > mP(f"ROUND:{s[:12]}", [h]) for s in hosts),
                       "median_partner_mass_new_donors": round(statistics.median(mass[f"new:{s[:12]}"]["PARTNER"][h]
                                                                                 for s in donors), 6),
                       "median_partner_mass_new_hosts": round(statistics.median(mass[f"new:{s[:12]}"]["PARTNER"][h]
                                                                                for s in hosts), 6)}
                   for h in range(16)}
    res = {"schema": "JEV_A461_MECH_M3_ANALYSIS_V1", "table": T, "consistency_gate": gate, "head_rules": V,
           "verdict": final, "leave_one_donor_group_out": logo, "per_host_S": per_host,
           "attention": {"H_star": hstar, "A1": a1, "A2": a2, "per_head_A1": per_head_a1, "class_mass": mass},
           "rules": rules}
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / "m3_analysis.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({"consistency_gate": gate, "head_rules": V, "verdict": final,
                      "A1": {k: a1[k] for k in ("donors_positive", "hosts_positive", "DONOR_GATED", "HOST_GATED", "reading")},
                      "A2": a2}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
