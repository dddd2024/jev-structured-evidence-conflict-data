#!/usr/bin/env python3
"""A461-MECH-M7 R1 runner: delta-basis, mean-difference and round-contrast tests of the L11 BULK write of kev-4B.

Executes the frozen M7 manifest (2748 calls in 21 x 128 + 60; freeze A461_mech_m7_freeze_v1.py): the M4-M6
captures (L11 o_proj input at the append span and its exact split into key-class contributions, checked to sum to
it; readouts bitwise == M1 where M1 has one), then all-row span patches of host new: full (the M3 all-heads patch,
bitwise == M3), meanD_host (the M6 pooled-donor arm, bitwise == M6), dlr_k (host + alpha U_k U_k^T delta_B, U_k
from the other donors' differences to the same host), lr64_sm (the M6 raw basis, rescaled), rand64_sm (a seeded
random 64-subspace rescaled to ||delta_B||), and mean-difference arms (host + scale * (mean of a pool's BULK - mean
of another pool's BULK); mdir and the round-contrast arms rcH / rcD). Rescaled arms: alpha = min(||delta_B|| /
||projection||, 10) per row and span position, with a fail-closed size gate. Derived from the M6 runner (79c10a67)
by checked substitutions: same pre-hook gate, durable quota ledger, batch caps and fail-closed paths. Standing GPU
authorization (policy V2). Zero backprop, zero network, outputs only under ~/wjc.
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
GPU_RUNS_ROOT = WORK / "M7_GPU_RUNS"
GPU_QUOTA_ROOT = WORK / "M7_QUOTA_LEDGER"
STAGE = "A461_MECH_M7_DELTA_BASIS_MEANDIFF_GPU"
BLOB_MANIFEST = "17ee5d66a9c28f91d6c8d7abfc5b4bb3e2c53f6a"
BLOB_DESIGN = "f7d5318c1bfe24521831cc322be08bd6ed08fa17"
BLOB_M1_RAW = "298c7cdfab634cd6a6a9122fac90d41c87219c21"   # M1 raw rows (bitwise replay source)
BLOB_G10_CF = "06ee06d7942b9f1a5f09c35777d5da1149655e4d"   # G1.0 single-field variants
BLOB_M3_RAW = "a8c0fa6b5d96be7c7ab0433d4dcbb5d6f0411a0c"   # M3 raw rows (bitwise anchor of the full arm)
BLOB_M6_RAW = "2147311c2cf913fad5b07033e43789bb61293611"   # M6 raw rows (bitwise anchor of the meanD_host arm)
BLOB_ROSTER, BLOB_G5V2 = v4.BLOB_ROSTER, v4.BLOB_G5V2_PAIRS
FROZEN_BATCHES = [128] * 21 + [60]
FROZEN_TOTAL = 2748
N_LAYERS = 32
HEAD_LAYER = 11                  # Qwen3.5 full attention (M2: MIXER_WRITER at L11)
N_HEADS, N_KV = 16, 4            # query heads; KV groups (repeat_interleave: head h reads KV head h // 4)
BASE_CLASSES = ("PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT")
PARTNER_W = 33                   # every scene's partner item is 33 tokens
BULK = ["OTHER_ITEMS", "CONTEXT"]
OPS = ("full", "pool", "lowrank", "dlowrank", "randsub", "meandiff")
MAX_K = 64                       # largest frozen subspace rank
ALPHA_CAP = 10.0                 # largest rescaling of a projection to ||delta_B||

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
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--g10-cf", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m6-raw", required=True, type=Path)
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
        ck(out.parent == GPU_RUNS_ROOT.resolve(), "gpu run out dir must be a direct child of M7_GPU_RUNS")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    expect_batches = [int(x) for x in a.expect_batches.split(",")]
    receipt = {"schema": "JEV_A461_MECH_M7_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": "A461_MECH_M7_GPU_R1", "backend": a.backend,
               "expect_batches": expect_batches, "gpu_model_loads": 0, "model_loads": 0,
               "native_model_forward_calls": 0, "physical_prehook_calls": 0, "denied_prehook_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "batch_receipts": [], "output_dir": str(out),
               "stage_a_runner_v4_blob": V4_BLOB}
    produced = []
    raw_log = out / "raw_native_logits_m7.jsonl"
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
        pins = {"manifest_blob": BLOB_MANIFEST, "design_blob": BLOB_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                "g10_counterfactuals_blob": BLOB_G10_CF,
                "m3_raw_blob": BLOB_M3_RAW, "m6_raw_blob": BLOB_M6_RAW, "roster_blob": BLOB_ROSTER, "g5v2_questions_blob": BLOB_G5V2, "corpus_sha256": CORPUS_SHA}
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
               "gpu approval must be exactly 2748 calls / 21 x 128 + 60")
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
        ck(file_blob(a.m1_raw) == BLOB_M1_RAW, "M1 raw blob pin")
        ck(file_blob(a.g10_cf) == BLOB_G10_CF, "G1.0 counterfactuals blob pin")
        ck(file_blob(a.m3_raw) == BLOB_M3_RAW, "M3 raw blob pin")
        ck(file_blob(a.m6_raw) == BLOB_M6_RAW, "M6 raw blob pin")
        m3_raw = {r["forward_index"]: r for r in jsonl(a.m3_raw)}
        m6_raw = {r["forward_index"]: r for r in jsonl(a.m6_raw)}
        m1_raw = {r["forward_index"]: r for r in jsonl(a.m1_raw)}
        g10 = json.loads(a.g10_cf.read_text("utf8"))
        variant_key = {"ROUND": "ROUND", "OKALT": "OK_ALT"}
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
            for arm in sorted({m["target_arm"] for m in manifest if m["target_scene"] == s} & set(variant_key)):
                v = g10[s][variant_key[arm]]
                ck(v["ok"] and v["message"] == dict(r["declared_edit_new"]["message"], **{v["field"]: v["value"]}),
                   f"variant differs from the frozen message in more than one field {s[:8]}:{arm}")
                st_v = json.loads(canon(st_old))
                st_v["received_messages"].append(dict(v["message"]))
                enc, _meta = encode_state(st_v)
                ck(hids(enc["ids"]) == v["token_ids_sha256"], f"token gate {s[:8]}:{arm}")
                ids = enc["ids"][:enc["seg"].count(0)]
                W = r["frozen_width"]
                s0, s1 = v["span"]
                ck(s1 - s0 == W and len(ids) - len(o_ids) == W and ids[:s0] == o_ids[:s0] and ids[s1:] == o_ids[s0:],
                   f"span anchor {s[:8]}:{arm}")
                reqs[(s, arm)] = st_v
                spans[(s, arm)] = [s0, s1]
        cap_tags = set()
        for m in manifest:
            for key in ("capture", "patch"):
                if m.get(key):
                    ck(m[key]["span"] == spans[(m["target_scene"], m["target_arm"])], f"manifest span {m['forward_index']}")
            if m.get("capture"):
                c = m["capture"]
                s0, s1 = c["span"]
                ck(c["tag"] == f"{m['target_arm']}:{m['target_scene'][:12]}" and sorted(c["classes"]) == sorted(BASE_CLASSES)
                   and c["classes"]["SELF"] == [[s0, s1]] and c["classes"]["PARTNER"] == [c["partner"]]
                   and c["partner"][1] - c["partner"][0] == PARTNER_W and c["partner"][1] <= s0,
                   f"capture classes {m['forward_index']}")
                cover = sorted(k for v in c["classes"].values() for lo, hi in v for k in range(lo, hi))
                ck(cover == list(range(s1)), f"classes do not partition the keys < span end at {m['forward_index']}")
                cap_tags.add(c["tag"])
            if m.get("patch"):
                p = m["patch"]
                tags_ok = lambda v: bool(v) and set(v) <= cap_tags
                ck(p["layer"] == HEAD_LAYER and p["op"] in OPS
                   and set(p["classes"]) <= set(BASE_CLASSES) and (p["op"] == "full") == (not p["classes"])
                   and (p["op"] == "full" or p["classes"] == BULK)
                   and (p["op"] != "pool" or (p.get("base") in ("target", "source") and tags_ok(p.get("pool"))
                                              and len(set(p["pool"])) == len(p["pool"])))
                   and (p["op"] not in ("lowrank", "dlowrank", "randsub")
                        or (isinstance(p.get("k"), int) and 1 <= p["k"] <= MAX_K and p.get("rescale") in (None, "delta")))
                   and (p["op"] != "lowrank" or tags_ok(p.get("basis_pool")))
                   and (p["op"] != "dlowrank" or (p.get("basis_pairs") and all(
                       len(q_) == 2 and tags_ok(q_) and q_[0].split(":")[0] == q_[1].split(":")[0]
                       and q_[1].split(":")[1] == p["target"].split(":")[1] for q_ in p["basis_pairs"])))
                   and (p["op"] != "randsub" or (isinstance(p.get("seed"), int) and p.get("rescale") == "delta"))
                   and (p["op"] != "meandiff" or (tags_ok(p.get("plus")) and tags_ok(p.get("minus"))
                                                  and isinstance(p.get("scale"), float))), "patch op/classes")
                ck(p["target"] == f"{m['target_arm']}:{m['target_scene'][:12]}" and m["target_arm"] == "new",
                   f"patch target {m['forward_index']}")
                ck(p["source"] in cap_tags and p["target"] in cap_tags,
                   f"patch source/target not captured earlier at {m['forward_index']}")
            if m.get("bitwise_vs_m3"):
                kr = m3_raw[m["bitwise_vs_m3"]]
                ck(m["patch"]["op"] == "full" and kr["patch"]["arm"] == "all" and kr["donor"] == m["donor"]
                   and kr["host"] == m["host"] and kr["source_kind"] == m["source_kind"]
                   and kr["patch"]["source"] == m["patch"]["source"] and kr["patch"]["span"] == m["patch"]["span"],
                   f"M3 replay ref {m['forward_index']}")
            if m.get("bitwise_vs_m6"):
                kr = m6_raw[m["bitwise_vs_m6"]]
                ck(m["patch"]["op"] == "pool" and kr["patch"]["arm"] == "meanD_host" and kr["donor"] == m["donor"]
                   and kr["host"] == m["host"] and kr["source_kind"] == m["source_kind"]
                   and all(kr["patch"][k_] == m["patch"][k_] for k_ in ("source", "target", "span", "base", "pool")),
                   f"M6 replay ref {m['forward_index']}")
            if m.get("bitwise_vs_m1"):
                kr = m1_raw[m["bitwise_vs_m1"]]
                ck(m.get("capture") and kr["target_scene"] == m["target_scene"] and kr["target_arm"] == m["target_arm"]
                   and kr["condition"] == m["condition"] and kr["capture"]["span"] == m["capture"]["span"],
                   f"M1 replay ref {m['forward_index']}")
        needed = {t for m in manifest if m.get("patch")
                  for t in ([m["patch"]["source"], m["patch"]["target"]] + m["patch"].get("pool", [])
                            + m["patch"].get("basis_pool", []) + [u for q_ in m["patch"].get("basis_pairs", []) for u in q_]
                            + m["patch"].get("plus", []) + m["patch"].get("minus", [])) if t}
        cap_classes = {m["capture"]["tag"]: m["capture"] for m in manifest if m.get("capture")}
        receipt["preflight"] = {"scenes": len({m["target_scene"] for m in manifest}), "token_gate": "PASS",
                                "span_gate": "PASS", "manifest_rows": len(manifest)}
        if not full_run:
            receipt.update(status=("COMPLETE_A461_MECH_M7_PRE_MODEL_GATE" if a.pre_model_gate_only
                                   else "COMPLETE_A461_MECH_M7_PREFLIGHT"))
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
        attn = layer_mods[HEAD_LAYER].self_attn
        HD = attn.head_dim
        ck(attn.num_key_value_groups == N_HEADS // N_KV and (a.backend == "fake" or HD == 256), "L11 attention shape")
        rope = sys.modules[type(attn).__module__].apply_rotary_pos_emb
        cap_spec = {}       # active capture: tag, s0, s1, x = o_proj input at the span, attn = (probs, reconstruction)
        caps = {}           # tag -> {"x", "c" (class -> contribution), "gate", "pP", "vP"}, float32 CPU
        patch_spec = {}     # "x" -> (patched rows, s0, s1, replacement o_proj input [rows, W, N_HEADS * HD])
        fired = set()

        def oproj_pre(module, args):
            x = args[0]
            ck(x.shape[-1] == N_HEADS * HD, "o_proj input width")
            if cap_spec:
                cap_spec["x"] = x[:, cap_spec["s0"]:cap_spec["s1"], :].detach().float().cpu().clone()
                fired.add("capture_x")
            if patch_spec:
                prow, s0, s1, src = patch_spec["x"]
                ck(src.shape == (len(prow), s1 - s0, x.shape[2]), "patch state shape")
                x = x.clone()
                rt = torch.tensor(prow, device=x.device)
                for h in range(N_HEADS):   # same per-head copies as the M3 all-heads arm (bitwise anchor)
                    x[rt, s0:s1, h * HD:(h + 1) * HD] = src[:, :, h * HD:(h + 1) * HD].to(device=x.device, dtype=x.dtype)
                fired.add("patch")
                return (x,) + tuple(args[1:])
            return None

        def attn_pre(module, args, kwargs):
            # side computation only: the forward's own q/k/v and output are untouched (the bitwise replays check it)
            if not cap_spec:
                return None
            hs = kwargs["hidden_states"] if "hidden_states" in kwargs else args[0]
            cos, sin = kwargs["position_embeddings"]
            s0, s1 = cap_spec["s0"], cap_spec["s1"]
            B, T, _ = hs.shape
            q, gate = torch.chunk(module.q_proj(hs).view(B, T, -1, HD * 2), 2, dim=-1)
            gate = gate.reshape(B, T, -1)
            q = module.q_norm(q.reshape(B, T, -1, HD)).transpose(1, 2)
            k = module.k_norm(module.k_proj(hs).view(B, T, -1, HD)).transpose(1, 2)
            v = module.v_proj(hs).view(B, T, -1, HD).transpose(1, 2)
            q, k = rope(q, k, cos, sin)
            k = k.repeat_interleave(module.num_key_value_groups, dim=1)[:, :, :s1].float()
            v = v.repeat_interleave(module.num_key_value_groups, dim=1)[:, :, :s1].float()
            sc = (q[:, :, s0:s1].float() @ k.transpose(-1, -2)) * module.scaling
            qpos = torch.arange(s0, s1, device=hs.device).view(-1, 1)
            sc = sc.masked_fill(torch.arange(s1, device=hs.device).view(1, -1) > qpos, float("-inf"))
            p = sc.softmax(-1)                                       # [rows, heads, span queries, keys < s1]
            g = torch.sigmoid(gate[:, s0:s1].float())
            recon = (p @ v).transpose(1, 2).reshape(B, s1 - s0, -1) * g
            contrib = {}
            for cname, rr in cap_spec["classes"].items():
                mask = torch.zeros(s1, device=hs.device, dtype=p.dtype)
                for lo, hi in rr:
                    mask[lo:hi] = 1
                contrib[cname] = ((p * mask) @ v).transpose(1, 2).reshape(B, s1 - s0, -1) * g
            plo, phi = cap_spec["partner"]
            v_kv = module.v_proj(hs).view(B, T, -1, HD).transpose(1, 2)[:, :, plo:phi].float()   # [rows, KV, 33, HD]
            cap_spec["attn"] = (p.cpu(), recon.cpu(), {k: t.cpu() for k, t in contrib.items()}, g.cpu(),
                                p[:, :, :, plo:phi].cpu(), v_kv.cpu())
            fired.add("capture_attn")
            return None

        hooks += [attn.register_forward_pre_hook(attn_pre, with_kwargs=True),
                  attn.o_proj.register_forward_pre_hook(oproj_pre)]

        def span_stats(src, tgt):
            cos = torch.nn.functional.cosine_similarity(src, tgt, dim=-1)
            return {"src_norm_mean": round(float(src.norm(dim=-1).mean()), 6),
                    "tgt_norm_mean": round(float(tgt.norm(dim=-1).mean()), 6),
                    "cos_mean": round(float(cos.mean()), 6),
                    "delta_norm_mean": round(float((src - tgt).norm(dim=-1).mean()), 6)}

        rows_by_cond = collections.defaultdict(dict)
        bases = {}          # basis key -> right singular vectors [D, max k] (float64) and singular values

        def bulk(tag, prow):
            return sum(caps[tag]["c"][c][prow] for c in BULK)

        def basis(pool):
            key = tuple(pool)
            if key not in bases:
                X = torch.cat([bulk(t, [0])[0].double() for t in pool], dim=0)      # [len(pool) * W, D]
                _u, sv, vh = torch.linalg.svd(X, full_matrices=False)
                bases[key] = (vh[:MAX_K].T.contiguous(), sv)   # only the top MAX_K directions are used
            return bases[key]

        def dbasis(pairs):
            key = ("delta",) + tuple(tuple(q_) for q_ in pairs)
            if key not in bases:
                X = torch.cat([(bulk(u, [0]) - bulk(w, [0]))[0].double() for u, w in pairs], dim=0)   # [len * W, D]
                _u, sv, vh = torch.linalg.svd(X, full_matrices=False)
                bases[key] = (vh[:MAX_K].T.contiguous(), sv)
            return bases[key]

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
            alpha_stats = size_err = None
            if m.get("capture"):
                s0, s1 = m["capture"]["span"]
                ck(s1 <= state_len, "capture overhang")
                cap_spec.update(tag=m["capture"]["tag"], s0=s0, s1=s1, classes=m["capture"]["classes"],
                                partner=m["capture"]["partner"])
            if m.get("patch"):
                p = m["patch"]
                s0, s1 = p["span"]
                ck(0 <= s0 < s1 <= state_len and p["layer"] == HEAD_LAYER, "patch bounds/layer")
                qids = [q["id"] for q in meta]
                prow = [qids.index("certificate_action")] if p["rows"] == "action" else list(range(len(qids)))
                T_, S_ = caps[p["target"]], caps[p["source"]]
                tgt = T_["x"][prow]
                if p["op"] == "full":
                    states = S_["x"][prow].clone()
                elif p["op"] == "pool":
                    ck(p["classes"] == BULK, "pool arms average the BULK part")
                    B_ = T_ if p["base"] == "target" else S_
                    mean = sum(bulk(t, prow) for t in p["pool"]) / len(p["pool"])
                    states = B_["x"][prow] - bulk(p["target"] if p["base"] == "target" else p["source"], prow) + mean
                elif p["op"] == "meandiff":
                    ck(p["classes"] == BULK, "mean-difference arms use the BULK part")
                    vec = (sum(bulk(t, prow) for t in p["plus"]) / len(p["plus"])
                           - sum(bulk(t, prow) for t in p["minus"]) / len(p["minus"]))
                    states = T_["x"][prow] + float(p["scale"]) * vec
                else:   # lowrank / dlowrank / randsub: a k-dimensional part of delta_B
                    ck(p["classes"] == BULK, "subspace arms project delta_B")
                    k = p["k"]
                    dB = (bulk(p["source"], prow) - bulk(p["target"], prow)).double()
                    nd = dB.norm(dim=-1, keepdim=True)
                    if p["op"] == "randsub":
                        g_ = torch.Generator().manual_seed(int(p["seed"]))
                        Q, _r = torch.linalg.qr(torch.randn((dB.shape[-1], k), generator=g_, dtype=torch.float64))
                        pl = dB @ Q @ Q.T
                        nl = pl.norm(dim=-1, keepdim=True)
                        ck(bool((nl > 0).all()), "zero random-subspace projection")
                        alpha = nd / nl                      # exactly ||delta_B||, no cap
                        share = None
                    else:
                        V, sv = basis(p["basis_pool"]) if p["op"] == "lowrank" else dbasis(p["basis_pairs"])
                        ck(k <= V.shape[1], "k exceeds the basis rank")
                        U = V[:, :k]
                        pl = dB @ U @ U.T
                        nl = pl.norm(dim=-1, keepdim=True)
                        share = round(float((sv[:k] ** 2).sum() / (sv ** 2).sum()), 6)
                        if p["rescale"] == "delta":
                            alpha = torch.where(nl > 0, nd / nl.clamp_min(1e-300), torch.zeros_like(nl)).clamp(max=ALPHA_CAP)
                        else:
                            alpha = torch.ones_like(nl)
                    energy = nl / nd.clamp_min(1e-12)
                    alpha_stats = {"median": round(float(energy.median()), 6), "max": round(float(energy.max()), 6),
                                   "min": round(float(energy.min()), 6), "basis_sv_share_k": share,
                                   "alpha_median": round(float(alpha.median()), 6),
                                   "alpha_max": round(float(alpha.max()), 6),
                                   "capped_share": round(float((alpha >= ALPHA_CAP).double().mean()), 6)}
                    states = (T_["x"][prow].double() + pl * alpha).float()
                    if p["rescale"] == "delta":
                        want = nl * alpha
                        got = (states - T_["x"][prow]).double().norm(dim=-1, keepdim=True)
                        size_err = float(((got - want).abs() / want.clamp_min(1e-3)).max())
                        ck(size_err <= 1e-3, f"matched-size gate: relative size error {size_err}")
                ck(bool(torch.isfinite(states).all()), "non-finite patch state")
                stats = span_stats(states, tgt)
                patch_spec["x"] = (prow, s0, s1, states)
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
                           direction=m.get("direction"), scope=m.get("scope"), source_kind=m.get("source_kind"),
                           cross_group=m.get("cross_group"), donor=m.get("donor"), host=m.get("host"), layer=m.get("layer"),
                           patch=m.get("patch") and {k: m["patch"].get(k) for k in
                                                     ("layer", "arm", "op", "classes", "span", "source", "target", "seed",
                                                      "rows", "base", "pool", "k", "rescale", "basis_pool", "basis_pairs",
                                                      "plus", "minus", "scale")},
                           capture=m.get("capture"), span_stats=stats, conflicting_vote_branch_index=c_idx,
                           alpha_stats=alpha_stats, size_rel_err=size_err,
                           capture_file=None,
                           questions=qs, M=c_margin(qs), token_ids_sha256=hids(enc["ids"]), state_len=state_len)
                canon(row)
            except Exception as err:
                append_line(attempt_log, dict(att, status="INVALID_OUTPUT", error_type=type(err).__name__,
                                              error_message=str(err)[:200]), sync=True)
                raise
            if m.get("capture"):
                ck({"capture_x", "capture_attn"} <= fired and "x" in cap_spec and "attn" in cap_spec,
                   f"capture hooks did not fire at {m['forward_index']}")
                x = cap_spec["x"]
                probs, recon, contrib, g, pP, vP = cap_spec["attn"]
                scale = max(1.0, float(x.abs().max()))
                err = float((recon - x).abs().max())
                ck(err <= 1e-3 * scale, f"attention readout does not reconstruct the o_proj input (max abs {err})")
                add_err = float((sum(contrib.values()) - x).abs().max())
                ck(add_err <= 1e-3 * scale, f"class contributions do not sum to the o_proj input (max abs {add_err})")
                row["attn_readout_recon_maxabs"] = err
                row["class_additivity_maxabs"] = add_err
                row["class_contribution_norm_mean"] = {k: round(float(t[0].norm(dim=-1).mean()), 6) for k, t in contrib.items()}
                row["attn_cross_row_max_absdiff"] = float((probs - probs[:1]).abs().max())
                row["cross_row_max_absdiff"] = float((x - x[:1]).abs().max())
                stem = m["capture"]["tag"].replace(":", "_")
                cf = out / "captures" / (stem + "_oproj_in_L11.pt")
                with cf.open("xb") as fh:
                    torch.save(x.to(torch.float16), fh)
                    fh.flush()
                    os.fsync(fh.fileno())
                row["capture_file"] = {"name": cf.name, "sha256": sha_file(cf), "shape": list(x.shape),
                                       "dtype": "float16", "layer": HEAD_LAYER, "what": "o_proj input at the span"}
                kf = out / "captures" / (stem + "_classes_L11_row0.pt")
                with kf.open("xb") as fh:
                    torch.save({"contrib": {k: t[0].to(torch.float16) for k, t in contrib.items()},
                                "partner_values": vP[0].to(torch.float16), "partner_attention": pP[0].clone()}, fh)
                    fh.flush()
                    os.fsync(fh.fileno())
                row["class_file"] = {"name": kf.name, "sha256": sha_file(kf), "layer": HEAD_LAYER, "row": 0,
                                     "what": "per-class contributions [W, 4096] fp16, partner values [KV, 33, HD] "
                                             "fp16, span-to-partner attention [heads, W, 33] fp32"}
                if m["capture"]["tag"] in needed:
                    caps[m["capture"]["tag"]] = {"x": x, "c": contrib, "gate": g, "pP": pP, "vP": vP}
            append_line(raw_log, row, sync=True)
            # post-forward gates (row already durable)
            if m.get("patch"):
                ck("patch" in fired, f"patch hook did not fire at {m['forward_index']}")
            if m.get("capture"):
                ck({"capture_x", "capture_attn"} <= fired and "patch" not in fired,
                   f"capture hook did not fire at {m['forward_index']}")
            if m.get("bitwise_vs_m3") and a.backend == "gpu":
                kr = m3_raw[m["bitwise_vs_m3"]]
                ck(all(x["logits"] == y["logits"] for x, y in zip(kr["questions"], qs)),
                   f"not bitwise == M3 forward {m['bitwise_vs_m3']}")
            if m.get("bitwise_vs_m6") and a.backend == "gpu":
                kr = m6_raw[m["bitwise_vs_m6"]]
                ck(all(x["logits"] == y["logits"] for x, y in zip(kr["questions"], qs)),
                   f"not bitwise == M6 forward {m['bitwise_vs_m6']}")
            if m.get("bitwise_vs_m1") and a.backend == "gpu":
                kr = m1_raw[m["bitwise_vs_m1"]]
                ck(all(x["logits"] == y["logits"] for x, y in zip(kr["questions"], qs)),
                   f"not bitwise == M1 forward {m['bitwise_vs_m1']}")
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
        produced.append("raw_native_logits_m7.jsonl")
        produced += sorted("captures/" + p.name for p in (out / "captures").iterdir())
        if attempt_log.exists():
            produced.append("attempt_receipts.jsonl")
        receipt.update(status="COMPLETE_A461_MECH_M7", physical_forwards=physical[0],
                       elapsed_seconds=round(time.time() - t0, 3),
                       bitwise_vs_m1="checked" if a.backend == "gpu" else "not_applicable_fake_backend",
                       bitwise_vs_m3="checked" if a.backend == "gpu" else "not_applicable_fake_backend",
                       bitwise_vs_m6="checked" if a.backend == "gpu" else "not_applicable_fake_backend")
        code = 0
    except SystemExit as stop:
        code = int(stop.code or 0)
    except Exception as err:
        import traceback
        for n_, p_ in (("raw_native_logits_m7.jsonl", raw_log), ("attempt_receipts.jsonl", attempt_log)):
            if p_.exists() and n_ not in produced:
                produced.append(n_)
        receipt["physical_by_batch_at_failure"] = {str(k): v for k, v in physical_by_batch.items() if k}
        for br in receipt.get("batch_receipts", []):
            if br["status"] == "IN_PROGRESS":
                br["status"] = "FAILED_AT_THIS_BATCH"
                br["physical"] = physical_by_batch.get(br["run"], 0)
        receipt.update(status="FAIL_A461_MECH_M7", error_type=type(err).__name__, error_message=str(err),
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
    receipt["durable_appends"] = {"raw_rows": v4.DURABLE["raw_native_logits_m7.jsonl"],
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
