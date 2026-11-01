#!/usr/bin/env python3
"""A461-G2 capture verifier V1 (CPU, no model; audit item P1-4).

For one stage, checks every capture row of the archived raw log against the released tensors:
  1. the capture file exists and its SHA-256 equals both the raw row's `capture_file.sha256` and the stage's
     ATTEMPT_R1_CAPTURES_SHA256.txt entry;
  2. the tensor is float16 with the shape recorded in the raw row;
  3. where the runner recorded `cross_row_max_absdiff` (all-row captures, Stages E, F, K-B, K-C), the span state is
     recomputed as identical across question rows exactly when the runner reported 0.0;
  4. every file in the SHA list is referenced by exactly one raw row.
Usage: verify_captures_v1.py --raw RAW.jsonl --captures DIR --sha-list ATTEMPT_R1_CAPTURES_SHA256.txt
"""
import argparse, hashlib, json, sys
from pathlib import Path

import torch


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--captures", required=True, type=Path)
    ap.add_argument("--sha-list", required=True, type=Path)
    a = ap.parse_args()
    listed = {}
    for line in a.sha_list.read_text("utf8").splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            listed[name.lstrip("*").strip()] = h
    rows = [json.loads(x) for x in a.raw.read_text("utf8").splitlines() if x.strip()]
    caps = [r for r in rows if r.get("capture_file")]
    bad, seen, cross_checked = [], set(), 0
    for r in caps:
        cf = r["capture_file"]
        p = a.captures / cf["name"]
        if cf["name"] in seen:
            bad.append(f"{cf['name']}: referenced twice")
        seen.add(cf["name"])
        if not p.is_file():
            bad.append(f"{cf['name']}: missing"); continue
        h = sha(p)
        if h != cf["sha256"] or h != listed.get(cf["name"]):
            bad.append(f"{cf['name']}: sha mismatch")
        t = torch.load(p, map_location="cpu", weights_only=True)
        if t.dtype != torch.float16 or list(t.shape) != cf["shape"]:
            bad.append(f"{cf['name']}: dtype/shape {t.dtype} {list(t.shape)} vs {cf['shape']}")
        if "cross_row_max_absdiff" in r:
            d = float((t.float() - t[:, :1].float()).abs().max())
            if (d == 0.0) != (r["cross_row_max_absdiff"] == 0.0):
                bad.append(f"{cf['name']}: cross-row {d} vs recorded {r['cross_row_max_absdiff']}")
            cross_checked += 1
    unref = sorted(set(listed) - seen)
    if unref:
        bad.append(f"{len(unref)} listed files not referenced by any raw row")
    res = {"raw_rows": len(rows), "capture_rows": len(caps), "listed_files": len(listed),
           "cross_row_checked": cross_checked, "status": "PASS" if not bad else "FAIL", "problems": bad[:20]}
    print(json.dumps(res))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
