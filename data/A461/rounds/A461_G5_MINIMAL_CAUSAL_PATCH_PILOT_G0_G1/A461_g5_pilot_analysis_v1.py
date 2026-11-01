#!/usr/bin/env python3
"""A461-G5 minimal causal patch pilot: preregistered analysis (CPU, zero forwards).

Consumes ONLY the pilot GPU run's raw logits row file and the archived G1S V2
logits; implements exactly the analysis_preregistered section of
A461_G5_MINIMAL_CAUSAL_PATCH_PILOT_PROTOCOL_V1. No model, no GPU, no network.

Outputs (one JSON per block + receipt):
  analysis_results.json:
    - baselines: C margins of host SA / donor NEW (fresh runs) + bitwise match vs archived
    - restoration: per (host, layer) delta_margin vs host SA baseline, flip,
      SA-sham and permuted control deltas at the same (host, layer),
      and the preregistered supportive verdict (delta>0 AND beats BOTH controls)
    - suppression: per (host, layer) delta_margin vs donor NEW baseline + flips
    - off_target: quorum / certificate_action / evidence_level margin shifts on every patched forward
    - interpretation labels: single-donor DEV exploratory
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

BLOB_RAW_LOGITS = "13400252b360863a80baea66b39b9a7dbe0ca633"
DONOR_KEY = "T2_WAIT_TO_REJECT:433890d19a90625e"
HOST_KEYS = ["T2_WAIT_TO_REJECT:1b0e96fb22c6aebe", "T2_ACCEPT_TO_REJECT:231b919006dc1777"]
LAYERS = [11, 23]


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def save(p, v):
    with p.open("x", encoding="utf8", newline="\n") as f:
        json.dump(v, f, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def margin(qrow):
    return qrow["logits"][1] - qrow["logits"][0]


def read(row):
    m = margin(next(q for q in row["questions"] if q["id"] == "conflicting_vote"))
    return m, ("true" if m > 0 else "false")


def crow(row):
    return next(q for q in row["questions"] if q["id"] == "conflicting_vote")


def head_margin(row, qid, key_hi, key_lo):
    q = next(q for q in row["questions"] if q["id"] == qid)
    return q["logits"][q["keys"].index(key_hi)] - q["logits"][q["keys"].index(key_lo)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--pilot-raw", required=True, type=Path)
    ap.add_argument("--archived-raw", type=Path, default=None,
                    help="optional local copy of the archived G1S V2 logits jsonl; default reads the pinned git blob")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve(strict=False)
    ck(out.parent.is_dir() and not out.exists(), "NEW out dir")
    out.mkdir(mode=0o700)
    produced = []
    try:
        rows = [json.loads(x) for x in a.pilot_raw.read_text("utf8").splitlines() if x.strip()]
        ck(len(rows) == 28, f"expected 28 pilot rows, got {len(rows)}")
        by_cond = {}
        for r in rows:
            by_cond.setdefault(r["condition"], []).append(r)
        arch = {}
        if a.archived_raw is not None:
            src_lines = a.archived_raw.read_text("utf8").splitlines()
        else:
            src_lines = subprocess.run(["git", "-C", str(a.repo_root), "cat-file", "blob", BLOB_RAW_LOGITS],
                                       capture_output=True, text=True, check=True).stdout.splitlines()
        for x in src_lines:
            if x.strip():
                d = json.loads(x)
                if d.get("kind") == "primary" and "plan_row" in d:
                    arch[d["plan_row"]] = d
        arch_by_sha = {d["token_ids_sha256"]: d for d in arch.values()}
        res = {"schema": "JEV_A461_G5_PILOT_ANALYSIS_V1",
               "interpretation_label": "single-donor two-host two-layer DEV exploratory causal probe; not a mechanism proof"}

        # determinism of fresh baselines vs archived: join by full token-ids SHA
        det = []
        for cond, label in [("baseline_host_sa_unpatched", "host_sa"), ("baseline_donor_new_unpatched", "donor_new")]:
            for fresh in by_cond[cond]:
                a = arch_by_sha.get(fresh["token_ids_sha256"])
                ck(a is not None, "no archived row with token sha of " + fresh["target"])
                bitwise = all(x["logits"] == y["logits"]
                              for x, y in zip(sorted(a["questions"], key=lambda q: q["id"]),
                                              sorted(fresh["questions"], key=lambda q: q["id"])))
                det.append({"condition": cond, "target": fresh["target"],
                            "token_ids_sha256": fresh["token_ids_sha256"],
                            "archived_plan_row": a["plan_row"],
                            "fresh_c_margin": round(read(fresh)[0], 6),
                            "archived_c_margin": round(read(a)[0], 6),
                            "bitwise_all_heads": bitwise})
        ck(len(det) == 3 and all(d["bitwise_all_heads"] for d in det), "baseline determinism failed")
        res["baseline_determinism_vs_archived"] = det
        donor_new_base = next(r for r in by_cond["baseline_donor_new_unpatched"])
        res["baselines"] = {
            "donor_new_fresh_c_margin": round(read(donor_new_base)[0], 6),
            "donor_new_fresh_read": read(donor_new_base)[1],
            "host_sa_fresh_c_margins": {r["target"]: round(read(r)[0], 6)
                                        for r in by_cond["baseline_host_sa_unpatched"]},
        }

        # identity (plumbing gate)
        ident = []
        for key in HOST_KEYS:
            fresh = next(r for r in by_cond["baseline_host_sa_unpatched"] if r["target"] == key + ":SA")
            pid = next(r for r in by_cond["patch_identity_host_sa"] if r["target"] == key + ":SA")
            same = all(x["logits"] == y["logits"] for x, y in zip(fresh["questions"], pid["questions"]))
            ident.append({"target": key + ":SA", "layer": pid["patch_layer"], "bitwise_equal": same})
        res["identity_self_patch"] = ident

        # restoration + controls
        rest = []
        for key in HOST_KEYS:
            base = next(r for r in by_cond["baseline_host_sa_unpatched"] if r["target"] == key + ":SA")
            mb = read(base)[0]
            for L in LAYERS:
                e = {}
                for cond, label in [("patch_restoration_donor_new_to_host_sa", "restoration"),
                                    ("patch_sasham_donor_sa_to_host_sa", "sa_sham"),
                                    ("patch_permuted_donor_new_to_host_sa", "permuted")]:
                    r = next(x for x in by_cond[cond] if x["target"] == key + ":SA" and x["patch_layer"] == L)
                    m, rd = read(r)
                    e[label] = {"delta_margin": round(m - mb, 6), "read": rd, "margin": round(m, 6)}
                e["layer"] = L
                e["host"] = key
                e["baseline_margin"] = round(mb, 6)
                e["supportive_preregistered"] = bool(
                    e["restoration"]["delta_margin"] > 0
                    and e["restoration"]["delta_margin"] > e["sa_sham"]["delta_margin"]
                    and e["restoration"]["delta_margin"] > e["permuted"]["delta_margin"])
                rest.append(e)
        res["restoration"] = rest

        # suppression
        sup = []
        mdb = read(donor_new_base)[0]
        for key in HOST_KEYS:
            for L in LAYERS:
                r = next(x for x in by_cond["patch_suppression_host_new_to_donor_new"]
                         if x["patch_source"] == key + ":new" and x["patch_layer"] == L)
                m, rd = read(r)
                sup.append({"host_source": key, "layer": L, "delta_margin": round(m - mdb, 6),
                            "read": rd, "donor_baseline_margin": round(mdb, 6),
                            "negative": m - mdb < 0, "flip_away": rd == "false"})
        res["suppression"] = sup

        # off-target margins on every patched forward
        off = []
        for r in rows:
            if r["condition"].startswith("patch_"):
                off.append({"forward_index": r["forward_index"], "condition": r["condition"],
                            "target": r["target"], "layer": r["patch_layer"],
                            "quorum_margin_true": round(head_margin(r, "quorum", "true", "false"), 6),
                            "action_margin_reject": round(head_margin(r, "certificate_action", "reject_conflict", "accept"), 6),
                            "evidence_margin_l2_l0": round(head_margin(r, "evidence_level", "2", "0"), 6)})
        res["off_target"] = off

        # summary verdicts (descriptive)
        n_sup = sum(1 for e in rest if e["supportive_preregistered"])
        res["summary"] = {
            "restoration_supportive_cells": f"{n_sup}/{len(rest)}",
            "restoration_any_flip": any(e["restoration"]["read"] == "true" for e in rest),
            "suppression_negative_cells": f"{sum(1 for s in sup if s['negative'])}/{len(sup)}",
            "suppression_any_flip": any(s["flip_away"] for s in sup),
            "identity_all_bitwise": all(i["bitwise_equal"] for i in ident),
            "note": "supportive/negative are per-cell descriptive labels under the frozen decision rule; "
                    "no claim beyond single-donor DEV exploratory evidence is licensed by this pilot"
        }
        save(out / "analysis_results.json", res)
        produced.append("analysis_results.json")
        receipt = {"schema": "JEV_A461_G5_PILOT_ANALYSIS_RECEIPT_V1", "status": "COMPLETE_A461_G5_PILOT_ANALYSIS",
                   "gpu_forwards": 0, "model_loads": 0, "rows_analyzed": len(rows)}
    except Exception as err:
        import traceback
        receipt = {"schema": "JEV_A461_G5_PILOT_ANALYSIS_RECEIPT_V1", "status": "FAIL_ANALYSIS",
                   "error_type": type(err).__name__, "error_message": str(err),
                   "traceback": traceback.format_exc()[-1500:]}
    receipt_file = out / "analysis_receipt.json"
    with receipt_file.open("x", encoding="utf8", newline="\n") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    produced.append("analysis_receipt.json")
    h = hashlib.sha256()
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            d = (out / n).read_bytes()
            f.write(hashlib.sha256(d).hexdigest() + "  " + n + "\n")
    print(canon(receipt))
    return 0 if receipt["status"].startswith("COMPLETE") else 2


if __name__ == "__main__":
    sys.exit(main())
