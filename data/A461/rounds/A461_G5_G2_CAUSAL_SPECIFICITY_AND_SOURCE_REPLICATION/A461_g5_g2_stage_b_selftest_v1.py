#!/usr/bin/env python3
"""Stage-B runner CPU self-test (zero GPU; every subprocess CUDA_VISIBLE_DEVICES="")."""
import argparse, collections, importlib.util, json, os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_g5_g2_stage_b_gpu_runner_v1.py"
STAGE = "A461_G5_G2_STAGE_B_CAUSAL_PATCHING_GPU"
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
    p = Path(d) / "raw_native_logits_stage_b.jsonl"
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    (out / "_adm").mkdir()
    quota = out / "_quota"
    quota.mkdir()
    spec = importlib.util.spec_from_file_location("stage_b", RUNNER)
    rb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rb)
    runner_blob = rb.file_blob(RUNNER)

    def adm(name, **kw):
        p = out / "_adm" / f"{name}.json"
        p.write_text(json.dumps(kw) + "\n", encoding="utf8")
        return p

    def fake_adm(name, aid, approved=464):
        return adm(name, stage=STAGE, mode="L1_FAKE", admission_id=aid, approved_max_native_forwards=approved,
                   approved_batches=4)

    def gpu_adm(name, **over):
        base = dict(stage=STAGE, mode="GPU", admission_id="SELFTEST_SYNTH_STAGE_B_0001",
                    selftest_synthetic_not_an_authorization=True,
                    governance="JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2",
                    user_gpu_approval_quote="self-test synthetic quote (not a real approval)",
                    user_gpu_approval_utc="1970-01-01T00:00:00Z", approved_runner_blob=runner_blob,
                    explicit_user_gpu_approval=True, approved_max_native_forwards=464, approved_batches=4,
                    approved_batch_plan=[116, 116, 116, 116],
                    frozen_inputs={"manifest_blob": rb.BLOB_MANIFEST, "design_blob": rb.BLOB_DESIGN,
                                   "stage_a_raw_blob": rb.BLOB_STAGE_A_RAW, "roster_blob": rb.BLOB_ROSTER,
                                   "g5v2_questions_blob": rb.BLOB_G5V2, "corpus_sha256": rb.CORPUS_SHA},
                    model_identity_sha256=rb.v4.identity_digest(rb.v4.MODEL_IDENTITY))
        base.update(over)
        return adm(name, **base)

    def run(name, admission, backend="fake", mode=None, extra=(), fault="none", manifest=None):
        cmd = [sys.executable, str(RUNNER), "--repo-root", str(a.repo_root), "--admission", str(admission),
               "--manifest", str(manifest or a.manifest), "--stage-a-raw", str(a.stage_a_raw),
               "--backend", backend, "--out", str(out / name), *extra]
        if mode:
            cmd.append(mode)
        if backend == "fake" and mode is None:
            cmd += ["--quota-root", str(quota)]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                              env=dict(os.environ, CUDA_VISIBLE_DEVICES="", FAKE_FAULT=fault))

    run("T1_preflight", fake_adm("pf", "SELFTEST_PF_0001"), mode="--preflight-only")
    guarded("preflight_token_and_span_gates_on_real_manifest", lambda: (
        receipt(out / "T1_preflight")["status"] == "COMPLETE_A461_G5_G2_STAGE_B_PREFLIGHT"
        and receipt(out / "T1_preflight")["preflight"] == {"scenes": 8, "token_gate": "PASS", "span_gate": "PASS",
                                                          "manifest_rows": 464},
        f"{receipt(out / 'T1_preflight')['preflight']}"))

    run("T2_fullpath", fake_adm("full", "SELFTEST_FULL_0001"))
    r2, x2 = receipt(out / "T2_fullpath"), rows(out / "T2_fullpath")

    def t_full():
        brs = [(b["run"], b["planned"], b["physical"], b["status"]) for b in r2["batch_receipts"]]
        cond = collections.Counter(x["condition"] for x in x2)
        return (r2["status"] == "COMPLETE_A461_G5_G2_STAGE_B" and len(x2) == 464
                and [x["forward_index"] for x in x2] == list(range(1, 465))
                and brs == [(k, 116, 116, "COMPLETE") for k in (1, 2, 3, 4)]
                and r2["physical_prehook_calls"] == 464 and r2["denied_prehook_calls"] == 0
                and r2["durable_appends"]["raw_rows"] == 464 and cond["patch_identity_host_sa"] == 16
                and cond["patch_restoration_donor_new_to_host_sa"] == 48
                and cond["patch_normrand_host_new_to_donor_new"] == 48,
                f"status={r2['status']} rows={len(x2)} batches={brs} conditions={len(cond)} kinds")
    guarded("fake_full_path_464_in_4x116_with_identity_and_hook_liveness", t_full)

    def t_effect():
        base = {(x["run"], x["target_scene"]): x["M"] for x in x2 if x["condition"] == "baseline_host_sa_unpatched"}
        moved = [abs(x["M"] - base[(x["run"], x["target_scene"])]) > 1e-6 for x in x2
                 if x["condition"] == "patch_restoration_donor_new_to_host_sa"]
        idm = [x["M"] == base[(x["run"], x["target_scene"])] for x in x2 if x["condition"] == "patch_identity_host_sa"]
        stats = [x["span_stats"] for x in x2 if x.get("direction")]
        return (sum(moved) == len(moved) == 48 and all(idm) and len(stats) == 384 and all(stats),
                f"restoration patches move M in {sum(moved)}/48 (fake model); identity == baseline 16/16; "
                f"span stats on 384 patch rows")
    guarded("patches_have_effect_and_identity_is_noop", t_effect)

    def t_transform():
        import torch
        g = torch.Generator().manual_seed(1)
        src = torch.randn(31, 64, generator=g)
        perm = list(range(31))[::-1]
        p = rb.transform(src, {"transform": "permute", "perm": perm})
        n = rb.transform(src, {"transform": "normrand", "seed": 123})
        n2 = rb.transform(src, {"transform": "normrand", "seed": 123})
        return (torch.equal(p, src[perm]) and torch.allclose(n.norm(dim=1), src.norm(dim=1), atol=1e-5)
                and torch.equal(n, n2) and float(torch.nn.functional.cosine_similarity(n, src, dim=1).abs().mean()) < 0.3,
                "permute == row reindex; normrand per-position norms == source (1e-5), seeded-deterministic, "
                "near-orthogonal to source")
    guarded("control_transforms_unit", t_transform)

    def t_norms():
        bad = [x["forward_index"] for x in x2 if x.get("patch") and x["patch"]["transform"] == "normrand"
               and abs(x["span_stats"]["src_norm_mean"] - next(
                   y["span_stats"]["src_norm_mean"] for y in x2 if y["run"] == x["run"] and y.get("direction") == x["direction"]
                   and y["host"] == x["host"] and y["layer"] == x["layer"] and y["patch"]["transform"] == "permute")) > 1e-3]
        return not bad, f"norm-matched random span mean norm == permuted source span norm on all 96 rows (bad={bad[:3]})"
    guarded("normrand_rows_norm_matched_in_run", t_norms)

    run("T3_extra_lm_call", fake_adm("dbl", "SELFTEST_DBL_0001"), fault="doublefire@50")
    guarded("extra_lm_call_refused_at_prehook", lambda: (
        receipt(out / "T3_extra_lm_call")["status"] == "FAIL_A461_G5_G2_STAGE_B"
        and "LM pre-hook refused" in receipt(out / "T3_extra_lm_call")["error_message"]
        and receipt(out / "T3_extra_lm_call")["denied_prehook_calls"] == 1
        and receipt(out / "T3_extra_lm_call")["physical_prehook_calls"] == 50
        and len(rows(out / "T3_extra_lm_call")) == 49,
        "2nd LM call inside reserved call 50 denied before LM body; physical 50, rows 49"))

    run("T4_reuse", fake_adm("full", "SELFTEST_FULL_0001"))
    guarded("same_approval_reuse_refused_by_ledger", lambda: (
        receipt(out / "T4_reuse")["status"] == "FAIL_A461_G5_G2_STAGE_B"
        and "ledger consumed 464" in receipt(out / "T4_reuse")["error_message"]
        and receipt(out / "T4_reuse")["model_loads"] == 0,
        "same admission from a new out dir after a complete 464-call run: refused, 0 loads"))

    run("P1_gpu_pre_model", gpu_adm("gpu_ok"), backend="gpu", mode="--pre-model-gate-only")
    guarded("gpu_policy_v2_admission_reaches_pre_model_gate", lambda: (
        receipt(out / "P1_gpu_pre_model")["status"] == "COMPLETE_A461_G5_G2_STAGE_B_PRE_MODEL_GATE"
        and receipt(out / "P1_gpu_pre_model")["model_identity_verified"] is True
        and receipt(out / "P1_gpu_pre_model")["model_loads"] == 0
        and receipt(out / "P1_gpu_pre_model")["cuda_initialized"] is False
        and not rb.GPU_QUOTA_ROOT.exists(),
        "synthetic policy-V2 GPU admission passes all gates and stops before load; real ledger untouched"))
    tampered = out / "_tampered_manifest.jsonl"
    lines = a.manifest.read_text("utf8").splitlines()
    t0 = json.loads(lines[20])
    t0["patch"]["layer"] = 19
    lines[20] = json.dumps(t0, sort_keys=True, separators=(",", ":"))
    tampered.write_text("\n".join(lines) + "\n", encoding="utf8")
    run("P2_gpu_tampered_manifest", gpu_adm("gpu_ok2"), backend="gpu", mode="--pre-model-gate-only", manifest=tampered)
    guarded("gpu_tampered_manifest_refused", lambda: (
        "manifest blob override refused" in receipt(out / "P2_gpu_tampered_manifest")["error_message"],
        "manifest with one patch layer changed: refused before load"))
    run("P3_gpu_plan_override", gpu_adm("gpu_ok3"), backend="gpu", mode="--pre-model-gate-only",
        extra=("--expect-batches", "128,128,128,80"))
    guarded("gpu_plan_override_refused", lambda: (
        receipt(out / "P3_gpu_plan_override")["status"] == "FAIL_A461_G5_G2_STAGE_B"
        and receipt(out / "P3_gpu_plan_override")["model_loads"] == 0,
        f"refused: {receipt(out / 'P3_gpu_plan_override')['error_message'][:80]}"))
    rr = run("P4_full_gpu_outside_runs_root", gpu_adm("gpu_ok4"), backend="gpu")
    guarded("full_gpu_run_outside_runs_root_refused", lambda: (
        rr.returncode != 0 and not (out / "P4_full_gpu_outside_runs_root").exists()
        and "G2_STAGE_B_GPU_RUNS" in rr.stderr, "refused before mkdir"))
    guarded("no_gpu_in_selftest", lambda: (
        all(receipt(d)["gpu_model_loads"] == 0 and receipt(d)["cuda_initialized"] is False
            for d in out.iterdir() if (d / "execution_receipt.json").exists())
        and not rb.GPU_RUNS_ROOT.exists(), "all receipts: gpu_model_loads=0, CUDA never initialized"))

    ok = all(r["verdict"] == "PASS" for r in RESULTS)
    res = {"schema": "JEV_A461_G5_G2_STAGE_B_SELFTEST_V1", "status": "PASS" if ok else "FAIL",
           "passed": sum(r["verdict"] == "PASS" for r in RESULTS), "tests": len(RESULTS), "runner_blob": runner_blob,
           "manifest_blob": rb.file_blob(a.manifest), "results": RESULTS, "gpu_calls": 0}
    (out / "selftest_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("status", "passed", "tests", "runner_blob", "manifest_blob")}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
