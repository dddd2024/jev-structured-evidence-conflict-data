#!/usr/bin/env python3
"""A461-MON-M23 freeze (CPU, tokenizer only): design + manifest for the same-span twin test of the M18 / M22 probes.

For each model (k = kev-4B, parent M18; s = SecJev-0.8B, parent M22) and each of the 124 Stage-A scenes:
  new   the parent's `new` row, unchanged (Stage-A anchor kept; must replay bitwise on the GPU)
  TWIN  the same state + appended vote, with ONLY the appended author's earlier vote for the candidate block in the
        candidate round moved to the nearest non-candidate round (G2.3 family PARTNER_ROUND). The appended span is
        byte-identical and at the same position; exactly one token differs, before the span; Gold is not
        reject_conflict (both oracles agree).
Order: new / TWIN interleaved per scene (sorted by scene sha); batches [128, 120].
Writes m23{k,s}_design.json and m23{k,s}_manifest.jsonl."""
import argparse, collections, gzip, hashlib, json, os, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
KEV_SRC = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
BLOB_G5V2_PAIRS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
BATCHES = [128, 120]


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--helper", required=True, type=Path)
    ap.add_argument("--blobs", required=True, type=Path)
    ap.add_argument("--g23", required=True, type=Path, help="G23_OUT_R1/ctx_counterfactuals.json")
    for k in ("k", "s"):
        ap.add_argument(f"--parent-design-{k}", required=True, type=Path)
        ap.add_argument(f"--parent-manifest-{k}", required=True, type=Path)
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
    g23 = {r["scene"]: r for r in json.loads(a.g23.read_text("utf8"))}
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
        g1, _ = oracle1(st)
        ck(g1 == oracle2(st), "oracles disagree")
        return g1

    scenes = {}
    for line in gzip.open(CORPUS, "rt", encoding="utf8"):
        if line.strip():
            rec = json.loads(line)
            if rec["_meta"].get("source") == "twins_streamlet":
                scenes[hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()] = rec["state"]

    twin = {}   # model-independent: same tokenizer, same states
    Dk = json.loads(a.parent_design_k.read_text("utf8"))
    for sh, sc in sorted(Dk["scenes"].items()):
        st = scenes[sh]
        newm = sc["arms"]["new"]["message"]
        A, cr, cb = newm["author"], st["candidate_round"], st["candidate_block"]
        idx = [i for i, m in enumerate(st["received_messages"])
               if m.get("kind") == "vote" and m.get("author") == A and m.get("round") == cr and m.get("block") == cb]
        ck(len(idx) == 1, f"one partner vote {sh[:12]}")
        g = g23[sh[:12]]["PARTNER_ROUND"]
        ck(g["ok"] and g["field"] == "round", f"G2.3 twin {sh[:12]}")
        s_ = json.loads(canon(st))
        orig = dict(s_["received_messages"][idx[0]])
        s_["received_messages"][idx[0]]["round"] = g["value"]
        s_["received_messages"].append(dict(newm))
        gt = gold(s_)
        ck(gt["certificate_action"] != "reject_conflict" and not gt["conflicting_vote"] and gt == g["gold"], f"twin gold {sh[:12]}")
        e, sp = enc(s_), sc["arms"]["new"]["span"]
        ck(hids(e["ids"]) == g["token_ids_sha256"], f"twin tokens == G2.3 {sh[:12]}")
        n_ids = e["ids"][:e["seg"].count(0)]
        ck(len(n_ids) == sc["arms"]["new"]["state_len"], f"twin length {sh[:12]}")
        twin[sh] = {"message": newm, "partner_edit": {"index": idx[0], "field": "round", "from": orig["round"],
                                                      "to": g["value"], "original": orig},
                    "gold": gt, "span": sp, "state_len": len(n_ids), "token_ids_sha256": hids(e["ids"]),
                    "anchor_stage_a_fi": None}

    out.mkdir(mode=0o700)
    summary = {}
    for k in ("k", "s"):
        D = json.loads(getattr(a, f"parent_design_{k}").read_text("utf8"))
        man_p = [json.loads(x) for x in getattr(a, f"parent_manifest_{k}").read_text("utf8").splitlines() if x.strip()]
        newrow = {m["target_scene"]: m for m in man_p if m["target_arm"] == "new"}
        ck(set(newrow) == set(twin) and len(newrow) == 124, f"{k}: 124 new rows")
        design = {"schema": f"JEV_A461_MON_M23{k.upper()}_DESIGN_V1", "parent_design_sha256": sa.sha_file(getattr(a, f"parent_design_{k}")),
                  "parent_manifest_sha256": sa.sha_file(getattr(a, f"parent_manifest_{k}")),
                  "twin_family": "PARTNER_ROUND (G2.3)", "arms": ["new", "TWIN"], "batches": BATCHES, "total": sum(BATCHES),
                  "scenes": {}}
        for k2 in ("attn_layer", "resid_layers", "span_width", "groups", "preregistered_analysis"):
            if k2 in D:
                design[k2] = D[k2]
        rows, fi = [], 0
        for sh in sorted(twin):
            sc = D["scenes"][sh]
            ck(sc["arms"]["new"]["message"] == twin[sh]["message"] and sc["arms"]["new"]["span"] == twin[sh]["span"], f"{k}: new arm {sh[:12]}")
            design["scenes"][sh] = {"group": sc["group"], "gold_old": sc["gold_old"],
                                    "arms": {"new": sc["arms"]["new"], "TWIN": twin[sh]}}
            for arm in ("new", "TWIN"):
                fi += 1
                base = newrow[sh]
                m = {"forward_index": fi, "run": 1 if fi <= BATCHES[0] else 2, "condition": f"monitor_capture_{arm}",
                     "target_scene": sh, "target_arm": arm, "source_group": base["source_group"],
                     "gold_action": base["gold_action"] if arm == "new" else twin[sh]["gold"]["certificate_action"],
                     "span": base["span"], "state_len": base["state_len"], "capture": base["capture"],
                     "anchor_stage_a_fi": base["anchor_stage_a_fi"] if arm == "new" else None,
                     "token_ids_sha256": base["token_ids_sha256"] if arm == "new" else twin[sh]["token_ids_sha256"]}
                rows.append(m)
        ck(fi == sum(BATCHES), "total")
        (out / f"m23{k}_design.json").write_text(json.dumps(design, indent=1, sort_keys=True) + "\n", encoding="utf8")
        (out / f"m23{k}_manifest.jsonl").write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows), encoding="utf8")
        summary[k] = {"rows": len(rows), "twin_gold": dict(collections.Counter(t["gold"]["certificate_action"] for t in twin.values()))}
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
