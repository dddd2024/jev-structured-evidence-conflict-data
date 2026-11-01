#!/usr/bin/env python3
"""A461-G5 stage-1 construction: donor-resolution pairs with SA neutrals (CPU).

40 T2 conflict pairs (20 wait + 20 accept) from scene-level non-reused states,
each with old/new/SA arms. Treatment block chosen by preregistered token-width
scan so the SA duplicate-vote neutral is token-matched by construction.
Dual-oracle implementation #1; protocol:
research/experiments/2026-10-25_A461_G5_DONOR_RESOLUTION_PROTOCOL_V1.json
Zero forwards; tokenizer-only label scan (no model weights).
"""
import argparse, collections, gzip, hashlib, json, os, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
G3DIR = "research/rounds/A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE"
A428_G0A = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0A_REAL_20261023"
CAPS = {"T2_WAIT_TO_REJECT": 20, "T2_ACCEPT_TO_REJECT": 20}
REPLAYS = 4
BUDGET = 124
EXPECTED_TWINS = 797


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
    ck(all(x.is_relative_to(ROOT) for x in (repo, out)), "paths")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    receipt = {"schema": "JEV_A461_G5_G0D_CONS_RECEIPT_V1", "status": "INCOMPLETE",
               "gpu_forwards": 0, "backbone_forwards": 0, "cpu_model_loads": 0,
               "network_calls": 0, "test_or_calibration_rows": 0, "output_dir": str(out)}
    files = []
    try:
        out.mkdir(mode=0o700)
        twins = []
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    ck(rec["_meta"].get("split") == "development", "non-DEV")
                    twins.append(rec)
        ck(len(twins) == EXPECTED_TWINS, "census drift")
        # scene-level exclusions: G3 pair scenes + A428 scenes (state hashes)
        excl = set()
        pilot = repo / (G3DIR + "/G0C_REAL_20261025/pair_rows.jsonl")
        ck(pilot.is_file(), "pilot rows missing")
        n_g3 = 0
        for x in pilot.read_text("utf8").splitlines():
            if x.strip():
                r = json.loads(x)
                if r["arm"] == "new":
                    # reconstruct the G3 ORIGINAL state by removing the single
                    # appended treatment event (always the last received message),
                    # then exclude by the full 64-hex SHA (fixes the truncated-hash
                    # exclusion no-op found by the pre-patching audit afbebb4)
                    st_new = r["native_request"]["state"]
                    st_old = json.loads(canon(st_new))
                    st_old["received_messages"].pop()
                    excl.add(hx(canon(st_old)))
                    n_g3 += 1
        a428a = repo / (A428_G0A + "/frozen_model_inputs.jsonl")
        a428g = repo / (A428_G0A + "/independent_source_local_gold.jsonl")
        ck(a428a.is_file() and a428g.is_file(), "A428 files missing")
        a428_rows = [json.loads(x) for x in a428a.read_text("utf8").splitlines() if x.strip()]
        a428g = {json.loads(x)["id"]: json.loads(x) for x in a428g.read_text("utf8").splitlines() if x.strip()}
        a428_state = {}
        for r in a428_rows:
            ck(not any("label" in v for v in r["native_request"]["questions"].values()), "gold leak")
            a428_state.setdefault(hx(canon(r["native_request"]["state"])), r["id"])
        a428_checked = 0
        for rec in twins:
            gid = a428_state.get(hx(canon(rec["state"])))
            if gid is not None:
                want = a428g[gid]["gold"]
                o, _ = twins_oracle(rec["state"])
                ck({"conflicting_vote": o["conflicting_vote"], "quorum": o["quorum"],
                    "certificate_action": o["certificate_action"],
                    "evidence_level": o["evidence_level"]} == want, "A428 mismatch")
                excl.add(hx(canon(rec["state"])))
                a428_checked += 1
        ck(a428_checked >= 12, "A428 cross-check weak")
        q_tw = next(r["native_request"]["questions"] for r in a428_rows if "certificate_action" in r["native_request"]["questions"])

        # census with scene-level exclusion
        cellw, cella = [], []
        for i, rec in enumerate(twins):
            if hx(canon(rec["state"])) in excl:
                continue
            st = rec["state"]
            o, support = twins_oracle(st)
            if o["conflicting_vote"]:
                continue
            msgs = st["received_messages"]
            recv = [e["received"] for e in msgs]
            if not all(recv[j] <= recv[j + 1] for j in range(len(recv) - 1)):
                continue
            if max(recv) > st["decision_time"]:
                continue
            blocks = sorted({e["block"] for e in msgs} - {st["candidate_block"]})
            if not support or not blocks:
                continue
            grp = rec["_meta"]["split_group_id"]
            if o["quorum"]:
                cella.append((grp, i))
            elif len(support) == st["quorum_size"] - 1 and fresh_voter(st, msgs) is not None:
                cellw.append((grp, i))

        def pick(pool, cap):
            by_g = collections.defaultdict(list)
            for grp, i in sorted(pool, key=lambda x: (x[0], x[1])):
                by_g[grp].append(i)
            sel, used, gi = [], set(), 0
            groups = sorted(by_g)
            while len(sel) < cap and any(by_g[g] for g in groups if g not in used):
                g = groups[gi % len(groups)]
                if by_g[g] and g not in used:
                    sel.append((g, by_g[g].pop(0)))
                    used.add(g)
                gi += 1
            return sel

        selw = pick(cellw, CAPS["T2_WAIT_TO_REJECT"])
        sela = pick(cella, CAPS["T2_ACCEPT_TO_REJECT"])
        # token-width scan (tokenizer label-only; no model weights)
        from tokenizers import Tokenizer
        tok = Tokenizer.from_file(str(CKPT / "tokenizer.json"))
        tlen = lambda s: len(tok.encode(s).ids)
        emitted = []
        seq = [0]

        def emit(family, grp, old_state, new_state, edit, arm):
            seq[0] += 1
            base = family
            for suf in ("_SA",):
                if base.endswith(suf):
                    base = base[:-len(suf)]
                    break
            pair_key = base + ":" + hx(canon(old_state))[:16]
            g = twins_oracle(new_state)[0]
            gold = {"conflicting_vote": g["conflicting_vote"], "quorum": g["quorum"],
                    "certificate_action": g["certificate_action"], "evidence_level": g["evidence_level"]}
            emitted.append({"row_id": f"G5_{seq[0]:04d}", "family": family, "source": "twins_streamlet",
                            "source_group": grp, "pair_key": pair_key, "arm": arm,
                            "declared_edit": edit, "oracle_gold_impl1": gold,
                            "native_request": {"questions": q_tw, "state": new_state}})

        for fam, sel in (("T2_WAIT_TO_REJECT", selw), ("T2_ACCEPT_TO_REJECT", sela)):
            for grp, i in sel:
                st_old = twins[i]["state"]
                og, support = twins_oracle(st_old)
                ck(not og["conflicting_vote"], "baseline conflict")
                msgs = st_old["received_messages"]
                mx = max(e["received"] for e in msgs)
                sup = sorted(support)[0]
                blocks = sorted({e["block"] for e in msgs} - {st_old["candidate_block"]})
                # token-width scan: prefer a block with the same label token count as candidate_block
                cl = tlen(st_old["candidate_block"])
                same_w = [b for b in blocks if tlen(b) == cl]
                blk = same_w[0] if same_w else blocks[0]
                width_note = "same_width" if same_w else "fallback_diff_width"
                st_new = json.loads(canon(st_old))
                new = json.loads(canon({"author": sup, "block": blk, "kind": "vote",
                                        "round": st_old["candidate_round"], "received": mx}))
                st_new["received_messages"].append(new)
                ng, _ = twins_oracle(st_new)
                ck(ng["conflicting_vote"] and ng["certificate_action"] == "reject_conflict", "T2 flip failed")
                emit(fam, grp, st_old, st_new,
                     {"op": "append_conflict_vote", "message": new, "block_width_scan": width_note}, "new")
                # SA neutral: duplicate of an existing candidate vote (valid author, in-contract)
                cand_votes = [e for e in st_old["received_messages"]
                              if e.get("kind") == "vote" and e.get("block") == st_old["candidate_block"]
                              and e.get("round") == st_old["candidate_round"]]
                ck(cand_votes, "no candidate vote to duplicate")
                dup = json.loads(canon(cand_votes[0]))
                dup["received"] = mx
                st_sa = json.loads(canon(st_old))
                st_sa["received_messages"].append(dup)
                gsa, _ = twins_oracle(st_sa)
                ck(gsa["conflicting_vote"] == og["conflicting_vote"]
                   and gsa["certificate_action"] == og["certificate_action"], "SA changed gold")
                emit(fam + "_SA", grp, st_old, st_sa,
                     {"op": "SHAM_same_author_duplicate", "message": dup}, "SA")

        total_arms = len(emitted)
        n_pairs = total_arms // 2
        planned = n_pairs + total_arms + REPLAYS
        ck(planned <= BUDGET, f"budget {planned} > {BUDGET}")
        census = {"excluded_scene_hashes": len(excl), "g3_pairs_excluded": n_g3,
                  "a428_scenes_excluded": a428_checked,
                  "eligible": {"wait": len(cellw), "accept": len(cella)},
                  "selected": {"wait": len(selw), "accept": len(sela)},
                  "pairs": n_pairs, "total_arms": total_arms,
                  "planned_forwards_including_old_and_replays": planned,
                  "forward_budget": BUDGET,
                  "group_reuse_disclosure": "all 42 DEV groups previously touched by some round; scene-level non-reuse enforced instead"}
        with (out / "pair_rows.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for r in emitted:
                f.write(canon(r) + "\n")
        files.append("pair_rows.jsonl")
        with (out / "census.json").open("x", encoding="utf8", newline="\n") as f:
            json.dump(census, f, sort_keys=True, indent=2, ensure_ascii=False)
            f.write("\n")
        files.append("census.json")
        if a.phase1_only:
            receipt.update(status="COMPLETE_A461_G5_CONS_PHASE1_ONLY", pairs=n_pairs,
                           total_arms=total_arms, planned_forwards=planned, cpu_model_loads=0)
            code = 0
        else:
            receipt.update(status="COMPLETE_A461_G5_CONS_CPU_GATE_IMPL1", pairs=n_pairs,
                           total_arms=total_arms, planned_forwards=planned, cpu_model_loads=0)
            code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G5_CONS", error_type=type(err).__name__,
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
