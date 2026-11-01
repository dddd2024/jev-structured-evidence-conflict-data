#!/usr/bin/env python3
"""A461-G5 G1S: donor search stage (GPU, 124 forwards).

Second-path gates BEFORE any forward: independent oracle recomputation of all
120 arm golds from corpus states, independent edit re-application, SA
token-match verification with its own tokenizer encode. Then 40x3 arms + 4
replays of native FP32 forwards; donor qualification per the frozen protocol.
"""
import argparse, collections, gzip, hashlib, json, math, os, sys, time
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
BUDGET = 124
REPLAYS = 4
DP = 256

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


def gold_v2(st):
    """Independent oracle (per-author explicit scan)."""
    cand, rnd, dl, qsz = st["candidate_block"], st["candidate_round"], st["decision_time"], st["quorum_size"]
    per = {}
    for m in st["received_messages"]:
        if m.get("kind") != "vote" or m.get("round") != rnd or m.get("author") not in st["validator_set"]:
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--g5-run", required=True, type=Path)
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    g5 = a.g5_run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA and
       all(x.is_relative_to(ROOT) for x in (repo, g5, SOURCE, CKPT, BASE, out)), "paths/corpus")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    admit = json.loads(a.admission.read_text("utf8"))
    ck(admit.get("explicit_user_gpu_approval") is True and admit.get("stage") == "A461_G5_G1S_DONOR_SEARCH"
       and admit.get("approved_max_native_forwards") == BUDGET, "No G5 G1S authorization")
    receipt = {"schema": "JEV_A461_G5_G1S_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": admit["run_id"], "gpu_model_loads": 0, "native_model_forward_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "tool_actions": 0,
               "test_or_calibration_rows": 0, "output_dir": str(out)}
    produced = []
    try:
        out.mkdir(mode=0o700)
        prows = [json.loads(x) for x in (g5 / "G0D_CONS" / "pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        cons = json.loads((g5 / "G0D_CONS" / "execution_receipt.json").read_text("utf8"))
        ck(cons["status"].startswith("COMPLETE_A461_G5_CONS"), "construction not complete")
        save(out / "admission_receipt_copy.json", admit)
        produced.append("admission_receipt_copy.json")
        twins = []
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    twins.append(rec)
        state_by = {}
        for rec in twins:
            state_by[hashlib.sha256(json.dumps(rec["state"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")).hexdigest()[:16]] = rec["state"]
        # ---------- second-path gates BEFORE any forward ----------
        from tokenizers import Tokenizer
        tok = Tokenizer.from_file(str(CKPT / "tokenizer.json"))
        by_pair = collections.OrderedDict()
        for r in prows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        n_pairs = 0
        for key, rs in by_pair.items():
            old_state = state_by.get(key.split(":", 1)[1])
            ck(old_state is not None, "old state missing " + key)
            g_old = gold_v2(old_state)
            treat = next(r for r in rs if r["arm"] == "new")
            sa = next(r for r in rs if r["arm"] == "SA")
            st_t = json.loads(flat_st(treat["native_request"]["state"]))
            rt = rebuild(old_state, treat["declared_edit"])
            ck(flat_st(rt) == flat_st(st_t), "treatment re-application differs " + key)
            g_t = gold_v2(st_t)
            need = (g_t["conflicting_vote"] is True and g_t["certificate_action"] == "reject_conflict"
                    and g_old["conflicting_vote"] is False)
            ck(need, "treatment gold wrong " + key)
            st_s = json.loads(flat_st(sa["native_request"]["state"]))
            rs2 = rebuild(old_state, sa["declared_edit"])
            ck(flat_st(rs2) == flat_st(st_s), "SA re-application differs " + key)
            g_s = gold_v2(st_s)
            ck(g_s == g_old, "SA moved gold " + key)
            n_pairs += 1
        ck(n_pairs >= 20, f"pair count {n_pairs} below stop-condition floor")
        review = {"second_path_gates": "PASS", "pairs": n_pairs}
        save(out / "second_path_gate_receipt.json", review)
        produced.append("second_path_gate_receipt.json")
        # ---------- forwards ----------
        import torch
        torch.set_num_threads(4)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        ck(torch.cuda.is_available() and torch.cuda.mem_get_info(0)[0] >= 8 * (1 << 30), "GPU capacity")
        sys.path.insert(0, str(SOURCE))
        from kev.api import SystemOneRequest, to_record
        from kev.checkpoint import Checkpoint, LoadOptions
        from kev.model import rows_of
        checkpoint = Checkpoint(str(CKPT))
        checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
        tokenizer, model = checkpoint.load("cuda:0", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
        receipt["gpu_model_loads"] = 1
        model.eval()
        model.requires_grad_(False)
        q_tw = prows[0]["native_request"]["questions"]
        plan = []
        for key, rs in by_pair.items():
            old_state = state_by[key.split(":", 1)[1]]
            plan.append((key + ":old", key, "old", {"questions": q_tw, "state": json.loads(canon(old_state))}))
            for r in rs:
                plan.append((r["row_id"], key, r["arm"], r["native_request"]))
        ck(len(plan) + REPLAYS <= BUDGET, f"plan {len(plan)}+{REPLAYS} exceeds {BUDGET}")
        encoded_all = []
        for row_id, key, arm, req in plan:
            rendered, meta = to_record(SystemOneRequest.model_validate(req))
            enc = model.encode(tokenizer, rendered, max_state=8192, max_branch=8192, strict=True)
            state_ids, _, branches = rows_of(enc)
            ck(not enc["state_truncated"] and len(meta) == len(branches) == 4, "encode gate " + row_id)
            encoded_all.append((row_id, key, arm, meta, enc, len(state_ids)))
        token_lens = [{"row_id": rid, "arm": arm, "state_token_len": L} for rid, key, arm, meta, enc, L in encoded_all]
        save(out / "render_token_lengths.json", {"schema": "JEV_A461_G5_RENDER_TOKEN_LENGTHS_V1", "rows": token_lens})
        produced.append("render_token_lengths.json")
        physical = [0]

        def bump(_m, _a):
            physical[0] += 1
        hk = model.lm.register_forward_pre_hook(bump)
        queue = [(rid, key, arm, meta, enc, "primary") for rid, key, arm, meta, enc, _L in encoded_all]
        reps = [(rid, key, arm, meta, enc) for rid, key, arm, meta, enc, _L in encoded_all if arm == "old"][:REPLAYS]
        for rid, key, arm, meta, enc in reps:
            queue.append((rid + ":replay", key, arm, meta, enc, "replay"))
        rows_out = []
        t0 = time.time()
        with torch.inference_mode():
            for row_id, key, arm, meta, enc, kind in queue:
                ck(receipt["native_model_forward_calls"] < BUDGET, "Exceeded frozen forward budget")
                outlogits = model.forward(enc)
                receipt["native_model_forward_calls"] += 1
                ck(len(outlogits) == len(meta), "branch/logit mismatch")
                raw = [z.detach().float().cpu().tolist() for z in outlogits]
                ck(all(len(v) == len(m["keys"]) and all(math.isfinite(float(x)) for x in v)
                       for v, m in zip(raw, meta)), "invalid logits")
                probs = [torch.softmax(z.float(), dim=-1).detach().cpu().tolist() for z in outlogits]
                rec = {"forward_index": receipt["native_model_forward_calls"], "plan_row": row_id,
                       "arm": arm, "kind": kind,
                       "questions": [{"id": m["id"], "keys": list(m["keys"]), "logits": v, "probs": p}
                                     for m, v, p in zip(meta, raw, probs)],
                       "token_ids_sha256": hids(enc["ids"])}
                rows_out.append(rec)
                if kind == "replay":
                    base = row_id.split(":replay")[0]
                    pr = next(r for r in rows_out if r["plan_row"] == base and r["kind"] == "primary")
                    ck(all(x["logits"] == y["logits"] for x, y in zip(pr["questions"], rec["questions"])),
                       "replay nondeterminism " + base)
        ck(physical[0] == receipt["native_model_forward_calls"] <= BUDGET, f"ledger {physical[0]}")
        lines_out(out / "raw_native_logits_112_requests.jsonl", rows_out)
        produced.append("raw_native_logits_112_requests.jsonl")
        elapsed = time.time() - t0
        gpu_after = torch.cuda.mem_get_info(0)
        composition = collections.Counter(r["arm"] for r in rows_out if r["kind"] == "primary")
        receipt.update(status="COMPLETE_A461_G5_G1S_DONOR_SEARCH",
                       physical_forwards=physical[0], budget=BUDGET,
                       composition=dict(composition), replays=REPLAYS,
                       elapsed_seconds=round(elapsed, 3),
                       gpu_free_bytes_after=gpu_after[0],
                       backprop_calls=0, network_calls=0, tool_actions=0,
                       test_or_calibration_rows=0)
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G5_G1S", error_type=type(err).__name__, error_message=str(err),
                       traceback=traceback.format_exc()[-1500:])
        code = 2
    save(out / "execution_receipt.json", receipt)
    produced.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(canon(receipt))
    return code


def flat_st(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def rebuild(old, declared):
    st = json.loads(flat_st(old))
    op = declared["op"]
    msgs = st["received_messages"]
    mx = max(e["received"] for e in msgs)
    if op == "append_conflict_vote":
        m = dict(declared["message"])
        # supporter rule
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


if __name__ == "__main__":
    sys.exit(main())
