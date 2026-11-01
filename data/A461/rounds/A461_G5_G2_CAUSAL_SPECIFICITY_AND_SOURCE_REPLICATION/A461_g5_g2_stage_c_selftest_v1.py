#!/usr/bin/env python3
"""Stage-C runner CPU self-test (zero GPU; every subprocess CUDA_VISIBLE_DEVICES="")."""
import argparse, collections, importlib.util, json, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_g5_g2_stage_c_gpu_runner_v1.py"
STAGE = "A461_G5_G2_STAGE_C_DOSE_MATCHED_AND_ENCODING_GPU"
RESULTS = []


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
    p = Path(d) / "raw_native_logits_stage_c.jsonl"
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--stage-b-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    (out / "_adm").mkdir()
    quota = out / "_quota"
    quota.mkdir()
    spec = importlib.util.spec_from_file_location("stage_c", RUNNER)
    rb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rb)
    runner_blob = rb.file_blob(RUNNER)

    def adm(name, **kw):
        p = out / "_adm" / f"{name}.json"
        p.write_text(json.dumps(kw) + "\n", encoding="utf8")
        return p

    def fake_adm(name, aid, approved=696):
        return adm(name, stage=STAGE, mode="L1_FAKE", admission_id=aid, approved_max_native_forwards=approved,
                   approved_batches=6)

    def gpu_adm(name, **over):
        base = dict(stage=STAGE, mode="GPU", admission_id="SELFTEST_SYNTH_STAGE_C_0001",
                    selftest_synthetic_not_an_authorization=True,
                    governance="JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2",
                    user_gpu_approval_quote="self-test synthetic quote (not a real approval)",
                    user_gpu_approval_utc="1970-01-01T00:00:00Z", approved_runner_blob=runner_blob,
                    explicit_user_gpu_approval=True, approved_max_native_forwards=696, approved_batches=6,
                    approved_batch_plan=[124, 124, 112, 112, 112, 112],
                    frozen_inputs={"manifest_blob": rb.BLOB_MANIFEST, "design_blob": rb.BLOB_DESIGN,
                                   "stage_a_raw_blob": rb.BLOB_STAGE_A_RAW, "stage_b_raw_blob": rb.BLOB_STAGE_B_RAW,
                                   "roster_blob": rb.BLOB_ROSTER,
                                   "g5v2_questions_blob": rb.BLOB_G5V2, "corpus_sha256": rb.CORPUS_SHA},
                    model_identity_sha256=rb.v4.identity_digest(rb.v4.MODEL_IDENTITY))
        base.update(over)
        return adm(name, **base)

    def run(name, admission, backend="fake", mode=None, extra=(), fault="none", manifest=None):
        cmd = [sys.executable, str(RUNNER), "--repo-root", str(a.repo_root), "--admission", str(admission),
               "--manifest", str(manifest or a.manifest), "--stage-a-raw", str(a.stage_a_raw),
               "--stage-b-raw", str(a.stage_b_raw),
               "--backend", backend, "--out", str(out / name), *extra]
        if mode:
            cmd.append(mode)
        if backend == "fake" and mode is None:
            cmd += ["--quota-root", str(quota)]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                              env=dict(os.environ, CUDA_VISIBLE_DEVICES="", FAKE_FAULT=fault))

    run("T1_preflight", fake_adm("pf", "SELFTEST_PF_0001"), mode="--preflight-only")
    guarded("preflight_token_and_span_gates_on_real_manifest", lambda: (
        receipt(out / "T1_preflight")["status"] == "COMPLETE_A461_G5_G2_STAGE_C_PREFLIGHT"
        and receipt(out / "T1_preflight")["preflight"] == {"scenes": 124, "token_gate": "PASS", "span_gate": "PASS",
                                                          "manifest_rows": 696},
        f"{receipt(out / 'T1_preflight')['preflight']}"))

    run("T2_fullpath", fake_adm("full", "SELFTEST_FULL_0001"))
    r2, x2 = receipt(out / "T2_fullpath"), rows(out / "T2_fullpath")

    def t_full():
        brs = [(b["run"], b["planned"], b["physical"], b["status"]) for b in r2["batch_receipts"]]
        cond = collections.Counter(x["condition"] for x in x2)
        caps = [x for x in x2 if x.get("capture_file")]
        files = sorted((out / "T2_fullpath" / "captures").iterdir())
        import hashlib
        ok_files = all(hashlib.sha256((out / "T2_fullpath" / "captures" / c["capture_file"]["name"]).read_bytes()).hexdigest()
                       == c["capture_file"]["sha256"] and c["capture_file"]["shape"] == [24, 31, 64] for c in caps)
        return (r2["status"] == "COMPLETE_A461_G5_G2_STAGE_C" and len(x2) == 696
                and [x["forward_index"] for x in x2] == list(range(1, 697))
                and brs == [(1, 124, 124, "COMPLETE"), (2, 124, 124, "COMPLETE")] + [(k, 112, 112, "COMPLETE") for k in range(3, 7)]
                and r2["physical_prehook_calls"] == 696 and r2["denied_prehook_calls"] == 0
                and r2["durable_appends"]["raw_rows"] == 696 and len(caps) == 248 and len(files) == 248 and ok_files
                and cond["patch_doserand_s2_to_host_sa"] == 64 and cond["patch_doserand_s1_to_donor_new"] == 64,
                f"status={r2['status']} rows={len(x2)} batches={brs} captures saved={len(files)} (sha+shape ok={ok_files})")
    guarded("fake_full_path_696_with_248_saved_captures", t_full)

    def t_dose():
        main = {(x["direction"], x["donor"], x["host"], x["layer"]): x["span_stats"]["delta_norm_mean"] for x in x2
                if x["condition"] in ("patch_restoration_donor_new_to_host_sa", "patch_suppression_host_new_to_donor_new")}
        dose = [(x, main[(x["direction"], x["donor"], x["host"], x["layer"])]) for x in x2 if "doserand" in x["condition"]]
        bad = [x["forward_index"] for x, m in dose if abs(x["span_stats"]["delta_norm_mean"] - m) > 1e-4 * max(1, m)]
        moved = sum(abs(x["span_stats"]["cos_mean"] - 1) > 1e-6 for x, _ in dose)
        return (len(dose) == 192 and not bad and moved == 192,
                f"192 dose-matched rows: mean per-position perturbation == main patch's (bad={bad[:3]}); "
                f"all differ in direction from the target")
    guarded("dose_matched_rows_equal_main_perturbation_size", t_dose)

    def t_transform():
        import torch
        g = torch.Generator().manual_seed(1)
        src = torch.randn(31, 64, generator=g)
        tgt = torch.randn(31, 64, generator=g)
        d1 = rb.transform(src, {"transform": "deltarand", "seed": 5}, target=tgt)
        d2 = rb.transform(src, {"transform": "deltarand", "seed": 5}, target=tgt)
        return (torch.allclose((d1 - tgt).norm(dim=1), (src - tgt).norm(dim=1), atol=1e-5) and torch.equal(d1, d2)
                and float(torch.nn.functional.cosine_similarity(d1 - tgt, src - tgt, dim=1).abs().mean()) < 0.3,
                "deltarand: per-position ||out - target|| == ||source - target||, seeded-deterministic, random direction")
    guarded("dose_matched_transform_unit", t_transform)

    run("T3_extra_lm_call", fake_adm("dbl", "SELFTEST_DBL_0001"), fault="doublefire@50")
    guarded("extra_lm_call_refused_at_prehook", lambda: (
        receipt(out / "T3_extra_lm_call")["status"] == "FAIL_A461_G5_G2_STAGE_C"
        and "LM pre-hook refused" in receipt(out / "T3_extra_lm_call")["error_message"]
        and receipt(out / "T3_extra_lm_call")["denied_prehook_calls"] == 1
        and receipt(out / "T3_extra_lm_call")["physical_prehook_calls"] == 50
        and len(rows(out / "T3_extra_lm_call")) == 49,
        "2nd LM call inside reserved call 50 denied before LM body; physical 50, rows 49"))

    run("T4_reuse", fake_adm("full", "SELFTEST_FULL_0001"))
    guarded("same_approval_reuse_refused_by_ledger", lambda: (
        receipt(out / "T4_reuse")["status"] == "FAIL_A461_G5_G2_STAGE_C"
        and "ledger consumed 696" in receipt(out / "T4_reuse")["error_message"]
        and receipt(out / "T4_reuse")["model_loads"] == 0,
        "same admission from a new out dir after a complete 696-call run: refused, 0 loads"))

    run("P1_gpu_pre_model", gpu_adm("gpu_ok"), backend="gpu", mode="--pre-model-gate-only")
    guarded("gpu_policy_v2_admission_reaches_pre_model_gate", lambda: (
        receipt(out / "P1_gpu_pre_model")["status"] == "COMPLETE_A461_G5_G2_STAGE_C_PRE_MODEL_GATE"
        and receipt(out / "P1_gpu_pre_model")["model_identity_verified"] is True
        and receipt(out / "P1_gpu_pre_model")["model_loads"] == 0
        and receipt(out / "P1_gpu_pre_model")["cuda_initialized"] is False
        and not rb.GPU_QUOTA_ROOT.exists(),
        "synthetic policy-V2 GPU admission passes all gates and stops before load; real ledger untouched"))
    tampered = out / "_tampered_manifest.jsonl"
    lines = a.manifest.read_text("utf8").splitlines()
    t0 = json.loads(lines[20])
    t0 = json.loads(lines[300])
    t0["patch"]["seed"] = 1
    lines[300] = json.dumps(t0, sort_keys=True, separators=(",", ":"))
    tampered.write_text("\n".join(lines) + "\n", encoding="utf8")
    run("P2_gpu_tampered_manifest", gpu_adm("gpu_ok2"), backend="gpu", mode="--pre-model-gate-only", manifest=tampered)
    guarded("gpu_tampered_manifest_refused", lambda: (
        "manifest blob override refused" in receipt(out / "P2_gpu_tampered_manifest")["error_message"],
        "manifest with one patch layer changed: refused before load"))
    run("P3_gpu_plan_override", gpu_adm("gpu_ok3"), backend="gpu", mode="--pre-model-gate-only",
        extra=("--expect-batches", "128,128,128,128,128,56"))
    guarded("gpu_plan_override_refused", lambda: (
        receipt(out / "P3_gpu_plan_override")["status"] == "FAIL_A461_G5_G2_STAGE_C"
        and receipt(out / "P3_gpu_plan_override")["model_loads"] == 0,
        f"refused: {receipt(out / 'P3_gpu_plan_override')['error_message'][:80]}"))
    rr = run("P4_full_gpu_outside_runs_root", gpu_adm("gpu_ok4"), backend="gpu")
    guarded("full_gpu_run_outside_runs_root_refused", lambda: (
        rr.returncode != 0 and not (out / "P4_full_gpu_outside_runs_root").exists()
        and "G2_STAGE_C_GPU_RUNS" in rr.stderr, "refused before mkdir"))
    guarded("no_gpu_in_selftest", lambda: (
        all(receipt(d)["gpu_model_loads"] == 0 and receipt(d)["cuda_initialized"] is False
            for d in out.iterdir() if (d / "execution_receipt.json").exists())
        and not rb.GPU_RUNS_ROOT.exists(), "all receipts: gpu_model_loads=0, CUDA never initialized"))

    ok = all(r["verdict"] == "PASS" for r in RESULTS)
    res = {"schema": "JEV_A461_G5_G2_STAGE_C_SELFTEST_V1", "status": "PASS" if ok else "FAIL",
           "passed": sum(r["verdict"] == "PASS" for r in RESULTS), "tests": len(RESULTS), "runner_blob": runner_blob,
           "manifest_blob": rb.file_blob(a.manifest), "results": RESULTS, "gpu_calls": 0}
    (out / "selftest_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("status", "passed", "tests", "runner_blob", "manifest_blob")}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
