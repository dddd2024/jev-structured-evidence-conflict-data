#!/usr/bin/env python3
"""A461-PSMI G2: independent CPU analysis of the persisted G1 logits.

Independently recomputes oracle Gold from the frozen states (third oracle
implementation), then evaluates the preregistered endpoints:
- GOLD_CHANGING_RESPONSIVENESS (LANL L1, Twins T1/T2): with a correct old-arm
  baseline, does the new arm match the recomputed new Gold (responsive), stay
  at the old Gold (failed-to-change), or land elsewhere?
- GOLD_INVARIANT_RISK_NONREGRESSION (LANL L3A, Twins T3): with a correct old
  baseline, does the new arm hold the unchanged Gold?
- GOLD_INVARIANT_NUISANCE (N1B matched / N1 unmatched / N2 retime): does the
  arm leave the old Gold?
Secondary: signed option-logit margins toward the new Gold. McNemar-style
discordant counts use only old-correct pairs, one unit per pair, reported per
family and source cluster. No cross-family merging. CPU only, no model.
"""
import argparse, collections, hashlib, json, sys
from pathlib import Path


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def hx(v):
    return hashlib.sha256(canon(v).encode("utf8")).hexdigest()


def known(s):
    if not isinstance(s, str):
        return False
    t = s.strip().lower()
    return bool(t) and t not in {"unknown", "unk", "none", "null", "n/a", "na", "?", "unavailable", "-"} and not t.startswith("unknown_")


def gold_twins(st):
    """Third-implementation C/Q oracle (explicit scan, no defaultdict)."""
    cand, rnd, dl, qsz = st["candidate_block"], st["candidate_round"], st["decision_time"], st["quorum_size"]
    per_author = {}
    for m in st["received_messages"]:
        if m.get("kind") != "vote" or m.get("round") != rnd or m.get("author") not in st["validator_set"]:
            continue
        r = m.get("received")
        if not isinstance(r, (int, float)) or r > dl:
            continue
        per_author.setdefault(m["author"], []).append(m["block"])
    n_sup = 0
    conflict = False
    for a, blocks in per_author.items():
        if cand in blocks:
            n_sup += 1
            if any(b != cand for b in blocks):
                conflict = True
    act = "reject_conflict" if conflict else ("accept" if n_sup >= qsz else "wait")
    return {"conflicting_vote": conflict, "quorum": n_sup >= qsz, "certificate_action": act}


def gold_lanl(st):
    """Third-implementation LANL oracle."""
    ce = st["current_event"]
    cur_fail = ce["result"] == "Fail"
    nf, dests, unk = 0, set(), 0
    for e in st["recent_prior_events"]:
        t = e["seconds_before_current"]
        if not (isinstance(t, (int, float)) and 0 < t <= 300) or e.get("orientation") != "LogOn" or e["result"] != "Fail":
            continue
        nf += 1
        if known(e.get("destination_computer")):
            dests.add(e["destination_computer"])
        else:
            unk += 1
    old = st.get("older_history_summary") or {}
    of = old.get("failed_attempts", 0)
    od = [d for d in (old.get("known_failed_destination_computers") or []) if known(d)]
    b = nf >= 5
    b2 = nf + of >= 5
    s = len(dests) >= 3
    s2 = len(dests | set(od)) + unk + of >= 3
    amb = (b != b2) or (s != s2)
    act = "investigate" if (b or s) else ("record_failed_attempt" if cur_fail else "continue_monitoring")
    return {"failure_burst": b, "triage": act, "ambiguous": amb}


ACTION_QID = {"twins_streamlet": "certificate_action", "lanl_auth_policy": "triage"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    run = a.run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    assert out.parent.is_dir() and not out.exists(), "new out dir"
    out.mkdir(mode=0o700)
    files = []
    g1rows = [json.loads(x) for x in (run / "G1/raw_native_logits_103_requests.jsonl").read_text("utf8").splitlines() if x.strip()]
    prows = [json.loads(x) for x in (run / "G0/pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
    n1brows = [json.loads(x) for x in (run / "G0_N1B/n1b_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
    corr = json.loads((run / "G1/execution_receipt_corrected.json").read_text("utf8"))
    assert corr["status"] == "COMPLETE_A461_PSMI_G1_PAIRED_PILOT", "G1 not complete"

    arms = {}
    for r in g1rows:
        if r["kind"] == "primary":
            arms[r["plan_row"]] = r
    n1b_by_source = {r["source_pair_row"]: r["row_id"] for r in n1brows}
    # old states live in the pinned corpus, keyed by the 16-hex prefix of the
    # canonical state hash (same rule as G0 pair_key)
    import gzip
    old_state_by = {}
    with gzip.open(Path.home() / "wjc/a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz", "rt", encoding="utf8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            s = rec["_meta"].get("source")
            if s in ("twins_streamlet", "lanl_auth_policy"):
                old_state_by[(s, hx(rec["state"])[:16])] = rec["state"]

    def model_action(g1row, qid):
        for q in g1row["questions"]:
            if q["id"] == qid:
                best = max(range(len(q["logits"])), key=lambda i: q["logits"][i])
                return q["keys"][best], q["keys"], q["logits"]
        raise RuntimeError("branch missing " + qid)

    def pred(row):
        qid = ACTION_QID[row["source"]]
        act, keys, logits = model_action(arms[row["row_id"]], qid)
        srt = sorted(logits, reverse=True)
        margin = srt[0] - srt[1]
        return act, margin, keys, logits

    per_pair = []
    agg = collections.defaultdict(lambda: collections.Counter())
    margins = []
    for family in sorted({r["family"] for r in prows if r["family"] != "LANL_N2_TIMESTAMP_INVARIANCE"}):
        fam_rows = [r for r in prows if r["family"] == family]
        by_pair = collections.OrderedDict()
        for r in fam_rows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        for key, rs in by_pair.items():
            new_r = next(r for r in rs if r["arm"] == "new")
            neu_r = next((r for r in rs if r["arm"] == "neutral"), None)
            src = new_r["source"]
            qid = ACTION_QID[src]
            old_key = key.split(":")[0] + ":" + key.split(":", 1)[1] + ":old"
            old_g1 = arms.get(old_key)
            old_state = old_state_by.get((src, key.split(":", 1)[1]))
            assert old_g1 is not None and old_state is not None, "old arm missing " + key
            g_old = (gold_lanl(old_state) if src == "lanl_auth_policy" else gold_twins(old_state))
            old_gold = g_old["triage"] if src == "lanl_auth_policy" else g_old["certificate_action"]
            new_state = new_r["native_request"]["state"]
            g_new = (gold_lanl(new_state) if src == "lanl_auth_policy" else gold_twins(new_state))
            new_gold = g_new["triage"] if src == "lanl_auth_policy" else g_new["certificate_action"]
            ck_disagree = (new_gold != new_r["oracle_gold_impl1"].get("triage", new_r["oracle_gold_impl1"].get("certificate_action")))
            old_pred, keys_old, logits_old = model_action(old_g1, qid)
            srt_oo = sorted(logits_old, reverse=True)
            old_margin = srt_oo[0] - srt_oo[1]
            new_pred, new_margin, keys_new, logits_new = pred(new_r)
            row_out = {"pair_key": key, "family": family, "endpoint": new_r["endpoint"],
                       "source": src, "source_group": new_r["source_group"],
                       "old_gold": old_gold, "new_gold": new_gold,
                       "gold_impl_disagreement": ck_disagree,
                       "old_pred": old_pred, "new_pred": new_pred,
                       "old_correct": old_pred == old_gold,
                       "new_margin_old2new": None, "outcome": None}
            srt_o = sorted(logits_old, reverse=True)
            row_out["old_margin_top12"] = srt_o[0] - srt_o[1]
            oc = row_out["old_correct"]
            if family in ("LANL_L1_B_THRESHOLD", "TWINS_T1_QUORUM_AXIS", "TWINS_T2_CONFLICT_AXIS"):
                if not oc:
                    row_out["outcome"] = "baseline_wrong_" + ("new_responsive" if new_pred == new_gold else "new_also_wrong")
                    agg[family]["baseline_wrong"] += 1
                elif new_pred == new_gold:
                    row_out["outcome"] = "responsive_correct"
                    agg[family]["responsive_correct"] += 1
                elif new_pred == old_gold:
                    row_out["outcome"] = "failed_to_change"
                    agg[family]["failed_to_change"] += 1
                else:
                    row_out["outcome"] = "wrong_other_option"
                    agg[family]["wrong_other_option"] += 1
                row_out["new_margin_old2new"] = logits_new[keys_new.index(new_gold)] - logits_new[keys_new.index(old_gold)] - \
                                                (logits_old[keys_old.index(new_gold)] - logits_old[keys_old.index(old_gold)])
            else:  # nonregression
                if not oc:
                    row_out["outcome"] = "baseline_wrong_" + ("held_gold" if new_pred == old_gold else "new_left_gold")
                    agg[family]["baseline_wrong"] += 1
                elif new_pred == old_gold:
                    row_out["outcome"] = "nonregression_held"
                    agg[family]["nonregression_held"] += 1
                else:
                    row_out["outcome"] = "nonregression_violation"
                    agg[family]["nonregression_violation"] += 1
                row_out["new_margin_old2new"] = logits_new[keys_new.index(old_gold)] - logits_old[keys_old.index(old_gold)]
            margins.append(row_out)
            # nuisance arms
            n1b_r = next((x for x in n1brows
                          if x["source_pair_row"] == new_r["row_id"] and x["N1B_token_count_matched"]), None)
            for tag, r_ in (("N1B_matched", n1b_r), ("N1_unmatched", neu_r)):
                if not r_:
                    continue
                if r_["row_id"] not in arms:
                    row_out[tag + "_forwarded"] = False  # outside the equal-count executed plan
                    agg[family][("N1B" if tag == "N1B_matched" else "N1") + "_not_forwarded"] += 1
                    continue
                row_out[tag + "_forwarded"] = True
                rid = r_["row_id"]
                state_n = r_["native_request"]["state"]
                g_n = (gold_lanl(state_n) if src == "lanl_auth_policy" else gold_twins(state_n))
                gold_n = g_n["triage"] if src == "lanl_auth_policy" else g_n["certificate_action"]
                n_act, n_margin, n_keys, n_logits = pred(r_)
                row_out[tag + "_pred"] = n_act
                row_out[tag + "_gold"] = gold_n
                if oc:
                    viol = n_act != old_gold
                    row_out[tag + "_violation"] = viol
                    agg[family][("N1B" if tag == "N1B_matched" else "N1") + ("_violation" if viol else "_held")] += 1
            per_pair.append(row_out)
    # N2 retiming rows
    n2_rows = [r for r in prows if r["family"] == "LANL_N2_TIMESTAMP_INVARIANCE"]
    n2_out = []
    for r in n2_rows:
        src = r["source"]
        state_n = r["native_request"]["state"]
        g = gold_lanl(state_n)
        act, _, _, _ = pred(r)
        old_state = next(x["native_request"]["state"] for x in prows if x["pair_key"] == r["pair_key"])
        g_old = gold_lanl(old_state)["triage"]
        n2_out.append({"pair_key": r["pair_key"], "retimed_pred": act, "gold": g["triage"],
                       "old_gold": g_old, "violation": act != g["triage"]})
        agg["LANL_N2_TIMESTAMP_INVARIANCE"]["violation" if act != g["triage"] else "held"] += 1
    analysis = {"schema": "JEV_A461_PSMI_G2_ANALYSIS_V1",
                "g1_status": corr["status"], "forwards": len(g1rows),
                "pairs": len(per_pair),
                "aggregate": {k: dict(v) for k, v in sorted(agg.items())},
                "n2_retiming": n2_out,
                "notes": ["action branch = certificate_action (Twins) / triage (LANL); argmax over native option logits",
                          "old-correct conditioning per preregistration; no cross-family merging",
                          "N1B matched neutrals only from the 14 token-count-matched constructions",
                          "margin_old2new > 0 means the native action logit difference moved toward the preregistered new/kept Gold"]}
    with (out / "per_pair_outcomes.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in per_pair + n2_out:
            f.write(canon(r) + "\n")
    files.append("per_pair_outcomes.jsonl")
    with (out / "analysis.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(analysis, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    files.append("analysis.json")
    receipt = {"schema": "JEV_A461_PSMI_G2_RECEIPT_V1", "status": "COMPLETE_A461_PSMI_G2_INDEPENDENT_ANALYSIS",
               "gpu_forwards": 0, "model_loads": 0, "pairs": len(per_pair), "files": files}
    with (out / "execution_receipt.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    files.append("execution_receipt.json")
    h = hashlib.sha256()
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in files:
            f.write(sha(out / n) + "  " + n + "\n")
    print(canon(analysis["aggregate"]))
    return 0


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


if __name__ == "__main__":
    sys.exit(main())
