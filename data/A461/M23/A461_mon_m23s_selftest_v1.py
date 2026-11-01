#!/usr/bin/env python3
"""A461-MON-M23 (M23S) self-test, derived from the M22 one by A461_mon_m23_derive_v1.py: 248 rows, arms
{new, TWIN}; the span test requires the emb-layer span mean of new == TWIN (byte-identical span) while the full
token sequences differ. Parent docstring follows.
A461-MON-M23S runner (SecJev-0.8B) CPU self-test (zero GPU; every subprocess CUDA_VISIBLE_DEVICES="").
Preflight on the real 620-row manifest; the fake full path (620 rows, 620 feature files, batches, sha, shapes, span
rows agree); the decision position is the one the head reads (fake model: the saved last-token state after the final
layer times the fake head reproduces the logged certificate_action logits); span means are of the frozen span (the
emb-layer span mean of new and ROUND differ, the old arm has the 33-token last item); refusals: tampered manifest
token sha, tampered Stage-A raw (blob pin), an extra LM call (pre-hook), approval reuse (ledger), GPU admission gates
(synthetic policy-V2 admission reaches the pre-model gate; tampered manifest, plan override and a run outside the runs
root are refused); no GPU anywhere."""
import argparse, collections, hashlib, importlib.util, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_mon_m23s_runner_v1.py"
STAGE = "A461_MON_M23_TWIN_PROBE_GPU"
RESULTS = []
THREADS = {"OMP_NUM_THREADS": "24", "MKL_NUM_THREADS": "24"}
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
    p = Path(d) / "raw_native_logits_m23s.jsonl"
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    (out / "_adm").mkdir()
    quota = out / "_quota"
    quota.mkdir()
    spec = importlib.util.spec_from_file_location("m23s", RUNNER)
    rb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rb)
    runner_blob = rb.file_blob(RUNNER)
    PLAN, TOTAL = rb.FROZEN_BATCHES, rb.FROZEN_TOTAL

    def adm(name, **kw):
        p = out / "_adm" / f"{name}.json"
        p.write_text(json.dumps(kw) + "\n", encoding="utf8")
        return p

    def fake_adm(name, aid, approved=TOTAL, batches=len(PLAN)):
        return adm(name, stage=STAGE, mode="L1_FAKE", admission_id=aid, approved_max_native_forwards=approved,
                   approved_batches=batches)

    def gpu_adm(name, **over):
        base = dict(stage=STAGE, mode="GPU", admission_id="SELFTEST_SYNTH_M23S_0001",
                    selftest_synthetic_not_an_authorization=True,
                    governance="JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2",
                    user_gpu_approval_quote="self-test synthetic quote (not a real approval)",
                    user_gpu_approval_utc="1970-01-01T00:00:00Z", approved_runner_blob=runner_blob,
                    explicit_user_gpu_approval=True, approved_max_native_forwards=TOTAL, approved_batches=len(PLAN),
                    approved_batch_plan=PLAN,
                    frozen_inputs={"manifest_blob": rb.BLOB_MANIFEST, "design_blob": rb.BLOB_DESIGN,
                                   "stage_a_raw_blob": rb.BLOB_STAGE_A_RAW, "roster_blob": rb.BLOB_ROSTER,
                                   "g5v2_questions_blob": rb.BLOB_G5V2, "corpus_sha256": rb.CORPUS_SHA},
                    model_identity_sha256=rb.v4.identity_digest(rb.v4.MODEL_IDENTITY))
        base.update(over)
        return adm(name, **base)

    def run(name, admission, backend="fake", mode=None, extra=(), fault="none", manifest=None, stage_a=None):
        cmd = [sys.executable, str(RUNNER), "--repo-root", str(a.repo_root), "--admission", str(admission),
               "--manifest", str(manifest or a.manifest), "--design", str(a.design),
               "--stage-a-raw", str(stage_a or a.stage_a_raw), "--backend", backend, "--out", str(out / name), *extra]
        if mode:
            cmd.append(mode)
        if backend == "fake" and mode is None:
            cmd += ["--quota-root", str(quota)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10800,
                           env=dict(os.environ, CUDA_VISIBLE_DEVICES="", FAKE_FAULT=fault, **THREADS))
        (out / f"_child_{name}.log").write_text(
            f"returncode={r.returncode}" + chr(10) + "--- stdout ---" + chr(10) + r.stdout[-4000:] + chr(10)
            + "--- stderr ---" + chr(10) + r.stderr[-8000:] + chr(10), encoding="utf8")
        return r

    man = [json.loads(x) for x in a.manifest.read_text("utf8").splitlines() if x.strip()]
    run("T1_preflight", fake_adm("pf", "SELFTEST_PF_0001"), mode="--preflight-only")
    guarded("preflight_token_and_span_gates_on_real_manifest", lambda: (
        receipt(out / "T1_preflight")["status"] == "COMPLETE_A461_MON_M23S_PREFLIGHT"
        and receipt(out / "T1_preflight")["preflight"] == {"scenes": 124, "token_gate": "PASS", "span_gate": "PASS",
                                                          "manifest_rows": TOTAL},
        f"{receipt(out / 'T1_preflight')['preflight']}"))

    run("T2_fullpath", fake_adm("full", "SELFTEST_FULL_0001"))
    r2, x2 = receipt(out / "T2_fullpath"), rows(out / "T2_fullpath")
    d2 = out / "T2_fullpath" / "captures"

    def t_full():
        brs = [(b["run"], b["planned"], b["physical"], b["status"]) for b in r2["batch_receipts"]]
        files = sorted(d2.iterdir())
        sha_ok = all(hashlib.sha256((d2 / x["capture_file"]["name"]).read_bytes()).hexdigest() == x["capture_file"]["sha256"]
                     for x in x2)
        shp = all(x["capture_file"]["span_mean_shape"] == [7, 64]
                  and x["capture_file"]["attn11_span_shape"] == [x["span"][1] - x["span"][0], 64] for x in x2)
        arms = collections.Counter(x["target_arm"] for x in x2)
        xr = max(x["cross_row_max_absdiff"] for x in x2)
        return (r2["status"] == "COMPLETE_A461_MON_M23S" and len(x2) == TOTAL
                and [x["forward_index"] for x in x2] == list(range(1, TOTAL + 1))
                and brs == [(k + 1, n, n, "COMPLETE") for k, n in enumerate(PLAN)]
                and r2["physical_prehook_calls"] == TOTAL and r2["denied_prehook_calls"] == 0
                and r2["durable_appends"]["raw_rows"] == TOTAL and len(files) == TOTAL and sha_ok and shp
                and arms == {k: 124 for k in ("new", "TWIN")} and xr <= 1e-4,
                f"status={r2['status']} rows={len(x2)} files={len(files)} sha={sha_ok} shapes={shp} arms={dict(arms)}; "
                f"span rows agree within {xr:.1e} (fake float32; the GPU run requires 0)")
    guarded("fake_full_path_248_rows_and_feature_files", t_full)

    def t_decision():
        import torch
        sys.path.insert(0, str(HERE))
        from A461_mech_m3_fake_attention_model_v1 import FakePatchModel
        head = FakePatchModel(n_layers=24).head
        worst, n = 0.0, 0
        for x in x2[:40]:
            f = torch.load(d2 / x["capture_file"]["name"], weights_only=True)
            ca = next(q for q in x["questions"] if q["id"] == "certificate_action")
            got = f["last"][f["names"].index("L23")] @ head[:, :len(ca["keys"])]
            worst = max(worst, float((got - torch.tensor(ca["logits"])).abs().max()))
            n += 1
        ok_pos = all(x["decision_row"] == [q["id"] for q in x["questions"]].index("certificate_action") for x in x2)
        return (worst <= 1e-4 and ok_pos,
                f"saved last-token state after layer 31 x fake head reproduces the certificate_action logits in {n} rows "
                f"(max abs {worst:.1e}); decision row = the certificate_action row: {ok_pos}")
    guarded("decision_position_is_the_head_readout", t_decision)

    def t_span():
        import torch
        by = {(x["target_scene"], x["target_arm"]): x for x in x2}
        same, tokdiff = 0, 0
        for s in {x["target_scene"] for x in x2}:
            fn = torch.load(d2 / by[(s, "new")]["capture_file"]["name"], weights_only=True)
            ft = torch.load(d2 / by[(s, "TWIN")]["capture_file"]["name"], weights_only=True)
            same += bool(torch.equal(fn["span_mean"][0], ft["span_mean"][0]))
            tokdiff += by[(s, "new")]["token_ids_sha256"] != by[(s, "TWIN")]["token_ids_sha256"]
        return (same == 124 and tokdiff == 124,
                f"emb-layer span mean of new == TWIN in {same}/124 scenes (byte-identical span); full token "
                f"sequences differ in {tokdiff}/124")
    guarded("span_features_cover_the_frozen_span", t_span)

    bad = [dict(m) for m in man]
    bad[5]["token_ids_sha256"] = "0" * 64
    bad_p = out / "_bad_token_manifest.jsonl"
    bad_p.write_text("".join(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n" for m in bad), encoding="utf8")
    run("T3_bad_token", fake_adm("bt", "SELFTEST_BT_0001"), mode="--preflight-only", manifest=bad_p,
        extra=("--allow-manifest-blob", rb.file_blob(bad_p)))
    guarded("tampered_manifest_token_sha_refused", lambda: (
        receipt(out / "T3_bad_token")["status"] == "FAIL_A461_MON_M23S"
        and "token gate" in receipt(out / "T3_bad_token")["error_message"],
        f"refused: {receipt(out / 'T3_bad_token')['error_message'][:80]}"))
    bad_a = out / "_tampered_stage_a.jsonl"
    bad_a.write_text(a.stage_a_raw.read_text("utf8").replace('"arm":"old"', '"arm":"OLD"', 1)
                     .replace('"arm": "old"', '"arm": "OLD"', 1), encoding="utf8")
    run("T4_tampered_stage_a", fake_adm("pf2", "SELFTEST_PF_0002"), mode="--preflight-only", stage_a=bad_a)
    guarded("tampered_stage_a_raw_refused", lambda: (
        receipt(out / "T4_tampered_stage_a")["status"] == "FAIL_A461_MON_M23S"
        and "Stage-A raw blob pin" in receipt(out / "T4_tampered_stage_a")["error_message"],
        "one Stage-A row edited: refused at the blob pin"))
    run("T5_extra_lm_call", fake_adm("dbl", "SELFTEST_DBL_0001"), fault="doublefire@50")
    guarded("extra_lm_call_refused_at_prehook", lambda: (
        receipt(out / "T5_extra_lm_call")["status"] == "FAIL_A461_MON_M23S"
        and "LM pre-hook refused" in receipt(out / "T5_extra_lm_call")["error_message"]
        and receipt(out / "T5_extra_lm_call")["denied_prehook_calls"] == 1
        and receipt(out / "T5_extra_lm_call")["physical_prehook_calls"] == 50
        and len(rows(out / "T5_extra_lm_call")) == 49,
        "2nd LM call inside reserved call 50 denied before LM body; physical 50, rows 49"))
    run("T6_reuse", fake_adm("full", "SELFTEST_FULL_0001"))
    guarded("same_approval_reuse_refused_by_ledger", lambda: (
        receipt(out / "T6_reuse")["status"] == "FAIL_A461_MON_M23S"
        and f"ledger consumed {TOTAL}" in receipt(out / "T6_reuse")["error_message"]
        and receipt(out / "T6_reuse")["model_loads"] == 0,
        f"same admission after a complete {TOTAL}-call run: refused, 0 loads"))
    run("P1_gpu_pre_model", gpu_adm("gpu_ok"), backend="gpu", mode="--pre-model-gate-only")
    guarded("gpu_policy_v2_admission_reaches_pre_model_gate", lambda: (
        receipt(out / "P1_gpu_pre_model")["status"] == "COMPLETE_A461_MON_M23S_PRE_MODEL_GATE"
        and receipt(out / "P1_gpu_pre_model")["model_identity_verified"] is True
        and receipt(out / "P1_gpu_pre_model")["model_loads"] == 0
        and receipt(out / "P1_gpu_pre_model")["cuda_initialized"] is False
        and not rb.GPU_QUOTA_ROOT.exists(),
        "synthetic policy-V2 GPU admission passes all gates and stops before load; real ledger untouched"))
    run("P2_gpu_tampered_manifest", gpu_adm("gpu_ok2"), backend="gpu", mode="--pre-model-gate-only", manifest=bad_p)
    guarded("gpu_tampered_manifest_refused", lambda: (
        "manifest blob override refused" in receipt(out / "P2_gpu_tampered_manifest")["error_message"],
        "tampered manifest refused before load"))
    run("P3_gpu_plan_override", gpu_adm("gpu_ok3"), backend="gpu", mode="--pre-model-gate-only",
        extra=("--expect-batches", ",".join(map(str, PLAN[:-1] + [PLAN[-1] - 1, 1]))))
    guarded("gpu_plan_override_refused", lambda: (
        receipt(out / "P3_gpu_plan_override")["status"] == "FAIL_A461_MON_M23S"
        and receipt(out / "P3_gpu_plan_override")["model_loads"] == 0,
        f"refused: {receipt(out / 'P3_gpu_plan_override')['error_message'][:80]}"))
    rr = run("P4_full_gpu_outside_runs_root", gpu_adm("gpu_ok4"), backend="gpu")
    guarded("full_gpu_run_outside_runs_root_refused", lambda: (
        rr.returncode != 0 and not (out / "P4_full_gpu_outside_runs_root").exists()
        and "M23S_GPU_RUNS" in rr.stderr, "refused before mkdir"))
    guarded("no_gpu_in_selftest", lambda: (
        all(receipt(d)["gpu_model_loads"] == 0 and receipt(d)["cuda_initialized"] is False
            for d in out.iterdir() if (d / "execution_receipt.json").exists())
        and not rb.GPU_RUNS_ROOT.exists(), "all receipts: gpu_model_loads=0, CUDA never initialized"))
    ok = all(r["verdict"] == "PASS" for r in RESULTS)
    res = {"schema": "JEV_A461_MON_M23S_SELFTEST_V1", "status": "PASS" if ok else "FAIL",
           "passed": sum(r["verdict"] == "PASS" for r in RESULTS), "tests": len(RESULTS), "runner_blob": runner_blob,
           "manifest_blob": rb.file_blob(a.manifest), "results": RESULTS, "gpu_calls": 0}
    (out / "selftest_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("status", "passed", "tests", "runner_blob", "manifest_blob")}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
