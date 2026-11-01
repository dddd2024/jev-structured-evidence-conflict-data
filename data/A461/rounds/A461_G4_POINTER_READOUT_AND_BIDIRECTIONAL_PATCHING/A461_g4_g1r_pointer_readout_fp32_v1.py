#!/usr/bin/env python3
"""A461-G4 G1R: pointer readout decomposition on real native forwards (GPU).

For every one of the 26 frozen pairs, run old/new arms once each with a
forward hook on the PointerHead capturing (h_decide, h_opts) per question
branch; reconstruct every branch's native logits from the q/k algebra
(reconstruction gate: must match model.forward output to FP32 tolerance);
compute per-pair conflicting_vote margins and the exact three-term Delta_M
decomposition (query delta, candidate-key contrast delta, interaction).
56 physical forwards (52 arms + 4 replays) within the frozen budget.
Zero backprop, zero network, zero patching.
"""
import argparse, collections, hashlib, json, math, os, sys, time
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
G3DIR = "research/rounds/A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE"
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
BUDGET = 56
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--g3-run", required=True, type=Path)
    ap.add_argument("--g4-run", required=True, type=Path, help="G4 run dir containing G0ABC")
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    g3 = a.g3_run.expanduser().resolve(strict=True)
    g4 = a.g4_run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and all(x.is_relative_to(ROOT) for x in (repo, g3, g4, SOURCE, CKPT, BASE, out)), "paths")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    admit = json.loads(a.admission.read_text("utf8"))
    ck(admit.get("explicit_user_gpu_approval") is True and admit.get("stage") == "A461_G4_G1R_POINTER_READOUT_DECOMPOSITION"
       and admit.get("approved_max_native_forwards") == BUDGET and bool(admit.get("authorizing_evidence_ref")),
       "No A461-G4 G1R-specific GPU authorization")
    anchors = [json.loads(x) for x in (g4 / "G0ABC" / "g0c_anchor_map.jsonl").read_text("utf8").splitlines() if x.strip()]
    anchors_by = {r["pair_key"]: r for r in anchors}
    g0receipt = json.loads((g4 / "G0ABC" / "execution_receipt.json").read_text("utf8"))
    ck(g0receipt["status"] == "COMPLETE_A461_G4_G0ABC_CPU_ADMISSION", "G0 not complete")
    g0b = json.loads((g4 / "G0ABC" / "g0b_checkpoint_metadata.json").read_text("utf8"))
    T = float(g0b["temperature_value"])
    s = math.sqrt(DP) * T
    receipt = {"schema": "JEV_A461_G4_G1R_EXECUTION_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": admit["run_id"], "gpu_model_loads": 0, "native_model_forward_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "tool_actions": 0,
               "test_or_calibration_rows": 0, "output_dir": str(out)}
    produced = []
    try:
        out.mkdir(mode=0o700)
        prows = [json.loads(x) for x in (g3 / "G0C" / "pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        by_pair = collections.OrderedDict()
        for r in prows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        import gzip
        ck(sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
        old_states = {}
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    old_states[hashlib.sha256(json.dumps(rec["state"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")).hexdigest()[:16]] = rec["state"]
        q_tw = prows[0]["native_request"]["questions"]
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
        a428b = json.loads((repo / ("research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0B_REAL_20261023/native_token_manifest.json")).read_text("utf8"))
        ck(sha_file(SOURCE / "kev/model.py") == a428b["native_code_sha256"]["kev_model_py"], "renderer drift")
        checkpoint = Checkpoint(str(CKPT))
        checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
        tokenizer, model = checkpoint.load("cuda:0", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
        receipt["gpu_model_loads"] = 1
        model.eval()
        model.requires_grad_(False)
        # hook: capture (h_decide, h_opts) per PointerHead call
        cap = []
        def head_hook(module, args, kwargs=None):
            h_decide, h_opts = args[0], args[1]
            cap.append({"h_decide": h_decide.detach().float().cpu(), "h_opts": h_opts.detach().float().cpu()})
            return None
        hk = model.head.register_forward_pre_hook(head_hook, with_kwargs=False)
        plan = []
        for key, rs in by_pair.items():
            old_state = old_states.get(key.split(":", 1)[1])
            ck(old_state is not None, "old state missing " + key)
            treat = next(r for r in rs if r["arm"] == "new")
            plan.append((key + ":old", key, "old", {"questions": q_tw, "state": json.loads(canon(old_state))}))
            plan.append((key + ":new", key, "new", treat["native_request"]))
        ck(len(plan) + REPLAYS == BUDGET, f"plan {len(plan)} != {BUDGET - REPLAYS}")
        encoded_all = []
        decoded = []
        for row_id, key, arm, req in plan:
            rendered, meta = to_record(SystemOneRequest.model_validate(req))
            enc = model.encode(tokenizer, rendered, max_state=8192, max_branch=8192, strict=True)
            state_ids, _, branches = rows_of(enc)
            ck(not enc["state_truncated"] and len(meta) == len(branches) == 4, "encode gate " + row_id)
            decoded.append({"plan_row": row_id, "arm": arm, "branch_sha": [hids(b["ids"]) for b in branches],
                            "keys": {m["id"]: list(m["keys"]) for m in meta}})
            encoded_all.append((row_id, key, arm, meta, enc))
        save(out / "pre_forward_gate_receipt.json", {
            "status": "PASS_A461_G4_G1R_PRE_FORWARD_GATES",
            "plan_rows": len(plan), "replays": REPLAYS, "budget": BUDGET,
            "token_rows": decoded})
        produced.append("pre_forward_gate_receipt.json")
        physical = [0]
        cap.clear()

        def counting_bump(_m, _a):
            physical[0] += 1
        hk2 = model.lm.register_forward_pre_hook(counting_bump)
        rows_out = []
        cap_by_row = {}
        t0 = time.time()
        queue = [(rid, key, arm, meta, enc, "primary") for rid, key, arm, meta, enc in encoded_all]
        replay_pairs = [(rid, key, arm, meta, enc) for rid, key, arm, meta, enc in encoded_all if arm == "old"][:REPLAYS]
        for rid, key, arm, meta, enc in replay_pairs:
            queue.append((rid + ":replay", key, arm, meta, enc, "replay"))
        with torch.inference_mode():
            for row_id, key, arm, meta, enc, kind in queue:
                ck(receipt["native_model_forward_calls"] < BUDGET, "Exceeded frozen forward budget")
                n_before = len(cap)
                outlogits = model.forward(enc)
                receipt["native_model_forward_calls"] += 1
                ck(len(outlogits) == len(meta), "branch/logit count mismatch")
                ck(len(cap) - n_before == len(meta), "head capture count mismatch")
                raw = [z.detach().float().cpu().tolist() for z in outlogits]
                probs = [torch.softmax(z.float(), dim=-1).detach().cpu().tolist() for z in outlogits]
                caps = cap[n_before:]
                rows_out.append({"forward_index": receipt["native_model_forward_calls"], "plan_row": row_id,
                                 "arm": arm, "kind": kind,
                                 "questions": [{"id": m["id"], "keys": list(m["keys"]), "logits": v, "probs": p}
                                               for m, v, p in zip(meta, raw, probs)],
                                 "token_ids_sha256": hids(enc["ids"])})
                if kind == "primary":
                    cap_by_row[row_id] = caps
                if kind == "replay":
                    base_row = row_id.split(":replay")[0]
                    pr = next(r for r in rows_out if r["plan_row"] == base_row and r["kind"] == "primary")
                    ck(all(x["logits"] == y["logits"] for x, y in zip(pr["questions"], rows_out[-1]["questions"])),
                       "replay nondeterminism " + base_row)
        ck(physical[0] == receipt["native_model_forward_calls"] == BUDGET, f"physical ledger {physical[0]}")
        lines_out(out / "raw_native_logits_56_requests.jsonl", rows_out)
        produced.append("raw_native_logits_56_requests.jsonl")
        # ---------- readout decomposition ----------
        Wq = model.head.q.weight.detach().float().cpu()
        bq = model.head.q.bias.detach().float().cpu()
        Wk = model.head.k.weight.detach().float().cpu()
        bk = model.head.k.bias.detach().float().cpu()
        per_pair = []
        recon_fail = []
        for rid, key, arm, meta, enc in encoded_all:
            caps = cap_by_row[rid]
            ck(len(caps) == len(meta), "capture/meta mismatch")
            for i, m in enumerate(meta):
                h_dec = caps[i]["h_decide"]
                h_opts = caps[i]["h_opts"]
                qv = Wq @ h_dec + bq
                kv = h_opts @ Wk.T + bk
                recon = (kv @ qv) / math.sqrt(DP) / T
                native = None
                for r in rows_out:
                    if r["plan_row"] == rid and r["kind"] == "primary":
                        native = r["questions"][i]["logits"]
                        break
                err = max(abs(float(a) - float(b)) for a, b in zip(recon.tolist(), native))
                if err > 1e-3:
                    recon_fail.append({"row": rid, "qid": m["id"], "err": err})
        ck(not recon_fail, f"reconstruction gate failed: {canon(recon_fail[:3])}")
        for key, rs in by_pair.items():
            treat = next(r for r in rs if r["arm"] == "new")
            grp = treat["source_group"]
            out_row = {"pair_key": key, "family": treat["family"], "source_group": grp}
            vecs = {}
            for sub in ("old", "new"):
                caps = cap_by_row[key + ":" + sub]
                # branch order equals meta order; recover from decoded rows
                meta_i = [d for d in decoded if d["plan_row"] == key + ":" + sub][0]
                ids_order = list(meta_i["keys"].keys())
                c_i = ids_order.index("conflicting_vote")
                h_dec = caps[c_i]["h_decide"]
                h_opts = caps[c_i]["h_opts"]
                qv = Wq @ h_dec + bq
                kv = h_opts @ Wk.T + bk
                keys = list(meta_i["keys"]["conflicting_vote"])
                nkeys = [{"true": True, "false": False}.get(str(k).strip().lower(), k) for k in keys]
                fi, ti = nkeys.index(False), nkeys.index(True)
                vecs[sub] = {"q": qv, "k_false": kv[fi], "k_true": kv[ti],
                             "M": float((kv[ti] - kv[fi]) @ qv) / s}
            dq = vecs["new"]["q"] - vecs["old"]["q"]
            dT = vecs["new"]["k_true"] - vecs["old"]["k_true"]
            dF = vecs["new"]["k_false"] - vecs["old"]["k_false"]
            d_old = vecs["old"]["k_true"] - vecs["old"]["k_false"]
            d_new = vecs["new"]["k_true"] - vecs["new"]["k_false"]
            dd = d_new - d_old
            t1 = float(dq @ d_old) / s
            t2 = float(vecs["old"]["q"] @ dd) / s
            t3t = float(dq @ dd) / s
            dm_direct = vecs["new"]["M"] - vecs["old"]["M"]
            resid = (t1 + t2 + t3t) - dm_direct
            out_row.update({"M_old": vecs["old"]["M"], "M_new": vecs["new"]["M"],
                            "delta_M": dm_direct, "term_query": t1, "term_key": t2, "term_interaction": t3t,
                            "decomposition_residual": float(resid),
                            "dominant_term": max(("query", t1), ("key", t2), ("interaction", t3t), key=lambda x: abs(x[1]))[0]})
            per_pair.append(out_row)
        ck(all(abs(r["decomposition_residual"]) < 1e-3 for r in per_pair), "decomposition residual too large")
        with (out / "per_pair_decomposition.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for r in per_pair:
                f.write(canon(r) + "\n")
        produced.append("per_pair_decomposition.jsonl")
        agg = collections.defaultdict(lambda: collections.Counter())
        for r in per_pair:
            if r["family"].startswith("T2"):
                agg["T2_" + ("wait" if "WAIT" in r["family"] else "accept")]["pairs"] += 1
                agg["T2_" + ("wait" if "WAIT" in r["family"] else "accept")]["dominant_" + r["dominant_term"]] += 1
            elif r["family"].startswith("T3"):
                agg["T3"]["pairs"] += 1
                agg["T3"]["dominant_" + r["dominant_term"]] += 1
        save(out / "readout_analysis.json", {
            "schema": "JEV_A461_G4_G1R_READOUT_ANALYSIS_V1",
            "temperature": T, "scale_s": s,
            "aggregate_dominant_terms": {k: dict(v) for k, v in sorted(agg.items())},
            "per_pair": per_pair,
            "note": "delta_M three-term exact decomposition on the conflicting_vote branch; dominant term by absolute value; not causal mediation"})
        produced.append("readout_analysis.json")
        gpu_after = torch.cuda.mem_get_info(0)
        hook.remove()
        hk2.remove()
        elapsed = time.time() - t0
        receipt.update(status="COMPLETE_A461_G4_G1R_POINTER_READOUT",
                       physical_forwards=physical[0], budget=BUDGET,
                       elapsed_seconds=round(elapsed, 3),
                       gpu_free_bytes_after=gpu_after[0],
                       backprop_calls=0, network_calls=0, tool_actions=0,
                       test_or_calibration_rows=0,
                       reconstruction_failures=0)
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G4_G1R", error_type=type(err).__name__, error_message=str(err),
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
