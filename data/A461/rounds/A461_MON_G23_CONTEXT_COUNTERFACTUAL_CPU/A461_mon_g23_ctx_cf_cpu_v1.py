#!/usr/bin/env python3
"""A461-MON-G2.3 CPU constructibility check (zero model loads, zero forwards; tokenizer only).

Answers V4 audit P0-1 (02a2b73): in M18 / M22 every positive is a `new` row and every negative a non-`new` row, so a
probe could separate arms rather than conflict validity. This checks whether, for the 124 M18 scenes, a context
counterfactual exists that keeps the appended `new` vote BYTE-IDENTICAL (same tokens, same positions) and changes only
the earlier "partner" vote(s) that make it an equivocation, so that Gold is no longer reject_conflict.

Families (each modifies only the appended author A's own support vote(s) for the candidate block in the candidate round):
  PARTNER_ROUND   round -> nearest non-candidate round      (A stops being a supporter; quorum may drop)
  PARTNER_AUTHOR  author -> a validator who is not a supporter (A stops being a supporter; quorum preserved)
  PARTNER_BLOCK   block  -> the appended vote's block        (A no longer supports the candidate; quorum may drop)
Gates: both oracles agree; Gold != reject_conflict; total token length equals the new arm's; the appended span's
token ids and position equal the new arm's; the branch segments are unchanged. Reported per scene, per source group,
and split by kev-4B's M18 native set (MISSED / RECOGNIZED) and SecJev's M22 set."""
import argparse, collections, gzip, hashlib, json, os, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
KEV_SRC = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
BLOB_G5V2_PAIRS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
FAMILIES = ("PARTNER_ROUND", "PARTNER_AUTHOR", "PARTNER_BLOCK")


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def act(qs):
    a = next(q for q in qs if q["id"] == "certificate_action")
    return a["keys"][max(range(len(a["keys"])), key=lambda i: a["logits"][i])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--helper", required=True, type=Path, help="A461_g5_g2_stage_a_cpu_freeze_v1.py")
    ap.add_argument("--blobs", required=True, type=Path)
    ap.add_argument("--m18-design", required=True, type=Path)
    ap.add_argument("--m18-raw", required=True, type=Path)
    ap.add_argument("--m22-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve(strict=False)
    ck(str(out).startswith(str(ROOT)) and out.parent.is_dir() and not out.exists(), "out dir")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1")
    import importlib.util
    spec = importlib.util.spec_from_file_location("stage_a", a.helper)
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    canon, hids, oracle1, oracle2 = sa.canon, sa.hids, sa.oracle1, sa.oracle2
    ck(sa.sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    pairs = (a.blobs / BLOB_G5V2_PAIRS).read_bytes()
    ck(hashlib.sha1(b"blob %d\0" % len(pairs) + pairs).hexdigest() == BLOB_G5V2_PAIRS, "pairs blob")
    q_tw = json.loads(pairs.decode("utf8").splitlines()[0])["native_request"]["questions"]
    D = json.loads(a.m18_design.read_text("utf8"))
    nat = {}
    for name, p in (("k4b", a.m18_raw), ("secjev", a.m22_raw)):
        for line in p.read_text("utf8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r["target_arm"] == "new":
                    nat[(name, r["target_scene"])] = act(r["questions"])
    receipt = {"schema": "JEV_A461_MON_G23_CTX_CF_CPU_V1", "gpu_forwards": 0, "model_loads": 0,
               "script_sha256": sa.sha_file(Path(__file__).resolve()), "helper_sha256": sa.sha_file(a.helper),
               "m18_design_sha256": sa.sha_file(a.m18_design), "corpus_sha256": CORPUS_SHA}

    sys.path.insert(0, str(KEV_SRC))
    from transformers import AutoTokenizer
    from kev.api import SystemOneRequest, to_record
    from kev.model import encode
    tok = AutoTokenizer.from_pretrained(str(BASE))

    def enc(state):
        rendered, _ = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
        e = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
        ck(not e["state_truncated"], "truncated")
        return e

    def gold(st):
        g1, sup = oracle1(st)
        return (g1 if g1 == oracle2(st) else None), sup

    scenes = {}
    for line in gzip.open(CORPUS, "rt", encoding="utf8"):
        if line.strip():
            rec = json.loads(line)
            if rec["_meta"].get("source") == "twins_streamlet":
                st = rec["state"]
                scenes[hashlib.sha256(canon(st).encode("utf8")).hexdigest()] = st

    rows = []
    for sh, sc in sorted(D["scenes"].items()):
        ck(sh in scenes, f"scene {sh[:12]}")
        st = scenes[sh]
        newm = sc["arms"]["new"]["message"]
        new_state = json.loads(canon(st))
        new_state["received_messages"].append(dict(newm))
        g_new, sup = gold(new_state)
        ck(g_new and g_new["certificate_action"] == "reject_conflict", "new gold")
        e_new = enc(new_state)
        ck(hids(e_new["ids"]) == sc["arms"]["new"]["token_ids_sha256"], f"new tokens {sh[:12]}")
        sp = sc["arms"]["new"]["span"]
        n_state = e_new["seg"].count(0)
        A, cr, cb = newm["author"], st["candidate_round"], st["candidate_block"]
        idx = [i for i, m in enumerate(st["received_messages"])
               if m.get("kind") == "vote" and m.get("author") == A and m.get("round") == cr and m.get("block") == cb]
        rounds_seen = {m.get("round") for m in st["received_messages"] if isinstance(m.get("round"), int)}
        round_vals = sorted((r for r in rounds_seen | {cr - 1, cr + 1, cr + 2} if r != cr and r >= 0),
                            key=lambda r: (abs(r - cr), r))
        others = sorted(set(st["validator_set"]) - set(sup))
        cands = {"PARTNER_ROUND": [("round", v) for v in round_vals],
                 "PARTNER_AUTHOR": [("author", v) for v in others],
                 "PARTNER_BLOCK": [("block", newm["block"])]}
        row = {"scene": sh[:12], "group": sc["group"],
               "partner_votes": len(idx), "k4b_new": nat.get(("k4b", sh)), "secjev_new": nat.get(("secjev", sh)),
               "old_gold": sc["arms"]["old"]["gold"]["certificate_action"]}
        for fam in FAMILIES:
            res = {"ok": False, "gold_ok_tried": 0}
            if idx:
                for field, v in cands[fam]:
                    s = json.loads(canon(new_state))
                    for i in idx:
                        s["received_messages"][i][field] = v
                    g, _ = gold(s)
                    if g is None or g["certificate_action"] == "reject_conflict" or g["conflicting_vote"]:
                        continue
                    res["gold_ok_tried"] += 1
                    e = enc(s)
                    ids, nids = e["ids"], e_new["ids"]
                    if (len(ids) != len(nids) or e["seg"].count(0) != n_state or ids[sp[0]:sp[1]] != nids[sp[0]:sp[1]]
                            or ids[n_state:] != nids[n_state:]):
                        continue
                    diff = [p for p in range(len(ids)) if ids[p] != nids[p]]
                    res = {"ok": True, "field": field, "value": v, "gold": g, "gold_eq_old": g["certificate_action"] == row["old_gold"],
                           "token_positions_changed": len(diff), "changed_before_span": all(p < sp[0] for p in diff),
                           "token_ids_sha256": hids(ids), "gold_ok_tried": res["gold_ok_tried"]}
                    break
            row[fam] = res
        rows.append(row)

    groups = sorted({r["group"] for r in rows})

    def cover(pred):
        sub = [r for r in rows if pred(r)]
        out_ = {"scenes": len(sub)}
        for fam in FAMILIES + ("ANY",):
            ok = [r for r in sub if (any(r[f]["ok"] for f in FAMILIES) if fam == "ANY" else r[fam]["ok"])]
            out_[fam] = {"scenes": len(ok), "groups": len({r["group"] for r in ok}), "groups_of": len({r["group"] for r in sub}),
                         "gold_eq_old": sum(1 for r in ok if fam != "ANY" and r[fam].get("gold_eq_old"))}
        return out_
    receipt["coverage"] = {"all": cover(lambda r: True),
                           "k4b_MISSED": cover(lambda r: r["k4b_new"] not in (None, "reject_conflict")),
                           "k4b_RECOGNIZED": cover(lambda r: r["k4b_new"] == "reject_conflict"),
                           "secjev_MISSED": cover(lambda r: r["secjev_new"] not in (None, "reject_conflict"))}
    receipt["groups"] = len(groups)
    receipt["partner_votes_hist"] = dict(collections.Counter(r["partner_votes"] for r in rows))
    receipt["token_positions_changed_hist"] = {fam: dict(collections.Counter(r[fam]["token_positions_changed"] for r in rows if r[fam]["ok"]))
                                               for fam in FAMILIES}
    receipt["status"] = "COMPLETE"
    out.mkdir(mode=0o700)
    sa.save(out / "ctx_counterfactuals.json", rows)
    sa.save(out / "receipt.json", receipt)
    print(json.dumps({k: receipt[k] for k in ("coverage", "groups", "partner_votes_hist", "token_positions_changed_hist")}, indent=1))


if __name__ == "__main__":
    main()
