#!/usr/bin/env python3
"""A461-G3 primary construction: appended-conflict recognition gate (CPU only).

Scales the conflict axis on UNSEEN Twins run groups with both gold cells
(wait->reject, accept->reject), a pre-existing-conflict contrast (T3), token-
matched single-field neutrals (N1B) for every pair, structure-matched neutrals
(N1) and three gold-invariant SHAM families (SA duplicate vote, TS time shift,
RO order reversal). Dual-oracle implementation #1; protocol:
research/experiments/2026-10-25_A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE_PROTOCOL_V1.json
Zero backbone forwards, zero GPU; one CPU load for the render/token phase.
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
PILOT_DIR = "research/rounds/A461_20261025_PSMI_RULE_PRESERVING_COUNTERFACTUAL_CPU_GATE"
CAPS = {"T2_WAIT_TO_REJECT": 10, "T2_ACCEPT_TO_REJECT": 10, "T3_PREEXISTING_CONTRAST": 6}
N1_CAP = 6
SHAM_CAP = 6  # per SHAM family, drawn from T2 pairs
REPLAYS = 4
BUDGET = 106
WINDOW = 300
EXPECTED_TWINS = 797
EXPECTED_LANL = 328

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


def twins_oracle(state):
    """Implementation #1 (same formulation as the pilot primary, re-verified)."""
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


def fresh_voter(state, msgs):
    for v in state["validator_set"]:
        if not any(e.get("kind") == "vote" and e.get("round") == state["candidate_round"]
                   and isinstance(e.get("received"), (int, float))
                   and e["received"] <= state["decision_time"] and e.get("author") == v
                   for e in msgs):
            return v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--phase1-only", action="store_true")
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and CORPUS.is_file() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(all(x.is_relative_to(ROOT) for x in (repo, out)), "under ~/wjc")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    receipt = {"schema": "JEV_A461_G3_G0C_CPU_RECEIPT_V1", "status": "INCOMPLETE",
               "gpu_forwards": 0, "backbone_forwards": 0, "cpu_model_loads": 0,
               "network_calls": 0, "test_or_calibration_rows": 0, "output_dir": str(out)}
    files = []
    try:
        out.mkdir(mode=0o700)
        rows = []
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") in ("twins_streamlet", "lanl_auth_policy"):
                    rows.append(rec)
        ck(all(r["_meta"].get("split") == "development" for r in rows), "non-DEV row")
        twins = [r for r in rows if r["_meta"]["source"] == "twins_streamlet"]
        lanl = [r for r in rows if r["_meta"]["source"] == "lanl_auth_policy"]
        ck(len(twins) == EXPECTED_TWINS and len(lanl) == EXPECTED_LANL, "census drift")

        # archived cross-checks (A428 twins gold by scene hash)
        a428a_path = repo / (A428_G0A + "/frozen_model_inputs.jsonl")
        a428g_path = repo / (A428_G0A + "/independent_source_local_gold.jsonl")
        a428b_path = repo / (A428_G0B + "/native_token_manifest.json")
        ck(all(p.is_file() for p in (a428a_path, a428g_path, a428b_path)), "archived files missing")
        a428_rows = [json.loads(x) for x in a428a_path.read_text("utf8").splitlines() if x.strip()]
        a428g = {json.loads(x)["id"]: json.loads(x) for x in a428g_path.read_text("utf8").splitlines() if x.strip()}
        a428_state = {}
        for r in a428_rows:
            ck(not any("label" in v for v in r["native_request"]["questions"].values()), "gold leak")
            a428_state.setdefault(hx(canon(r["native_request"]["state"])), r["id"])
        q_tw = next(r["native_request"]["questions"] for r in a428_rows if "certificate_action" in r["native_request"]["questions"])
        tw_checked = 0
        for rec in twins:
            gid = a428_state.get(hx(canon(rec["state"])))
            if gid is None:
                continue
            want = a428g[gid]["gold"]
            o, _ = twins_oracle(rec["state"])
            ck({"conflicting_vote": o["conflicting_vote"], "quorum": o["quorum"],
                "certificate_action": o["certificate_action"],
                "evidence_level": o["evidence_level"]} == want, "A428 twins gold mismatch")
            tw_checked += 1
        ck(tw_checked >= 12, f"A428 cross-check weak: {tw_checked}")

        # exclusion list: A428 groups + pilot groups
        a428_groups = {r["_meta"]["split_group_id"] for r in twins
                       if hx(canon(r["state"])) in a428_state}
        pilot_path = repo / (PILOT_DIR + "/G0_REAL_20261025/pair_rows.jsonl")
        ck(pilot_path.is_file(), "pilot pair_rows missing")
        pilot_groups = set()
        for x in pilot_path.read_text("utf8").splitlines():
            if x.strip():
                r = json.loads(x)
                if r.get("source") == "twins_streamlet":
                    pilot_groups.add(r["source_group"])
        excluded_groups = a428_groups | pilot_groups

        # census
        cells = {"T2_WAIT_TO_REJECT": [], "T2_ACCEPT_TO_REJECT": [], "T3_PREEXISTING_CONTRAST": []}
        reasons = collections.Counter()
        for i, rec in enumerate(twins):
            st = rec["state"]
            grp = rec["_meta"]["split_group_id"]
            if grp in excluded_groups:
                reasons["excluded_group"] += 1
                continue
            o, support = twins_oracle(st)
            msgs = st["received_messages"]
            recv = [e["received"] for e in msgs]
            if not all(recv[j] <= recv[j + 1] for j in range(len(recv) - 1)):
                reasons["unsorted"] += 1
                continue
            if max(recv) > st["decision_time"]:
                reasons["infeasible"] += 1
                continue
            blocks = sorted({e["block"] for e in msgs} - {st["candidate_block"]})
            if o["conflicting_vote"]:
                if fresh_voter(st, msgs) is not None and msgs:
                    cells["T3_PREEXISTING_CONTRAST"].append((grp, i))
                else:
                    reasons["t3_no_fresh"] += 1
                continue
            if support and blocks:
                cell = "T2_ACCEPT_TO_REJECT" if o["quorum"] else "T2_WAIT_TO_REJECT"
                cells[cell].append((grp, i))
            else:
                reasons["t2_not_eligible"] += 1
        census = {"twins_rows": len(twins), "lanl_rows": len(lanl),
                  "a428_crosschecked": tw_checked,
                  "excluded_groups": sorted(excluded_groups),
                  "excluded_group_count": len(excluded_groups),
                  "eligible": {k: {"count": len(v), "groups": sorted({g for g, _ in v})} for k, v in cells.items()},
                  "reasons": dict(reasons)}

        def pick_one_per_group(pool, cap, prefer_groups=(), exclude_groups=()):
            by_g = collections.defaultdict(list)
            for grp, i in sorted(pool, key=lambda x: (x[0], x[1])):
                by_g[grp].append(i)
            sel, used = [], set()
            for g in prefer_groups:
                if g in by_g and by_g[g] and len(sel) < cap and g not in exclude_groups:
                    sel.append((g, by_g[g].pop(0)))
                    used.add(g)
            gi = 0
            groups = sorted(by_g)
            while len(sel) < cap and any(by_g[g] for g in groups if g not in exclude_groups and g not in used):
                g = groups[gi % len(groups)]
                if by_g[g] and g not in used and g not in exclude_groups:
                    sel.append((g, by_g[g].pop(0)))
                    used.add(g)
                gi += 1
            return sel

        t2w_sel = pick_one_per_group(cells["T2_WAIT_TO_REJECT"], CAPS["T2_WAIT_TO_REJECT"])
        t2a_sel = pick_one_per_group(cells["T2_ACCEPT_TO_REJECT"], CAPS["T2_ACCEPT_TO_REJECT"], exclude_groups={g for g, _ in t2w_sel})
        t2_groups = {g for g, _ in t2w_sel} | {g for g, _ in t2a_sel}
        t3_sel = pick_one_per_group(cells["T3_PREEXISTING_CONTRAST"], CAPS["T3_PREEXISTING_CONTRAST"],
                                    prefer_groups=sorted(t2_groups))
        census["selected"] = {"T2_wait": len(t2w_sel), "T2_accept": len(t2a_sel), "T3": len(t3_sel)}
        n_pairs = len(t2w_sel) + len(t2a_sel) + len(t3_sel)

        emitted = []
        seq = [0]

        def emit(family, endpoint, grp, old_state, new_state, edit, arm, extra=None):
            seq[0] += 1
            base = family
            for suf in ("_N1B", "_N1", "_SHAM_SA", "_SHAM_TS", "_SHAM_RO"):
                if base.endswith(suf):
                    base = base[:-len(suf)]
                    break
            pair_key = base + ":" + hx(canon(old_state))[:16]
            g = twins_oracle(new_state)[0]
            gold = {"conflicting_vote": g["conflicting_vote"], "quorum": g["quorum"],
                    "certificate_action": g["certificate_action"], "evidence_level": g["evidence_level"]}
            row = {"row_id": f"G3_{seq[0]:04d}", "family": family, "endpoint": endpoint,
                   "source": "twins_streamlet", "source_group": grp, "pair_key": pair_key,
                   "arm": arm, "declared_edit": edit, "oracle_gold_impl1": gold,
                   "native_request": {"questions": q_tw, "state": new_state}}
            if extra:
                row.update(extra)
            emitted.append(row)
            return row

        for fam, sel in (("T2_WAIT_TO_REJECT", t2w_sel), ("T2_ACCEPT_TO_REJECT", t2a_sel)):
            for grp, i in sel:
                st_old = twins[i]["state"]
                og, support = twins_oracle(st_old)
                ck(not og["conflicting_vote"], "baseline conflict")
                msgs = st_old["received_messages"]
                mx = max(e["received"] for e in msgs)
                sup = sorted(support)[0]
                blocks = sorted({e["block"] for e in msgs} - {st_old["candidate_block"]})
                st_new = json.loads(canon(st_old))
                new = json.loads(canon({"author": sup, "block": blocks[0], "kind": "vote",
                                        "round": st_old["candidate_round"], "received": mx}))
                st_new["received_messages"].append(new)
                ng, _ = twins_oracle(st_new)
                ck(ng["conflicting_vote"] and ng["certificate_action"] == "reject_conflict", "T2 flip failed")
                emit(fam, "GOLD_CHANGING_RECOGNITION", grp, st_old, st_new,
                     {"op": "append_conflict_vote", "message": new}, "new")
                # N1B author swap: fresh non-supporting validator, token scan deferred to phase 2
                fresh = fresh_voter(st_old, msgs)
                st_nb = json.loads(canon(st_new))
                nb = json.loads(canon(new))
                nb["author"] = fresh if fresh is not None else "z_neutral_outside_set"
                nb = json.loads(canon(nb))
                st_nb["received_messages"] = st_nb["received_messages"][:-1] + [nb]
                emit(fam + "_N1B", "GOLD_INVARIANT_NUISANCE", grp, st_old, st_nb,
                     {"op": "N1B_author_swap", "value": nb["author"], "message": nb}, "N1B")
                # N1 structure-matched (subset)
                if (fam == "T2_WAIT_TO_REJECT" and sum(1 for e in emitted if e.get("arm") == "N1" and e["family"].startswith("T2_WAIT")) < N1_CAP // 2):
                    st_n1 = json.loads(canon(st_new))
                    n1m = json.loads(canon(new))
                    n1m["author"] = fresh if fresh is not None else "z_neutral_outside_set"
                    n1m = json.loads(canon(n1m))
                    st_n1["received_messages"] = st_n1["received_messages"][:-1] + [n1m]
                    emit(fam + "_N1", "GOLD_INVARIANT_NUISANCE", grp, st_old, st_n1,
                         {"op": "N1_nonsupporter_vote", "message": n1m}, "N1")
        # N1 for accept cell (cap/2)
        n1a = 0
        for grp, i in t2a_sel:
            if n1a >= N1_CAP // 2:
                break
            st_old = twins[i]["state"]
            fresh = fresh_voter(st_old, st_old["received_messages"])
            if fresh is None:
                continue
            og, support = twins_oracle(st_old)
            msgs = st_old["received_messages"]
            mx = max(e["received"] for e in msgs)
            sup = sorted(support)[0]
            blocks = sorted({e["block"] for e in msgs} - {st_old["candidate_block"]})
            st_new = json.loads(canon(st_old))
            new = json.loads(canon({"author": sup, "block": blocks[0], "kind": "vote",
                                    "round": st_old["candidate_round"], "received": mx}))
            st_new["received_messages"].append(new)
            st_n1 = json.loads(canon(st_new))
            n1m = json.loads(canon(new))
            n1m["author"] = fresh
            n1m = json.loads(canon(n1m))
            st_n1["received_messages"] = st_n1["received_messages"][:-1] + [n1m]
            emit("T2_ACCEPT_TO_REJECT_N1", "GOLD_INVARIANT_NUISANCE", grp, st_old, st_n1,
                 {"op": "N1_nonsupporter_vote", "message": n1m}, "N1")
            n1a += 1
        # T3 pairs + N1B round-shift
        for grp, i in t3_sel:
            st_old = twins[i]["state"]
            og, _ = twins_oracle(st_old)
            ck(og["conflicting_vote"], "T3 baseline must be conflicted")
            msgs = st_old["received_messages"]
            mx = max(e["received"] for e in msgs)
            fv = fresh_voter(st_old, msgs)
            ck(fv is not None, "T3 fresh voter")
            st_new = json.loads(canon(st_old))
            new = json.loads(canon({"author": fv, "block": st_old["candidate_block"], "kind": "vote",
                                    "round": st_old["candidate_round"], "received": mx}))
            st_new["received_messages"].append(new)
            ng, _ = twins_oracle(st_new)
            ck(ng["conflicting_vote"] and ng["certificate_action"] == "reject_conflict", "T3 gold must hold")
            emit("T3_PREEXISTING_CONTRAST", "GOLD_INVARIANT_RISK_NONREGRESSION", grp, st_old, st_new,
                 {"op": "append_fresh_vote", "message": new}, "new")
            alt_rounds = sorted({e["round"] for e in st_old["received_messages"]} - {st_old["candidate_round"]})
            if not alt_rounds:
                r0 = st_old["candidate_round"] - 1 if st_old["candidate_round"] > 0 else st_old["candidate_round"] + 1
                alt_rounds = [r0]
            r0 = alt_rounds[0]
            st_nb = json.loads(canon(st_new))
            nb = json.loads(canon(new))
            nb["round"] = r0
            nb = json.loads(canon(nb))
            st_nb["received_messages"] = st_nb["received_messages"][:-1] + [nb]
            emit("T3_PREEXISTING_CONTRAST_N1B", "GOLD_INVARIANT_NUISANCE", grp, st_old, st_nb,
                 {"op": "N1B_round_shift", "value": r0, "message": nb}, "N1B")
        # SHAM arms on first SHAM_CAP T2 pairs (from the wait cell, then accept)
        sham_pairs = [(g, i, "T2_WAIT_TO_REJECT") for g, i in t2w_sel] + [(g, i, "T2_ACCEPT_TO_REJECT") for g, i in t2a_sel]
        sham_used = 0
        for grp, i, fam in sham_pairs:
            if sham_used >= SHAM_CAP:
                break
            st_old = twins[i]["state"]
            og, support = twins_oracle(st_old)
            msgs = st_old["received_messages"]
            mx = max(e["received"] for e in msgs)
            sup = sorted(support)[0]
            blocks = sorted({e["block"] for e in msgs} - {st_old["candidate_block"]})
            st_new = json.loads(canon(st_old))
            new = json.loads(canon({"author": sup, "block": blocks[0], "kind": "vote",
                                    "round": st_old["candidate_round"], "received": mx}))
            st_new["received_messages"].append(new)
            # SHAM-SA: duplicate an existing candidate vote (same author/block/round)
            st_sa = json.loads(canon(st_old))
            cand_votes = [e for e in st_old["received_messages"]
                          if e.get("kind") == "vote" and e.get("block") == st_old["candidate_block"]
                          and e.get("round") == st_old["candidate_round"]]
            dup = json.loads(canon(cand_votes[0]))
            dup["received"] = mx
            st_sa["received_messages"].append(dup)
            gsa, _ = twins_oracle(st_sa)
            ck(gsa["conflicting_vote"] == og["conflicting_vote"] and gsa["certificate_action"] == og["certificate_action"], "SHAM-SA changed gold")
            emit(fam + "_SHAM_SA", "GOLD_INVARIANT_NUISANCE", grp, st_old, st_sa,
                 {"op": "SHAM_same_author_duplicate", "message": dup}, "SHAM_SA")
            # SHAM-TS: treatment vote at another unused in-window second
            used_t = {e["received"] for e in st_old["received_messages"]}
            below = [t for t in sorted(used_t, reverse=True) if t < mx and t not in used_t - {mx}]
            ts_val = None
            for t in sorted((t for t in range(0, int(st_old["decision_time"]) + 1)), reverse=True):
                if isinstance(mx, int) or mx == int(mx):
                    if float(t) not in used_t and t <= st_old["decision_time"] and float(t) < mx:
                        ts_val = float(t)
                        break
            if ts_val is None:
                continue
            st_ts = json.loads(canon(st_new))
            ts = json.loads(canon(new))
            ts["received"] = ts_val
            ts = json.loads(canon(ts))
            st_ts["received_messages"] = st_ts["received_messages"][:-1] + [ts]
            gts, _ = twins_oracle(st_ts)
            ck(gts["conflicting_vote"] and gts["certificate_action"] == "reject_conflict", "SHAM-TS must keep gold")
            emit(fam + "_SHAM_TS", "GOLD_INVARIANT_NUISANCE", grp, st_old, st_ts,
                 {"op": "SHAM_time_shift", "value": ts_val, "message": ts}, "SHAM_TS")
            # SHAM-RO: reverse the treatment message list
            st_ro = json.loads(canon(st_new))
            st_ro["received_messages"] = list(reversed(st_ro["received_messages"]))
            gro, _ = twins_oracle(st_ro)
            ck(gro == twins_oracle(st_new)[0], "SHAM-RO changed gold")
            emit(fam + "_SHAM_RO", "GOLD_INVARIANT_NUISANCE", grp, st_old, st_ro,
                 {"op": "SHAM_order_reversal"}, "SHAM_RO")
            sham_used += 1

        total_arms = len(emitted)
        n_old = len({r["pair_key"] for r in emitted})
        planned = n_old + total_arms + REPLAYS
        ck(planned <= 128, f"budget {planned} > 128")
        census["total_arms"] = total_arms
        census["pairs"] = n_pairs
        census["planned_forwards_including_old_and_replays"] = planned
        with (out / "pair_rows.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for r in emitted:
                f.write(canon(r) + "\n")
        files.append("pair_rows.jsonl")
        with (out / "census.json").open("x", encoding="utf8", newline="\n") as f:
            json.dump(census, f, sort_keys=True, indent=2, ensure_ascii=False)
            f.write("\n")
        files.append("census.json")

        if a.phase1_only:
            receipt.update(status="COMPLETE_A461_G3_G0C_PHASE1_ONLY", total_arms=total_arms,
                           pairs=n_pairs, planned_forwards=planned, cpu_model_loads=0)
            code = 0
        else:
            import torch
            torch.set_num_threads(4)
            sys.path.insert(0, str(SOURCE))
            from kev.api import SystemOneRequest, to_record
            from kev.checkpoint import Checkpoint, LoadOptions
            from kev.model import rows_of
            manifest = json.loads(a428b_path.read_text("utf8"))
            ck(sha_file(SOURCE / "kev/model.py") == manifest["native_code_sha256"]["kev_model_py"]
               and sha_file(SOURCE / "kev/api.py") == manifest["native_code_sha256"]["kev_api_py"], "renderer drift")
            checkpoint = Checkpoint(str(CKPT))
            checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
            tokenizer, model = checkpoint.load("cpu", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
            receipt["cpu_model_loads"] = 1

            def encode_state(state):
                rendered, _ = to_record(SystemOneRequest.model_validate(
                    {"questions": q_tw, "state": json.loads(canon(state))}))
                enc = model.encode(tokenizer, rendered, max_state=8192, max_branch=8192, strict=True)
                sids, _, brs = rows_of(enc)
                ck(not enc["state_truncated"] and all(len(sids) + len(b["ids"]) <= 8192 for b in brs), "truncation")
                return sids, enc, brs

            old_cache = {}

            def old_state_for(pair_key):
                h = pair_key.split(":", 1)[1]
                for rec in twins:
                    if hx(canon(rec["state"]))[:16] == h:
                        return rec["state"]
                raise RuntimeError("old state missing " + pair_key)

            token_rows = []
            by_pair = collections.OrderedDict()
            for r in emitted:
                by_pair.setdefault(r["pair_key"], []).append(r)
            for key, rs in by_pair.items():
                t_ids, t_enc, _ = encode_state(next(r["native_request"]["state"] for r in rs if r["arm"] == "new"))
                if key not in old_cache:
                    o_ids, o_enc, _ = encode_state(old_state_for(key))
                    old_cache[key] = (len(o_ids), hx(json.dumps(o_enc["ids"])))
                for r in sorted(rs, key=lambda x: x["row_id"]):
                    sids, enc, brs = encode_state(r["native_request"]["state"])
                    z = 0
                    while z < min(len(t_ids), len(sids)) and t_ids[z] == sids[z]:
                        z += 1
                    token_rows.append({"row_id": r["row_id"], "pair_key": key, "arm": r["arm"],
                                       "family": r["family"], "questions": 4,
                                       "state_token_len": len(sids),
                                       "state_token_sha256": hx(json.dumps(enc["ids"])),
                                       "treatment_state_token_len": len(t_ids),
                                       "token_len_delta_vs_treatment": len(sids) - len(t_ids),
                                       "matched_vs_treatment": len(sids) == len(t_ids),
                                       "first_diff_vs_treatment": z,
                                       "old_state_token_len": old_cache[key][0],
                                       "old_state_token_sha256": old_cache[key][1],
                                       "branch_lengths": [len(b["ids"]) for b in brs]})
            with (out / "token_audit.jsonl").open("x", encoding="utf8", newline="\n") as f:
                for r in token_rows:
                    f.write(canon(r) + "\n")
            files.append("token_audit.jsonl")
            n1b_rows = [r for r in token_rows if r["arm"] == "N1B"]
            receipt.update(status="COMPLETE_A461_G3_G0C_CPU_GATE_IMPL1",
                           total_arms=total_arms, pairs=n_pairs,
                           planned_forwards=planned, budget=128,
                           n1b_matched_vs_treatment=sum(1 for r in n1b_rows if r["matched_vs_treatment"]),
                           n1b_total=len(n1b_rows), cpu_model_loads=1)
            code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G3_G0C", error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-1200:])
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
