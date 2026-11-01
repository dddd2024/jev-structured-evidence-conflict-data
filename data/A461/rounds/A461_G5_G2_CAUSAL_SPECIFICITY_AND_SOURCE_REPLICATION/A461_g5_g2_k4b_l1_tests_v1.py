#!/usr/bin/env python3
"""A461-G5-G2 kev-4B Stage-A screen runner self-test (the Stage-A L1 suite V3, retargeted to the kev-4B runner) (per JEV_L1_L2_L3_GATE_MATRIX_V1).

Pilot task: A461_G5_G2_STAGE_A_GPU_SCREEN_RUNNER_G0_V4 (fix cycle for L2 delta
review 0c676ab; V2 suite cases for review 277fdb7 kept). V3 adds: hidden extra
LM call at EVERY batch boundary entry (127/128, 255/256, 377/378) refused at
the LM pre-hook itself; SIGKILL at the last entry of batch 1 with recovery
refusal; attempt_manifest bijection (deleted / mismatched / duplicated
manifest refused, provably zero-forward start tolerated, zero-reservation
start with evidence refused); fsync durability counts and an injected raw-row
fsync failure that must stop before the next reservation.
Runs runner V4 as a subprocess through its full paths with
the pure-python FakeModel, on the REAL frozen 378-row manifest and on
synthetic mini-manifests committed to throwaway git repos, plus:
  - durable quota ledger: same approval reused from different output dirs
    after complete / partial / SIGKILL attempts, lost ledger, moved run dir,
    tampered ledger, held lock
  - gpu backend admission exercised up to (not including) model load via
    --pre-model-gate-only with a SYNTHETIC, L1-labelled GPU admission, and
    negative cases for every unapproved plan/blob/identity/runner value,
    including the reviewer's 134/122/122 re-partition counterexample
Every runner subprocess gets CUDA_VISIBLE_DEVICES="" so no test can reach a
GPU even if a gate were wrong. Zero GPU, zero native forwards, no network.
Outputs L1_test_matrix.json + L1_test_receipt.json in --out.
"""
import argparse, collections, fcntl, hashlib, importlib.util, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_g5_g2_k4b_stage_a_screen_runner_v1.py"
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
FAIL = "FAIL_A461_G5_G2_STAGE_A_SCREEN"
DONE = "COMPLETE_A461_G5_G2_STAGE_A_SCREEN"
MATRIX = []
EVIDENCE = []


def inside(p, root):
    try:
        Path(p).relative_to(root)
        return True
    except ValueError:
        return False


def record(group, test, ok, evidence):
    MATRIX.append({"group": group, "test": test, "verdict": "PASS" if ok else "FAIL", "evidence": evidence})
    print(("PASS " if ok else "FAIL ") + group + "/" + test + " :: " + evidence[:170], flush=True)
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


def jsonl(p):
    p = Path(p)
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def raw_rows(outdir):
    return jsonl(Path(outdir) / "raw_native_logits_stage_a.jsonl")


def attempt_rows(outdir):
    return jsonl(Path(outdir) / "attempt_receipts.jsonl")


def sums_ok(outdir):
    """SHA256SUMS lists every produced file and each hash matches the bytes."""
    lines = (Path(outdir) / "SHA256SUMS").read_text("utf8").splitlines()
    for ln in lines:
        h, n = ln.split("  ", 1)
        if hashlib.sha256((Path(outdir) / n).read_bytes()).hexdigest() != h:
            return False
    listed = {ln.split("  ", 1)[1] for ln in lines} | {"SHA256SUMS"}
    return listed == {p.name for p in Path(outdir).iterdir()}


def run_runner(repo, admission, out, fault="none", backend="fake", extra=(), mode=None, quota=None, env_extra=None):
    cmd = [sys.executable, str(RUNNER), "--repo-root", str(repo), "--admission", str(admission),
           "--backend", backend, "--out", str(out), *extra]
    if mode:
        cmd.append(mode)
    if quota is not None:
        cmd += ["--quota-root", str(quota)]
    env = dict(os.environ, FAKE_FAULT=fault, CUDA_VISIBLE_DEVICES="", **(env_extra or {}))
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=3000)
    EVIDENCE.append({"out": out.name, "fault": fault, "backend": backend, "returncode": r.returncode,
                     "command": " ".join(cmd[1:]).replace(str(HERE) + "/", ""),
                     "stderr_tail": r.stderr[-600:]})
    if r.returncode < 0:
        print(f"!! runner {out.name} killed by signal {-r.returncode}: {r.stderr[-300:]}", flush=True)
    return r


def ledger_events(quota, admission_id):
    return jsonl(Path(quota) / admission_id / "ledger.jsonl")


def consumed(events):
    return (sum(1 for e in events if e["event"] == "reserve")
            + sum(int(e["count"]) for e in events if e["event"] == "unreserved_physical"))


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


def build_repartition_fixture(fx, real_repo, rows):
    """Reviewer 277fdb7 counterexample: the same 124 scenes / 372 primaries
    re-partitioned 44/40/40 scenes + 2 replays per batch = 134/122/122, with
    byte-identical roster and questions blobs. Returns the new manifest blob."""
    prim = [r for r in rows if r["kind"] == "primary"]
    scenes = []
    for r in prim:
        if r["scene_sha256"] not in scenes:
            scenes.append(r["scene_sha256"])
    by_scene = collections.defaultdict(list)
    for r in prim:
        by_scene[r["scene_sha256"]].append(r)
    out, idx = [], 0
    for b, chunk in ((1, scenes[:44]), (2, scenes[44:84]), (3, scenes[84:])):
        first_old = None
        for s in chunk:
            for r in by_scene[s]:
                idx += 1
                nr = dict(r, forward_index=idx, run=b)
                if r["arm"] == "old" and first_old is None:
                    first_old = nr
                out.append(nr)
        for _ in range(2):
            idx += 1
            out.append({"forward_index": idx, "run": b, "kind": "replay", "arm": "old",
                        "frozen_width": 31, "replay_of_forward_index": first_old["forward_index"],
                        "scene_sha256": first_old["scene_sha256"]})
    subprocess.run(["git", "init", "-q", str(fx)], check=True)
    (fx / "roster.json").write_bytes(subprocess.run(["git", "-C", str(real_repo), "cat-file", "blob", ROSTER_BLOB],
                                                    capture_output=True, check=True).stdout)
    (fx / "questions.jsonl").write_bytes(subprocess.run(["git", "-C", str(real_repo), "cat-file", "blob", G5V2_BLOB],
                                                        capture_output=True, check=True).stdout)
    (fx / "manifest.jsonl").write_text("".join(canon(r) + "\n" for r in out), encoding="utf8")
    git(fx, "add", "roster.json", "manifest.jsonl", "questions.jsonl")
    git(fx, "-c", "user.email=l1@test", "-c", "user.name=l1", "commit", "-q", "-m", "134/122/122 counterexample")
    blobs = {n: git(fx, "rev-parse", f"HEAD:{n}").strip() for n in ("roster.json", "manifest.jsonl", "questions.jsonl")}
    assert blobs["roster.json"] == ROSTER_BLOB and blobs["questions.jsonl"] == G5V2_BLOB
    counts = collections.Counter(r["run"] for r in out)
    assert dict(counts) == {1: 134, 2: 122, 3: 122} and len(out) == 378
    return blobs["manifest.jsonl"]


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
    quota = out / "_quota"
    quota.mkdir()

    spec = importlib.util.spec_from_file_location("runner_k4b", RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    global STAGE
    STAGE = runner.STAGE   # kev-4B runner has its own stage name
    runner_blob = git(repo, "hash-object", str(RUNNER)).strip()

    def fake_adm(name, approved, batches, admission_id, **kw):
        p = adm_dir / f"{name}.json"
        p.write_text(json.dumps(dict({"stage": STAGE, "mode": "L1_FAKE", "admission_id": admission_id,
                                      "approved_max_native_forwards": approved, "approved_batches": batches,
                                      "blind_review_verdict": None, "explicit_user_gpu_approval": False,
                                      "blind_review_runner_blob": None}, **kw)) + "\n", encoding="utf8")
        return p

    def gpu_adm(name, admission_id, **kw):
        """SYNTHETIC GPU-shaped admission for --pre-model-gate-only tests only."""
        p = adm_dir / f"{name}.json"
        p.write_text(json.dumps(dict({
            "stage": STAGE, "mode": "GPU", "admission_id": admission_id,
            "l1_synthetic_not_an_authorization": True,
            "approved_max_native_forwards": 378, "approved_batches": 3, "approved_batch_plan": [128, 128, 122],
            "frozen_inputs": {"roster_blob": ROSTER_BLOB, "manifest_blob": MANIFEST_BLOB,
                              "g5v2_questions_blob": G5V2_BLOB, "corpus_sha256": CORPUS_SHA},
            "model_identity_sha256": runner.identity_digest(runner.MODEL_IDENTITY),
            "blind_review_verdict": "PASS", "blind_review_runner_blob": runner_blob,
            "explicit_user_gpu_approval": True}, **kw)) + "\n", encoding="utf8")
        return p

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
    pf = out / "T2_preflight"
    run_runner(repo, fake_adm("preflight", 378, 3, "L1_PREFLIGHT_0001"), pf, mode="--preflight-only")

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
    run_runner(repo, fake_adm("full", 378, 3, "L1_FULLPATH_0001"), fp, quota=quota)
    rec3, raws3 = receipt_of(fp), raw_rows(fp)

    def t_full():
        brs = [json.loads((fp / f"batch_receipt_run{b}.json").read_text("utf8")) for b in (1, 2, 3)]
        shape = [(x["run"], x["planned"], x["physical"], x["rows"], x["status"]) for x in brs]
        ev = ledger_events(quota, "L1_FULLPATH_0001")
        return (rec3["status"] == DONE and rec3["physical_forwards"] == 378
                and rec3["fake_model_forward_invocations"] == 378 and len(raws3) == 378
                and [x["forward_index"] for x in raws3] == list(range(1, 379))
                and shape == [(1, 128, 128, 128, "COMPLETE"), (2, 128, 128, 128, "COMPLETE"),
                              (3, 122, 122, 122, "COMPLETE")] and sums_ok(fp)
                and consumed(ev) == 378 and [e["event"] for e in ev][0] == "attempt_open"
                and ev[-1]["event"] == "attempt_close",
                f"status={rec3['status']} physical={rec3.get('physical_forwards')} rows={len(raws3)} batches={shape} "
                f"ledger reserved={consumed(ev)} (open..close)")
    guarded(G, "planned_forwards_all_covered", t_full)
    rep3 = [x for x in raws3 if x["kind"] == "replay"]
    guarded(G, "replay_effective_entry_inherits_primary_metadata", lambda: (
        len(rep3) == 6 and all(x[k] is not None for x in rep3 for k in runner.INHERITED_FIELDS),
        f"{len(rep3)} replay raw rows, inherited metadata non-null"))
    fwd3 = {x["forward_index"]: x for x in raws3}
    guarded(G, "replay_bitwise_pass", lambda: (
        len(rep3) == 6 and all(fwd3[x["replay_of_forward_index"]]["questions"] == x["questions"] for x in rep3),
        "6/6 replay logits == referenced primary logits"))

    fx = out / "_fixture_repo"
    r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--repo-root", str(repo), "--out", str(fx),
                        "--build-fixture"], capture_output=True, text=True, check=True, timeout=1200)
    blob_r, blob_m, blob_q, n_mini = json.loads(r.stdout.strip().splitlines()[-1])
    mini = ("--roster-blob", blob_r, "--manifest-blob", blob_m, "--g5v2-questions-blob", blob_q,
            "--expect-total", str(n_mini), "--expect-batches", str(n_mini))
    rb = out / "T3b_replay_mismatch"
    run_runner(fx, fake_adm("replay_fail", n_mini, 1, "L1_REPLAYFAIL_0001"), rb, fault="callcount", extra=mini, quota=quota)

    def t_replay_fail():
        rec, rr = receipt_of(rb), raw_rows(rb)
        return (rec["status"] == FAIL and "replay not bitwise" in rec["error_message"]
                and len(rr) == 10 and rr[-1]["kind"] == "replay" and sums_ok(rb),
                f"status={rec['status']} err={rec.get('error_message', '')[:50]} raw rows kept={len(rr)}")
    guarded(G, "replay_bitwise_fault_fail", t_replay_fail)

    # ---------- group 4: physical_per_batch ----------
    G = "physical_per_batch"

    def t_guard():
        try:
            runner.batch_guard(128, 128)
            return False, "guard(128,128) did not raise"
        except RuntimeError:
            pass
        try:
            runner.batch_guard(128, 134)
            return False, "guard(128,134) did not raise (cap above RUN_CAP)"
        except RuntimeError:
            pass
        runner.batch_guard(127, 128)
        return True, "guard(128,128) and guard(128,134) raise; guard(127,128) passes"
    guarded(G, "batch_guard_unit", t_guard)
    for b, call in ((1, 127), (1, 128), (2, 255), (2, 256), (3, 377), (3, 378)):
        d = out / f"T4_hook_extra_lm_call_{call}"
        aid = f"L1_HOOK_EXTRA_{call}_0001"
        run_runner(repo, fake_adm(f"hook{call}", 378, 3, aid), d, fault=f"doublefire@{call}", quota=quota)

        def t_hook(d=d, b=b, call=call, aid=aid):
            rec, att = receipt_of(d), attempt_rows(d)
            cap = {1: 128, 2: 128, 3: 122}[b]
            in_batch = call - {1: 0, 2: 128, 3: 256}[b]
            ev = ledger_events(quota, aid)
            return (rec["status"] == FAIL
                    and "LM pre-hook refused call before LM body: no unused reservation" in rec["error_message"]
                    and rec["denied_prehook_calls"] == 1 and rec["physical_prehook_calls"] == call
                    and rec["physical_by_batch_at_failure"][str(b)] == in_batch <= cap
                    and rec["fake_model_forward_invocations"] == call - 1
                    and len(att) == 1 and att[0]["status"] == "FORWARD_FAILED" and att[0]["forward_index"] == call
                    and rec["batch_receipts"][b - 1]["status"] == "FAILED_AT_THIS_BATCH"
                    and all(x["status"] == "COMPLETE" for x in rec["batch_receipts"][:b - 1])
                    and all(x["status"] == "NOT_STARTED" for x in rec["batch_receipts"][b:])
                    and len(raw_rows(d)) == call - 1 and sums_ok(d)
                    and consumed(ev) == call and not any(e["event"] == "unreserved_physical" for e in ev),
                    f"2nd LM pre-hook inside reserved call {call} denied at the hook: batch {b} physical "
                    f"{in_batch}/{cap} (never above), global physical {call}, denied 1, ledger {consumed(ev)} "
                    f"reservations, 0 unreserved")
        guarded(G, f"extra_lm_call_at_{call}_denied_at_prehook", t_hook)
    ke = out / "T4_sigkill_last_entry_batch1"
    KE = "L1_SIGKILL_EDGE_0001"
    rke = run_runner(repo, fake_adm("kedge", 378, 3, KE), ke, fault="sigkill@128", quota=quota)
    run_runner(repo, fake_adm("kedge", 378, 3, KE), out / "T4_after_sigkill_last_entry", quota=quota)

    def t_kill_edge():
        ev = ledger_events(quota, KE)
        rec2 = receipt_of(out / "T4_after_sigkill_last_entry")
        pa = list(rec2.get("quota_ledger", {}).get("prior_attempts", {}).values())
        return (rke.returncode == -9 and not (ke / "execution_receipt.json").exists()
                and consumed(ev) == 128 and len(raw_rows(ke)) == 127
                and rec2["status"] == FAIL and "ledger consumed 128" in rec2["error_message"]
                and rec2["physical_prehook_calls"] == 0 and len(pa) == 1 and pa[0]["state"] == "UNCLOSED"
                and pa[0]["ledgered_calls"] == 128 and pa[0]["saved_call_rows"] == 127,
                f"SIGKILL inside call 128 (last entry of batch 1): ledger 128, durable raw rows 127, no receipt; "
                f"recovery attempt refused (128 + 378 > 378), prior attempt reported UNCLOSED")
    guarded(G, "sigkill_at_batch_edge_charged_and_recovery_refused", t_kill_edge)
    guarded(G, "all_batch_counts_exact", lambda: (
        [json.loads((fp / f"batch_receipt_run{b}.json").read_text("utf8"))["physical"] for b in (1, 2, 3)]
        == [128, 128, 122] and rec3["physical_prehook_calls"] == 378 and rec3["ledger_reserved_calls"] == 378,
        "per-batch pre-hook ledgers 128/128/122, global 378, durable reservations 378 (T3)"))
    tb = out / "T4_budget_overrun"
    run_runner(fx, fake_adm("over", n_mini - 4, 1, "L1_OVER_0001"), tb, extra=mini, quota=quota)

    def t_over():
        rec = receipt_of(tb)
        return (rec["status"] == FAIL and "cumulative overrun" in rec["error_message"]
                and rec["model_loads"] == 0 and rec["physical_prehook_calls"] == 0 and not raw_rows(tb),
                f"plan {n_mini} > approved {n_mini - 4}: refused at admission, 0 loads, 0 calls")
    guarded(G, "attempt_extra_forward_before_model_must_fail", t_over)

    # ---------- group 4b: durable_quota_ledger (P0-2) ----------
    G = "durable_quota_ledger"

    def refused_by_ledger(d, needle):
        rec = receipt_of(d)
        return (rec["status"] == FAIL and needle in rec["error_message"] and rec["model_loads"] == 0
                and rec["physical_prehook_calls"] == 0 and not raw_rows(d)
                and not (Path(d) / "attempt_manifest.json").exists())

    # A: complete, then the same approval from new out dirs (stale caller value / no caller value)
    A = "L1_LEDGER_COMPLETE_0001"
    run_runner(fx, fake_adm("A", n_mini, 1, A), out / "L_A1_complete", extra=mini, quota=quota)
    run_runner(fx, fake_adm("A_stale", n_mini, 1, A, cumulative_calls_already_consumed=0),
               out / "L_A2_reuse_stale_consumed0", extra=mini, quota=quota)
    run_runner(fx, fake_adm("A", n_mini, 1, A), out / "L_A3_reuse_new_outdir", extra=mini, quota=quota)
    guarded(G, "same_approval_new_outdir_after_complete_refused", lambda: (
        receipt_of(out / "L_A1_complete")["status"] == DONE
        and refused_by_ledger(out / "L_A2_reuse_stale_consumed0", "stale caller-supplied consumed 0 != ledger 11")
        and refused_by_ledger(out / "L_A3_reuse_new_outdir", "ledger consumed 11"),
        "after a complete 11-call attempt: caller consumed=0 refused as stale; plain reuse refused "
        "(ledger 11 + plan 11 > 11); 0 loads/calls"))
    # B: partial (throw at 4), legit resume within a larger approval, then overrun refused
    B = "L1_LEDGER_PARTIAL_0001"
    run_runner(fx, fake_adm("B", n_mini + 4, 1, B), out / "L_B1_partial_throw4", fault="throw4", extra=mini, quota=quota)
    run_runner(fx, fake_adm("B", n_mini + 4, 1, B), out / "L_B2_resume_within_budget", extra=mini, quota=quota)
    run_runner(fx, fake_adm("B", n_mini + 4, 1, B), out / "L_B3_resume_overrun", extra=mini, quota=quota)

    def t_partial():
        ev = ledger_events(quota, B)
        r1, r2 = receipt_of(out / "L_B1_partial_throw4"), receipt_of(out / "L_B2_resume_within_budget")
        return (r1["status"] == FAIL and r1["quota_ledger"]["consumed_after"] == 4
                and r2["status"] == DONE and r2["quota_ledger"]["consumed_before"] == 4
                and r2["quota_ledger"]["consumed_after"] == 15 and consumed(ev) == 15
                and refused_by_ledger(out / "L_B3_resume_overrun", "ledger consumed 15"),
                f"approval 15: throw at call 4 charges 4 (incl. the failed call); resume of 11 fits (4+11) and "
                f"completes; third attempt refused (15+11>15)")
    guarded(G, "partial_attempt_charged_and_resume_bounded", t_partial)
    # C: abrupt SIGKILL mid-run -> no receipt, ledger still authoritative
    C = "L1_LEDGER_SIGKILL_0001"
    rk = run_runner(fx, fake_adm("C", n_mini, 1, C), out / "L_C1_sigkill5", fault="sigkill@5", extra=mini, quota=quota)
    run_runner(fx, fake_adm("C", n_mini, 1, C), out / "L_C2_after_kill", extra=mini, quota=quota)

    def t_kill():
        ev = ledger_events(quota, C)
        prior = receipt_of(out / "L_C2_after_kill").get("quota_ledger", {}).get("prior_attempts", {})
        pa = list(prior.values())[0] if len(prior) == 1 else {}
        return (rk.returncode == -9 and not (out / "L_C1_sigkill5" / "execution_receipt.json").exists()
                and consumed(ev) == 5 and not any(e["event"] == "attempt_close" for e in ev)
                and len(raw_rows(out / "L_C1_sigkill5")) == 4
                and refused_by_ledger(out / "L_C2_after_kill", "ledger consumed 5")
                and pa.get("receipt") is False and pa.get("closed") is False and pa.get("ledgered_calls") == 5
                and pa.get("saved_call_rows") == 4,
                f"SIGKILL inside call 5: no receipt, no close, 4 raw rows; ledger holds 5 reservations; next "
                f"attempt reconciles prior={canon(pa)[:120]} and is refused")
    guarded(G, "abrupt_stop_missing_receipt_still_charged", t_kill)
    # D: ledger lost while run dirs remain -> fail closed
    Dd = "L1_LEDGER_LOST_0001"
    run_runner(fx, fake_adm("D", 2 * n_mini, 1, Dd), out / "L_D1_complete", extra=mini, quota=quota)
    (quota / Dd / "ledger.jsonl").rename(quota / Dd / "ledger.jsonl.moved_by_L1")
    run_runner(fx, fake_adm("D", 2 * n_mini, 1, Dd), out / "L_D2_after_ledger_loss", extra=mini, quota=quota)
    guarded(G, "lost_ledger_fails_closed", lambda: (
        receipt_of(out / "L_D1_complete")["status"] == DONE
        and refused_by_ledger(out / "L_D2_after_ledger_loss", "quota ledger stale or missing"),
        "ledger removed after a complete run (approval 22 would otherwise allow a 2nd run): refused"))
    # E: ledgered run dir moved away -> ambiguous prior spend
    E = "L1_LEDGER_DIRMOVED_0001"
    run_runner(fx, fake_adm("E", 2 * n_mini, 1, E), out / "L_E1_complete", extra=mini, quota=quota)
    (out / "L_E1_complete").rename(out / "L_E1_complete_moved")
    run_runner(fx, fake_adm("E", 2 * n_mini, 1, E), out / "L_E2_after_dir_move", extra=mini, quota=quota)
    guarded(G, "missing_ledgered_dir_fails_closed", lambda: (
        refused_by_ledger(out / "L_E2_after_dir_move", "ledgered attempt dir missing"),
        "ledgered attempt dir renamed: next attempt refused (prior spend ambiguous)"))
    # F: ledger tampered (reservations removed) -> evidence > ledger
    F = "L1_LEDGER_TAMPER_0001"
    run_runner(fx, fake_adm("F", 2 * n_mini, 1, F), out / "L_F1_complete", extra=mini, quota=quota)
    lp = quota / F / "ledger.jsonl"
    lines = lp.read_text("utf8").splitlines()
    drop = [i for i, x in enumerate(lines) if '"event":"reserve"' in x][:3]
    lp.write_text("".join(x + "\n" for i, x in enumerate(lines) if i not in drop), encoding="utf8")
    run_runner(fx, fake_adm("F", 2 * n_mini, 1, F), out / "L_F2_after_tamper", extra=mini, quota=quota)
    guarded(G, "tampered_ledger_fails_closed", lambda: (
        refused_by_ledger(out / "L_F2_after_tamper", "saved call rows > 8 ledgered calls"),
        "3 reservations deleted from ledger: 11 saved rows > 8 ledgered -> refused"))
    # H: concurrent attempt (lock held) refused
    Hh = "L1_LEDGER_LOCK_0001"
    (quota / Hh).mkdir()
    fd = os.open(str(quota / Hh / ".lock"), os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        run_runner(fx, fake_adm("H", n_mini, 1, Hh), out / "L_H1_locked", extra=mini, quota=quota)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    guarded(G, "concurrent_attempt_lock_refused", lambda: (
        refused_by_ledger(out / "L_H1_locked", "quota ledger locked"),
        "flock held by another holder: attempt refused before any model object"))

    # ---------- group 4d: attempt_manifest bijection (P1-1 of 0c676ab) ----------
    G = "attempt_manifest_bijection"

    def complete_then(tag, mutate):
        aid = f"L1_BIJ_{tag}_0001"
        d1 = out / f"L_BIJ_{tag}_1"
        run_runner(fx, fake_adm(f"bij_{tag}", 2 * n_mini, 1, aid), d1, extra=mini, quota=quota)
        ok1 = receipt_of(d1)["status"] == DONE
        mutate(d1, aid)
        d2 = out / f"L_BIJ_{tag}_2"
        run_runner(fx, fake_adm(f"bij_{tag}", 2 * n_mini, 1, aid), d2, extra=mini, quota=quota)
        return ok1, d2

    def m_delete(d1, aid):
        (d1 / "attempt_manifest.json").unlink()
    ok, d2 = complete_then("DELETED", m_delete)
    guarded(G, "deleted_manifest_refused", lambda: (
        ok and refused_by_ledger(d2, "lacks a matching attempt_manifest.json"),
        "manifest of a completed, ledgered attempt deleted (quota room left): next attempt refused"))

    def m_blob(d1, aid):
        mp = d1 / "attempt_manifest.json"
        am = json.loads(mp.read_text("utf8"))
        am["runner_blob"] = "0" * 40
        mp.write_text(json.dumps(am) + "\n", encoding="utf8")
    ok, d2 = complete_then("BLOBEDIT", m_blob)
    guarded(G, "mismatched_manifest_refused", lambda: (
        ok and refused_by_ledger(d2, "attempt_manifest mismatch"),
        "manifest runner_blob edited: next attempt refused"))

    def m_aid(d1, aid):
        mp = d1 / "attempt_manifest.json"
        am = json.loads(mp.read_text("utf8"))
        am["admission_id"] = "L1_SOME_OTHER_ADMISSION"
        mp.write_text(json.dumps(am) + "\n", encoding="utf8")
    ok, d2 = complete_then("AIDEDIT", m_aid)
    guarded(G, "manifest_admission_id_edit_refused", lambda: (
        ok and refused_by_ledger(d2, "lacks a matching attempt_manifest.json"),
        "manifest admission_id edited (attempt no longer matched): next attempt refused"))

    def m_dup(d1, aid):
        dd = out / "L_BIJ_DUP_copy"
        dd.mkdir()
        (dd / "attempt_manifest.json").write_bytes((d1 / "attempt_manifest.json").read_bytes())
    ok, d2 = complete_then("DUP", m_dup)
    guarded(G, "duplicated_manifest_refused", lambda: (
        ok and refused_by_ledger(d2, "attempt_manifest duplicated"),
        "manifest copied into a second run dir: next attempt refused"))

    def zero_start(tag, with_row):
        aid = f"L1_BIJ_{tag}_0001"
        zd = out / f"L_BIJ_{tag}_open_only"
        zd.mkdir()
        if with_row:
            (zd / "raw_native_logits_stage_a.jsonl").write_text('{"forward_index":1}\n', encoding="utf8")
        (quota / aid).mkdir()
        (quota / aid / "ledger.jsonl").write_text(canon({
            "event": "attempt_open", "attempt_id": "f" * 32, "out_dir": str(zd), "runner_blob": runner_blob,
            "backend": "fake", "plan": [n_mini], "admission_id": aid, "t": 0}) + "\n", encoding="utf8")
        d2 = out / f"L_BIJ_{tag}_next"
        run_runner(fx, fake_adm(f"bij_{tag}", n_mini, 1, aid), d2, extra=mini, quota=quota)
        return d2
    dz = zero_start("ZERO", False)

    def t_zero():
        rec = receipt_of(dz)
        pa = list(rec["quota_ledger"]["prior_attempts"].values())
        return (rec["status"] == DONE and rec["quota_ledger"]["consumed_before"] == 0 and len(pa) == 1
                and pa[0]["state"] == "INCOMPLETE_START_ZERO_FORWARD",
                "crash between attempt_open and attempt_manifest (0 reservations, 0 rows): tolerated as "
                "INCOMPLETE_START_ZERO_FORWARD, next attempt completes within the same approval")
    guarded(G, "zero_forward_incomplete_start_tolerated", t_zero)
    dzr = zero_start("ZEROROW", True)
    guarded(G, "zero_reservation_start_with_evidence_refused", lambda: (
        refused_by_ledger(dzr, "lacks a matching attempt_manifest.json"),
        "open-only attempt holding a raw row but 0 reservations: refused (not provably zero-forward)"))

    # ---------- group 4e: durable evidence (P1-2 of 0c676ab) ----------
    G = "durable_evidence"
    guarded(G, "every_row_and_reservation_fsynced", lambda: (
        rec3["durable_appends"] == {"raw_rows": 378, "attempt_rows": 0, "ledger_events": 380},
        f"T3 full path: durable appends {canon(rec3['durable_appends'])} (378 raw rows, 1 open + 378 reserve "
        f"+ 1 close)"))
    FS = "L1_FSYNC_FAULT_0001"
    dfs = out / "T5_raw_fsync_fault_row5"
    run_runner(fx, fake_adm("fsync", n_mini, 1, FS), dfs, extra=mini, quota=quota,
               env_extra={"L1_FSYNC_FAIL_RAW_ROW": "5"})
    run_runner(fx, fake_adm("fsync", n_mini, 1, FS), out / "T5_after_fsync_fault", extra=mini, quota=quota)

    def t_fsync():
        rec = receipt_of(dfs)
        ev = ledger_events(quota, FS)
        res = [e["forward_index"] for e in ev if e["event"] == "reserve"]
        return (rec["status"] == FAIL and "injected fsync failure" in rec["error_message"]
                and res == [1, 2, 3, 4, 5] and rec["durable_appends"]["raw_rows"] == 4
                and refused_by_ledger(out / "T5_after_fsync_fault", "ledger consumed 5"),
                "fsync of raw row 5 fails -> attempt stops before reserving call 6 (reservations 1..5, durable "
                "rows 4); retry under the same approval refused")
    guarded(G, "raw_row_fsync_failure_stops_before_next_reservation", t_fsync)

    # ---------- group 4c: gpu_admission_pre_model (P0-1, P1-1, P1-2) ----------
    G = "gpu_admission_pre_model"
    P = "L1_SYNTH_GPU_PREMODEL_0001"
    p_ok = out / "P1_gpu_pre_model_ok"
    run_runner(repo, gpu_adm("gpu_ok", P), p_ok, backend="gpu", mode="--pre-model-gate-only")

    def t_gpu_ok():
        rec = receipt_of(p_ok)
        return (rec["status"] == "COMPLETE_A461_G5_G2_STAGE_A_PRE_MODEL_GATE"
                and rec["model_identity_verified"] is True and rec["model_identity"] == runner.MODEL_IDENTITY
                and rec["token_gate"] == "372/372 PASS" and rec["gpu_model_loads"] == 0 and rec["model_loads"] == 0
                and rec["cuda_initialized"] is False and rec["quota_ledger"]["consumed_before"] == 0
                and not (runner.GPU_QUOTA_ROOT / P).exists() and sums_ok(p_ok),
                f"synthetic well-formed GPU admission passes every gate (pins, plan, identity "
                f"{runner.identity_digest(runner.MODEL_IDENTITY)[:12]}, ledger read-only, 372 token) and stops "
                f"before torch/model; real GPU ledger untouched")
    guarded(G, "well_formed_gpu_admission_reaches_pre_model_gate", t_gpu_ok)
    fx2 = out / "_fixture_repartition"
    blob_134 = build_repartition_fixture(fx2, repo, rows)

    def neg(name, admission, extra=(), repo_=repo, needle="", mode="--pre-model-gate-only", backend="gpu", quota_=None):
        d = out / f"P_{name}"
        run_runner(repo_, admission, d, backend=backend, extra=extra, mode=mode, quota=quota_)
        rec = receipt_of(d)
        ok = (rec["status"] == FAIL and needle in rec["error_message"] and rec["model_loads"] == 0
              and rec["gpu_model_loads"] == 0 and rec["cuda_initialized"] is False)
        return ok, f"refused before load: {rec.get('error_message', '')[:90]}"
    guarded(G, "reviewer_134_122_122_counterexample_refused", lambda: neg(
        "repartition_134", gpu_adm("gpu_ok", P), ("--manifest-blob", blob_134, "--expect-batches", "134,122,122"),
        repo_=fx2, needle="input blob override refused"))
    guarded(G, "manifest_blob_override_alone_refused", lambda: neg(
        "manifest_override", gpu_adm("gpu_ok", P), ("--manifest-blob", blob_134), repo_=fx2,
        needle="input blob override refused"))
    guarded(G, "plan_override_alone_refused", lambda: neg(
        "plan_override", gpu_adm("gpu_ok", P), ("--expect-batches", "128,122,128"), needle="plan override refused"))
    guarded(G, "quota_root_override_refused", lambda: neg(
        "quota_override", gpu_adm("gpu_ok", P), (), needle="quota root is fixed", quota_=quota))
    guarded(G, "admission_plan_mismatch_refused", lambda: neg(
        "adm_plan", gpu_adm("adm_plan", P, approved_batch_plan=[134, 122, 122]), needle="admission batch plan"))
    guarded(G, "admission_frozen_inputs_mismatch_refused", lambda: neg(
        "adm_inputs", gpu_adm("adm_inputs", P, frozen_inputs={"roster_blob": ROSTER_BLOB, "manifest_blob": blob_134,
                                                              "g5v2_questions_blob": G5V2_BLOB, "corpus_sha256": CORPUS_SHA}),
        needle="admission frozen_inputs"))
    guarded(G, "admission_runner_blob_mismatch_refused", lambda: neg(
        "adm_runner", gpu_adm("adm_runner", P, blind_review_runner_blob="b0b9f6eea2e43006e743d91696f5bb8e8464c3ee"),
        needle="runner blob != approved runner blob"))
    # policy V2 route: no review verdict, user's verbatim GPU approval bound to this blob
    pv2 = dict(blind_review_verdict=None, blind_review_runner_blob=None,
               governance="JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2",
               user_gpu_approval_quote="L1 synthetic quote (not a real approval)",
               user_gpu_approval_utc="1970-01-01T00:00:00Z", approved_runner_blob=runner_blob)
    p_v2 = out / "P_policy_v2_pre_model_ok"
    run_runner(repo, gpu_adm("policy_v2_ok", P, **pv2), p_v2, backend="gpu", mode="--pre-model-gate-only")
    guarded(G, "policy_v2_user_approval_route_reaches_pre_model_gate", lambda: (
        receipt_of(p_v2)["status"] == "COMPLETE_A461_G5_G2_STAGE_A_PRE_MODEL_GATE"
        and receipt_of(p_v2)["model_loads"] == 0 and receipt_of(p_v2)["cuda_initialized"] is False,
        "policy V2 admission (no review verdict; quote + time + approved_runner_blob) passes all gates, stops "
        "before torch/model"))
    guarded(G, "policy_v2_without_quote_refused", lambda: neg(
        "pv2_noquote", gpu_adm("pv2_noquote", P, **dict(pv2, user_gpu_approval_quote="")),
        needle="no GPU approval route"))
    guarded(G, "policy_v2_wrong_runner_blob_refused", lambda: neg(
        "pv2_blob", gpu_adm("pv2_blob", P, **dict(pv2, approved_runner_blob="b78da9c0476f0558cd77fa9771c04d020830dede")),
        needle="runner blob != approved runner blob"))
    guarded(G, "policy_v2_without_user_gpu_approval_flag_refused", lambda: neg(
        "pv2_noflag", gpu_adm("pv2_noflag", P, **dict(pv2, explicit_user_gpu_approval=False)),
        needle="no explicit user GPU approval"))
    guarded(G, "admission_model_identity_mismatch_refused", lambda: neg(
        "adm_identity", gpu_adm("adm_identity", P, model_identity_sha256="0" * 64), needle="model_identity_sha256"))
    guarded(G, "admission_without_user_approval_refused", lambda: neg(
        "adm_noapproval", gpu_adm("adm_noapproval", P, explicit_user_gpu_approval=False),
        needle="no explicit user GPU approval"))
    guarded(G, "l1_fake_admission_cannot_authorize_gpu", lambda: neg(
        "fake_mode", fake_adm("fake_for_gpu", 378, 3, "L1_FAKE_FOR_GPU_0001"), needle="admission mode GPU"))
    guarded(G, "fake_backend_plan_above_cap_refused", lambda: neg(
        "fake_134", fake_adm("fake_134", 378, 3, "L1_FAKE_134_0001"),
        ("--manifest-blob", blob_134, "--expect-batches", "134,122,122"), repo_=fx2,
        needle="exceeds cap 128", mode=None, backend="fake", quota_=quota))

    def t_identity_unit():
        observed = receipt_of(p_ok)["model_identity"]
        runner.verify_identity(observed, runner.MODEL_IDENTITY)
        caught = []
        for name in ("ckpt", "base", "source"):
            tampered = json.loads(json.dumps(runner.MODEL_IDENTITY))
            tampered[name]["sha256"] = "f" * 64
            try:
                runner.verify_identity(observed, tampered)
            except RuntimeError:
                caught.append(name)
        return caught == ["ckpt", "base", "source"], f"observed == pinned; tampered pin refused for {caught}"
    guarded(G, "model_identity_verify_unit", t_identity_unit)
    full_gpu_outside = out / "P_full_gpu_outside_runs_root"
    rg = run_runner(repo, gpu_adm("gpu_ok", P), full_gpu_outside, backend="gpu")
    guarded(G, "full_gpu_run_outside_runs_root_refused", lambda: (
        rg.returncode != 0 and not full_gpu_outside.exists() and "G2_STAGE_A_GPU_RUNS" in rg.stderr,
        f"full gpu-backend run with out outside G2_STAGE_A_GPU_RUNS: rc={rg.returncode}, nothing created"))

    # ---------- group 5: fail_closed_storage ----------
    G = "fail_closed_storage"
    tf = out / "T5_forward_throw"
    run_runner(fx, fake_adm("throw", n_mini, 1, "L1_THROW_0001"), tf, fault="throw4", extra=mini, quota=quota)

    def t_throw():
        rec, att = receipt_of(tf), attempt_rows(tf)
        return (rec["status"] == FAIL and len(att) == 1
                and att[0]["status"] == "FORWARD_FAILED" and att[0]["forward_index"] == 4
                and att[0]["logits_saved"] is False
                and rec["physical_prehook_count_at_failure"] == 4 and rec["native_model_forward_calls"] == 3
                and rec["ledger_reserved_calls"] == 4 and rec["durable_appends"]["attempt_rows"] == 1
                and sums_ok(tf),
                f"attempt rows={len(att)} status={att[0]['status'] if att else None}; physical 4 = reserved 4, "
                f"successful 3")
    guarded(G, "forward_throw_keeps_attempt_receipt", t_throw)
    guarded(G, "post_forward_failure_keeps_raw_lines", lambda: (
        [x["forward_index"] for x in raw_rows(tf)] == [1, 2, 3],
        "raw rows 1..3 kept after call 4 threw"))
    tn = out / "T5_nonfinite"
    run_runner(fx, fake_adm("nonfinite", n_mini, 1, "L1_NONFINITE_0001"), tn, fault="nonfinite2", extra=mini, quota=quota)

    def t_nonfinite():
        rec, att = receipt_of(tn), attempt_rows(tn)
        return (rec["status"] == FAIL and "invalid logits" in rec["error_message"]
                and len(att) == 1 and att[0]["status"] == "INVALID_OUTPUT" and att[0]["forward_index"] == 2
                and [x["forward_index"] for x in raw_rows(tn)] == [1] and rec["native_model_forward_calls"] == 2
                and sums_ok(tn),
                "NaN at call 2 -> INVALID_OUTPUT attempt row (distinct from FORWARD_FAILED), raw rows=[1]")
    guarded(G, "nonfinite_shape_error_fail_receipt", t_nonfinite)
    outside = Path.home() / ("jev_l1_outside_probe_" + out.name)  # never created: refused before mkdir
    r = run_runner(fx, fake_adm("outside", n_mini, 1, "L1_OUTSIDE_0001"), outside, extra=mini, quota=quota)
    guarded(G, "output_realpath_inside_wjc_and_append_only", lambda: (
        r.returncode != 0 and not outside.exists() and "inside ~/wjc" in r.stderr,
        f"out={outside} rc={r.returncode} created={outside.exists()}"))
    r2 = run_runner(fx, fake_adm("throw", n_mini, 1, "L1_THROW_0001"), tf, extra=mini, quota=quota)
    guarded(G, "existing_out_dir_never_overwritten", lambda: (
        r2.returncode != 0 and receipt_of(tf)["status"] == FAIL
        and [x["forward_index"] for x in raw_rows(tf)] == [1, 2, 3] and sums_ok(tf),
        "rerun into an existing out dir refused; prior receipt/rows untouched"))

    # ---------- group 6: freezing_and_independence ----------
    G = "freezing_and_independence"
    guarded(G, "source_hash_and_code_blob_pins", lambda: (
        rec3["runner_blob"] == runner_blob and rec3["frozen_inputs"] == {
            "roster_blob": ROSTER_BLOB, "manifest_blob": MANIFEST_BLOB, "g5v2_questions_blob": G5V2_BLOB,
            "corpus_sha256": CORPUS_SHA} and runner.BLOB_MANIFEST == MANIFEST_BLOB and runner.BLOB_ROSTER == ROSTER_BLOB
        and runner.FROZEN_BATCHES == [128, 128, 122] and runner.RUN_CAP == 128,
        f"runner blob {runner_blob[:12]} in receipt; frozen input/plan pins == review pins"))
    dirs = [d for d in out.iterdir() if (d / "execution_receipt.json").exists()]
    guarded(G, "no_model_load_no_gpu_no_network_in_l1", lambda: (
        all(receipt_of(d)["gpu_model_loads"] == 0 and receipt_of(d)["cuda_initialized"] is False
            and receipt_of(d)["network_calls"] == 0 for d in dirs)
        and not any(e["backend"] == "gpu" and e["returncode"] == 0 and "--pre-model-gate-only" not in e["command"]
                    for e in EVIDENCE)
        and not runner.GPU_QUOTA_ROOT.exists() and not runner.GPU_RUNS_ROOT.exists(),
        f"{len(dirs)} runner receipts: gpu_model_loads=0, CUDA never initialized, network_calls=0; every subprocess "
        f"CUDA_VISIBLE_DEVICES=''; real GPU ledger/runs roots never created"))
    guarded(G, "separate_test_oracle_for_manifest_counts", lambda: (
        ok_counts, "manifest counts recounted by this suite from the blob, not via the runner"))

    # ---------- matrix + receipt ----------
    all_ok = all(m["verdict"] == "PASS" for m in MATRIX)
    groups = collections.OrderedDict()
    for m in MATRIX:
        groups.setdefault(m["group"], []).append(m["test"] + ":" + m["verdict"])
    save(out / "L1_test_matrix.json", {"schema": "JEV_A461_G5_G2_STAGE_A_L1_TEST_MATRIX_V3",
                                       "policy": "research_governance/JEV_L1_L2_L3_GATE_MATRIX_V1.json",
                                       "pilot_task": "A461_G5_G2_K4B_STAGE_A_SCREEN_RUNNER_V1",
                                       "groups": groups, "tests": MATRIX, "all_pass": all_ok})
    receipt = {"schema": "JEV_A461_G5_G2_K4B_SELFTEST_RECEIPT_V1",
               "status": "COMPLETE_A461_G5_G2_STAGE_A_L1_TESTS" if all_ok else "L1_FAILURES_PRESENT",
               "tests": len(MATRIX), "passed": sum(1 for m in MATRIX if m["verdict"] == "PASS"),
               "runner_blob": runner_blob, "fake_model_blob": git(repo, "hash-object", str(FAKE)).strip(),
               "test_suite_blob": git(repo, "hash-object", str(Path(__file__).resolve())).strip(),
               "manifest_blob": MANIFEST_BLOB, "roster_blob": ROSTER_BLOB,
               "model_identity_sha256": runner.identity_digest(runner.MODEL_IDENTITY),
               "tested_command": "python3 A461_g5_g2_k4b_l1_tests_v1.py --repo-root <jev checkout> --out <~/wjc/...>",
               "runner_invocations": EVIDENCE,
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
