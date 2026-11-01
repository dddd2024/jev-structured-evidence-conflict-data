#!/usr/bin/env python3
"""A461-G5-G2 Stage-E GPU runner V1: action-level repair (per-row span patching).

Executes the frozen Stage-E manifest (G2_STAGE_E_FREEZE_R1, 304 calls in
[88, 72, 72, 72]). Captures store the appended span from EVERY question row
(kev row form: each question is its own causal row) at all 24 layer outputs;
patches overwrite the host's own new span in the certificate_action row only
(scope "action") or in every question row (scope "all"), each row with the
same row's source span; dose-matched random per row and position. Derived
from the Stage-D runner (5ba88abb, used for the real Stage-D run); same
imported Stage-A V4 safety module and policy V2 admission route. Zero
backprop, zero network, outputs only under ~/wjc.
"""
import argparse, collections, gzip, hashlib, importlib.util, json, math, os, subprocess, sys, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
V4_PATH = HERE / "A461_g5_g2_stage_a_gpu_screen_runner_g0_v4.py"
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
GPU_RUNS_ROOT = WORK / "G2_STAGE_E_GPU_RUNS"
GPU_QUOTA_ROOT = WORK / "G2_STAGE_E_QUOTA_LEDGER"
STAGE = "A461_G5_G2_STAGE_E_ACTION_REPAIR_GPU"
BLOB_MANIFEST = "aa8c77b71064299b19050ad49d28b360b9e1b48b"
BLOB_DESIGN = "af68448c27ebbb04a59a8691d4b6c23447fdf6b0"
BLOB_STAGE_A_RAW = "680a78116e8099b19ef11298326587d7d8e76fd0"
BLOB_STAGE_B_RAW = "801c4a0eb790cf37db3a83018be178dda97bd28e"
BLOB_ROSTER, BLOB_G5V2 = v4.BLOB_ROSTER, v4.BLOB_G5V2_PAIRS
FROZEN_BATCHES = [88, 72, 72, 72]
FROZEN_TOTAL = 304
LAYERS = tuple(range(24))        # capture hooks on every layer output
PATCH_LAYERS = (11, 12)


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def c_margin(questions):
    c = next(q for q in questions if q["id"] == "conflicting_vote")
    return c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]


def transform(states, patch, target=None):
    """Apply the frozen control transform to a [W, D] float32 CPU tensor.
    deltarand: target_i + u_i * ||states_i - target_i|| (u_i seeded unit Gaussian)."""
    import torch
    tr = patch["transform"]
    if tr == "none":
        return states
    if tr == "deltarand":
        ck(target is not None and target.shape == states.shape, "deltarand needs the target span")
        g = torch.Generator().manual_seed(int(patch["seed"]))
        u = torch.randn(states.shape, generator=g, dtype=torch.float32)
        u = u / u.norm(dim=-1, keepdim=True)
        return target + u * (states - target).norm(dim=-1, keepdim=True)
    if tr == "permute":
        p = patch["perm"]
        ck(sorted(p) == list(range(states.shape[0])) and p != list(range(states.shape[0])), "frozen permutation")
        return states[p]
    ck(tr == "normrand", "unknown transform " + tr)
    g = torch.Generator().manual_seed(int(patch["seed"]))
    z = torch.randn(states.shape, generator=g, dtype=torch.float32)
    return z / z.norm(dim=-1, keepdim=True) * states.norm(dim=-1, keepdim=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--stage-b-raw", required=True, type=Path)
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
        ck(out.parent == GPU_RUNS_ROOT.resolve(), "gpu run out dir must be a direct child of G2_STAGE_E_GPU_RUNS")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    expect_batches = [int(x) for x in a.expect_batches.split(",")]
    receipt = {"schema": "JEV_A461_G5_G2_STAGE_E_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": "A461_G5_G2_STAGE_E_GPU_R1", "backend": a.backend,
               "expect_batches": expect_batches, "gpu_model_loads": 0, "model_loads": 0,
               "native_model_forward_calls": 0, "physical_prehook_calls": 0, "denied_prehook_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "batch_receipts": [], "output_dir": str(out),
               "stage_a_runner_v4_blob": V4_BLOB}
    produced = []
    raw_log = out / "raw_native_logits_stage_e.jsonl"
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
                "stage_b_raw_blob": BLOB_STAGE_B_RAW,
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
               "gpu approval must be exactly 304 calls / [88, 72, 72, 72]")
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
        ck(file_blob(a.stage_b_raw) == BLOB_STAGE_B_RAW, "Stage-B raw blob pin")
        stage_a = {r["forward_index"]: r for r in jsonl(a.stage_a_raw)}
        stage_b = {r["forward_index"]: r for r in jsonl(a.stage_b_raw)}
        manifest = jsonl(a.manifest)
        ck(len(manifest) == sum(expect_batches), "manifest length != plan")
        ck([m["forward_index"] for m in manifest] == list(range(1, len(manifest) + 1)), "forward_index not 1..N")
        caps_b = {k + 1: n for k, n in enumerate(expect_batches)}
        ck(dict(collections.Counter(m["run"] for m in manifest)) == caps_b, "run sizes != plan")
        ck([m["run"] for m in manifest] == sorted(m["run"] for m in manifest), "runs not contiguous")
        roster = {r["scene_sha256"]: r for r in json.loads(git_blob(repo, BLOB_ROSTER))["candidates"]}
        q_tw = json.loads(git_blob(repo, BLOB_G5V2).splitlines()[0])["native_request"]["questions"]
        state_by = {}
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    if rec["_meta"].get("source") == "twins_streamlet":
                        state_by[hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()] = rec["state"]
        from transformers import AutoTokenizer
        from kev.api import SystemOneRequest, to_record
        from kev.model import encode
        tok = AutoTokenizer.from_pretrained(str(BASE))

        def encode_state(state):
            rendered, meta = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
            enc = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
            ck(not enc["state_truncated"], "truncated state")
            return enc, meta

        reqs, spans = {}, {}
        for s in sorted({m["target_scene"] for m in manifest}):
            r = roster[s]
            st_old = state_by[s]
            st = {"old": st_old}
            for arm, key in (("new", "declared_edit_new"), ("SA", "declared_edit_sa")):
                st[arm] = json.loads(canon(st_old))
                st[arm]["received_messages"].append(dict(r[key]["message"]))
            o_ids = None
            for arm in ("old", "new", "SA"):
                enc, _meta = encode_state(st[arm])
                ck(hids(enc["ids"]) == r["token_ids_sha256"][arm], f"token gate {s[:8]}:{arm}")
                ids = enc["ids"][:enc["seg"].count(0)]
                ck(len(ids) == r["state_token_len"][arm], f"state length {s[:8]}:{arm}")
                reqs[(s, arm)] = st[arm]
                if arm == "old":
                    o_ids = ids
                else:
                    z = 0
                    while z < min(len(o_ids), len(ids)) and o_ids[z] == ids[z]:
                        z += 1
                    W = r["frozen_width"]   # per-scene frozen witness width (31 or 34)
                    ck(len(ids) - len(o_ids) == W and ids[z + W:] == o_ids[z:], f"span anchor {s[:8]}:{arm}")
                    spans[(s, arm)] = [z, z + W]
        cap_tags = set()
        for m in manifest:
            for key in ("capture", "patch"):
                if m.get(key):
                    ck(m[key]["span"] == spans[(m["target_scene"], m["target_arm"])], f"manifest span {m['forward_index']}")
            if m.get("capture"):
                cap_tags.add(m["capture"]["tag"])
            if m.get("patch"):
                ck(m["patch"]["layer"] in PATCH_LAYERS, "patch layer")
                for t in (m["patch"]["source"], m["patch"].get("delta_target")):
                    ck(t is None or t in cap_tags, f"patch source not captured earlier at {m['forward_index']}")
            if m.get("bitwise_vs_stage_a"):
                sa = stage_a[m["bitwise_vs_stage_a"]]
                ck(sa["scene_sha256"] == m["target_scene"] and sa["arm"] == m["target_arm"], "Stage-A baseline ref")
            if m.get("bitwise_vs_stage_b"):
                sb = stage_b[m["bitwise_vs_stage_b"]]
                ck(sb["condition"] == m["condition"] and sb["layer"] == 11 and sb["donor"] == m["donor"]
                   and sb["host"] == m["host"], "Stage-B replication ref")
        needed = {(t, L) for m in manifest if m.get("patch") for t in (m["patch"]["source"], m["patch"].get("delta_target"))
                  if t for L in [m["patch"]["layer"]]} | {(f"{m['target_arm']}:{m['target_scene'][:12]}", m["patch"]["layer"])
                                                         for m in manifest if m.get("patch")}
        receipt["preflight"] = {"scenes": len({m["target_scene"] for m in manifest}), "token_gate": "PASS",
                                "span_gate": "PASS", "manifest_rows": len(manifest)}
        if not full_run:
            receipt.update(status=("COMPLETE_A461_G5_G2_STAGE_E_PRE_MODEL_GATE" if a.pre_model_gate_only
                                   else "COMPLETE_A461_G5_G2_STAGE_E_PREFLIGHT"))
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
            from A461_g5_g2_fake_patch_model_v1 import FakePatchModel
            model = FakePatchModel()
            receipt["fake_model_fault"] = model.fault
        else:
            torch.set_num_threads(4)
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            torch.backends.cuda.enable_flash_sdp(False)
            torch.backends.cuda.enable_mem_efficient_sdp(False)
            from kev.checkpoint import Checkpoint, LoadOptions
            checkpoint = Checkpoint(str(CKPT))
            checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
            _tok, model = checkpoint.load("cuda:0", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
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
        cap_spec = {}       # active capture: tag, c_idx, s0, s1
        caps = {}           # (tag, layer) -> [W, D] float32 CPU
        patch_spec = {}     # layer -> (patched rows, s0, s1, states [rows, W, D])
        fired = set()

        def make_hook(L):
            def hook(module, args, output):
                h, rest = (output[0], output[1:]) if isinstance(output, tuple) else (output, ())
                if cap_spec:
                    # every question row's copy of the span: [rows, W, D]
                    cap_spec["layers"][L] = h[:, cap_spec["s0"]:cap_spec["s1"], :].detach().float().cpu().clone()
                    fired.add(("capture", L))
                if L in patch_spec:
                    prow, s0, s1, states = patch_spec[L]
                    ck(states.shape == (len(prow), s1 - s0, h.shape[2]), "patch state shape")
                    h = h.clone()
                    h[torch.tensor(prow, device=h.device), s0:s1, :] = states.to(device=h.device, dtype=h.dtype)
                    fired.add(("patch", L))
                    output = (h,) + rest if rest else h
                return output
            return hook
        layer_mods = model.lm.base_model.model.layers
        hooks += [layer_mods[L].register_forward_hook(make_hook(L)) for L in LAYERS]

        def span_stats(src, tgt):
            cos = torch.nn.functional.cosine_similarity(src, tgt, dim=-1)
            return {"src_norm_mean": round(float(src.norm(dim=-1).mean()), 6),
                    "tgt_norm_mean": round(float(tgt.norm(dim=-1).mean()), 6),
                    "cos_mean": round(float(cos.mean()), 6),
                    "delta_norm_mean": round(float((src - tgt).norm(dim=-1).mean()), 6)}

        rows_by_cond = collections.defaultdict(dict)

        def run_entry(m):
            b = m["run"]
            ck(current[0] == b and receipt["native_model_forward_calls"] + 1 == m["forward_index"], "order")
            v4.batch_guard(physical_by_batch.get(b, 0), caps_b[b])
            ck(physical[0] == receipt["native_model_forward_calls"] == reserved[0], "ledger drift")
            ck(consumed_total[0] + 1 <= approved_max, "global budget")
            enc, meta = encode_state(reqs[(m["target_scene"], m["target_arm"])])
            c_idx = [q["id"] for q in meta].index("conflicting_vote")
            state_len = len(enc["ids"][:enc["seg"].count(0)])
            cap_spec.clear()
            patch_spec.clear()
            fired.clear()
            stats = None
            if m.get("capture"):
                s0, s1 = m["capture"]["span"]
                ck(s1 <= state_len, "capture overhang")
                cap_spec.update(tag=m["capture"]["tag"], c_idx=c_idx, s0=s0, s1=s1, layers={})
            if m.get("patch"):
                p = m["patch"]
                s0, s1 = p["span"]
                ck(0 <= s0 < s1 <= state_len and p["layer"] in PATCH_LAYERS, "patch bounds/layer")
                tgt_tag = f"{m['target_arm']}:{m['target_scene'][:12]}"
                qids = [q["id"] for q in meta]
                prow = [qids.index("certificate_action")] if p["rows"] == "action" else list(range(len(qids)))
                tgt = caps[(tgt_tag, p["layer"])][prow]
                states = transform(caps[(p["source"], p["layer"])][prow], p, target=tgt)
                stats = span_stats(states, tgt)
                patch_spec[p["layer"]] = (prow, s0, s1, states)
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
                # everything between a returned forward and its durable raw row is
                # guarded: a failure here still leaves an attempt row for the call
                ck(len(z) == len(meta) == 4, "branch count")
                raw = [[float(x) for x in (zz.detach().float().cpu().tolist())] for zz in z]
                ck(all(len(v) == len(q["keys"]) and all(math.isfinite(x) for x in v) for v, q in zip(raw, meta)),
                   "invalid logits")
                qs = [{"id": q["id"], "keys": list(q["keys"]), "logits": v} for q, v in zip(meta, raw)]
                row = dict(att, target_scene=m["target_scene"], target_arm=m["target_arm"],
                           direction=m.get("direction"), scope=m.get("scope"), donor=m.get("donor"), host=m.get("host"), layer=m.get("layer"),
                           patch=m.get("patch") and {k: m["patch"].get(k) for k in
                                                     ("layer", "span", "source", "transform", "seed", "rows")},
                           capture=m.get("capture"), span_stats=stats, conflicting_vote_branch_index=c_idx,
                           capture_file=None,
                           questions=qs, M=c_margin(qs), token_ids_sha256=hids(enc["ids"]), state_len=state_len)
                canon(row)
            except Exception as err:
                append_line(attempt_log, dict(att, status="INVALID_OUTPUT", error_type=type(err).__name__,
                                              error_message=str(err)[:200]), sync=True)
                raise
            if m.get("capture"):
                ck(len(cap_spec["layers"]) == len(LAYERS), f"capture hooks fired on {len(cap_spec['layers'])} layers")
                stack = torch.stack([cap_spec["layers"][L] for L in LAYERS])
                cf = out / "captures" / (m["capture"]["tag"].replace(":", "_") + ".pt")
                with cf.open("xb") as fh:
                    torch.save(stack.to(torch.float16), fh)
                    fh.flush()
                    os.fsync(fh.fileno())
                row["cross_row_max_absdiff"] = float((stack - stack[:, :1]).abs().max())
                row["capture_file"] = {"name": cf.name, "sha256": sha_file(cf), "shape": list(stack.shape),
                                       "dtype": "float16"}
                for L in LAYERS:
                    if (m["capture"]["tag"], L) in needed:
                        caps[(m["capture"]["tag"], L)] = cap_spec["layers"][L]
            append_line(raw_log, row, sync=True)
            # post-forward gates (row already durable)
            if m.get("patch"):
                ck(("patch", m["patch"]["layer"]) in fired, f"patch hook did not fire at {m['forward_index']}")
            if m.get("capture"):
                ck(all(("capture", L) in fired for L in LAYERS), f"capture hook did not fire at {m['forward_index']}")
            if m.get("bitwise_vs_stage_a") and a.backend == "gpu":
                sa = stage_a[m["bitwise_vs_stage_a"]]
                ck(all(x["logits"] == y["logits"] for x, y in zip(sa["questions"], qs)),
                   f"baseline not bitwise == Stage-A forward {m['bitwise_vs_stage_a']}")
            if m.get("bitwise_vs_stage_b") and a.backend == "gpu":
                sb = stage_b[m["bitwise_vs_stage_b"]]
                ck(all(x["logits"] == y["logits"] for x, y in zip(sb["questions"], qs)),
                   f"L11 patch not bitwise == Stage-B forward {m['bitwise_vs_stage_b']}")
            rows_by_cond[m["condition"]][m["target_scene"]] = row
            return row

        t0 = time.time()
        receipt["batch_receipts"] = [{"run": k, "planned": caps_b[k], "status": "NOT_STARTED", "physical": 0}
                                     for k in sorted(caps_b)]
        for br in receipt["batch_receipts"]:
            b = br["run"]
            current[0] = b
            physical_by_batch[b] = 0
            rows_by_cond.clear()
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
        produced.append("raw_native_logits_stage_e.jsonl")
        produced += sorted("captures/" + p.name for p in (out / "captures").iterdir())
        if attempt_log.exists():
            produced.append("attempt_receipts.jsonl")
        receipt.update(status="COMPLETE_A461_G5_G2_STAGE_E", physical_forwards=physical[0],
                       elapsed_seconds=round(time.time() - t0, 3),
                       bitwise_vs_stage_a_and_b="checked" if a.backend == "gpu" else "not_applicable_fake_backend")
        code = 0
    except SystemExit as stop:
        code = int(stop.code or 0)
    except Exception as err:
        import traceback
        for n_, p_ in (("raw_native_logits_stage_e.jsonl", raw_log), ("attempt_receipts.jsonl", attempt_log)):
            if p_.exists() and n_ not in produced:
                produced.append(n_)
        receipt["physical_by_batch_at_failure"] = {str(k): v for k, v in physical_by_batch.items() if k}
        for br in receipt.get("batch_receipts", []):
            if br["status"] == "IN_PROGRESS":
                br["status"] = "FAILED_AT_THIS_BATCH"
                br["physical"] = physical_by_batch.get(br["run"], 0)
        receipt.update(status="FAIL_A461_G5_G2_STAGE_E", error_type=type(err).__name__, error_message=str(err),
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
    receipt["durable_appends"] = {"raw_rows": v4.DURABLE["raw_native_logits_stage_e.jsonl"],
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
