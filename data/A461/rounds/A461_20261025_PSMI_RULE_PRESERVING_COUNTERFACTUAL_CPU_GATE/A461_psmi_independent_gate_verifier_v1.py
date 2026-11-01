#!/usr/bin/env python3
"""A461-PSMI G0 second-path independent verifier.

Independently written oracle, edit re-application and token re-render; verifies
the primary G0 output row-by-row. No import of the primary module. CPU only:
one extra checkpoint load for its own encode pass, zero forwards.
"""
import argparse, collections, gzip, hashlib, json, os, sys
from pathlib import Path

HOME = Path.home() / "wjc"
DEVPIN = HOME / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
DEVSUM = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
KEVDIR = HOME / "a5-secjev08b-exact-parent-20261005/source/kev"
CKPTDIR = HOME / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASEDIR = HOME / "kev08b-smoke-20261001-153041/models/base"
A428_G0A = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0A_REAL_20261023"
A428_G0B = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0B_REAL_20261023"
A427_GOLD = "research/rounds/A427_20261023_LANL_TRIAGE_FAIL_VOCABULARY_V2_CPU_GATE/P0_REAL_20261023/independent_gold_rows.jsonl"
BUDGET = 128

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1",
                  TMPDIR=str(HOME / ".tmp"), HF_HOME=str(HOME / ".cache" / "huggingface"),
                  TORCH_HOME=str(HOME / ".cache" / "torch"), XDG_CACHE_HOME=str(HOME / ".cache"),
                  PYTHONPYCACHEPREFIX=str(HOME / ".cache" / "pycache"))
sys.dont_write_bytecode = True

UNKNOWN_WORDS = ("unknown", "unk", "none", "null", "n/a", "na", "?", "unavailable", "-")


def need(cond, msg):
    if not cond:
        raise AssertionError(msg)


def filesum(path):
    acc = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            acc.update(chunk)
    return acc.hexdigest()


def textsum(s):
    return hashlib.sha256(s.encode("utf8")).hexdigest()


def flat(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def name_known(x):
    # independent rewrite of the known-destination predicate
    if not isinstance(x, str):
        return False
    low = x.strip().lower()
    i = 0
    while i < len(UNKNOWN_WORDS):
        if low == UNKNOWN_WORDS[i]:
            return False
        i += 1
    if low.startswith("unknown_"):
        return False
    return len(low) > 0


# ------------- independent oracles (different structure from impl #1) -------------

def twins_gold_v2(st):
    cand = st["candidate_block"]
    rnd = st["candidate_round"]
    dl = st["decision_time"]
    qsz = st["quorum_size"]
    vs = st["validator_set"]
    i = 0
    byauthor = {}
    while i < len(st["received_messages"]):
        m = st["received_messages"][i]
        i += 1
        ok = (m.get("kind") == "vote") and (m.get("round") == rnd) and (m.get("author") in vs)
        ok = ok and isinstance(m.get("received"), (int, float)) and (m["received"] <= dl)
        if not ok:
            continue
        byauthor.setdefault(m["author"], [])
        byauthor[m["author"]].append(m["block"])
    n_sup = 0
    conflict = False
    for author, blocks in byauthor.items():
        has_cand = False
        other = False
        j = 0
        while j < len(blocks):
            if blocks[j] == cand:
                has_cand = True
            if blocks[j] != cand:
                other = True
            j += 1
        if has_cand:
            n_sup += 1
            if other:
                conflict = True
    if conflict:
        act = "reject_conflict"
        lvl = 2
    elif n_sup >= qsz:
        act = "accept"
        lvl = 0
    else:
        act = "wait"
        lvl = 1
    return {"conflicting_vote": conflict, "quorum": n_sup >= qsz,
            "certificate_action": act, "evidence_level": lvl}, n_sup


def lanl_gold_v2(st):
    ce = st["current_event"]
    need(st["history_window_seconds"] == 300, "window")
    need(ce["orientation"] == "LogOn", "current not LogOn")
    need(ce["result"] in ("Success", "Fail"), "current result vocab")
    is_fail = ce["result"] == "Fail"
    nf = 0
    ds = []
    unk = 0
    for e in st["recent_prior_events"]:
        age = e["seconds_before_current"]
        need(isinstance(age, (int, float)) and not isinstance(age, bool) and age >= 0, "age")
        if age <= 0 or age > 300 or e.get("orientation") != "LogOn":
            continue
        need(e["result"] in ("Success", "Fail"), "recent result vocab")
        if e["result"] != "Fail":
            continue
        nf += 1
        d = e.get("destination_computer")
        if name_known(d):
            if d not in ds:
                ds.append(d)
        else:
            unk += 1
    oh = st.get("older_history_summary") or {}
    of = oh.get("failed_attempts", 0)
    od = [x for x in (oh.get("known_failed_destination_computers") or []) if name_known(x)]
    bmn = nf >= 5
    bmx = (nf + of) >= 5
    smn = len(ds) >= 3
    smx = (len(set(ds).union(od)) + unk + of) >= 3
    amb = (bmn != bmx) or (smn != smx)
    risk = bmn or smn
    if risk:
        act = "investigate"
    elif is_fail:
        act = "record_failed_attempt"
    else:
        act = "continue_monitoring"
    return {"failure_burst": bmn, "triage": act, "ambiguous": amb,
            "nf": nf, "ndest": len(ds), "unk": unk, "of": of}


# ------------- independent edit re-application -------------

def old_style_sorted(events):
    k = 0
    while k + 1 < len(events):
        if events[k]["seconds_before_current"] < events[k + 1]["seconds_before_current"]:
            return False
        k += 1
    return True


def redo_lanl_append(st_old, declared):
    st = json.loads(flat(st_old))
    fails = []
    for e in st["recent_prior_events"]:
        if e.get("orientation") == "LogOn" and e["result"] == "Fail" and 0 < e["seconds_before_current"] <= 300:
            fails.append(e)
    dests = sorted({e["destination_computer"] for e in fails if name_known(e["destination_computer"])})
    need(dests, "no failed dest")
    need(declared["destination_computer"] == dests[0], "dest rule differs")
    need(declared["result"] in ("Fail", "Success"), "result vocab")
    used = set()
    for e in st["recent_prior_events"]:
        used.add(e["seconds_before_current"])
    fsecs = []
    for e in fails:
        fsecs.append(e["seconds_before_current"])
    fsecs.sort()
    med = fsecs[len(fsecs) // 2]
    chosen = None
    t = 1
    while t <= 300:
        if t not in used:
            score = (abs(t - med), t)
            if chosen is None or score < chosen[0]:
                chosen = (score, t)
        t += 1
    need(declared["seconds_before_current"] == chosen[1], "seconds rule differs")
    tmpl = json.loads(flat(fails[0]))
    tmpl["seconds_before_current"] = chosen[1]
    tmpl["destination_computer"] = dests[0]
    tmpl["result"] = declared["result"]
    if declared["insert_position_rule"] == "inserted_sorted_desc":
        pos = 0
        for e in st["recent_prior_events"]:
            if e["seconds_before_current"] >= chosen[1]:
                pos += 1
            else:
                break
        st["recent_prior_events"].insert(pos, tmpl)
    else:
        st["recent_prior_events"].append(tmpl)
    return st


def redo_lanl_retime(st_old, declared):
    st = json.loads(flat(st_old))
    idxs = []
    for j, e in enumerate(st["recent_prior_events"]):
        if e.get("orientation") == "LogOn" and e["result"] == "Fail" and 0 < e["seconds_before_current"] <= 300:
            idxs.append(j)
    others = set()
    for j, e in enumerate(st["recent_prior_events"]):
        if j not in idxs:
            others.add(e["seconds_before_current"])
    orig = [st["recent_prior_events"][j]["seconds_before_current"] for j in idxs]
    need(declared["delta"] >= 1, "delta")
    newvals = [o + declared["delta"] for o in orig]
    for t in newvals:
        need(1 <= t <= 300 and t not in others, "retime legality")
    need(len(set(newvals)) == len(newvals), "retime distinct")
    width_change = False
    for a, b in zip(orig, newvals):
        if len(str(a)) != len(str(b)):
            width_change = True
    need(declared["digit_width_change"] == width_change, "width report differs")
    for j, t in zip(idxs, newvals):
        st["recent_prior_events"][j]["seconds_before_current"] = t
    return st


def redo_twins_append(st_old, declared):
    st = json.loads(flat(st_old))
    msgs = st["received_messages"]
    mx = msgs[0]["received"]
    for e in msgs:
        if e["received"] > mx:
            mx = e["received"]
    want = declared["message"]
    need(want["received"] == mx, "received rule differs")
    need(want["round"] == st["candidate_round"], "round rule")
    if want["kind"] == "proposal":
        pass
    elif want["block"] == st["candidate_block"]:
        # T1/T3: author must be first fresh validator in validator_set order
        fresh = None
        for v in st["validator_set"]:
            used = False
            for e in msgs:
                if e.get("author") == v and e.get("kind") == "vote" and e.get("round") == st["candidate_round"] \
                        and isinstance(e.get("received"), (int, float)) and e["received"] <= st["decision_time"]:
                    used = True
                    break
            if not used:
                fresh = v
                break
        if fresh is None:
            need(want["author"] == "z_neutral_outside_set", "unexpected fresh fallback")
        else:
            need(want["author"] == fresh, "fresh voter rule differs")
    else:
        # T2/T2_NEUTRAL: block must be lowest observed non-candidate block
        blocks = sorted({e["block"] for e in msgs} - {st["candidate_block"]})
        need(want["block"] == blocks[0], "block rule differs")
        if want["author"] != "z_neutral_outside_set":
            sup = []
            for a, bl in _by_author_msgs(msgs, st):
                if st["candidate_block"] in bl and a not in sup:
                    sup.append(a)
            sup.sort()
            fresh = None
            for v in st["validator_set"]:
                used = False
                for e in msgs:
                    if e.get("author") == v and e.get("kind") == "vote" and e.get("round") == st["candidate_round"] \
                            and isinstance(e.get("received"), (int, float)) and e["received"] <= st["decision_time"]:
                        used = True
                        break
                if not used:
                    fresh = v
                    break
            if want["author"] in sup:
                need(want["author"] == sup[0], "supporter rule differs")
            else:
                need(want["author"] == fresh or want["author"] == "z_neutral_outside_set",
                     "non-supporter rule differs")
    st["received_messages"].append(dict(want))
    return st


def _by_author_msgs(msgs, st):
    out = {}
    for e in msgs:
        if e.get("kind") == "vote" and e.get("round") == st["candidate_round"] \
                and isinstance(e.get("received"), (int, float)) and e["received"] <= st["decision_time"] \
                and e.get("author") in st["validator_set"]:
            out.setdefault(e["author"], [])
            out[e["author"]].append(e["block"])
    return list(out.items())


TRANSITIONS = {
    "LANL_L1_B_THRESHOLD": ("record_failed_attempt|continue_monitoring", "investigate"),
    "LANL_L3A_RISK_NONREGRESSION": ("investigate", "investigate"),
    "LANL_N2_TIMESTAMP_INVARIANCE": ("record_failed_attempt|continue_monitoring",
                                     "record_failed_attempt|continue_monitoring"),
    "TWINS_T1_QUORUM_AXIS": ("wait", "accept"),
    "TWINS_T2_CONFLICT_AXIS": ("wait|accept", "reject_conflict"),
    "TWINS_T3_CONFLICT_STABILITY": ("reject_conflict", "reject_conflict"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g0", required=True, type=Path)
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--skip-render", action="store_true")
    ap.add_argument("--n1b", required=False, type=Path, default=None,
                    help="optional G0_N1B dir to verify matched-neutral controls")
    a = ap.parse_args()
    g0 = a.g0.expanduser().resolve(strict=True)
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    need(HOME.is_dir(), "~/wjc")
    need(filesum(DEVPIN) == DEVSUM, "corpus pin")
    need(all(x.is_relative_to(HOME) for x in (g0, repo, out)), "paths under ~/wjc")
    need(out.parent.is_dir() and not out.exists(), "new out dir")
    review = {"schema": "JEV_A461_PSMI_G0_INDEPENDENT_REVIEW_V1", "status": "INCOMPLETE",
              "checks": {}, "gpu_forwards": 0, "cpu_model_loads": 0}
    files = []
    try:
        out.mkdir(mode=0o700)
        prows = [json.loads(x) for x in (g0 / "pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        need(len(prows) <= BUDGET, "budget")
        review["checks"]["budget"] = {"arms": len(prows), "cap": BUDGET}
        census = json.loads((g0 / "census.json").read_text("utf8"))

        # independent corpus scan
        tw, ln = [], []
        with gzip.open(DEVPIN, "rt", encoding="utf8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                rec = json.loads(line)
                m = rec["_meta"]
                if m.get("source") == "twins_streamlet":
                    need(m.get("split") == "development", "twins non-DEV")
                    tw.append(rec)
                elif m.get("source") == "lanl_auth_policy":
                    need(m.get("split") == "development", "lanl non-DEV")
                    ln.append(rec)
        need(len(ln) == census["lanl_rows"] and len(tw) == census["twins_rows"], "census drift")

        # archived cross-checks (independent code path)
        a427 = {}
        for x in (repo / A427_GOLD).read_text("utf8").splitlines():
            if x.strip():
                g = json.loads(x)
                a427[g["original_record_sha256"]] = g
        n427 = 0
        for rec in ln:
            g = a427.get(textsum(flat(rec)))
            need(g is not None, "a427 row missing")
            o = lanl_gold_v2(rec["state"])
            need(o["nf"] == g["count_visible_failed_logons"]
                 and o["ndest"] == g["count_distinct_known_failed_destinations"]
                 and o["unk"] == g["unknown_destination_failed_events"]
                 and o["of"] == g["older_summary_failed_count_unscoped"]
                 and o["triage"] == g["inferred"]["triage"]
                 and o["failure_burst"] == g["inferred"]["failure_burst"], "a427 mismatch")
            n427 += 1
        need(n427 == 328, "a427 coverage")
        a428rows = [json.loads(x) for x in (repo / (A428_G0A + "/frozen_model_inputs.jsonl")).read_text("utf8").splitlines() if x.strip()]
        a428gold = {json.loads(x)["id"]: json.loads(x) for x in (repo / (A428_G0A + "/independent_source_local_gold.jsonl")).read_text("utf8").splitlines() if x.strip()}
        by_scene = {}
        for r in a428rows:
            by_scene.setdefault(textsum(flat(r["native_request"]["state"])), r["id"])
        n428 = 0
        for rec in tw:
            gid = by_scene.get(textsum(flat(rec["state"])))
            if gid is None:
                continue
            want = a428gold[gid]["gold"]
            got, _ = twins_gold_v2(rec["state"])
            need({"conflicting_vote": got["conflicting_vote"], "quorum": got["quorum"],
                  "certificate_action": got["certificate_action"],
                  "evidence_level": got["evidence_level"]} == want, "a428 twins mismatch")
            n428 += 1
        need(n428 >= 12, "a428 coverage")
        review["checks"]["archived_crosscheck"] = {"lanl_rows": n427, "twins_scenes": n428}

        # per-row verification
        by_key = collections.OrderedDict()
        for r in prows:
            by_key.setdefault(r["pair_key"], []).append(r)
        fam_counts = collections.Counter()
        for key, rows in by_key.items():
            fam = rows[0]["family"]
            fam_counts[(fam, rows[0]["arm"])] += 1
            old_state = None
            pool = ln if rows[0]["source"] == "lanl_auth_policy" else tw
            h = key.split(":", 1)[1]
            for rec in pool:
                if textsum(flat(rec["state"]))[:16] == h:
                    old_state = rec["state"]
                    break
            need(old_state is not None, "old state not found " + key)
            if rows[0]["source"] == "lanl_auth_policy":
                og = lanl_gold_v2(old_state)
                need(not og["ambiguous"], "old ambiguous " + key)
                expect_old, expect_new = TRANSITIONS[fam]
                need(og["triage"] in expect_old.split("|"), f"old gold {og['triage']} not in {expect_old} for {key}")
                for r in rows:
                    got = lanl_gold_v2(r["native_request"]["state"])
                    need(not got["ambiguous"], "arm ambiguous " + key)
                    need(got["triage"] == r["oracle_gold_impl1"]["triage"]
                         and got["failure_burst"] == r["oracle_gold_impl1"]["failure_burst"],
                         "oracle disagree " + r["row_id"])
                    if r["arm"] == "new":
                        need(got["triage"] in expect_new.split("|"), f"new gold {got['triage']} != {expect_new} {key}")
                    else:
                        need(got["triage"] == og["triage"], "invariant arm moved gold " + r["row_id"])
                    st2 = (redo_lanl_retime(old_state, r["declared_edit"]) if r["arm"] == "retimed"
                           else redo_lanl_append(old_state, r["declared_edit"]))
                    need(flat(st2) == flat(r["native_request"]["state"]), "edit re-application differs " + r["row_id"])
            else:
                og, osup = twins_gold_v2(old_state)
                expect_old, expect_new = TRANSITIONS[fam]
                need(og["certificate_action"] in expect_old.split("|"), f"old gold {og['certificate_action']} for {key}")
                for r in rows:
                    got, sup = twins_gold_v2(r["native_request"]["state"])
                    need(got["certificate_action"] == r["oracle_gold_impl1"]["certificate_action"]
                         and got["conflicting_vote"] == r["oracle_gold_impl1"]["conflicting_vote"]
                         and got["quorum"] == r["oracle_gold_impl1"]["quorum"]
                         and got["evidence_level"] == r["oracle_gold_impl1"]["evidence_level"],
                         "oracle disagree " + r["row_id"])
                    if r["arm"] == "new":
                        need(got["certificate_action"] in expect_new.split("|"),
                             f"new gold {got['certificate_action']} != {expect_new} {key}")
                    else:
                        need(got["certificate_action"] == og["certificate_action"]
                             and got["conflicting_vote"] == og["conflicting_vote"], "invariant moved " + r["row_id"])
                    st2 = redo_twins_append(old_state, r["declared_edit"])
                    need(flat(st2) == flat(r["native_request"]["state"]), "edit re-application differs " + r["row_id"])
        review["checks"]["row_verification"] = {
            "pairs": len(by_key),
            "by_family_arm": {f"{k[0]}:{k[1]}": v for k, v in sorted(fam_counts.items())}}

        # token re-render (2nd CPU load)
        if not a.skip_render:
            import torch
            torch.set_num_threads(4)
            sys.path.insert(0, str(KEVDIR))
            from kev.api import SystemOneRequest, to_record
            from kev.checkpoint import Checkpoint, LoadOptions
            from kev.model import rows_of
            man = json.loads((repo / (A428_G0B + "/native_token_manifest.json")).read_text("utf8"))
            need(filesum(KEVDIR / "kev" / "model.py") == man["native_code_sha256"]["kev_model_py"], "kev model pin")
            need(filesum(KEVDIR / "kev" / "api.py") == man["native_code_sha256"]["kev_api_py"], "kev api pin")
            cp = Checkpoint(str(CKPTDIR))
            cp.meta.base, cp.meta.base_revision = str(BASEDIR), None
            tok, mdl = cp.load("cpu", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
            review["cpu_model_loads"] = 1
            trows = [json.loads(x) for x in (g0 / "token_audit.jsonl").read_text("utf8").splitlines() if x.strip()]
            need(len(trows) == len(prows), "token audit row count")
            old_renders = {}
            for tr, pr in zip(trows, prows):
                need(tr["pair_key"] == pr["pair_key"] and tr["arm"] == pr["arm"], "token row order")
                if tr["pair_key"] not in old_renders:
                    pool = ln if pr["source"] == "lanl_auth_policy" else tw
                    h = pr["pair_key"].split(":", 1)[1]
                    old_state = None
                    for rec in pool:
                        if textsum(flat(rec["state"]))[:16] == h:
                            old_state = rec["state"]
                            break
                    need(old_state is not None, "old state render")
                    # canonicalize before rendering (insertion-order sensitivity)
                    old_state = json.loads(json.dumps(old_state, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
                    qs = pr["native_request"]["questions"]
                    rendered, _ = to_record(SystemOneRequest.model_validate({"questions": qs, "state": old_state}))
                    enc = mdl.encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
                    sids, _, _ = rows_of(enc)
                    old_renders[pr["pair_key"]] = sids
                rendered, _ = to_record(SystemOneRequest.model_validate(pr["native_request"]))
                enc = mdl.encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
                sids, _, brs = rows_of(enc)
                need(len(sids) == tr["state_token_len"], "token len disagree " + str(tr["row_id"]))
                need(textsum(json.dumps(enc["ids"])) == tr["state_token_sha256"], "token sha disagree " + str(tr["row_id"]))
                ob = old_renders[tr["pair_key"]]
                z = 0
                while z < min(len(ob), len(sids)) and ob[z] == sids[z]:
                    z += 1
                need(z == tr["first_diff_vs_old"], "first diff disagree " + str(tr["row_id"]))
                need(tr["token_len_delta_vs_old"] == len(sids) - len(ob), "len delta disagree")
                need(len(brs) == len(pr["native_request"]["questions"]), "branch count")
            review["checks"]["token_rerender"] = {"rows": len(trows), "verdict": "MATCH"}

        # N1B matched-neutral verification (independent re-derivation)
        if a.n1b is not None:
            n1b_dir = a.n1b.expanduser().resolve(strict=True)
            nb_rows = [json.loads(x) for x in (n1b_dir / "n1b_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
            nb_audit = {r["row_id"]: r for r in (json.loads(x) for x in (n1b_dir / "n1b_token_audit.jsonl").read_text("utf8").splitlines() if x.strip())}
            prow_by_id = {r["row_id"]: r for r in prows}
            n_checked = 0
            n_matched_true = 0
            for nb in nb_rows:
                tr = prow_by_id[nb["source_pair_row"]]
                need(nb["pair_key"] == tr["pair_key"], "n1b pair mismatch")
                tm = tr["declared_edit"]["message"]
                d = nb["declared_edit"]
                m2 = d["message"]
                st_tr = tr["native_request"]["state"]
                if d["op"] == "N1B_round_shift":
                    need(m2["round"] == d["value"], "n1b round value")
                    need(m2["round"] != st_tr["candidate_round"], "n1b round not shifted")
                    need({k: v for k, v in m2.items() if k != "round"} == {k: v for k, v in tm.items() if k != "round"}, "n1b not single-field")
                elif d["op"] == "N1B_fresh_author_swap":
                    need(m2["author"] == d["value"], "n1b author value")
                    need(m2["author"] != tm["author"], "n1b author not swapped")
                    need({k: v for k, v in m2.items() if k != "author"} == {k: v for k, v in tm.items() if k != "author"}, "n1b not single-field")
                else:
                    need(False, "unknown n1b op " + str(d["op"]))
                st2 = json.loads(flat(st_tr))
                st2["received_messages"] = st2["received_messages"][:-1] + [m2]
                need(flat(st2) == flat(nb["native_request"]["state"]), "n1b state re-application differs " + nb["row_id"])
                pool = ln if nb["source"] == "lanl_auth_policy" else tw
                h = nb["pair_key"].split(":", 1)[1]
                old_state = None
                for rec in pool:
                    if textsum(flat(rec["state"]))[:16] == h:
                        old_state = rec["state"]
                        break
                need(old_state is not None, "n1b old state")
                if nb["source"] == "lanl_auth_policy":
                    og = lanl_gold_v2(old_state)
                    g2 = lanl_gold_v2(nb["native_request"]["state"])
                    need(g2["triage"] == og["triage"] and g2["failure_burst"] == og["failure_burst"], "n1b lanl gold moved")
                else:
                    og, _ = twins_gold_v2(old_state)
                    g2, _ = twins_gold_v2(nb["native_request"]["state"])
                    need(g2["certificate_action"] == og["certificate_action"]
                         and g2["conflicting_vote"] == og["conflicting_vote"]
                         and g2["quorum"] == og["quorum"], "n1b gold moved " + nb["row_id"])
                    need({"conflicting_vote": g2["conflicting_vote"], "quorum": g2["quorum"],
                          "certificate_action": g2["certificate_action"],
                          "evidence_level": g2["evidence_level"]} == nb["oracle_gold_impl1"], "n1b gold disagree impl1")
                if not a.skip_render:
                    qs = tr["native_request"]["questions"]
                    rendered, _ = to_record(SystemOneRequest.model_validate({"questions": qs, "state": json.loads(json.dumps(nb["native_request"]["state"], sort_keys=True, separators=(",", ":"), ensure_ascii=False))}))
                    enc = mdl.encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
                    sids, _, _ = rows_of(enc)
                    nb_a = nb_audit[nb["row_id"]]
                    need(len(sids) == nb_a["n1b_state_token_len"], "n1b token len disagree " + nb["row_id"])
                    need(textsum(json.dumps(enc["ids"])) == nb_a["n1b_state_token_sha256"], "n1b token sha disagree " + nb["row_id"])
                    rendered_t, _ = to_record(SystemOneRequest.model_validate({"questions": qs, "state": json.loads(json.dumps(st_tr, sort_keys=True, separators=(",", ":"), ensure_ascii=False))}))
                    enc_t = mdl.encode(tok, rendered_t, max_state=8192, max_branch=8192, strict=True)
                    sids_t, _, _ = rows_of(enc_t)
                    equal_cnt = len(sids) == len(sids_t)
                    need(equal_cnt == nb["N1B_token_count_matched"], "n1b match flag wrong " + nb["row_id"])
                    if nb["N1B_token_count_matched"]:
                        n_matched_true += 1
                n_checked += 1
            review["checks"]["n1b_verification"] = {"rows": n_checked, "token_count_matched": n_matched_true}

        review.update(status="PASS_A461_PSMI_G0_INDEPENDENT_VERIFICATION")
        code = 0
    except AssertionError as err:
        review.update(status="FAIL_A461_PSMI_G0_INDEPENDENT_VERIFICATION",
                      error_type="AssertionError", error_message=str(err))
        code = 2
    except Exception as err:
        review.update(status="FAIL_A461_PSMI_G0_INDEPENDENT_VERIFICATION",
                      error_type=type(err).__name__, error_message=str(err))
        code = 2
    with (out / "independent_review.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(review, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    files.append("independent_review.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in files:
            f.write(filesum(out / n) + "  " + n + "\n")
    print(json.dumps(review, sort_keys=True, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
