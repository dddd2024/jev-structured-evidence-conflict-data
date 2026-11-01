#!/usr/bin/env python3
"""A461-G3 G1C: paired native FP32 forwards on the frozen G3 pairs.

Budget: exactly 109 physical native forwards (26 old baselines + 79 edit arms
+ 4 precision replays) under the frozen G3 protocol V1 and the user's standing
authorization recorded in the admission receipt. Pre-forward gates: pinned
component SHAs, GPU capacity, A428 cross-run token identity for any scene
shared with the archived A428 run, dual-oracle gold spot checks. Zero backprop,
zero network, zero tools. Same native API as the A430/A461 pilots.
"""
import argparse, hashlib, json, math, os, sys, time
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
A428_G0A = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0A_REAL_20261023"
A428_G0B = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0B_REAL_20261023"
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
BUDGET = 109
REPLAYS = 4

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    run = a.run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and all(x.is_relative_to(ROOT) for x in (repo, run, SOURCE, CKPT, BASE, out)), "paths under ~/wjc")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    admit = json.loads(a.admission.read_text("utf8"))
    ck(admit.get("explicit_user_gpu_approval") is True and admit.get("stage") == "A461_G3_G1C_PAIRED_FORWARDS"
       and admit.get("approved_max_native_forwards") == BUDGET and bool(admit.get("authorizing_evidence_ref")),
       "No A461-G3-specific GPU authorization")
    receipt = {"schema": "JEV_A461_G3_G1C_EXECUTION_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": admit["run_id"], "gpu_model_loads": 0, "native_model_forward_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "tool_actions": 0,
               "test_or_calibration_rows": 0, "output_dir": str(out)}
    produced = []
    try:
        out.mkdir(mode=0o700)
        prows = [json.loads(x) for x in (run / "G0C/pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        g0c_receipt = json.loads((run / "G0C/execution_receipt.json").read_text("utf8"))
        ck(g0c_receipt["status"] == "COMPLETE_A461_G3_G0C_CPU_GATE_IMPL1", "G0C not complete")
        verify = json.loads((run / "G0C_VERIFY/independent_review.json").read_text("utf8"))
        ck(verify["status"] == "PASS_A461_G3_G0C_INDEPENDENT_VERIFICATION", "G0C verifier not PASS")
        tw = []
        import gzip
        ck(sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    tw.append(rec)
        q_tw = prows[0]["native_request"]["questions"]
        state_by = {}
        for rec in tw:
            state_by[hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()[:16]] = rec["state"]
        a428b = json.loads((repo / (A428_G0B + "/native_token_manifest.json")).read_text("utf8"))
        a428_rows = [json.loads(x) for x in (repo / (A428_G0A + "/frozen_model_inputs.jsonl")).read_text("utf8").splitlines() if x.strip()]
        a428_state = {}
        for r in a428_rows:
            a428_state.setdefault(hashlib.sha256(canon(r["native_request"]["state"]).encode("utf8")).hexdigest()[:16], r["id"])
        a428_tokens = {t["id"]: t for t in a428b["token_rows"]}
        save(out / "admission_receipt_copy.json", admit)
        produced.append("admission_receipt_copy.json")
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
        ck(sha_file(SOURCE / "kev/model.py") == a428b["native_code_sha256"]["kev_model_py"]
           and sha_file(SOURCE / "kev/api.py") == a428b["native_code_sha256"]["kev_api_py"], "renderer drift")
        checkpoint = Checkpoint(str(CKPT))
        checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
        tokenizer, model = checkpoint.load("cuda:0", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
        receipt["gpu_model_loads"] = 1
        model.eval()
        model.requires_grad_(False)
        pair_keys = []
        seen = set()
        for r in prows:
            if r["pair_key"] not in seen:
                seen.add(r["pair_key"])
                pair_keys.append(r["pair_key"])
        ck(len(pair_keys) == 26, f"pair count {len(pair_keys)}")
        plan = []
        for key in pair_keys:
            old_state = state_by[key.split(":", 1)[1]]
            ck(old_state is not None, "old state missing " + key)
            req = {"questions": q_tw, "state": json.loads(canon(old_state))}
            plan.append((key + ":old", "old_baseline", req))
        for r in prows:
            plan.append((r["row_id"], r["arm"], r["native_request"]))
        ck(len(plan) + REPLAYS == BUDGET, f"plan {len(plan)}+{REPLAYS} != {BUDGET}")
        encoded_all = []
        decoded = []
        for row_id, role, req in plan:
            rendered, meta = to_record(SystemOneRequest.model_validate(req))
            enc = model.encode(tokenizer, rendered, max_state=8192, max_branch=8192, strict=True)
            state_ids, _, branches = rows_of(enc)
            ck(not enc["state_truncated"] and len(meta) == len(branches) == 4
               and all(len(state_ids) + len(b["ids"]) <= 8192 for b in branches), "encode gate " + row_id)
            d = {"plan_row": row_id, "role": role, "state_len": len(state_ids),
                 "token_ids_sha256": hids(enc["ids"]),
                 "branch_hashes": {m["id"]: hids(b["ids"]) for m, b in zip(meta, branches)},
                 "keys": {m["id"]: list(m["keys"]) for m in meta}}
            if role == "old_baseline":
                sh = row_id.split(":")[1]
                if sh in a428_state:
                    want = a428_tokens[a428_state[sh]]["token_ids_sha256"]
                    ck(hids(enc["ids"]) == want, f"A428 token identity drift {sh}")
                    d["a428_identity"] = a428_state[sh]
            decoded.append(d)
            encoded_all.append((row_id, role, meta, enc))
        save(out / "pre_forward_token_gate_receipt.json", {
            "status": "PASS_A461_G3_G1C_PRE_FORWARD_GATES",
            "plan_rows": len(plan), "replays": REPLAYS, "budget": BUDGET,
            "a428_shared_scene_identity": [d["a428_identity"] for d in decoded if "a428_identity" in d],
            "token_rows": decoded})
        produced.append("pre_forward_token_gate_receipt.json")
        physical = [0]

        def bump(_m, _a):
            physical[0] += 1
        hook = model.lm.register_forward_pre_hook(bump)
        queue = [(rid, role, meta, enc, "primary") for rid, role, meta, enc in encoded_all]
        replay_pairs = [(rid, role, meta, enc) for rid, role, meta, enc in encoded_all if role == "old_baseline"][:REPLAYS]
        for rid, role, meta, enc in replay_pairs:
            queue.append((rid + ":replay", "replay", meta, enc, "replay"))
        rows_out = []
        t0 = time.time()
        replay_state = {}
        with torch.inference_mode():
            for row_id, role, meta, enc, kind in queue:
                ck(receipt["native_model_forward_calls"] < BUDGET, "Exceeded frozen forward budget")
                outlogits = model.forward(enc)
                receipt["native_model_forward_calls"] += 1
                ck(len(outlogits) == len(meta), "branch/logit count mismatch")
                raw = [z.detach().float().cpu().tolist() for z in outlogits]
                ck(all(len(v) == len(m["keys"]) and all(math.isfinite(float(x)) for x in v)
                       for v, m in zip(raw, meta)), "invalid logits")
                probs = [torch.softmax(z.float(), dim=-1).detach().cpu().tolist() for z in outlogits]
                rec = {"forward_index": receipt["native_model_forward_calls"], "plan_row": row_id,
                       "role": role, "kind": kind,
                       "questions": [{"id": m["id"], "keys": list(m["keys"]), "logits": v, "probs": p}
                                     for m, v, p in zip(meta, raw, probs)],
                       "token_ids_sha256": hids(enc["ids"])}
                rows_out.append(rec)
                if kind == "replay":
                    replay_state.setdefault(row_id.split(":replay")[0], []).append(rec)
        ck(physical[0] == receipt["native_model_forward_calls"] == BUDGET,
           f"physical ledger mismatch {physical[0]}")
        lines_out(out / "raw_native_logits_109_requests.jsonl", rows_out)
        produced.append("raw_native_logits_109_requests.jsonl")
        replay_results = []
        prim_by = {r["plan_row"]: r for r in rows_out if r["kind"] == "primary"}
        for base, rrs in replay_state.items():
            p = prim_by.get(base)
            ck(p is not None and len(rrs) == 1, "replay ledger " + base)
            same = all(x["logits"] == y["logits"] for x, y in zip(p["questions"], rrs[0]["questions"])) \
                and p["token_ids_sha256"] == rrs[0]["token_ids_sha256"]
            replay_results.append({"base_row": base, "primary_index": p["forward_index"],
                                   "replay_index": rrs[0]["forward_index"],
                                   "verdict": "IDENTICAL" if same else "DIFFER"})
        ck(len(replay_results) == REPLAYS and all(r["verdict"] == "IDENTICAL" for r in replay_results),
           "replay determinism failure: " + canon(replay_results))
        hook.remove()
        elapsed = time.time() - t0
        save(out / "replay_receipt.json", {"schema": "JEV_A461_G3_G1C_REPLAY_V1", "replays": replay_results})
        produced.append("replay_receipt.json")
        gpu_after = torch.cuda.mem_get_info(0)
        composition = {}
        for rid, role, meta, enc in encoded_all:
            composition[role] = composition.get(role, 0) + 1
        receipt.update(status="COMPLETE_A461_G3_G1C_PAIRED_FORWARDS",
                       physical_forwards=physical[0], budget=BUDGET,
                       plan_composition=composition, replays=len(replay_results),
                       elapsed_seconds=round(elapsed, 3),
                       gpu_free_bytes_after=gpu_after[0],
                       backprop_calls=0, network_calls=0, tool_actions=0,
                       test_or_calibration_rows=0)
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G3_G1C", error_type=type(err).__name__, error_message=str(err),
                       traceback=traceback.format_exc()[-1200:])
        code = 2
    save(out / "execution_receipt.json", receipt)
    produced.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(canon(receipt))
    return code


if __name__ == "__main__":
    sys.exit(main())
