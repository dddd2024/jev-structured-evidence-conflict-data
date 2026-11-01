#!/usr/bin/env python3
"""A461-MON-M22 R1 runner: the M18 monitor-capture stage on the second frozen model, SecJev-0.8B (Qwen3.5-0.8B base
+ SecJev LoRA + pointer head; 24 layers, full attention at 3, 7, 11, 15, 19, 23). Plain forwards of the 124 Stage-A
scenes x (old, new, SA, ROUND, OUTSIDER) with read-only feature captures (L11 o_proj input over the monitored span;
residuals after the full-attention layers and the layer-0 input, averaged over the span and at the decision position of
the certificate_action row). Every old / new / SA forward must equal the pinned SecJev Stage-A raw row bitwise (GPU,
fail-closed). Built from the M18 runner (f5e5c499): the identity / ledger / safety module is the SecJev Stage-A runner
(g0_v4, b675e9d5) instead of the kev-4B one, the model load is SecJev's (as in that runner), and the layer counts,
names, plan and pins change; hooks and per-forward body are unchanged. Standing GPU authorization (policy V2). Zero
backprop, zero network, outputs only under ~/wjc.
"""
import argparse, collections, gzip, hashlib, importlib.util, json, math, os, subprocess, sys, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
V4_PATH = HERE / "A461_g5_g2_stage_a_gpu_screen_runner_g0_v4.py"   # SecJev-0.8B identity, source, paths, safety module
V4_BLOB = "b675e9d555307720cf1dd964b20db487344f8803"
_blob = subprocess.run(["git", "hash-object", str(V4_PATH)], capture_output=True, text=True, check=True).stdout.strip()
if _blob != V4_BLOB:
    raise SystemExit(f"Stage-A runner V4 blob {_blob} != pinned {V4_BLOB}")
_spec = importlib.util.spec_from_file_location("stage_a_v4", V4_PATH)
v4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v4)
ck, inside, sha_file, hids, canon, git_blob = v4.ck, v4.inside, v4.sha_file, v4.hids, v4.canon, v4.git_blob
write_new, append_line, jsonl = v4.write_new, v4.append_line, v4.jsonl

ROOT, CORPUS, CORPUS_SHA, CKPT, BASE, SOURCE, WORK = v4.ROOT, v4.CORPUS, v4.CORPUS_SHA, v4.CKPT, v4.BASE, v4.SOURCE, v4.WORK
GPU_RUNS_ROOT = WORK / "M22_GPU_RUNS"
GPU_QUOTA_ROOT = WORK / "M22_QUOTA_LEDGER"
STAGE = "A461_MON_M22_SECJEV_REPLICATION_GPU"
BLOB_MANIFEST = "c06d08ad1ebf9268bde44fc73ac21db0439ca542"
BLOB_DESIGN = "759a4c83a5f205d9c606094502a5be07a33792e4"
BLOB_STAGE_A_RAW = "680a78116e8099b19ef11298326587d7d8e76fd0"   # SecJev-0.8B Stage-A raw rows (bitwise anchors)
BLOB_ROSTER, BLOB_G5V2 = v4.BLOB_ROSTER, v4.BLOB_G5V2_PAIRS
FROZEN_BATCHES = [128, 128, 128, 128, 108]
FROZEN_TOTAL = 620
N_LAYERS = 24
HEAD_LAYER = 11
N_HEADS = 8
RESID_LAYERS = [3, 7, 11, 15, 19, 23]
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
    ap.add_argument("--stage-a-raw", required=True, type=Path)
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
        ck(out.parent == GPU_RUNS_ROOT.resolve(), "gpu run out dir must be a direct child of M22_GPU_RUNS")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    expect_batches = [int(x) for x in a.expect_batches.split(",")]
    receipt = {"schema": "JEV_A461_MON_M22_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": "A461_MON_M22_GPU_R1", "backend": a.backend,
               "expect_batches": expect_batches, "gpu_model_loads": 0, "model_loads": 0,
               "native_model_forward_calls": 0, "physical_prehook_calls": 0, "denied_prehook_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "batch_receipts": [], "output_dir": str(out),
               "stage_a_runner_v4_blob": V4_BLOB}
    produced = []
    raw_log = out / "raw_native_logits_m22.jsonl"
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
        pins = {"manifest_blob": BLOB_MANIFEST, "design_blob": BLOB_DESIGN, "stage_a_raw_blob": BLOB_STAGE_A_RAW,
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
               "gpu approval must be exactly 620 calls / [128, 128, 128, 128, 108]")
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
        ck(file_blob(a.stage_a_raw) == BLOB_STAGE_A_RAW, "Stage-A raw blob pin")
        ck(file_blob(a.design) == BLOB_DESIGN or a.backend == "fake", "design blob pin")
        rawA = {r["forward_index"]: r for r in jsonl(a.stage_a_raw)}
        design = json.loads(a.design.read_text("utf8"))
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
            ck(arm in ARMS and m["condition"] == f"monitor_capture_{arm}", f"arm {m['forward_index']}")
            ck(m["capture"]["resid_layers"] == RESID_LAYERS and m["capture"]["attn_layer"] == HEAD_LAYER
               and m["capture"]["decision_question"] == "certificate_action", f"capture spec {m['forward_index']}")
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
            ck(m["capture"]["span"] == m["span"] == x["span"] and 0 <= s0 < s1 <= len(ids), f"span {s[:8]}:{arm}")
            ck((s1 - s0 == SPAN_W) == (arm != "old"), f"span width {s[:8]}:{arm}")
            if m.get("anchor_stage_a_fi"):
                kr = rawA[m["anchor_stage_a_fi"]]
                ck(kr["scene_sha256"] == s and kr["arm"] == arm and kr["kind"] == "primary"
                   and kr["token_ids_sha256"] == m["token_ids_sha256"], f"Stage-A anchor ref {m['forward_index']}")
            else:
                ck(arm in ("ROUND", "OUTSIDER"), f"missing Stage-A anchor {m['forward_index']}")
            reqs[(s, arm)] = st
        receipt["preflight"] = {"scenes": len(need), "token_gate": "PASS", "span_gate": "PASS",
                                "manifest_rows": len(manifest)}
        if not full_run:
            receipt.update(status=("COMPLETE_A461_MON_M22_PRE_MODEL_GATE" if a.pre_model_gate_only
                                   else "COMPLETE_A461_MON_M22_PREFLIGHT"))
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
            from kev.checkpoint import Checkpoint, LoadOptions   # the SecJev Stage-A runner's load (g0_v4)
            checkpoint = Checkpoint(str(CKPT))
            checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
            _tok, model = checkpoint.load("cuda:0", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
            ck(model.lm.config.hidden_size == 1024, "SecJev-0.8B hidden size")
            receipt["secjev_load"] = {"cuda_max_memory_allocated_after_load": torch.cuda.max_memory_allocated()}
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
        attn = layer_mods[HEAD_LAYER].self_attn
        HD = attn.head_dim
        OPROJ_IN = attn.o_proj.in_features   # the fake model keeps 16 x 4; SecJev is 8 heads x 256 (checked on the GPU)
        ck(a.backend == "fake" or OPROJ_IN == N_HEADS * HD == 2048, "SecJev L11 o_proj input width")
        spec = {}           # active capture: s0, s1, end (decision position of the certificate_action row), row
        got = {}            # name -> captured tensors of the current forward
        fired = set()

        def take(name, h):
            # h: [rows, T, D]; span rows (all rows, to check they agree) and the decision-row last token
            s0, s1, row, end = spec["s0"], spec["s1"], spec["row"], spec["end"]
            sp = h[:, s0:s1, :].detach().float()
            got[name] = (sp.mean(dim=1).cpu(), float((sp - sp[:1]).abs().max()), h[row, end, :].detach().float().cpu())
            fired.add(name)

        def emb_pre(module, args, kwargs):
            if spec:
                take("emb", kwargs["hidden_states"] if "hidden_states" in kwargs else args[0])
            return None

        def layer_post(i):
            def fn(module, args, kwargs, output):
                if spec:
                    take(f"L{i}", output[0] if isinstance(output, tuple) else output)
                return None
            return fn

        def oproj_pre(module, args):
            if spec:
                x = args[0]
                ck(x.shape[-1] == OPROJ_IN, "o_proj input width")
                sp = x[:, spec["s0"]:spec["s1"], :].detach().float()
                got["attn11"] = (sp[0].cpu(), float((sp - sp[:1]).abs().max()))
                fired.add("attn11")
            return None

        hooks += [layer_mods[0].register_forward_pre_hook(emb_pre, with_kwargs=True),
                  attn.o_proj.register_forward_pre_hook(oproj_pre)]
        hooks += [layer_mods[i].register_forward_hook(layer_post(i), with_kwargs=True) for i in RESID_LAYERS]
        NAMES = ["emb"] + [f"L{i}" for i in RESID_LAYERS]

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
            spec.clear()
            got.clear()
            fired.clear()
            s0, s1 = m["span"]
            spec.update(s0=s0, s1=s1, row=row, end=S_len + br_len[row] - 1)
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
                ck(fired == set(NAMES) | {"attn11"}, f"capture hooks fired {sorted(fired)}")
                span_mean = torch.stack([got[n][0][0] for n in NAMES])          # [layers, D] (row 0)
                last = torch.stack([got[n][2] for n in NAMES])                  # [layers, D]
                xrow = max([got[n][1] for n in NAMES] + [got["attn11"][1]])
                cf = out / "captures" / f"{m['target_arm']}_{m['target_scene'][:12]}_m22.pt"
                with cf.open("xb") as fh:
                    torch.save({"names": NAMES, "span_mean": span_mean, "last": last,
                                "attn11_span": got["attn11"][0].to(torch.float16)}, fh)
                    fh.flush()
                    os.fsync(fh.fileno())
                row_ = dict(att, target_scene=m["target_scene"], target_arm=m["target_arm"],
                            source_group=m["source_group"], gold_action=m["gold_action"], span=m["span"],
                            decision_position=spec["end"], decision_row=row, conflicting_vote_branch_index=c_idx,
                            cross_row_max_absdiff=xrow,
                            capture_file={"name": cf.name, "sha256": sha_file(cf), "names": NAMES,
                                          "span_mean_shape": list(span_mean.shape),
                                          "attn11_span_shape": list(got["attn11"][0].shape)},
                            questions=qs, M=c_margin(qs), token_ids_sha256=hids(enc["ids"]),
                            state_len=len(enc["ids"][:S_len]))
                canon(row_)
            except Exception as err:
                append_line(attempt_log, dict(att, status="INVALID_OUTPUT", error_type=type(err).__name__,
                                              error_message=str(err)[:200]), sync=True)
                raise
            append_line(raw_log, row_, sync=True)
            if m.get("anchor_stage_a_fi") and a.backend == "gpu":
                kr = rawA[m["anchor_stage_a_fi"]]
                ck(all(x["logits"] == y["logits"] for x, y in zip(kr["questions"], qs)),
                   f"not bitwise == Stage-A forward {m['anchor_stage_a_fi']}")
                ck(xrow == 0.0, f"span features differ across rows at {m['forward_index']}")
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
        produced.append("raw_native_logits_m22.jsonl")
        produced += sorted("captures/" + p.name for p in (out / "captures").iterdir())
        if attempt_log.exists():
            produced.append("attempt_receipts.jsonl")
        receipt.update(status="COMPLETE_A461_MON_M22", physical_forwards=physical[0],
                       elapsed_seconds=round(time.time() - t0, 3),
                       bitwise_vs_stage_a="checked" if a.backend == "gpu" else "not_applicable_fake_backend")
        code = 0
    except SystemExit as stop:
        code = int(stop.code or 0)
    except Exception as err:
        import traceback
        for n_, p_ in (("raw_native_logits_m22.jsonl", raw_log), ("attempt_receipts.jsonl", attempt_log)):
            if p_.exists() and n_ not in produced:
                produced.append(n_)
        receipt["physical_by_batch_at_failure"] = {str(k): v for k, v in physical_by_batch.items() if k}
        for br in receipt.get("batch_receipts", []):
            if br["status"] == "IN_PROGRESS":
                br["status"] = "FAILED_AT_THIS_BATCH"
                br["physical"] = physical_by_batch.get(br["run"], 0)
        receipt.update(status="FAIL_A461_MON_M22", error_type=type(err).__name__, error_message=str(err),
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
    receipt["durable_appends"] = {"raw_rows": v4.DURABLE["raw_native_logits_m22.jsonl"],
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
