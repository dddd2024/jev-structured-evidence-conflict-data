#!/usr/bin/env python3
"""A461-G3 G2C: independent multihead analysis of the 109 persisted logits.

Primary endpoint (reclassified per the multihead screen): conflicting_vote
head recognition on T2 new arms. Also: evidence_level, quorum, certificate_action
correctness, action=f(predC,predQ) consistency, N1B/N1/SHAM contrasts, signed
conflict-head logit deltas, baselines. Fourth independent oracle formulation.
CPU only, no model.
"""
import argparse, collections, hashlib, json, sys
from pathlib import Path


def flat(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def oracle(st):
    """Fourth formulation: accumulate (author -> set of blocks) with sets."""
    cand, rnd, dl = st["candidate_block"], st["candidate_round"], st["decision_time"]
    vs = frozenset(st["validator_set"])
    blocks_by = {}
    for m in st["received_messages"]:
        if {m.get("kind"), m.get("round"), m.get("author")} and False:
            continue
        if m.get("kind") != "vote" or m.get("round") != rnd or m.get("author") not in vs:
            continue
        r = m.get("received")
        if not isinstance(r, (int, float)) or r > dl:
            continue
        blocks_by.setdefault(m["author"], set()).add(m["block"])
    supporters = {a for a, bs in blocks_by.items() if cand in bs}
    conflict = any(bs - {cand} for a, bs in blocks_by.items() if a in supporters)
    q = len(supporters) >= st["quorum_size"]
    act = "reject_conflict" if conflict else ("accept" if q else "wait")
    return {"conflicting_vote": conflict, "quorum": q, "certificate_action": act,
            "evidence_level": {"reject_conflict": 2, "accept": 0, "wait": 1}[act]}


HEADS = ["conflicting_vote", "evidence_level", "quorum", "certificate_action"]


def norm(v):
    if isinstance(v, str):
        return {"true": True, "false": False, "1": True, "0": False}.get(v.strip().lower(), v)
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    run = a.run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    assert out.parent.is_dir() and not out.exists(), "new out dir"
    out.mkdir(mode=0o700)
    g1 = [json.loads(x) for x in (run / "G1C/raw_native_logits_109_requests.jsonl").read_text("utf8").splitlines() if x.strip()]
    prows = [json.loads(x) for x in (run / "G0C/pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
    receipt = json.loads((run / "G1C/execution_receipt.json").read_text("utf8"))
    assert receipt["status"] == "COMPLETE_A461_G3_G1C_PAIRED_FORWARDS"

    import gzip
    old_states = {}
    with gzip.open(Path.home() / "wjc/a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz", "rt", encoding="utf8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["_meta"].get("source") == "twins_streamlet":
                old_states[hashlib.sha256(json.dumps(rec["state"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")).hexdigest()[:16]] = rec["state"]

    prim = {}
    for r in g1:
        if r["kind"] == "primary":
            prim[r["plan_row"]] = r

    def preds(row):
        d = {}
        for q in prim[row["row_id"]]["questions"]:
            vals = q["logits"]
            d[q["id"]] = {"pred": norm(q["keys"][max(range(len(vals)), key=lambda i: vals[i])]),
                          "keys": q["keys"], "logits": vals}
        return d

    def gold_of(state):
        g = oracle(state)
        return {"conflicting_vote": g["conflicting_vote"], "evidence_level": g["evidence_level"],
                "quorum": g["quorum"], "certificate_action": g["certificate_action"]}

    by_pair = collections.OrderedDict()
    for r in prows:
        by_pair.setdefault(r["pair_key"], []).append(r)
    per_pair = []
    agg = collections.defaultdict(lambda: collections.Counter())
    for key, rs in by_pair.items():
        old_state = old_states[key.split(":", 1)[1]]
        g_old = gold_of(old_state)
        treat = next(r for r in rs if r["arm"] == "new")
        st_t = treat["native_request"]["state"]
        g_new = gold_of(st_t)
        cell = ("accept_to_reject" if g_old["certificate_action"] == "accept" else "wait_to_reject") \
            if treat["family"].startswith("T2") else None
        po = preds(next(r for r in rs if r["arm"] == "new"))  # placeholder replaced below
        # old-arm predictions from the G1C old row
        old_g1 = prim[key + ":old"]
        oldp = {}
        for q in old_g1["questions"]:
            vals = q["logits"]
            oldp[q["id"]] = {"pred": norm(q["keys"][max(range(len(vals)), key=lambda i: vals[i])]), "logits": vals, "keys": q["keys"]}
        newp = preds(treat)
        row = {"pair_key": key, "family": treat["family"], "cell": cell,
               "source_group": treat["source_group"], "old_gold": g_old, "new_gold": g_new,
               "old_pred": {h: oldp[h]["pred"] for h in HEADS},
               "new_pred": {h: newp[h]["pred"] for h in HEADS},
               "old_correct": {h: oldp[h]["pred"] == g_old[h] for h in HEADS},
               "new_correct": {h: newp[h]["pred"] == g_new[h] for h in HEADS}}
        # action = f(predC, predQ) consistency on the new arm
        f_act = ("reject_conflict" if newp["conflicting_vote"]["pred"] in (True, "true")
                 else ("accept" if newp["quorum"]["pred"] in (True, "true") else "wait"))
        row["action_consistent_with_own_CQ"] = f_act == row["new_pred"]["certificate_action"]
        # conflict head margin delta
        ocl = oldp["conflicting_vote"]["logits"]
        ncl = newp["conflicting_vote"]["logits"]
        okeys = oldp["conflicting_vote"]["keys"]
        nkeys = newp["conflicting_vote"]["keys"]
        ti_o, fi_o = okeys.index(True) if True in okeys else okeys.index("true"), okeys.index(False) if False in okeys else okeys.index("false")
        ti_n, fi_n = nkeys.index(True) if True in nkeys else nkeys.index("true"), nkeys.index(False) if False in nkeys else nkeys.index("false")
        row["conflict_head_margin_old"] = ocl[ti_o] - ocl[fi_o]
        row["conflict_head_margin_new"] = ncl[ti_n] - ncl[fi_n]
        row["conflict_head_margin_delta"] = row["conflict_head_margin_new"] - row["conflict_head_margin_old"]
        # nuisance arms
        for r in rs:
            if r["arm"] == "new":
                continue
            st_a = r["native_request"]["state"]
            g_a = gold_of(st_a)
            pa = preds(r)
            row[r["arm"] + "_pred"] = {h: pa[h]["pred"] for h in HEADS}
            row[r["arm"] + "_gold"] = g_a
            ref_gold = g_new if r["family"].endswith("_SHAM_TS") or r["family"].endswith("_SHAM_RO") else g_old
            row[r["arm"] + "_action_vs_ref"] = pa["certificate_action"]["pred"] != ref_gold["certificate_action"]
            row[r["arm"] + "_C_vs_ref"] = pa["conflicting_vote"]["pred"] != ref_gold["conflicting_vote"]
        per_pair.append(row)
        # aggregates
        if cell:
            agg["T2_" + cell]["pairs"] += 1
            agg["T2_" + cell]["C_head_recognized"] += row["new_correct"]["conflicting_vote"]
            agg["T2_" + cell]["action_correct"] += row["new_correct"]["certificate_action"]
            agg["T2_" + cell]["action_consistent_own_CQ"] += row["action_consistent_with_own_CQ"]
            agg["T2_" + cell]["old_action_correct"] += row["old_correct"]["certificate_action"]
            agg["T2_" + cell]["margin_delta_positive"] += (row["conflict_head_margin_delta"] > 0)
        elif treat["family"].startswith("T3"):
            agg["T3_contrast"]["pairs"] += 1
            agg["T3_contrast"]["C_head_true"] += row["new_correct"]["conflicting_vote"]
            agg["T3_contrast"]["action_held_reject"] += row["new_correct"]["certificate_action"]
        for r in rs:
            if r["arm"] == "new":
                continue
            tag = r["arm"]
            rowk = next(x for x in per_pair if x["pair_key"] == key)
            if rowk.get(tag + "_action_vs_ref") is not None:
                agg["nuisance_" + tag]["arms"] += 1
                agg["nuisance_" + tag]["action_differs_ref"] += rowk[tag + "_action_vs_ref"]
                agg["nuisance_" + tag]["C_differs_ref"] += rowk[tag + "_C_vs_ref"]
    # baselines
    t2_all = [r for r in per_pair if r["cell"]]
    persist_correct = sum(1 for r in t2_all if r["new_pred"]["certificate_action"] == r["old_gold"]["certificate_action"])
    majority = collections.Counter(r["old_gold"]["certificate_action"] for r in t2_all).most_common(1)[0]
    analysis = {"schema": "JEV_A461_G3_G2C_ANALYSIS_V1",
                "forwards": len(g1), "pairs": len(per_pair),
                "aggregate": {k: dict(v) for k, v in sorted(agg.items())},
                "baselines": {
                    "deterministic_rule_ceiling": "100% by construction (oracle)",
                    "persist_at_old_decision_on_t2": {"correct": persist_correct, "of": len(t2_all)},
                    "majority_class_old_gold_on_t2": {"label": majority[0], "count": majority[1], "of": len(t2_all)}},
                "notes": ["conflict-head margin delta > 0 means the true-minus-false logit gap moved toward recognizing the appended conflict",
                          "SHAM_TS/SHAM_RO reference gold is the treatment gold (treatment-format controls); N1B/N1/SHAM_SA reference the old gold"]}
    with (out / "per_pair_heads.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in per_pair:
            f.write(flat(r) + "\n")
    with (out / "analysis.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(analysis, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    receipt = {"schema": "JEV_A461_G3_G2C_RECEIPT_V1", "status": "COMPLETE_A461_G3_G2C_ANALYSIS",
               "gpu_forwards": 0, "model_loads": 0, "pairs": len(per_pair)}
    with (out / "execution_receipt.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    h = hashlib.sha256()
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("per_pair_heads.jsonl", "analysis.json", "execution_receipt.json"):
            hh = hashlib.sha256()
            with (out / n).open("rb") as f2:
                for b in iter(lambda: f2.read(1 << 20), b""):
                    hh.update(b)
            f.write(hh.hexdigest() + "  " + n + "\n")
    print(flat(analysis["aggregate"]))
    print(flat(analysis["baselines"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
