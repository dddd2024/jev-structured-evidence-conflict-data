#!/usr/bin/env python3
"""A461-G5-G2 Stage-A GPU screen runner G0_V3 (donor discovery).

Executes the Option-A admission draft manifest (N=124 W31 candidates x 3 arms
= 372 primary forwards + 6 determinism replays = 378 physical calls in 3 batch
transactions of 128/128/122) exactly as frozen in
research/rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/
G2_STAGE_A_ADMISSION_DRAFT/ (manifest blob 01ca5390..., roster blob 1bc84bf5...).

V3 changes per the L2 review 277fdb7 (P0x2, P1x2) on top of V2 (b0b9f6ee):
  - P0-1 frozen GPU plan: the gpu backend (full run and --pre-model-gate-only)
    refuses any roster/manifest/questions blob, expect-total or expect-batches
    other than the pinned values; the admission must bind the same frozen
    inputs, batch plan [128,128,122] and model identity digest. In every mode
    each batch cap must be <= 128 (RUN_CAP). Overrides exist only for L1_FAKE.
  - P0-2 durable quota ledger: one append-only ledger per admission_id under
    ~/wjc, held under an exclusive flock for the whole attempt. Every physical
    call is RESERVED (fsync) before the model is invoked; physical calls seen
    by the pre-hook but not reserved are appended as unreserved_physical on
    failure. Consumed quota = ledger, never a caller-supplied number (a stale
    caller value is refused). Before any attempt the ledger is reconciled
    against every run dir of this admission (attempt_manifest.json): an
    unknown run dir (ledger lost/stale), a missing ledgered dir, or more saved
    rows than reservations fails closed.
  - P1-1 model identity: per-file SHA-256 digests of the checkpoint dir, the
    base model/tokenizer dir and the kev source are pinned and verified before
    any model load (gpu backend), and persisted in the receipt.
  - P1-2 --pre-model-gate-only: runs every gpu admission, pin, identity, ledger
    and token gate, then exits before torch import / model load (L1-testable).

HARD ADMISSION GATE: gpu backend requires mode GPU, blind_review_verdict ==
"PASS" pinned to this runner blob AND fresh explicit user approval for exactly
378 calls / 3 batches [128,128,122]; fake backend requires mode L1_FAKE. Zero
backprop, zero network, outputs only under ~/wjc.
"""
import argparse, collections, fcntl, gzip, hashlib, json, math, os, re, subprocess, sys, time, uuid
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
WORK = ROOT / "a461-g5-minimal-patch-pilot-20261025-v1"
GPU_RUNS_ROOT = WORK / "G2_STAGE_A_GPU_RUNS"
GPU_QUOTA_ROOT = WORK / "G2_STAGE_A_QUOTA_LEDGER"

BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_MANIFEST = "01ca53908cc73276d4f6821a4892f05e47e02a15"
BLOB_G5V2_PAIRS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
STAGE = "A461_G5_G2_STAGE_A_DONOR_DISCOVERY_GPU"
FROZEN_WIDTH = 31
FROZEN_TOTAL = 378
FROZEN_BATCHES = [128, 128, 122]
RUN_CAP = 128
INHERITED_FIELDS = ("token_ids_sha256", "state_token_len", "frozen_width", "cell", "source_group")
# per-root digest = sha256(canon({relative path: file sha256})) over the files
# selected by identity_files(); frozen on the server 2026-10-27
MODEL_IDENTITY = {
    "ckpt": {"files": 28, "sha256": "fb8b042db5a986a88e8e0fc25e50bce6117f449c7211e8c176d789c7afd99295"},
    "base": {"files": 8, "sha256": "3a2fb1ffd126a3b12ddff5a80446feebb270a15a41a7ba67c92f1fd1879ca5e2"},
    "source": {"files": 26, "sha256": "99fcc711569f09be74c8f811eefcd8698efa2bd4ba319cc53251354d054d8bf6"},
}


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def inside(p, root):
    """Directory relation (Path.is_relative_to is 3.9+; server runs 3.8)."""
    try:
        Path(p).relative_to(root)
        return True
    except ValueError:
        return False


def sha_file(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def hids(v):
    return hashlib.sha256(json.dumps(v, ensure_ascii=False).encode("utf8")).hexdigest()


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def git_blob(repo, sha):
    t = subprocess.run(["git", "-C", str(repo), "cat-file", "-t", sha], capture_output=True, text=True)
    ck(t.returncode == 0 and t.stdout.strip() == "blob", f"not a blob: {sha}")
    return subprocess.run(["git", "-C", str(repo), "cat-file", "blob", sha],
                          capture_output=True, text=True, check=True).stdout


def canon_state(state):
    return json.loads(canon(state))


def write_new(p, v):
    with Path(p).open("x", encoding="utf8", newline="\n") as f:
        json.dump(v, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")


def append_line(p, v, sync=False):
    with Path(p).open("a", encoding="utf8", newline="\n") as f:
        f.write(canon(v) + "\n")
        if sync:
            f.flush()
            os.fsync(f.fileno())


def jsonl(p):
    p = Path(p)
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


# ---------------- model identity (P1-1) ----------------

def identity_files(name):
    if name == "ckpt":
        root, files = CKPT, [p for p in CKPT.rglob("*") if p.is_file()]
    elif name == "base":
        root, files = BASE, [p for p in BASE.rglob("*") if p.is_file()]
    else:
        root = SOURCE
        files = [p for p in (SOURCE / "kev").rglob("*.py") if "__pycache__" not in p.parts]
        files += [SOURCE / "pyproject.toml", SOURCE / "uv.lock"]
    return root, sorted(files)


def model_identity():
    out = {}
    for name in ("ckpt", "base", "source"):
        root, files = identity_files(name)
        fmap = {str(p.relative_to(root)): sha_file(p) for p in files}
        out[name] = {"files": len(fmap), "sha256": hashlib.sha256(canon(fmap).encode("utf8")).hexdigest()}
    return out


def identity_digest(ident):
    return hashlib.sha256(canon(ident).encode("utf8")).hexdigest()


def verify_identity(observed, expected):
    for name in ("ckpt", "base", "source"):
        ck(observed.get(name) == expected.get(name),
           f"model identity mismatch for {name}: observed {observed.get(name)} != pinned {expected.get(name)}")


# ---------------- manifest (P0-1 of review 3c4721da, P0-1 of 277fdb7) ----------------

def effective_entries(manifest):
    """Pure function: return the entries with replays replaced by EFFECTIVE
    entries that inherit token_ids_sha256 / state_token_len / frozen_width /
    cell / source_group from their referenced primary row. Raises if any
    replay reference is invalid, any inherited field is missing, or a field
    the replay already carries disagrees with its primary."""
    by_index = {e["forward_index"]: e for e in manifest}
    ck(len(by_index) == len(manifest), "duplicate forward_index")
    out = []
    for e in manifest:
        if e["kind"] == "primary":
            ck(all(k in e for k in INHERITED_FIELDS), f"primary {e['forward_index']} missing fields")
            out.append(dict(e))
            continue
        ck(e["kind"] == "replay", f"unknown kind at {e['forward_index']}")
        ref = by_index.get(e.get("replay_of_forward_index"))
        ck(ref is not None and ref["kind"] == "primary" and ref["arm"] == "old"
           and ref["run"] == e["run"] and ref["forward_index"] < e["forward_index"],
           f"replay {e['forward_index']} reference invalid")
        ck(e.get("scene_sha256") == ref["scene_sha256"] and e.get("arm", "old") == "old",
           f"replay {e['forward_index']} scene/arm != referenced primary")
        eff = dict(e)
        for k in INHERITED_FIELDS:
            ck(k in ref, f"replay {e['forward_index']}: referenced primary lacks {k}")
            ck(k not in e or e[k] == ref[k], f"replay {e['forward_index']}: {k} disagrees with primary")
            eff[k] = ref[k]
        out.append(eff)
    return out


def batch_guard(batch_physical, batch_planned):
    """Pure guard: raise BEFORE the model is invoked when the next call of a
    batch would exceed that batch's frozen physical cap (never above RUN_CAP)."""
    ck(batch_physical < min(batch_planned, RUN_CAP),
       f"batch physical cap: call {batch_physical + 1} of {min(batch_planned, RUN_CAP)} refused before model")


def batch_plan(manifest, expect_batches):
    """Frozen per-run caps (run k -> expect_batches[k-1], each <= RUN_CAP); the
    manifest must match them run by run and be contiguous in run order."""
    ck(all(0 < n <= RUN_CAP for n in expect_batches), f"batch plan {expect_batches} exceeds cap {RUN_CAP}")
    caps = {k + 1: n for k, n in enumerate(expect_batches)}
    counts = collections.Counter(m["run"] for m in manifest)
    ck(dict(counts) == caps, f"run sizes {dict(counts)} != frozen plan {caps}")
    runs = [m["run"] for m in manifest]
    ck(runs == sorted(runs), "manifest runs not contiguous")
    ck([m["forward_index"] for m in manifest] == list(range(1, len(manifest) + 1)), "forward_index not 1..N")
    return caps


def gpu_pin_gate(a, admit, self_blob):
    """P0-1: the gpu backend runs only the reviewed plan on the reviewed inputs."""
    pins = {"roster_blob": BLOB_ROSTER, "manifest_blob": BLOB_MANIFEST,
            "g5v2_questions_blob": BLOB_G5V2_PAIRS, "corpus_sha256": CORPUS_SHA}
    given = {"roster_blob": a.roster_blob, "manifest_blob": a.manifest_blob,
             "g5v2_questions_blob": a.g5v2_questions_blob, "corpus_sha256": CORPUS_SHA}
    ck(given == pins, "gpu backend: input blob override refused (frozen roster/manifest/questions only)")
    ck(a.expect_total == FROZEN_TOTAL and [int(x) for x in a.expect_batches.split(",")] == FROZEN_BATCHES,
       "gpu backend: plan override refused (frozen 378 = 128,128,122 only)")
    ck(a.quota_root is None, "gpu backend: quota root is fixed")
    ck(admit.get("mode") == "GPU", "gpu backend requires admission mode GPU")
    ck(admit.get("frozen_inputs") == pins, "admission frozen_inputs != pinned inputs")
    ck(admit.get("approved_batch_plan") == FROZEN_BATCHES, "admission batch plan != [128,128,122]")
    ck(admit.get("approved_max_native_forwards") == FROZEN_TOTAL and admit.get("approved_batches") == 3,
       "gpu approval must be exactly the frozen 378 calls / 3 batches")
    ck(admit.get("model_identity_sha256") == identity_digest(MODEL_IDENTITY),
       "admission model_identity_sha256 != pinned model identity")
    ck(admit.get("blind_review_verdict") == "PASS", "runner code review has not PASSed")
    ck(admit.get("blind_review_runner_blob") == self_blob, "runner blob != reviewed blob")
    ck(admit.get("explicit_user_gpu_approval") is True, "no explicit user GPU approval")


# ---------------- durable quota ledger (P0-2) ----------------

def ledger_consumed(events, attempt_id=None):
    sel = [e for e in events if attempt_id is None or e.get("attempt_id") == attempt_id]
    return (sum(1 for e in sel if e["event"] == "reserve")
            + sum(int(e["count"]) for e in sel if e["event"] == "unreserved_physical"))


def reconcile_ledger(events, runs_root, admission_id):
    """Fail closed unless every run dir of this admission is ledgered, every
    ledgered dir exists, and no dir holds more call evidence than its
    reservations. Returns (consumed, per-attempt summary)."""
    opened = {e["attempt_id"]: e["out_dir"] for e in events if e["event"] == "attempt_open"}
    on_disk = {}
    if Path(runs_root).is_dir():
        for m in sorted(Path(runs_root).glob("*/attempt_manifest.json")):
            am = json.loads(m.read_text("utf8"))
            if am.get("admission_id") == admission_id:
                on_disk[am["attempt_id"]] = str(m.parent)
    unknown = sorted(set(on_disk) - set(opened))
    ck(not unknown, f"quota ledger stale or missing: {len(unknown)} run dir(s) of this admission not in ledger")
    summary = {}
    for aid, od in opened.items():
        ck(Path(od).is_dir(), f"ledgered attempt dir missing ({od}): prior spend ambiguous")
        spent = ledger_consumed(events, aid)
        evidence = len(jsonl(Path(od) / "raw_native_logits_stage_a.jsonl")) + len(jsonl(Path(od) / "attempt_receipts.jsonl"))
        ck(evidence <= spent, f"attempt {aid}: {evidence} saved call rows > {spent} ledgered calls")
        rp = Path(od) / "execution_receipt.json"
        closed = any(e["event"] == "attempt_close" and e["attempt_id"] == aid for e in events)
        if rp.exists():
            ck(json.loads(rp.read_text("utf8")).get("physical_prehook_calls", 0) <= spent,
               f"attempt {aid}: receipt physical > ledgered calls")
        summary[aid] = {"out_dir": od, "ledgered_calls": spent, "saved_call_rows": evidence,
                        "receipt": rp.exists(), "closed": closed}
    return ledger_consumed(events), summary


class QuotaLedger:
    """Exclusive, append-only, fsync'd ledger for one admission_id."""

    def __init__(self, quota_root, admission_id, runs_root, write):
        self.dir = Path(quota_root) / admission_id
        self.path = self.dir / "ledger.jsonl"
        self.runs_root = runs_root
        self.admission_id = admission_id
        self.fd = None
        if write:
            self.dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            self.fd = os.open(str(self.dir / ".lock"), os.O_RDWR | os.O_CREAT, 0o600)
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(self.fd)
                self.fd = None
                raise RuntimeError("quota ledger locked by another attempt of this admission")

    def state(self):
        events = jsonl(self.path)
        consumed, summary = reconcile_ledger(events, self.runs_root, self.admission_id)
        return events, consumed, summary

    def append(self, ev):
        ck(self.fd is not None, "ledger not held")
        append_line(self.path, dict(ev, admission_id=self.admission_id, t=round(time.time(), 3)), sync=True)

    def release(self):
        if self.fd is not None:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            os.close(self.fd)
            self.fd = None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--admission", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--backend", choices=["gpu", "fake"], default="gpu")
    ap.add_argument("--roster-blob", default=BLOB_ROSTER)
    ap.add_argument("--manifest-blob", default=BLOB_MANIFEST)
    ap.add_argument("--g5v2-questions-blob", default=BLOB_G5V2_PAIRS)
    ap.add_argument("--expect-total", type=int, default=FROZEN_TOTAL)
    ap.add_argument("--expect-batches", default=",".join(map(str, FROZEN_BATCHES)),
                    help="physical cap per batch, run k -> k-th value; gpu backend: frozen only")
    ap.add_argument("--quota-root", type=Path, default=None,
                    help="L1_FAKE only: quota ledger root (gpu uses the fixed ledger root)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--preflight-only", action="store_true",
                      help="CPU input gates only (blob pins, manifest re-verification, token gate, dry-run)")
    mode.add_argument("--pre-model-gate-only", action="store_true",
                      help="every admission/pin/identity/ledger/token gate of a real run, then exit before "
                           "torch import and model load (read-only ledger)")
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(inside(out, ROOT), "out dir: output must be inside ~/wjc (directory relation)")
    ck(out.parent.is_dir() and not out.exists(), "out dir: parent missing or out exists")
    full_run = not (a.preflight_only or a.pre_model_gate_only)
    if a.backend == "gpu" and full_run:
        ck(out.parent == GPU_RUNS_ROOT.resolve(), "gpu run out dir must be a direct child of G2_STAGE_A_GPU_RUNS")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    expect_batches = [int(x) for x in a.expect_batches.split(",")]
    ck(sum(expect_batches) == a.expect_total, "expect-batches do not sum to expect-total")
    receipt = {"schema": "JEV_A461_G5_G2_STAGE_A_SCREEN_RECEIPT_V3", "status": "INCOMPLETE",
               "run_id": "A461_G5_G2_STAGE_A_DONOR_DISCOVERY_GPU_R1",
               "backend": a.backend, "expect_total": a.expect_total, "expect_batches": expect_batches,
               "gpu_model_loads": 0, "model_loads": 0, "native_model_forward_calls": 0,
               "physical_prehook_calls": 0, "backprop_calls": 0,
               "network_calls": 0, "tool_actions": 0, "test_or_calibration_rows": 0,
               "batch_receipts": [], "output_dir": str(out),
               "frozen_inputs": {"roster_blob": a.roster_blob, "manifest_blob": a.manifest_blob,
                                 "g5v2_questions_blob": a.g5v2_questions_blob, "corpus_sha256": CORPUS_SHA}}
    produced = []
    raw_log = out / "raw_native_logits_stage_a.jsonl"
    attempt_log = out / "attempt_receipts.jsonl"
    physical = [0]
    physical_by_batch = {}
    current = [None]
    reserved = [0]
    model = None
    ledger = None
    attempt_id = uuid.uuid4().hex
    try:
        out.mkdir(mode=0o700)
        sys.path.insert(0, str(SOURCE))

        # ---------- hard admission shape (no model objects touched yet) ----------
        admit = json.loads(a.admission.read_text("utf8"))
        self_blob = subprocess.run(["git", "-C", str(repo), "hash-object", str(Path(__file__).resolve())],
                                   capture_output=True, text=True, check=True).stdout.strip()
        receipt["runner_blob"] = self_blob
        ck(admit.get("stage") == STAGE, "wrong admission stage")
        ck(admit.get("approved_batches") == len(expect_batches), "approved batches != expected")
        approved_max = int(admit.get("approved_max_native_forwards", 0))
        ck(a.expect_total <= approved_max, "cumulative overrun: plan exceeds the approved total")
        receipt["admission_fields_observed"] = {k: admit.get(k) for k in (
            "admission_id", "mode", "blind_review_verdict", "explicit_user_gpu_approval",
            "blind_review_runner_blob", "approved_max_native_forwards", "approved_batch_plan",
            "model_identity_sha256", "cumulative_calls_already_consumed")}
        receipt["admission_fields_observed"]["self_blob"] = self_blob
        if a.backend == "fake":
            ck(admit.get("mode") == "L1_FAKE", "fake backend requires admission mode L1_FAKE")
        elif not a.preflight_only:
            gpu_pin_gate(a, admit, self_blob)

        # ---------- model identity (gpu, before any load) ----------
        if a.backend == "gpu" and not a.preflight_only:
            ident = model_identity()
            receipt["model_identity"] = ident
            verify_identity(ident, MODEL_IDENTITY)
            receipt["model_identity_verified"] = True

        # ---------- durable quota ledger ----------
        if not a.preflight_only:
            admission_id = admit.get("admission_id")
            ck(isinstance(admission_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{8,80}", admission_id),
               "admission_id missing or malformed")
            if a.backend == "gpu":
                qroot, runs_root = GPU_QUOTA_ROOT, GPU_RUNS_ROOT
            else:
                ck(a.quota_root is not None, "fake backend run needs --quota-root")
                qroot, runs_root = a.quota_root.expanduser().resolve(strict=False), out.parent
                ck(inside(qroot, ROOT) and qroot != GPU_QUOTA_ROOT.resolve(), "fake quota root")
            receipt["quota_ledger"] = {"path": str(Path(qroot) / admission_id / "ledger.jsonl"),
                                       "attempt_id": attempt_id}
            ledger = QuotaLedger(qroot, admission_id, runs_root, write=full_run)
            _events, consumed, summary = ledger.state()
            receipt["quota_ledger"].update(consumed_before=consumed, prior_attempts=summary)
            if "cumulative_calls_already_consumed" in admit:
                ck(int(admit["cumulative_calls_already_consumed"]) == consumed,
                   f"stale caller-supplied consumed {admit['cumulative_calls_already_consumed']} != ledger {consumed}")
            ck(consumed + a.expect_total <= approved_max,
               f"cumulative overrun: ledger consumed {consumed} + plan {a.expect_total} > approved {approved_max}")

        # ---------- frozen inputs ----------
        roster_doc = json.loads(git_blob(repo, a.roster_blob))
        ck(roster_doc["schema"] == "JEV_A461_G5_G2_STAGE_A_CANDIDATE_ROSTER_V3", "roster schema")
        by_sha = {r["scene_sha256"]: r for r in roster_doc["candidates"]}
        manifest = [json.loads(x) for x in git_blob(repo, a.manifest_blob).splitlines() if x.strip()]
        ck(len(manifest) == a.expect_total, f"manifest {len(manifest)} != expected {a.expect_total}")
        caps = batch_plan(manifest, expect_batches)
        prows = [json.loads(x) for x in git_blob(repo, a.g5v2_questions_blob).splitlines() if x.strip()]
        q_tw = prows[0]["native_request"]["questions"]

        state_by = {}
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    ck(rec["_meta"].get("split") == "development", "non-DEV")
                    state_by[hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()] = rec["state"]
        ck(all(m["scene_sha256"] in state_by for m in manifest), "manifest scenes missing from corpus")

        eff = effective_entries(manifest)
        primary = [e for e in eff if e["kind"] == "primary"]
        n_replay = len(eff) - len(primary)

        # manifest-vs-roster per-row tuple re-check for every primary
        for e in primary:
            r = by_sha.get(e["scene_sha256"])
            ck(r is not None, f"primary {e['forward_index']} scene not in roster")
            want = (r["token_ids_sha256"][e["arm"]], r["state_token_len"][e["arm"]], r["frozen_width"],
                    r["cell"], r["source_group"])
            got = tuple(e[k] for k in INHERITED_FIELDS)
            ck(got == want, f"manifest row {e['forward_index']} tuple != roster")
            ck(e["frozen_width"] == FROZEN_WIDTH, "slice is W31 tier")
        arms = collections.Counter((e["scene_sha256"], e["arm"]) for e in primary)
        ck(all(v == 1 for v in arms.values()) and set(a_ for _, a_ in arms) == {"old", "new", "SA"},
           "each scene x arm exactly once")

        # ---------- tokenizer + per-row token gate (all primary rows) ----------
        from transformers import AutoTokenizer
        from kev.api import SystemOneRequest, to_record
        from kev.model import encode
        tok = AutoTokenizer.from_pretrained(str(BASE))
        receipt["tokenizer_source"] = str(BASE)
        receipt["base_tokenizer_json_sha256"] = sha_file(BASE / "tokenizer.json")

        def encode_state(state):
            rendered, meta = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": canon_state(state)}))
            enc = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
            ck(not enc["state_truncated"], "truncated state")
            return enc, meta

        reqs = {}
        for scene_sha in sorted({e["scene_sha256"] for e in primary}):
            r = by_sha[scene_sha]
            st_old = state_by[scene_sha]
            st_new = json.loads(canon(st_old))
            st_new["received_messages"].append(dict(r["declared_edit_new"]["message"]))
            st_sa = json.loads(canon(st_old))
            st_sa["received_messages"].append(dict(r["declared_edit_sa"]["message"]))
            states = {"old": st_old, "new": st_new, "SA": st_sa}
            for arm in ("old", "new", "SA"):
                enc, _meta = encode_state(states[arm])
                ck(hids(enc["ids"]) == r["token_ids_sha256"][arm], f"token gate mismatch {scene_sha[:8]}:{arm}")
                ck(len(enc["ids"][:enc["seg"].count(0)]) == r["state_token_len"][arm],
                   f"state length mismatch {scene_sha[:8]}:{arm}")
                reqs[(scene_sha, arm)] = {"questions": q_tw, "state": states[arm]}
        ck(len(reqs) == len(primary), "derived requests")

        dry = collections.Counter((e["run"], e["kind"]) for e in eff)
        receipt["ledger_dry_run"] = {f"run{k}": {"primary": dry[(k, "primary")], "replay": dry[(k, "replay")],
                                                 "total": dry[(k, "primary")] + dry[(k, "replay")], "cap": caps[k]}
                                     for k in sorted(caps)}

        if not full_run:
            receipt.update(status=("COMPLETE_A461_G5_G2_STAGE_A_PRE_MODEL_GATE" if a.pre_model_gate_only
                                   else "COMPLETE_A461_G5_G2_STAGE_A_PREFLIGHT"),
                           manifest_rows=len(manifest), primary_rows=len(primary), replay_rows=n_replay,
                           token_gate=f"{len(primary)}/{len(primary)} PASS",
                           manifest_roster_tuple_gate=f"{len(primary)}/{len(primary)} PASS",
                           runs={str(k): v for k, v in sorted(caps.items())},
                           note="all gates before torch import / model load; not a GPU run and not an admission")
            raise SystemExit(0)

        # ---------- attempt open (ledgered before any model object exists) ----------
        ledger.append({"event": "attempt_open", "attempt_id": attempt_id, "out_dir": str(out),
                       "runner_blob": self_blob, "backend": a.backend, "plan": expect_batches})
        write_new(out / "attempt_manifest.json", {"admission_id": admission_id, "attempt_id": attempt_id,
                                                  "runner_blob": self_blob, "backend": a.backend})
        produced.append("attempt_manifest.json")
        consumed_total = [consumed]

        # ---------- backend ----------
        if a.backend == "fake":
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from A461_g5_g2_fake_kev_model_v1 import FakeModel
            model = FakeModel()
            receipt["fake_model_fault"] = model.fault
        else:
            import torch
            torch.set_num_threads(4)
            torch.backends.cuda.matmul.allow_tf32 = False
            torch.backends.cudnn.allow_tf32 = False
            torch.backends.cuda.enable_flash_sdp(False)
            torch.backends.cuda.enable_mem_efficient_sdp(False)
            from kev.checkpoint import Checkpoint, LoadOptions
            checkpoint = Checkpoint(str(CKPT))
            checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
            tokenizer, model = checkpoint.load("cuda:0", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
            receipt["gpu_model_loads"] = 1
        receipt["model_loads"] = 1
        model.eval()
        model.requires_grad_(False)
        ck(model.hybrid, "expected hybrid backbone (row-form forwards)")

        def bump(_m, _a):
            physical[0] += 1
            physical_by_batch[current[0]] = physical_by_batch.get(current[0], 0) + 1
        hk = model.lm.register_forward_pre_hook(bump)

        def run_forward(req, entry):
            """One physical forward for one EFFECTIVE entry. All contract checks
            run and the call is reserved in the durable ledger before the model;
            valid logits are appended to the raw log before any post-forward
            gate; failures write an attempt row."""
            b = entry["run"]
            ck(current[0] == b, "entry outside the open batch transaction")
            ck(receipt["native_model_forward_calls"] + 1 == entry["forward_index"],
               f"manifest order deviation at call {receipt['native_model_forward_calls'] + 1}")
            batch_guard(physical_by_batch.get(b, 0), caps[b])
            ck(physical[0] == receipt["native_model_forward_calls"] == reserved[0],
               f"physical pre-hook {physical[0]} != recorded/reserved calls {reserved[0]}")
            ck(consumed_total[0] + 1 <= approved_max,
               "global budget: ledger consumed + this call exceeds approved_max")
            enc, meta = encode_state(req["state"])
            ck(hids(enc["ids"]) == entry["token_ids_sha256"], "encode != frozen witness")
            ck(len(enc["ids"][:enc["seg"].count(0)]) == entry["state_token_len"], "encode length != frozen witness")
            c_idx = [m["id"] for m in meta].index("conflicting_vote")
            att = {"forward_index": entry["forward_index"], "run": b, "kind": entry["kind"],
                   "scene_sha256": entry["scene_sha256"], "arm": entry["arm"]}
            ledger.append({"event": "reserve", "attempt_id": attempt_id, "forward_index": entry["forward_index"],
                           "run": b})
            reserved[0] += 1
            consumed_total[0] += 1
            try:
                z = model.forward(enc)
            except Exception as err:
                append_line(attempt_log, dict(att, status="FORWARD_FAILED", logits_saved=False,
                                              physical_prehook_after=physical[0],
                                              error_type=type(err).__name__, error_message=str(err)[:200]))
                raise
            receipt["native_model_forward_calls"] += 1
            try:
                ck(len(z) == len(meta) == 4, "branch count")
                raw = []
                for zz, m in zip(z, meta):
                    vals = zz if isinstance(zz, list) else zz.detach().float().cpu().tolist()
                    vals = [float(x) for x in vals]
                    ck(len(vals) == len(m["keys"]) and all(math.isfinite(x) for x in vals), "invalid logits")
                    raw.append(vals)
            except Exception as err:
                append_line(attempt_log, dict(att, status="INVALID_OUTPUT", logits_saved=False,
                                              physical_prehook_after=physical[0],
                                              error_type=type(err).__name__, error_message=str(err)[:200]))
                raise
            row = dict(att, frozen_width=entry["frozen_width"], cell=entry["cell"],
                       source_group=entry["source_group"],
                       replay_of_forward_index=entry.get("replay_of_forward_index"),
                       conflicting_vote_branch_index=c_idx,
                       questions=[{"id": m["id"], "keys": list(m["keys"]), "logits": v}
                                  for m, v in zip(meta, raw)],
                       token_ids_sha256=entry["token_ids_sha256"], state_token_len=entry["state_token_len"])
            append_line(raw_log, row)
            return row

        t0 = time.time()
        old_req_by_scene = {s: req for (s, arm), req in reqs.items() if arm == "old"}
        primary_rows_by_index = {}
        receipt["batch_receipts"] = [{"run": k, "planned": caps[k], "status": "NOT_STARTED", "physical": 0}
                                     for k in sorted(caps)]
        for br in receipt["batch_receipts"]:
            b = br["run"]
            current[0] = b
            physical_by_batch[b] = 0
            br["status"] = "IN_PROGRESS"
            rows_b = 0
            for entry in (e for e in eff if e["run"] == b):
                row = run_forward(old_req_by_scene[entry["scene_sha256"]] if entry["kind"] == "replay"
                                  else reqs[(entry["scene_sha256"], entry["arm"])], entry)
                rows_b += 1
                br["physical"] = physical_by_batch[b]
                if entry["kind"] == "replay":
                    ref_row = primary_rows_by_index[entry["replay_of_forward_index"]]
                    ck(all(x["logits"] == y["logits"] for x, y in zip(ref_row["questions"], row["questions"])),
                       f"replay not bitwise vs forward {entry['replay_of_forward_index']}")
                else:
                    primary_rows_by_index[entry["forward_index"]] = row
            ck(physical_by_batch[b] == caps[b] == rows_b, f"batch {b} physical != planned")
            br.update(status="COMPLETE", physical=physical_by_batch[b], rows=rows_b,
                      cumulative_physical_after=physical[0])
            write_new(out / f"batch_receipt_run{b}.json", dict(br, runner_blob=self_blob, attempt_id=attempt_id))
            produced.append(f"batch_receipt_run{b}.json")
            current[0] = None
        hk.remove()

        ck(physical[0] == receipt["native_model_forward_calls"] == reserved[0] == a.expect_total,
           f"ledger mismatch physical={physical[0]} reserved={reserved[0]}")
        n_raw = len(jsonl(raw_log))
        ck(n_raw == a.expect_total, "row count")
        produced.append("raw_native_logits_stage_a.jsonl")
        if attempt_log.exists():
            produced.append("attempt_receipts.jsonl")
        receipt.update(status="COMPLETE_A461_G5_G2_STAGE_A_SCREEN",
                       physical_forwards=physical[0], rows=n_raw, runs=sorted(caps),
                       elapsed_seconds=round(time.time() - t0, 3))
        code = 0
    except SystemExit as stop:
        code = int(stop.code or 0)
    except Exception as err:
        import traceback
        for n, p in (("raw_native_logits_stage_a.jsonl", raw_log), ("attempt_receipts.jsonl", attempt_log)):
            if p.exists() and n not in produced:
                produced.append(n)
        receipt["physical_prehook_count_at_failure"] = physical[0]
        receipt["physical_by_batch_at_failure"] = {str(k): v for k, v in physical_by_batch.items() if k}
        for br in receipt.get("batch_receipts", []):
            if br["status"] == "IN_PROGRESS":
                br["status"] = "FAILED_AT_THIS_BATCH"
                br["physical"] = physical_by_batch.get(br["run"], 0)
        receipt.update(status="FAIL_A461_G5_G2_STAGE_A_SCREEN", error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-2000:])
        code = 2
    if ledger is not None and ledger.fd is not None:
        if physical[0] > reserved[0]:
            # physical calls the pre-hook saw but no reservation covered: charge them
            ledger.append({"event": "unreserved_physical", "attempt_id": attempt_id,
                           "count": physical[0] - reserved[0]})
        if (out / "attempt_manifest.json").exists():
            ledger.append({"event": "attempt_close", "attempt_id": attempt_id, "status": receipt["status"],
                           "physical": physical[0], "reserved": reserved[0]})
        receipt.setdefault("quota_ledger", {})["consumed_after"] = ledger_consumed(jsonl(ledger.path))
        ledger.release()
    receipt["physical_prehook_calls"] = physical[0]
    receipt["ledger_reserved_calls"] = reserved[0]
    if model is not None and a.backend == "fake":
        receipt["fake_model_forward_invocations"] = len(model.forward_log)
    receipt["cuda_initialized"] = "torch" in sys.modules and bool(sys.modules["torch"].cuda.is_initialized())
    if not out.is_dir():
        print(canon(receipt))
        return code
    write_new(out / "execution_receipt.json", receipt)
    produced.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(canon(receipt))
    return code


if __name__ == "__main__":
    sys.exit(main())
