#!/usr/bin/env python3
"""A461-MECH-M20 runner CPU self-test (zero GPU; every subprocess CUDA_VISIBLE_DEVICES="").
The M17 gate / ledger / refusal tests (preflight, extra LM call, approval reuse, tampered G1.0 variants, GPU admission
gates), plus: the fake full path on the real 488-row manifest (44 captures; 4 x 104 interchange rows and 2 x 14 per-donor
rows, all targeting the donors' new captures); wiring (full arms take the source's whole write, bulk arms replace the
donor's BULK by the listed pool; host / control donor from other groups); identities: full with source = target (the
donor's own capture) is a bitwise no-op, and a bulk pool holding the donor's own new capture is a no-op up to float
rounding."""
import argparse, collections, hashlib, importlib.util, json, os, statistics, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_mech_m20_runner_v1.py"
STAGE = "A461_MECH_M20_NATURAL_NECESSITY_GPU"
TOTAL, PLAN = 488, [128] * 3 + [104]
RESULTS = []
# R2: children died with "libgomp: Thread creation failed" under the shared per-user thread limit
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
    p = Path(d) / "raw_native_logits_m20.jsonl"
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--g10-cf", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m6-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    (out / "_adm").mkdir()
    quota = out / "_quota"
    quota.mkdir()
    spec = importlib.util.spec_from_file_location("m20", RUNNER)
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
        base = dict(stage=STAGE, mode="GPU", admission_id="SELFTEST_SYNTH_M20_0001",
                    selftest_synthetic_not_an_authorization=True,
                    governance="JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2",
                    user_gpu_approval_quote="self-test synthetic quote (not a real approval)",
                    user_gpu_approval_utc="1970-01-01T00:00:00Z", approved_runner_blob=runner_blob,
                    explicit_user_gpu_approval=True, approved_max_native_forwards=TOTAL, approved_batches=len(PLAN),
                    approved_batch_plan=PLAN,
                    frozen_inputs={"manifest_blob": rb.BLOB_MANIFEST, "design_blob": rb.BLOB_DESIGN,
                                   "m1_raw_blob": rb.BLOB_M1_RAW, "g10_counterfactuals_blob": rb.BLOB_G10_CF, "m3_raw_blob": rb.BLOB_M3_RAW, "m6_raw_blob": rb.BLOB_M6_RAW,
                                   "roster_blob": rb.BLOB_ROSTER,
                                   "g5v2_questions_blob": rb.BLOB_G5V2, "corpus_sha256": rb.CORPUS_SHA},
                    model_identity_sha256=rb.v4.identity_digest(rb.v4.MODEL_IDENTITY))
        base.update(over)
        return adm(name, **base)

    def run(name, admission, backend="fake", mode=None, extra=(), fault="none", manifest=None, g10=None):
        cmd = [sys.executable, str(RUNNER), "--repo-root", str(a.repo_root), "--admission", str(admission),
               "--manifest", str(manifest or a.manifest), "--m1-raw", str(a.m1_raw),
               "--g10-cf", str(g10 or a.g10_cf), "--m3-raw", str(a.m3_raw), "--m6-raw", str(a.m6_raw),
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
        receipt(out / "T1_preflight")["status"] == "COMPLETE_A461_MECH_M20_PREFLIGHT"
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
        return (r2["status"] == "COMPLETE_A461_MECH_M20" and len(x2) == TOTAL
                and [x["forward_index"] for x in x2] == list(range(1, TOTAL + 1))
                and brs == [(k, 128, 128, "COMPLETE") for k in range(1, 4)] + [(4, 104, 104, "COMPLETE")]
                and r2["physical_prehook_calls"] == TOTAL and r2["denied_prehook_calls"] == 0
                and r2["durable_appends"]["raw_rows"] == TOTAL and len(caps) == 44 and len(files) == 88
                and ok_files and shapes
                and {k: v for k, v in cond.items() if k.startswith("patch_m20_")}
                == {"patch_m20_full_host": 104, "patch_m20_full_ctrl": 104, "patch_m20_bulk_host": 104,
                    "patch_m20_bulk_ctrl": 104, "patch_m20_bulk_round_self": 14, "patch_m20_bulk_hostmean": 14}
                # fake explicit-softmax attention is batched over rows: float32 rounding only (<= 1e-6)
                and all(c["cross_row_max_absdiff"] <= 1e-6 for c in caps),
                f"status={r2['status']} rows={len(x2)} batches={len(brs)} captures={len(caps)} files={len(files)} "
                f"(sha ok={ok_files}, shapes ok={shapes}); cross-row max {max(c['cross_row_max_absdiff'] for c in caps):.1e}")
    guarded("fake_full_path_488_with_44_captures_and_class_files", t_full)
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
    man = [json.loads(x) for x in a.manifest.read_text("utf8").splitlines() if x.strip()]

    def dev(x, y):
        return max(abs(u - v) for q, qb in zip(x["questions"], y["questions"]) for u, v in zip(q["logits"], qb["logits"]))

    def t_wiring():
        pm = [m for m in man if m["phase"] == "patch"]
        caps_ = {m["target_scene"]: m for m in man if m["phase"] == "capture" and m["source_kind"] == "donor"}
        ok = 0
        for m in pm:
            p, d = m["patch"], m["target_scene"]
            good = (m["target_arm"] == "new" and d == m["donor"] and d in caps_ and p["target"] == f"new:{d[:12]}"
                    and p["span"] == caps_[d]["capture"]["span"])
            arm = p["arm"]
            if arm in ("full_host", "full_ctrl"):
                src = m["host"] if arm == "full_host" else m["control_donor"]
                good = good and p["op"] == "full" and p["classes"] == [] and p["source"] == f"new:{src[:12]}"
            elif arm in ("bulk_host", "bulk_ctrl"):
                src = m["host"] if arm == "bulk_host" else m["control_donor"]
                good = (good and p["op"] == "pool" and p["base"] == "target" and p["classes"] == ["OTHER_ITEMS", "CONTEXT"]
                        and p["pool"] == [f"new:{src[:12]}"])
            elif arm == "bulk_round_self":
                good = good and p["pool"] == [f"ROUND:{d[:12]}"]
            else:
                good = good and arm == "bulk_hostmean" and len(p["pool"]) >= 5 and all(t_.startswith("new:") for t_ in p["pool"])
            ok += good
        return (ok == len(pm) == 444, f"interchange wiring as frozen in {ok}/{len(pm)} patch rows")
    guarded("interchange_wiring_into_donors", t_wiring)

    caps_rows = [m for m in man if m["phase"] == "capture"]
    fh = next(m for m in man if m["phase"] == "patch" and m["patch"]["arm"] == "full_host")
    d0 = fh["target_scene"]
    idf = dict(fh, condition="identity_full_self", patch=dict(fh["patch"], source=f"new:{d0[:12]}"))
    bh = next(m for m in man if m["phase"] == "patch" and m["patch"]["arm"] == "bulk_host" and m["target_scene"] == d0)
    idb = dict(bh, condition="identity_bulk_self", patch=dict(bh["patch"], pool=[f"new:{d0[:12]}"]))
    mini = [dict(m, forward_index=i + 1, run=1) for i, m in enumerate(caps_rows + [idf, idb])]
    mini_p = out / "_identity_manifest.jsonl"
    mini_p.write_text("".join(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n" for m in mini), encoding="utf8")
    run("T6_identity", fake_adm("ident", "SELFTEST_IDENT_0001", approved=len(mini), batches=1), manifest=mini_p,
        extra=("--expect-batches", str(len(mini)), "--allow-manifest-blob", rb.file_blob(mini_p)))

    def t_identity():
        x6 = rows(out / "T6_identity")
        base = next(x for x in x6 if x.get("capture") and x["target_scene"] == d0 and x["target_arm"] == "new")
        pr = {x["condition"]: x for x in x6 if x.get("patch")}
        db = dev(pr["identity_bulk_self"], base)
        return (receipt(out / "T6_identity")["status"] == "COMPLETE_A461_MECH_M20" and len(pr) == 2
                and pr["identity_full_self"]["questions"] == base["questions"] and db <= 1e-4,
                f"full with the donor's own write is a bitwise no-op; bulk with its own BULK differs by {db:.1e}")
    guarded("identities_on_donor_targets", t_identity)

    bad_cf = out / "_tampered_g10.json"
    bad_cf.write_text(a.g10_cf.read_text("utf8").replace('"round": 1', '"round": 9', 1), encoding="utf8")
    run("T5_tampered_g10", fake_adm("pf2", "SELFTEST_PF_0002"), mode="--preflight-only", g10=bad_cf)
    guarded("tampered_g10_counterfactuals_refused", lambda: (
        receipt(out / "T5_tampered_g10")["status"] == "FAIL_A461_MECH_M20"
        and "G1.0 counterfactuals blob pin" in receipt(out / "T5_tampered_g10")["error_message"],
        "one variant round edited: refused at the blob pin"))

    run("T3_extra_lm_call", fake_adm("dbl", "SELFTEST_DBL_0001"), fault="doublefire@50")
    guarded("extra_lm_call_refused_at_prehook", lambda: (
        receipt(out / "T3_extra_lm_call")["status"] == "FAIL_A461_MECH_M20"
        and "LM pre-hook refused" in receipt(out / "T3_extra_lm_call")["error_message"]
        and receipt(out / "T3_extra_lm_call")["denied_prehook_calls"] == 1
        and receipt(out / "T3_extra_lm_call")["physical_prehook_calls"] == 50
        and len(rows(out / "T3_extra_lm_call")) == 49,
        "2nd LM call inside reserved call 50 denied before LM body; physical 50, rows 49"))

    run("T4_reuse", fake_adm("full", "SELFTEST_FULL_0001"))
    guarded("same_approval_reuse_refused_by_ledger", lambda: (
        receipt(out / "T4_reuse")["status"] == "FAIL_A461_MECH_M20"
        and f"ledger consumed {TOTAL}" in receipt(out / "T4_reuse")["error_message"]
        and receipt(out / "T4_reuse")["model_loads"] == 0,
        f"same admission from a new out dir after a complete {TOTAL}-call run: refused, 0 loads"))

    run("P1_gpu_pre_model", gpu_adm("gpu_ok"), backend="gpu", mode="--pre-model-gate-only")
    guarded("gpu_policy_v2_admission_reaches_pre_model_gate", lambda: (
        receipt(out / "P1_gpu_pre_model")["status"] == "COMPLETE_A461_MECH_M20_PRE_MODEL_GATE"
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
        "manifest with one patch row's classes changed: refused before load"))
    run("P3_gpu_plan_override", gpu_adm("gpu_ok3"), backend="gpu", mode="--pre-model-gate-only",
        extra=("--expect-batches", ",".join(["128"] * 3 + ["103", "1"])))
    guarded("gpu_plan_override_refused", lambda: (
        receipt(out / "P3_gpu_plan_override")["status"] == "FAIL_A461_MECH_M20"
        and receipt(out / "P3_gpu_plan_override")["model_loads"] == 0,
        f"refused: {receipt(out / 'P3_gpu_plan_override')['error_message'][:80]}"))
    rr = run("P4_full_gpu_outside_runs_root", gpu_adm("gpu_ok4"), backend="gpu")
    guarded("full_gpu_run_outside_runs_root_refused", lambda: (
        rr.returncode != 0 and not (out / "P4_full_gpu_outside_runs_root").exists()
        and "M20_GPU_RUNS" in rr.stderr, "refused before mkdir"))
    guarded("no_gpu_in_selftest", lambda: (
        all(receipt(d)["gpu_model_loads"] == 0 and receipt(d)["cuda_initialized"] is False
            for d in out.iterdir() if (d / "execution_receipt.json").exists())
        and not rb.GPU_RUNS_ROOT.exists(), "all receipts: gpu_model_loads=0, CUDA never initialized"))

    ok = all(r["verdict"] == "PASS" for r in RESULTS)
    res = {"schema": "JEV_A461_MECH_M20_SELFTEST_V1", "status": "PASS" if ok else "FAIL",
           "passed": sum(r["verdict"] == "PASS" for r in RESULTS), "tests": len(RESULTS), "runner_blob": runner_blob,
           "manifest_blob": rb.file_blob(a.manifest), "results": RESULTS, "gpu_calls": 0}
    (out / "selftest_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("status", "passed", "tests", "runner_blob", "manifest_blob")}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
