#!/usr/bin/env python3
"""A461-MECH-M21 runner CPU self-test (zero GPU; every subprocess CUDA_VISIBLE_DEVICES="").
As the M19 self-test (preflight, fake full path with a synthetic 64-wide directions file, decide capture = head readout,
held-out leak and tampered directions refused, ledger / pre-hook / GPU admission gates), with the op check extended to
both kinds: gain rows record dev = proj - c and |delta| = (gamma - 1)|dev|; push rows record dev = |h| and
|delta| = beta |h|; every op row moved the certificate_action logits while the other rows stayed (runner-enforced)."""
import argparse, collections, hashlib, importlib.util, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_mech_m21_runner_v1.py"
STAGE = "A461_MECH_M21_READOUT_MEANDIFF_GPU"
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
    p = Path(d) / "raw_native_logits_m21.jsonl"
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--design", required=True, type=Path)
    ap.add_argument("--directions", required=True, type=Path)
    ap.add_argument("--m18-design", required=True, type=Path)
    ap.add_argument("--m18-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    (out / "_adm").mkdir()
    quota = out / "_quota"
    quota.mkdir()
    spec = importlib.util.spec_from_file_location("m21", RUNNER)
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
        base = dict(stage=STAGE, mode="GPU", admission_id="SELFTEST_SYNTH_M21_0001",
                    selftest_synthetic_not_an_authorization=True,
                    governance="JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2",
                    user_gpu_approval_quote="self-test synthetic quote (not a real approval)",
                    user_gpu_approval_utc="1970-01-01T00:00:00Z", approved_runner_blob=runner_blob,
                    explicit_user_gpu_approval=True, approved_max_native_forwards=TOTAL, approved_batches=len(PLAN),
                    approved_batch_plan=PLAN,
                    frozen_inputs={"manifest_blob": rb.BLOB_MANIFEST, "design_blob": rb.BLOB_DESIGN,
                                   "m18_raw_blob": rb.BLOB_M18_RAW, "m18_design_blob": rb.BLOB_M18_DESIGN,
                                   "roster_blob": rb.BLOB_ROSTER,
                                   "g5v2_questions_blob": rb.BLOB_G5V2, "corpus_sha256": rb.CORPUS_SHA},
                    model_identity_sha256=rb.v4.identity_digest(rb.v4.MODEL_IDENTITY))
        base.update(over)
        return adm(name, **base)

    def run(name, admission, backend="fake", mode=None, extra=(), fault="none", manifest=None, directions=None, design=None):
        cmd = [sys.executable, str(RUNNER), "--repo-root", str(a.repo_root), "--admission", str(admission),
               "--manifest", str(manifest or a.manifest), "--design", str(design or a.design),
               "--directions", str(directions or a.directions), "--m18-design", str(a.m18_design),
               "--m18-raw", str(a.m18_raw), "--backend", backend, "--out", str(out / name), *extra]
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
        receipt(out / "T1_preflight")["status"] == "COMPLETE_A461_MECH_M21_PREFLIGHT"
        and receipt(out / "T1_preflight")["preflight"] == {"scenes": 124, "token_gate": "PASS", "span_gate": "PASS",
                                                          "manifest_rows": TOTAL},
        f"{receipt(out / 'T1_preflight')['preflight']}"))

    # the fake model is 64 wide: a synthetic directions file under the frozen keys (seeded unit vectors) and a design
    # copy carrying its sha (the runner accepts a non-pinned design only on the fake backend); the GPU tests use the real files
    import torch
    real_dirs = torch.load(a.directions, weights_only=True)
    fake_dirs = {}
    for i_, k_ in enumerate(sorted(real_dirs)):
        v_ = torch.randn(64, generator=torch.Generator().manual_seed(1000 + i_))
        fake_dirs[k_] = (v_ / v_.norm()).float()
    fdir = out / "_fake_directions.pt"
    torch.save(fake_dirs, fdir)
    fdes = out / "_fake_design.json"
    dj = json.loads(a.design.read_text("utf8"))
    dj["directions_file"]["sha256"] = hashlib.sha256(fdir.read_bytes()).hexdigest()
    fdes.write_text(json.dumps(dj), encoding="utf8")
    FAKE = {"directions": fdir, "design": fdes}
    run("T2_fullpath", fake_adm("full", "SELFTEST_FULL_0001"), **FAKE)
    r2, x2 = receipt(out / "T2_fullpath"), rows(out / "T2_fullpath")
    d2 = out / "T2_fullpath" / "captures"

    def t_full():
        brs = [(b["run"], b["planned"], b["physical"], b["status"]) for b in r2["batch_receipts"]]
        files = sorted(d2.iterdir())
        caps = [x for x in x2 if x.get("capture_file")]
        sha_ok = all(hashlib.sha256((d2 / x["capture_file"]["name"]).read_bytes()).hexdigest() == x["capture_file"]["sha256"]
                     for x in caps)
        cond = collections.Counter(x["condition"].split("_")[0] for x in x2)
        return (r2["status"] == "COMPLETE_A461_MECH_M21" and len(x2) == TOTAL
                and [x["forward_index"] for x in x2] == list(range(1, TOTAL + 1))
                and brs == [(k + 1, n, n, "COMPLETE") for k, n in enumerate(PLAN)]
                and r2["physical_prehook_calls"] == TOTAL and r2["denied_prehook_calls"] == 0
                and r2["durable_appends"]["raw_rows"] == TOTAL and len(files) == 620 == len(caps) and sha_ok
                and cond == {"replay": 620, "gain": 2480, "push": 2480, "rand": 1240},
                f"status={r2['status']} rows={len(x2)} capture files={len(files)} sha={sha_ok} conditions={dict(cond)}")
    guarded("fake_full_path_6820_rows", t_full)

    def t_decision():
        import torch
        sys.path.insert(0, str(HERE))
        from A461_mech_m3_fake_attention_model_v1 import FakePatchModel
        head = FakePatchModel(n_layers=32).head
        worst, n = 0.0, 0
        for x in [x for x in x2 if x.get("capture_file")][:40]:
            f = torch.load(d2 / x["capture_file"]["name"], weights_only=True)
            ca = next(q for q in x["questions"] if q["id"] == "certificate_action")
            worst = max(worst, float((f["decide"] @ head[:, :len(ca["keys"])] - torch.tensor(ca["logits"])).abs().max()))
            n += 1
        return (worst <= 1e-4, f"replay decide state x fake head reproduces the certificate_action logits in {n} rows "
                               f"(max abs {worst:.1e})")
    guarded("decide_capture_is_the_head_readout", t_decision)

    def t_op():
        ops = [x for x in x2 if x.get("op")]
        rep_ = {(x["target_scene"], x["target_arm"]): x for x in x2 if not x.get("op")}
        gains = [x for x in ops if x["op"]["kind"] == "gain"]
        pushes = [x for x in ops if x["op"]["kind"] == "push"]
        bad_dev = max([abs(x["op_stats"]["dev"] - (x["op_stats"]["proj_before"] - x["op"]["c"])) for x in gains]
                      + [abs(x["op_stats"]["dev"] - x["op_stats"]["h_norm"]) for x in pushes])
        top = max(1.0, max(x["op_stats"]["delta_norm"] for x in ops))
        bad_d = max([abs(x["op_stats"]["delta_norm"] - (x["op"]["gamma"] - 1) * abs(x["op_stats"]["dev"])) for x in gains]
                    + [abs(x["op_stats"]["delta_norm"] - x["op"]["beta"] * x["op_stats"]["h_norm"]) for x in pushes])
        ca = lambda x: next(q for q in x["questions"] if q["id"] == "certificate_action")["logits"]
        moved = sum(ca(x) != ca(rep_[(x["target_scene"], x["target_arm"])]) for x in ops)
        return (len(ops) == 6200 and len(gains) == 2480 and len(pushes) == 3720 and bad_dev <= 1e-3
                and bad_d <= 1e-3 * top and moved >= 6200 - 50,
                f"op rows {len(ops)}: dev = proj - c within {bad_dev:.1e}; |delta| = (gamma - 1)|dev| within {bad_d:.1e}; "
                f"certificate_action logits moved in {moved}; other rows unchanged (runner-enforced, fake tol 1e-5)")
    guarded("op_is_the_frozen_amplification", t_op)

    bad = [json.loads(json.dumps(m)) for m in man]
    k5 = next(i for i, m in enumerate(bad) if m.get("op") and m["op"]["dir"] == "meandiff")
    other = next(m["source_group"] for m in bad if m["source_group"] != bad[k5]["source_group"])
    bad[k5]["op"]["key"] = f"L{bad[k5]['op']['layer']}|{other}"
    bad_p = out / "_bad_token_manifest.jsonl"
    bad_p.write_text("".join(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n" for m in bad), encoding="utf8")
    run("T3_bad_token", fake_adm("bt", "SELFTEST_BT_0001"), mode="--preflight-only", manifest=bad_p,
        extra=("--allow-manifest-blob", rb.file_blob(bad_p)))
    guarded("probe_direction_of_another_group_refused", lambda: (
        receipt(out / "T3_bad_token")["status"] == "FAIL_A461_MECH_M21"
        and "op row" in receipt(out / "T3_bad_token")["error_message"],
        f"refused: {receipt(out / 'T3_bad_token')['error_message'][:80]}"))
    bad_d = out / "_tampered_directions.pt"
    bad_d.write_bytes(a.directions.read_bytes() + bytes(1))
    run("T4_tampered_directions", fake_adm("pf2", "SELFTEST_PF_0002"), mode="--preflight-only", directions=bad_d)
    guarded("tampered_directions_refused", lambda: (
        receipt(out / "T4_tampered_directions")["status"] == "FAIL_A461_MECH_M21"
        and "directions file sha" in receipt(out / "T4_tampered_directions")["error_message"],
        "one byte appended to the directions file: refused at its sha"))
    run("T5_extra_lm_call", fake_adm("dbl", "SELFTEST_DBL_0001"), fault="doublefire@50", **FAKE)
    guarded("extra_lm_call_refused_at_prehook", lambda: (
        receipt(out / "T5_extra_lm_call")["status"] == "FAIL_A461_MECH_M21"
        and "LM pre-hook refused" in receipt(out / "T5_extra_lm_call")["error_message"]
        and receipt(out / "T5_extra_lm_call")["denied_prehook_calls"] == 1
        and receipt(out / "T5_extra_lm_call")["physical_prehook_calls"] == 50
        and len(rows(out / "T5_extra_lm_call")) == 49,
        "2nd LM call inside reserved call 50 denied before LM body; physical 50, rows 49"))
    run("T6_reuse", fake_adm("full", "SELFTEST_FULL_0001"), **FAKE)
    guarded("same_approval_reuse_refused_by_ledger", lambda: (
        receipt(out / "T6_reuse")["status"] == "FAIL_A461_MECH_M21"
        and f"ledger consumed {TOTAL}" in receipt(out / "T6_reuse")["error_message"]
        and receipt(out / "T6_reuse")["model_loads"] == 0,
        f"same admission after a complete {TOTAL}-call run: refused, 0 loads"))
    run("P1_gpu_pre_model", gpu_adm("gpu_ok"), backend="gpu", mode="--pre-model-gate-only")
    guarded("gpu_policy_v2_admission_reaches_pre_model_gate", lambda: (
        receipt(out / "P1_gpu_pre_model")["status"] == "COMPLETE_A461_MECH_M21_PRE_MODEL_GATE"
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
        receipt(out / "P3_gpu_plan_override")["status"] == "FAIL_A461_MECH_M21"
        and receipt(out / "P3_gpu_plan_override")["model_loads"] == 0,
        f"refused: {receipt(out / 'P3_gpu_plan_override')['error_message'][:80]}"))
    rr = run("P4_full_gpu_outside_runs_root", gpu_adm("gpu_ok4"), backend="gpu")
    guarded("full_gpu_run_outside_runs_root_refused", lambda: (
        rr.returncode != 0 and not (out / "P4_full_gpu_outside_runs_root").exists()
        and "M21_GPU_RUNS" in rr.stderr, "refused before mkdir"))
    guarded("no_gpu_in_selftest", lambda: (
        all(receipt(d)["gpu_model_loads"] == 0 and receipt(d)["cuda_initialized"] is False
            for d in out.iterdir() if (d / "execution_receipt.json").exists())
        and not rb.GPU_RUNS_ROOT.exists(), "all receipts: gpu_model_loads=0, CUDA never initialized"))
    ok = all(r["verdict"] == "PASS" for r in RESULTS)
    res = {"schema": "JEV_A461_MECH_M21_SELFTEST_V1", "status": "PASS" if ok else "FAIL",
           "passed": sum(r["verdict"] == "PASS" for r in RESULTS), "tests": len(RESULTS), "runner_blob": runner_blob,
           "manifest_blob": rb.file_blob(a.manifest), "results": RESULTS, "gpu_calls": 0}
    (out / "selftest_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("status", "passed", "tests", "runner_blob", "manifest_blob")}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
