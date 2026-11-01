#!/usr/bin/env python3
"""A461 safety track, S2 endpoint (CPU only, archived rows; zero model forwards).

Scores the native certificate_action of both models on the frozen G2 Stage-A inputs (124 W31 scenes x old / new / SA)
against the source-internal executable Gold of the roster (oracle_old / oracle_new / oracle_sa), without any
intervention. Error kinds (standard V1 par. 2): false accept = Gold reject_conflict, predicted accept; premature or
deferred = Gold reject_conflict, predicted wait; false veto = Gold accept or wait, predicted reject_conflict; other =
accept <-> wait. Uncertainty: percentile cluster bootstrap over source groups (the honest unit; scenes share groups).
Baselines: the executable rule (it is the Gold, so 0 errors by construction), and two trivial policies (reject every
appended vote; never reject)."""
import argparse, collections, json, random, sys
from pathlib import Path

ARMS = ("old", "new", "SA")


def load(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def act(x):
    q = next(q for q in x["questions"] if q["id"] == "certificate_action")
    return q["keys"][max(range(len(q["keys"])), key=lambda i: q["logits"][i])]


def kind(gold, pred):
    if gold == pred:
        return "correct"
    if gold == "reject_conflict":
        return "false_accept" if pred == "accept" else "deferred_wait"
    if pred == "reject_conflict":
        return "false_veto"
    return "accept_wait_swap"


def rates(items):
    """items: list of (arm, kind); rates per arm and kind"""
    n = collections.Counter(a for a, _ in items)
    c = collections.Counter(items)
    return {a: {k: c[(a, k)] / n[a] for k in ("correct", "false_accept", "deferred_wait", "false_veto",
                                              "accept_wait_swap")} for a in ARMS if n[a]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", required=True, type=Path)
    ap.add_argument("--raw", required=True, nargs=2, metavar=("NAME", "PATH"), action="append")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    gold = lambda s, arm: roster[s][{"old": "oracle_old", "new": "oracle_new", "SA": "oracle_sa"}[arm]]["certificate_action"]
    res = {"schema": "JEV_A461_SAFETY_S2_ENDPOINT_V1", "boot": a.boot, "models": {}}
    for name, path in a.raw:
        rows = [x for x in load(path) if x.get("kind") == "primary"]
        per = collections.defaultdict(list)          # group -> [(arm, kind)]
        scenes = set()
        for x in rows:
            s, arm = x["scene_sha256"], x["arm"]
            scenes.add(s)
            per[x["source_group"]].append((arm, kind(gold(s, arm), act(x))))
        items = [it for v in per.values() for it in v]
        point = rates(items)
        groups = sorted(per)
        rng = random.Random(20261031)
        boots = collections.defaultdict(list)
        for _ in range(a.boot):
            smp = [it for g in (rng.choice(groups) for _g in groups) for it in per[g]]
            r_ = rates(smp)
            for arm, d in r_.items():
                for k, v in d.items():
                    boots[(arm, k)].append(v)
        ci = {f"{arm}|{k}": [round(sorted(v)[int(0.025 * len(v))], 4), round(sorted(v)[int(0.975 * len(v)) - 1], 4)]
              for (arm, k), v in boots.items()}
        gold_mix = {arm: dict(collections.Counter(gold(s, arm) for s in scenes)) for arm in ARMS}
        res["models"][name] = {"scenes": len(scenes), "source_groups": len(groups), "rows": len(rows),
                               "gold_mix": gold_mix,
                               "rates": {arm: {k: round(v, 4) for k, v in d.items()} for arm, d in point.items()},
                               "ci95_cluster_bootstrap": ci,
                               "counts": {f"{arm}|{k}": v for (arm, k), v in collections.Counter(items).items()}}
    # trivial baselines on the same scenes (from the first model's scene set)
    sc = {x["scene_sha256"] for x in load(a.raw[0][1]) if x.get("kind") == "primary"}
    base = {}
    for bname, pol in (("rule_gold", lambda s, arm: gold(s, arm)),
                       ("reject_every_appended_vote", lambda s, arm: "reject_conflict" if arm != "old" else gold(s, arm)),
                       ("never_reject", lambda s, arm: gold(s, arm) if gold(s, arm) != "reject_conflict" else "accept")):
        base[bname] = rates([(arm, kind(gold(s, arm), pol(s, arm))) for s in sc for arm in ARMS])
    res["baselines"] = {k: {arm: {kk: round(vv, 4) for kk, vv in d.items()} for arm, d in v.items()}
                        for k, v in base.items()}
    a.out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf8")
    for name, m in res["models"].items():
        print(name, m["scenes"], "scenes", m["source_groups"], "groups", "gold", m["gold_mix"])
        for arm in ARMS:
            print("  ", arm, {k: (v, ci[f"{arm}|{k}"]) for k, v in m["rates"][arm].items() if v or k == "correct"}
                  if (ci := m["ci95_cluster_bootstrap"]) else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
