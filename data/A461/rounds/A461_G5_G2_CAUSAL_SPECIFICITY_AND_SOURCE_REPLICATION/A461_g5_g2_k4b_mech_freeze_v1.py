#!/usr/bin/env python3
"""A461-G5-G2 kev-4B mechanism replication: CPU freeze of K-B (layer scan) and generator of K-C (replication).

Answers paper audit 64faaee P0-2 (repair rests on one donor) and P1-1 (one model) on kev-4B, where the
screen (fd4bf13) found 44 strict donors in 14 groups. Two stages, both decided before any kev-4B patch:

  K-B  layer scan (this script, mode "kb"): 6 scan donors x 4 scan hosts x 7 full-attention layers
       (3, 7, 11, 15, 19, 23, 27; 31 excluded as a structural null) x {main, dose-matched random}, every
       question row patched into the host's own new span; 10 all-row captures. 346 calls in [128, 128, 90].
       Window rule (preregistered): L* = the scanned layer maximizing the median over cross-group cells of
       dM_main - dM_dose on the conflict margin; ties -> lower layer.
  K-C  replication (mode "kc", run after K-B with --layer L* taken from the K-B analysis): 14 replication
       donors (one per donor group, never a scan donor) x 8 replication hosts (never scan hosts) x {main,
       SA-sham, dose-matched random} + 5 unrecognized-conflict sources (kev-4B FFF new spans) x 8 hosts,
       all rows at L*; 41 captures. 417 calls in [128, 128, 128, 33].

Selection rules (deterministic, by scene SHA): scan donors = first donor of each of the first 6 groups (by
group name) that hold >= 2 donors; replication donors = first non-scan donor of every donor group; hosts =
kev-4B FFF scenes whose new-arm action is not reject_conflict, sorted by M_new descending, one per group:
first 8 -> replication hosts, next 4 (groups not already used) -> scan hosts; unrecognized sources = first
FFF scene (by SHA) of each of the 5 groups not used by any host. Pairs whose donor and host share a source group
are run but excluded from every preregistered count (reported separately).
"""
import argparse, collections, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
BLOB_K4B_RAW = "756e372a8b89eb5200f2baa4520e5f53282e8f09"
BLOB_K4B_PER_SCENE = "ee1ca3b8196bdb3ae02ab164d878417a2f39832f"
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
SCAN_LAYERS = [3, 7, 11, 15, 19, 23, 27]
KB_PLAN = [128, 128, 90]
KC_PLAN = [128, 128, 128, 33]


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


def select(per):
    donors = sorted([x for x in per if x["strict_qualified"]], key=lambda x: x["scene_sha256"])
    by_g = collections.defaultdict(list)
    for x in donors:
        by_g[x["source_group"]].append(x["scene_sha256"])
    scan_groups = sorted(g for g, v in by_g.items() if len(v) >= 2)[:6]
    scan_donors = [by_g[g][0] for g in scan_groups]
    rep_donors = [next(s for s in by_g[g] if s not in scan_donors) for g in sorted(by_g) if any(s not in scan_donors for s in by_g[g])]
    fff = sorted([x for x in per if x["pattern"] == "FFF" and x["action"]["new"] != "reject_conflict"],
                 key=lambda x: (-x["M"]["new"], x["scene_sha256"]))
    rep_hosts, scan_hosts, used = [], [], set()
    for x in fff:
        if x["source_group"] in used:
            continue
        if len(rep_hosts) < 8:
            rep_hosts.append(x["scene_sha256"])
        elif len(scan_hosts) < 4:
            scan_hosts.append(x["scene_sha256"])
        else:
            break
        used.add(x["source_group"])
    hosts = set(rep_hosts) | set(scan_hosts)
    unrec, ug = [], set(used)
    for x in sorted([x for x in per if x["pattern"] == "FFF" and x["scene_sha256"] not in hosts], key=lambda x: x["scene_sha256"]):
        if x["source_group"] not in ug and len(unrec) < 5:
            unrec.append(x["scene_sha256"])
            ug.add(x["source_group"])
    return scan_donors, rep_donors, scan_hosts, rep_hosts, unrec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["kb", "kc"])
    ap.add_argument("--k4b-raw", required=True, type=Path)
    ap.add_argument("--k4b-per-scene", required=True, type=Path)
    ap.add_argument("--roster", required=True, type=Path)
    ap.add_argument("--layer", type=int, help="kc only: L* from the K-B analysis")
    ap.add_argument("--kb-analysis", type=Path, help="kc only: K-B analysis JSON whose window rule gives --layer")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    ck(file_blob(a.k4b_raw) == BLOB_K4B_RAW and file_blob(a.k4b_per_scene) == BLOB_K4B_PER_SCENE
       and file_blob(a.roster) == BLOB_ROSTER, "pins")
    per = jsonl(a.k4b_per_scene)
    meta = {x["scene_sha256"]: x for x in per}
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    ref = {(r["scene_sha256"], r["arm"]): r["forward_index"] for r in jsonl(a.k4b_raw) if r["kind"] == "primary"}
    scan_donors, rep_donors, scan_hosts, rep_hosts, unrec = select(per)
    ck(len(scan_donors) == 6 and len(rep_donors) == 14 and len(scan_hosts) == 4 and len(rep_hosts) == 8 and len(unrec) == 5,
       f"selection sizes {len(scan_donors)} {len(rep_donors)} {len(scan_hosts)} {len(rep_hosts)} {len(unrec)}")
    ck(not (set(scan_donors) & set(rep_donors)) and not (set(scan_hosts) & set(rep_hosts)), "scan/replication disjoint")

    def span(s, arm):
        return roster[s]["appended_span_in_state"][arm]

    def g(s):
        return meta[s]["source_group"]
    rows = []

    def add(**kw):
        rows.append(dict(forward_index=len(rows) + 1, **kw))

    def capture(s, arm, kind, run):
        add(run=run, phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm, source_kind=kind,
            capture={"tag": f"{arm}:{s[:12]}", "span": span(s, arm), "layers": "all", "rows": "all", "save": True},
            bitwise_vs_k4b_screen=ref[(s, arm)])

    if a.mode == "kb":
        for d in scan_donors:
            capture(d, "new", "donor", 1)
        for h in scan_hosts:
            capture(h, "new", "host", 1)
        cells = [(d, h, L, arm) for d in scan_donors for h in scan_hosts for L in SCAN_LAYERS for arm in ("main", "doserand")]
        for i, (d, h, L, arm) in enumerate(cells):
            run = 1 if len(rows) < 128 else (2 if len(rows) < 256 else 3)
            add(run=run, phase="patch", condition=f"patch_kb_{arm}_all", direction="repair", scope="all", source_kind=f"donor_{arm}",
                donor=d, host=h, layer=L, cross_group=g(d) != g(h), target_scene=h, target_arm="new",
                patch={"layer": L, "span": span(h, "new"), "source": f"new:{d[:12]}", "transform": "none" if arm == "main" else "deltarand",
                       "rows": "all", "delta_target": None if arm == "main" else f"new:{h[:12]}",
                       "seed": None if arm == "main" else seed_of("KB", d, h, L)})
        plan, name, layers = KB_PLAN, "kb", SCAN_LAYERS
    else:
        ck(a.layer in SCAN_LAYERS and a.kb_analysis is not None, "kc needs --layer in the scan set and --kb-analysis")
        kb = json.loads(a.kb_analysis.read_text("utf8"))
        ck(kb.get("window_layer") == a.layer, f"--layer {a.layer} != K-B window rule result {kb.get('window_layer')}")
        L = a.layer
        for d in rep_donors:
            capture(d, "new", "donor", 1)
            capture(d, "SA", "donor", 1)
        for s in unrec:
            capture(s, "new", "unrecognized", 1)
        for h in rep_hosts:
            capture(h, "new", "host", 1)
        cells = [(d, h, arm) for d in rep_donors for h in rep_hosts for arm in ("main", "sasham", "doserand")] + \
                [(s, h, "unrecognized") for s in unrec for h in rep_hosts]
        for d, h, arm in cells:
            n = len(rows)
            run = 1 if n < 128 else (2 if n < 256 else (3 if n < 384 else 4))
            src = f"{'SA' if arm == 'sasham' else 'new'}:{d[:12]}"
            add(run=run, phase="patch", condition=f"patch_kc_{arm}_all", direction="repair", scope="all", source_kind=arm,
                donor=d, host=h, layer=L, cross_group=g(d) != g(h), target_scene=h, target_arm="new",
                patch={"layer": L, "span": span(h, "new"), "source": src, "transform": "deltarand" if arm == "doserand" else "none",
                       "rows": "all", "delta_target": f"new:{h[:12]}" if arm == "doserand" else None,
                       "seed": seed_of("KC", d, h, L) if arm == "doserand" else None})
        plan, name, layers = KC_PLAN, "kc", [L]
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(plan) + 1)] == plan and sum(plan) == len(rows), f"plan {dict(per_run)} vs {plan}")

    design = {
        "schema": f"JEV_A461_G5_G2_K4B_{name.upper()}_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_KEV4B_PATCH_FORWARD",
        "model": "kev-4B (runner module f118ea59: identity, source, loader)",
        "inputs": {"k4b_screen_raw_blob": BLOB_K4B_RAW, "k4b_per_scene_blob": BLOB_K4B_PER_SCENE, "roster_blob": BLOB_ROSTER},
        "selection": {"scan_donors": [(s, g(s)) for s in scan_donors], "replication_donors": [(s, g(s)) for s in rep_donors],
                      "scan_hosts": [(s, g(s), meta[s]["M"]["new"]) for s in scan_hosts],
                      "replication_hosts": [(s, g(s), meta[s]["M"]["new"]) for s in rep_hosts],
                      "unrecognized_sources": [(s, g(s)) for s in unrec]},
        "layers": layers, "plan": plan, "total": len(rows),
        "preregistered_analysis": {
            "readouts": "M = conflict margin; A = logit(reject_conflict) - max(accept, wait); C = M > 0; R = A > 0; "
                        "JOINT = C and R; dM, dA vs the in-run host capture (bitwise == kev-4B screen row)",
            "units": "only cross-group cells (donor group != host group) enter preregistered counts; same-group cells "
                     "reported separately; source groups are the unit; counts are descriptive decision rules",
            "K-B_window_rule": "L* = argmax over scanned layers of median over cross-group cells of (dM_main - dM_dose); "
                               "ties -> lower layer; reported with the full layer profile of dM_main, dM_dose, dA",
            "K-C1_dose_specificity": "dM_main > dM_dose in >= 75% of cross-group cells AND in a majority of cells for "
                                     ">= 10 of the 14 donor groups",
            "K-C2_sham_specificity": "dM_main > dM_sasham in >= 75% of cross-group cells",
            "K-C3_joint_generality": "SPECIFIC_JOINT = main JOINT and neither SA-sham nor dose JOINT; generality iff "
                                     "SPECIFIC_JOINT cells come from >= 7 donor groups and no donor group supplies "
                                     "> 30% of them",
            "K-C4_recognition": "JOINT rate of unrecognized sources <= one quarter of the main-arm JOINT rate",
            "always_reported": "leave-one-donor-group-out for K-C1..K-C3, per-host results, flip rates of every arm "
                               "(kev-4B margins are small, so flips are cheap; specificity is judged by contrasts)"},
        "gpu_status": f"0 kev-4B patch forwards; needs the user's explicit approval of {len(rows)} calls / {plan}"}
    out.mkdir(mode=0o700)
    with (out / f"k4b_{name}_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / f"k4b_{name}_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in (f"k4b_{name}_design.json", f"k4b_{name}_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"mode": name, "rows": len(rows), "plan": [per_run[k] for k in range(1, len(plan) + 1)],
                      "cross_group_patch_cells": sum(1 for r in rows if r.get("cross_group")),
                      "patch_cells": sum(1 for r in rows if r["phase"] == "patch"),
                      "scan_donor_groups": [g(s)[-7:] for s in scan_donors], "rep_donor_groups": [g(s)[-7:] for s in rep_donors],
                      "scan_hosts": [(g(s)[-7:], round(meta[s]["M"]["new"], 2)) for s in scan_hosts],
                      "rep_hosts": [(g(s)[-7:], round(meta[s]["M"]["new"], 2)) for s in rep_hosts],
                      "unrec_groups": [g(s)[-7:] for s in unrec],
                      "manifest_blob": file_blob(out / f"k4b_{name}_manifest.jsonl"),
                      "design_blob": file_blob(out / f"k4b_{name}_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
