#!/usr/bin/env python3
"""A461-PSMI G0 primary implementation: rule-preserving counterfactual pair
construction, oracle implementation #1, and native token audit. CPU only.

Zero backbone forwards, zero GPU, zero network, zero TEST/CAL rows. One CPU
checkpoint load in phase 2 for tokenizer/render availability (A428 G0B
precedent). Protocols:
research/experiments/2026-10-25_A461_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE_PROTOCOL_V1.json
research/experiments/2026-10-25_A461_PSMI_CPU_GATE_AMENDMENT_V2_ENDPOINTS_AND_CHRONOLOGY.json
"""
import argparse, collections, gzip, hashlib, json, os, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
A428_G0A = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0A_REAL_20261023"
A428_G0B = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0B_REAL_20261023"
A427_GOLD = "research/rounds/A427_20261023_LANL_TRIAGE_FAIL_VOCABULARY_V2_CPU_GATE/P0_REAL_20261023/independent_gold_rows.jsonl"
CAPS = {"LANL_L1_B_THRESHOLD": 3, "LANL_L3A_RISK_NONREGRESSION": 2,
        "TWINS_T1_QUORUM_AXIS": 6, "TWINS_T2_CONFLICT_AXIS": 6,
        "TWINS_T3_CONFLICT_STABILITY": 4}
N2_LANL_CAP = 3
FORWARD_CAP = 128
WINDOW = 300
EXPECTED_TWINS = (797, 42)
EXPECTED_LANL = (328, 7)

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1",
                  TMPDIR=str(ROOT / ".tmp"), HF_HOME=str(ROOT / ".cache" / "huggingface"),
                  TORCH_HOME=str(ROOT / ".cache" / "torch"), XDG_CACHE_HOME=str(ROOT / ".cache"),
                  PYTHONPYCACHEPREFIX=str(ROOT / ".cache" / "pycache"))
sys.dont_write_bytecode = True


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def sha_file(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def hx(s):
    return hashlib.sha256(s.encode("utf8")).hexdigest()


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def known_dest(s):
    if not isinstance(s, str):
        return False
    t = s.strip().lower()
    return bool(t) and t not in {"unknown", "unk", "none", "null", "n/a", "na", "?", "unavailable", "-"} and not t.startswith("unknown_")


# ---------------- oracle implementation #1 ----------------

def twins_oracle(state):
    """C/Q truth table over valid votes (impl #1: support-set formulation)."""
    votes = collections.defaultdict(list)
    allowed = set(state["validator_set"])
    for e in state["received_messages"]:
        if (e.get("kind") == "vote" and e.get("round") == state["candidate_round"]
                and isinstance(e.get("received"), (int, float))
                and e["received"] <= state["decision_time"] and e.get("author") in allowed):
            votes[e["author"]].append(e["block"])
    support = {v for v, blocks in votes.items() if state["candidate_block"] in blocks}
    q = len(support) >= state["quorum_size"]
    c = any(any(b != state["candidate_block"] for b in votes[v]) for v in support)
    action = "reject_conflict" if c else "accept" if q else "wait"
    return {"conflicting_vote": c, "quorum": q, "certificate_action": action,
            "evidence_level": {"reject_conflict": 2, "accept": 0, "wait": 1}[action]}, sorted(support)


def lanl_oracle(state):
    """LANL triage truth table (impl #1), mirrors A427 v2 semantics."""
    ce = state["current_event"]
    ck(state["history_window_seconds"] == WINDOW, "window changed")
    ck(ce.get("orientation") == "LogOn", "non-LogOn current event")
    ck(ce.get("result") in ("Success", "Fail"), "unexpected current result")
    cur = "Failure" if ce["result"] == "Fail" else "Success"
    fails, dests, unknown_fails = 0, set(), 0
    for e in state["recent_prior_events"]:
        t = e["seconds_before_current"]
        ck(isinstance(t, (int, float)) and not isinstance(t, bool) and t >= 0, "bad age")
        if not (0 < t <= WINDOW) or e.get("orientation") != "LogOn":
            continue
        ck(e.get("result") in ("Success", "Fail"), "unexpected recent result")
        if e["result"] == "Fail":
            fails += 1
            if known_dest(e.get("destination_computer")):
                dests.add(e["destination_computer"])
            else:
                unknown_fails += 1
    old = state.get("older_history_summary", {})
    old_fails = old.get("failed_attempts", 0)
    old_dest = {d for d in old.get("known_failed_destination_computers", []) if known_dest(d)}
    b_min, b_max = fails >= 5, fails + old_fails >= 5
    s_min = len(dests) >= 3
    s_max = (len(dests | old_dest) + unknown_fails + old_fails) >= 3
    ambiguous = (b_min != b_max) or (s_min != s_max)
    r = b_min or s_min
    action = "investigate" if r else "record_failed_attempt" if cur == "Failure" else "continue_monitoring"
    return {"failure_burst": b_min, "triage": action, "ambiguous": ambiguous,
            "count_visible_failed_logons": fails,
            "count_distinct_known_failed_destinations": len(dests),
            "unknown_destination_failed_events": unknown_fails,
            "older_summary_failed_count_unscoped": old_fails}


def lanl_fails_and_dests(state):
    fails_ev = [e for e in state["recent_prior_events"]
                if e.get("orientation") == "LogOn" and e["result"] == "Fail"
                and 0 < e["seconds_before_current"] <= WINDOW]
    fdests = sorted({e["destination_computer"] for e in fails_ev if known_dest(e.get("destination_computer"))})
    return fails_ev, fdests


def twins_fresh_voter(state, msgs):
    return next(v for v in state["validator_set"]
                if not any(e.get("kind") == "vote" and e.get("round") == state["candidate_round"]
                           and isinstance(e.get("received"), (int, float))
                           and e["received"] <= state["decision_time"] and e.get("author") == v
                           for e in msgs))


# ---------------- edit implementations (deterministic) ----------------

def insert_event(events, new_ev):
    secs = [e["seconds_before_current"] for e in events]
    if all(secs[j] >= secs[j + 1] for j in range(len(secs) - 1)):
        pos = 0
        for e in events:
            if e["seconds_before_current"] >= new_ev["seconds_before_current"]:
                pos += 1
            else:
                break
        events.insert(pos, new_ev)
        return "inserted_sorted_desc"
    events.append(new_ev)
    return "appended_end"


def lanl_pick_seconds(state):
    fails_ev, _ = lanl_fails_and_dests(state)
    used = {e["seconds_before_current"] for e in state["recent_prior_events"]}
    fsecs = sorted(e["seconds_before_current"] for e in fails_ev)
    med = fsecs[len(fsecs) // 2]
    best = None
    for t in range(1, WINDOW + 1):
        if t in used:
            continue
        k = (abs(t - med), t)
        if best is None or k < best[0]:
            best = (k, t)
    return best[1]


def lanl_append_edit(state, result_value):
    st = json.loads(canon(state))
    fails_ev, fdests = lanl_fails_and_dests(st)
    ck(bool(fdests), "no known failed destination to append against")
    tmpl = json.loads(canon(fails_ev[0]))
    tmpl["seconds_before_current"] = lanl_pick_seconds(state)
    tmpl["destination_computer"] = fdests[0]
    tmpl["result"] = result_value
    where = insert_event(st["recent_prior_events"], tmpl)
    return st, {"op": "append_prior_event", "result": result_value,
                "destination_computer": tmpl["destination_computer"],
                "seconds_before_current": tmpl["seconds_before_current"],
                "insert_position_rule": where}


def lanl_retime_edit(state):
    st = json.loads(canon(state))
    fails_idx = [j for j, e in enumerate(st["recent_prior_events"])
                 if e.get("orientation") == "LogOn" and e["result"] == "Fail"
                 and 0 < e["seconds_before_current"] <= WINDOW]
    used_others = {e["seconds_before_current"] for j, e in enumerate(st["recent_prior_events"]) if j not in fails_idx}
    originals = [st["recent_prior_events"][j]["seconds_before_current"] for j in fails_idx]
    for delta in range(1, 60):
        new = [o + delta for o in originals]
        if (all(1 <= t <= WINDOW for t in new) and len(set(new)) == len(new)
                and not (set(new) & used_others)):
            for j, t in zip(fails_idx, new):
                st["recent_prior_events"][j]["seconds_before_current"] = t
            return st, {"op": "retime_failure_events", "delta": delta, "new_seconds": new,
                        "digit_width_change": any(len(str(t)) != len(str(o)) for t, o in zip(new, originals))}
    raise RuntimeError("no retime delta found")


def twins_append_edit(state, mode):
    st = json.loads(canon(state))
    msgs = st["received_messages"]
    o, support = twins_oracle(state)
    max_recv = max(e["received"] for e in msgs)
    if mode in ("T1", "T3"):
        new = {"author": twins_fresh_voter(state, msgs), "block": st["candidate_block"],
               "kind": "vote", "round": st["candidate_round"], "received": max_recv}
    elif mode == "T2":
        blocks = sorted({e["block"] for e in msgs} - {st["candidate_block"]})
        new = {"author": sorted(support)[0], "block": blocks[0], "kind": "vote",
               "round": st["candidate_round"], "received": max_recv}
    elif mode == "T2_NEUTRAL":
        blocks = sorted({e["block"] for e in msgs} - {st["candidate_block"]})
        try:
            author = twins_fresh_voter(state, msgs)
        except StopIteration:
            author = "z_neutral_outside_set"
        new = {"author": author, "block": blocks[0], "kind": "vote",
               "round": st["candidate_round"], "received": max_recv}
    elif mode == "PROPOSAL_NEUTRAL":
        try:
            author = twins_fresh_voter(state, msgs)
        except StopIteration:
            author = "z_neutral_outside_set"
        new = {"author": author, "block": st["candidate_block"], "kind": "proposal",
               "round": st["candidate_round"], "received": max_recv}
    else:
        raise RuntimeError("unknown twins mode " + mode)
    # Canonicalize key order so in-memory, file round-trip, and independent
    # re-application render to identical token streams (renderer is
    # insertion-order sensitive; discovered via G0 row-33 sha mismatch).
    new = json.loads(canon(new))
    msgs.append(new)
    return st, {"op": "append_message", "message": new}


# ---------------- main ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--phase1-only", action="store_true",
                    help="dev/test affordance: construction+oracle without renderer/token phase; server runs omit this")
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir(), "~/wjc missing")
    ck(CORPUS.is_file() and sha_file(CORPUS) == CORPUS_SHA, "pinned DEV corpus missing/changed")
    ck(all(x.is_relative_to(ROOT) for x in (repo, out)), "inputs must be under ~/wjc")
    ck(out.parent.is_dir() and not out.exists(), "NEW output dir required")
    receipt = {"schema": "JEV_A461_PSMI_G0_CPU_RECEIPT_V1", "status": "INCOMPLETE",
               "gpu_forwards": 0, "backbone_forwards": 0, "cpu_model_loads": 0,
               "network_calls": 0, "test_or_calibration_rows": 0, "output_dir": str(out)}
    files = []
    try:
        out.mkdir(mode=0o700)
        # ---------- phase 1a: corpus census + archived cross-checks ----------
        rows = []
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") in ("twins_streamlet", "lanl_auth_policy"):
                    rows.append(rec)
        ck(all(r["_meta"].get("split") == "development" for r in rows), "non-DEV row seen")
        twins = [r for r in rows if r["_meta"]["source"] == "twins_streamlet"]
        lanl = [r for r in rows if r["_meta"]["source"] == "lanl_auth_policy"]
        tw_groups = {r["_meta"]["split_group_id"] for r in twins}
        ln_groups = {r["_meta"]["split_group_id"] for r in lanl}
        ck(len(twins) == EXPECTED_TWINS[0] and len(tw_groups) == EXPECTED_TWINS[1],
           f"Twins DEV census drifted: {len(twins)}/{len(tw_groups)}")
        ck(len(lanl) == EXPECTED_LANL[0] and len(ln_groups) == EXPECTED_LANL[1],
           f"LANL DEV census drifted: {len(lanl)}/{len(ln_groups)}")

        a427_path = repo / A427_GOLD
        a428a_path = repo / (A428_G0A + "/frozen_model_inputs.jsonl")
        a428g_path = repo / (A428_G0A + "/independent_source_local_gold.jsonl")
        a428b_path = repo / (A428_G0B + "/native_token_manifest.json")
        ck(all(p.is_file() for p in (a427_path, a428a_path, a428g_path, a428b_path)),
           "archived cross-check files missing (sparse checkout?)")
        a427 = {}
        for line in a427_path.read_text("utf8").splitlines():
            if line.strip():
                g = json.loads(line)
                a427[g["original_record_sha256"]] = g
        a428_rows = [json.loads(x) for x in a428a_path.read_text("utf8").splitlines() if x.strip()]
        a428g = {}
        for line in a428g_path.read_text("utf8").splitlines():
            if line.strip():
                g = json.loads(line)
                a428g[g["id"]] = g
        a428_state_ids = {}
        for r in a428_rows:
            ck(not any("label" in v for v in r["native_request"]["questions"].values()),
               "gold leaked in archived questions")
            a428_state_ids.setdefault(hx(canon(r["native_request"]["state"])), r["id"])
        q_tw = next(r["native_request"]["questions"] for r in a428_rows if "certificate_action" in r["native_request"]["questions"])
        q_ln = next(r["native_request"]["questions"] for r in a428_rows if "triage" in r["native_request"]["questions"])

        lanl_checked = tw_checked = 0
        for rec in rows:
            st, rsha = rec["state"], hashlib.sha256(canon(rec).encode("utf8")).hexdigest()
            if rec["_meta"]["source"] == "lanl_auth_policy":
                g = a427.get(rsha)
                ck(g is not None, f"LANL row missing from A427 archive: {rec['_meta']['split_group_id']}")
                o = lanl_oracle(st)
                ck(o["count_visible_failed_logons"] == g["count_visible_failed_logons"]
                   and o["count_distinct_known_failed_destinations"] == g["count_distinct_known_failed_destinations"]
                   and o["unknown_destination_failed_events"] == g["unknown_destination_failed_events"]
                   and o["older_summary_failed_count_unscoped"] == g["older_summary_failed_count_unscoped"]
                   and o["triage"] == g["inferred"]["triage"]
                   and o["failure_burst"] == g["inferred"]["failure_burst"],
                   f"LANL oracle mismatch vs A427 archive group {rec['_meta']['split_group_id']}")
                lanl_checked += 1
            else:
                gid = a428_state_ids.get(hx(canon(st)))
                if gid is not None:
                    want = a428g[gid]["gold"]
                    o, _ = twins_oracle(st)
                    ck({"conflicting_vote": o["conflicting_vote"], "quorum": o["quorum"],
                        "certificate_action": o["certificate_action"],
                        "evidence_level": o["evidence_level"]} == want,
                       f"Twins oracle mismatch vs A428 gold {gid}")
                    tw_checked += 1
        ck(lanl_checked == 328, f"LANL cross-check coverage {lanl_checked}")
        ck(tw_checked >= 12, f"Twins cross-check too weak: {tw_checked}")

        # ---------- phase 1b: eligibility census ----------
        census = {"twins_rows": len(twins), "twins_groups": len(tw_groups),
                  "lanl_rows": len(lanl), "lanl_groups": len(ln_groups),
                  "twins_a428_crosschecked_scenes": tw_checked, "families": {}}
        l1_pool, l3a_pool = [], []
        for i, rec in enumerate(lanl):
            st, o = rec["state"], lanl_oracle(rec["state"])
            if o["ambiguous"] or o["unknown_destination_failed_events"] > 0 or o["older_summary_failed_count_unscoped"] > 0:
                continue
            secs = [e["seconds_before_current"] for e in st["recent_prior_events"]]
            if len(set(secs)) != len(secs):
                continue
            fails_ev, fdests = lanl_fails_and_dests(st)
            grp = rec["_meta"]["split_group_id"]
            if (o["count_visible_failed_logons"] == 4 and o["count_distinct_known_failed_destinations"] <= 2
                    and len(fdests) == o["count_distinct_known_failed_destinations"] and fdests):
                l1_pool.append((grp, i))
            if (o["failure_burst"] or o["count_distinct_known_failed_destinations"] >= 3) and fdests:
                l3a_pool.append((grp, i))
        census["families"]["LANL_L1_B_THRESHOLD"] = {"eligible": len(l1_pool),
            "by_group": dict(collections.Counter(g for g, _ in l1_pool))}
        census["families"]["LANL_L3A_RISK_NONREGRESSION"] = {"eligible": len(l3a_pool),
            "by_group": dict(collections.Counter(g for g, _ in l3a_pool))}

        def twins_census(pred):
            pool, reasons = [], collections.Counter()
            for i, rec in enumerate(twins):
                st = rec["state"]
                o, support = twins_oracle(st)
                msgs = st["received_messages"]
                recv = [e["received"] for e in msgs]
                if not all(recv[j] <= recv[j + 1] for j in range(len(recv) - 1)):
                    reasons["unsorted_received"] += 1
                    continue
                if max(recv) > st["decision_time"]:
                    reasons["append_infeasible"] += 1
                    continue
                blocks = sorted({e["block"] for e in msgs} - {st["candidate_block"]})
                fresh_exists = True
                try:
                    twins_fresh_voter(st, msgs)
                except StopIteration:
                    fresh_exists = False
                if pred(st, o, support, fresh_exists, blocks):
                    pool.append((rec["_meta"]["split_group_id"], i))
                else:
                    reasons["not_eligible"] += 1
            return pool, reasons

        t1_pool, t1_r = twins_census(lambda st, o, s, f, b: (not o["conflicting_vote"]) and (not o["quorum"])
                                     and len(s) == st["quorum_size"] - 1 and f)
        t2_pool, t2_r = twins_census(lambda st, o, s, f, b: (not o["conflicting_vote"]) and len(s) >= 1 and b)
        t3_pool, t3_r = twins_census(lambda st, o, s, f, b: o["conflicting_vote"] and f)
        for name, pool, rr in (("TWINS_T1_QUORUM_AXIS", t1_pool, t1_r),
                               ("TWINS_T2_CONFLICT_AXIS", t2_pool, t2_r),
                               ("TWINS_T3_CONFLICT_STABILITY", t3_pool, t3_r)):
            census["families"][name] = {"eligible": len(pool), "reasons": dict(rr)}

        def pick_round_robin(pool, cap):
            by_g = collections.defaultdict(list)
            for grp, i in sorted(pool, key=lambda x: (x[0], x[1])):
                by_g[grp].append(i)
            sel, gi = [], 0
            groups = sorted(by_g)
            while len(sel) < cap and any(by_g[g] for g in groups):
                g = groups[gi % len(groups)]
                if by_g[g]:
                    sel.append((g, by_g[g].pop(0)))
                gi += 1
            return sel

        def pick_by_group_cap(pool, per_group):
            by_g = collections.defaultdict(list)
            for grp, i in sorted(pool, key=lambda x: (x[0], x[1])):
                by_g[grp].append(i)
            sel = []
            for g in sorted(by_g):
                sel.extend((g, i) for i in by_g[g][:per_group])
            return sel

        l1_sel = pick_by_group_cap(l1_pool, CAPS["LANL_L1_B_THRESHOLD"])
        l3a_sel = pick_by_group_cap(l3a_pool, CAPS["LANL_L3A_RISK_NONREGRESSION"])
        t1_sel = pick_round_robin(t1_pool, CAPS["TWINS_T1_QUORUM_AXIS"])
        t2_sel = pick_round_robin(t2_pool, CAPS["TWINS_T2_CONFLICT_AXIS"])
        t3_sel = pick_round_robin(t3_pool, CAPS["TWINS_T3_CONFLICT_STABILITY"])

        # ---------- phase 1c: construction ----------
        emitted = []
        _row_seq = [0]

        def emit(family, endpoint, source, grp, old_state, new_state, edit, arm):
            _row_seq[0] += 1
            pair_key = family + ":" + hx(canon(old_state))[:16]
            if source == "lanl_auth_policy":
                g = lanl_oracle(new_state)
                gold = {"failure_burst": g["failure_burst"], "triage": g["triage"]}
            else:
                g, _ = twins_oracle(new_state)
                gold = {"conflicting_vote": g["conflicting_vote"], "quorum": g["quorum"],
                        "certificate_action": g["certificate_action"], "evidence_level": g["evidence_level"]}
            emitted.append({"row_id": f"A461P_{_row_seq[0]:04d}", "family": family, "endpoint": endpoint,
                            "source": source, "source_group": grp, "pair_key": pair_key, "arm": arm,
                            "declared_edit": edit, "oracle_gold_impl1": gold,
                            "native_request": {"questions": q_ln if source == "lanl_auth_policy" else q_tw,
                                               "state": new_state}})

        for fam, sel, endpoint in (("LANL_L1_B_THRESHOLD", l1_sel, "GOLD_CHANGING_RESPONSIVENESS"),
                                   ("LANL_L3A_RISK_NONREGRESSION", l3a_sel, "GOLD_INVARIANT_RISK_NONREGRESSION")):
            for grp, i in sel:
                rec = lanl[i]
                st_old = rec["state"]
                og = lanl_oracle(st_old)
                ck(not og["ambiguous"], "baseline ambiguity")
                st_new, edit = lanl_append_edit(st_old, "Fail")
                ng = lanl_oracle(st_new)
                ck(not ng["ambiguous"] and ng["triage"] == "investigate",
                   f"{fam} new arm must be investigate")
                if fam == "LANL_L1_B_THRESHOLD":
                    ck(og["triage"] in ("record_failed_attempt", "continue_monitoring"),
                       "L1 old gold sanity")
                st_neu, edit_n = lanl_append_edit(st_old, "Success")
                nug = lanl_oracle(st_neu)
                ck(not nug["ambiguous"] and nug["triage"] == og["triage"]
                   and nug["failure_burst"] == og["failure_burst"], "neutral arm changed gold")
                emit(fam, endpoint, "lanl_auth_policy", grp, st_old, st_new, edit, "new")
                emit(fam, endpoint, "lanl_auth_policy", grp, st_old, st_neu, edit_n, "neutral")

        n2_groups = sorted({grp for grp, _ in l1_sel})[:N2_LANL_CAP]
        for grp in n2_groups:
            i = next(i for g, i in l1_sel if g == grp)
            st_old = lanl[i]["state"]
            og = lanl_oracle(st_old)
            st_rt, edit = lanl_retime_edit(st_old)
            rg = lanl_oracle(st_rt)
            ck(not rg["ambiguous"] and rg["triage"] == og["triage"]
               and rg["failure_burst"] == og["failure_burst"], "retiming changed gold")
            emit("LANL_N2_TIMESTAMP_INVARIANCE", "GOLD_INVARIANT_NUISANCE",
                 "lanl_auth_policy", grp, st_old, st_rt, edit, "retimed")

        for fam, sel, endpoint, mode in (("TWINS_T1_QUORUM_AXIS", t1_sel, "GOLD_CHANGING_RESPONSIVENESS", "T1"),
                                         ("TWINS_T2_CONFLICT_AXIS", t2_sel, "GOLD_CHANGING_RESPONSIVENESS", "T2"),
                                         ("TWINS_T3_CONFLICT_STABILITY", t3_sel, "GOLD_INVARIANT_RISK_NONREGRESSION", "T3")):
            for grp, i in sel:
                st_old = twins[i]["state"]
                og, _ = twins_oracle(st_old)
                st_new, edit = twins_append_edit(st_old, mode)
                ng, _ = twins_oracle(st_new)
                if mode == "T1":
                    ck(not ng["conflicting_vote"] and ng["quorum"]
                       and og["certificate_action"] == "wait" and ng["certificate_action"] == "accept",
                       "T1 flip must be wait->accept with C staying false")
                if mode == "T2":
                    ck(ng["conflicting_vote"] and ng["certificate_action"] == "reject_conflict",
                       "T2 must create conflict -> reject_conflict")
                if mode == "T3":
                    ck(ng["certificate_action"] == og["certificate_action"] == "reject_conflict",
                       "T3 gold must stay reject_conflict")
                neu_mode = "T2_NEUTRAL" if mode == "T2" else "PROPOSAL_NEUTRAL"
                st_neu, edit_n = twins_append_edit(st_old, neu_mode)
                nug, _ = twins_oracle(st_neu)
                ck(nug["certificate_action"] == og["certificate_action"]
                   and nug["conflicting_vote"] == og["conflicting_vote"], "twins neutral changed gold")
                emit(fam, endpoint, "twins_streamlet", grp, st_old, st_new, edit, "new")
                emit(fam, endpoint, "twins_streamlet", grp, st_old, st_neu, edit_n, "neutral")

        total_arms = len(emitted)
        ck(total_arms <= FORWARD_CAP, f"forward budget exceeded: {total_arms}")

        with (out / "pair_rows.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for r in emitted:
                f.write(canon(r) + "\n")
        files.append("pair_rows.jsonl")
        census["selected"] = {"LANL_L1": len(l1_sel), "LANL_L3A": len(l3a_sel),
                              "T1": len(t1_sel), "T2": len(t2_sel), "T3": len(t3_sel),
                              "N2_LANL": len(n2_groups)}
        census["total_arms"] = total_arms
        census["forward_budget_cap"] = FORWARD_CAP
        with (out / "census.json").open("x", encoding="utf8", newline="\n") as f:
            json.dump(census, f, sort_keys=True, indent=2, ensure_ascii=False)
            f.write("\n")
        files.append("census.json")

        # ---------- phase 2: native render + token audit (1 CPU load, 0 forwards) ----------
        if a.phase1_only:
            receipt.update(status="COMPLETE_A461_PSMI_G0_CPU_GATE_IMPL1_PHASE1_ONLY",
                           total_arms=total_arms, forward_budget_cap=FORWARD_CAP,
                           cpu_model_loads=0, backbone_forwards=0, gpu_forwards=0,
                           pairs_selected=census["selected"],
                           cross_checks={"lanl_rows": lanl_checked, "twins_scenes": tw_checked})
            code = 0
        else:
            import torch
            torch.set_num_threads(4)
            torch.backends.cuda.matmul.allow_tf32 = False
            sys.path.insert(0, str(SOURCE))
            from kev.api import SystemOneRequest, to_record
            from kev.checkpoint import Checkpoint, LoadOptions
            from kev.model import rows_of
            ck(CKPT.is_dir() and BASE.is_dir(), "missing pinned checkpoint/base")
            manifest = json.loads(a428b_path.read_text("utf8"))
            ck(sha_file(SOURCE / "kev" / "model.py") == manifest["native_code_sha256"]["kev_model_py"]
               and sha_file(SOURCE / "kev" / "api.py") == manifest["native_code_sha256"]["kev_api_py"],
               "kev renderer code drift vs A428 pin")
            checkpoint = Checkpoint(str(CKPT))
            checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
            tokenizer, model = checkpoint.load("cpu", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
            receipt["cpu_model_loads"] = 1

            def encode_state(state, source):
                state = json.loads(canon(state))
                req = {"questions": q_ln if source == "lanl_auth_policy" else q_tw, "state": state}
                rendered, _ = to_record(SystemOneRequest.model_validate(req))
                enc = model.encode(tokenizer, rendered, max_state=8192, max_branch=8192, strict=True)
                sids, _, brs = rows_of(enc)
                ck(not enc["state_truncated"] and all(len(sids) + len(b["ids"]) <= 8192 for b in brs),
                   "truncation or over-length row")
                return sids, enc, brs

            old_cache = {}

            # Old-arm state is not emitted as a row; re-derive it from the corpus by
            # matching the pair_key hash (16-hex prefix of the canonical state hash).
            def old_state_for(pair_key, source):
                fam = pair_key.split(":")[0]
                h = pair_key.split(":", 1)[1]
                pool = lanl if source == "lanl_auth_policy" else twins
                for rec in pool:
                    if hx(canon(rec["state"]))[:16] == h:
                        return rec["state"]
                raise RuntimeError("old state not found for " + pair_key)

            token_rows = []
            for r in emitted:
                key = r["pair_key"]
                if key not in old_cache:
                    os_old = old_state_for(key, r["source"])
                    sids, enc, brs = encode_state(os_old, r["source"])
                    old_cache[key] = (sids, len(sids), hx(json.dumps(enc["ids"])))
                sids, enc, brs = encode_state(r["native_request"]["state"], r["source"])
                ob = old_cache[key]
                z = 0
                while z < min(len(ob[0]), len(sids)) and ob[0][z] == sids[z]:
                    z += 1
                token_rows.append({"row_id": r["row_id"], "pair_key": key, "arm": r["arm"],
                                   "family": r["family"], "endpoint": r["endpoint"],
                                   "questions": len(r["native_request"]["questions"]),
                                   "state_token_len": len(sids),
                                   "state_token_sha256": hx(json.dumps(enc["ids"])),
                                   "old_state_token_len": ob[1], "old_state_token_sha256": ob[2],
                                   "token_len_delta_vs_old": len(sids) - ob[1],
                                   "first_diff_vs_old": z,
                                   "branch_lengths": [len(b["ids"]) for b in brs]})
            with (out / "token_audit.jsonl").open("x", encoding="utf8", newline="\n") as f:
                for r in token_rows:
                    f.write(canon(r) + "\n")
            files.append("token_audit.jsonl")
            receipt.update(status="COMPLETE_A461_PSMI_G0_CPU_GATE_IMPL1",
                           total_arms=total_arms, forward_budget_cap=FORWARD_CAP,
                           cpu_model_loads=1, backbone_forwards=0, gpu_forwards=0,
                           pairs_selected=census["selected"],
                           cross_checks={"lanl_rows": lanl_checked, "twins_scenes": tw_checked})
            code = 0
    except Exception as err:
        receipt.update(status="FAIL_A461_PSMI_G0", error_type=type(err).__name__, error_message=str(err))
        code = 2
    with (out / "execution_receipt.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    files.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in files:
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(canon(receipt))
    return code


if __name__ == "__main__":
    sys.exit(main())
