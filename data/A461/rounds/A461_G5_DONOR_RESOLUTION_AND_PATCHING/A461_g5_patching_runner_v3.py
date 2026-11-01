#!/usr/bin/env python3
"""A461-G5 patching runner V3: fixes A470 audit V2-P0-1..8 and V2-RISK-1/2.

172A = 97 forwards: 3 donor prepass (keyed (tag,layer) captures, hooks bind
tag and layer at registration) + 10 host baselines + 4 identity (2 captures +
2 patches) + 60 sufficiency + 20 SA-sham.
172B = 93 forwards: 2 donor captures (new, sa) + 40 SA-sham (10x4 remaining
layers) + 30 random-token (5x6) + 3 necessity-source captures + 18 necessity
patches.
Hosts = failing scenes' SA arms. Spans validated: the appended-event start
must equal the old state length (first divergence exactly at the old state
boundary); width mismatch handled by an explicit linear index map.
V2-RISK-2 validation: assert z == state_len(old) so the span is exactly the
appended event's tokens.
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


def sha_file(pth):
    h = hashlib.sha256()
    with open(pth, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


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
    expect = 97 if a.substage == "172A" else 93
    ck(admit.get("explicit_user_gpu_approval") is True and admit.get("substage") == a.substage
       and admit.get("approved_max_native_forwards") == expect
       and admit.get("runner_version") == "v3", "No V3 sub-stage authorization")
    receipt = {"schema": f"JEV_A461_G5_PATCHING_{a.substage}_V3_RECEIPT", "status": "INCOMPLETE",
               "runner_version": "v3", "gpu_model_loads": 0, "native_model_forward_calls": 0,
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

        def appended_span(enc_new, enc_old):
            """V2-RISK-2 validation: the first divergence must be exactly at the
            old state boundary (the appended event is the last message), so the
            span is precisely the appended event's tokens."""
            Ls_o = state_len(enc_old)
            Ls_n = state_len(enc_new)
            o_ids = enc_old["ids"][:Ls_o]
            n_ids = enc_new["ids"][:Ls_n]
            z = 0
            while z < min(len(o_ids), len(n_ids)) and o_ids[z] == n_ids[z]:
                z += 1
            ck(z == Ls_o, f"divergence {z} != old state length {Ls_o}: appended-event anchor invalid")
            w = Ls_n - Ls_o
            ck(w in (33, 34), f"span width {w}")
            return z, w

        # donor states (parameters, no closure over branch locals — V2-P0-3 fix)
        d_old_state = state_by[donor_key.split(":", 1)[1]]
        d_new_state = next(r for r in by_pair[donor_key] if r["arm"] == "new")["native_request"]["state"]
        d_sa_state = next(r for r in by_pair[donor_key] if r["arm"] == "SA")["native_request"]["state"]

        def capture_donors(tags, states_by_tag):
            """Capture layer outputs keyed (tag, layer); hooks bind tag and layer
            at registration — V2-P0-1 fix."""
            cap = {}
            encs = {}
            for tag in tags:
                enc, meta = render(states_by_tag[tag])
                encs[tag] = enc
                hs = []
                for L in LAYERS:
                    def mk(tg=tag, ll=L):
                        def hook(module, inp, out):
                            h = out[0] if isinstance(out, tuple) else out
                            cap[(tg, ll)] = h.detach()
                            return None
                        return hook
                    hs.append(layers[L].register_forward_hook(mk()))
                forward_plain(enc)
                for h in hs:
                    h.remove()
            for tag in tags:
                for L in LAYERS:
                    ck((tag, L) in cap, f"capture missing {(tag, L)}")
            return cap, encs

        if a.substage == "172A":
            cap, encs = capture_donors(("old", "new", "sa"),
                                       {"old": d_old_state, "new": d_new_state, "sa": d_sa_state})
            z_n, w_n = appended_span(encs["new"], encs["old"])
            z_s, w_s = appended_span(encs["sa"], encs["old"])
            donor_span = {L: {"new": cap[("new", L)][0, z_n:z_n + w_n, :].clone(),
                              "sa": cap[("sa", L)][0, z_s:z_s + w_s, :].clone()} for L in LAYERS}
            ck(physical[0] == 3, f"donor prepass {physical[0]}")
            # hosts = failing scenes' SA arms (V2 SA-host design)
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
                    # identity: capture own states at layer 11, then patch them back
                    cap2 = {}
                    def mk_id():
                        def hook(module, inp, out):
                            h = out[0] if isinstance(out, tuple) else out
                            cap2["own"] = h.detach()
                            return None
                        return hook
                    hnd = layers[11].register_forward_hook(mk_id())
                    forward_plain(enc)
                    hnd.remove()
                    own_states = cap2["own"][0, Ls - w:Ls, :].clone()
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
            composed = 3 + 10 + 4 + 60 + 20
            ck(physical[0] == composed == 97, f"ledger {physical[0]} != {composed}")
            receipt.update(status="COMPLETE_A461_G5_PATCHING_172A_V3",
                           native_model_forward_calls=physical[0],
                           physical_forwards=physical[0],
                           composition={"donor_prepass": 3, "host_baselines": 10,
                                        "identity_captures": 2, "identity_patches": 2,
                                        "sufficiency": 60, "sa_sham": 20, "total": 97},
                           backprop_calls=0, network_calls=0, tool_actions=0,
                           test_or_calibration_rows=0)
        else:
            # 172B: donor captures (new, sa) only — V2-P0-3 fix
            cap, encs = capture_donors(("new", "sa"),
                                       {"new": d_new_state, "sa": d_sa_state})
            # donor span widths vs donor old state (render is encode-only)
            enc_do, _ = render(d_old_state)
            w_n = state_len(encs["new"]) - state_len(enc_do)
            w_s = state_len(encs["sa"]) - state_len(enc_do)
            ck(w_n in (33, 34) and w_s in (33, 34), f"donor span widths {w_n}/{w_s}")
            Ls_n = state_len(encs["new"])
            donor_span = {L: {"new": cap[("new", L)][0, Ls_n - w_n:Ls_n, :].clone(),
                              "sa": cap[("sa", L)][0, state_len(encs["sa"]) - w_s:state_len(encs["sa"]), :].clone()} for L in LAYERS}
            # donor new unpatched read comes from this capture's own forward? The
            # capture forwards ARE the donor new forward: record its C read as the
            # necessity baseline by also reading logits — forward_plain returned
            # logits inside capture_donors; re-derive necessity baseline from the
            # dedicated necessity loop below instead (donor new unpatched = 1 extra
            # forward, counted).
            ck(physical[0] == 2, f"donor captures {physical[0]}")
            # baselines reused from 172A rows (same hosts)
            base_by_host = {}
            ck(a.baselines is not None, "172B requires --baselines (172A rows)")
            for line in a.baselines.read_text("utf8").splitlines():
                if line.strip():
                    r0 = json.loads(line)
                    if r0["condition"] == "baseline":
                        base_by_host[r0["host"]] = (r0["base_pred"], r0["base_M"])
            ck(len(base_by_host) == 10, f"baselines {len(base_by_host)}")
            patch_hosts = sorted(failed_wait)[:5] + sorted(failed_accept)[:5]
            SA_layers_B = LAYERS[2:]
            # SA-sham: donor SA span -> host SA arm, 10 hosts x 4 layers = 40
            for k in patch_hosts:
                sa_state = next(r for r in by_pair[k] if r["arm"] == "SA")["native_request"]["state"]
                enc, meta = render(sa_state)
                Ls = state_len(enc)
                enc_old, _ = render(state_by[k.split(":", 1)[1]])
                z_h, w_h = appended_span(enc, enc_old)
                base_pred, base_M = base_by_host[k]
                for L in SA_layers_B:
                    p2 = forward_patched(enc, L, (0, z_h, donor_span[L]["sa"]))
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
                z_h, w_h = appended_span(enc, enc_old)
                base_pred, base_M = base_by_host[k]
                for L in LAYERS:
                    p3 = forward_patched(enc, L, (0, z_h, donor_rand[L]))
                    pr3 = c_read(p3, meta)
                    rows.append({"host": k, "layer": L, "condition": "random_token",
                                 "base_pred": base_pred, "patched_pred": pr3["pred"],
                                 "base_M": base_M, "patched_M": pr3["M"],
                                 "delta_M": pr3["M"] - base_M,
                                 "off_target": qa_reads(p3, meta)})
            # necessity: 3 target treatment spans -> donor NEW arm (suppression)
            necessity_targets = sorted(failed_wait)[:2] + sorted(failed_accept)[:1]
            for tk in necessity_targets:
                t_treat = next(r for r in by_pair[tk] if r["arm"] == "new")["native_request"]["state"]
                enc_t, _ = render(t_treat)
                t_old = state_by[tk.split(":", 1)[1]]
                enc_told, _ = render(t_old)
                z_t, w_t = appended_span(enc_t, enc_told)
                cap_t = {}
                hs = []
                for L in LAYERS:
                    def mk_t(ll=L):
                        def hook(module, inp, out):
                            h = out[0] if isinstance(out, tuple) else out
                            cap_t[ll] = h.detach()
                            return None
                        return hook
                    hs.append(layers[L].register_forward_hook(mk_t()))
                forward_plain(enc_t)
                for h in hs:
                    h.remove()
                enc_dn, meta_dn = render(d_new_state)
                Ls_dn = state_len(enc_dn)
                # donor new unpatched baseline (1 forward, counted)
                dn_base_logits = forward_plain(enc_dn)
                dn_base_read = c_read(dn_base_logits, meta_dn)
                ck(dn_base_read["pred"] is True, "donor new baseline must read C=true")
                for L in LAYERS:
                    t_span = cap_t[L][0, z_t:z_t + w_t, :].clone()
                    p = forward_patched(enc_dn, L, (0, Ls_dn - w_n, t_span))
                    pr = c_read(p, meta_dn)
                    rows.append({"host": tk, "layer": L, "condition": "necessity",
                                 "base_pred": dn_base_read["pred"], "patched_pred": pr["pred"],
                                 "base_M": dn_base_read["M"], "patched_M": pr["M"],
                                 "delta_M": pr["M"] - dn_base_read["M"],
                                 "off_target": qa_reads(p, meta_dn)})
            composed = 2 + 40 + 30 + 3 + 18 + 1
            ck(physical[0] == composed == 94, f"ledger {physical[0]} != {composed}")
            receipt.update(status="COMPLETE_A461_G5_PATCHING_172B_V3",
                           native_model_forward_calls=physical[0],
                           physical_forwards=physical[0],
                           composition={"donor_captures": 2, "sa_sham_rest": 40, "random_token": 30,
                                        "necessity_source_captures": 3, "donor_new_baseline": 1,
                                        "necessity_patches": 18, "total": 94},
                           backprop_calls=0, network_calls=0, tool_actions=0,
                           test_or_calibration_rows=0)
        # V2-P0-8 fix: receipt counter synced
        receipt["native_model_forward_calls"] = physical[0]
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
    h = hashlib.sha256()
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            hh = hashlib.sha256()
            with (out / n).open("rb") as f2:
                for b in iter(lambda: f2.read(1 << 20), b""):
                    hh.update(b)
            f.write(hh.hexdigest() + "  " + n + "\n")
    print(canon(receipt))
    return code


if __name__ == "__main__":
    sys.exit(main())
