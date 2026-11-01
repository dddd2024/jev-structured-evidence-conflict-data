#!/usr/bin/env python3
"""A461-MECH-M4 runner CPU self-test (zero GPU; every subprocess CUDA_VISIBLE_DEVICES="").
Same gate/ledger/refusal tests as M3 (A461_mech_m3_selftest_v1.py), plus the key-class split (contributions
partition the keys and sum to the o_proj input), distinct outputs of the 14 arms, and source = target identity
for every op (full bitwise; only / drop / vswap within float tolerance)."""
import argparse, collections, hashlib, importlib.util, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_mech_m4_runner_v1.py"
STAGE = "A461_MECH_M4_KEYCLASS_VALUE_GPU"
TOTAL, PLAN = 2956, [128] * 23 + [12]
RESULTS = []
# R2: children died with "libgomp: Thread creation failed" under the shared per-user thread limit
THREADS = {"OMP_NUM_THREADS": "8", "MKL_NUM_THREADS": "8"}
os.environ.update(THREADS)


def rec(name, ok, ev):
    RESULTS.append({"test": name, "verdict": "PASS" if ok else "FAIL", "evidence": ev})
    print(("PASS " if ok else "FAIL ") + name + " :: " + ev[:200], flush=True)


def guarded(name, fn):
    try:
        ok, ev = fn()
    except Exception as err:
        ok, ev = False, f"test raised {type(err).__name__}: {str(err)[:200]}"
    rec(name, ok, ev)


def receipt(d):
    return json.loads((Path(d) / "execution_receipt.json").read_text("utf8"))


def rows(d):
    p = Path(d) / "raw_native_logits_m4.jsonl"
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--g10-cf", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    (out / "_adm").mkdir()
    quota = out / "_quota"
    quota.mkdir()
    spec = importlib.util.spec_from_file_location("m4", RUNNER)
    rb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rb)
    runner_blob = rb.file_blob(RUNNER)

    def adm(name, **kw):
        p = out / "_adm" / f"{name}.json"
        p.write_text(json.dumps(kw) + "\n", encoding="utf8")
        return p

    def fake_adm(name, aid, approved=TOTAL, batches=len(PLAN)):
        return adm(name, stage=STAGE, mode="L1_FAKE", admission_id=aid, approved_max_native_forwards=approved,
                   approved_batches=batches)

    def gpu_adm(name, **over):
        base = dict(stage=STAGE, mode="GPU", admission_id="SELFTEST_SYNTH_M4_0001",
                    selftest_synthetic_not_an_authorization=True,
                    governance="JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2",
                    user_gpu_approval_quote="self-test synthetic quote (not a real approval)",
                    user_gpu_approval_utc="1970-01-01T00:00:00Z", approved_runner_blob=runner_blob,
                    explicit_user_gpu_approval=True, approved_max_native_forwards=TOTAL, approved_batches=len(PLAN),
                    approved_batch_plan=PLAN,
                    frozen_inputs={"manifest_blob": rb.BLOB_MANIFEST, "design_blob": rb.BLOB_DESIGN,
                                   "m1_raw_blob": rb.BLOB_M1_RAW, "g10_counterfactuals_blob": rb.BLOB_G10_CF, "m3_raw_blob": rb.BLOB_M3_RAW,
                                   "roster_blob": rb.BLOB_ROSTER,
                                   "g5v2_questions_blob": rb.BLOB_G5V2, "corpus_sha256": rb.CORPUS_SHA},
                    model_identity_sha256=rb.v4.identity_digest(rb.v4.MODEL_IDENTITY))
        base.update(over)
        return adm(name, **base)

    def run(name, admission, backend="fake", mode=None, extra=(), fault="none", manifest=None, g10=None):
        cmd = [sys.executable, str(RUNNER), "--repo-root", str(a.repo_root), "--admission", str(admission),
               "--manifest", str(manifest or a.manifest), "--m1-raw", str(a.m1_raw),
               "--g10-cf", str(g10 or a.g10_cf), "--m3-raw", str(a.m3_raw),
               "--backend", backend, "--out", str(out / name), *extra]
        if mode:
            cmd.append(mode)
        if backend == "fake" and mode is None:
            cmd += ["--quota-root", str(quota)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10800,
                           env=dict(os.environ, CUDA_VISIBLE_DEVICES="", FAKE_FAULT=fault, **THREADS))
        # keep every child's exit code and output tail (R1 lost two children without a receipt)
        (out / f"_child_{name}.log").write_text(
            f"returncode={r.returncode}" + chr(10) + "--- stdout ---" + chr(10) + r.stdout[-4000:] + chr(10)
            + "--- stderr ---" + chr(10) + r.stderr[-8000:] + chr(10), encoding="utf8")
        return r

    run("T1_preflight", fake_adm("pf", "SELFTEST_PF_0001"), mode="--preflight-only")
    guarded("preflight_token_and_span_gates_on_real_manifest", lambda: (
        receipt(out / "T1_preflight")["status"] == "COMPLETE_A461_MECH_M4_PREFLIGHT"
        and receipt(out / "T1_preflight")["preflight"] == {"scenes": 22, "token_gate": "PASS", "span_gate": "PASS",
                                                          "manifest_rows": TOTAL},
        f"{receipt(out / 'T1_preflight')['preflight']}"))

    run("T2_fullpath", fake_adm("full", "SELFTEST_FULL_0001"))
    r2, x2 = receipt(out / "T2_fullpath"), rows(out / "T2_fullpath")
    caps = [x for x in x2 if x.get("capture_file")]

    def t_full():
        brs = [(b["run"], b["planned"], b["physical"], b["status"]) for b in r2["batch_receipts"]]
        cond = collections.Counter(x["condition"] for x in x2)
        files = sorted((out / "T2_fullpath" / "captures").iterdir())
        d = out / "T2_fullpath" / "captures"
        ok_files = all(hashlib.sha256((d / c[k]["name"]).read_bytes()).hexdigest() == c[k]["sha256"]
                       for c in caps for k in ("capture_file", "class_file"))
        shapes = all(c["capture_file"]["shape"] == [4, c["capture"]["span"][1] - c["capture"]["span"][0], 64]
                     for c in caps)
        return (r2["status"] == "COMPLETE_A461_MECH_M4" and len(x2) == TOTAL
                and [x["forward_index"] for x in x2] == list(range(1, TOTAL + 1))
                and brs == [(k, 128, 128, "COMPLETE") for k in range(1, 24)] + [(24, 12, 12, "COMPLETE")]
                and r2["physical_prehook_calls"] == TOTAL and r2["denied_prehook_calls"] == 0
                and r2["durable_appends"]["raw_rows"] == TOTAL and len(caps) == 44 and len(files) == 88
                and ok_files and shapes
                and len([k for k in cond if k.startswith("patch_m4_")]) == 28
                and all(v == 104 for k, v in cond.items() if k.startswith("patch_m4_"))
                # fake explicit-softmax attention is batched over rows: float32 rounding only (<= 1e-6)
                and all(c["cross_row_max_absdiff"] <= 1e-6 for c in caps),
                f"status={r2['status']} rows={len(x2)} batches={len(brs)} captures={len(caps)} files={len(files)} "
                f"(sha ok={ok_files}, shapes ok={shapes}); cross-row max {max(c['cross_row_max_absdiff'] for c in caps):.1e}")
    guarded("fake_full_path_2956_with_44_captures_and_class_files", t_full)
    def t_readout():
        import torch
        d = out / "T2_fullpath" / "captures"
        worst_file = 0.0
        for c in caps:
            x = torch.load(d / c["capture_file"]["name"], weights_only=True).float()[0]
            k = torch.load(d / c["class_file"]["name"], weights_only=True)
            ok = sorted(k["contrib"]) == sorted(["PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT"])
            if not ok or list(k["partner_values"].shape)[1] != 33 or list(k["partner_attention"].shape)[2] != 33:
                return False, f"class file layout at {c['capture']['tag']}"
            worst_file = max(worst_file, float((sum(t.float() for t in k["contrib"].values()) - x).abs().max()))
        recon = max(c["attn_readout_recon_maxabs"] for c in caps)
        add = max(c["class_additivity_maxabs"] for c in caps)
        return (recon < 1e-5 and add < 1e-5 and worst_file < 1e-2,
                f"5 class contributions sum to the forward's o_proj input (max abs {add:.2e}; saved fp16 files "
                f"{worst_file:.1e}); attention readout reconstructs it ({recon:.2e})")
    guarded("class_contributions_partition_and_sum_to_oproj_input", t_readout)
    def t_heads():
        lg = {(x["donor"], x["host"], x["patch"]["arm"], x["source_kind"]): json.dumps(x["questions"])
              for x in x2 if x.get("patch")}
        keys = {(d, h, src) for (d, h, _a, src) in lg}
        arms = sorted({a_ for (_d, _h, a_, _s) in lg})
        distinct = sum(len({lg[(d, h, arm, src)] for arm in arms}) == len(arms) for d, h, src in keys)
        cnt = collections.Counter(x["patch"]["arm"] for x in x2 if x.get("patch"))
        ops_ok = all((x["patch"]["op"], x["patch"]["classes"]) == (
            ("full", []) if x["patch"]["arm"] == "full"
            else ("vswap", ["PARTNER"]) if x["patch"]["arm"] == "vswap_PARTNER"
            else (x["patch"]["arm"].split("_", 1)[0],
                  ["PARTNER", "ROUND_PEERS"] if x["patch"]["arm"].endswith("ROUNDVOTES") else [x["patch"]["arm"].split("_", 1)[1]]))
            for x in x2 if x.get("patch"))
        return (distinct == len(keys) == 208 and len(arms) == 14 and set(cnt.values()) == {208} and ops_ok,
                f"14 arms give 14 distinct outputs in {distinct}/{len(keys)} (cell, source); {len(arms)} arms x 208; "
                f"op/classes match arm names: {ops_ok}")
    guarded("fourteen_arms_distinct_outputs", t_heads)
    def t_allrows():
        base = {(x["target_scene"], x["target_arm"]): {q["id"]: q["logits"] for q in x["questions"]} for x in x2
                if x.get("capture") and x.get("source_kind") == "host"}
        pr = [x for x in x2 if x.get("patch")]
        moved = sum({q["id"]: q["logits"] for q in x["questions"]}["conflicting_vote"] != base[(x["target_scene"], x["target_arm"])]["conflicting_vote"]
                    and {q["id"]: q["logits"] for q in x["questions"]}["certificate_action"] != base[(x["target_scene"], x["target_arm"])]["certificate_action"]
                    for x in pr)
        return (len(base) == 16 and len(pr) == 2912 and moved == 2912,
                f"host baselines={len(base)}; all-row patches moving both C and action rows: {moved}/{len(pr)}")
    guarded("all_row_patches_reach_c_and_action", t_allrows)

    # identity patches: the host's OWN capture as source and target must leave the forward unchanged: full
    # bitwise; only / drop / vswap rebuild the o_proj input from class contributions (float32 rounding)
    man = [json.loads(x) for x in a.manifest.read_text("utf8").splitlines() if x.strip()]
    caps_rows = [m for m in man if m["phase"] == "capture"]
    h0 = next(m for m in caps_rows if m["source_kind"] == "host" and m["target_arm"] == "new")
    ident = []
    for arm in ("full", "only_PARTNER", "drop_SELF", "only_ROUNDVOTES", "drop_CONTEXT", "vswap_PARTNER"):
        t = dict(next(m for m in man if m["phase"] == "patch" and m["target_scene"] == h0["target_scene"]
                      and m["patch"]["arm"] == arm and m["target_arm"] == "new"))
        t["patch"] = dict(t["patch"], source=h0["capture"]["tag"])
        t["bitwise_vs_m3"] = None
        ident.append(t)
    mini = [dict(m, forward_index=i + 1, run=1) for i, m in enumerate(caps_rows + ident)]
    mini_p = out / "_identity_manifest.jsonl"
    mini_p.write_text("".join(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n" for m in mini), encoding="utf8")
    run("T6_identity", fake_adm("ident", "SELFTEST_IDENT_0001", approved=len(mini), batches=1), manifest=mini_p,
        extra=("--expect-batches", str(len(mini)), "--allow-manifest-blob", rb.file_blob(mini_p)))

    def t_identity():
        x6 = rows(out / "T6_identity")
        base = next(x for x in x6 if x.get("capture") and x["target_scene"] == h0["target_scene"]
                    and x["target_arm"] == "new")
        pr = {x["patch"]["arm"]: x for x in x6 if x.get("patch")}
        dev = {a_: max(abs(u - v) for q, qb in zip(x["questions"], base["questions"])
                       for u, v in zip(q["logits"], qb["logits"])) for a_, x in pr.items()}
        return (receipt(out / "T6_identity")["status"] == "COMPLETE_A461_MECH_M4" and len(pr) == 6
                and pr["full"]["questions"] == base["questions"] and max(dev.values()) <= 1e-4,
                f"host-own source = target: full bitwise no-op; max |logit diff| per op "
                + ", ".join(f"{k} {v:.1e}" for k, v in sorted(dev.items())))
    guarded("identity_source_equals_target_every_op", t_identity)
    def t_variants():
        cf = json.loads(a.g10_cf.read_text("utf8"))
        cap = {(x["target_scene"], x["target_arm"]): x for x in caps}
        good = sum(cap[(s, arm)]["token_ids_sha256"] == cf[s]["ROUND"]["token_ids_sha256"]
                   and cap[(s, arm)]["capture"]["span"] == cf[s]["ROUND"]["span"]
                   and cap[(s, arm)]["token_ids_sha256"] != cap[(s, "new")]["token_ids_sha256"]
                   for (s, arm) in cap if arm == "ROUND")
        src = collections.Counter(x["patch"]["source"].split(":")[0] for x in x2 if x.get("patch"))
        tg = collections.Counter(x["patch"]["target"].split(":")[0] for x in x2 if x.get("patch"))
        return (good == 22 and src == {"new": 1560, "ROUND": 1352} and tg == {"new": 2808, "ROUND": 104},
                f"ROUND captures (14 donors + 8 hosts) with G1.0 token sha + span, distinct from new: {good}/22; "
                f"patch sources {dict(src)}, targets {dict(tg)}")
    guarded("round_arms_rebuilt_from_g10_and_used_as_sources", t_variants)

    bad_cf = out / "_tampered_g10.json"
    bad_cf.write_text(a.g10_cf.read_text("utf8").replace('"round": 1', '"round": 9', 1), encoding="utf8")
    run("T5_tampered_g10", fake_adm("pf2", "SELFTEST_PF_0002"), mode="--preflight-only", g10=bad_cf)
    guarded("tampered_g10_counterfactuals_refused", lambda: (
        receipt(out / "T5_tampered_g10")["status"] == "FAIL_A461_MECH_M4"
        and "G1.0 counterfactuals blob pin" in receipt(out / "T5_tampered_g10")["error_message"],
        "one variant round edited: refused at the blob pin"))

    run("T3_extra_lm_call", fake_adm("dbl", "SELFTEST_DBL_0001"), fault="doublefire@50")
    guarded("extra_lm_call_refused_at_prehook", lambda: (
        receipt(out / "T3_extra_lm_call")["status"] == "FAIL_A461_MECH_M4"
        and "LM pre-hook refused" in receipt(out / "T3_extra_lm_call")["error_message"]
        and receipt(out / "T3_extra_lm_call")["denied_prehook_calls"] == 1
        and receipt(out / "T3_extra_lm_call")["physical_prehook_calls"] == 50
        and len(rows(out / "T3_extra_lm_call")) == 49,
        "2nd LM call inside reserved call 50 denied before LM body; physical 50, rows 49"))

    run("T4_reuse", fake_adm("full", "SELFTEST_FULL_0001"))
    guarded("same_approval_reuse_refused_by_ledger", lambda: (
        receipt(out / "T4_reuse")["status"] == "FAIL_A461_MECH_M4"
        and f"ledger consumed {TOTAL}" in receipt(out / "T4_reuse")["error_message"]
        and receipt(out / "T4_reuse")["model_loads"] == 0,
        f"same admission from a new out dir after a complete {TOTAL}-call run: refused, 0 loads"))

    run("P1_gpu_pre_model", gpu_adm("gpu_ok"), backend="gpu", mode="--pre-model-gate-only")
    guarded("gpu_policy_v2_admission_reaches_pre_model_gate", lambda: (
        receipt(out / "P1_gpu_pre_model")["status"] == "COMPLETE_A461_MECH_M4_PRE_MODEL_GATE"
        and receipt(out / "P1_gpu_pre_model")["model_identity_verified"] is True
        and receipt(out / "P1_gpu_pre_model")["model_loads"] == 0
        and receipt(out / "P1_gpu_pre_model")["cuda_initialized"] is False
        and not rb.GPU_QUOTA_ROOT.exists(),
        "synthetic policy-V2 GPU admission passes all gates and stops before load; real ledger untouched"))
    tampered = out / "_tampered_manifest.jsonl"
    lines = a.manifest.read_text("utf8").splitlines()
    t0 = json.loads(lines[300])
    t0["patch"]["classes"] = ["SELF"] if t0["patch"]["classes"] != ["SELF"] else ["CONTEXT"]
    lines[300] = json.dumps(t0, sort_keys=True, separators=(",", ":"))
    tampered.write_text("\n".join(lines) + "\n", encoding="utf8")
    run("P2_gpu_tampered_manifest", gpu_adm("gpu_ok2"), backend="gpu", mode="--pre-model-gate-only", manifest=tampered)
    guarded("gpu_tampered_manifest_refused", lambda: (
        "manifest blob override refused" in receipt(out / "P2_gpu_tampered_manifest")["error_message"],
        "manifest with one patch row's key classes changed: refused before load"))
    run("P3_gpu_plan_override", gpu_adm("gpu_ok3"), backend="gpu", mode="--pre-model-gate-only",
        extra=("--expect-batches", ",".join(["128"] * 23 + ["11", "1"])))
    guarded("gpu_plan_override_refused", lambda: (
        receipt(out / "P3_gpu_plan_override")["status"] == "FAIL_A461_MECH_M4"
        and receipt(out / "P3_gpu_plan_override")["model_loads"] == 0,
        f"refused: {receipt(out / 'P3_gpu_plan_override')['error_message'][:80]}"))
    rr = run("P4_full_gpu_outside_runs_root", gpu_adm("gpu_ok4"), backend="gpu")
    guarded("full_gpu_run_outside_runs_root_refused", lambda: (
        rr.returncode != 0 and not (out / "P4_full_gpu_outside_runs_root").exists()
        and "M4_GPU_RUNS" in rr.stderr, "refused before mkdir"))
    guarded("no_gpu_in_selftest", lambda: (
        all(receipt(d)["gpu_model_loads"] == 0 and receipt(d)["cuda_initialized"] is False
            for d in out.iterdir() if (d / "execution_receipt.json").exists())
        and not rb.GPU_RUNS_ROOT.exists(), "all receipts: gpu_model_loads=0, CUDA never initialized"))

    ok = all(r["verdict"] == "PASS" for r in RESULTS)
    res = {"schema": "JEV_A461_MECH_M4_SELFTEST_V1", "status": "PASS" if ok else "FAIL",
           "passed": sum(r["verdict"] == "PASS" for r in RESULTS), "tests": len(RESULTS), "runner_blob": runner_blob,
           "manifest_blob": rb.file_blob(a.manifest), "results": RESULTS, "gpu_calls": 0}
    (out / "selftest_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("status", "passed", "tests", "runner_blob", "manifest_blob")}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
