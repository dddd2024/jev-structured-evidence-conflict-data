#!/usr/bin/env python3
"""A461-G5 patching runner: sub-stages 172A (95 forwards) and 172B (88 forwards).

Frozen protocol: research/experiments/2026-10-25_A461_G5_PATCHING_PROTOCOL_V1.json
DISCLOSED DEVIATION (before execution, G3 provenance lesson): the protocol split
froze 84 for 172A on a miscount - shared host baselines and the third
donor-prepass forward were not itemized. Corrected composition:
172A = 3 donor prepass + 10 host baselines + 2 identity patches
       + 60 sufficiency patches + 20 SA-sham patches = 95 (<= 128 cap).
172B = 40 SA-sham (remaining 4 layers) + 30 random-token controls
       + 18 necessity patches = 88 (<= 128 cap).

Layer outputs are [4, L, 1024] tensors (4 branch rows batched per question);
patching replaces hidden states at the host's appended-span tail positions with
donor arm span states (linear index map over width difference). Hybrid
architecture respected: single-row forwards via model.forward on the encoded
row set, never packed-sequence patching.
"""
import argparse, collections, gzip, hashlib, json, os, sys, time
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
LAYERS = [3, 7, 11, 15, 19, 23]

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1",
                  TMPDIR=str(ROOT / ".tmp"), HF_HOME=str(ROOT / ".cache" / "huggingface"),
                  TORCH_HOME=str(ROOT / ".cache" / "torch"), XDG_CACHE_HOME=str(ROOT / ".cache"),
                  PYTHONPYCACHEPREFIX=str(ROOT / ".cache" / "pycache"))
sys.dont_write_bytecode = True


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def save(p, v):
    with p.open("x", encoding="utf8", newline="\n") as f:
        json.dump(v, f, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--g5-run", required=True, type=Path)
    ap.add_argument("--substage", required=True, choices=["172A", "172B"])
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--baselines", required=False, type=Path, default=None,
                    help="172A rows jsonl; supplies unpatched host baselines for 172B (which spends no forwards on baselines)")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    g5 = a.g5_run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA and
       all(x.is_relative_to(ROOT) for x in (repo, g5, SOURCE, CKPT, BASE, out)), "paths")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    admit = json.loads(a.admission.read_text("utf8"))
    expect = 95 if a.substage == "172A" else 88
    ck(admit.get("explicit_user_gpu_approval") is True and admit.get("substage") == a.substage
       and admit.get("approved_max_native_forwards") == expect
       and admit.get("composition_disclosed") is True, "No sub-stage authorization")
    receipt = {"schema": f"JEV_A461_G5_PATCHING_{a.substage}_RECEIPT_V1", "status": "INCOMPLETE",
               "gpu_model_loads": 0, "native_model_forward_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "tool_actions": 0,
               "test_or_calibration_rows": 0, "output_dir": str(out)}
    produced = []
    rows = []
    try:
        out.mkdir(mode=0o700)
        search = json.loads((g5 / "G1S_REAL/donor_search_result.json").read_text("utf8"))
        donor_hash = search["qualification"]["the_qualified_donor"]["pair_key_hash"]
        prows = [json.loads(x) for x in (g5 / "G0D_CONS/pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        by_pair = collections.OrderedDict()
        for r in prows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        donor_key = next(k for k in by_pair if donor_hash in k)
        failed_wait, failed_accept = [], []
        for k in by_pair:
            if k == donor_key:
                continue
            treat = next(r for r in by_pair[k] if r["arm"] == "new")
            if treat["oracle_gold_impl1"]["certificate_action"] != "reject_conflict":
                continue
            (failed_wait if "WAIT" in treat["family"] else failed_accept).append(k)
        hosts = sorted(failed_wait)[:5] + sorted(failed_accept)[:5]
        ck(len(hosts) == 10, f"hosts {len(hosts)}")
        necessity_targets = sorted(failed_wait)[:2] + sorted(failed_accept)[:1]
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
        q_tw = prows[0]["native_request"]["questions"]

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
        layers = None
        for name, mod in model.named_modules():
            if name.endswith("layers") and isinstance(mod, torch.nn.ModuleList) and len(mod) == 24:
                layers = mod
                break
        ck(layers is not None, "layers not found")

        def render(state):
            rendered, meta = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
            enc = model.encode(tokenizer, rendered, max_state=8192, max_branch=8192, strict=True)
            ck(not enc["state_truncated"], "truncated")
            return enc, meta

        def state_len(enc):
            return sum(1 for x in enc["seg"] if x == 0)

        cap_store = {}

        def cap_hook(idx):
            def hook(module, inp, out):
                h = out[0] if isinstance(out, tuple) else out
                cap_store[idx] = h.detach()
                return None
            return hook

        physical = [0]

        def bump(_m, _a):
            physical[0] += 1
        ledger = model.lm.register_forward_pre_hook(bump)

        def forward_counted(enc, patch=None, layer_idx=None):
            def hook(module, inp, out):
                if patch is None:
                    return None
                bi, start, states = patch
                h = out[0] if isinstance(out, tuple) else out
                h = h.clone()
                w = states.shape[0]
                h[bi, start:start + w, :] = states.to(h.device).to(h.dtype)
                if isinstance(out, tuple):
                    return (h,) + tuple(out[1:])
                return h
            hndl = layers[layer_idx].register_forward_hook(hook) if layer_idx is not None else None
            try:
                with torch.inference_mode():
                    logits = model.forward(enc)
            finally:
                if hndl is not None:
                    hndl.remove()
            physical[0] += 1
            return logits

        def c_read(logits, meta):
            c_i = [m["id"] for m in meta].index("conflicting_vote")
            keys = list(meta[c_i]["keys"])
            nk = [{"true": True, "false": False}.get(str(k).strip().lower(), k) for k in keys]
            vals = logits[c_i].detach().float().cpu().tolist()
            ti, fi = nk.index(True), nk.index(False)
            return {"pred": nk[max(range(len(vals)), key=lambda i2: vals[i2])],
                    "M": vals[ti] - vals[fi]}

        def qa_reads(logits, meta):
            out = {}
            for i, m in enumerate(meta):
                if m["id"] in ("quorum", "certificate_action"):
                    vals = logits[i].detach().float().cpu().tolist()
                    nk = [{"true": True, "false": False}.get(str(k).strip().lower(), k) for k in m["keys"]]
                    out[m["id"]] = nk[max(range(len(vals)), key=lambda i2: vals[i2])]
            return out

        if a.substage == "172A":
            # ---- donor prepass: 3 forwards, span states at 6 layers ----
            d_old = state_by[donor_key.split(":", 1)[1]]
            d_new = next(r for r in by_pair[donor_key] if r["arm"] == "new")["native_request"]["state"]
            d_sa = next(r for r in by_pair[donor_key] if r["arm"] == "SA")["native_request"]["state"]
            spans = {}
            encs = {}
            for tag, st in (("old", d_old), ("new", d_new), ("sa", d_sa)):
                enc, meta = render(st)
                encs[tag] = enc
                cap_store.clear()
                hs = [layers[i].register_forward_hook(cap_hook(i)) for i in LAYERS]
                forward_counted(enc)
                for h in hs:
                    h.remove()
            Ls_o, Ls_n, Ls_s = state_len(encs["old"]), state_len(encs["new"]), state_len(encs["sa"])
            o_ids = encs["old"]["ids"][:Ls_o]
            n_ids = encs["new"]["ids"][:Ls_n]
            s_ids = encs["sa"]["ids"][:Ls_s]
            z_n = 0
            while z_n < min(len(o_ids), len(n_ids)) and o_ids[z_n] == n_ids[z_n]:
                z_n += 1
            w_n = Ls_n - Ls_o
            z_s = 0
            while z_s < min(len(o_ids), len(s_ids)) and o_ids[z_s] == s_ids[z_s]:
                z_s += 1
            w_s = Ls_s - Ls_o
            ck(w_n in (33, 34) and w_s in (33, 34), f"unexpected span widths {w_n}/{w_s}")
            donor_span = {L: {"new": cap_store[L][0, z_n:z_n + w_n, :].clone(),
                              "sa": cap_store[L][0, z_s:z_s + w_s, :].clone()} for L in LAYERS}
            spans["donor"] = {"z_new": z_n, "w_new": w_n, "z_sa": z_s, "w_sa": w_s}
            # ---- hosts: baseline + identity + sufficiency + SA(2 layers) ----
            host_enc = {}
            for k in hosts:
                host_enc[k] = render(state_by[k.split(":", 1)[1]])
            identity_hosts = hosts[:2]
            for k in hosts:
                enc, meta = host_enc[k]
                Ls = state_len(enc)
                w = min(w_n, Ls)
                base_logits = forward_counted(enc)
                base_read = c_read(base_logits, meta)
                # identity patches (2 hosts only, layer 11)
                if k in identity_hosts:
                    # capture host's own layer-11 states at the patch site
                    cap_store.clear()
                    hnd = layers[11].register_forward_hook(cap_hook(11))
                    forward_counted(enc)
                    hnd.remove()
                    own_states = cap_store[11][0, Ls - w:Ls, :].clone()
                    p = forward_counted(enc, (0, Ls - w, own_states), 11)
                    pr = c_read(p, meta)
                    ck(pr["pred"] == base_read["pred"]
                       and abs(pr["M"] - base_read["M"]) < 1e-3, "identity failed " + k)
                    rows.append({"host": k, "layer": 11, "condition": "identity",
                                 "base_pred": base_read["pred"], "patched_pred": pr["pred"],
                                 "base_M": base_read["M"], "patched_M": pr["M"],
                                 "delta_M": pr["M"] - base_read["M"], "off_target": {}})
                for li, L in enumerate(LAYERS):
                    p = forward_counted(enc, (0, Ls - w, donor_span[L]["new"]), L)
                    pr = c_read(p, meta)
                    rows.append({"host": k, "layer": L, "condition": "donor_sufficiency",
                                 "base_pred": base_read["pred"], "patched_pred": pr["pred"],
                                 "base_M": base_read["M"], "patched_M": pr["M"],
                                 "delta_M": pr["M"] - base_read["M"],
                                 "off_target": qa_reads(p, meta)})
                    if L in LAYERS[:2]:
                        p2 = forward_counted(enc, (0, Ls - w, donor_span[L]["sa"]), L)
                        pr2 = c_read(p2, meta)
                        rows.append({"host": k, "layer": L, "condition": "sa_sham",
                                     "base_pred": base_read["pred"], "patched_pred": pr2["pred"],
                                     "base_M": base_read["M"], "patched_M": pr2["M"],
                                     "delta_M": pr2["M"] - base_read["M"],
                                     "off_target": qa_reads(p2, meta)})
            composed = 3 + len(hosts) + 2 + 60 + 20
            ck(physical[0] == composed, f"ledger {physical[0]} != {composed}")
            receipt.update(status=f"COMPLETE_A461_G5_PATCHING_172A",
                           physical_forwards=physical[0], composed=composition_172a(),
                           backprop_calls=0, network_calls=0, tool_actions=0,
                           test_or_calibration_rows=0)
        else:
            # ---- 172B: SA-sham remaining layers + random-token + necessity ----
            d_old = state_by[donor_key.split(":", 1)[1]]
            d_new = next(r for r in by_pair[donor_key] if r["arm"] == "new")["native_request"]["state"]
            d_sa = next(r for r in by_pair[donor_key] if r["arm"] == "SA")["native_request"]["state"]
            spans = {}
            encs = {}
            for tag, st in (("old", d_old), ("new", d_new), ("sa", d_sa)):
                enc, meta = render(st)
                encs[tag] = enc
                cap_store.clear()
                hs = [layers[i].register_forward_hook(cap_hook(i)) for i in LAYERS]
                forward_counted(enc)
                for h in hs:
                    h.remove()
            Ls_o, Ls_n, Ls_s = state_len(encs["old"]), state_len(encs["new"]), state_len(encs["sa"])
            o_ids = encs["old"]["ids"][:Ls_o]
            n_ids = encs["new"]["ids"][:Ls_n]
            s_ids = encs["sa"]["ids"][:Ls_s]
            z_n = 0
            while z_n < min(len(o_ids), len(n_ids)) and o_ids[z_n] == n_ids[z_n]:
                z_n += 1
            w_n = Ls_n - Ls_o
            z_s = 0
            while z_s < min(len(o_ids), len(s_ids)) and o_ids[z_s] == s_ids[z_s]:
                z_s += 1
            w_s = Ls_s - Ls_o
            donor_span = {L: {"new": cap_store[L][0, z_n:z_n + w_n, :].clone(),
                              "sa": cap_store[L][0, z_s:z_s + w_s, :].clone()} for L in LAYERS}
            # random-token: donor new-span with positions permuted (fixed seed)
            g = torch.Generator().manual_seed(461)
            donor_rand = {L: donor_span[L]["new"][torch.randperm(donor_span[L]["new"].shape[0], generator=g), :].clone()
                          for L in LAYERS}
            host_enc = {}
            patch_hosts = sorted(failed_wait)[:5] + sorted(failed_accept)[:5]
            base_by_host = {}
            for r in rows:
                pass
            for line in open(a.out.parent / "NOPE", encoding="utf8") if False else []:
                pass
            SA_layers_B = LAYERS[2:]
            base_by_host = {}
            if a.baselines is not None:
                for line in a.baselines.read_text("utf8").splitlines():
                    if line.strip():
                        r0 = json.loads(line)
                        if r0["condition"] == "donor_sufficiency" and r0["layer"] == LAYERS[0]:
                            base_by_host[r0["host"]] = (r0["base_pred"], r0["base_M"])
            for k in patch_hosts:
                enc, meta = host_enc[k]
                Ls = state_len(enc)
                w = min(w_n, Ls)
                base_pred, base_M = base_by_host[k]
                for li, L in enumerate(LAYERS):
                    if L in SA_layers_B:
                        p2 = forward_counted(enc, (0, Ls - w, donor_span[L]["sa"]), L)
                        pr2 = c_read(p2, meta)
                        rows.append({"host": k, "layer": L, "condition": "sa_sham",
                                     "base_pred": base_pred, "patched_pred": pr2["pred"],
                                     "base_M": base_M, "patched_M": pr2["M"],
                                     "delta_M": pr2["M"] - base_M,
                                     "off_target": qa_reads(p2, meta)})
                    p3 = forward_counted(enc, (0, Ls - w, donor_rand[L]), L)
                    pr3 = c_read(p3, meta)
                    rows.append({"host": k, "layer": L, "condition": "random_token",
                                 "base_pred": base_pred, "patched_pred": pr3["pred"],
                                 "base_M": base_M, "patched_M": pr3["M"],
                                 "delta_M": pr3["M"] - base_M,
                                 "off_target": qa_reads(p3, meta)})
            # necessity: 3 targets' spans patched into donor new arm
            for tk in necessity_targets:
                t_state = state_by[tk.split(":", 1)[1]]
                enc_t, _ = render(t_state)
                cap_store.clear()
                hs = [layers[i].register_forward_hook(cap_hook(i)) for i in LAYERS]
                forward_counted(enc_t)
                for h in hs:
                    h.remove()
                Ls_t = state_len(enc_t)
                for L in LAYERS:
                    t_span = cap_store[L][0, Ls_t - w_n:Ls_t, :].clone()
                    enc_d, meta_d = render(d_new)
                    Ls_d = state_len(enc_d)
                    p = forward_counted(enc_d, (0, Ls_d - w_n, t_span), L)
                    pr = c_read(p, meta_d)
                    rows.append({"host": tk, "layer": L, "condition": "necessity",
                                 "base_pred": "true", "patched_pred": pr["pred"],
                                 "base_M": None, "patched_M": pr["M"],
                                 "delta_M": None,
                                 "off_target": qa_reads(p, meta_d)})
            composed = 40 + 30 + 18
            ck(physical[0] == composed, f"ledger {physical[0]} != {composed}")
            receipt.update(status="COMPLETE_A461_G5_PATCHING_172B",
                           physical_forwards=physical[0], composed=composed,
                           backprop_calls=0, network_calls=0, tool_actions=0,
                           test_or_calibration_rows=0)
        with (out / f"patching_{a.substage}_rows.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for r in rows:
                f.write(canon(r) + "\n")
        produced.append(f"patching_{a.substage}_rows.jsonl")
        gpu_after = torch.cuda.mem_get_info(0)
        receipt["gpu_free_bytes_after"] = gpu_after[0]
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status=f"FAIL_A461_G5_PATCHING_{a.substage}", error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-1500:])
        code = 2
    save(out / "execution_receipt.json", receipt)
    produced.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            h = hashlib.sha256()
            with (out / n).open("rb") as f2:
                for b in iter(lambda: f2.read(1 << 20), b""):
                    h.update(b)
            f.write(h.hexdigest() + "  " + n + "\n")
    print(canon(receipt))
    return code


def composition_172a():
    return {"donor_prepass": 3, "host_baselines": 10, "identity": 2,
            "sufficiency": 60, "sa_sham": 20, "total": 95}


if __name__ == "__main__":
    sys.exit(main())
