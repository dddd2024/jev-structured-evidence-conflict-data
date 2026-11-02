#!/usr/bin/env python3
"""A461-G5-G2 Stage-A CPU freeze V3 (zero forwards).

Freezes the tier-2 confirmatory candidate roster through the ACTUAL
full-request native token gate (per G2_DESIGN_V2 narrow review 769b1e76:
the per-block width scan of the feasibility round is not sufficient).

Construction search per candidate scene (all choices contract-legal and
deterministic; first passing combo recorded):
  - treatment block: observed non-candidate blocks, same-label-width first,
    then the rest (both sorted); author = min supporter (V2 supporter rule)
  - SA message: duplicate of an existing candidate vote, list order
  - received timestamp: chronology-legal values in [max(existing), decision_time]
    (mx, the deadline, then 1.0/0.1/0.01 steps; capped) - V2 used mx as a
    convention; G2_DESIGN_V2 requires only the chronology contract + token gate
  - both arms must land at exactly +34 tokens with a preserved trailing
    validator_set suffix; branch token identities must be equal across arms

Zero model loads, zero forwards; tokenizer-only.
"""
import argparse, collections, gzip, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
BLOB_G5V2_PAIRS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
PILOT_TRIO_GROUPS = {"twins_streamlet:run-83", "twins_streamlet:run-114", "twins_streamlet:run-182"}
EXPECTED_WIDTH = 34
HARD_CAP = 128
REPLAYS_PER_RUN = 2


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def sha_file(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def hids(v):
    return hashlib.sha256(json.dumps(v, ensure_ascii=False).encode("utf8")).hexdigest()


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def save(p, v):
    with p.open("x", encoding="utf8", newline="\n") as f:
        json.dump(v, f, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def git_blob(repo, sha):
    t = subprocess.run(["git", "-C", str(repo), "cat-file", "-t", sha], capture_output=True, text=True)
    ck(t.returncode == 0 and t.stdout.strip() == "blob", f"not a blob: {sha}")
    return subprocess.run(["git", "-C", str(repo), "cat-file", "blob", sha],
                          capture_output=True, text=True, check=True).stdout


def oracle2(state):
    cand, rnd, dl, qsz = state["candidate_block"], state["candidate_round"], state["decision_time"], state["quorum_size"]
    per = {}
    for m in state["received_messages"]:
        if m.get("kind") != "vote" or m.get("round") != rnd or m.get("author") not in state["validator_set"]:
            continue
        r = m.get("received")
        if not isinstance(r, (int, float)) or r > dl:
            continue
        per.setdefault(m["author"], []).append(m["block"])
    n_sup = 0
    confl = False
    for a, blocks in per.items():
        if cand in blocks:
            n_sup += 1
            if any(b != cand for b in blocks):
                confl = True
    act = "reject_conflict" if confl else ("accept" if n_sup >= qsz else "wait")
    return {"conflicting_vote": confl, "quorum": n_sup >= qsz, "certificate_action": act}


def oracle1(state):
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
    return {"conflicting_vote": c, "quorum": q, "certificate_action": action}, sorted(support)


def received_candidates(mx, dt, cap=24):
    vals = [mx]
    if dt > mx:
        vals.append(dt)
    for step in (1.0, 0.1, 0.01):
        k = 1
        while len(vals) < cap:
            v = round(mx + step * k, 2)
            if v > dt:
                break
            vals.append(v)
            k += 1
    out, seen = [], set()
    for v in vals:
        if v not in seen and mx <= v <= dt:
            seen.add(v)
            out.append(v)
    return out[:cap]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--constructible-blob", required=True, type=str)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(str(out).startswith(str(ROOT)) and out.parent.is_dir() and not out.exists(), "out dir")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    receipt = {"schema": "JEV_A461_G5_G2_STAGE_A_CPU_FREEZE_RECEIPT_V3", "status": "INCOMPLETE",
               "run_id": "A461_G5_G2_STAGE_A_CPU_FREEZE_R1",
               "gpu_forwards": 0, "model_loads": 0, "tokenizer_loads": 0,
               "network_calls": 0, "tool_actions": 0, "test_or_calibration_rows": 0,
               "output_dir": str(out),
               "frozen_inputs": {"constructible_blob": a.constructible_blob,
                                 "g5v2_pair_rows_blob": BLOB_G5V2_PAIRS, "corpus_sha256": CORPUS_SHA}}
    produced = []
    try:
        out.mkdir(mode=0o700)
        sys.path.insert(0, str(ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"))
        from transformers import AutoTokenizer
        from kev.api import SystemOneRequest, to_record
        from kev.model import encode
        tok = AutoTokenizer.from_pretrained(str(BASE))
        receipt["tokenizer_loads"] = 1
        receipt["tokenizer_source"] = str(BASE)
        receipt["base_tokenizer_json_sha256"] = sha_file(BASE / "tokenizer.json")
        q_tw = json.loads(git_blob(repo, BLOB_G5V2_PAIRS).splitlines()[0])["native_request"]["questions"]

        scenes = {}
        for line in gzip.open(CORPUS, "rt", encoding="utf8"):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["_meta"].get("source") == "twins_streamlet":
                ck(rec["_meta"].get("split") == "development", "non-DEV")
                scenes[hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()] = rec

        cands = [json.loads(x) for x in git_blob(repo, a.constructible_blob).splitlines() if x.strip()]
        ck(len(cands) == 189, f"candidate census {len(cands)}")
        tier2_sw = [c for c in cands if c["same_width_block_available"] and c["source_group"] not in PILOT_TRIO_GROUPS]
        tier3_sw = [c for c in cands if c["same_width_block_available"] and c["source_group"] in PILOT_TRIO_GROUPS]

        def encode_state(state):
            rendered, meta = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
            enc = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
            ck(not enc["state_truncated"], "truncated state")
            return enc, meta

        def arm_delta(state_old_ids, state_with_message):
            """Encode one constructed arm; return (suffix_ok, enc, meta, ids, span, delta)."""
            enc, meta = encode_state(state_with_message)
            a_ids = enc["ids"][:enc["seg"].count(0)]
            delta = len(a_ids) - len(state_old_ids)
            z = 0
            while z < min(len(state_old_ids), len(a_ids)) and state_old_ids[z] == a_ids[z]:
                z += 1
            span = [z, len(a_ids) - (len(state_old_ids) - z)]
            suffix_ok = a_ids[span[1]:] == state_old_ids[z:]
            return suffix_ok, enc, meta, a_ids, span, delta

        roster, gate_fail, width_profiles = [], [], []
        search_stats = {"scenes_searched": 0, "scenes_with_passing_combo": 0, "combos_encoded": 0}
        for c in tier2_sw:
            st_old = scenes[c["scene_sha256"]]["state"]
            o1, support = oracle1(st_old)
            o2 = oracle2(st_old)
            ck(not o1["conflicting_vote"] and o1 == o2, "baseline oracle " + c["scene_sha256"][:8])
            msgs = st_old["received_messages"]
            mx = max(e["received"] for e in msgs)
            cand_votes = [e for e in msgs if e.get("kind") == "vote" and e.get("block") == st_old["candidate_block"]
                          and e.get("round") == st_old["candidate_round"]]
            ck(cand_votes, "no candidate vote")
            recv_vals = received_candidates(mx, st_old["decision_time"])
            search_stats["scenes_searched"] += 1

            o_enc, o_meta = encode_state(st_old)
            o_ids = o_enc["ids"][:o_enc["seg"].count(0)]
            search_stats["combos_encoded"] += 1
            cl = len(tok.encode(str(st_old["candidate_block"]), add_special_tokens=False))
            blocks = sorted({e["block"] for e in msgs} - {st_old["candidate_block"]})
            blocks = sorted({b for b in blocks if len(tok.encode(str(b), add_special_tokens=False)) == cl}) + \
                sorted({b for b in blocks if len(tok.encode(str(b), add_special_tokens=False)) != cl})
            author = support[0]

            # width profile: all (delta, witness) per arm over the legal search space;
            # a transplant pair needs one width W where BOTH scenes can land all four
            # spans (donor new+SA, host new+SA)
            prof_new, prof_sa = {}, {}
            for blk in blocks:
                for rv in recv_vals:
                    m = {"author": author, "block": blk, "kind": "vote",
                         "round": st_old["candidate_round"], "received": rv}
                    st_t = json.loads(canon(st_old))
                    st_t["received_messages"].append(dict(m))
                    g1, _ = oracle1(st_t)
                    g2 = oracle2(st_t)
                    search_stats["combos_encoded"] += 1
                    suffix_ok, enc_t, meta_t, a_ids_t, span_t, delta = arm_delta(o_ids, st_t)
                    if not suffix_ok or not (g1["conflicting_vote"] and g1["certificate_action"] == "reject_conflict" and g1 == g2):
                        continue
                    if delta not in prof_new:
                        prof_new[delta] = {"message": m, "enc": enc_t, "meta": meta_t,
                                           "ids": a_ids_t, "span": span_t, "oracle": g1}
            for cv in cand_votes:
                for rv in recv_vals:
                    dup = json.loads(canon(cv))
                    dup["received"] = rv
                    st_s = json.loads(canon(st_old))
                    st_s["received_messages"].append(dup)
                    g1s, _ = oracle1(st_s)
                    g2s = oracle2(st_s)
                    search_stats["combos_encoded"] += 1
                    suffix_ok, enc_s, meta_s, a_ids_s, span_s, delta = arm_delta(o_ids, st_s)
                    if not suffix_ok or not (g1s["conflicting_vote"] == o1["conflicting_vote"] and
                                             g1s["certificate_action"] == o1["certificate_action"] and g1s == g2s):
                        continue
                    if delta not in prof_sa:
                        prof_sa[delta] = {"message": dup, "enc": enc_s, "meta": meta_s,
                                          "ids": a_ids_s, "span": span_s, "oracle": g1s}
            common_w = sorted(set(prof_new) & set(prof_sa))
            width_profiles.append({"scene_sha256": c["scene_sha256"], "source_group": c["source_group"],
                                   "cell": c["cell"], "new_deltas": sorted(prof_new), "sa_deltas": sorted(prof_sa),
                                   "common_widths": common_w})
            if not common_w:
                gate_fail.append({"scene_sha256": c["scene_sha256"],
                                  "gate": "no_common_width_between_arms",
                                  "new_deltas": sorted(prof_new), "sa_deltas": sorted(prof_sa)})
                continue
            search_stats["scenes_with_passing_combo"] += 1
            # freeze witnesses: prefer the pilot width 34 when available, else the
            # smallest common width (deterministic)
            W = 34 if 34 in common_w else common_w[0]
            enc_t, meta_t, a_ids_t, span_t = prof_new[W]["enc"], prof_new[W]["meta"], prof_new[W]["ids"], prof_new[W]["span"]
            enc_s, meta_s, a_ids_s, span_s = prof_sa[W]["enc"], prof_sa[W]["meta"], prof_sa[W]["ids"], prof_sa[W]["span"]
            treat_msg, g_new1 = prof_new[W]["message"], prof_new[W]["oracle"]
            dup, g_sa1 = prof_sa[W]["message"], prof_sa[W]["oracle"]
            c_idx = [m["id"] for m in meta_t].index("conflicting_vote")
            ck(meta_t[c_idx]["keys"] == ["false", "true"], "C keys")
            branch_shas = {}
            for arm, enc in (("old", o_enc), ("new", enc_t), ("SA", enc_s)):
                seg_list = enc["seg"]
                segs, cur = [], enc["seg"].count(0)
                while cur < len(seg_list):
                    k = seg_list[cur]
                    end = cur
                    while end < len(seg_list) and seg_list[end] == k:
                        end += 1
                    segs.append(hids(enc["ids"][cur:end]))
                    cur = end
                branch_shas[arm] = segs
            if not (branch_shas["new"] == branch_shas["old"] == branch_shas["SA"]):
                gate_fail.append({"scene_sha256": c["scene_sha256"], "gate": "branch_identity"})
                search_stats["scenes_with_passing_combo"] -= 1
                continue
            roster.append({
                "scene_sha256": c["scene_sha256"], "source_group": c["source_group"], "cell": c["cell"],
                "declared_edit_new": {"op": "append_conflict_vote", "message": treat_msg},
                "declared_edit_sa": {"op": "SHAM_same_author_duplicate", "message": dup},
                "oracle_old": o1, "oracle_new": g_new1, "oracle_sa": g_sa1,
                "state_token_len": {"old": len(o_ids), "new": len(a_ids_t), "SA": len(a_ids_s)},
                "appended_span_in_state": {"new": span_t, "SA": span_s},
                "frozen_width": W, "common_widths": common_w,
                "token_ids_sha256": {"old": hids(o_enc["ids"]), "new": hids(enc_t["ids"]), "SA": hids(enc_s["ids"])},
                "conflicting_vote_branch_index": c_idx,
                "construction_search": "block: same-label-width first then remaining (sorted); author=min supporter; "
                                       "SA duplicate in list order; received scanned over chronology-legal values in "
                                       "[max(existing), decision_time] (mx, deadline, 1.0/0.1/0.01 steps, cap 24); "
                                       "width profile recorded for both arms; frozen width = 34 if achievable else smallest common width",
                "full_request_token_gate": "PASS"})
        save(out / "stage_a_candidate_roster.json",
             {"schema": "JEV_A461_G5_G2_STAGE_A_CANDIDATE_ROSTER_V3",
              "tier": "tier2_same_width_full_request_gate_pass",
              "tokenizer_json_sha256": receipt["base_tokenizer_json_sha256"],
              "construction_search_stats": search_stats,
              "gate_failures": gate_fail,
              "candidates": roster})
        produced.append("stage_a_candidate_roster.json")
        with (out / "width_profiles.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for wp in width_profiles:
                f.write(canon(wp) + "\n")
        produced.append("width_profiles.jsonl")

        # pairing feasibility: (donor, host) valid iff common_widths intersect and groups differ
        pair_count, pair_groups, w_hist = 0, set(), collections.Counter()
        rosters_sorted = sorted(roster, key=lambda r: r["scene_sha256"])
        for i in range(len(rosters_sorted)):
            for j in range(len(rosters_sorted)):
                if i == j:
                    continue
                d, h = rosters_sorted[i], rosters_sorted[j]
                inter = set(d["common_widths"]) & set(h["common_widths"])
                if inter and d["source_group"] != h["source_group"]:
                    pair_count += 1
                    pair_groups.add((d["source_group"], h["source_group"]))
        for r in roster:
            for w in r["common_widths"]:
                w_hist[w] += 1
        pairing = {"directed_donor_host_pairs_cross_group": pair_count,
                   "distinct_group_pairs": len(pair_groups),
                   "width_histogram_scenes_per_width": {str(k): v for k, v in sorted(w_hist.items())},
                   "note": "a Stage-A search needs only N forward-screened scenes; donor/host pairing happens after qualification is known"}
        n_roster = len(roster)
        plans = {}
        for N in sorted({26, 62, 93, 124, n_roster}):
            if N > n_roster:
                continue
            arms = N * 3
            per_run = HARD_CAP - REPLAYS_PER_RUN
            runs = -(-arms // per_run)
            plans[f"N{N}"] = {"native_forwards": arms, "replays_total": runs * REPLAYS_PER_RUN,
                              "runs_of_le_128": runs,
                              "note": f"{arms} primary + {runs * REPLAYS_PER_RUN} replays; each run <= {HARD_CAP} incl. replays; roster slice fixed at admission by seeded order"}
        groups_cov = len({r["source_group"] for r in roster})
        save(out / "stage_a_batching_plans.json",
             {"schema": "JEV_A461_G5_G2_STAGE_A_BATCHING_PLANS_V3", "roster_size": n_roster,
              "groups_covered": groups_cov, "pairing_feasibility": pairing, "plans": plans,
              "rule": "planning only; actual counts from the Stage-A runner trace; separate admission + review + user authorization before any GPU"})
        produced.append("stage_a_batching_plans.json")

        receipt.update(status="COMPLETE_A461_G5_G2_STAGE_A_CPU_FREEZE",
                       tier2_same_width_input=len(tier2_sw),
                       construction_search=search_stats,
                       gate_pass=n_roster, gate_fail_count=len(gate_fail),
                       groups_covered=groups_cov, pairing_summary=pairing,
                       tier3_same_width_exploratory_only=len(tier3_sw),
                       batching_plans=plans, gpu_blocked=True,
                       next_gate="Stage-A admission draft -> narrow review -> fresh user authorization; qualification read from raw logits; <2 qualified donors => HOLD")
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G5_G2_STAGE_A_CPU_FREEZE", error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-2000:])
        code = 2
    with (out / "execution_receipt.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    produced.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(canon(receipt))
    return code


if __name__ == "__main__":
    sys.exit(main())
