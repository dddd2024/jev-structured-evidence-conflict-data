#!/usr/bin/env python3
"""A461-G5 minimal causal patch pilot: GPU execution (G1), 28 native forwards.

HARD ADMISSION GATE: refuses to load the backbone unless the pilot admission
receipt carries BOTH (a) an independent blind-review verdict of exactly "PASS"
pinned to this runner's git blob, and (b) fresh explicit user GPU approval for
exactly 28 native forwards. CPU-side gates are re-verified here (input blobs,
corpus pin, roster logits, token ids parity, span anchors) before the single
model load. One model load, 28 native forwards, zero backprop, zero network,
outputs only under ~/wjc. Every forward appends its raw row to disk before the
next one starts (crash-safe ledger); a failure keeps all completed rows and
writes a FAIL receipt.

Physical plan (frozen; identical to pilot_execution_plan.jsonl from the CPU
closed loop): 3 donor captures (old at new-span coords, new, SA; layers 11+23
captured per forward) + 2 host SA unpatched baselines (bitwise-checked against
archived G1S V2 logits) + 2 host SA captures + 2 identity self-patches at layer
11 (bitwise-checked against the fresh baseline) + 4 restoration + 4 SA-sham
cross + 4 position-permuted + 2 host treatment captures + 1 donor new unpatched
baseline (bitwise-checked against archived) + 4 suppression = 28.
"""
import argparse, collections, gzip, hashlib, json, math, os, random, subprocess, sys, time
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"

BLOB_PAIR_ROWS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
BLOB_RAW_LOGITS = "13400252b360863a80baea66b39b9a7dbe0ca633"
BLOB_TOKEN_LENS = "5cf52a37f4e420da86c39fd537c40a98336c3be7"

DONOR_KEY = "T2_WAIT_TO_REJECT:433890d19a90625e"
HOST_KEYS = ["T2_WAIT_TO_REJECT:1b0e96fb22c6aebe", "T2_ACCEPT_TO_REJECT:231b919006dc1777"]
LAYERS = [11, 23]
IDENTITY_LAYER = 11
EXPECTED_WIDTH = 34
BUDGET = 28
HARD_CAP = 128
PERM_SEED = 20261025

# frozen condition sequence — must equal pilot_execution_plan.jsonl from the G0
# closed loop, position by position (28 entries)
FROZEN_CONDITIONS = (
    "capture_donor_old_at_new_span_coords", "capture_donor_new", "capture_donor_sa",
    "baseline_host_sa_unpatched", "baseline_host_sa_unpatched",
    "capture_host_sa", "capture_host_sa",
    "patch_identity_host_sa", "patch_identity_host_sa",
    "patch_restoration_donor_new_to_host_sa", "patch_restoration_donor_new_to_host_sa",
    "patch_restoration_donor_new_to_host_sa", "patch_restoration_donor_new_to_host_sa",
    "patch_sasham_donor_sa_to_host_sa", "patch_sasham_donor_sa_to_host_sa",
    "patch_sasham_donor_sa_to_host_sa", "patch_sasham_donor_sa_to_host_sa",
    "patch_permuted_donor_new_to_host_sa", "patch_permuted_donor_new_to_host_sa",
    "patch_permuted_donor_new_to_host_sa", "patch_permuted_donor_new_to_host_sa",
    "capture_host_new", "capture_host_new",
    "baseline_donor_new_unpatched",
    "patch_suppression_host_new_to_donor_new", "patch_suppression_host_new_to_donor_new",
    "patch_suppression_host_new_to_donor_new", "patch_suppression_host_new_to_donor_new",
)


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
    ck(t.returncode == 0 and t.stdout.strip() == "blob", f"not a blob in checkout: {sha}")
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
                    help="run the exact pre-model CPU path (admission shape, blob pins, gzip corpus, "
                         "roster logits, token parity, span anchors) and exit before any torch/CUDA/model load")
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(str(out).startswith(str(ROOT)) and out.parent.is_dir() and not out.exists(), "out dir")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    receipt = {"schema": "JEV_A461_G5_PILOT_GPU_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": "A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_GPU_R1",
               "gpu_model_loads": 0, "native_model_forward_calls": 0, "backprop_calls": 0,
               "network_calls": 0, "tool_actions": 0, "test_or_calibration_rows": 0,
               "output_dir": str(out)}
    produced = []
    raw_log = out / "raw_native_logits_pilot.jsonl"
    try:
        out.mkdir(mode=0o700)
        sys.path.insert(0, str(SOURCE))

        # ---------- hard admission gate (no model objects touched yet) ----------
        admit = json.loads(a.admission.read_text("utf8"))
        self_blob = subprocess.run(["git", "-C", str(repo), "hash-object", str(Path(__file__).resolve())],
                                   capture_output=True, text=True, check=True).stdout.strip()
        ck(admit.get("stage") == "A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_GPU", "wrong admission stage")
        ck(admit.get("approved_max_native_forwards") == BUDGET, f"approved != {BUDGET}")
        receipt["admission_fields_observed"] = {"blind_review_verdict": admit.get("blind_review_verdict"),
                                                "explicit_user_gpu_approval": admit.get("explicit_user_gpu_approval"),
                                                "blind_review_runner_blob": admit.get("blind_review_runner_blob"),
                                                "self_blob": self_blob}
        if a.preflight_only:
            # preflight verifies the source contract only; the GPU approval gates stay with the full run
            pass
        else:
            ck(admit.get("blind_review_verdict") == "PASS", "blind review has not PASSed")
            ck(admit.get("blind_review_runner_blob") == self_blob, "runner blob != reviewed blob")
            ck(admit.get("explicit_user_gpu_approval") is True, "no explicit user GPU approval")

        # ---------- CPU re-verification before any load ----------
        prows = [json.loads(x) for x in git_blob(repo, BLOB_PAIR_ROWS).splitlines() if x.strip()]
        prim = [json.loads(x) for x in git_blob(repo, BLOB_RAW_LOGITS).splitlines() if x.strip()
                and json.loads(x).get("kind") == "primary"]
        lens_doc = json.loads(git_blob(repo, BLOB_TOKEN_LENS))
        ck(len(prows) == 72 and len(prim) == 108, "input shapes")
        by_pair = collections.OrderedDict()
        for r in prows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        ck(len(by_pair) == 36, "pair census")
        state_by = {}
        n_twins = 0
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    ck(rec["_meta"].get("split") == "development", "non-DEV")
                    n_twins += 1
                    state_by[hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()[:16]] = rec["state"]
        ck(n_twins == 797, f"twins census {n_twins}")
        ck(DONOR_KEY.split(":", 1)[1] in state_by
           and all(k.split(":", 1)[1] in state_by for k in HOST_KEYS), "roster old states missing")
        arch_by_rowid = {r["plan_row"]: r for r in prim}

        def c_margin(row):
            c = next(q for q in row["questions"] if q["id"] == "conflicting_vote")
            return c["logits"][1] - c["logits"][0]

        donor_new_rowid = next(r["row_id"] for r in by_pair[DONOR_KEY] if r["arm"] == "new")
        ck(c_margin(arch_by_rowid[DONOR_KEY + ":old"]) < 0, "donor old archived not C=false")
        ck(c_margin(arch_by_rowid[donor_new_rowid]) > 0, "donor new archived not recognized")
        ck(c_margin(arch_by_rowid[next(r["row_id"] for r in by_pair[DONOR_KEY] if r["arm"] == "SA")]) < 0,
           "donor SA archived not C=false")
        for key in HOST_KEYS:
            ck(c_margin(arch_by_rowid[key + ":old"]) < 0, "host old not C=false " + key)
            for r in by_pair[key]:
                ck(c_margin(arch_by_rowid[r["row_id"]]) < 0, "host arm not C=false " + r["row_id"])

        import torch
        torch.set_num_threads(4)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        from transformers import AutoTokenizer
        from kev.api import SystemOneRequest, to_record
        from kev.model import encode
        tok = AutoTokenizer.from_pretrained(str(BASE))
        q_tw = prows[0]["native_request"]["questions"]
        ck(all(r["native_request"]["questions"] == q_tw for r in prows), "frozen questions shared")

        def encode_req(state):
            rendered, meta = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": canon_state(state)}))
            enc = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
            ck(not enc["state_truncated"], "truncated state")
            return enc, meta

        # token ids parity re-check on the 9 roster arms; requests keyed by the
        # ARCHIVED row id (old arms are "pair_key:old", new/SA arms are G5_XXXX)
        roster_reqs = {}
        for key in [DONOR_KEY] + HOST_KEYS:
            roster_reqs[key + ":old"] = {"questions": q_tw, "state": state_by[key.split(":", 1)[1]]}
            for r in by_pair[key]:
                roster_reqs[r["row_id"]] = r["native_request"]
        for rid, req in roster_reqs.items():
            enc, meta = encode_req(req["state"])
            ck(hids(enc["ids"]) == arch_by_rowid[rid]["token_ids_sha256"], "token parity " + rid)

        def arm_req(key, arm):
            return next(r["native_request"] for r in by_pair[key] if r["arm"] == arm)

        def arm_rowid(key, arm):
            return next(r["row_id"] for r in by_pair[key] if r["arm"] == arm)

        def old_req(key):
            return {"questions": q_tw, "state": state_by[key.split(":", 1)[1]]}

        # fresh span anchors (tokenizer only)
        spans = {}
        for key in [DONOR_KEY] + HOST_KEYS:
            enc_o, _ = encode_req(old_req(key)["state"])
            o_ids = enc_o["ids"][:enc_o["seg"].count(0)]
            for arm in ("new", "SA"):
                enc_a, _ = encode_req(arm_req(key, arm)["state"])
                a_ids = enc_a["ids"][:enc_a["seg"].count(0)]
                z = 0
                while z < min(len(o_ids), len(a_ids)) and o_ids[z] == a_ids[z]:
                    z += 1
                w = len(a_ids) - len(o_ids)
                ck(w == EXPECTED_WIDTH, "width " + key + ":" + arm)
                ck(a_ids[z + w:] == o_ids[z:], "trailing suffix " + key + ":" + arm)
                spans[(key, arm)] = (z, z + w)

        if a.preflight_only:
            receipt.update(status="COMPLETE_A461_G5_PILOT_PREFLIGHT",
                           corpus_path=str(CORPUS), twins_census=n_twins,
                           roster_old_state_sha256={k: hashlib.sha256(canon(state_by[k.split(":", 1)[1]]).encode("utf8")).hexdigest()
                                                    for k in [DONOR_KEY] + HOST_KEYS},
                           spans={f"{k[0]}:{k[1]}": list(v) for k, v in spans.items()},
                           native_model_forward_calls=0, model_loads=0,
                           note="preflight of the full-run code path before any torch CUDA/model load; "
                                "not a GPU admission")
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

        cap_tag = [None, None, None, None]   # [tag, c_idx, s0, s1] for the C-row capture
        caps = {}                            # (tag, layer) -> [w, D] states of the C row span
        patch_spec = {}                      # layer -> (c_idx, s0, s1, states)
        hook_applied = set()                 # layers whose patch branch actually fired

        def make_hook(L):
            def hook(module, args, output):
                if isinstance(output, tuple):
                    h, rest = output[0], output[1:]
                elif isinstance(output, torch.Tensor):
                    h, rest = output, ()
                else:
                    raise RuntimeError("unexpected layer output type " + str(type(output)))
                if cap_tag[0] is not None:
                    c_idx, s0, s1 = cap_tag[1], cap_tag[2], cap_tag[3]
                    caps[(cap_tag[0], L)] = h[c_idx, s0:s1, :].detach().float().cpu().clone()
                if L in patch_spec:
                    c_idx, s0, s1, states = patch_spec[L]
                    h = h.clone()
                    ck(states.shape == (s1 - s0, h.shape[2]), "patch state shape")
                    h[c_idx, s0:s1, :] = states.to(device=h.device, dtype=h.dtype)
                    hook_applied.add(L)
                    output = (h,) + rest if rest else h
                return output
            return hook

        handles = [model.lm.base_model.model.layers[L].register_forward_hook(make_hook(L)) for L in LAYERS]

        def run_forward(req, condition, target, patch=None, capture=None):
            """One physical forward; appends its raw row to disk before returning.
            patch = (layer, s0, s1, states, source_label) in state coords (row coords
            equal state coords: the state starts at position 0 of every row).
            capture = (tag, s0, s1) of the C row."""
            ck(receipt["native_model_forward_calls"] < BUDGET, "budget exceeded before forward")
            ck(FROZEN_CONDITIONS[receipt["native_model_forward_calls"]] == condition,
               f"condition sequence deviates from frozen plan at position {receipt['native_model_forward_calls'] + 1}")
            enc, meta = encode_req(req["state"])
            c_idx = [m["id"] for m in meta].index("conflicting_vote")
            state_len = len(enc["ids"][:enc["seg"].count(0)])
            if capture is not None and capture[2] > state_len:
                # blind-review caveat 1: only the donor_old capture may overhang the
                # state end (its last positions are C-branch prefix tokens; MIXED,
                # descriptive only, used by no patch) - checked BEFORE the forward
                ck(condition == "capture_donor_old_at_new_span_coords", "unexpected capture overhang")
            cap_tag[0], cap_tag[1], cap_tag[2], cap_tag[3] = (capture[0], c_idx, capture[1], capture[2]) \
                if capture else (None, None, None, None)
            patch_spec.clear()
            hook_applied.clear()
            if patch is not None:
                L, s0, s1, states, src = patch
                ck(0 <= s0 < s1 <= state_len, "patch span bounds")
                ck(L in LAYERS, "patch layer not in frozen layers")
                patch_spec[L] = (c_idx, s0, s1, states)
            else:
                src = None
            with torch.inference_mode():
                outlogits = model.forward(enc)
            receipt["native_model_forward_calls"] += 1
            ck(len(outlogits) == len(meta) == 4, "branch count")
            raw = [z.detach().float().cpu().tolist() for z in outlogits]
            ck(all(len(v) == len(m["keys"]) and all(math.isfinite(float(x)) for x in v)
                   for v, m in zip(raw, meta)), "invalid logits")
            row = {"forward_index": receipt["native_model_forward_calls"], "condition": condition,
                   "target": target, "patch_layer": patch[0] if patch else None,
                   "patch_span_in_state": [patch[1], patch[2]] if patch else None,
                   "patch_source": src,
                   "capture_tag": capture[0] if capture else None,
                   "capture_span_in_state": [capture[1], capture[2]] if capture else None,
                   "conflicting_vote_branch_index": c_idx,
                   "questions": [{"id": m["id"], "keys": list(m["keys"]), "logits": v}
                                 for m, v in zip(meta, raw)],
                   "token_ids_sha256": hids(enc["ids"]), "state_len": state_len}
            if capture is not None and capture[2] > state_len:
                row["capture_note"] = (f"MIXED_STATE_BRANCH_UNUSED: last {capture[2] - state_len} positions beyond "
                                       f"state_len={state_len} are C-branch prefix tokens; descriptive only, "
                                       "used by no patch in this pilot")
            # write the raw row to disk BEFORE any post-forward gate so a failure
            # keeps the readout of every physical call that happened
            with raw_log.open("a", encoding="utf8", newline="\n") as f:
                f.write(canon(row) + "\n")
            # hook liveness: a silent no-op would fake identity and zero the effects
            if patch is not None:
                ck(patch[0] in hook_applied, "patch hook did not fire at layer " + str(patch[0]))
            if capture is not None:
                ck(all((capture[0], L) in caps for L in LAYERS), "capture hook did not fire " + capture[0])
            return row

        # ---------- execute the frozen 28-call plan ----------
        rows_out = []
        t0 = time.time()
        rng = random.Random(PERM_SEED)
        perm = list(range(EXPECTED_WIDTH))
        rng.shuffle(perm)

        # (1-3) donor captures: old at NEW-span coords (descriptive no-evidence baseline),
        # new and SA at their own appended spans; layers 11+23 captured per forward.
        # Condition names MUST equal the frozen pilot_execution_plan.jsonl names.
        for cond, tag, rid, arm in [("capture_donor_old_at_new_span_coords", "donor_old", DONOR_KEY + ":old", "new"),
                                    ("capture_donor_new", "donor_new", donor_new_rowid, "new"),
                                    ("capture_donor_sa", "donor_sa",
                                     next(r["row_id"] for r in by_pair[DONOR_KEY] if r["arm"] == "SA"), "SA")]:
            s0, s1 = spans[(DONOR_KEY, arm)]
            rows_out.append(run_forward(roster_reqs[rid], cond, tag,
                                        capture=(tag, s0, s1)))
        # (4-5) host SA unpatched baselines, bitwise-checked against archived logits
        for key in HOST_KEYS:
            row = run_forward(roster_reqs[arm_rowid(key, "SA")], "baseline_host_sa_unpatched", key + ":SA")
            arch = arch_by_rowid[next(r["row_id"] for r in by_pair[key] if r["arm"] == "SA")]
            for q_arch, q_new in zip(arch["questions"], row["questions"]):
                ck(q_arch["keys"] == q_new["keys"] and all(x - y == 0.0 for x, y in zip(q_arch["logits"], q_new["logits"])),
                   "baseline determinism vs archived " + key)
            rows_out.append(row)
        # (6-7) host SA captures (both layers per forward)
        for key in HOST_KEYS:
            s0, s1 = spans[(key, "SA")]
            rows_out.append(run_forward(roster_reqs[arm_rowid(key, "SA")], "capture_host_sa", key + ":SA",
                                        capture=(key + ":SA", s0, s1)))
        # (8-9) identity self-patch at layer 11, bitwise-checked against the fresh baseline
        for key in HOST_KEYS:
            s0, s1 = spans[(key, "SA")]
            row = run_forward(roster_reqs[arm_rowid(key, "SA")], "patch_identity_host_sa", key + ":SA",
                              patch=(IDENTITY_LAYER, s0, s1, caps[(key + ":SA", IDENTITY_LAYER)], "identity"))
            base_row = next(r for r in rows_out if r["condition"] == "baseline_host_sa_unpatched"
                            and r["target"] == key + ":SA")
            for q_b, q_n in zip(base_row["questions"], row["questions"]):
                ck(all(x - y == 0.0 for x, y in zip(q_b["logits"], q_n["logits"])),
                   "identity patch changed logits " + key)
            rows_out.append(row)
        # (10-13) restoration: donor recognized-new span states -> host neutral-SA span
        for key in HOST_KEYS:
            s0, s1 = spans[(key, "SA")]
            for L in LAYERS:
                rows_out.append(run_forward(roster_reqs[arm_rowid(key, "SA")], "patch_restoration_donor_new_to_host_sa",
                                            key + ":SA", patch=(L, s0, s1, caps[("donor_new", L)], "donor_new")))
        # (14-17) SA-sham cross: donor duplicate-vote (non-recognized) states -> host SA span
        for key in HOST_KEYS:
            s0, s1 = spans[(key, "SA")]
            for L in LAYERS:
                rows_out.append(run_forward(roster_reqs[arm_rowid(key, "SA")], "patch_sasham_donor_sa_to_host_sa",
                                            key + ":SA", patch=(L, s0, s1, caps[("donor_sa", L)], "donor_sa")))
        # (18-21) position-permuted donor span states -> host SA span
        for key in HOST_KEYS:
            s0, s1 = spans[(key, "SA")]
            for L in LAYERS:
                rows_out.append(run_forward(roster_reqs[arm_rowid(key, "SA")], "patch_permuted_donor_new_to_host_sa",
                                            key + ":SA", patch=(L, s0, s1, caps[("donor_new", L)][perm], "donor_new_permuted")))
        # (22-23) host treatment captures
        for key in HOST_KEYS:
            s0, s1 = spans[(key, "new")]
            rows_out.append(run_forward(roster_reqs[arm_rowid(key, "new")], "capture_host_new", key + ":new",
                                        capture=(key + ":new", s0, s1)))
        # (24) donor new unpatched baseline, bitwise-checked against archived logits
        row = run_forward(roster_reqs[donor_new_rowid], "baseline_donor_new_unpatched", "donor_new")
        arch = arch_by_rowid[donor_new_rowid]
        for q_arch, q_new in zip(arch["questions"], row["questions"]):
            ck(all(x - y == 0.0 for x, y in zip(q_arch["logits"], q_new["logits"])),
               "donor baseline determinism vs archived")
        rows_out.append(row)
        # (25-28) suppression: failed-host treatment span states -> donor recognized-new span
        for key in HOST_KEYS:
            s0, s1 = spans[(DONOR_KEY, "new")]
            for L in LAYERS:
                rows_out.append(run_forward(roster_reqs[donor_new_rowid], "patch_suppression_host_new_to_donor_new",
                                            "donor_new", patch=(L, s0, s1, caps[(key + ":new", L)], key + ":new")))

        ck(physical[0] == receipt["native_model_forward_calls"] == BUDGET,
           f"ledger mismatch physical={physical[0]}")
        ck(len(rows_out) == BUDGET, "row count")
        produced.append("raw_native_logits_pilot.jsonl")
        for h in handles:
            h.remove()
        hk.remove()
        receipt.update(status="COMPLETE_A461_G5_PILOT_GPU", physical_forwards=physical[0],
                       budget=BUDGET, rows=len(rows_out),
                       elapsed_seconds=round(time.time() - t0, 3),
                       backprop_calls=0, network_calls=0, tool_actions=0, test_or_calibration_rows=0)
        code = 0
    except Exception as err:
        import traceback
        if raw_log.exists() and "raw_native_logits_pilot.jsonl" not in produced:
            produced.append("raw_native_logits_pilot.jsonl")
        try:
            receipt["physical_prehook_count_at_failure"] = physical[0]
        except NameError:
            pass
        receipt.update(status="FAIL_A461_G5_PILOT_GPU", error_type=type(err).__name__,
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
