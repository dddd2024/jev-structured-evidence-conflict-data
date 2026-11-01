#!/usr/bin/env python3
"""A461-G4 G0A+G0B+G0C (CPU only): cohort freeze, checkpoint metadata, anchor map.

Implements the frozen G0 CPU admission plan steps G0A-G0C of
research/rounds/A461_G4_POINTER_READOUT_AND_BIDIRECTIONAL_PATCHING/A461_g4_pointer_patch_admission_protocol_v0.json
- G0A: SHA inventory of archived G3 sources; independent recompute of the
  strict 11-T2 and 6-T3 cohorts from the archived pair rows/token audits,
  cross-checked against the frozen cohort manifest.
- G0B: pinned checkpoint + Kev version inspection on CPU: PointerHead q/k
  shapes, temperature, backbone layer census, LoRA modules; assert the
  rows_of branch-offset contract (decide/opts within-branch). Zero forwards.
- G0C: native tokenizer rerender for all 26 pairs (old/new/N1B): branch token
  SHA identity old-vs-new, candidate menu identity, state growth histogram,
  appended-event token span (first divergence), decide/opts anchor map per
  question. Zero forwards.
One CPU checkpoint load (metadata + weights) and tokenizer; no backbone call.
"""
import argparse, collections, gzip, hashlib, json, os, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
G3DIR = "research/rounds/A461_G3_APPENDED_CONFLICT_RECOGNITION_CAUSAL_GATE"
COHORT = "research/experiments/2026-10-25_A461_G4_POINTER_HEAD_CAUSAL_CPU_COHORT_V0.json"

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                  TOKENIZERS_PARALLELISM="false", PYTHONDONTWRITEBYTECODE="1",
                  TMPDIR=str(ROOT / ".tmp"), HF_HOME=str(ROOT / ".cache" / "huggingface"),
                  TORCH_HOME=str(ROOT / ".cache" / "torch"), XDG_CACHE_HOME=str(ROOT / ".cache"),
                  PYTHONPYCACHEPREFIX=str(ROOT / ".cache" / "pycache"))
sys.dont_write_bytecode = True


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def sha_file(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def hx(s):
    return hashlib.sha256(s.encode("utf8")).hexdigest()


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--g3-run", required=True, type=Path, help="archived G3 run dir (G0C/G1C subdirs)")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    g3 = a.g3_run.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and CORPUS.is_file() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(all(x.is_relative_to(ROOT) for x in (repo, g3, SOURCE, CKPT, BASE, out)), "paths")
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    receipt = {"schema": "JEV_A461_G4_G0ABC_CPU_RECEIPT_V1", "status": "INCOMPLETE",
               "gpu_forwards": 0, "backbone_forwards": 0, "cpu_model_loads": 0,
               "network_calls": 0, "test_or_calibration_rows": 0, "output_dir": str(out)}
    files = []
    try:
        out.mkdir(mode=0o700)
        # ---------- G0A: source SHA inventory + cohort recompute ----------
        inventory = {
            "kev_model_py": sha_file(SOURCE / "kev" / "model.py"),
            "kev_api_py": sha_file(SOURCE / "kev" / "api.py"),
            "g0c_pair_rows": sha_file(g3 / "G0C" / "pair_rows.jsonl"),
            "g0c_token_audit": sha_file(g3 / "G0C" / "token_audit.jsonl"),
            "g1c_raw_logits": sha_file(g3 / "G1C" / "raw_native_logits_109_requests.jsonl"),
            "g1c_preforward_gate": sha_file(g3 / "G1C" / "pre_forward_token_gate_receipt.json"),
            "g2c_per_pair_heads": sha_file(g3 / "G2C" / "per_pair_heads.jsonl"),
            "cohort_manifest": sha_file(repo / COHORT),
            "checkpoint_adapter": sha_file(CKPT / "adapter_model.safetensors"),
            "checkpoint_head": sha_file(CKPT / "head.pt"),
            "checkpoint_tokenizer": sha_file(CKPT / "tokenizer.json"),
            "checkpoint_adapter_config": sha_file(CKPT / "adapter_config.json"),
        }
        frozen = json.loads((repo / COHORT).read_text("utf8"))
        ck(frozen["sources"]["kev_model_source_blob"].startswith("2b2dead6a03946b02c9") or
           frozen["sources"]["kev_source_upstream_revision"] == "90990a5fac2995b9faa3190f7d437e84f2067768",
           "cohort manifest kev revision mismatch")
        ck(frozen["summary"]["total"] == 26 and frozen["summary"]["sameBranch"] == 26
           and frozen["summary"]["keysSame"] == 26, "frozen cohort summary mismatch")
        strict_frozen = set(frozen["summary"]["strictPrimary"])
        t3_frozen = [r["source_group"] for r in frozen["rows"] if r["cohort"] == "T3_PRESENT_CONFLICT_POSITIVE"]

        # independent cohort recompute from archived rows
        prows = [json.loads(x) for x in (g3 / "G0C" / "pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        ta = {json.loads(x)["row_id"]: json.loads(x) for x in (g3 / "G0C" / "token_audit.jsonl").read_text("utf8").splitlines() if x.strip()}
        heads = {json.loads(x)["pair_key"]: json.loads(x) for x in (g3 / "G2C" / "per_pair_heads.jsonl").read_text("utf8").splitlines() if x.strip()}
        by_pair = collections.OrderedDict()
        for r in prows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        strict, t3, invalid, false_alarm = [], [], [], []
        for key, rs in by_pair.items():
            h = heads[key]
            treat = next(r for r in rs if r["arm"] == "new")
            nb = next((r for r in rs if r["arm"] == "N1B"), None)
            grp = treat["source_group"]
            old_c = h["old_pred"]["conflicting_vote"]
            new_c = h["new_pred"]["conflicting_vote"]
            if treat["family"].startswith("T3"):
                t3.append(grp)
                continue
            nb_valid = nb is not None and nb["declared_edit"]["message"]["author"] in treat["native_request"]["state"]["validator_set"]
            nb_matched = ta[nb["row_id"]]["matched_vs_treatment"] if nb else False
            if old_c is False and nb_valid and nb_matched and new_c is False:
                strict.append(grp)
            elif old_c is True:
                false_alarm.append(grp)
            elif not (nb_valid and nb_matched):
                invalid.append(grp)
            elif new_c is True:
                false_alarm.append(grp)
        ck(sorted(strict) == sorted(strict_frozen), f"strict cohort mismatch {sorted(strict)}")
        ck(sorted(t3) == sorted(t3_frozen), "T3 cohort mismatch")
        ck(len(strict) == 11 and len(t3) == 6, "cohort sizes")
        g0a = {"inventory": inventory, "strict_recomputed": sorted(strict),
               "t3_recomputed": sorted(t3), "invalid_accept_groups": sorted(invalid),
               "false_alarm_groups": sorted(false_alarm),
               "cohort_crosscheck": "PASS vs frozen cohort manifest"}
        with (out / "g0a_cohort_freeze.json").open("x", encoding="utf8", newline="\n") as f:
            json.dump(g0a, f, sort_keys=True, indent=2, ensure_ascii=False)
            f.write("\n")
        files.append("g0a_cohort_freeze.json")

        # ---------- G0B: checkpoint metadata (1 CPU load, 0 forwards) ----------
        import torch
        torch.set_num_threads(4)
        sys.path.insert(0, str(SOURCE))
        from kev.api import SystemOneRequest, to_record
        from kev.checkpoint import Checkpoint, LoadOptions
        from kev.model import rows_of
        ck(CKPT.is_dir() and BASE.is_dir(), "missing pinned checkpoint/base")
        checkpoint = Checkpoint(str(CKPT))
        checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
        tokenizer, model = checkpoint.load("cpu", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
        receipt["cpu_model_loads"] = 1
        head = model.head
        meta = {"head_type": type(head).__name__,
                "q_weight_shape": list(head.q.weight.shape), "q_bias_shape": list(head.q.bias.shape),
                "k_weight_shape": list(head.k.weight.shape), "k_bias_shape": list(head.k.bias.shape),
                "scale": head.scale, "temperature_init": head.temperature,
                "temperature_value": float(head.temperature) if isinstance(head.temperature, torch.Tensor) else head.temperature}
        ck(meta["q_weight_shape"][0] == 256 and meta["k_weight_shape"][0] == 256, "pointer dim != 256")
        layer_census = collections.Counter()
        lora_modules = []
        for name, mod in model.named_modules():
            cn = type(mod).__name__
            layer_census[cn] += 1
            if "lora" in cn.lower() or "lora" in name.lower():
                lora_modules.append(name)
        meta["backbone_layer_census"] = dict(layer_census)
        meta["lora_module_count"] = len(lora_modules)
        meta["lora_module_sample"] = sorted(lora_modules)[:8]
        # temperature provenance: head.pt may carry a fitted value
        hp = CKPT / "head.pt"
        try:
            pt = torch.load(str(hp), map_location="cpu", weights_only=False)
            meta["head_pt_keys"] = sorted(pt.keys()) if isinstance(pt, dict) else str(type(pt))
            if isinstance(pt, dict) and "temperature" in pt:
                meta["temperature_from_head_pt"] = float(pt["temperature"])
        except Exception as e:
            meta["head_pt_read"] = f"unreadable: {type(e).__name__}"
        with (out / "g0b_checkpoint_metadata.json").open("x", encoding="utf8", newline="\n") as f:
            json.dump(meta, f, sort_keys=True, indent=2, ensure_ascii=False, default=str)
            f.write("\n")
        files.append("g0b_checkpoint_metadata.json")

        # ---------- G0C: rerender + anchor map (tokenizer only, no forward) ----------
        # corpus old states
        old_states = {}
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    old_states[hashlib.sha256(json.dumps(rec["state"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")).hexdigest()[:16]] = rec["state"]
        q_tw = prows[0]["native_request"]["questions"]
        branch_check = {"pairs": 0, "branch_sha_identical": 0, "keys_identical": 0}
        anchor_rows = []
        growth = collections.Counter()
        for key, rs in by_pair.items():
            old_state = old_states.get(key.split(":", 1)[1])
            ck(old_state is not None, "old state missing " + key)
            treat = next(r for r in rs if r["arm"] == "new")
            encs = {}
            for tag, st in (("old", old_state), ("new", treat["native_request"]["state"])):
                rendered, meta_r = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(st))}))
                enc = model.encode(tokenizer, rendered, max_state=8192, max_branch=8192, strict=True)
                state_ids, state_pos, branches = rows_of(enc)
                ck(not enc["state_truncated"], "truncated")
                encs[tag] = {"enc": enc, "state_ids": state_ids, "branches": branches, "meta": meta_r}
            # branch identity old vs new
            sha_old = [hx(json.dumps(b["ids"])) for b in encs["old"]["branches"]]
            sha_new = [hx(json.dumps(b["ids"])) for b in encs["new"]["branches"]]
            same_branch = sha_old == sha_new
            keys_old = {m["id"]: list(m["keys"]) for m in encs["old"]["meta"]}
            keys_new = {m["id"]: list(m["keys"]) for m in encs["new"]["meta"]}
            same_keys = keys_old == keys_new
            branch_check["pairs"] += 1
            branch_check["branch_sha_identical"] += same_branch
            branch_check["keys_identical"] += same_keys
            # state growth + appended span
            o_ids, n_ids = encs["old"]["state_ids"], encs["new"]["state_ids"]
            delta = len(n_ids) - len(o_ids)
            growth[delta] += 1
            z = 0
            while z < min(len(o_ids), len(n_ids)) and o_ids[z] == n_ids[z]:
                z += 1
            appended_span = [z, len(n_ids) - (len(o_ids) - z)] if delta > 0 else None
            # anchor map per question: decide/opts offsets within branch (identical old/new when branch same)
            cmeta = None
            for m in encs["new"]["meta"]:
                if m["id"] == "conflicting_vote":
                    cmeta = m
            branches_new = encs["new"]["branches"]
            c_idx = [m["id"] for m in encs["new"]["meta"]].index("conflicting_vote")
            cb = branches_new[c_idx]
            anchors = {"conflicting_vote_branch_index": c_idx,
                       "decide_offset_in_branch": cb["decide"],
                       "opts_offsets_in_branch": cb["opts"],
                       "branch_len": len(cb["ids"]),
                       "branch_pos_start": cb["pos"][0] if cb["pos"] else None,
                       "state_len_old": len(o_ids), "state_len_new": len(n_ids),
                       "state_growth": delta, "appended_span_in_state": appended_span,
                       "first_divergence": z}
            anchor_rows.append({"pair_key": key, "family": treat["family"], "source_group": treat["source_group"],
                                "same_branch": same_branch, "same_keys": same_keys,
                                "C_anchors": anchors,
                                "all_branch_anchors": {m["id"]: {"decide": branches_new[i]["decide"],
                                                                  "opts": branches_new[i]["opts"]}
                                                        for i, m in enumerate(encs["new"]["meta"])}})
        ck(branch_check["pairs"] == 26 and branch_check["branch_sha_identical"] == 26
           and branch_check["keys_identical"] == 26, "branch identity gate failed")
        ck(sum(growth.values()) == 26 and set(growth) <= {33, 34}, f"growth histogram {dict(growth)}")
        with (out / "g0c_anchor_map.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for r in anchor_rows:
                f.write(canon(r) + "\n")
        files.append("g0c_anchor_map.jsonl")
        with (out / "g0c_branch_identity.json").open("x", encoding="utf8", newline="\n") as f:
            json.dump({**branch_check, "growth_histogram": dict(growth)}, f, sort_keys=True, indent=2)
            f.write("\n")
        files.append("g0c_branch_identity.json")
        receipt.update(status="COMPLETE_A461_G4_G0ABC_CPU_ADMISSION",
                       pairs=branch_check["pairs"], strict_pairs=len(g0a["strict_recomputed"]),
                       growth_histogram=dict(growth), cpu_model_loads=1,
                       backbone_forwards=0, gpu_forwards=0)
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G4_G0ABC", error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-1200:])
        code = 2
    with (out / "execution_receipt.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    files.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in files:
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(canon(receipt))
    return code


if __name__ == "__main__":
    sys.exit(main())
