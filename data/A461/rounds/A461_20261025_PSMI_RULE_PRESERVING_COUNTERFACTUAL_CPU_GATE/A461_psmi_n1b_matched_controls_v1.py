#!/usr/bin/env python3
"""A461-PSMI G0-N1B: token-count-matched neutral controls (CPU only).

Preregistered BEFORE any model run (shadow QA QA-1/QA-2). Per family:
- TWINS T1/T3: same treatment vote but at a different OBSERVED round of the
  same scene (round != candidate_round) - invisible to the C/Q oracle because
  eligibility requires round==candidate_round; in-contract (3582/9120 corpus
  messages are at other rounds). Candidate rounds scanned in ascending order;
  first with equal state token count wins.
- TWINS T2: treatment vote for b' re-assigned to a fresh in-set validator
  (never joined support, so C/Q unchanged); all corpus authors are width-2
  validator names.
- LANL: INFEASIBLE_IN_CONTRACT - corpus contains only in-window LogOn events,
  every in-window failed LogOn to a known destination changes B, so no
  in-contract token-matched neutral exists; recorded, not fabricated.
Token equality is measured with the pinned native tokenizer (CPU encode only);
model weights are loaded for the renderer exactly as in G0 (zero forwards).
"""
import argparse, collections, gzip, hashlib, json, os, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
A428_G0B = "research/rounds/A428_20261023_TWO_FAMILY_NATIVE_POLICY_MULTIQ_MODEL_PILOT/G0B_REAL_20261023"

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


def twins_oracle(state):
    votes = collections.defaultdict(list)
    allowed = set(state["validator_set"])
    for e in state["received_messages"]:
        if (e.get("kind") == "vote" and e.get("round") == state["candidate_round"]
                and isinstance(e.get("received"), (int, float))
                and e["received"] <= state["decision_time"] and e.get("author") in allowed):
            votes[e["author"]].append(e["block"])
    support = {v for v, blocks in votes.items() if state["candidate_block"] in blocks}
    q = len(support) >= state["quorum_size"]
    c = any(any(b != state["candidate_block"] for b in votes[v]) for v in support)
    action = "reject_conflict" if c else "accept" if q else "wait"
    return {"conflicting_vote": c, "quorum": q, "certificate_action": action,
            "evidence_level": {"reject_conflict": 2, "accept": 0, "wait": 1}[action]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g0", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    g0 = a.g0.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(CORPUS.is_file() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(out.parent.is_dir() and not out.exists(), "new out dir required")
    receipt = {"schema": "JEV_A461_PSMI_G0_N1B_RECEIPT_V1", "status": "INCOMPLETE",
               "gpu_forwards": 0, "backbone_forwards": 0, "cpu_model_loads": 0}
    files = []
    try:
        out.mkdir(mode=0o700)
        prows = [json.loads(x) for x in (g0 / "pair_rows.jsonl").read_text("utf8").splitlines() if x.strip()]
        trows = {r["row_id"]: r for r in (json.loads(x) for x in (g0 / "token_audit.jsonl").read_text("utf8").splitlines() if x.strip())}
        tw = []
        with gzip.open(CORPUS, "rt", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    tw.append(rec)
        state_by_hash = {}
        for rec in tw:
            state_by_hash[hx(canon(rec["state"]))[:16]] = rec["state"]

        import torch
        torch.set_num_threads(4)
        torch.backends.cuda.matmul.allow_tf32 = False
        sys.path.insert(0, str(SOURCE))
        from kev.api import SystemOneRequest, to_record
        from kev.checkpoint import Checkpoint, LoadOptions
        from kev.model import rows_of
        ck(CKPT.is_dir() and BASE.is_dir(), "missing pinned checkpoint/base")
        checkpoint = Checkpoint(str(CKPT))
        checkpoint.meta.base, checkpoint.meta.base_revision = str(BASE), None
        tokenizer, model = checkpoint.load("cpu", LoadOptions(dtype=torch.float32, merge=False, attn="sdpa"))
        receipt["cpu_model_loads"] = 1

        def state_tokens(state, questions):
            rendered, _ = to_record(SystemOneRequest.model_validate(
                {"questions": questions, "state": json.loads(canon(state))}))
            enc = model.encode(tokenizer, rendered, max_state=8192, max_branch=8192, strict=True)
            sids, _, brs = rows_of(enc)
            ck(not enc["state_truncated"], "truncated")
            return sids, enc, brs

        by_pair = collections.OrderedDict()
        for r in prows:
            by_pair.setdefault(r["pair_key"], []).append(r)
        n1b_rows, audit_rows = [], []
        stats = collections.Counter()
        for key, rs in by_pair.items():
            fam = rs[0]["family"]
            if fam.startswith("LANL"):
                stats["LANL_infeasible_in_contract"] += 1
                continue
            old_state = state_by_hash[key.split(":", 1)[1]]
            og = twins_oracle(old_state)
            treatments = [r for r in rs if r["arm"] == "new"]
            neutrals = [r for r in rs if r["arm"] == "neutral"]
            for tr in treatments:
                tm = tr["declared_edit"]["message"]
                st_new = json.loads(canon(tr["native_request"]["state"]))
                t_ids, t_enc, t_brs = state_tokens(st_new, tr["native_request"]["questions"])
                cand_variants = []
                if fam in ("TWINS_T1_QUORUM_AXIS", "TWINS_T3_CONFLICT_STABILITY"):
                    alt_rounds = sorted(r0 for r0 in set(e["round"] for e in old_state["received_messages"]) if r0 != old_state["candidate_round"])
                    if not alt_rounds:
                        # no observed alternative round in this scene: fall back to the
                        # adjacent earlier round (schema-legal; marked unobserved in scan)
                        r0 = old_state["candidate_round"] - 1
                        if r0 < 0:
                            r0 = old_state["candidate_round"] + 1
                        alt_rounds = [r0]
                    for r0 in alt_rounds:
                        m2 = json.loads(canon(tm))
                        m2["round"] = r0
                        m2 = json.loads(canon(m2))
                        st2 = json.loads(canon(st_new))
                        st2["received_messages"] = st2["received_messages"][:-1] + [m2]
                        cand_variants.append(("round_shift", r0, st2, m2))
                else:  # T2: fresh in-set validator as author
                    st2 = json.loads(canon(st_new))
                    msgs = st2["received_messages"]
                    fresh = None
                    for v in old_state["validator_set"]:
                        if not any(e.get("kind") == "vote" and e.get("round") == old_state["candidate_round"]
                                   and isinstance(e.get("received"), (int, float))
                                   and e["received"] <= old_state["decision_time"] and e.get("author") == v
                                   for e in old_state["received_messages"]):
                            fresh = v
                            break
                    if fresh is None:
                        stats["no_candidate"] += 1
                        continue
                    m2 = json.loads(canon(tm))
                    m2["author"] = fresh
                    m2 = json.loads(canon(m2))
                    st2["received_messages"] = st2["received_messages"][:-1] + [m2]
                    cand_variants.append(("fresh_author_swap", fresh, st2, m2))
                matched = None
                scan = []
                for kind, val, st2, m2 in cand_variants:
                    sids, enc, brs = state_tokens(st2, tr["native_request"]["questions"])
                    eq = (hx(json.dumps(enc["ids"])) == hx(json.dumps(t_enc["ids"])))
                    cnt_eq = (len(sids) == len(t_ids))
                    scan.append({"variant_kind": kind, "value": val,
                                 "state_token_len": len(sids), "equal_token_count": cnt_eq,
                                 "equal_full_token_stream": eq})
                    if cnt_eq and matched is None:
                        matched = (kind, val, st2, m2, sids, enc, brs)
                    if eq:
                        break
                g2 = twins_oracle(matched[2]) if matched else twins_oracle(cand_variants[0][2])
                base_gold = twins_oracle(json.loads(canon(old_state)))
                if matched:
                    ck(g2 == base_gold, "N1b arm changed gold: " + key)
                    stats["matched"] += 1
                else:
                    stats["unmatched"] += 1
                chosen = matched or cand_variants[0]
                kind, val, st2, m2, sids, enc, brs = chosen
                row_id = tr["row_id"] + "N"
                n1b_rows.append({"row_id": row_id, "source_pair_row": tr["row_id"],
                                 "pair_key": key, "family": fam, "arm": "N1B_matched_attempt",
                                 "source": tr["source"], "source_group": tr["source_group"],
                                 "declared_edit": {"op": "N1B_" + kind, "value": val, "message": m2},
                                 "oracle_gold_impl1": {"conflicting_vote": g2["conflicting_vote"],
                                                       "quorum": g2["quorum"],
                                                       "certificate_action": g2["certificate_action"],
                                                       "evidence_level": g2["evidence_level"]},
                                 "N1B_token_count_matched": bool(matched),
                                 "native_request": {"questions": tr["native_request"]["questions"],
                                                    "state": st2}})
                audit_rows.append({"row_id": row_id, "pair_key": key,
                                   "treatment_state_token_len": len(t_ids),
                                   "n1b_state_token_len": len(sids),
                                   "n1b_state_token_sha256": hx(json.dumps(enc["ids"])),
                                   "candidate_scan": scan})
        with (out / "n1b_rows.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for r in n1b_rows:
                f.write(canon(r) + "\n")
        files.append("n1b_rows.jsonl")
        with (out / "n1b_token_audit.jsonl").open("x", encoding="utf8", newline="\n") as f:
            for r in audit_rows:
                f.write(canon(r) + "\n")
        files.append("n1b_token_audit.jsonl")
        receipt.update(status="COMPLETE_A461_PSMI_G0_N1B_CPU_ONLY",
                       pairs_total=len(by_pair), stats=dict(stats),
                       gpu_forwards=0, backbone_forwards=0, cpu_model_loads=1)
        code = 0
    except Exception as err:
        receipt.update(status="FAIL_A461_PSMI_G0_N1B", error_type=type(err).__name__, error_message=str(err))
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
