#!/usr/bin/env python3
"""A461-G5-G2 Stage-A runner L1 test suite (per JEV_L1_L2_L3_GATE_MATRIX_V1).

Pilot task: A461_G5_G2_STAGE_A_GPU_SCREEN_RUNNER_G0_V2.
Runs the runner as a subprocess through its full paths with the pure-python
FakeModel, on the REAL frozen 378-row manifest (full path, per-batch cap
faults) and on synthetic mini-manifests committed to a throwaway git repo
(budget, resume, replay mismatch, forward throw, nonfinite faults), plus unit
tests of the pure functions. Manifest counts are recounted here independently
of the runner. Zero GPU, zero native forwards, no network.
Outputs L1_test_matrix.json + L1_test_receipt.json in --out.
"""
import argparse, collections, hashlib, importlib.util, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_g5_g2_stage_a_gpu_screen_runner_g0_v2.py"
FAKE = HERE / "A461_g5_g2_fake_kev_model_v1.py"
WJC = (Path.home() / "wjc").resolve()
CORPUS = WJC / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
KEV_SOURCE = WJC / "a5-secjev08b-exact-parent-20261005/source/kev"
BASE = WJC / "kev08b-smoke-20261001-153041/models/base"
MANIFEST_BLOB = "01ca53908cc73276d4f6821a4892f05e47e02a15"
ROSTER_BLOB = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
G5V2_BLOB = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
STAGE = "A461_G5_G2_STAGE_A_DONOR_DISCOVERY_GPU"
MATRIX = []
EVIDENCE = []


def inside(p, root):
    """Directory relation (Path.is_relative_to is 3.9+; server runs 3.8)."""
    try:
        Path(p).relative_to(root)
        return True
    except ValueError:
        return False


def record(group, test, ok, evidence):
    MATRIX.append({"group": group, "test": test, "verdict": "PASS" if ok else "FAIL", "evidence": evidence})
    print(("PASS " if ok else "FAIL ") + group + "/" + test + " :: " + evidence[:160], flush=True)
    return ok


def guarded(group, test, fn):
    """Run one test body; an exception inside the test is a FAIL row, not a crash."""
    try:
        ok, ev = fn()
    except Exception as err:
        ok, ev = False, f"test raised {type(err).__name__}: {str(err)[:200]}"
    return record(group, test, ok, ev)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def receipt_of(outdir):
    return json.loads((Path(outdir) / "execution_receipt.json").read_text("utf8"))


def raw_rows(outdir):
    p = Path(outdir) / "raw_native_logits_stage_a.jsonl"
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def attempt_rows(outdir):
    p = Path(outdir) / "attempt_receipts.jsonl"
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def sums_ok(outdir):
    """SHA256SUMS lists every produced file and each hash matches the bytes."""
    lines = (Path(outdir) / "SHA256SUMS").read_text("utf8").splitlines()
    for ln in lines:
        h, n = ln.split("  ", 1)
        if hashlib.sha256((Path(outdir) / n).read_bytes()).hexdigest() != h:
            return False
    listed = {ln.split("  ", 1)[1] for ln in lines} | {"SHA256SUMS"}
    return listed == {p.name for p in Path(outdir).iterdir()}


def run_runner(repo, admission, out, fault="none", backend="fake", extra=(), preflight=False):
    cmd = [sys.executable, str(RUNNER), "--repo-root", str(repo), "--admission", str(admission),
           "--backend", backend, "--out", str(out), *extra]
    if preflight:
        cmd.append("--preflight-only")
    env = dict(os.environ, FAKE_FAULT=fault)
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=3000)
    EVIDENCE.append({"out": out.name, "fault": fault, "backend": backend, "returncode": r.returncode,
                     "command": " ".join(cmd[1:]).replace(str(HERE) + "/", ""),
                     "stderr_tail": r.stderr[-600:]})
    if r.returncode < 0:
        print(f"!! runner {out.name} killed by signal {-r.returncode}: {r.stderr[-400:]}", flush=True)
    return r


def write_admission(p, approved, batches, consumed=0, mode="L1_FAKE"):
    Path(p).write_text(json.dumps({"stage": STAGE, "mode": mode, "approved_max_native_forwards": approved,
                                   "approved_batches": batches, "cumulative_calls_already_consumed": consumed,
                                   "blind_review_verdict": None, "explicit_user_gpu_approval": False,
                                   "blind_review_runner_blob": None}) + "\n", encoding="utf8")
    return Path(p)


def build_mini_fixture(fx, real_repo, n_scenes):
    """Synthetic W31-labelled roster + manifest (n_scenes x 3 arms, 1 batch,
    then 2 replays of the first old arm) committed as blobs in a throwaway git
    repo `fx`. Token SHAs/lengths come from the real kev encode of canonical
    states, so the runner's token gate runs for real; the fake model ignores
    widths. Returns (blob_roster, blob_manifest, blob_questions, total)."""
    import gzip
    sys.path.insert(0, str(KEV_SOURCE))
    from kev.api import SystemOneRequest, to_record
    from kev.model import encode
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(BASE))
    q_tw = json.loads(git(real_repo, "cat-file", "blob", G5V2_BLOB).splitlines()[0])["native_request"]["questions"]
    twins = []
    with gzip.open(CORPUS, "rt", encoding="utf8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    twins.append(rec)
                    if len(twins) >= n_scenes:
                        break

    def enc_len_sha(state):
        rendered, _ = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
        enc = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
        return (len(enc["ids"][:enc["seg"].count(0)]),
                hashlib.sha256(json.dumps(enc["ids"], ensure_ascii=False).encode("utf8")).hexdigest())

    roster, manifest = [], []
    for rec in twins:
        st = json.loads(canon(rec["state"]))
        msgs = st["received_messages"]
        blk = sorted({e["block"] for e in msgs} - {st["candidate_block"]})[0]
        mx = max(e["received"] for e in msgs)
        cand = [e for e in msgs if e.get("block") == st["candidate_block"]]
        treat = {"author": sorted({e.get("author") for e in cand})[0], "block": blk, "kind": "vote",
                 "round": st["candidate_round"], "received": mx}
        dup = dict(cand[0], received=mx)
        st_new = json.loads(canon(st))
        st_new["received_messages"].append(dict(treat))
        st_sa = json.loads(canon(st))
        st_sa["received_messages"].append(dict(dup))
        lens, shas = {}, {}
        for arm, s_ in (("old", st), ("new", st_new), ("SA", st_sa)):
            lens[arm], shas[arm] = enc_len_sha(s_)
        sha = hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()
        grp = rec["_meta"]["split_group_id"]
        roster.append({"scene_sha256": sha, "source_group": grp, "cell": "accept",
                       "declared_edit_new": {"op": "append_conflict_vote", "message": treat},
                       "declared_edit_sa": {"op": "SHAM_same_author_duplicate", "message": dup},
                       "state_token_len": lens, "frozen_width": 31, "common_widths": [31],
                       "token_ids_sha256": shas, "full_request_token_gate": "PASS"})
        for arm in ("old", "new", "SA"):
            manifest.append({"forward_index": len(manifest) + 1, "run": 1, "kind": "primary", "scene_sha256": sha,
                             "arm": arm, "frozen_width": 31, "cell": "accept", "source_group": grp,
                             "token_ids_sha256": shas[arm], "state_token_len": lens[arm]})
    for _ in range(2):
        manifest.append({"forward_index": len(manifest) + 1, "run": 1, "kind": "replay", "arm": "old",
                         "replay_of_forward_index": 1, "scene_sha256": manifest[0]["scene_sha256"]})
    subprocess.run(["git", "init", "-q", str(fx)], check=True)
    (fx / "roster.json").write_text(json.dumps({"schema": "JEV_A461_G5_G2_STAGE_A_CANDIDATE_ROSTER_V3",
                                                "candidates": roster}, indent=1) + "\n", encoding="utf8")
    (fx / "manifest.jsonl").write_text("".join(canon(r) + "\n" for r in manifest), encoding="utf8")
    (fx / "questions.jsonl").write_text(canon({"native_request": {"questions": q_tw}}) + "\n", encoding="utf8")
    git(fx, "add", "roster.json", "manifest.jsonl", "questions.jsonl")
    git(fx, "-c", "user.email=l1@test", "-c", "user.name=l1", "commit", "-q", "-m", "L1 mini fixture")
    blobs = [git(fx, "rev-parse", f"HEAD:{n}").strip() for n in ("roster.json", "manifest.jsonl", "questions.jsonl")]
    return blobs[0], blobs[1], blobs[2], len(manifest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path, help="real jev checkout (frozen blobs)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--build-fixture", action="store_true",
                    help="internal: build the mini fixture repo at --out and print its blobs (run as a "
                         "subprocess so the test parent never loads kev/tokenizers in-process)")
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    if a.build_fixture:
        print(json.dumps(build_mini_fixture(a.out.expanduser().resolve(strict=False), repo, 3)))
        return 0
    out = a.out.expanduser().resolve(strict=False)
    assert inside(out, WJC), "out must be inside ~/wjc"
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    adm_dir = out / "_admissions"
    adm_dir.mkdir()

    spec = importlib.util.spec_from_file_location("runner_v2", RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    # ---------- group 1: compile_and_schema (independent oracle for counts) ----------
    G = "compile_and_schema"
    guarded(G, "python_import_compile", lambda: (
        (lambda r: (r.returncode == 0, "py_compile runner + fake: rc=%d %s" % (r.returncode, r.stderr[-200:])))(
            subprocess.run([sys.executable, "-m", "py_compile", str(RUNNER), str(FAKE)], capture_output=True, text=True))))
    rows = [json.loads(x) for x in git(repo, "cat-file", "blob", MANIFEST_BLOB).splitlines() if x.strip()]
    roster = {r["scene_sha256"]: r for r in json.loads(git(repo, "cat-file", "blob", ROSTER_BLOB))["candidates"]}

    def t_counts():
        kinds = collections.Counter(m["kind"] for m in rows)
        per_run = collections.Counter(m["run"] for m in rows)
        return (len(rows) == 378 and kinds == {"primary": 372, "replay": 6}
                and dict(per_run) == {1: 128, 2: 128, 3: 122}
                and [m["forward_index"] for m in rows] == list(range(1, 379)),
                f"rows={len(rows)} kinds={dict(kinds)} per_run={dict(per_run)} (recounted from blob {MANIFEST_BLOB[:8]})")
    ok_counts = guarded(G, "frozen_manifest_index_and_counts", t_counts)

    def t_schema():
        need = {"scene_sha256", "source_group", "cell", "declared_edit_new", "declared_edit_sa",
                "state_token_len", "frozen_width", "token_ids_sha256"}
        scenes = {m["scene_sha256"] for m in rows}
        bad = [s for s in scenes if s not in roster or not need <= set(roster[s])]
        return not bad and len(scenes) == 124, f"{len(scenes)} manifest scenes, roster fields present; missing={len(bad)}"
    guarded(G, "runtime_input_schema", t_schema)

    # ---------- group 2: native_full_input ----------
    G = "native_full_input"
    adm_real = write_admission(adm_dir / "real_378.json", 378, 3)
    pf = out / "T2_preflight"
    run_runner(repo, adm_real, pf, preflight=True)

    def t_preflight():
        rec = receipt_of(pf)
        return (rec["status"] == "COMPLETE_A461_G5_G2_STAGE_A_PREFLIGHT" and rec["token_gate"] == "372/372 PASS"
                and rec["manifest_roster_tuple_gate"] == "372/372 PASS" and rec["model_loads"] == 0
                and rec["physical_prehook_calls"] == 0 and rec["cuda_initialized"] is False,
                f"status={rec['status']} token={rec.get('token_gate')} tuple={rec.get('manifest_roster_tuple_gate')} "
                f"dry={canon(rec.get('ledger_dry_run'))}")
    guarded(G, "corpus_to_roster_and_manifest_token_sha", t_preflight)
    eff = runner.effective_entries(rows)
    by_idx = {e["forward_index"]: e for e in eff}
    replays = [e for e in eff if e["kind"] == "replay"]

    def t_eff():
        refs = {e["forward_index"]: e["replay_of_forward_index"] for e in replays}
        inh = all(e[k] is not None and e[k] == by_idx[e["replay_of_forward_index"]][k]
                  for e in replays for k in runner.INHERITED_FIELDS)
        return (len(eff) == 378 and refs == {127: 1, 128: 1, 255: 129, 256: 129, 377: 257, 378: 257} and inh,
                f"effective={len(eff)} replay refs={refs}; all {len(runner.INHERITED_FIELDS)} fields inherited == primary")
    guarded(G, "primary_and_replay_all_call_contracts", t_eff)

    def t_eff_neg():
        cases = {}
        for name, mut in (("ref_to_new_arm", lambda m: m[126].update(replay_of_forward_index=2)),
                          ("ref_cross_run", lambda m: m[254].update(replay_of_forward_index=1)),
                          ("conflicting_width", lambda m: m[126].update(frozen_width=34)),
                          ("dangling_ref", lambda m: m[126].update(replay_of_forward_index=999))):
            m = [dict(x) for x in rows]
            mut(m)
            try:
                runner.effective_entries(m)
                cases[name] = "ACCEPTED"
            except RuntimeError:
                cases[name] = "REJECTED"
        return all(v == "REJECTED" for v in cases.values()), canon(cases)
    guarded(G, "replay_effective_entry_negative_cases", t_eff_neg)

    def t_span():
        bad = [e["forward_index"] for e in eff if e["kind"] == "primary" and
               (e["token_ids_sha256"], e["state_token_len"], e["frozen_width"], e["cell"], e["source_group"]) !=
               (roster[e["scene_sha256"]]["token_ids_sha256"][e["arm"]],
                roster[e["scene_sha256"]]["state_token_len"][e["arm"]], roster[e["scene_sha256"]]["frozen_width"],
                roster[e["scene_sha256"]]["cell"], roster[e["scene_sha256"]]["source_group"])]
        widths = {roster[s]["state_token_len"]["new"] - roster[s]["state_token_len"]["old"] for s in roster
                  if s in {e["scene_sha256"] for e in eff}}
        return not bad and widths == {31}, f"tuple mismatches={len(bad)}; new-old state length deltas={sorted(widths)}"
    guarded(G, "span_suffix_branch_and_question_gold_checks", t_span)

    # ---------- group 3: fake_model_full_path (REAL 378 manifest) ----------
    G = "fake_model_full_path"
    fp = out / "T3_fullpath"
    run_runner(repo, adm_real, fp)
    rec3, raws3 = receipt_of(fp), raw_rows(fp)

    def t_full():
        brs = [json.loads((fp / f"batch_receipt_run{b}.json").read_text("utf8")) for b in (1, 2, 3)]
        shape = [(x["run"], x["planned"], x["physical"], x["rows"], x["status"]) for x in brs]
        return (rec3["status"] == "COMPLETE_A461_G5_G2_STAGE_A_SCREEN" and rec3["physical_forwards"] == 378
                and rec3["fake_model_forward_invocations"] == 378 and len(raws3) == 378
                and [x["forward_index"] for x in raws3] == list(range(1, 379))
                and shape == [(1, 128, 128, 128, "COMPLETE"), (2, 128, 128, 128, "COMPLETE"),
                              (3, 122, 122, 122, "COMPLETE")] and sums_ok(fp),
                f"status={rec3['status']} physical={rec3.get('physical_forwards')} rows={len(raws3)} batches={shape}")
    guarded(G, "planned_forwards_all_covered", t_full)
    rep3 = [x for x in raws3 if x["kind"] == "replay"]
    guarded(G, "replay_effective_entry_inherits_primary_metadata", lambda: (
        len(rep3) == 6 and all(x[k] is not None for x in rep3 for k in runner.INHERITED_FIELDS),
        f"{len(rep3)} replay raw rows, inherited metadata non-null"))
    fwd3 = {x["forward_index"]: x for x in raws3}
    guarded(G, "replay_bitwise_pass", lambda: (
        len(rep3) == 6 and all(fwd3[x["replay_of_forward_index"]]["questions"] == x["questions"] for x in rep3),
        "6/6 replay logits == referenced primary logits"))

    # mini fixture for synthetic faults
    fx = out / "_fixture_repo"
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--repo-root", str(repo), "--out", str(fx),
                        "--build-fixture"], capture_output=True, text=True, check=True, timeout=1200)
    blob_r, blob_m, blob_q, n_mini = json.loads(r.stdout.strip().splitlines()[-1])
    mini = ("--roster-blob", blob_r, "--manifest-blob", blob_m, "--g5v2-questions-blob", blob_q,
            "--expect-total", str(n_mini), "--expect-batches", str(n_mini))
    adm_mini = write_admission(adm_dir / "mini_11.json", n_mini, 1)
    rb = out / "T3b_replay_mismatch"
    run_runner(fx, adm_mini, rb, fault="callcount", extra=mini)

    def t_replay_fail():
        rec, rr = receipt_of(rb), raw_rows(rb)
        return (rec["status"] == "FAIL_A461_G5_G2_STAGE_A_SCREEN" and "replay not bitwise" in rec["error_message"]
                and len(rr) == 10 and rr[-1]["kind"] == "replay" and sums_ok(rb),
                f"status={rec['status']} err={rec.get('error_message', '')[:50]} raw rows kept={len(rr)} (replay row "
                f"saved before the bitwise gate)")
    guarded(G, "replay_bitwise_fault_fail", t_replay_fail)

    # ---------- group 4: physical_per_batch ----------
    G = "physical_per_batch"

    def t_guard():
        try:
            runner.batch_guard(128, 128)
            return False, "guard(128,128) did not raise"
        except RuntimeError:
            pass
        runner.batch_guard(127, 128)
        return True, "guard(128,128) raises; guard(127,128) passes"
    guarded(G, "batch_guard_unit", t_guard)
    for b, call, refused in ((1, 127, 128), (2, 255, 256), (3, 377, 378)):
        d = out / f"T4_cap_batch{b}"
        run_runner(repo, adm_real, d, fault=f"doublefire@{call}")

        def t_cap(d=d, b=b, call=call, refused=refused):
            rec = receipt_of(d)
            cap = {1: 128, 2: 128, 3: 122}[b]
            return (rec["status"] == "FAIL_A461_G5_G2_STAGE_A_SCREEN"
                    and f"batch physical cap: call {cap + 1} of {cap}" in rec["error_message"]
                    and rec["fake_model_forward_invocations"] == refused - 1
                    and rec["physical_by_batch_at_failure"][str(b)] == cap
                    and rec["batch_receipts"][b - 1]["status"] == "FAILED_AT_THIS_BATCH"
                    and all(x["status"] == "COMPLETE" for x in rec["batch_receipts"][:b - 1])
                    and all(x["status"] == "NOT_STARTED" for x in rec["batch_receipts"][b:])
                    and len(raw_rows(d)) == refused - 1 and sums_ok(d),
                    f"hidden extra lm call at {call} -> batch {b} physical={cap}; entry {refused} = physical "
                    f"{cap + 1} of batch refused before model; model invocations={rec.get('fake_model_forward_invocations')}")
        guarded(G, f"physical_cap_plus_one_batch{b}_refused_before_model", t_cap)
    guarded(G, "all_batch_counts_exact", lambda: (
        [json.loads((fp / f"batch_receipt_run{b}.json").read_text("utf8"))["physical"] for b in (1, 2, 3)]
        == [128, 128, 122] and rec3["physical_prehook_calls"] == 378,
        "per-batch pre-hook ledgers 128/128/122, global 378 (T3)"))
    adm_over = write_admission(adm_dir / "mini_over.json", n_mini - 4, 1)
    tb = out / "T4_budget_overrun"
    run_runner(fx, adm_over, tb, extra=mini)

    def t_over():
        rec = receipt_of(tb)
        return (rec["status"] == "FAIL_A461_G5_G2_STAGE_A_SCREEN" and "cumulative overrun" in rec["error_message"]
                and rec["model_loads"] == 0 and rec["physical_prehook_calls"] == 0 and not raw_rows(tb),
                f"plan {n_mini} > approved {n_mini - 4}: refused at admission, 0 loads, 0 calls")
    guarded(G, "attempt_extra_forward_before_model_must_fail", t_over)
    adm_res = write_admission(adm_dir / "mini_resume.json", n_mini, 1, consumed=4)
    tr = out / "T4_resume_after_dropout"
    run_runner(fx, adm_res, tr, extra=mini)

    def t_resume():
        rec = receipt_of(tr)
        return (rec["status"] == "FAIL_A461_G5_G2_STAGE_A_SCREEN" and "cumulative overrun" in rec["error_message"]
                and rec["physical_prehook_calls"] == 0,
                f"same authorization ({n_mini}) with 4 already consumed: rerun refused, 0 calls")
    guarded(G, "abort_resume_cumulative_count_no_overrun", t_resume)
    tg = out / "T4_fake_admission_gpu_backend"
    run_runner(fx, adm_mini, tg, backend="gpu", extra=mini)

    def t_gpu_refused():
        rec = receipt_of(tg)
        return (rec["status"] == "FAIL_A461_G5_G2_STAGE_A_SCREEN" and "L1_FAKE" in rec["error_message"]
                and rec["gpu_model_loads"] == 0 and rec["cuda_initialized"] is False
                and rec["model_loads"] == 0,
                f"gpu backend with L1_FAKE admission refused before any load/CUDA: {rec.get('error_message', '')[:60]}")
    guarded(G, "fake_admission_cannot_authorize_gpu", t_gpu_refused)

    # ---------- group 5: fail_closed_storage ----------
    G = "fail_closed_storage"
    tf = out / "T5_forward_throw"
    run_runner(fx, adm_mini, tf, fault="throw4", extra=mini)

    def t_throw():
        rec, att = receipt_of(tf), attempt_rows(tf)
        return (rec["status"] == "FAIL_A461_G5_G2_STAGE_A_SCREEN" and len(att) == 1
                and att[0]["status"] == "FORWARD_FAILED" and att[0]["forward_index"] == 4
                and att[0]["logits_saved"] is False
                and rec["physical_prehook_count_at_failure"] == 4 and rec["native_model_forward_calls"] == 3
                and sums_ok(tf),
                f"attempt rows={len(att)} status={att[0]['status'] if att else None}; physical consumed=4 "
                f"(charged to authorization), successful=3")
    guarded(G, "forward_throw_keeps_attempt_receipt", t_throw)
    guarded(G, "post_forward_failure_keeps_raw_lines", lambda: (
        [x["forward_index"] for x in raw_rows(tf)] == [1, 2, 3],
        "raw rows 1..3 kept after call 4 threw"))
    tn = out / "T5_nonfinite"
    run_runner(fx, adm_mini, tn, fault="nonfinite2", extra=mini)

    def t_nonfinite():
        rec, att = receipt_of(tn), attempt_rows(tn)
        return (rec["status"] == "FAIL_A461_G5_G2_STAGE_A_SCREEN" and "invalid logits" in rec["error_message"]
                and len(att) == 1 and att[0]["status"] == "INVALID_OUTPUT" and att[0]["forward_index"] == 2
                and [x["forward_index"] for x in raw_rows(tn)] == [1] and rec["native_model_forward_calls"] == 2
                and sums_ok(tn),
                f"NaN at call 2 -> INVALID_OUTPUT attempt row (distinct from FORWARD_FAILED), raw rows=[1]")
    guarded(G, "nonfinite_shape_error_fail_receipt", t_nonfinite)
    outside = Path.home() / ("jev_l1_outside_probe_" + out.name)  # never created: refused before mkdir
    r = run_runner(fx, adm_mini, outside, extra=mini)

    def t_outside():
        return (r.returncode != 0 and not outside.exists() and "inside ~/wjc" in r.stderr,
                f"out={outside} rc={r.returncode} created={outside.exists()}")
    guarded(G, "output_realpath_inside_wjc_and_append_only", t_outside)
    r2 = run_runner(fx, adm_mini, tf, extra=mini)
    guarded(G, "existing_out_dir_never_overwritten", lambda: (
        r2.returncode != 0 and receipt_of(tf)["status"] == "FAIL_A461_G5_G2_STAGE_A_SCREEN"
        and [x["forward_index"] for x in raw_rows(tf)] == [1, 2, 3] and sums_ok(tf),
        "rerun into an existing out dir refused; prior receipt/rows untouched"))

    # ---------- group 6: freezing_and_independence ----------
    G = "freezing_and_independence"
    runner_blob = git(repo, "hash-object", str(RUNNER)).strip()
    guarded(G, "source_hash_and_code_blob_pins", lambda: (
        rec3["runner_blob"] == runner_blob and rec3["frozen_inputs"] == {
            "roster_blob": ROSTER_BLOB, "manifest_blob": MANIFEST_BLOB, "g5v2_questions_blob": G5V2_BLOB,
            "corpus_sha256": CORPUS_SHA} and runner.BLOB_MANIFEST == MANIFEST_BLOB and runner.BLOB_ROSTER == ROSTER_BLOB,
        f"runner blob {runner_blob[:12]} in receipt; frozen input pins == review pins"))
    dirs = [d for d in out.iterdir() if d.name.startswith("T") and (d / "execution_receipt.json").exists()]
    guarded(G, "no_model_load_no_gpu_no_network_in_l1", lambda: (
        all(receipt_of(d)["gpu_model_loads"] == 0 and receipt_of(d)["cuda_initialized"] is False
            and receipt_of(d)["network_calls"] == 0 for d in dirs) and len(dirs) == 11,
        f"{len(dirs)} runner receipts: gpu_model_loads=0, CUDA never initialized, network_calls=0"))
    guarded(G, "separate_test_oracle_for_manifest_counts", lambda: (
        ok_counts, "manifest counts recounted by this suite from the blob, not via the runner"))

    # ---------- matrix + receipt ----------
    all_ok = all(m["verdict"] == "PASS" for m in MATRIX)
    groups = collections.OrderedDict()
    for m in MATRIX:
        groups.setdefault(m["group"], []).append(m["test"] + ":" + m["verdict"])
    save(out / "L1_test_matrix.json", {"schema": "JEV_A461_G5_G2_STAGE_A_L1_TEST_MATRIX_V1",
                                       "policy": "research_governance/JEV_L1_L2_L3_GATE_MATRIX_V1.json",
                                       "pilot_task": "A461_G5_G2_STAGE_A_GPU_SCREEN_RUNNER_G0_V2",
                                       "groups": groups, "tests": MATRIX, "all_pass": all_ok})
    receipt = {"schema": "JEV_A461_G5_G2_STAGE_A_L1_TEST_RECEIPT_V1",
               "status": "COMPLETE_A461_G5_G2_STAGE_A_L1_TESTS" if all_ok else "L1_FAILURES_PRESENT",
               "tests": len(MATRIX), "passed": sum(1 for m in MATRIX if m["verdict"] == "PASS"),
               "runner_blob": runner_blob, "fake_model_blob": git(repo, "hash-object", str(FAKE)).strip(),
               "test_suite_blob": git(repo, "hash-object", str(Path(__file__).resolve())).strip(),
               "manifest_blob": MANIFEST_BLOB, "roster_blob": ROSTER_BLOB,
               "tested_command": "python3 A461_g5_g2_stage_a_l1_tests_v1.py --repo-root <jev checkout> --out <~/wjc/...>",
               "runner_invocations": EVIDENCE,
               "fault_injection_evidence": ["callcount: replay bitwise mismatch -> FAIL, rows kept",
                                            "doublefire@127/255/377: per-batch physical cap+1 refused before model",
                                            "throw4: FORWARD_FAILED attempt row, physical 4 charged",
                                            "nonfinite2: INVALID_OUTPUT attempt row",
                                            "approved < plan: refused at admission",
                                            "consumed + plan > approved: resume refused",
                                            "L1_FAKE admission + gpu backend: refused before any load/CUDA",
                                            "out dir outside ~/wjc or existing: refused"],
               "gpu_calls": 0, "native_forwards": 0}
    save(out / "L1_test_receipt.json", receipt)
    print(canon({k: receipt[k] for k in ("status", "tests", "passed", "runner_blob")}))
    return 0 if all_ok else 2


def save(p, v):
    with open(p, "x", encoding="utf8", newline="\n") as f:
        json.dump(v, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    sys.exit(main())
