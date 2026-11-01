#!/usr/bin/env python3
"""A461-G5-G2 Stage-F CPU freeze (zero GPU): semantic negative controls for the repair result.

Answers paper-audit 64faaee P1-3 (decision-class prototype), P0-1 (content vs recognition) and P0-2
(joint C-and-A repair dominated by one donor). Same 8 near-threshold hosts as Stages D/E; layer 11;
every question row patched (scope "all") so the conflict readout C and the certificate action A are
measured in the same forward. Source spans (all W = 31, natural activations of real scenes):
  donor_new  - the 4 strict donors' recognized new spans            (replicates Stage E bitwise)
  donor_sa   - the 4 donors' SA spans                                (replicates Stage E bitwise)
  ttt_new    - new spans of TTT scenes (C true on every arm, action reject_conflict): conflict content
               in a scene the model already reads as a conflict
  ttt_sa     - SA spans of the same TTT scenes: duplicate-vote content in a scene read as a conflict,
               SA arm itself reads C true and reject_conflict -> CLASS-MATCHED, CONTENT-MISMATCHED
  fff_new    - new spans of FFF scenes (appended conflict missed): conflict content, NOT recognized
TTT and FFF sources come only from groups that contain no host and no donor. Captures (bitwise replays
of Stage-A rows, or of the Stage-D screen rows for the D1 TTT scenes) store every row's span copy.
"""
import argparse, collections, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
BLOB_STAGE_A_RAW = "680a78116e8099b19ef11298326587d7d8e76fd0"
BLOB_STAGE_E_DESIGN = "af68448c27ebbb04a59a8691d4b6c23447fdf6b0"
BLOB_STAGE_E_RAW = "932cf380c4e4699a902aa01f5685bd7ddc80d0c8"
LAYER = 11
PLAN = [104, 64, 64, 64]


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


def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--stage-a-per-scene", required=True, type=Path)
    ap.add_argument("--stage-d-analysis", required=True, type=Path)
    ap.add_argument("--stage-d-raw", required=True, type=Path)
    ap.add_argument("--stage-d-manifest", required=True, type=Path)
    ap.add_argument("--stage-e-design", required=True, type=Path)
    ap.add_argument("--stage-e-raw", required=True, type=Path)
    ap.add_argument("--roster", required=True, type=Path, help="roster JSON (blob 1bc84bf5) for spans of new sources")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    ck(file_blob(a.stage_a_raw) == BLOB_STAGE_A_RAW and file_blob(a.stage_e_design) == BLOB_STAGE_E_DESIGN
       and file_blob(a.stage_e_raw) == BLOB_STAGE_E_RAW and file_blob(a.roster) == "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8",
       "pins")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    per = {x["scene_sha256"]: x for x in jsonl(a.stage_a_per_scene)}
    d1 = {x["scene_sha256"]: x for x in json.loads(a.stage_d_analysis.read_text("utf8"))["D1_scenes"]}
    edes = json.loads(a.stage_e_design.read_text("utf8"))
    donors = [x["scene_sha256"] for x in edes["donors"]]
    hosts = [x["scene_sha256"] for x in edes["hosts"]]
    excluded = {x["source_group"] for x in edes["donors"]} | {x["source_group"] for x in edes["hosts"]}

    # baselines for bitwise replay of every captured arm: Stage-A rows, or Stage-D screen rows (D1 scenes)
    ref = {}
    for r in jsonl(a.stage_a_raw):
        if r["kind"] == "primary":
            ref[(r["scene_sha256"], r["arm"])] = ("A", r["forward_index"])
    for r in jsonl(a.stage_d_raw):
        if r["condition"].startswith("screen_"):
            ref[(r["target_scene"], r["target_arm"])] = ("D", r["forward_index"])

    pool = {**{s: dict(x, origin="A") for s, x in per.items()}, **{s: dict(x, origin="D1") for s, x in d1.items()}}
    ttt = sorted([s for s, x in pool.items() if x["pattern"] == "TTT" and x["source_group"] not in excluded
                  and roster[s]["frozen_width"] == 31], key=lambda s: s)
    fff_all = sorted([s for s, x in per.items() if x["pattern"] == "FFF" and s not in hosts
                      and x["source_group"] not in excluded], key=lambda s: s)
    fff, seen = [], set()
    for s in fff_all:                                   # one per group, first by scene SHA
        if per[s]["source_group"] not in seen:
            fff.append(s)
            seen.add(per[s]["source_group"])
    ck(len(ttt) == 9 and len(fff) == 6, f"sources ttt={len(ttt)} fff={len(fff)}")
    ck(all(pool[s]["action"]["SA"] == "reject_conflict" and pool[s]["M"]["SA"] > 0 for s in ttt),
       "TTT SA arms must read C true and reject_conflict (class-matched control)")

    def span(s, arm):
        return roster[s]["appended_span_in_state"][arm]
    # Stage-E rows to replicate bitwise (all-row scope, layer 11, main and SA-sham)
    erows = {(r["condition"], r["donor"], r["host"]): r["forward_index"] for r in jsonl(a.stage_e_raw)
             if r.get("scope") == "all" and r.get("layer") == 11}
    ck(len([k for k in erows if k[0] in ("patch_repair_main_all", "patch_repair_sasham_all")]) == 64, "Stage-E refs")
    # spans of hosts/donors must equal the spans frozen in Stage D/E
    dspans = {(m["target_scene"], m["target_arm"]): m["capture"]["span"] for m in jsonl(a.stage_d_manifest) if m.get("capture")}
    ck(all(dspans[(s, arm)] == span(s, arm) for (s, arm) in dspans), "roster spans != Stage-D spans")

    rows = []

    def add(**kw):
        rows.append(dict(forward_index=len(rows) + 1, **kw))
    captures = ([(d, arm, "donor") for d in donors for arm in ("new", "SA")] + [(s, arm, "ttt") for s in ttt for arm in ("new", "SA")]
                + [(s, "new", "fff") for s in fff] + [(h, "new", "host") for h in hosts])
    for s, arm, kind in captures:
        src, idx = ref[(s, arm)]
        add(run=1, phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm, source_kind=kind,
            capture={"tag": f"{arm}:{s[:12]}", "span": span(s, arm), "layers": "all", "rows": "all", "save": True},
            **({"bitwise_vs_stage_a": idx} if src == "A" else {"bitwise_vs_stage_d": idx}))
    sources = ([("patch_repair_main_all", d, "new", "donor_new") for d in donors]
               + [("patch_repair_sasham_all", d, "SA", "donor_sa") for d in donors]
               + [("patch_tttnew_all", s, "new", "ttt_new") for s in ttt] + [("patch_tttsa_all", s, "SA", "ttt_sa") for s in ttt]
               + [("patch_fffnew_all", s, "new", "fff_new") for s in fff])
    for hi, h in enumerate(hosts):
        run = 1 if hi < 2 else 2 + (hi - 2) // 2
        for cond, s, arm, kind in sources:
            add(run=run, phase="patch", condition=cond, direction="repair", scope="all", source_kind=kind,
                donor=s, host=h, layer=LAYER, target_scene=h, target_arm="new",
                patch={"layer": LAYER, "span": span(h, "new"), "source": f"{arm}:{s[:12]}", "transform": "none",
                       "rows": "all", "delta_target": None, "seed": None},
                bitwise_vs_stage_e=erows.get((cond, s, h)))
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, 5)] == PLAN and len(rows) == 296, f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r.get("bitwise_vs_stage_e")) == 64, "replication rows")

    groups = {s: pool[s]["source_group"] for s in ttt + fff}
    design = {
        "schema": "JEV_A461_G5_G2_STAGE_F_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_STAGE_F_FORWARD",
        "answers": "paper audit 64faaee: P1-3 decision-class prototype, P0-1 content vs recognition, P0-2 joint repair "
                   "dominated by one donor",
        "inputs": {"stage_a_raw_blob": BLOB_STAGE_A_RAW, "stage_e_design_blob": BLOB_STAGE_E_DESIGN,
                   "stage_e_raw_blob": BLOB_STAGE_E_RAW, "stage_d_raw_blob": file_blob(a.stage_d_raw),
                   "stage_d_manifest_blob": file_blob(a.stage_d_manifest), "roster_blob": "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"},
        "hosts": edes["hosts"], "donors": edes["donors"], "layer": LAYER, "scope": "all question rows",
        "sources": {"ttt": [{"scene_sha256": s, "source_group": groups[s], "origin": pool[s]["origin"], "M": pool[s]["M"],
                             "action": pool[s]["action"]} for s in ttt],
                    "fff": [{"scene_sha256": s, "source_group": groups[s], "M": per[s]["M"], "action": per[s]["action"]}
                            for s in fff]},
        "source_rules": {"ttt": "pattern TTT, W31, source group not a host or donor group (all qualifying)",
                         "fff": "Stage-A pattern FFF, not a host, group not host/donor; first scene per group by SHA"},
        "plan": PLAN, "total": len(rows),
        "preregistered_analysis": {
            "endpoints": "per cell (source, host): C = logit(true) > logit(false) on the conflict row; R = argmax "
                         "certificate_action == reject_conflict; JOINT = C and R in the same forward",
            "H_F1_class_prototype": "content beyond decision class iff JOINT(ttt_new) - JOINT(ttt_sa) >= 5 cells (of 72) "
                                    "AND JOINT(ttt_new) >= 2 x JOINT(ttt_sa); otherwise the repair is reported as "
                                    "consistent with a positive-class-associated representation",
            "H_F2_recognition": "recognition matters iff JOINT(fff_new) <= 2 cells (of 48) AND JOINT(donor_new) - "
                                "JOINT(fff_new) >= 5 cells",
            "H_F3_source_diversity": "joint repair from recognized conflict spans beyond run-140 iff ttt_new JOINT cells "
                                     "come from >= 3 source groups and >= 3 host groups",
            "replication": "64 donor_new/donor_sa rows bitwise == Stage-E all-row rows; captures bitwise == Stage-A "
                           "or Stage-D screen rows",
            "reported_always": "C-only, R-only and JOINT counts per source kind, per source group and per host; "
                               "leave-one-source-group-out for every kind",
            "units": "source groups; cells share sources and hosts; counts are descriptive decision rules"},
        "gpu_status": "0 Stage-F forwards; needs the user's explicit approval of 296 calls / [104, 64, 64, 64]"}
    out.mkdir(mode=0o700)
    with (out / "stage_f_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "stage_f_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("stage_f_design.json", "stage_f_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "plan": [per_run[k] for k in range(1, 5)],
                      "ttt": [(s[:10], groups[s][-7:]) for s in ttt], "fff": [(s[:10], groups[s][-7:]) for s in fff],
                      "manifest_blob": file_blob(out / "stage_f_manifest.jsonl"),
                      "design_blob": file_blob(out / "stage_f_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
