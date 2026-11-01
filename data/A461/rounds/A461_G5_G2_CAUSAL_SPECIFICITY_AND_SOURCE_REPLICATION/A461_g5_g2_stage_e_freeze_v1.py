#!/usr/bin/env python3
"""A461-G5-G2 Stage-E CPU freeze (zero GPU): action-level repair on near-threshold hosts.

Stage-D (01f46ef) erratum: Stage-B/C/D patches overwrote the span only in the
conflicting_vote row; in kev row form every question is its own causal row, so the
certificate_action output could not change. Stage-E patches the span in the
certificate_action row itself (scope "action") and in every question row (scope "all").

Same donors (Stage-B design) and the same 8 Stage-D hosts (Stage-A FFF, M_new >= -4.0,
outside donor groups); their certificate_action margin on the new arm
A = logit(reject_conflict) - max(logit(accept), logit(wait)) is -0.59 .. -4.07.
Captures (bitwise replays of Stage-A rows) store the span from ALL question rows.
Patches into the host's own new span, per row with that row's own source span:
  settings: (L11, action), (L11, all), (L12, all); arms: main (donor new), SA-sham
  (donor SA), dose-matched random (host new + seeded unit direction x ||donor new -
  host new|| per row and position).
Total 16 + 4 x 8 x 3 x 3 = 304 calls in [88, 72, 72, 72].
"""
import argparse, collections, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
BLOB_STAGE_A_RAW = "680a78116e8099b19ef11298326587d7d8e76fd0"
BLOB_STAGE_D_DESIGN = "1351650201c48ba2bff2818b3f891c064fddd53c"
BLOB_STAGE_D_RAW_NAME = "raw_native_logits_stage_d.jsonl"
SETTINGS = [(11, "action"), (11, "all"), (12, "all")]
PLAN = [88, 72, 72, 72]


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_file(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def seed_of(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode("utf8")).hexdigest()[:12], 16)


def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--stage-d-design", required=True, type=Path)
    ap.add_argument("--stage-d-manifest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    ck(file_blob(a.stage_a_raw) == BLOB_STAGE_A_RAW and file_blob(a.stage_d_design) == BLOB_STAGE_D_DESIGN, "pins")
    sa = {(r["scene_sha256"], r["arm"]): r for r in jsonl(a.stage_a_raw) if r["kind"] == "primary"}
    ddesign = json.loads(a.stage_d_design.read_text("utf8"))
    donors = [x["scene_sha256"] for x in ddesign["D2_repair"]["donors"]]
    hosts = [x["scene_sha256"] for x in ddesign["D2_repair"]["hosts"]]
    ck(len(donors) == 4 and len(hosts) == 8, "donor/host sets")
    # spans exactly as frozen (and fresh-encode verified) in the Stage-D manifest
    spans = {}
    for m in jsonl(a.stage_d_manifest):
        if m.get("capture"):
            spans[(m["target_scene"], m["target_arm"])] = m["capture"]["span"]
    ck(all((d, arm) in spans for d in donors for arm in ("new", "SA")) and all((h, "new") in spans for h in hosts),
       "spans from Stage-D manifest")

    def A(row):
        q = next(q for q in row["questions"] if q["id"] == "certificate_action")
        d = dict(zip(q["keys"], q["logits"]))
        return d["reject_conflict"] - max(d["accept"], d["wait"])
    host_A = {h: A(sa[(h, "new")]) for h in hosts}
    donor_A = {d: {arm: A(sa[(d, arm)]) for arm in ("old", "new", "SA")} for d in donors}
    ck(all(v < 0 for v in host_A.values()), "hosts must not already reject")

    rows = []

    def add(**kw):
        rows.append(dict(forward_index=len(rows) + 1, **kw))
    for s, arm in [(d, arm) for d in donors for arm in ("new", "SA")] + [(h, "new") for h in hosts]:
        add(run=1, phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm,
            capture={"tag": f"{arm}:{s[:12]}", "span": spans[(s, arm)], "layers": "all", "rows": "all", "save": True},
            bitwise_vs_stage_a=sa[(s, arm)]["forward_index"])
    for di, d in enumerate(donors):
        for h in hosts:
            for L, scope in SETTINGS:
                for cond, src, tr in (("patch_repair_main", f"new:{d[:12]}", "none"),
                                      ("patch_repair_sasham", f"SA:{d[:12]}", "none"),
                                      ("patch_repair_doserand", f"new:{d[:12]}", "deltarand")):
                    add(run=1 + di, phase="patch", condition=f"{cond}_{scope}", direction="repair", scope=scope,
                        donor=d, host=h, layer=L, target_scene=h, target_arm="new",
                        patch={"layer": L, "span": spans[(h, "new")], "source": src, "transform": tr, "rows": scope,
                               "delta_target": f"new:{h[:12]}" if tr == "deltarand" else None,
                               "seed": seed_of("E-repair", d, h, L, scope) if tr == "deltarand" else None})
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, 5)] == PLAN and len(rows) == 304, f"plan {dict(per_run)}")

    design = {
        "schema": "JEV_A461_G5_G2_STAGE_E_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_STAGE_E_FORWARD",
        "inputs": {"stage_a_raw_blob": BLOB_STAGE_A_RAW, "stage_d_design_blob": BLOB_STAGE_D_DESIGN,
                   "stage_d_manifest_blob": file_blob(a.stage_d_manifest)},
        "motivation": "Stage-D erratum: C-row-only patches cannot reach certificate_action (separate causal row). "
                      "Stage-D L11 repair flipped the C readout specifically in 10/32 cells across all 7 host groups.",
        "donors": ddesign["D2_repair"]["donors"], "donor_action_margin": donor_A,
        "hosts": ddesign["D2_repair"]["hosts"], "host_action_margin_new": host_A,
        "settings": [{"layer": L, "scope": s} for L, s in SETTINGS],
        "row_semantics": "scope action = only the certificate_action row's span copy; scope all = every question "
                         "row; each row is patched with the SAME row's span from the source capture",
        "plan": PLAN, "total": len(rows),
        "preregistered_analysis": {
            "action_margin": "A = logit(reject_conflict) - max(logit(accept), logit(wait)); REJECT iff A > 0; dA vs "
                             "the Stage-A host new baseline",
            "cell": "(donor, host, setting): SPECIFIC_REJECT iff main REJECT and neither SA-sham nor dose-random "
                    "REJECT; DOSE_SPECIFIC_A iff dA_main > dA_dose",
            "primary": "per setting: SPECIFIC_REJECT cells /32 with donor/host group coverage; action-level "
                       "correction is claimed iff in some setting SPECIFIC_REJECT cells involve >= 2 donor groups "
                       "and >= 2 host groups",
            "reachability_checks": "scope action: every non-action row logits bitwise == baseline (C unchanged); "
                                   "scope all at L11: C-row outcome reported against Stage-D C-row-only results",
            "secondary": "dA medians per arm and setting; C flips in scope all; A vs M coupling per cell",
            "units": "source groups (3 donor, 7 host); cells not independent; counts are descriptive"},
        "gpu_status": "0 Stage-E forwards; needs the user's explicit approval of 304 calls / [88, 72, 72, 72]"}
    out.mkdir(mode=0o700)
    with (out / "stage_e_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "stage_e_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("stage_e_design.json", "stage_e_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "plan": [per_run[k] for k in range(1, 5)],
                      "host_A": {h[:8]: round(v, 2) for h, v in host_A.items()},
                      "manifest_blob": file_blob(out / "stage_e_manifest.jsonl"),
                      "design_blob": file_blob(out / "stage_e_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
