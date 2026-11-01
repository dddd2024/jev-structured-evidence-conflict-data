#!/usr/bin/env python3
"""A461-MECH-M1 R1: CPU freeze of the round-binding transplant test on kev-4B (zero forwards).

Question (M1, H-REL vs H-CLS): does the repairing L11 append-span state carry a relation the donor
computed in context (the vote conflicts with the author's earlier vote IN THE CANDIDATE ROUND), or a
generic "vote for another block" state? The G1.0 gate (fd79903) built single-field variants of each
donor's appended conflict vote under the frozen-width token gate:
  ROUND   same message, round -> a non-candidate round (rule Gold: no conflict); ~1 token differs
  OK_ALT  same message, author -> another supporter (rule Gold: still a conflict)
Design: the 14 K-C replication donors x the 8 K-C hosts (same selection as K-C, cd4cd9e5), all question
rows patched into the host's own new span at L* = 11 (the K-C layer), arms
  main        donor new span              (positive control; must replay K-C bitwise)
  round       donor ROUND span
  okalt       donor OK_ALT span
  doserand_r  dose-matched random around the host span with the ROUND span's per-position distance
Captures (all rows, all 32 layers): donor new (bitwise == K-C), donor ROUND, donor OK_ALT, host new
(bitwise == K-C). 50 captures + 448 patches = 498 calls in [128, 128, 128, 114].
"""
import argparse, collections, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_KC_DESIGN = "cd4cd9e5632cfa1b8aa476b94a332e3705af2f0f"
BLOB_KC_RAW = "19d3a06c27953b1f2b4dcd2770394d28741a69fd"
BLOB_G10_CF = "06ee06d7942b9f1a5f09c35777d5da1149655e4d"
LAYER = 11
PLAN = [128, 128, 128, 114]
ARMS = ("main", "round", "okalt", "doserand_r")
SRC_ARM = {"main": "new", "round": "ROUND", "okalt": "OKALT", "doserand_r": "ROUND"}

PREREG = {
    "readouts": "M = conflict margin; A = logit(reject_conflict) - max(accept, wait); JOINT = M > 0 and A > 0; "
                "dM = M(patch) - M(in-run host capture)",
    "units": "only the 104 cross-group cells (donor group != host group) enter counts; source groups are the unit; "
             "cells share donors and hosts, counts are descriptive decision rules, not independent tests",
    "P0_positive_control": "all 112 main patches and the 22 donor-new/host-new captures replay the K-C raw rows bitwise "
                           "(runner fails closed otherwise)",
    "D_donor_recognition": "reported first, per donor: JOINT and M of the donor's own ROUND and OK_ALT forwards "
                           "(does kev-4B read the round field in the donor context)",
    "H_REL": "(a) #JOINT_round <= 1/4 * #JOINT_main AND (b) dM_main > dM_round in >= 75% of cells and in a majority of "
             "cells for >= 10 of 14 donor groups",
    "H_CLS": "#JOINT_round >= 1/2 * #JOINT_main AND dM_main > dM_round in < 60% of cells",
    "verdict_round": "REL_SUPPORTED if H_REL; CLS_SUPPORTED if H_CLS; else GRADED_INTERMEDIATE",
    "H_ROLE_ABSTRACT": "#JOINT_okalt >= 1/2 * #JOINT_main -> repair does not hinge on the specific author token; "
                       "#JOINT_okalt <= 1/4 * #JOINT_main -> author-identity specific; else intermediate",
    "always_reported": "round vs doserand_r (specific residual of the ROUND span), leave-one-donor-group-out, per host, "
                       "stratification by donor ROUND self-recognition, all null and negative outcomes",
}


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def seed_of(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode("utf8")).hexdigest()[:12], 16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", required=True, type=Path)
    ap.add_argument("--kc-design", required=True, type=Path)
    ap.add_argument("--kc-raw", required=True, type=Path)
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.kc_design) == BLOB_KC_DESIGN
       and file_blob(a.kc_raw) == BLOB_KC_RAW and file_blob(a.g10_counterfactuals) == BLOB_G10_CF, "pins")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    kc = json.loads(a.kc_design.read_text("utf8"))
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    kraw = [json.loads(x) for x in a.kc_raw.read_text("utf8").splitlines() if x.strip()]
    ck(kc["layers"] == [LAYER], "K-C layer")
    donors = [(s, g) for s, g in kc["selection"]["replication_donors"]]
    hosts = [(s, g) for s, g, _m in kc["selection"]["replication_hosts"]]
    ck(len(donors) == 14 and len(hosts) == 8, "selection")
    for s, _g in donors:
        ck(cf[s]["ROUND"]["ok"] and cf[s]["OK_ALT"]["ok"], f"G1.0 variant missing {s[:8]}")
        for k in ("ROUND", "OK_ALT"):
            sp = cf[s][k]["span"]
            ck(sp[1] - sp[0] == roster[s]["frozen_width"], f"variant width {s[:8]}:{k}")
    kc_cap = {(x["target_scene"], x["target_arm"]): x["forward_index"] for x in kraw if x["capture"]}
    kc_main = {(x["donor"], x["host"]): x["forward_index"] for x in kraw if x["condition"] == "patch_kc_main_all"}

    def span(s, arm):
        if arm in ("new", "SA"):
            return roster[s]["appended_span_in_state"][arm]
        return cf[s]["ROUND" if arm == "ROUND" else "OK_ALT"]["span"]
    rows = []

    def add(**kw):
        n = len(rows)
        run = 1 if n < 128 else (2 if n < 256 else (3 if n < 384 else 4))
        rows.append(dict(forward_index=n + 1, run=run, **kw))

    def capture(s, arm, kind):
        add(phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm, source_kind=kind,
            capture={"tag": f"{arm}:{s[:12]}", "span": span(s, arm), "layers": "all", "rows": "all", "save": True},
            bitwise_vs_kc=kc_cap.get((s, arm)),
            variant_message=None if arm in ("new", "SA") else cf[s]["ROUND" if arm == "ROUND" else "OK_ALT"]["message"])

    for s, _g in donors:
        for arm in ("new", "ROUND", "OKALT"):
            capture(s, arm, "donor")
    for h, _g in hosts:
        capture(h, "new", "host")
    gd, gh = dict(donors), dict(hosts)
    for d, _ in donors:
        for h, _ in hosts:
            for arm in ARMS:
                src = SRC_ARM[arm]
                add(phase="patch", condition=f"patch_m1_{arm}_all", direction="repair", scope="all", source_kind=arm,
                    donor=d, host=h, layer=LAYER, cross_group=gd[d] != gh[h], target_scene=h, target_arm="new",
                    bitwise_vs_kc=kc_main[(d, h)] if arm == "main" else None,
                    patch={"layer": LAYER, "span": span(h, "new"), "source": f"{src}:{d[:12]}",
                           "transform": "deltarand" if arm == "doserand_r" else "none", "rows": "all",
                           "delta_target": f"new:{h[:12]}" if arm == "doserand_r" else None,
                           "seed": seed_of("M1", d, h, LAYER) if arm == "doserand_r" else None})
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, 5)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r.get("bitwise_vs_kc")) == 22 + 112, "bitwise replay refs")
    design = {"schema": "JEV_A461_MECH_M1_ROUND_BINDING_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M1_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader)",
              "inputs": {"roster_blob": BLOB_ROSTER, "kc_design_blob": BLOB_KC_DESIGN, "kc_raw_blob": BLOB_KC_RAW,
                         "g10_counterfactuals_blob": BLOB_G10_CF},
              "selection": {"donors": donors, "hosts": hosts,
                            "variants": {s: {"ROUND": cf[s]["ROUND"]["message"], "OK_ALT": cf[s]["OK_ALT"]["message"],
                                             "frozen": cf[s]["frozen_message"]} for s, _ in donors}},
              "layers": [LAYER], "arms": list(ARMS), "plan": PLAN, "total": len(rows),
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M1 forwards; {len(rows)} calls / {PLAN} under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m1_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m1_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m1_design.json", "m1_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "plan": PLAN, "cross_group_cells": sum(1 for r in rows if r.get("cross_group")) // 4,
                      "manifest_blob": file_blob(out / "m1_manifest.jsonl"), "design_blob": file_blob(out / "m1_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
