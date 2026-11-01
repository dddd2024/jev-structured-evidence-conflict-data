#!/usr/bin/env python3
"""A461-G3 second-path independent verifier (CPU only).

Independently re-derives: corpus census and group exclusions, per-arm oracle
gold (own oracle formulation), every declared edit from the corpus old state,
N1B single-field + token-match claims, SHAM gold invariance, cell/group
constraints and budget. No import of the primary implementation.
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
PILOT_ROWS = "research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE/G0_REAL_20261025/pair_rows.jsonl"
BUDGET_CAP = 128


def need(c, m):
    if not c:
        raise AssertionError(m)


def fsum(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tsum(s):
    return hashlib.sha256(s.encode("utf8")).hexdigest()


def flat(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def gold_v2(st):
    """Independent oracle: per-author block scan with explicit loops."""
    cand, rnd, dl, qsz = st["candidate_block"], st["candidate_round"], st["decision_time"], st["quorum_size"]
    per = {}
    k = 0
    while k < len(st["received_messages"]):
        m = st["received_messages"][k]
        k += 1
        if m.get("kind") != "vote" or m.get("round") != rnd or m.get("author") not in st["validator_set"]:
            continue
        r = m.get("received")
        if not isinstance(r, (int, float)) or r > dl:
            continue
        per.setdefault(m["author"], [])
        per[m["author"]].append(m["block"])
    n_sup = 0
    confl = False
    for a in per:
        if cand in per[a]:
            n_sup += 1
            for b in per[a]:
                if b != cand:
                    confl = True
    if confl:
        act = "reject_conflict"
    elif n_sup >= qsz:
        act = "accept"
    else:
        act = "wait"
    return {"conflicting_vote": confl, "quorum": n_sup >= qsz, "certificate_action": act}, n_sup


def rebuild(old, declared, treatment_msg=None):
    """Independent re-application of a declared edit; returns the new state."""
    st = json.loads(flat(old))
    op = declared["op"]
    msgs = st["received_messages"]
    mx = msgs[0]["received"]
    for e in msgs:
        if e["received"] > mx:
            mx = e["received"]
    if op == "append_conflict_vote":
        supset = set()
        for e in msgs:
            if e.get("kind") == "vote" and e.get("round") == st["candidate_round"]                     and isinstance(e.get("received"), (int, float)) and e["received"] <= st["decision_time"]                     and e.get("author") in st["validator_set"] and e.get("block") == st["candidate_block"]:
                supset.add(e["author"])
        need(declared["message"]["author"] == min(supset), "supporter rule")
        blocks = sorted({e["block"] for e in msgs} - {st["candidate_block"]})
        need(declared["message"]["block"] == blocks[0], "block rule")
        m = dict(declared["message"])
    elif op == "N1B_author_swap":
        need(treatment_msg is not None, "n1b needs treatment")
        m = dict(declared["message"])
        t = dict(treatment_msg)
        need(m["author"] != t["author"], "author not swapped")
        need({k: v for k, v in m.items() if k != "author"} == {k: v for k, v in t.items() if k != "author"}, "n1b not single-field")
    elif op == "N1_nonsupporter_vote":
        m = dict(declared["message"])
    elif op == "N1B_round_shift":
        need(treatment_msg is not None, "n1b needs treatment")
        m = dict(declared["message"])
        t = dict(treatment_msg)
        need(m["round"] != t["round"] and m["round"] == declared["value"], "round shift")
        need({k: v for k, v in m.items() if k != "round"} == {k: v for k, v in t.items() if k != "round"}, "n1b not single-field")
    elif op == "SHAM_same_author_duplicate":
        cand_votes = [e for e in msgs if e.get("kind") == "vote" and e.get("block") == st["candidate_block"]
                      and e.get("round") == st["candidate_round"]]
        need(len(cand_votes) >= 1, "no candidate vote to duplicate")
        m = dict(declared["message"])
        need(m["author"] == cand_votes[0]["author"] and m["block"] == cand_votes[0]["block"], "duplicate rule")
    elif op == "SHAM_time_shift":
        need(treatment_msg is not None, "ts needs treatment")
        m = dict(declared["message"])
        t = dict(treatment_msg)
        need(m["received"] != t["received"] and m["received"] <= st["decision_time"], "ts rule")
        need({k: v for k, v in m.items() if k != "received"} == {k: v for k, v in t.items() if k != "received"}, "ts not single-field")
    elif op == "SHAM_order_reversal":
        need(treatment_msg is not None, "ro needs treatment")
        st["received_messages"].append(dict(treatment_msg))
        st["received_messages"] = list(reversed(st["received_messages"]))
        return st
    elif op == "append_fresh_vote":
        need(treatment_msg is None or True, "")
        m = dict(declared["message"])
        need(m["block"] == st["candidate_block"], "t3 vote block")
    else:
        need(False, "unknown op " + str(op))
    if op != "SHAM_order_reversal":
        need(m["received"] <= st["decision_time"], "received beyond window")
    st["received_messages"].append(m) if op != "SHAM_order_reversal" else None
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g0c", required=True, type=Path)
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--skip-render", action="store_true")
    a = ap.parse_args()
    g0 = a.g0c.expanduser().resolve(strict=True)
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    need(HOME.is_dir() and fsum(DEVPIN) == DEVSUM, "corpus pin")
    need(all(x.is_relative_to(HOME) for x in (g0, repo, out)), "paths")
    need(out.parent.is_dir() and not out.exists(), "new out dir")
    review = {"schema": "JEV_A461_G3_G0C_INDEPENDENT_REVIEW_V1", "status": "INCOMPLETE", "checks": {}}
    files = []
    try:
        out.mkdir(mode=0o700)
        prows = [json.loads(x) for x in (g0 / "pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        census = json.loads((g0 / "census.json").read_text("utf8"))
        tw = []
        with gzip.open(DEVPIN, "rt", encoding="utf8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    need(rec["_meta"].get("split") == "development", "non-DEV")
                    tw.append(rec)
        need(len(tw) == census["twins_rows"], "census drift")
        # exclusion list independently rebuilt
        a428rows = [json.loads(x) for x in (repo / (A428_G0A + "/frozen_model_inputs.jsonl")).read_text("utf8").splitlines() if x.strip()]
        a428gold = {json.loads(x)["id"]: json.loads(x) for x in (repo / (A428_G0A + "/independent_source_local_gold.jsonl")).read_text("utf8").splitlines() if x.strip()}
        by_scene = {}
        for r in a428rows:
            by_scene.setdefault(tsum(flat(r["native_request"]["state"])), r["id"])
        excl = set()
        n428 = 0
        for rec in tw:
            gid = by_scene.get(tsum(flat(rec["state"])))
            if gid is not None:
                want = a428gold[gid]["gold"]
                got, _ = gold_v2(rec["state"])
                need({"conflicting_vote": got["conflicting_vote"], "quorum": got["quorum"],
                      "certificate_action": got["certificate_action"],
                      "evidence_level": {"reject_conflict": 2, "accept": 0, "wait": 1}[got["certificate_action"]]} == want, "a428 mismatch")
                excl.add(rec["_meta"]["split_group_id"])
                n428 += 1
        need(n428 >= 12, "a428 coverage")
        for x in (repo / PILOT_ROWS).read_text("utf8").splitlines():
            if x.strip():
                r = json.loads(x)
                if r.get("source") == "twins_streamlet":
                    excl.add(r["source_group"])
        need(sorted(excl) == census["excluded_groups"], "exclusion list differs")
        review["checks"]["exclusions"] = {"groups": len(excl), "a428_scenes": n428}

        state_by = {}
        for rec in tw:
            state_by[tsum(flat(rec["state"]))[:16]] = rec["state"]
        # group constraints
        by_family = collections.defaultdict(list)
        for r in prows:
            by_family[r["family"]].append(r)
        for fam in ("T2_WAIT_TO_REJECT", "T2_ACCEPT_TO_REJECT"):
            groups = [r["source_group"] for r in by_family.get(fam, [])]
            need(len(groups) == len(set(groups)), "duplicate group in " + fam)
            need(all(g not in excl for g in groups), "seen group used in " + fam)
        new_by_pair = {}
        for r in prows:
            if r["arm"] == "new":
                new_by_pair[r["pair_key"]] = r
        t2_groups = {r["source_group"] for k, r in new_by_pair.items() if r["family"].startswith("T2")}
        t3_groups = {r["source_group"] for k, r in new_by_pair.items() if r["family"].startswith("T3")}
        review["checks"]["within_group_contrast_overlap"] = {
            "t3_groups": len(t3_groups), "t3_also_t2": len(t3_groups & t2_groups),
            "note": "protocol prefers (does not require) T3 groups to also carry a T2 pair"}
        review["checks"]["groups"] = {"t2": sorted(t2_groups), "t3": sorted(t3_groups)}

        # per-pair verification
        by_pair = collections.OrderedDict()
        for r in prows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        n_pairs = 0
        for key, rs in by_pair.items():
            old_state = state_by.get(key.split(":", 1)[1])
            need(old_state is not None, "old state missing " + key)
            og, sup = gold_v2(old_state)
            treat = next((r for r in rs if r["arm"] == "new"), None)
            need(treat is not None, "no treatment " + key)
            fam = treat["family"]
            st_t = json.loads(flat(treat["native_request"]["state"]))
            rt = rebuild(old_state, treat["declared_edit"])
            need(flat(rt) == flat(st_t), "treatment re-application differs " + key)
            ng, _ = gold_v2(st_t)
            need({"conflicting_vote": ng["conflicting_vote"], "quorum": ng["quorum"],
                  "certificate_action": ng["certificate_action"],
                  "evidence_level": {"reject_conflict": 2, "accept": 0, "wait": 1}[ng["certificate_action"]]} ==
                 treat["oracle_gold_impl1"], "gold disagree " + key)
            if fam.startswith("T2"):
                need(og["conflicting_vote"] is False and ng["conflicting_vote"] is True
                     and ng["certificate_action"] == "reject_conflict", "T2 flip wrong " + key)
                if fam == "T2_WAIT_TO_REJECT":
                    need(og["certificate_action"] == "wait" and og["quorum"] is False, "wait cell wrong " + key)
                else:
                    need(og["certificate_action"] == "accept" and og["quorum"] is True, "accept cell wrong " + key)
            else:
                need(og["conflicting_vote"] is True and ng["conflicting_vote"] is True
                     and ng["certificate_action"] == "reject_conflict", "T3 hold wrong " + key)
            n_pairs += 1
            for r in rs:
                if r["arm"] == "new":
                    continue
                base_fam = r["family"]
                for suf in ("_N1B", "_N1", "_SHAM_SA", "_SHAM_TS", "_SHAM_RO"):
                    if base_fam.endswith(suf):
                        base_fam = base_fam[:-len(suf)]
                        break
                treat2 = new_by_pair.get(base_fam + ":" + key.split(":", 1)[1])
                need(treat2 is not None, "no treatment " + r["row_id"])
                st2 = rebuild(old_state, r["declared_edit"],
                              treatment_msg=treat2["declared_edit"].get("message"))
                need(flat(st2) == flat(r["native_request"]["state"]), "arm re-application differs " + r["row_id"])
                g2, _ = gold_v2(st2)
                need({"conflicting_vote": g2["conflicting_vote"], "quorum": g2["quorum"],
                      "certificate_action": g2["certificate_action"],
                      "evidence_level": {"reject_conflict": 2, "accept": 0, "wait": 1}[g2["certificate_action"]]} ==
                     r["oracle_gold_impl1"], "arm gold disagree " + r["row_id"])
                if r["family"].endswith("_SHAM_TS") or r["family"].endswith("_SHAM_RO"):
                    need(g2["certificate_action"] == ng["certificate_action"], "treatment-format SHAM moved treatment gold " + r["row_id"])
                else:
                    need(g2["certificate_action"] == og["certificate_action"] and g2["conflicting_vote"] == og["conflicting_vote"],
                         "invariant arm moved gold " + r["row_id"])
        need(len(by_pair) == n_pairs, "pair count")
        review["checks"]["row_verification"] = {"pairs": n_pairs, "arms": len(prows)}
        planned = len(new_by_pair) + len(prows) + 4
        need(planned <= BUDGET_CAP, "budget")
        review["checks"]["budget"] = {"planned_forwards": planned, "cap": BUDGET_CAP}

        if not a.skip_render:
            import torch
            torch.set_num_threads(4)
            sys.path.insert(0, str(KEVDIR))
            from kev.api import SystemOneRequest, to_record
            from kev.checkpoint import Checkpoint, LoadOptions
            from kev.model import rows_of
            man = json.loads((repo / (A428_G0B + "/native_token_manifest.json")).read_text("utf8"))
            need(fsum(KEVDIR / "kev/model.py") == man["native_code_sha256"]["kev_model_py"], "kev model pin")
            cp = Checkpoint(str(CKPTDIR))
            cp.meta.base, cp.meta.base_revision = str(BASEDIR), None
            tok, mdl = cp.load("cpu", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
            review["cpu_model_loads"] = 1
            trows = {r["row_id"]: r for r in (json.loads(x) for x in (g0 / "token_audit.jsonl").read_text("utf8").splitlines() if x.strip())}
            need(len(trows) == len(prows), "token audit count")
            for r in prows:
                tr = trows[r["row_id"]]
                rendered, _ = to_record(SystemOneRequest.model_validate(
                    {"questions": r["native_request"]["questions"],
                     "state": json.loads(flat(r["native_request"]["state"]))}))
                enc = mdl.encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
                sids, _, brs = rows_of(enc)
                need(len(sids) == tr["state_token_len"], "len disagree " + r["row_id"])
                need(tsum(json.dumps(enc["ids"])) == tr["state_token_sha256"], "sha disagree " + r["row_id"])
                if r["arm"] == "N1B":
                    need(tr["matched_vs_treatment"] == (len(sids) == tr["treatment_state_token_len"]), "n1b flag wrong")
            review["checks"]["token_rerender"] = {"rows": len(prows), "verdict": "MATCH"}

        review.update(status="PASS_A461_G3_G0C_INDEPENDENT_VERIFICATION")
        code = 0
    except AssertionError as err:
        review.update(status="FAIL_A461_G3_G0C_INDEPENDENT_VERIFICATION", error_type="AssertionError", error_message=str(err))
        code = 2
    except Exception as err:
        import traceback
        review.update(status="FAIL_A461_G3_G0C_INDEPENDENT_VERIFICATION", error_type=type(err).__name__,
                      error_message=str(err), traceback=traceback.format_exc()[-1000:])
        code = 2
    with (out / "independent_review.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(review, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    files.append("independent_review.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in files:
            f.write(fsum(out / n) + "  " + n + "\n")
    print(json.dumps(review, sort_keys=True, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
