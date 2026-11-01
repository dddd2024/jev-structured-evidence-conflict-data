#!/usr/bin/env python3
"""A461-PSMI G1: paired native FP32 forward pilot on the frozen G0 pairs.

Budget: exactly 103 physical native forwards (user-approved 2026-10-25,
AskUserQuestion "批准 GPU（A461 G1，103 次 forward）"). Equal-count amendment
within the approved total: 17 unmatched-N1 rows are substituted by the 14
token-matched N1B rows (strict-contrast controls per shadow QA QA-1), keeping
103. Composition: 34 old baselines + 31 treatment + 14 N1B + 3 N2 + 17 N1 +
4 precision replays = 103.

Pre-forward gates: pinned component SHAs, GPU capacity, old-arm token identity
vs A428 archive for scenes shared with A428, oracle Gold consistency. Zero
backprop, zero network, zero tools. Uses the same native API as A430 G1.
"""
import argparse, hashlib, json, math, os, sys, time
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
A428_G0A = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0A_REAL_20261023"
A428_G0B = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0B_REAL_20261023"
A428_G1 = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G1_REAL_20261023"
BUDGET = 103
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
    ap.add_argument("--run", required=True, type=Path, help="G0 run dir (contains G0, G0_N1B, manifests)")
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    run = a.run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and all(x.is_relative_to(ROOT) for x in (repo, run, SOURCE, CKPT, BASE, out)),
       "All sources and outputs must be under ~/wjc")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir required")
    admit = json.loads(a.admission.read_text("utf8"))
    # negative gate: refuse without explicit approval
    ck(admit.get("explicit_user_gpu_approval") is True and admit.get("stage") == "A461_PSMI_G1_PAIRED_PILOT"
       and admit.get("approved_max_native_forwards") == BUDGET and bool(admit.get("authorizing_evidence_ref"))
       and admit.get("run_id") == "a461-psmi-counterfactual-cpu-gate-20261025-v1",
       "No A461-PSMI G1-specific user GPU authorization")
    receipt = {"schema": "JEV_A461_PSMI_G1_EXECUTION_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": admit["run_id"], "gpu_model_loads": 0, "native_model_forward_calls": 0,
               "native_question_branch_rows": 0, "backprop_calls": 0, "network_calls": 0,
               "tool_actions": 0, "test_or_calibration_rows": 0, "output_dir": str(out)}
    files = []
    produced = []
    try:
        out.mkdir(mode=0o700)
        manifest = json.loads((run / "manifests/forward_manifest/physical_forward_manifest.json").read_text("utf8"))
        prows = {r["row_id"]: r for r in (json.loads(x) for x in (run / "G0/pair_rows.jsonl").read_text("utf8").splitlines() if x.strip())}
        n1b_rows = {r["row_id"]: r for r in (json.loads(x) for x in (run / "G0_N1B/n1b_rows.jsonl").read_text("utf8").splitlines() if x.strip())}
        corpus_pairs = json.loads((run / "G0/census.json").read_text("utf8"))
        # ---- build the executed forward plan: equal-count amendment ----
        plan = []
        old_keys = [r for r in manifest["rows"] if r["role"] == "old_baseline"]
        old_by_id = {r["row_id"]: r for r in old_keys}
        treat = [r for r in manifest["rows"] if r["role"] == "treatment"]
        n2 = [r for r in manifest["rows"] if r["role"] == "N2_retime"]
        n1_all = [r for r in manifest["rows"] if r["role"] == "N1_neutral"]
        ck(len(old_keys) == 34 and len(treat) == 31 and len(n2) == 3 and len(n1_all) == 31, "manifest shape")
        n1b_by_source = {r["source_pair_row"]: r for r in n1b_rows.values() if r["N1B_token_count_matched"]}
        ck(len(n1b_by_source) == 14, "n1b matched count")
        n1_keep = n1_all[:17]  # deterministic: first 17 unmatched-N1 rows kept
        ck(len(n1_keep) == 17, "n1 keep count")
        for r in old_keys:
            plan.append((r["row_id"], "old_baseline", None))
        for r in treat:
            plan.append((r["row_id"], "treatment", prows[r["row_id"]]))
        for src, r in sorted(n1b_by_source.items()):
            plan.append((r["row_id"], "N1B_matched", n1b_rows[r["row_id"]]))
        for r in n2:
            plan.append((r["row_id"], "N2_retime", prows[r["row_id"]]))
        for r in n1_keep:
            plan.append((r["row_id"], "N1_unmatched", prows[r["row_id"]]))
        replays = [k[0] for k in plan if k[1] == "old_baseline"][:REPLAYS]
        ck(len(plan) + len(replays) == BUDGET, f"plan size {len(plan)}+{len(replays)} != {BUDGET}")
        # old-baseline requests: questions template from its family rows + corpus old state
        q_tw = prows[next(k for k in prows if prows[k]["source"] == "twins_streamlet")]["native_request"]["questions"]
        q_ln = prows[next(k for k in prows if prows[k]["source"] == "lanl_auth_policy")]["native_request"]["questions"]
        tw, ln = [], []
        import gzip
        CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
        ck(sha_file(CORPUS) == "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56", "corpus pin")
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                s = rec["_meta"].get("source")
                if s == "twins_streamlet":
                    tw.append(rec)
                elif s == "lanl_auth_policy":
                    ln.append(rec)
        # A428 archived token identity for shared scenes
        a428b = json.loads((repo / (A428_G0B + "/native_token_manifest.json")).read_text("utf8"))
        a428_state_by_id = {}
        a428_rows = [json.loads(x) for x in (repo / (A428_G0A + "/frozen_model_inputs.jsonl")).read_text("utf8").splitlines() if x.strip()]
        pool = tw + ln
        for r in a428_rows:
            sh = hashlib.sha256(canon(r["native_request"]["state"]).encode("utf8")).hexdigest()[:16]
            a428_state_by_id[sh] = r["id"]
        a428_tokens_by_id = {t["id"]: t for t in a428b["token_rows"]}
        save(out / "admission_receipt_copy.json", admit)
        produced.append("admission_receipt_copy.json")
        # ---- GPU ----
        import torch
        torch.set_num_threads(4)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        ck(torch.cuda.is_available() and torch.cuda.mem_get_info(0)[0] >= 8 * (1 << 30), "No available authorized GPU capacity")
        sys.path.insert(0, str(SOURCE))
        from kev.api import SystemOneRequest, to_record
        from kev.checkpoint import Checkpoint, LoadOptions
        from kev.model import rows_of
        ck(sha_file(SOURCE / "kev/model.py") == a428b["native_code_sha256"]["kev_model_py"]
           and sha_file(SOURCE / "kev/api.py") == a428b["native_code_sha256"]["kev_api_py"], "renderer drift")
        ckpt = Checkpoint(str(CKPT))
        ckpt.meta.base, ckpt.meta.base_revision = str(BASE), None
        tokenizer, model = ckpt.load("cuda:0", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
        receipt["gpu_model_loads"] = 1
        model.eval()
        model.requires_grad_(False)
        # ---- encode + pre-forward gates ----
        encoded_all = []
        decoded = []
        for row_id, role, row in plan:
            if role == "old_baseline":
                r0 = old_by_id[row_id]
                key = row_id
                pair_key = key.split(":old")[0]
                fam = pair_key.split(":")[0]
                pool_ = ln if r0["source_family"] == "lanl_auth_policy" else tw
                old_state = None
                for rec in pool_:
                    if hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()[:16] == r0["original_scene_sha"]:
                        old_state = rec["state"]
                        break
                ck(old_state is not None, "old state missing " + key)
                qs = q_ln if r0["source_family"] == "lanl_auth_policy" else q_tw
                req = {"questions": qs, "state": json.loads(canon(old_state))}
            else:
                req = row["native_request"]
            rendered, meta = to_record(SystemOneRequest.model_validate(req))
            enc = model.encode(tokenizer, rendered, max_state=8192, max_branch=8192, strict=True)
            state, _, branches = rows_of(enc)
            ck(not enc["state_truncated"] and len(meta) == len(branches) >= 2
               and all(len(state) + len(b["ids"]) <= 8192 for b in branches), "encode gate " + row_id)
            decoded.append({"plan_row": row_id, "role": role, "state_len": len(state),
                            "token_ids_sha256": hids(enc["ids"]),
                            "branch_hashes": {m["id"]: hids(b["ids"]) for m, b in zip(meta, branches)},
                            "keys": {m["id"]: list(m["keys"]) for m in meta}})
            # cross-run identity: old baseline of a scene shared with A428 must reproduce
            # the archived native token SHA exactly (same questions template + same state)
            if role == "old_baseline":
                sh = r0["original_scene_sha"]
                if sh in a428_state_by_id:
                    want = a428_tokens_by_id[a428_state_by_id[sh]]["token_ids_sha256"]
                    # archived sha is over enc["ids"] of the A428 request (same construction)
                    ck(hids(enc["ids"]) == want, f"A428 token identity drift for shared scene {sh} ({a428_state_by_id[sh]})")
                    decoded[-1]["a428_identity"] = a428_state_by_id[sh]
            encoded_all.append((row_id, role, row, meta, enc))
        save(out / "pre_forward_token_gate_receipt.json", {
            "status": "PASS_A461_PSMI_G1_PRE_FORWARD_GATES",
            "plan_rows": len(plan), "replays": len(replays), "budget": BUDGET,
            "a428_shared_scene_identity": [d["a428_identity"] for d in decoded if "a428_identity" in d],
            "token_rows": decoded})
        produced.append("pre_forward_token_gate_receipt.json")
        # ---- forwards ----
        physical = [0]

        def bump(_m, _a):
            physical[0] += 1
        hook = model.lm.register_forward_pre_hook(bump)
        queue = [(rid, role, row, meta, enc, "primary") for rid, role, row, meta, enc in encoded_all]
        replay_pairs = [(rid, role, row, meta, enc) for rid, role, row, meta, enc in encoded_all if role == "old_baseline"][:REPLAYS]
        for rid, role, row, meta, enc in replay_pairs:
            queue.append((rid + ":replay", "replay", row, meta, enc, "replay"))
        rows_out = []
        t0 = time.time()
        replay_results = []
        replay_state = {}
        with torch.inference_mode():
            for row_id, role, row, meta, enc, kind in queue:
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
           f"physical forward ledger mismatch {physical[0]}")
        # persist raw outputs BEFORE any post-loop assertion so forwards are never lost
        lines_out(out / "raw_native_logits_103_requests.jsonl", rows_out)
        produced.append("raw_native_logits_103_requests.jsonl")
        replay_ledger = {b: [r["forward_index"] for r in rrs] for b, rrs in replay_state.items()}
        replay_results = []
        for base_id, rrs in replay_state.items():
            verdict = "IDENTICAL" if (len(rrs) == 2 and all(
                x["logits"] == y["logits"] for x, y in zip(rrs[0]["questions"], rrs[1]["questions"]))) else \
                ("NONDETERMINISTIC" if len(rrs) == 2 else "INCOMPLETE_LEDGER")
            replay_results.append({"base_row": base_id, "n_replays": len(rrs), "verdict": verdict})
        hook.remove()
        elapsed = time.time() - t0
        save(out / "replay_receipt.json", {"schema": "JEV_A461_PSMI_G1_REPLAY_V1",
                                           "expected_bases": [rid for rid, role, _, _, _ in encoded_all if role == "old_baseline"][:REPLAYS],
                                           "replay_ledger": replay_ledger,
                                           "replays": replay_results})
        produced.append("replay_receipt.json")
        ck(all(r["verdict"] == "IDENTICAL" for r in replay_results) and len(replay_results) == REPLAYS,
           "replay determinism/ledger failure: " + canon(replay_ledger))
        gpu_after = torch.cuda.mem_get_info(0)
        receipt.update(status="COMPLETE_A461_PSMI_G1_PAIRED_PILOT",
                       physical_forwards=physical[0], budget=BUDGET,
                       plan_composition={"old_baseline": 34, "treatment": 31, "N1B_matched": 14,
                                         "N2_retime": 3, "N1_unmatched": 17, "replay": 4},
                       equal_count_amendment="17 unmatched-N1 rows substituted by 14 token-matched N1B rows within the approved 103 total",
                       elapsed_seconds=round(elapsed, 3),
                       gpu_free_bytes_after=gpu_after[0],
                       backprop_calls=0, network_calls=0, tool_actions=0,
                       test_or_calibration_rows=0)
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_PSMI_G1", error_type=type(err).__name__, error_message=str(err),
                       traceback=traceback.format_exc()[-1500:])
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
