#!/usr/bin/env python3
"""A461-MON-G2.4 CPU go/no-go (zero model loads, zero forwards; tokenizer only + existing M23 captures).

Answers the re-audit ee23782 (CONDITIONAL_CONTINUE / HOLD_UNBOUNDED_GPU) gates for the one bounded package it allows:
  Part A  orthogonal relation edit: PARTNER_BLOCK_OTHER - move the appended author's earlier candidate-block vote to a
          THIRD block (not the candidate, not the appended vote's block), so the appended vote is neither a conflict
          nor a duplicate. Gates as G2.3: both oracles agree, Gold != reject_conflict, equal token length, appended
          span ids and position unchanged, question segments unchanged.
  Part B  room for a within-scene state swap: from the M23 captures, the relative size of new-vs-TWIN differences in
          the L11 span write, the L11 span residual and the decision-position state, against the between-scene
          spread of the same features (median distance from a scene's new state to other scenes' new states)."""
import argparse, collections, gzip, hashlib, json, os, statistics, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
KEV_SRC = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
BLOB_G5V2_PAIRS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--helper", required=True, type=Path)
    ap.add_argument("--blobs", required=True, type=Path)
    ap.add_argument("--m18-design", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path, help="GPU work dir with M23K/M23S runs")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve(strict=False)
    ck(out.parent.is_dir() and not out.exists(), "out dir")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    import importlib.util
    spec = importlib.util.spec_from_file_location("stage_a", a.helper)
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    canon, hids, oracle1, oracle2 = sa.canon, sa.hids, sa.oracle1, sa.oracle2
    ck(sa.sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    pairs = (a.blobs / BLOB_G5V2_PAIRS).read_bytes()
    ck(hashlib.sha1(b"blob %d\0" % len(pairs) + pairs).hexdigest() == BLOB_G5V2_PAIRS, "pairs blob")
    q_tw = json.loads(pairs.decode("utf8").splitlines()[0])["native_request"]["questions"]
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
                scenes[hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()] = rec["state"]
    D = json.loads(a.m18_design.read_text("utf8"))

    # ---- Part A ----
    rowsA = []
    for sh, sc in sorted(D["scenes"].items()):
        st = scenes[sh]
        newm = sc["arms"]["new"]["message"]
        ns = json.loads(canon(st))
        ns["received_messages"].append(dict(newm))
        e_new = enc(ns)
        n_state, sp = e_new["seg"].count(0), sc["arms"]["new"]["span"]
        A, cr, cb = newm["author"], st["candidate_round"], st["candidate_block"]
        idx = [i for i, m in enumerate(st["received_messages"])
               if m.get("kind") == "vote" and m.get("author") == A and m.get("round") == cr and m.get("block") == cb]
        blocks = sorted({m.get("block") for m in st["received_messages"] if m.get("block")} - {cb, newm["block"]})
        res = {"scene": sh[:12], "group": sc["group"], "ok": False, "third_blocks_available": len(blocks), "gold_ok_tried": 0}
        for v in blocks:
            s = json.loads(canon(ns))
            for i in idx:
                s["received_messages"][i]["block"] = v
            g, _ = gold(s)
            if g is None or g["certificate_action"] == "reject_conflict" or g["conflicting_vote"]:
                continue
            res["gold_ok_tried"] += 1
            e = enc(s)
            ids, nids = e["ids"], e_new["ids"]
            if len(ids) != len(nids) or e["seg"].count(0) != n_state or ids[sp[0]:sp[1]] != nids[sp[0]:sp[1]] or ids[n_state:] != nids[n_state:]:
                continue
            diff = [p for p in range(len(ids)) if ids[p] != nids[p]]
            res.update(ok=True, value=v, gold=g, gold_eq_old=g["certificate_action"] == sc["gold_old"],
                       token_positions_changed=len(diff), changed_before_span=all(p < sp[0] for p in diff))
            break
        rowsA.append(res)
    okA = [r for r in rowsA if r["ok"]]
    partA = {"scenes": len(okA), "of": len(rowsA), "groups": len({r["group"] for r in okA}),
             "groups_of": len({r["group"] for r in rowsA}), "gold_eq_old": sum(r["gold_eq_old"] for r in okA),
             "no_third_block": sum(r["third_blocks_available"] == 0 for r in rowsA),
             "token_positions_changed": dict(collections.Counter(r["token_positions_changed"] for r in okA))}

    # ---- Part B ----
    import torch
    partB = {}
    for k, K, last in (("k", "K", "L31"), ("s", "S", "L23")):
        run = a.work / f"M23{K}_GPU_RUNS" / "ATTEMPT_R1"
        rows = [json.loads(x) for x in (run / f"raw_native_logits_m23{k}.jsonl").read_text("utf8").splitlines() if x.strip()]
        by = {(r["target_scene"], r["target_arm"]): r for r in rows}
        sc = sorted({r["target_scene"] for r in rows})
        F = {}
        for key in by:
            f = torch.load(run / "captures" / by[key]["capture_file"]["name"], weights_only=True)
            names = f["names"]
            F[key] = {"ATTN11": f["attn11_span"].double().mean(0), "SPAN_L11": f["span_mean"][names.index("L11")].double(),
                      "LAST": f["last"][names.index(last)].double()}
        res = {}
        for feat in ("ATTN11", "SPAN_L11", "LAST"):
            within = [float((F[(s, "new")][feat] - F[(s, "TWIN")][feat]).norm() / F[(s, "new")][feat].norm()) for s in sc]
            between = [statistics.median(float((F[(s, "new")][feat] - F[(t, "new")][feat]).norm() / F[(s, "new")][feat].norm())
                                         for t in sc if t != s) for s in sc]
            ratio = [w / b for w, b in zip(within, between)]
            res[feat] = {"median_rel_within_new_vs_twin": round(statistics.median(within), 5),
                         "median_rel_between_scenes": round(statistics.median(between), 5),
                         "median_within_over_between": round(statistics.median(ratio), 4)}
        act = lambda qs: (lambda q: q["keys"][max(range(len(q["keys"])), key=lambda i: q["logits"][i])])(next(x for x in qs if x["id"] == "certificate_action"))
        disc = sum(act(by[(s, "new")]["questions"]) != act(by[(s, "TWIN")]["questions"]) for s in sc)
        disc_rej = sum((act(by[(s, "new")]["questions"]) == "reject_conflict") != (act(by[(s, "TWIN")]["questions"]) == "reject_conflict") for s in sc)
        res["discordant_action_pairs"] = disc
        res["discordant_reject_pairs"] = disc_rej
        partB[k] = res

    receipt = {"schema": "JEV_A461_MON_G24_GO_NOGO_CPU_V1", "gpu_forwards": 0, "model_loads": 0,
               "script_sha256": sa.sha_file(Path(__file__).resolve()), "partA_PARTNER_BLOCK_OTHER": partA, "partB_state_gap": partB}
    out.mkdir(mode=0o700)
    sa.save(out / "partA_rows.json", rowsA)
    sa.save(out / "receipt.json", receipt)
    print(json.dumps(receipt, indent=1))


if __name__ == "__main__":
    main()
