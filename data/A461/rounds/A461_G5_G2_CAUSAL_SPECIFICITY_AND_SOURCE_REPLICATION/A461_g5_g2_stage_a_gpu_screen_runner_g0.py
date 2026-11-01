#!/usr/bin/env python3
"""A461-G5-G2 Stage-A GPU screen runner (donor discovery), with G0 CPU preflight.

Executes the Option-A admission draft manifest (N=124 tier-2 W31 candidates x
3 arms = 372 primary forwards + 6 determinism replays = 378 physical calls in
3 runs of 128/128/122) exactly as frozen in
research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/
G2_STAGE_A_ADMISSION_DRAFT/ (manifest blob 01ca53908cc73276d4f6821a4892f05e47e02a15,
roster blob 1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8).

HARD ADMISSION GATE: refuses to load the backbone unless the admission receipt
carries (a) a narrow code-review verdict of exactly "PASS" pinned to this
runner's git blob, and (b) fresh explicit user approval for exactly 378 calls
in 3 batches. --preflight-only runs the entire pre-model CPU path (manifest
re-verification against the roster + corpus, per-row token gate, batch
composition, ledger dry-run) and exits before any CUDA/model load.

Fail-closed: every forward appends its raw row to disk before any post-forward
gate; a failure keeps all completed rows and writes a FAIL receipt. One model
load, zero backprop, zero network, outputs only under ~/wjc.
"""
import argparse, collections, gzip, hashlib, json, math, os, subprocess, sys, time
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"

BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_MANIFEST = "01ca53908cc73276d4f6821a4892f05e47e02a15"
BLOB_G5V2_PAIRS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
TOTAL_CALLS = 378
RUN_CAP = 128


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


def git_blob(repo, sha):
    t = subprocess.run(["git", "-C", str(repo), "cat-file", "-t", sha], capture_output=True, text=True)
    ck(t.returncode == 0 and t.stdout.strip() == "blob", f"not a blob: {sha}")
    return subprocess.run(["git", "-C", str(repo), "cat-file", "blob", sha],
                          capture_output=True, text=True, check=True).stdout


def canon_state(state):
    return json.loads(canon(state))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--preflight-only", action="store_true",
                    help="run the exact pre-model CPU path (admission shape, blob pins, manifest "
                         "re-verification, per-row token gate, ledger dry-run) and exit before CUDA/load")
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(str(out).startswith(str(ROOT)) and out.parent.is_dir() and not out.exists(), "out dir")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    receipt = {"schema": "JEV_A461_G5_G2_STAGE_A_SCREEN_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": "A461_G5_G2_STAGE_A_DONOR_DISCOVERY_GPU_R1",
               "gpu_model_loads": 0, "native_model_forward_calls": 0, "backprop_calls": 0,
               "network_calls": 0, "tool_actions": 0, "test_or_calibration_rows": 0,
               "output_dir": str(out),
               "frozen_inputs": {"roster_blob": BLOB_ROSTER, "manifest_blob": BLOB_MANIFEST,
                                 "g5v2_questions_blob": BLOB_G5V2_PAIRS, "corpus_sha256": CORPUS_SHA}}
    produced = []
    raw_log = out / "raw_native_logits_stage_a.jsonl"
    try:
        out.mkdir(mode=0o700)
        sys.path.insert(0, str(SOURCE))

        # ---------- hard admission shape (no model objects touched yet) ----------
        admit = json.loads(a.admission.read_text("utf8"))
        self_blob = subprocess.run(["git", "-C", str(repo), "hash-object", str(Path(__file__).resolve())],
                                   capture_output=True, text=True, check=True).stdout.strip()
        ck(admit.get("stage") == "A461_G5_G2_STAGE_A_DONOR_DISCOVERY_GPU", "wrong admission stage")
        ck(admit.get("approved_max_native_forwards") == TOTAL_CALLS, f"approved != {TOTAL_CALLS}")
        ck(admit.get("approved_batches") == 3, "approved batches != 3")
        receipt["admission_fields_observed"] = {"blind_review_verdict": admit.get("blind_review_verdict"),
                                                "explicit_user_gpu_approval": admit.get("explicit_user_gpu_approval"),
                                                "runner_blob": admit.get("blind_review_runner_blob"),
                                                "self_blob": self_blob}
        if a.preflight_only:
            pass
        else:
            ck(admit.get("blind_review_verdict") == "PASS", "runner code review has not PASSed")
            ck(admit.get("blind_review_runner_blob") == self_blob, "runner blob != reviewed blob")
            ck(admit.get("explicit_user_gpu_approval") is True, "no explicit user GPU approval")

        # ---------- frozen inputs ----------
        roster_doc = json.loads(git_blob(repo, BLOB_ROSTER))
        ck(roster_doc["schema"] == "JEV_A461_G5_G2_STAGE_A_CANDIDATE_ROSTER_V3", "roster schema")
        by_sha = {r["scene_sha256"]: r for r in roster_doc["candidates"]}
        manifest = [json.loads(x) for x in git_blob(repo, BLOB_MANIFEST).splitlines() if x.strip()]
        ck(len(manifest) == TOTAL_CALLS, f"manifest {len(manifest)}")
        prows = [json.loads(x) for x in git_blob(repo, BLOB_G5V2_PAIRS).splitlines() if x.strip()]
        q_tw = prows[0]["native_request"]["questions"]

        state_by = {}
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    ck(rec["_meta"].get("split") == "development", "non-DEV")
                    state_by[hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()] = rec["state"]
        ck(all(m["scene_sha256"] in state_by for m in manifest if m.get("scene_sha256")), "manifest scenes missing")

        # per-run composition vs the reviewed plan 128/128/122
        run_counts = collections.Counter(m["run"] for m in manifest)
        ck(sorted(run_counts.values()) == [122, 128, 128], f"run sizes {dict(run_counts)}")
        for m in manifest:
            if m["kind"] == "replay":
                ref = next(x for x in manifest if x["forward_index"] == m["replay_of_forward_index"])
                ck(ref["kind"] == "primary" and ref["arm"] == "old" and ref["run"] == m["run"],
                   "replay reference invalid")
                ck(ref["scene_sha256"] == m["scene_sha256"], "replay scene mismatch")

        # ---------- tokenizer + per-row token gate (all 372 primary rows) ----------
        from transformers import AutoTokenizer
        from kev.api import SystemOneRequest, to_record
        from kev.model import encode
        tok = AutoTokenizer.from_pretrained(str(BASE))
        receipt["tokenizer_source"] = str(BASE)
        receipt["base_tokenizer_json_sha256"] = sha_file(BASE / "tokenizer.json")

        def encode_state(state):
            rendered, meta = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": canon_state(state)}))
            enc = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
            ck(not enc["state_truncated"], "truncated state")
            return enc, meta

        # derive each primary row's state from the corpus scene + the roster's frozen edit
        primary = [m for m in manifest if m["kind"] == "primary"]
        ck(len(primary) == 372, "primary count")
        reqs, shas = {}, {}
        for scene_sha in sorted({m["scene_sha256"] for m in primary}):
            r = by_sha[scene_sha]
            st_old = state_by[scene_sha]
            st_new = json.loads(canon(st_old))
            st_new["received_messages"].append(dict(r["declared_edit_new"]["message"]))
            st_sa = json.loads(canon(st_old))
            st_sa["received_messages"].append(dict(r["declared_edit_sa"]["message"]))
            states = {"old": st_old, "new": st_new, "SA": st_sa}
            for arm in ("old", "new", "SA"):
                enc, meta = encode_state(states[arm])
                sha = hids(enc["ids"])
                ck(sha == r["token_ids_sha256"][arm],
                   f"token gate mismatch {scene_sha[:8]}:{arm}")
                reqs[(scene_sha, arm)] = {"questions": q_tw, "state": states[arm]}
                shas[(scene_sha, arm)] = sha
        ck(len(reqs) == 372, "derived requests")

        # ledger dry-run: predicted composition per run
        dry = collections.Counter()
        for m in manifest:
            dry[(m["run"], m["kind"])] += 1
        receipt["ledger_dry_run"] = {f"run{k}": {"primary": v[0], "replay": v[1], "total": v[0] + v[1]}
                                     for k in sorted(run_counts)
                                     for v in [(dry[(k, "primary")], dry[(k, "replay")])]}

        if a.preflight_only:
            receipt.update(status="COMPLETE_A461_G5_G2_STAGE_A_PREFLIGHT",
                           manifest_rows=len(manifest), primary_rows=len(primary),
                           token_gate="372/372 PASS" if True else "FAIL",
                           runs={str(k): v for k, v in sorted(run_counts.items())},
                           native_model_forward_calls=0, model_loads=0,
                           note="preflight of the full-run code path before any CUDA/model load; not a GPU admission")
            with (out / "execution_receipt.json").open("x", encoding="utf8", newline="\n") as f:
                json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=False)
                f.write("\n")
            produced.append("execution_receipt.json")
            with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
                for n in produced:
                    f.write(sha_file(out / n) + "  " + n + "\n")
            print(canon(receipt))
            return 0

        # ---------- load model (1 load) ----------
        import torch
        torch.set_num_threads(4)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        from kev.checkpoint import Checkpoint, LoadOptions
        checkpoint = Checkpoint(str(CKPT))
        checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
        tokenizer, model = checkpoint.load("cuda:0", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
        receipt["gpu_model_loads"] = 1
        model.eval()
        model.requires_grad_(False)
        ck(model.hybrid, "expected hybrid backbone (row-form forwards)")
        physical = [0]

        def bump(_m, _a):
            physical[0] += 1
        hk = model.lm.register_forward_pre_hook(bump)

        def run_forward(req, entry):
            """One physical forward for one manifest entry; appends the raw row
            before any post-forward gate."""
            ck(receipt["native_model_forward_calls"] < TOTAL_CALLS, "budget exceeded")
            entry_index = entry["forward_index"]
            ck(receipt["native_model_forward_calls"] + 1 == entry_index,
               f"manifest order deviation at call {receipt['native_model_forward_calls'] + 1}")
            enc, meta = encode_state(req["state"])
            c_idx = [m["id"] for m in meta].index("conflicting_vote")
            ck(hids(enc["ids"]) == entry["token_ids_sha256"], "encode != frozen witness " + entry["scene_sha256"][:8])
            with torch.inference_mode():
                outlogits = model.forward(enc)
            receipt["native_model_forward_calls"] += 1
            ck(len(outlogits) == len(meta) == 4, "branch count")
            raw = [z.detach().float().cpu().tolist() for z in outlogits]
            ck(all(len(v) == len(m["keys"]) and all(math.isfinite(float(x)) for x in v)
                   for v, m in zip(raw, meta)), "invalid logits")
            row = {"forward_index": entry_index, "run": entry["run"], "kind": entry["kind"],
                   "scene_sha256": entry.get("scene_sha256"), "arm": entry.get("arm"),
                   "frozen_width": entry.get("frozen_width"), "cell": entry.get("cell"),
                   "source_group": entry.get("source_group"),
                   "replay_of_forward_index": entry.get("replay_of_forward_index"),
                   "conflicting_vote_branch_index": c_idx,
                   "questions": [{"id": m["id"], "keys": list(m["keys"]), "logits": v}
                                 for m, v in zip(meta, raw)],
                   "token_ids_sha256": hids(enc["ids"]),
                   "state_token_len": len(enc["ids"][:enc["seg"].count(0)])}
            with raw_log.open("a", encoding="utf8", newline="\n") as f:
                f.write(canon(row) + "\n")
            return row

        rows_out, primary_rows_by_index = [], {}
        t0 = time.time()
        for entry in manifest:
            if entry["kind"] == "replay":
                ref_row = primary_rows_by_index[entry["replay_of_forward_index"]]
                ref_req = next(req for (s, arm), req in reqs.items()
                               if s == ref_row["scene_sha256"] and arm == "old")
                row = run_forward(ref_req, entry)
                ck(all(x["logits"] == y["logits"] for x, y in
                       zip(ref_row["questions"], row["questions"])),
                   f"replay not bitwise vs forward {entry['replay_of_forward_index']}")
            else:
                key = (entry["scene_sha256"], entry["arm"])
                row = run_forward(reqs[key], entry)
                primary_rows_by_index[entry["forward_index"]] = row
            rows_out.append(row)

        ck(physical[0] == receipt["native_model_forward_calls"] == TOTAL_CALLS,
           f"ledger mismatch physical={physical[0]}")
        ck(len(rows_out) == TOTAL_CALLS, "row count")
        produced.append("raw_native_logits_stage_a.jsonl")
        hk.remove()
        receipt.update(status="COMPLETE_A461_G5_G2_STAGE_A_SCREEN",
                       physical_forwards=physical[0], budget=TOTAL_CALLS, rows=len(rows_out),
                       runs=sorted(run_counts), elapsed_seconds=round(time.time() - t0, 3),
                       backprop_calls=0, network_calls=0, tool_actions=0, test_or_calibration_rows=0)
        code = 0
    except Exception as err:
        import traceback
        if raw_log.exists() and "raw_native_logits_stage_a.jsonl" not in produced:
            produced.append("raw_native_logits_stage_a.jsonl")
        try:
            receipt["physical_prehook_count_at_failure"] = physical[0]
        except NameError:
            pass
        receipt.update(status="FAIL_A461_G5_G2_STAGE_A_SCREEN", error_type=type(err).__name__,
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
