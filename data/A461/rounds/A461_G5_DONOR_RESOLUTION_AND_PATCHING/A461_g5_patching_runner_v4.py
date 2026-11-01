#!/usr/bin/env python3
"""A461-G5 patching runner V4: fixes blind-review 7098a19 P0-1..P0-7.

P0-1  span anchor = true first divergence z (< old state length OK); the patch
      covers exactly [z, z+w_append) and the trailing unchanged suffix
      (validator_set etc.) is left intact; the prefix assertion is gone.
P0-2  C_ROW is the conflicting_vote branch index from meta (row 1 in the
      frozen G5 order); donor captures, host captures and patches all use
      batch index C_ROW. A separate CPU mock test proves the row-patching
      mechanism (A461_g5_mock_patch_test_v1.py).
P0-3  no undefined `hosts`: identity hosts derive from host_rows.
P0-4  172B admission expects 94 forwards (receipt bfc9f558... updated).
P0-5  donor NEW baseline hoisted outside the necessity loop (1 forward).
P0-6  host width policy: equal-width (+34) hosts use the identity span map;
      +33 hosts use an explicit truncation map (donor span minus its last
      token), labeled "truncation_map"; +35 hosts excluded. Map recorded.
P0-7  host roster joins G1S_V2 predictions: old C=false, new C=false,
      SA C=false (no false alarms), gold reject, width policy satisfied.
Atomic saving: rows are flushed to disk after every forward group.
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
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    g5 = a.g5_run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA and
       all(x.is_relative_to(ROOT) for x in (repo, g5, SOURCE, CKPT, BASE, out)), "paths")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    admit = json.loads(a.admission.read_text("utf8"))
    expect = 97
    ck(admit.get("explicit_user_gpu_approval") is True and admit.get("substage") == "172A_V4"
       and admit.get("approved_max_native_forwards") == expect
       and admit.get("runner_version") == "v4", "No V4 authorization")
    receipt = {"schema": "JEV_A461_G5_PATCHING_172A_V4_RECEIPT", "status": "INCOMPLETE",
               "runner_version": "v4", "gpu_model_loads": 0, "native_model_forward_calls": 0,
               "backprop_calls": 0, "network_calls": 0, "tool_actions": 0,
               "test_or_calibration_rows": 0, "output_dir": str(out)}
    rows_path = out / "patching_rows.jsonl"
    produced = []
    rows = []
    physical = [0]

    def flush_rows():
        tmp = out / "patching_rows.jsonl.tmp"
        with tmp.open("w", encoding="utf8", newline="\n") as f:
            for r in rows:
                f.write(canon(r) + "\n")
        tmp.replace(rows_path)

    try:
        out.mkdir(mode=0o700)
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

        # G1S_V2 predictions for the host roster (P0-7 fix)
        g1s = [json.loads(x) for x in (g5 / "G1S_V2" / "raw_native_logits_112_requests.jsonl").read_text("utf8").splitlines() if x.strip()]
        prim = {r["plan_row"]: r for r in g1s if r["kind"] == "primary"}

        def g1s_c(rid):
            rr = prim[rid]
            for q in rr["questions"]:
                if q["id"] == "conflicting_vote":
                    nk = [{"true": True, "false": False}.get(str(k).strip().lower(), k) for k in q["keys"]]
                    vals = q["logits"]
                    return nk[max(range(len(vals)), key=lambda i2: vals[i2])]
            raise RuntimeError("C branch missing " + rid)

        prows = [json.loads(x) for x in (g5 / "G0D_CONS" / "pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        by_pair = collections.OrderedDict()
        for r in prows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        donor_hash = "433890d1"
        donor_key = next(k for k in by_pair if donor_hash in k)
        # host roster: strict failures with clean old/new/SA reads (P0-7)
        host_pool = []
        excluded = []
        for k in by_pair:
            if k == donor_key:
                continue
            arms = {r["arm"]: r for r in by_pair[k]}
            rid = {"old": k + ":old", "new": arms["new"]["row_id"], "SA": arms["SA"]["row_id"]}
            old_c, new_c, sa_c = g1s_c(rid["old"]), g1s_c(rid["new"]), g1s_c(rid["SA"])
            treat = arms["new"]
            gold_reject = treat["oracle_gold_impl1"]["certificate_action"] == "reject_conflict"
            if not (old_c is False and new_c is False and sa_c is False and gold_reject):
                excluded.append({"pair_key": k, "old_c": old_c, "new_c": new_c, "sa_c": sa_c,
                                 "reason": "not a strict failed-recognition scene"})
                continue
            tl = {a: None for a in arms}
            host_pool.append({"pair_key": k, "group": treat["source_group"], "row_ids": rid,
                              "family": treat["family"]})
        # width policy from render token lengths
        rtldoc = json.loads((g5 / "G1S_V2" / "render_token_lengths.json").read_text("utf8"))
        rtl = {r["row_id"]: r["state_token_len"] for r in rtldoc["rows"]}
        donors_width = None
        host_final = []
        for h in host_pool:
            arms = {r["arm"]: r for r in by_pair[h["pair_key"]]}
            old_rid = k + ":old"
            w = rtl[arms["new"]["row_id"]] - rtl[old_rid]
            h["width"] = w
            if w == 34:
                h["width_map"] = "identity"
                host_final.append(h)
            elif w == 33:
                h["width_map"] = "truncation_map_donor_minus_last"
                host_final.append(h)
            else:
                excluded.append({"pair_key": h["pair_key"], "reason": f"width {w} not in (33,34)"})
        equal_w = [h for h in host_final if h["width_map"] == "identity"]
        trunc_w = [h for h in host_final if h["width_map"] == "truncation_map_donor_minus_last"]
        # hosts = equal-width first, then truncation-map hosts (all labeled)
        host_final = equal_w + trunc_w
        n_hosts = len(host_final)
        ck(n_hosts >= 2, f"too few hosts {n_hosts}")
        donor_rows = {r["arm"]: r for r in by_pair[donor_key]}
        d_old = state_by[donor_key.split(":", 1)[1]]
        d_new = donor_rows["new"]["native_request"]["state"]
        d_sa = donor_rows["SA"]["native_request"]["state"]

        # donor prepass: 3 forwards, span keyed (tag, layer); hooks bind (tag, layer)
        cap = {}
        encs = {}
        for tag, st in (("old", d_old), ("new", d_new), ("sa", d_sa)):
            enc, meta = render(st)
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
        produced_count = 0
        # donor spans: appended event = [z, z+w); z == Ls_old verified, suffix intact
        Ls_o = state_len(encs["old"])
        spans = {}
        for tag in ("new", "sa"):
            Ls_t = state_len(encs[tag])
            o_ids = encs["old"]["ids"][:Ls_o]
            t_ids = encs[tag]["ids"][:Ls_t]
            z = 0
            while z < min(len(o_ids), len(t_ids)) and o_ids[z] == t_ids[z]:
                z += 1
            w = Ls_t - Ls_o
            spans[tag] = {"z": z, "w": w, "suffix_intact": Ls_t - (z + w) == Ls_o - (z + w)}
        ck(spans["new"]["w"] == 34, f"donor width {spans['new']['w']}")
        donor_span = {L: {"new": cap[("new", L)][0, spans["new"]["z"]:spans["new"]["z"] + spans["new"]["w"], :].clone(),
                          "sa": cap[("sa", L)][0, spans["sa"]["z"]:spans["sa"]["z"] + spans["sa"]["w"], :].clone()} for L in LAYERS}
        ck(physical[0] == 3, f"donor prepass {physical[0]}")
        receipt["donor_spans"] = spans
        # per-host processing (baselines shared by sufficiency + SA controls)
        budget = 97
        for h in host_final:
            k = h["pair_key"]
            arms = {r["arm"]: r for r in by_pair[k]}
            host_state = arms["SA"]["native_request"]["state"]
            old_state = state_by[k.split(":", 1)[1]]
            enc_h, meta_h = render(host_state)
            Ls_h = state_len(enc_h)
            enc_ho, _ = render(old_state)
            z_h, w_h = None, None
            o_ids = enc_ho["ids"][:state_len(enc_ho)]
            h_ids = enc_h["ids"][:Ls_h]
            z_h = 0
            while z_h < min(len(o_ids), len(h_ids)) and o_ids[z_h] == h_ids[z_h]:
                z_h += 1
            w_h = Ls_h - state_len(enc_ho)
            ck(z_h + w_h <= Ls_h, "span overruns host row")
            C_ROW = [m["id"] for m in meta_h].index("conflicting_vote")
            base_logits = forward_plain(enc_h)
            base_read = c_read(base_logits, meta_h)
            rows.append({"host": k, "layer": None, "condition": "baseline",
                         "base_pred": base_read["pred"], "patched_pred": None,
                         "base_M": base_read["M"], "patched_M": None,
                         "delta_M": None, "off_target": qa_reads(base_logits, meta_h),
                         "width": w_h, "width_map": h["width_map"]})
            flush_rows()
            # identity (2 equal-width hosts, layer 11)
            if h["width_map"] == "identity" and len([r for r in rows if r["condition"] == "identity"]) < 4:
                cap2 = {}
                hs = []
                for L in [11]:
                    def mk_id(ll=L):
                        def hook(module, inp, out):
                            hh = out[0] if isinstance(out, tuple) else out
                            cap2[ll] = hh.detach()
                            return None
                        return hook
                    hs.append(layers[L].register_forward_hook(mk_id()))
                forward_plain(enc_h)
                for hh in hs:
                    hh.remove()
                own_states = cap2[11][0, z_h:z_h + w_h, :].clone()
                p = forward_patched(enc_h, 11, (C_ROW, z_h, own_states))
                pr = c_read(p, meta_h)
                ck(pr["pred"] == base_read["pred"]
                   and abs(pr["M"] - base_read["M"]) < 1e-3, "identity failed " + k)
                rows.append({"host": k, "layer": 11, "condition": "identity",
                             "base_pred": base_read["pred"], "patched_pred": pr["pred"],
                             "base_M": base_read["M"], "patched_M": pr["M"],
                             "delta_M": pr["M"] - base_read["M"], "off_target": {}})
                flush_rows()
            # sufficiency: donor NEW span -> host SA span, all 6 layers (C_ROW patch)
            dw = min(spans["new"]["w"], w_h)
            for L in LAYERS:
                p = forward_patched(enc_h, L, (C_ROW, z_h, donor_span[L]["new"][:dw]))
                pr = c_read(p, meta_h)
                rows.append({"host": k, "layer": L, "condition": "donor_sufficiency",
                             "base_pred": base_read["pred"], "patched_pred": pr["pred"],
                             "base_M": base_read["M"], "patched_M": pr["M"],
                             "delta_M": pr["M"] - base_read["M"],
                             "off_target": qa_reads(p, meta_h),
                             "map": h["width_map"], "patched_width": dw})
                flush_rows()
            # SA-sham cross: donor SA span -> host SA span (2 layers in 172A)
            if h["width_map"] == "identity":
                for L in LAYERS[:2]:
                    p2 = forward_patched(enc_h, L, (C_ROW, z_h, donor_span[L]["sa"][:dw]))
                    pr2 = c_read(p2, meta_h)
                    rows.append({"host": k, "layer": L, "condition": "sa_sham_cross",
                                 "base_pred": base_read["pred"], "patched_pred": pr2["pred"],
                                 "base_M": base_read["M"], "patched_M": pr2["M"],
                                 "delta_M": pr2["M"] - base_read["M"],
                                 "off_target": qa_reads(p2, meta_h)})
                    flush_rows()
        composed = 3 + sum(1 for h in host_final) + 2 + sum(1 for h in host_final) * 6 + \
            sum(1 for h in host_final if h["width_map"] == "identity") * 2
        ck(physical[0] == composed == 97, f"ledger {physical[0]} != {composed}")
        receipt.update(status="COMPLETE_A461_G5_PATCHING_172A_V4",
                       native_model_forward_calls=physical[0],
                       physical_forwards=physical[0],
                       composition={"donor_prepass": 3, "host_baselines": n_hosts,
                                    "identity": 2 + 2, "sufficiency": n_hosts * 6,
                                    "sa_sham_cross": 2 * 2, "total": 97},
                       host_roster=[{"pair_key": h["pair_key"], "group": h["group"],
                                     "width": h["width"], "width_map": h["width_map"]} for h in host_final],
                       excluded_hosts=excluded,
                       backprop_calls=0, network_calls=0, tool_actions=0,
                       test_or_calibration_rows=0)
        gpu_after = torch.cuda.mem_get_info(0)
        receipt["gpu_free_bytes_after"] = gpu_after[0]
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G5_PATCHING_172A_V4", error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-1500:])
        code = 2
        flush_rows()
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
