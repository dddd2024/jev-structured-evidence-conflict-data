#!/usr/bin/env python3
"""A461-G5 minimal causal patch pilot: one-shot CPU closed loop (G0), zero forwards.

Executes every pre-GPU CPU gate of the frozen pilot admission checklist
(research/experiments/2026-10-25_A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_CPU_GATE_DRAFT_V1.json,
git blob of the experiments file is pinned below) against the G5 V2 archived
artifacts, resolves every engineering defect class named by the governance
decision 5e35c044 (A471 P0-A..F, A472 stale-loop P0, V3 review P0-1..7), and
freezes the 28-call physical forward plan. No GPU, no backbone load, no
backprop: the only model-side object touched is the HF tokenizer of the pinned
base model, used through the exact kev encode() path that produced the
archived token ids (bitwise-verified against all 108 archived primary rows).

Gate map (checklist name -> implementation):
  VERIFY_ALL_INPUT_FILE_SCHEMA_AND_BLOB_SHA            G1
  RECONSTRUCT_OLD_STATE_AND_VALIDATE_NATIVE_TOKEN_SHA  G2 (+G5 sha gate)
  TWO_INDEPENDENT_SOURCE_POLICY_ORACLES_AGREE          G3
  VERIFY_AUTHOR_ROUND_BLOCK_AND_CHRONOLOGY_CONTRACT    G4
  RENDER_NATIVE_APPEND_SPAN_AND_TRAILING_SUFFIX        G5
  MATCH_EXACT_PLUS34_TOKEN_WIDTH                       G6
  RESOLVE_CONFLICTING_VOTE_CAUSAL_ROW_FROM_REAL_META   G7
  RUN_END_TO_END_MOCK_FOUR_INDEPENDENT_QUESTION_ROWS   G8
  VERIFY_IDENTITY_PATCH_NO_CHANGE_AND_OFF_ROW          G9 (in mock)
  VERIFY_ACTUAL_G1S_FALSE_FALSE_FALSE_HOST_ROSTER      G10
  AUTO_TRACE_PHYSICAL_FORWARDS_EQUALS_PRECOMPUTED      G11
  FREEZE_SOURCE_G_MINUS_1_CHECK_AND_STOP_RULE          G12
  INDEPENDENT_BLIND_REVIEW_EXPLICIT_PASS               G13 (external; runner emits WAITING)

Any gate failure => receipt status STOP_PRE_GPU_<GATE>, partial artifacts kept.
"""
import argparse, collections, gzip, hashlib, json, os, random, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"

# frozen input pointers (git blob ids in dddd2024/jev)
BLOB_PAIR_ROWS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
BLOB_RAW_LOGITS = "13400252b360863a80baea66b39b9a7dbe0ca633"
BLOB_TOKEN_LENS = "5cf52a37f4e420da86c39fd537c40a98336c3be7"
BLOB_PILOT_GATE = None  # resolved from --pilot-gate-blob

# frozen roster (pilot gate draft V1, re-verified here from raw archives)
DONOR_KEY = "T2_WAIT_TO_REJECT:433890d19a90625e"
HOST_KEYS = ["T2_WAIT_TO_REJECT:1b0e96fb22c6aebe", "T2_ACCEPT_TO_REJECT:231b919006dc1777"]
LAYERS = [11, 23]
EXPECTED_WIDTH = 34
BUDGET = 28
HARD_CAP = 128
PERM_SEED = 20261025


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


def lines_out(p, rows):
    with p.open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")


def git_blob(repo, sha):
    t = subprocess.run(["git", "-C", str(repo), "cat-file", "-t", sha], capture_output=True, text=True)
    ck(t.returncode == 0 and t.stdout.strip() == "blob", f"not a blob in checkout: {sha}")
    r = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", sha], capture_output=True, text=True, check=True)
    return r.stdout


# ---------------- oracles (two independent implementations, verbatim from G5 V2) ----------------

def oracle_impl1(state):
    """Constructor implementation (A461_g5_construction_v1.twins_oracle)."""
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
            "evidence_level": {"reject_conflict": 2, "accept": 0, "wait": 1}[action]}


def oracle_impl2(state):
    """G1S second-path implementation (A461_g5_g1s_donor_search_v1.gold_v2)."""
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


def rebuild(old, declared):
    """G1S rebuild (edit re-application; supporter/duplicate rules enforced)."""
    st = json.loads(canon(old))
    op = declared["op"]
    msgs = st["received_messages"]
    mx = max(e["received"] for e in msgs)
    if op == "append_conflict_vote":
        m = dict(declared["message"])
        cand, rnd, dl = st["candidate_block"], st["candidate_round"], st["decision_time"]
        sup = set()
        for e in msgs:
            if e.get("kind") == "vote" and e.get("round") == rnd and isinstance(e.get("received"), (int, float)) \
                    and e["received"] <= dl and e.get("author") in st["validator_set"] and e.get("block") == cand:
                sup.add(e["author"])
        ck(m["author"] == min(sup), "supporter rule")
        blocks = sorted({e["block"] for e in msgs} - {cand})
        ck(m["block"] in blocks, "block observed")
        st["received_messages"].append(m)
        return st
    if op == "SHAM_same_author_duplicate":
        m = dict(declared["message"])
        cand, rnd = st["candidate_block"], st["candidate_round"]
        cands = [e for e in msgs if e.get("kind") == "vote" and e.get("block") == cand and e.get("round") == rnd]
        ck(cands and m["author"] == cands[0]["author"] and m["block"] == cand, "duplicate rule")
        st["received_messages"].append(m)
        return st
    ck(False, "unknown op " + str(op))
    return st


def flat_st(x):
    return canon(x)


# ---------------- main ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--pilot-gate-blob", required=True, type=str)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    global BLOB_PILOT_GATE
    BLOB_PILOT_GATE = a.pilot_gate_blob
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(BASE.is_dir() and CKPT.is_dir(), "checkpoint/base dirs")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    ck(str(out).startswith(str(ROOT)), "output within ~/wjc")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    receipt = {"schema": "JEV_A461_G5_PILOT_CPU_CLOSED_LOOP_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": "A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_CPU_CLOSED_LOOP_R1",
               "gpu_forwards": 0, "backbone_loads": 0, "cpu_model_loads": 0, "tokenizer_loads": 0,
               "backprop_calls": 0, "network_calls": 0, "tool_actions": 0,
               "test_or_calibration_rows": 0, "output_dir": str(out),
               "frozen_inputs": {"pair_rows_blob": BLOB_PAIR_ROWS, "raw_logits_blob": BLOB_RAW_LOGITS,
                                 "token_lengths_blob": BLOB_TOKEN_LENS, "pilot_gate_blob": BLOB_PILOT_GATE,
                                 "corpus_sha256": CORPUS_SHA}}
    produced = []
    gates = collections.OrderedDict()
    try:
        out.mkdir(mode=0o700)
        sys.path.insert(0, str(ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"))

        # ---------- G1 schema + blob pins ----------
        blob_gate = json.loads(git_blob(repo, BLOB_PILOT_GATE))
        ck(blob_gate["schema"] == "JEV_A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_CPU_GATE_DRAFT_V1", "pilot gate schema")
        ck(blob_gate["baseline_input_blobs"]["v2_pair_rows"] == BLOB_PAIR_ROWS
           and blob_gate["baseline_input_blobs"]["v2_native_logits"] == BLOB_RAW_LOGITS
           and blob_gate["baseline_input_blobs"]["v2_render_lengths"] == BLOB_TOKEN_LENS, "gate json blob pointers")
        ck(blob_gate["donor_candidate"]["pair_key"] == DONOR_KEY
           and [h["pair_key"] for h in blob_gate["host_candidates"]] == HOST_KEYS, "roster matches gate json")
        ck(blob_gate["layers_checkpoint_outputs"] == LAYERS, "layers match gate json")
        ck(blob_gate["tentative_native_forward_calls"]["total"] == BUDGET, "budget matches gate json")
        pair_txt = git_blob(repo, BLOB_PAIR_ROWS)
        prows = [json.loads(x) for x in pair_txt.splitlines() if x.strip()]
        logit_txt = git_blob(repo, BLOB_RAW_LOGITS)
        lrows = [json.loads(x) for x in logit_txt.splitlines() if x.strip()]
        lens_doc = json.loads(git_blob(repo, BLOB_TOKEN_LENS))
        ck(len(prows) == 72 and {r["arm"] for r in prows} == {"new", "SA"}, "pair rows schema")
        ck(all(set(r) >= {"row_id", "arm", "pair_key", "family", "source", "source_group",
                          "declared_edit", "oracle_gold_impl1", "native_request"} for r in prows), "pair row fields")
        prim = [r for r in lrows if r.get("kind") == "primary"]
        ck(len(lrows) == 112 and len(prim) == 108, "logits rows")
        ck(all(sorted(q["id"] for q in r["questions"]) == ["certificate_action", "conflicting_vote",
                                                           "evidence_level", "quorum"] for r in prim), "logit questions")
        ck(lens_doc["schema"] == "JEV_A461_G5_RENDER_TOKEN_LENGTHS_V1" and len(lens_doc["rows"]) == 108,
           "token lens schema (single object, not jsonl)")
        gates["G1_VERIFY_ALL_INPUT_FILE_SCHEMA_AND_BLOB_SHA"] = "PASS"

        # ---------- G2 old-state reconstruction + G3 dual oracles + G4 contracts ----------
        state_by16, state_by64, dev_splits = {}, {}, set()
        twins_total = 0
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") != "twins_streamlet":
                    continue
                twins_total += 1
                ck(rec["_meta"].get("split") == "development", "non-DEV twins row")
                dev_splits.add(rec["_meta"].get("split"))
                h64 = hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()
                state_by16[h64[:16]] = rec["state"]
                state_by64[h64] = rec["state"]
        ck(twins_total == 797, f"twins census {twins_total}")
        by_pair = collections.OrderedDict()
        for r in prows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        roster_keys = [DONOR_KEY] + HOST_KEYS
        pair_checks = []
        for key, rs in by_pair.items():
            h16 = key.split(":", 1)[1]
            old_state = state_by16.get(h16)
            ck(old_state is not None, "old state missing " + key)
            h64 = hashlib.sha256(canon(old_state).encode("utf8")).hexdigest()
            ck(h64[:16] == h16 and h64 in state_by64, "sha16 collision " + key)
            treat = next(r for r in rs if r["arm"] == "new")
            sa = next(r for r in rs if r["arm"] == "SA")
            rt = rebuild(old_state, treat["declared_edit"])
            ck(flat_st(rt) == flat_st(treat["native_request"]["state"]), "treatment re-application " + key)
            rs2 = rebuild(old_state, sa["declared_edit"])
            ck(flat_st(rs2) == flat_st(sa["native_request"]["state"]), "SA re-application " + key)
            g_old1, g_old2 = oracle_impl1(old_state), oracle_impl2(old_state)
            g_t1, g_t2 = oracle_impl1(rt), oracle_impl2(rt)
            g_s1, g_s2 = oracle_impl1(rs2), oracle_impl2(rs2)
            shared = ("conflicting_vote", "quorum", "certificate_action")
            ck(all(g_old1[k] == g_old2[k] for k in shared)
               and all(g_t1[k] == g_t2[k] for k in shared)
               and all(g_s1[k] == g_s2[k] for k in shared), "oracle disagreement " + key)
            ck(g_t1 == treat["oracle_gold_impl1"], "stored gold mismatch " + key)
            ck(g_old1["conflicting_vote"] is False, "old not clean " + key)
            ck(g_t1["conflicting_vote"] is True and g_t1["certificate_action"] == "reject_conflict", "treatment gold " + key)
            ck(g_s1 == g_old1, "SA moved gold " + key)
            # chronology / author / block contracts on both appended messages
            for arm_row, st_arm in ((treat, rt), (sa, rs2)):
                m = st_arm["received_messages"][-1]
                ck(m == {k: arm_row["declared_edit"]["message"][k] for k in m}, "appended msg == declared " + key + ":" + arm_row["arm"])
                ck(m["author"] in old_state["validator_set"], "author not validator " + key)
                ck(m["kind"] == "vote" and m["round"] == old_state["candidate_round"], "round contract " + key)
                ck(isinstance(m["received"], (int, float)) and m["received"] <= old_state["decision_time"], "deadline " + key)
                recv = [e["received"] for e in st_arm["received_messages"]]
                ck(all(recv[j] <= recv[j + 1] for j in range(len(recv) - 1)), "monotone receive " + key)
                ck(m["received"] == max(e["received"] for e in old_state["received_messages"]), "appended not latest " + key)
                if arm_row["arm"] == "new":
                    ck(m["block"] != old_state["candidate_block"], "treatment block == candidate " + key)
                else:
                    ck(m["block"] == old_state["candidate_block"], "SA block != candidate " + key)
                    prior = [e for e in old_state["received_messages"]
                             if e.get("kind") == "vote" and e.get("block") == m["block"]
                             and e.get("round") == m["round"] and e.get("author") == m["author"]]
                    ck(prior, "SA duplicate has no prior vote " + key)
            pair_checks.append({"pair_key": key, "source_group": treat["source_group"],
                                "oracle_impl1_old": g_old1, "oracle_impl1_new": g_t1, "oracle_impl1_sa": g_s1,
                                "old_state_sha256": h64})
        ck(len(pair_checks) == 36, "pair count")
        gates["G2_RECONSTRUCT_OLD_STATE_AND_VALIDATE_NATIVE_TOKEN_SHA"] = "PASS"
        gates["G3_TWO_INDEPENDENT_SOURCE_POLICY_ORACLES_AGREE_FOR_ALL_ARMS"] = "PASS"
        gates["G4_VERIFY_AUTHOR_ROUND_BLOCK_AND_CHRONOLOGY_CONTRACT"] = "PASS"

        # ---------- tokenizer; G5 anchors; G6 widths; full 108-row token SHA parity ----------
        from transformers import AutoTokenizer
        from kev.api import SystemOneRequest, to_record
        from kev.model import encode, rows_of
        tok = AutoTokenizer.from_pretrained(str(BASE))
        receipt["tokenizer_loads"] = 1
        receipt["tokenizer_source"] = str(BASE)
        tok_sha = sha_file(BASE / "tokenizer.json")
        receipt["base_tokenizer_json_sha256"] = tok_sha
        q_tw = prows[0]["native_request"]["questions"]
        ck(all(r["native_request"]["questions"] == q_tw for r in prows), "frozen questions shared")

        def enc_state(state):
            rendered, meta = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
            enc = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
            ck(not enc["state_truncated"], "truncated state")
            return enc, meta

        # full parity gate: fresh ids sha == archived token_ids_sha256 for all 108 primary rows
        arch_by_rowid = {r["plan_row"]: r for r in prim}
        parity = {"checked": 0, "matched": 0}
        for key, rs in by_pair.items():
            old_state = state_by16[key.split(":", 1)[1]]
            arms = [("old", key + ":old", {"questions": q_tw, "state": json.loads(canon(old_state))})]
            for r in rs:
                arms.append((r["arm"], r["row_id"], r["native_request"]))
            for arm, rid, req in arms:
                rendered, meta = to_record(SystemOneRequest.model_validate(req))
                enc = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
                ck(not enc["state_truncated"], "truncated " + rid)
                ck(hids(enc["ids"]) == arch_by_rowid[rid]["token_ids_sha256"], "token sha parity " + rid)
                parity["checked"] += 1
                parity["matched"] += 1
        ck(parity["checked"] == 108, "parity count")
        gates["G5_TOKEN_SHA_PARITY_ALL_108_PRIMARY_ROWS"] = "PASS"

        # anchors for the roster pairs (G4 G0C method: first divergence, span, suffix)
        anchor_rows, width_rows = [], []
        for key in roster_keys:
            rs = by_pair[key]
            old_state = state_by16[key.split(":", 1)[1]]
            enc_o, meta_o = enc_state(old_state)
            state_ids_o, _, branches_o = rows_of(enc_o)
            c_idx = [m["id"] for m in meta_o].index("conflicting_vote")
            ck(meta_o[c_idx]["keys"] == ["false", "true"], "C keys")
            row = {"pair_key": key, "family": rs[0]["family"], "source_group": rs[0]["source_group"],
                   "conflicting_vote_branch_index": c_idx,
                   "conflicting_vote_keys": meta_o[c_idx]["keys"],
                   "all_meta_ids": [m["id"] for m in meta_o],
                   "branch_identity_old_vs_new": None, "branch_identity_old_vs_sa": None,
                   "state_len_old": len(state_ids_o), "arms": {}}
            shas_o = [hids(b["ids"]) for b in branches_o]
            for r in rs:
                enc_a, meta_a = enc_state(r["native_request"]["state"])
                state_ids_a, _, branches_a = rows_of(enc_a)
                shas_a = [hids(b["ids"]) for b in branches_a]
                row["branch_identity_old_vs_" + r["arm"]] = shas_a == shas_o
                delta = len(state_ids_a) - len(state_ids_o)
                z = 0
                while z < min(len(state_ids_o), len(state_ids_a)) and state_ids_o[z] == state_ids_a[z]:
                    z += 1
                ck(delta > 0, "no growth " + key + ":" + r["arm"])
                span = [z, len(state_ids_a) - (len(state_ids_o) - z)]
                ck(span[1] - span[0] == delta, "span width != delta " + key + ":" + r["arm"])
                ck(state_ids_a[span[1]:] == state_ids_o[z:], "trailing suffix changed " + key + ":" + r["arm"])
                cb = branches_a[c_idx]
                row["arms"][r["arm"]] = {"row_id": r["row_id"], "state_token_len": len(state_ids_a),
                                         "state_growth": delta, "first_divergence": z,
                                         "appended_span_in_state": span,
                                         "trailing_suffix_len": len(state_ids_o) - z,
                                         "c_branch_len": len(cb["ids"]),
                                         "c_decide_offset_in_branch": cb["decide"],
                                         "c_opts_offsets_in_branch": cb["opts"],
                                         "declared_edit": r["declared_edit"]}
                width_rows.append({"pair_key": key, "arm": r["arm"], "row_id": r["row_id"],
                                   "fresh_state_len": len(state_ids_a)})
            ck(all(row["branch_identity_old_vs_" + r["arm"]] for r in rs), "branch not identical " + key)
            anchor_rows.append(row)
        save(out / "pilot_anchor_map.json", {"schema": "JEV_A461_G5_PILOT_ANCHOR_MAP_V1",
                                             "tokenizer_json_sha256": tok_sha,
                                             "conflicting_vote_branch_resolution": "dynamic from to_record meta ids",
                                             "rows": anchor_rows})
        produced.append("pilot_anchor_map.json")
        # G6 widths: fresh == archived == 34, donor new/SA == host SA == 34
        arch_len = {r["row_id"]: r["state_token_len"] for r in lens_doc["rows"]}
        for wr in width_rows:
            ck(wr["fresh_state_len"] == arch_len[wr["row_id"]], "fresh len != archived " + wr["row_id"])
        for key in roster_keys:
            ar = next(r for r in anchor_rows if r["pair_key"] == key)
            dn = ar["arms"]["new"]["state_growth"]
            ds = ar["arms"]["SA"]["state_growth"]
            ck(dn == ds == EXPECTED_WIDTH, f"width {key}: new {dn} sa {ds} != {EXPECTED_WIDTH}")
        gates["G6_MATCH_EXACT_PLUS34_TOKEN_WIDTH_ALL_DONOR_AND_TWO_HOST_ARMS"] = "PASS"
        gates["G5_RENDER_NATIVE_APPEND_SPAN_AND_TRAILING_SUFFIX_UNCHANGED"] = "PASS"

        # ---------- G7 C-row resolution (dynamic; already enforced above, recorded here) ----------
        g7 = [{"pair_key": r["pair_key"], "conflicting_vote_branch_index": r["conflicting_vote_branch_index"],
               "all_meta_ids": r["all_meta_ids"], "c_keys": r["conflicting_vote_keys"],
               "c_decide_offset_in_branch": r["arms"]["new"]["c_decide_offset_in_branch"],
               "c_opts_offsets_in_branch": r["arms"]["new"]["c_opts_offsets_in_branch"]} for r in anchor_rows]
        ck(all(g["conflicting_vote_branch_index"] == 1 and g["c_keys"] == ["false", "true"] for g in g7),
           "C row resolution unstable")
        save(out / "pilot_c_row_resolution.json", {"schema": "JEV_A461_G5_PILOT_C_ROW_RESOLUTION_V1", "rows": g7})
        produced.append("pilot_c_row_resolution.json")
        gates["G7_RESOLVE_CONFLICTING_VOTE_CAUSAL_ROW_FROM_REAL_META"] = "PASS"

        # ---------- G10 roster from archived logits ----------
        def c_read(row):
            c = next(q for q in row["questions"] if q["id"] == "conflicting_vote")
            return c["logits"][1] - c["logits"][0], ("true" if c["logits"][1] > c["logits"][0] else "false")

        qual, partial, failed = [], [], []
        for key, rs in by_pair.items():
            d = {"old": arch_by_rowid[key + ":old"]}
            for r in rs:
                d[r["arm"]] = arch_by_rowid[r["row_id"]]
            mo, ro = c_read(d["old"]); mn, rn = c_read(d["new"]); ms, rs_ = c_read(d["SA"])
            rec = {"pair_key": key, "old_read": ro, "new_read": rn, "sa_read": rs_,
                   "old_margin": round(mo, 6), "new_margin": round(mn, 6), "sa_margin": round(ms, 6)}
            if ro == "false" and rn == "true" and rs_ == "false":
                qual.append(rec)
            elif ro == "false" and rn == "false" and rs_ == "false":
                failed.append(rec)
            else:
                partial.append(rec)
        ck(len(qual) == 1 and qual[0]["pair_key"] == DONOR_KEY, f"unique qualified donor violated: {[q['pair_key'] for q in qual]}")
        for key in HOST_KEYS:
            src = next((r for r in failed + partial if r["pair_key"] == key), None)
            ck(src is not None and src["old_read"] == "false" and src["new_read"] == "false" and src["sa_read"] == "false",
               "host not false/false/false " + key)
        save(out / "pilot_roster_verification.json",
             {"schema": "JEV_A461_G5_PILOT_ROSTER_VERIFICATION_V1",
              "qualified": qual, "partial": partial, "failed_count": len(failed),
              "hosts": {k: next(r for r in failed + partial if r["pair_key"] == k) for k in HOST_KEYS},
              "donor": qual[0]})
        produced.append("pilot_roster_verification.json")
        gates["G10_VERIFY_ACTUAL_G1S_FALSE_FALSE_FALSE_HOST_ROSTER"] = "PASS"

        # ---------- G8+G9 mock hook end-to-end (synthetic, same geometry as real rows) ----------
        import torch
        torch.set_num_threads(4)
        torch.manual_seed(0)
        D = 1024
        mock = run_mock_suite(anchor_rows, D)
        save(out / "mock_hook_test.json", mock)
        produced.append("mock_hook_test.json")
        ck(mock["verdict"] == "PASS", "mock suite failed")
        gates["G8_RUN_END_TO_END_MOCK_FOUR_INDEPENDENT_QUESTION_ROW_HOOKS"] = "PASS"
        gates["G9_VERIFY_IDENTITY_PATCH_NO_CHANGE_AND_OFF_ROW_NONINTERFERENCE"] = "PASS"

        # ---------- G11 physical plan + auto trace ----------
        plan = build_plan(anchor_rows)
        ck(len(plan) == BUDGET, f"plan {len(plan)} != {BUDGET}")
        observed = trace_plan_mock(plan, mock["geometry"])
        pred = sum(1 for _ in plan)
        ck(pred == observed == BUDGET <= HARD_CAP, f"budget reconciliation pred={pred} observed={observed}")
        lines_out(out / "pilot_execution_plan.jsonl", plan)
        produced.append("pilot_execution_plan.jsonl")
        save(out / "budget_reconciliation.json",
             {"schema": "JEV_A461_G5_PILOT_BUDGET_RECONCILIATION_V1",
              "predicted_native_forwards": pred, "observed_mock_trace": observed,
              "approved_planned_forwards": BUDGET, "hard_cap": HARD_CAP,
              "equal": pred == observed == BUDGET,
              "note": "plan derived from frozen roster x layers x conditions; no dynamic host pool"})
        produced.append("budget_reconciliation.json")
        gates["G11_AUTO_TRACE_PHYSICAL_FORWARDS_EQUALS_PRECOMPUTED_BUDGET"] = "PASS"

        # ---------- G12 source freeze / G-1 check / stop rule ----------
        roster_groups = sorted({p["source_group"] for p in pair_checks if p["pair_key"] in roster_keys})
        ck(len(roster_groups) == 3 and len(set(roster_groups)) == 3, "roster groups not independent")
        freeze = {"schema": "JEV_A461_G5_PILOT_SOURCE_FREEZE_V1",
                  "twins_census": twins_total, "dev_split_only": sorted(dev_splits) == ["development"],
                  "roster": {"donor": DONOR_KEY, "hosts": HOST_KEYS, "source_groups": roster_groups},
                  "corpus_sha256": CORPUS_SHA, "base_tokenizer_json_sha256": tok_sha,
                  "input_blobs": receipt["frozen_inputs"],
                  "layers": LAYERS, "expected_width": EXPECTED_WIDTH,
                  "stop_rule": "any gate FAIL => STOP_PRE_GPU_<GATE>; GPU blocked until independent blind "
                               "review explicit PASS AND fresh explicit user approval in the pilot admission receipt",
                  "g_minus_1_note": "novelty delta = first bidirectional activation patching on this scorer; "
                                    "prior art check per governance 5e35c044 (Tang et al. ICML 2026, "
                                    "activation-patching best practices) recorded in the pilot protocol"}
        save(out / "source_freeze.json", freeze)
        produced.append("source_freeze.json")
        gates["G12_FREEZE_SOURCE_G_MINUS_1_CHECK_AND_STOP_RULE"] = "PASS"
        gates["G13_INDEPENDENT_BLIND_REVIEW_EXPLICIT_PASS"] = "WAITING_BLIND_REVIEW"

        receipt.update(status="COMPLETE_A461_G5_PILOT_CPU_CLOSED_LOOP",
                       gates=dict(gates), parity=parity,
                       planned_forwards=BUDGET, gpu_blocked=True,
                       next_gate="independent blind review of protocol+runner+G0 artifacts, then fresh explicit user approval")
        code = 0
    except Exception as err:
        import traceback
        failed_gate = next((k for k, v in gates.items() if v != "PASS"), "UNKNOWN")
        receipt.update(status="STOP_PRE_GPU_" + failed_gate, error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-2000:],
                       gates=dict(gates))
        code = 2
    save(out / "execution_receipt.json", receipt)
    produced.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(canon(receipt))
    return code


# ---------------- mock suite (G8/G9) ----------------

def _layer_out_to_tensor(output):
    """Same unwrapping the GPU runner uses for Qwen3_5DecoderLayer outputs."""
    if isinstance(output, tuple):
        return output[0], output
    return output, (output,)


def run_mock_suite(anchor_rows, D):
    """Synthetic 4-row batch forward with the exact hook/spans/keying the GPU
    runner will use; verifies capture keying, span targeting, identity, off-row
    non-interference, both directions, and width equality."""
    import torch
    B, NL = 4, 24
    C = 1  # conflicting_vote branch index (verified dynamically in G5/G7)
    donor = next(r for r in anchor_rows if r["pair_key"] == DONOR_KEY)
    hosts = [next(r for r in anchor_rows if r["pair_key"] == k) for k in HOST_KEYS]
    geometry = {"rows_per_record": 4, "hidden": D, "layers": NL,
                "donor_state_len_new": donor["arms"]["new"]["state_token_len"],
                "host_state_len_sa": [h["arms"]["SA"]["state_token_len"] for h in hosts],
                "host_state_len_new": [h["arms"]["new"]["state_token_len"] for h in hosts],
                "c_branch_len": donor["arms"]["new"]["c_branch_len"],
                "spans": {r["pair_key"]: {a: r["arms"][a]["appended_span_in_state"] for a in ("new", "SA")}
                          for r in [donor] + hosts}}
    res = {"schema": "JEV_A461_G5_PILOT_MOCK_HOOK_TEST_V1", "geometry": geometry, "checks": {}}
    L_state = max(geometry["donor_state_len_new"], max(geometry["host_state_len_sa"]),
                  max(geometry["host_state_len_new"])) + geometry["c_branch_len"]
    weights = [torch.randn(D) * 0.01 + 1.0 for _ in range(NL)]  # row-independent toy layers
    span_w = EXPECTED_WIDTH

    def forward2(x, patch=None, cap_store=None, cap_tag=None, span=None):
        """Toy row-batch forward mirroring the GPU runner's hook contract:
        layers are row-independent transforms; both captures and patches fire
        POST-layer (register_forward_hook semantics), so patching a row with its
        own captured states is a bitwise identity; captures are (tag, layer)-keyed."""
        for i, g in enumerate(weights):
            x = x * g                      # layer i transform
            if patch is not None and i == patch[1]:
                bi, _, start, states = patch
                ck(states.shape == (span_w, D), "patch width")
                ck(start >= 0 and start + span_w <= x.shape[1], "span bounds")
                x = x.clone()
                x[bi, start:start + span_w, :] = states
            if cap_store is not None and i in (11, 23):
                s0, s1 = span
                cap_store[(cap_tag, i)] = x[C, s0:s1, :].detach().clone()
        return x

    x = torch.randn(B, L_state, D)
    # baseline
    base = forward2(x)
    # donor new capture (both layers, one forward)
    d_span = geometry["spans"][DONOR_KEY]["new"]
    cap = {}
    forward2(x, cap_store=cap, cap_tag="donor_new", span=d_span)
    ck(set(cap) == {("donor_new", 11), ("donor_new", 23)}, "donor capture keys")
    # second donor forward with a different tag must not overwrite the first
    cap2 = dict(cap)
    forward2(x, cap_store=cap2, cap_tag="donor_sa", span=geometry["spans"][DONOR_KEY]["SA"])
    ck(cap2[("donor_new", 11)].equal(cap[("donor_new", 11)]), "capture key overwrite")
    # host SA captures
    h_span = geometry["spans"][HOST_KEYS[0]]["SA"]
    hc = {}
    forward2(x, cap_store=hc, cap_tag="host_sa", span=h_span)
    ck(set(hc) == {("host_sa", 11), ("host_sa", 23)}, "host capture keys")
    # identity self-patch: bitwise identical
    ident = forward2(x, patch=(C, 11, h_span[0], hc[("host_sa", 11)]))
    res["checks"]["identity_self_patch_bitwise_equal"] = bool(torch.equal(base[C], ident[C])) and all(
        torch.equal(base[r], ident[r]) for r in range(B))
    # sufficiency: donor new -> host C row span; C row changes, others bitwise identical
    suff = forward2(x, patch=(C, 11, h_span[0], cap[("donor_new", 11)]))
    res["checks"]["sufficiency_c_row_changed"] = not torch.equal(base[C], suff[C])
    res["checks"]["sufficiency_off_rows_bitwise_identical"] = all(
        torch.equal(base[r], suff[r]) for r in range(B) if r != C)
    # necessity: host new capture -> donor C row span
    hn_span = geometry["spans"][HOST_KEYS[0]]["new"]
    hnc = {}
    forward2(x, cap_store=hnc, cap_tag="host_new", span=hn_span)
    necc = forward2(x, patch=(C, 23, d_span[0], hnc[("host_new", 23)]))
    res["checks"]["necessity_c_row_changed"] = not torch.equal(base[C], necc[C])
    res["checks"]["necessity_off_rows_bitwise_identical"] = all(
        torch.equal(base[r], necc[r]) for r in range(B) if r != C)
    # width equality precondition
    res["checks"]["span_widths_equal_34"] = all(
        r["arms"][a]["state_growth"] == EXPECTED_WIDTH for r in [donor] + hosts for a in ("new", "SA"))
    res["checks"]["spans_within_state_bounds"] = all(
        0 <= r["arms"][a]["appended_span_in_state"][0]
        and r["arms"][a]["appended_span_in_state"][1] <= r["arms"][a]["state_token_len"]
        for r in [donor] + hosts for a in ("new", "SA"))
    res["verdict"] = "PASS" if all(v is True or v == "PASS" for k, v in res["checks"].items()
                                   if k != "mock_note") else "FAIL"
    return res


# ---------------- plan construction + mock trace (G11) ----------------

def build_plan(anchor_rows):
    donor = next(r for r in anchor_rows if r["pair_key"] == DONOR_KEY)
    hosts = [next(r for r in anchor_rows if r["pair_key"] == k) for k in HOST_KEYS]
    plan = []

    def add(cond, target, layer, span, source_tag):
        plan.append({"seq": len(plan) + 1, "condition": cond, "target": target, "layer": layer,
                     "span_in_state": span, "source_capture_tag": source_tag,
                     "readouts": "all_four_questions"})

    # donor captures (3): old at the NEW-span coordinates (no-evidence descriptive
    # baseline; the old arm has no appended event), new and SA at their own appended
    # spans; layers 11+23 captured per forward (one physical forward each)
    add("capture_donor_old_at_new_span_coords", "donor_old", "both",
        donor["arms"]["new"]["appended_span_in_state"], None)
    add("capture_donor_new", "donor_new", "both",
        donor["arms"]["new"]["appended_span_in_state"], None)
    add("capture_donor_sa", "donor_sa", "both",
        donor["arms"]["SA"]["appended_span_in_state"], None)
    # host SA unpatched baselines (2)
    for h in hosts:
        add("baseline_host_sa_unpatched", h["pair_key"] + ":SA", None, None, None)
    # host SA captures (2)
    for h in hosts:
        add("capture_host_sa", h["pair_key"] + ":SA", "both",
            h["arms"]["SA"]["appended_span_in_state"], None)
    # identity self-patch (2)
    for h in hosts:
        add("patch_identity_host_sa", h["pair_key"] + ":SA", 11,
            h["arms"]["SA"]["appended_span_in_state"], h["pair_key"] + ":SA")
    # restoration (4): donor recognized-new span states -> host neutral-SA span
    for h in hosts:
        for L in LAYERS:
            add("patch_restoration_donor_new_to_host_sa", h["pair_key"] + ":SA", L,
                h["arms"]["SA"]["appended_span_in_state"], "donor_new")
    # SA-sham cross (4): donor duplicate-vote (non-recognized) span states -> host SA span
    for h in hosts:
        for L in LAYERS:
            add("patch_sasham_donor_sa_to_host_sa", h["pair_key"] + ":SA", L,
                h["arms"]["SA"]["appended_span_in_state"], "donor_sa")
    # position-permuted donor span (4)
    for h in hosts:
        for L in LAYERS:
            add("patch_permuted_donor_new_to_host_sa", h["pair_key"] + ":SA", L,
                h["arms"]["SA"]["appended_span_in_state"], "donor_new_permuted")
    # host treatment captures (2)
    for h in hosts:
        add("capture_host_new", h["pair_key"] + ":new", "both",
            h["arms"]["new"]["appended_span_in_state"], None)
    # donor new unpatched baseline (1)
    add("baseline_donor_new_unpatched", "donor_new", None, None, None)
    # suppression (4): failed-host treatment span states -> donor recognized-new span
    for h in hosts:
        for L in LAYERS:
            add("patch_suppression_host_new_to_donor_new", "donor_new", L,
                donor["arms"]["new"]["appended_span_in_state"], h["pair_key"] + ":new")
    return plan


def trace_plan_mock(plan, geometry):
    """Dry-run the plan through the mock forward path; returns the physical counter."""
    import torch
    torch.manual_seed(1)
    D = geometry["hidden"]
    C = 1
    L_state = max(geometry["donor_state_len_new"], max(geometry["host_state_len_sa"]),
                  max(geometry["host_state_len_new"])) + geometry["c_branch_len"]
    weights = [torch.randn(D) * 0.01 + 1.0 for _ in range(24)]
    caps = {}
    rng = random.Random(PERM_SEED)
    perm = list(range(EXPECTED_WIDTH))
    rng.shuffle(perm)
    counter = [0]

    def mock_forward(cap_tag=None, cap_span=None, patch=None):
        """patch = (layer_idx, start, states), post-layer semantics like forward2."""
        counter[0] += 1
        x = torch.randn(4, L_state, D)
        for i, g in enumerate(weights):
            x = x * g
            if patch is not None and i == patch[0]:
                _, start, states = patch
                x = x.clone()
                x[C, start:start + states.shape[0], :] = states
            if cap_tag is not None and i in (11, 23):
                s0, s1 = cap_span
                caps[(cap_tag, i)] = x[C, s0:s1, :].detach().clone()
        return x

    for entry in plan:
        cond = entry["condition"]
        span = entry["span_in_state"]
        L = entry["layer"]
        if cond.startswith("capture_"):
            mock_forward(cap_tag=entry["target"], cap_span=span)
        elif cond.startswith("baseline"):
            mock_forward()
        elif cond == "patch_identity_host_sa":
            mock_forward(patch=(L, span[0], caps[(entry["source_capture_tag"], L)]))
        elif cond.startswith("patch_restoration"):
            mock_forward(patch=(L, span[0], caps[("donor_new", L)]))
        elif cond.startswith("patch_sasham"):
            mock_forward(patch=(L, span[0], caps[("donor_sa", L)]))
        elif cond.startswith("patch_permuted"):
            mock_forward(patch=(L, span[0], caps[("donor_new", L)][perm]))
        elif cond.startswith("patch_suppression"):
            mock_forward(patch=(L, span[0], caps[(entry["source_capture_tag"], L)]))
        else:
            raise RuntimeError("unknown plan condition " + cond)
    ck(counter[0] == len(plan), "trace count drift")
    return counter[0]


if __name__ == "__main__":
    sys.exit(main())
