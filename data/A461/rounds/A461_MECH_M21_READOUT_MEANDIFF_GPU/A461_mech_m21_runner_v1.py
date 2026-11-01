#!/usr/bin/env python3
"""A461-MECH-M21 R1 runner: the high-energy readout test. Per M18 row: a plain replay (bitwise == M18), then, only at
the <decide> token of the certificate_action row on the residual output of layer 19 or 31, either the M19 gain op
h' = h + (gamma - 1) (h.u - c) u (gamma 8 / 32) or a push h' = h + beta |h| u (beta 0.05 / 0.2) along the held-out
class-mean-difference direction u, or a push of 0.2 |h| along a seeded random direction. Built from the M19 runner
(9c0a3108): the gain op, gates, ledger, admission, model load, batch loop, state rebuild and the other-rows check are
kept; the push kind is added, and the names, plan and pins change. Standing GPU authorization (policy V2). Zero
backprop, zero network, outputs only under ~/wjc.
"""
import argparse, collections, gzip, hashlib, importlib.util, json, math, os, subprocess, sys, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
V4_PATH = HERE / "A461_g5_g2_k4b_stage_a_screen_runner_v1.py"   # kev-4B identity, source, paths, safety module
V4_BLOB = "f118ea59120a9cd470ae934f5fc2482501c56bb9"
_blob = subprocess.run(["git", "hash-object", str(V4_PATH)], capture_output=True, text=True, check=True).stdout.strip()
if _blob != V4_BLOB:
    raise SystemExit(f"Stage-A runner V4 blob {_blob} != pinned {V4_BLOB}")
_spec = importlib.util.spec_from_file_location("stage_a_v4", V4_PATH)
v4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v4)
ck, inside, sha_file, hids, canon, git_blob = v4.ck, v4.inside, v4.sha_file, v4.hids, v4.canon, v4.git_blob
write_new, append_line, jsonl = v4.write_new, v4.append_line, v4.jsonl

ROOT, CORPUS, CORPUS_SHA, CKPT, BASE, SOURCE, WORK = v4.ROOT, v4.CORPUS, v4.CORPUS_SHA, v4.CKPT, v4.BASE, v4.SOURCE, v4.WORK
GPU_RUNS_ROOT = WORK / "M21_GPU_RUNS"
GPU_QUOTA_ROOT = WORK / "M21_QUOTA_LEDGER"
STAGE = "A461_MECH_M21_READOUT_MEANDIFF_GPU"
BLOB_MANIFEST = "e559fc17f1adcd1a73919cebfe5c3c0bc6b6e1c4"
BLOB_DESIGN = "eff089949d542f828e29a1675dfdb126b62d78f0"
BLOB_M18_DESIGN = "1998024bffc0e8deee2cbf0d563eafbffad6bfef"
BLOB_M18_RAW = "10e04cfadfaba7364abbb2eeb922b92c09ad9ea4"   # M18 raw rows (bitwise anchors of the replays)
BLOB_ROSTER, BLOB_G5V2 = v4.BLOB_ROSTER, v4.BLOB_G5V2_PAIRS
FROZEN_BATCHES = [128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 36]
FROZEN_TOTAL = 6820
N_LAYERS = 32
HEAD_LAYER = 11
N_HEADS = 16
OP_LAYERS = (19, 31)
GAMMAS = (8.0, 32.0)
BETAS = (0.05, 0.2)
SPAN_W = 31
ARMS = ("old", "new", "SA", "ROUND", "OUTSIDER")

def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def c_margin(questions):
    c = next(q for q in questions if q["id"] == "conflicting_vote")
    return c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--directions", required=True, type=Path)
    ap.add_argument("--m18-design", required=True, type=Path)
    ap.add_argument("--m18-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--backend", choices=["gpu", "fake"], default="gpu")
    ap.add_argument("--quota-root", type=Path, default=None, help="fake backend only")
    ap.add_argument("--expect-batches", default=",".join(map(str, FROZEN_BATCHES)))
    ap.add_argument("--allow-manifest-blob", default=BLOB_MANIFEST, help="fake backend only may differ")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--pre-model-gate-only", action="store_true")
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(inside(out, ROOT), "out dir: output must be inside ~/wjc (directory relation)")
    ck(out.parent.is_dir() and not out.exists(), "out dir: parent missing or out exists")
    full_run = not (a.preflight_only or a.pre_model_gate_only)
    if a.backend == "gpu" and full_run:
        ck(out.parent == GPU_RUNS_ROOT.resolve(), "gpu run out dir must be a direct child of M21_GPU_RUNS")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    expect_batches = [int(x) for x in a.expect_batches.split(",")]
    receipt = {"schema": "JEV_A461_MECH_M21_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": "A461_MECH_M21_GPU_R1", "backend": a.backend,
               "expect_batches": expect_batches, "gpu_model_loads": 0, "model_loads": 0,
               "native_model_forward_calls": 0, "physical_prehook_calls": 0, "denied_prehook_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "batch_receipts": [], "output_dir": str(out),
               "stage_a_runner_v4_blob": V4_BLOB}
    produced = []
    raw_log = out / "raw_native_logits_m21.jsonl"
    attempt_log = out / "attempt_receipts.jsonl"
    physical, reserved, current = [0], [0], [None]
    physical_by_batch = {}
    model = ledger = None
    attempt_id = uuid.uuid4().hex
    try:
        out.mkdir(mode=0o700)
        sys.path.insert(0, str(SOURCE))
        admit = json.loads(a.admission.read_text("utf8"))
        self_blob = file_blob(Path(__file__).resolve())
        receipt["runner_blob"] = self_blob
        ck(admit.get("stage") == STAGE, "wrong admission stage")
        approved_max = int(admit.get("approved_max_native_forwards", 0))
        ck(admit.get("approved_batches") == len(expect_batches), "approved batches != expected")
        ck(sum(expect_batches) <= approved_max, "cumulative overrun: plan exceeds the approved total")
        ck(all(0 < n <= v4.RUN_CAP for n in expect_batches), f"batch plan {expect_batches} exceeds cap {v4.RUN_CAP}")
        receipt["admission_fields_observed"] = {k: admit.get(k) for k in (
            "admission_id", "mode", "governance", "user_gpu_approval_quote", "user_gpu_approval_utc",
            "explicit_user_gpu_approval", "approved_runner_blob", "approved_max_native_forwards",
            "approved_batch_plan", "model_identity_sha256")}
        manifest_blob = file_blob(a.manifest)
        pins = {"manifest_blob": BLOB_MANIFEST, "design_blob": BLOB_DESIGN, "m18_raw_blob": BLOB_M18_RAW, "m18_design_blob": BLOB_M18_DESIGN,
                "roster_blob": BLOB_ROSTER, "g5v2_questions_blob": BLOB_G5V2, "corpus_sha256": CORPUS_SHA}
        receipt["frozen_inputs"] = dict(pins, manifest_blob=manifest_blob)
        if a.backend == "fake":
            ck(admit.get("mode") == "L1_FAKE", "fake backend requires admission mode L1_FAKE")
            ck(manifest_blob == a.allow_manifest_blob, "manifest blob != allowed")
        elif not a.preflight_only:
            ck(manifest_blob == BLOB_MANIFEST, "gpu backend: manifest blob override refused")
            ck(expect_batches == FROZEN_BATCHES and a.quota_root is None, "gpu backend: plan/quota override refused")
            ck(admit.get("mode") == "GPU", "gpu backend requires admission mode GPU")
            ck(admit.get("frozen_inputs") == pins, "admission frozen_inputs != pinned inputs")
            ck(admit.get("approved_batch_plan") == FROZEN_BATCHES and approved_max == FROZEN_TOTAL,
               "gpu approval must be exactly 6820 calls / [128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 36]")
            ck(admit.get("model_identity_sha256") == v4.identity_digest(v4.MODEL_IDENTITY), "model identity digest")
            ck(admit.get("governance") == "JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2"
               and isinstance(admit.get("user_gpu_approval_quote"), str)
               and len(admit["user_gpu_approval_quote"].strip()) >= 4 and admit.get("user_gpu_approval_utc"),
               "no policy V2 user GPU approval record (quote + time)")
            ck(admit.get("approved_runner_blob") == self_blob, "runner blob != approved runner blob")
            ck(admit.get("explicit_user_gpu_approval") is True, "no explicit user GPU approval")
        if a.backend == "gpu" and not a.preflight_only:
            ident = v4.model_identity()
            receipt["model_identity"] = ident
            v4.verify_identity(ident, v4.MODEL_IDENTITY)
            receipt["model_identity_verified"] = True

        # ---------- durable quota ledger ----------
        consumed = 0
        if not a.preflight_only:
            admission_id = admit.get("admission_id")
            ck(isinstance(admission_id, str) and 8 <= len(admission_id) <= 80
               and all(ch.isalnum() or ch in "_-" for ch in admission_id), "admission_id missing or malformed")
            if a.backend == "gpu":
                qroot, runs_root = GPU_QUOTA_ROOT, GPU_RUNS_ROOT
            else:
                ck(a.quota_root is not None, "fake backend run needs --quota-root")
                qroot, runs_root = a.quota_root.expanduser().resolve(strict=False), out.parent
                ck(inside(qroot, ROOT) and qroot != GPU_QUOTA_ROOT.resolve(), "fake quota root")
            receipt["quota_ledger"] = {"path": str(Path(qroot) / admission_id / "ledger.jsonl"), "attempt_id": attempt_id}
            ledger = v4.QuotaLedger(qroot, admission_id, runs_root, write=full_run)
            _ev, consumed, summary = ledger.state()
            receipt["quota_ledger"].update(consumed_before=consumed, prior_attempts=summary)
            ck(consumed + sum(expect_batches) <= approved_max,
               f"cumulative overrun: ledger consumed {consumed} + plan {sum(expect_batches)} > approved {approved_max}")

        # ---------- frozen inputs ----------
        ck(file_blob(a.m18_raw) == BLOB_M18_RAW and file_blob(a.m18_design) == BLOB_M18_DESIGN, "M18 pins")
        ck(file_blob(a.design) == BLOB_DESIGN or a.backend == "fake", "design blob pin")
        raw18 = {r["forward_index"]: r for r in jsonl(a.m18_raw)}
        design = json.loads(a.m18_design.read_text("utf8"))
        d19 = json.loads(a.design.read_text("utf8"))
        ck(sha_file(a.directions) == d19["directions_file"]["sha256"], "directions file sha")
        manifest = jsonl(a.manifest)
        ck(len(manifest) == sum(expect_batches), "manifest length != plan")
        ck([m["forward_index"] for m in manifest] == list(range(1, len(manifest) + 1)), "forward_index not 1..N")
        caps_b = {k + 1: n for k, n in enumerate(expect_batches)}
        ck(dict(collections.Counter(m["run"] for m in manifest)) == caps_b, "run sizes != plan")
        ck([m["run"] for m in manifest] == sorted(m["run"] for m in manifest), "runs not contiguous")
        roster = {r["scene_sha256"]: r for r in json.loads(git_blob(repo, BLOB_ROSTER))["candidates"]}
        q_tw = json.loads(git_blob(repo, BLOB_G5V2).splitlines()[0])["native_request"]["questions"]
        need = {m["target_scene"] for m in manifest}
        state_by = {}
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    if rec["_meta"].get("source") == "twins_streamlet":
                        h_ = hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()
                        if h_ in need:
                            state_by[h_] = rec["state"]
        ck(set(state_by) == need, "scene recovery")
        from transformers import AutoTokenizer
        from kev.api import SystemOneRequest, to_record
        from kev.model import encode
        tok = AutoTokenizer.from_pretrained(str(BASE))

        def encode_state(state):
            rendered, meta = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
            enc = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
            ck(not enc["state_truncated"], "truncated state")
            return enc, meta

        reqs = {}
        for m in manifest:
            s, arm = m["target_scene"], m["target_arm"]
            ck(arm in ARMS, f"arm {m['forward_index']}")
            op = m.get("op")
            if op is None:
                ck(m["condition"] == f"replay_{arm}" and m.get("replay_of_m18"), f"replay row {m['forward_index']}")
                kr = raw18[m["replay_of_m18"]]
                ck(kr["target_scene"] == s and kr["target_arm"] == arm and kr["token_ids_sha256"] == m["token_ids_sha256"],
                   f"M18 replay ref {m['forward_index']}")
            else:
                ck(op["layer"] in OP_LAYERS and op["kind"] in ("gain", "push") and op["dir"] in ("meandiff", "random")
                   and ((op["kind"] == "gain" and op["dir"] == "meandiff" and op["gamma"] in GAMMAS
                         and isinstance(op["c"], float) and set(op) == {"layer", "kind", "gamma", "dir", "key", "c"}
                         and m["condition"] == f"gain_L{op['layer']}_g{int(op['gamma'])}")
                        or (op["kind"] == "push" and op["dir"] == "meandiff" and op["beta"] in BETAS
                            and set(op) == {"layer", "kind", "beta", "dir", "key"}
                            and m["condition"] == f"push_L{op['layer']}_b{int(op['beta'] * 100):02d}")
                        or (op["kind"] == "push" and op["dir"] == "random" and op["beta"] == 0.2
                            and set(op) == {"layer", "kind", "beta", "dir", "key"}
                            and m["condition"] == f"rand_L{op['layer']}_b20"))
                   and op["key"] == (f"L{op['layer']}|{m['source_group']}" if op["dir"] == "meandiff"
                                     else f"R|L{op['layer']}|{s[:12]}|{arm}"), f"op row {m['forward_index']}")
                ck(op["kind"] == "push" or op["c"] == d19["centres"][op["key"]], f"centre {m['forward_index']}")
            st = json.loads(canon(state_by[s]))
            x = design["scenes"][s]["arms"][arm]
            if arm != "old":
                msg = (roster[s]["declared_edit_new"]["message"] if arm == "new" else
                       roster[s]["declared_edit_sa"]["message"] if arm == "SA" else x["message"])
                ck(msg == x["message"], f"message {s[:8]}:{arm}")
                if arm in ("ROUND", "OUTSIDER"):
                    base = roster[s]["declared_edit_new"]["message"]
                    ck(sum(base[k_] != msg[k_] for k_ in base) == 1 and set(base) == set(msg),
                       f"{arm} differs from the frozen message in exactly one field {s[:8]}")
                st["received_messages"].append(dict(msg))
            enc, _meta = encode_state(st)
            ids = enc["ids"][:enc["seg"].count(0)]
            ck(hids(enc["ids"]) == m["token_ids_sha256"] == x["token_ids_sha256"], f"token gate {s[:8]}:{arm}")
            ck(len(ids) == m["state_len"], f"state length {s[:8]}:{arm}")
            s0, s1 = m["span"]
            ck(m["span"] == x["span"] and 0 <= s0 < s1 <= len(ids), f"span {s[:8]}:{arm}")
            ck((s1 - s0 == SPAN_W) == (arm != "old"), f"span width {s[:8]}:{arm}")
            reqs[(s, arm)] = st
        seen = set()
        for m in manifest:   # each (scene, arm) has its replay before its op rows
            k_ = (m["target_scene"], m["target_arm"])
            ck((m.get("op") is None) == (k_ not in seen), f"replay order {m['forward_index']}")
            seen.add(k_)
        need_dirs = {m["op"]["key"] for m in manifest if m.get("op")}
        receipt["preflight"] = {"scenes": len(need), "token_gate": "PASS", "span_gate": "PASS",
                                "manifest_rows": len(manifest)}
        if not full_run:
            receipt.update(status=("COMPLETE_A461_MECH_M21_PRE_MODEL_GATE" if a.pre_model_gate_only
                                   else "COMPLETE_A461_MECH_M21_PREFLIGHT"))
            raise SystemExit(0)

        ledger.append({"event": "attempt_open", "attempt_id": attempt_id, "out_dir": str(out),
                       "runner_blob": self_blob, "backend": a.backend, "plan": expect_batches})
        write_new(out / "attempt_manifest.json", {"admission_id": admission_id, "attempt_id": attempt_id,
                                                  "runner_blob": self_blob, "backend": a.backend})
        produced.append("attempt_manifest.json")
        consumed_total = [consumed]

        import torch
        if a.backend == "fake":
            sys.path.insert(0, str(HERE))
            from A461_mech_m3_fake_attention_model_v1 import FakePatchModel   # M3 fake model, unchanged
            model = FakePatchModel(n_layers=N_LAYERS)
            receipt["fake_model_fault"] = model.fault
        else:
            torch.set_num_threads(4)
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            torch.backends.cuda.enable_flash_sdp(False)
            torch.backends.cuda.enable_mem_efficient_sdp(False)
            from kev.checkpoint import Checkpoint, Meta, LoadOptions
            meta_ck = torch.load(CKPT / "head.pt", map_location="cpu", weights_only=True)
            ck(meta_ck["base"] == "Qwen/Qwen3.5-4B-Base" and meta_ck["lora"] == 16 and meta_ck["head_dim"] == 256
               and meta_ck["weights_dtype"] == "fp32", "kev-4B checkpoint metadata")
            checkpoint = Checkpoint.__new__(Checkpoint)
            checkpoint.requested = checkpoint.path = str(CKPT)
            checkpoint.meta = Meta.from_dict(meta_ck)
            checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
            _tok, model = checkpoint.load("cuda:0", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa",
                                                                backend="torch", cuda_graphs=False, fused=False,
                                                                lora_scale=1.0))
            ck(model.lm.config.hidden_size == 2560, "kev-4B hidden size")
            ck(all(torch.equal(model.head.state_dict()[k].cpu(), v) for k, v in meta_ck["head"].items()),
               "loaded head differs from head.pt")
            receipt["kev4b_load"] = {"cuda_max_memory_allocated_after_load": torch.cuda.max_memory_allocated()}
            receipt["gpu_model_loads"] = 1
        receipt["model_loads"] = 1
        model.eval()
        model.requires_grad_(False)
        ck(model.hybrid, "expected hybrid backbone (row-form forwards)")

        def gate(_m, _a):
            b = current[0]
            reason = None
            if physical[0] >= reserved[0]:
                reason = "no unused reservation (extra LM call within one forward)"
            elif b is None or physical_by_batch.get(b, 0) >= min(caps_b.get(b, 0), v4.RUN_CAP):
                reason = f"batch {b} physical cap reached"
            elif consumed + physical[0] >= approved_max:
                reason = "approval exhausted"
            if reason:
                receipt["denied_prehook_calls"] += 1
                raise RuntimeError(f"LM pre-hook refused call before LM body: {reason}")
            physical[0] += 1
            physical_by_batch[b] = physical_by_batch.get(b, 0) + 1
        hooks = [model.lm.register_forward_pre_hook(gate)]

        (out / "captures").mkdir(mode=0o700)
        layer_mods = model.lm.base_model.model.layers
        ck(len(layer_mods) == N_LAYERS, f"backbone has {len(layer_mods)} layers, expected {N_LAYERS}")
        norm_mod = getattr(model.lm.base_model.model, "norm", None)
        ck(norm_mod is not None or a.backend == "fake", "final norm module missing")
        dirs = torch.load(a.directions, weights_only=True)
        ck(need_dirs <= set(dirs), "directions missing from the directions file")
        spec, got, fired = {}, {}, set()
        replay_logits = {}

        def layer_post(i):
            def fn(module, args, kwargs, output):
                op = spec.get("op")
                if not op or op["layer"] != i:
                    return None
                h = output[0] if isinstance(output, tuple) else output
                ck(h.shape[0] == spec["n_rows"], f"rows per pass {h.shape[0]} != questions {spec['n_rows']}")
                r, e = spec["row"], spec["end"]
                ck(spec["u"].numel() == h.shape[-1], f"direction width {spec['u'].numel()} != hidden {h.shape[-1]}")
                u = spec["u"].to(device=h.device, dtype=h.dtype)
                v = h[r, e]
                if op["kind"] == "gain":
                    d = (v @ u) - op["c"]
                    delta = (op["gamma"] - 1.0) * d * u
                else:
                    d = v.norm()
                    delta = op["beta"] * d * u
                h = h.clone()
                h[r, e] = v + delta
                got["op"] = {"kind": op["kind"], "proj_before": float(v @ u), "dev": float(d),
                             "delta_norm": float(delta.norm()), "h_norm": float(v.norm())}
                fired.add("op")
                return (h,) + tuple(output[1:]) if isinstance(output, tuple) else h
            return fn

        def final_post(module, args, output):
            if spec.get("capture"):
                h = output[0] if isinstance(output, tuple) else output
                r = spec["row"]
                got["dec"] = h[r, spec["end"]].detach().float().cpu()
                got["opts"] = h[r, spec["opts"]].detach().float().cpu()
                fired.add("final")
            return None

        hooks += [layer_mods[i].register_forward_hook(layer_post(i), with_kwargs=True) for i in OP_LAYERS]
        hooks.append((norm_mod if norm_mod is not None else layer_mods[N_LAYERS - 1]).register_forward_hook(final_post))

        def run_entry(m):
            b = m["run"]
            ck(current[0] == b and receipt["native_model_forward_calls"] + 1 == m["forward_index"], "order")
            v4.batch_guard(physical_by_batch.get(b, 0), caps_b[b])
            ck(physical[0] == receipt["native_model_forward_calls"] == reserved[0], "ledger drift")
            ck(consumed_total[0] + 1 <= approved_max, "global budget")
            enc, meta = encode_state(reqs[(m["target_scene"], m["target_arm"])])
            qids = [q["id"] for q in meta]
            c_idx = qids.index("conflicting_vote")
            row = qids.index("certificate_action")
            seg = enc["seg"]
            S_len = seg.count(0)
            br_len = [seg.count(k) for k in range(1, len(qids) + 1)]
            ck(sum(br_len) + S_len == len(seg), "segments")
            base_k = S_len + sum(br_len[:row])
            spec.clear()
            got.clear()
            fired.clear()
            spec.update(row=row, end=S_len + br_len[row] - 1, n_rows=len(qids),
                        opts=[S_len + (o - base_k) for o in enc["opt_idx"][row]])
            ck(enc["decide_idx"][row] - base_k + S_len == spec["end"], "decide position")
            op = m.get("op")
            if op:
                spec.update(op=op, u=dirs[op["key"]])
            else:
                spec["capture"] = True
            ledger.append({"event": "reserve", "attempt_id": attempt_id, "forward_index": m["forward_index"], "run": b})
            reserved[0] += 1
            consumed_total[0] += 1
            att = {"forward_index": m["forward_index"], "run": b, "condition": m["condition"]}
            try:
                with torch.inference_mode():
                    z = model.forward(enc)
            except Exception as err:
                append_line(attempt_log, dict(att, status="FORWARD_FAILED", error_type=type(err).__name__,
                                              error_message=str(err)[:200]), sync=True)
                raise
            receipt["native_model_forward_calls"] += 1
            try:
                ck(len(z) == len(meta) == 4, "branch count")
                raw = [[float(x) for x in (zz.detach().float().cpu().tolist())] for zz in z]
                ck(all(len(v) == len(q["keys"]) and all(math.isfinite(x) for x in v) for v, q in zip(raw, meta)),
                   "invalid logits")
                qs = [{"id": q["id"], "keys": list(q["keys"]), "logits": v} for q, v in zip(meta, raw)]
                row_ = dict(att, target_scene=m["target_scene"], target_arm=m["target_arm"],
                            source_group=m["source_group"], gold_action=m["gold_action"], op=op,
                            op_stats=got.get("op"), decision_position=spec["end"], decision_row=row,
                            conflicting_vote_branch_index=c_idx, capture_file=None,
                            questions=qs, M=c_margin(qs), token_ids_sha256=hids(enc["ids"]), state_len=S_len)
                if op:
                    ck(fired == {"op"}, f"op hook fired {sorted(fired)}")
                else:
                    ck(fired == {"final"}, f"capture hook fired {sorted(fired)}")
                    cf = out / "captures" / f"{m['target_arm']}_{m['target_scene'][:12]}_m21.pt"
                    with cf.open("xb") as fh:
                        torch.save({"decide": got["dec"], "opts": got["opts"], "opt_keys": list(meta[row]["keys"])}, fh)
                        fh.flush()
                        os.fsync(fh.fileno())
                    row_["capture_file"] = {"name": cf.name, "sha256": sha_file(cf), "opts_shape": list(got["opts"].shape)}
                canon(row_)
            except Exception as err:
                append_line(attempt_log, dict(att, status="INVALID_OUTPUT", error_type=type(err).__name__,
                                              error_message=str(err)[:200]), sync=True)
                raise
            append_line(raw_log, row_, sync=True)
            k_ = (m["target_scene"], m["target_arm"])
            if not op:
                replay_logits[k_] = qs
                if a.backend == "gpu":
                    kr = raw18[m["replay_of_m18"]]
                    ck(all(x["logits"] == y["logits"] for x, y in zip(kr["questions"], qs)),
                       f"not bitwise == M18 forward {m['replay_of_m18']}")
            else:
                ref = replay_logits[k_]
                tol = 0.0 if a.backend == "gpu" else 1e-5
                ck(all(max(abs(u_ - v_) for u_, v_ in zip(x["logits"], y["logits"])) <= tol
                       for i_, (x, y) in enumerate(zip(ref, qs)) if i_ != row),
                   f"op reached a question row other than certificate_action at {m['forward_index']}")
            return row_

        t0 = time.time()
        receipt["batch_receipts"] = [{"run": k, "planned": caps_b[k], "status": "NOT_STARTED", "physical": 0}
                                     for k in sorted(caps_b)]
        for br in receipt["batch_receipts"]:
            b = br["run"]
            current[0] = b
            physical_by_batch[b] = 0
            br["status"] = "IN_PROGRESS"
            n = 0
            for m in (x for x in manifest if x["run"] == b):
                run_entry(m)
                n += 1
                br["physical"] = physical_by_batch[b]
            ck(physical_by_batch[b] == caps_b[b] == n, f"batch {b} physical != planned")
            br.update(status="COMPLETE", rows=n, cumulative_physical_after=physical[0])
            write_new(out / f"batch_receipt_run{b}.json", dict(br, runner_blob=self_blob, attempt_id=attempt_id))
            produced.append(f"batch_receipt_run{b}.json")
            current[0] = None
        for hk in hooks:
            hk.remove()
        ck(physical[0] == receipt["native_model_forward_calls"] == reserved[0] == sum(expect_batches), "ledger total")
        ck(len(jsonl(raw_log)) == sum(expect_batches), "row count")
        produced.append("raw_native_logits_m21.jsonl")
        produced += sorted("captures/" + p.name for p in (out / "captures").iterdir())
        if attempt_log.exists():
            produced.append("attempt_receipts.jsonl")
        receipt.update(status="COMPLETE_A461_MECH_M21", physical_forwards=physical[0],
                       elapsed_seconds=round(time.time() - t0, 3),
                       bitwise_vs_m18="checked" if a.backend == "gpu" else "not_applicable_fake_backend")
        code = 0
    except SystemExit as stop:
        code = int(stop.code or 0)
    except Exception as err:
        import traceback
        for n_, p_ in (("raw_native_logits_m21.jsonl", raw_log), ("attempt_receipts.jsonl", attempt_log)):
            if p_.exists() and n_ not in produced:
                produced.append(n_)
        receipt["physical_by_batch_at_failure"] = {str(k): v for k, v in physical_by_batch.items() if k}
        for br in receipt.get("batch_receipts", []):
            if br["status"] == "IN_PROGRESS":
                br["status"] = "FAILED_AT_THIS_BATCH"
                br["physical"] = physical_by_batch.get(br["run"], 0)
        receipt.update(status="FAIL_A461_MECH_M21", error_type=type(err).__name__, error_message=str(err),
                       traceback=traceback.format_exc()[-2000:])
        code = 2
    if ledger is not None and ledger.fd is not None:
        if (out / "attempt_manifest.json").exists():
            ledger.append({"event": "attempt_close", "attempt_id": attempt_id, "status": receipt["status"],
                           "physical": physical[0], "reserved": reserved[0]})
        receipt.setdefault("quota_ledger", {})["consumed_after"] = v4.ledger_consumed(jsonl(ledger.path))
        ledger.release()
    receipt["physical_prehook_calls"] = physical[0]
    receipt["ledger_reserved_calls"] = reserved[0]
    receipt["durable_appends"] = {"raw_rows": v4.DURABLE["raw_native_logits_m21.jsonl"],
                                  "ledger_events": v4.DURABLE["ledger.jsonl"]}
    receipt["cuda_initialized"] = "torch" in sys.modules and bool(sys.modules["torch"].cuda.is_initialized())
    if not out.is_dir():
        print(canon(receipt))
        return code
    write_new(out / "execution_receipt.json", receipt)
    produced.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n_ in produced:
            f.write(sha_file(out / n_) + "  " + n_ + "\n")
    print(canon({k: receipt.get(k) for k in ("status", "error_message", "physical_prehook_calls", "denied_prehook_calls",
                                             "batch_receipts", "elapsed_seconds", "preflight")}))
    return code


if __name__ == "__main__":
    sys.exit(main())
