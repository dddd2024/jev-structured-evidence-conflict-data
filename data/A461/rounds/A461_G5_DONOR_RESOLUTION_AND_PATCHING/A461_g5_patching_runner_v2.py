#!/usr/bin/env python3
"""A461-G5 patching runner V2: fixes A469 audit P0-A..P0-G.

172A = 97 forwards: 3 donor prepass (keyed (tag,layer) captures, no clearing)
+ 10 host baselines + 4 identity (2 capture + 2 patch) + 60 sufficiency
+ 20 SA-sham (first 2 layers).
172B = 93 forwards: 2 donor captures (new, sa) + 40 SA-sham (10x4 remaining layers)
+ 30 random-token (5x6) + 3 necessity-source captures + 18 necessity patches.
Hosts = failing scenes' SA arms (real appended spans). Single counting
mechanism (lm pre-hook). V2 protocol/receipt references throughout.
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
    ap.add_argument("--baselines", required=False, type=Path, default=None)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    g5 = a.g5_run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA and
       all(x.is_relative_to(ROOT) for x in (repo, g5, SOURCE, CKPT, BASE, out)), "paths")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    admit = json.loads(a.admission.read_text("utf8"))
    expect = 97 if a.substage == "172A" else 113
    ck(admit.get("explicit_user_gpu_approval") is True and admit.get("substage") == a.substage
       and admit.get("approved_max_native_forwards") == expect
       and admit.get("runner_version") == "v2", "No V2 sub-stage authorization")
    receipt = {"schema": f"JEV_A461_G5_PATCHING_{a.substage}_V2_RECEIPT", "status": "INCOMPLETE",
               "runner_version": "v2", "gpu_model_loads": 0, "native_model_forward_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "tool_actions": 0,
               "test_or_calibration_rows": 0, "output_dir": str(out)}
    produced = []
    rows = []
    try:
        out.mkdir(mode=0o700)
        prows = [json.loads(x) for x in (g5 / "G0D_CONS" / "pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        g0receipt = json.loads((g5 / "G0D_CONS" / "execution_receipt.json").read_text("utf8"))
        ck(g0receipt["status"].startswith("COMPLETE_A461_G5_CONS"), "construction not complete")
        donor_hash = "433890d1"
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
        import gzip
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

        physical = [0]

        def bump(_m, _a):
            physical[0] += 1
        ledger = model.lm.register_forward_pre_hook(bump)

        def forward_plain(enc):
            with torch.inference_mode():
                return model.forward(enc)

        def forward_patched(enc, layer_idx, patch):
            def hook(module, inp, out):
                bi, start, states = patch
                h = out[0] if isinstance(out, tuple) else out
                h = h.clone()
                w = states.shape[0]
                h[bi, start:start + w, :] = states.to(h.device).to(h.dtype)
                if isinstance(out, tuple):
                    return (h,) + tuple(out[1:])
                return h
            hndl = layers[layer_idx].register_forward_hook(hook)
            try:
                with torch.inference_mode():
                    return model.forward(enc)
            finally:
                hndl.remove()

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

        # donor capture helper: keys (tag, layer); NO clearing (P0-A fix)
        def capture_donors(tags):
            cap = {}
            encs = {}
            for tag in tags:
                st = {"old": d_old, "new": d_new, "sa": d_sa}[tag]
                enc, meta = render(st)
                encs[tag] = enc
                hs = []
                cur = [None]
                def mk(tg, curref):
                    def hook(module, inp, out):
                        h = out[0] if isinstance(out, tuple) else out
                        cap[(tg, curref[0])] = h.detach()
                        return None
                    return hook
                for L in LAYERS:
                    cur[0] = L
                    hs.append(layers[L].register_forward_hook(mk(tag, cur)))
                forward_plain(enc)
                for h in hs:
                    h.remove()
            return cap, encs

        if a.substage == "172A":
            d_old = state_by[donor_key.split(":", 1)[1]]
            d_new = next(r for r in by_pair[donor_key] if r["arm"] == "new")["native_request"]["state"]
            d_sa = next(r for r in by_pair[donor_key] if r["arm"] == "SA")["native_request"]["state"]
            cap, encs = capture_donors(("old", "new", "sa"))
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
            ck(w_n in (33, 34) and w_s in (33, 34), f"span widths {w_n}/{w_s}")
            donor_span = {L: {"new": cap[("new", L)][0, z_n:z_n + w_n, :].clone(),
                              "sa": cap[("sa", L)][0, z_s:z_s + w_s, :].clone()} for L in LAYERS}
            ck(physical[0] == 3, f"donor prepass {physical[0]}")
            host_rows = []
            for k in (sorted(failed_wait)[:5] + sorted(failed_accept)[:5]):
                sa_state = next(r for r in by_pair[k] if r["arm"] == "SA")["native_request"]["state"]
                host_rows.append((k, sa_state))
            ck(len(host_rows) == 10, f"hosts {len(host_rows)}")
            host_enc = {}
            for k, st in host_rows:
                host_enc[k] = render(st)
            identity_hosts = hosts[:2]
            for k, st in host_rows:
                enc, meta = host_enc[k]
                Ls = state_len(enc)
                w = min(w_n, Ls)
                base_logits = forward_plain(enc)
                base_read = c_read(base_logits, meta)
                rows.append({"host": k, "layer": None, "condition": "baseline",
                             "base_pred": base_read["pred"], "patched_pred": None,
                             "base_M": base_read["M"], "patched_M": None,
                             "delta_M": None, "off_target": qa_reads(base_logits, meta)})
                if k in identity_hosts:
                    cap2 = {}
                    hs = []
                    cur = [11]
                    def mk_id(curref):
                        def hook(module, inp, out):
                            h = out[0] if isinstance(out, tuple) else out
                            cap2[("id", curref[0])] = h.detach()
                            return None
                        return hook
                    hs.append(layers[11].register_forward_hook(mk_id(cur)))
                    forward_plain(enc)
                    for h in hs:
                        h.remove()
                    own_states = cap2[("id", 11)][0, Ls - w:Ls, :].clone()
                    p = forward_patched(enc, 11, (0, Ls - w, own_states))
                    pr = c_read(p, meta)
                    ck(pr["pred"] == base_read["pred"]
                       and abs(pr["M"] - base_read["M"]) < 1e-3, "identity failed " + k)
                    rows.append({"host": k, "layer": 11, "condition": "identity",
                                 "base_pred": base_read["pred"], "patched_pred": pr["pred"],
                                 "base_M": base_read["M"], "patched_M": pr["M"],
                                 "delta_M": pr["M"] - base_read["M"], "off_target": {}})
                for L in LAYERS:
                    p = forward_patched(enc, L, (0, Ls - w, donor_span[L]["new"]))
                    pr = c_read(p, meta)
                    rows.append({"host": k, "layer": L, "condition": "donor_sufficiency",
                                 "base_pred": base_read["pred"], "patched_pred": pr["pred"],
                                 "base_M": base_read["M"], "patched_M": pr["M"],
                                 "delta_M": pr["M"] - base_read["M"],
                                 "off_target": qa_reads(p, meta)})
                    if L in LAYERS[:2]:
                        p2 = forward_patched(enc, L, (0, Ls - w, donor_span[L]["sa"]))
                        pr2 = c_read(p2, meta)
                        rows.append({"host": k, "layer": L, "condition": "sa_sham",
                                     "base_pred": base_read["pred"], "patched_pred": pr2["pred"],
                                     "base_M": base_read["M"], "patched_M": pr2["M"],
                                     "delta_M": pr2["M"] - base_read["M"],
                                     "off_target": qa_reads(p2, meta)})
            composed = 97
            ck(physical[0] == composed, f"ledger {physical[0]} != {composed}")
            receipt.update(status="COMPLETE_A461_G5_PATCHING_172A_V2",
                           physical_forwards=physical[0],
                           composition={"donor_prepass": 3, "host_baselines": 10,
                                        "identity_captures": 2, "identity_patches": 2,
                                        "sufficiency": 60, "sa_sham": 20, "total": 97},
                           backprop_calls=0, network_calls=0, tool_actions=0,
                           test_or_calibration_rows=0)
        else:
            base_by_host = {}
            if a.baselines is not None:
                for line in a.baselines.read_text("utf8").splitlines():
                    if line.strip():
                        r0 = json.loads(line)
                        if r0["condition"] == "baseline":
                            base_by_host[r0["host"]] = (r0["base_pred"], r0["base_M"])
            ck(len(base_by_host) == 10, "172A baselines missing")
            cap, encs = capture_donors(("new", "sa"))
            Ls_n, Ls_s = state_len(encs["new"]), state_len(encs["sa"])
            # donor span widths vs donor old state (encode-only, no forward)
            d_old_state = state_by[donor_key.split(":", 1)[1]]
            enc_o, _ = render(d_old_state)
            Ls_o = state_len(enc_o)
            w_n = Ls_n - Ls_o
            w_s = Ls_s - Ls_o
            ck(w_n in (33, 34) and w_s in (33, 34), f"donor span widths {w_n}/{w_s}")
            donor_span = {L: {"new": cap[("new", L)][0, Ls_n - w_n:Ls_n, :].clone(),
                              "sa": cap[("sa", L)][0, Ls_s - w_s:Ls_s, :].clone()} for L in LAYERS}
            ck(physical[0] == 2, f"donor captures {physical[0]}")
            patch_hosts = sorted(failed_wait)[:5] + sorted(failed_accept)[:5]
            SA_layers_B = LAYERS[2:]
            # SA-sham: donor SA span -> host SA arm, 10 hosts x 4 layers = 40
            for k in patch_hosts:
                sa_state = next(r for r in by_pair[k] if r["arm"] == "SA")["native_request"]["state"]
                enc, meta = render(sa_state)
                Ls = state_len(enc)
                enc_old, _ = render(state_by[k.split(":", 1)[1]])
                w_h = Ls - state_len(enc_old)
                ck(w_h in (33, 34), f"host span width {w_h}")
                base_pred, base_M = base_by_host[k]
                for L in SA_layers_B:
                    p2 = forward_patched(enc, L, (0, Ls - w_h, donor_span[L]["sa"]))
                    pr2 = c_read(p2, meta)
                    rows.append({"host": k, "layer": L, "condition": "sa_sham",
                                 "base_pred": base_pred, "patched_pred": pr2["pred"],
                                 "base_M": base_M, "patched_M": pr2["M"],
                                 "delta_M": pr2["M"] - base_M,
                                 "off_target": qa_reads(p2, meta)})
            # random-token: first 5 hosts x 6 layers = 30
            g = torch.Generator().manual_seed(461)
            donor_rand = {L: donor_span[L]["new"][torch.randperm(donor_span[L]["new"].shape[0], generator=g), :].clone()
                          for L in LAYERS}
            for k in patch_hosts[:5]:
                sa_state = next(r for r in by_pair[k] if r["arm"] == "SA")["native_request"]["state"]
                enc, meta = render(sa_state)
                Ls = state_len(enc)
                enc_old, _ = render(state_by[k.split(":", 1)[1]])
                w_h = Ls - state_len(enc_old)
                base_pred, base_M = base_by_host[k]
                for L in LAYERS:
                    p3 = forward_patched(enc, L, (0, Ls - w_h, donor_rand[L]))
                    pr3 = c_read(p3, meta)
                    rows.append({"host": k, "layer": L, "condition": "random_token",
                                 "base_pred": base_pred, "patched_pred": pr3["pred"],
                                 "base_M": base_M, "patched_M": pr3["M"],
                                 "delta_M": pr3["M"] - base_M,
                                 "off_target": qa_reads(p3, meta)})
            # necessity: 3 target treatment spans -> donor NEW arm, 3 captures + 18 patches
            necessity_targets = sorted(failed_wait)[:2] + sorted(failed_accept)[:1]
            for tk in necessity_targets:
                t_treat = next(r for r in by_pair[tk] if r["arm"] == "new")["native_request"]["state"]
                enc_t, _ = render(t_treat)
                cap_store.clear()
                hs = []
                cur = [None]
                def mk_t(curref):
                    def hook(module, inp, out):
                        h = out[0] if isinstance(out, tuple) else out
                        cap_store[("target", curref[0])] = h.detach()
                        return None
                    return hook
                for L in LAYERS:
                    cur[0] = L
                    hs.append(layers[L].register_forward_hook(mk_t(cur)))
                forward_plain(enc_t)
                for h in hs:
                    h.remove()
                Ls_t = state_len(enc_t)
                t_old = state_by[tk.split(":", 1)[1]]
                enc_told, _ = render(t_old)
                w_t = Ls_t - state_len(enc_told)
                ck(w_t in (33, 34), f"target span width {w_t}")
                enc_dn, meta_dn = render(d_new)
                Ls_dn = state_len(enc_dn)
                for L in LAYERS:
                    t_span = cap_store[("target", L)][0, Ls_t - w_t:Ls_t, :].clone()
                    p = forward_patched(enc_dn, L, (0, Ls_dn - w_n, t_span))
                    pr = c_read(p, meta_dn)
                    rows.append({"host": tk, "layer": L, "condition": "necessity",
                                 "base_pred": "true", "patched_pred": pr["pred"],
                                 "base_M": None, "patched_M": pr["M"],
                                 "delta_M": None,
                                 "off_target": qa_reads(p, meta_dn)})
            composed = 93
            ck(physical[0] == composed, f"ledger {physical[0]} != {composed}")
            receipt.update(status="COMPLETE_A461_G5_PATCHING_172B_V2",
                           physical_forwards=physical[0],
                           composition={"donor_captures": 2, "sa_sham_rest": 40, "random_token": 30,
                                        "necessity_source_captures": 3, "necessity_patches": 18, "total": 93},
                           backprop_calls=0, network_calls=0, tool_actions=0,
                           test_or_calibration_rows=0)
            code = 0
    except Exception as err:
        import traceback
        receipt.update(status=f"FAIL_A461_G5_PATCHING_{a.substage}", error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-1500:])
        code = 2
    save(out / "execution_receipt.json", receipt)
    produced.append("execution_receipt.json")
    print(canon(receipt))
    return code


if __name__ == "__main__":
    sys.exit(main())
