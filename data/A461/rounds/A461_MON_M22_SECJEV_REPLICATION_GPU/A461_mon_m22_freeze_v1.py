#!/usr/bin/env python3
"""A461-MON-M22 R1: CPU freeze of the second-model replication of M18 on SecJev-0.8B (zero model forwards).

Same 124 Stage-A scenes x old / new / SA / ROUND / OUTSIDER as M18 (the frozen M18 rows: states, spans, token sha;
the two models share the tokenizer, and all 372 Stage-A token sha already match across them), re-pinned to SecJev:
the old / new / SA rows are anchored to the SecJev Stage-A raw rows (blob 680a7811), and the residual captures are
at SecJev's full-attention layers 3, 7, 11, 15, 19, 23 (24 layers; L11 is full attention, as in kev-4B). The M18
rules apply unchanged except the layer lists (LAST and SPAN residuals at emb + those 6 layers; whitening at L11 and
the last layer L23). M1's round-binding transplant is NOT replicated: SecJev has 4 strict donors in 3 groups (Stage
A), too few for the 14-donor design (stated in the prereg).
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
BLOB_M18_DESIGN = "1998024bffc0e8deee2cbf0d563eafbffad6bfef"
BLOB_M18_MANIFEST = "88f99a1827ad428515a9620408ae74c3545af0db"
BLOB_SECJEV_STAGE_A_RAW = "680a78116e8099b19ef11298326587d7d8e76fd0"
RESID_LAYERS = [3, 7, 11, 15, 19, 23]
HEAD_LAYER = 11
PLAN_CAP = 128


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m18-design", required=True, type=Path)
    ap.add_argument("--m18-manifest", required=True, type=Path)
    ap.add_argument("--secjev-stage-a-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.m18_design) == BLOB_M18_DESIGN and file_blob(a.m18_manifest) == BLOB_M18_MANIFEST
       and file_blob(a.secjev_stage_a_raw) == BLOB_SECJEV_STAGE_A_RAW, "pins")
    d18 = json.loads(a.m18_design.read_text("utf8"))
    man = [json.loads(x) for x in a.m18_manifest.read_text("utf8").splitlines() if x.strip()]
    sj = {(x["scene_sha256"], x["arm"]): x for x in (json.loads(l) for l in a.secjev_stage_a_raw.read_text("utf8").splitlines()
                                                     if l.strip()) if x.get("kind") == "primary"}
    ck(len(man) == 620 and len(sj) == 372, "620 rows / 372 SecJev Stage-A rows")
    rows = []
    for m in man:
        r = {k: m[k] for k in ("target_scene", "target_arm", "source_group", "gold_action", "span", "token_ids_sha256",
                               "state_len", "condition")}
        k = (m["target_scene"], m["target_arm"])
        if k in sj:
            ck(sj[k]["token_ids_sha256"] == m["token_ids_sha256"], f"token sha differs from SecJev Stage A {k[0][:8]}")
            r["anchor_stage_a_fi"] = sj[k]["forward_index"]
        else:
            ck(m["target_arm"] in ("ROUND", "OUTSIDER"), "missing SecJev anchor")
            r["anchor_stage_a_fi"] = None
        r["capture"] = dict(m["capture"], resid_layers=RESID_LAYERS)
        rows.append(r)
    n = len(rows)
    plan = [PLAN_CAP] * (n // PLAN_CAP) + ([n % PLAN_CAP] if n % PLAN_CAP else [])
    for i, r in enumerate(rows):
        r.update(forward_index=i + 1, run=i // PLAN_CAP + 1)
    ck(sum(1 for r in rows if r["anchor_stage_a_fi"]) == 372, "372 anchors")
    rules = dict(d18["preregistered_analysis"])
    rules["features"] = rules["features"].replace("L in {emb (input of layer 0), 3, 7, 11, 15, 19, 23, 27, 31}",
                                                  "L in {emb (input of layer 0), 3, 7, 11, 15, 19, 23}")
    rules["V2_location"] = rules["V2_location"].replace("WHITEN(LAST_RESID_31)", "WHITEN(LAST_RESID_23)")
    rules["consistency_gate"] = rules["consistency_gate"].replace("kev-4B Stage-A raw row", "SecJev-0.8B Stage-A raw row")
    rules["model"] = ("SecJev-0.8B (Qwen3.5-0.8B base + the SecJev LoRA and pointer head; 24 layers, full attention at 3, 7, "
                      "11, 15, 19, 23; hidden 1024, 8 query heads x 256)")
    rules["replication_scope"] = ("replicates M18 (decodability at the append span and the decision position, the "
                                  "monitor comparison, natural false veto on near misses) on a second frozen model; "
                                  "M1's round-binding transplant is not replicable on SecJev (4 strict donors in 3 groups)")
    ck("emb (input of layer 0), 3, 7, 11, 15, 19, 23}" in rules["features"] and "LAST_RESID_23" in rules["V2_location"],
       "rule edits")
    design = {"schema": "JEV_A461_MON_M22_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M22_FORWARD",
              "inputs": {"m18_design_blob": BLOB_M18_DESIGN, "m18_manifest_blob": BLOB_M18_MANIFEST,
                         "secjev_stage_a_raw_blob": BLOB_SECJEV_STAGE_A_RAW,
                         **{k: v for k, v in d18["inputs"].items() if k != "stage_a_k4b_raw_blob"}},
              "arms": d18["arms"], "resid_layers": RESID_LAYERS, "attn_layer": HEAD_LAYER, "writer_heads": None,
              "span_width": d18["span_width"], "field_marks": d18["field_marks"], "scenes": d18["scenes"],
              "groups": d18["groups"], "coverage": d18["coverage"], "plan": plan, "total": n,
              "preregistered_analysis": rules,
              "gpu_status": f"0 M22 forwards; {n} calls / {len(plan)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m22_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m22_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for nm in ("m22_design.json", "m22_manifest.jsonl"):
            f.write(sha_file(out / nm) + "  " + nm + "\n")
    print(json.dumps({"rows": n, "plan": plan, "anchors": 372, "manifest_blob": file_blob(out / "m22_manifest.jsonl"),
                      "design_blob": file_blob(out / "m22_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
