"""Exploratory (not preregistered): per-host J/M/A decomposition of the M14 tilt arms."""
import json, sys, statistics as st, collections
raw = [json.loads(l) for l in open(sys.argv[1], encoding="utf8") if l.strip()]
def ma(qs):
    q = {x["id"]: x for x in qs}
    c, a = q["conflicting_vote"], q["certificate_action"]
    M = c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]
    L = dict(zip(a["keys"], a["logits"]))
    return M, L["reject_conflict"] - max(L["accept"], L["wait"])
base = {x["target_scene"]: ma(x["questions"]) for x in raw if x["capture"] and x["source_kind"] == "host" and x["target_arm"] == "new"}
R = collections.defaultdict(dict)
for x in raw:
    if x["patch"]:
        R[x["patch"]["arm"]][(x["donor"], x["host"], x["source_kind"])] = ma(x["questions"])
for host in ("4bcbaf15", "264c458d"):
    for s in ("s0312", "s0437"):
        print(f"== {host} {s}  (baseline M,A median over hosts' rows)")
        arms = [f"rem_m3_{s}", f"rem_m1_{s}", f"cs_{s}", f"rem_p1_{s}", f"rem_p3_{s}"] + [f"rnull3_{s}_{i}" for i in range(1, 9)]
        for a in arms:
            ks = [k for k in R[a] if k[1].startswith(host)]
            row = {}
            for src in ("main", "round"):
                v = [R[a][k] for k in ks if k[2] == src]
                Ms, As = [m for m, _ in v], [aa for _, aa in v]
                row[src] = (sum(m > 0 for m in Ms), sum(aa > 0 for aa in As), sum(m > 0 and aa > 0 for m, aa in v),
                            round(st.median(Ms), 3), round(st.median(As), 3))
            S = sum((R[a][(d, h, "main")][0] > 0 and R[a][(d, h, "main")][1] > 0) and not (R[a][(d, h, "round")][0] > 0 and R[a][(d, h, "round")][1] > 0)
                    for (d, h, src) in ks if src == "main")
            print(f"{a:16s} S{S:3d}  main M+ {row['main'][0]:2d} A+ {row['main'][1]:2d} J {row['main'][2]:2d} medM {row['main'][3]:+.3f} medA {row['main'][4]:+.3f} | round M+ {row['round'][0]:2d} A+ {row['round'][1]:2d} J {row['round'][2]:2d} medM {row['round'][3]:+.3f} medA {row['round'][4]:+.3f}")
