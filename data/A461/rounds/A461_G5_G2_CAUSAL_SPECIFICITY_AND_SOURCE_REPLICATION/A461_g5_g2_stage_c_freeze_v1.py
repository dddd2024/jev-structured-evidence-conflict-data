#!/usr/bin/env python3
"""A461-G5-G2 Stage-C CPU freeze (zero GPU): dose-matched specificity, layer
localization 11-14, and span-encoding measurement.

Inputs (pinned): Stage-A raw (680a7811), Stage-B design (fd2a48b3), Stage-B
raw (801c4a0e), roster (1bc84bf5), G5V2 questions (66c1f95e), corpus.
Outputs: stage_c_design.json (preregistered), stage_c_manifest.jsonl,
SHA256SUMS.

Phase 1 - capture (batches 1-2, 124 + 124): for every Stage-A scene (124) the
  new and SA arms, capturing the C-row appended span at the outputs of ALL 24
  layers (saved to disk); each capture forward is also a bitwise replay of the
  Stage-A arm.
Phase 2 - patching (batches 3-6, one per donor, 112 each): the Stage-B 4x4
  donor x host pairs at layers 11, 12, 13, 14:
  restoration -> host SA: main (donor new span), SA-sham (donor SA span),
    dose-matched random x2 seeds (host SA span + per-position random unit
    direction x ||donor new - host SA||)
  suppression -> donor new: main (host new span), donor-side SA-sham (host SA
    span), dose-matched random x1 (donor new + random unit x ||host new -
    donor new||)
  L11 main / SA-sham rows are bitwise replications of Stage-B rows.
Total 248 + 448 = 696 calls in [124, 124, 112, 112, 112, 112].
"""
import argparse, collections, gzip, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_G5V2 = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
BLOB_STAGE_A_RAW = "680a78116e8099b19ef11298326587d7d8e76fd0"
BLOB_STAGE_B_DESIGN = "fd2a48b3384e08170676c3c90f95efb41c914eee"
BLOB_STAGE_B_RAW = "801c4a0eb790cf37db3a83018be178dda97bd28e"
PATCH_LAYERS = [11, 12, 13, 14]
CAPTURE_LAYERS = list(range(24))
WIDTH = 31
PLAN = [124, 124, 112, 112, 112, 112]


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def hids(v):
    return hashlib.sha256(json.dumps(v, ensure_ascii=False).encode("utf8")).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def git_blob(repo, sha):
    return subprocess.run(["git", "-C", str(repo), "cat-file", "blob", sha], capture_output=True, text=True,
                          check=True).stdout


def seed_of(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode("utf8")).hexdigest()[:12], 16)


def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text("utf8").splitlines() if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--stage-b-design", required=True, type=Path)
    ap.add_argument("--stage-b-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    ck(sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    for p, b in ((a.stage_a_raw, BLOB_STAGE_A_RAW), (a.stage_b_design, BLOB_STAGE_B_DESIGN),
                 (a.stage_b_raw, BLOB_STAGE_B_RAW)):
        ck(file_blob(p) == b, f"pin {p.name}")
    sa_raw = jsonl(a.stage_a_raw)
    sb_raw = jsonl(a.stage_b_raw)
    bdesign = json.loads(a.stage_b_design.read_text("utf8"))
    roster = {r["scene_sha256"]: r for r in json.loads(git_blob(repo, BLOB_ROSTER))["candidates"]}
    q_tw = json.loads(git_blob(repo, BLOB_G5V2).splitlines()[0])["native_request"]["questions"]
    sa_idx = {(r["scene_sha256"], r["arm"]): r["forward_index"] for r in sa_raw if r["kind"] == "primary"}
    scenes = sorted({s for s, _ in sa_idx})
    ck(len(scenes) == 124, "Stage-A scenes")
    donors = [x["scene_sha256"] for x in bdesign["donors"]]
    hosts = [x["scene_sha256"] for x in bdesign["hosts"]]

    # fresh-encode span verification for all 124 scenes x {new, SA}
    sys.path.insert(0, str(SOURCE))
    from kev.api import SystemOneRequest, to_record
    from kev.model import encode
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(BASE))
    state_by = {}
    with gzip.open(CORPUS, "rt", encoding="utf8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                if rec["_meta"].get("source") == "twins_streamlet":
                    state_by[hashlib.sha256(canon(rec["state"]).encode("utf8")).hexdigest()] = rec["state"]

    def enc_ids(state):
        rendered, _ = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
        e = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
        return e["ids"], e["ids"][:e["seg"].count(0)]
    spans = {}
    for s in scenes:
        r = roster[s]
        full_o, o_ids = enc_ids(state_by[s])
        ck(hids(full_o) == r["token_ids_sha256"]["old"], "old SHA " + s[:8])
        for arm, key in (("new", "declared_edit_new"), ("SA", "declared_edit_sa")):
            st = json.loads(canon(state_by[s]))
            st["received_messages"].append(dict(r[key]["message"]))
            full, ids = enc_ids(st)
            ck(hids(full) == r["token_ids_sha256"][arm], f"SHA {s[:8]}:{arm}")
            z = 0
            while z < min(len(o_ids), len(ids)) and o_ids[z] == ids[z]:
                z += 1
            ck(len(ids) - len(o_ids) == WIDTH and ids[z + WIDTH:] == o_ids[z:], f"span {s[:8]}:{arm}")
            ck([z, z + WIDTH] == r["appended_span_in_state"][arm], f"span != roster {s[:8]}:{arm}")
            spans[(s, arm)] = [z, z + WIDTH]

    # Stage-B rows to replicate bitwise at L11
    sb_rep = {}
    for r in sb_raw:
        if r.get("layer") == 11 and r["condition"] in (
                "patch_restoration_donor_new_to_host_sa", "patch_sasham_donor_sa_to_host_sa",
                "patch_suppression_host_new_to_donor_new", "patch_donorside_sasham_host_sa_to_donor_new"):
            sb_rep[(r["condition"], r["donor"], r["host"])] = r["forward_index"]
    ck(len(sb_rep) == 64, "Stage-B L11 replication rows")

    rows = []

    def add(**kw):
        rows.append(dict(forward_index=len(rows) + 1, **kw))
    cap_order = [(s, arm) for s in scenes for arm in ("new", "SA")]
    for i, (s, arm) in enumerate(cap_order):
        add(run=1 if i < 124 else 2, phase="capture", condition=f"capture_{arm}_all_layers", target_scene=s,
            target_arm=arm, capture={"tag": f"{arm}:{s[:12]}", "span": spans[(s, arm)], "layers": "all", "save": True},
            bitwise_vs_stage_a=sa_idx[(s, arm)])
    for di, d in enumerate(donors, start=3):
        for h in hosts:
            for L in PATCH_LAYERS:
                for cond, src, tr, seed_tag in (
                        ("patch_restoration_donor_new_to_host_sa", f"new:{d[:12]}", "none", None),
                        ("patch_sasham_donor_sa_to_host_sa", f"SA:{d[:12]}", "none", None),
                        ("patch_doserand_s1_to_host_sa", f"new:{d[:12]}", "deltarand", "s1"),
                        ("patch_doserand_s2_to_host_sa", f"new:{d[:12]}", "deltarand", "s2")):
                    add(run=di, phase="patch", condition=cond, direction="restoration", donor=d, host=h, layer=L,
                        target_scene=h, target_arm="SA",
                        patch={"layer": L, "span": spans[(h, "SA")], "source": src, "transform": tr,
                               "delta_target": f"SA:{h[:12]}" if tr == "deltarand" else None,
                               "seed": seed_of("C-restoration", d, h, L, seed_tag) if seed_tag else None},
                        bitwise_vs_stage_b=sb_rep.get((cond, d, h)) if L == 11 else None)
                for cond, src, tr, seed_tag in (
                        ("patch_suppression_host_new_to_donor_new", f"new:{h[:12]}", "none", None),
                        ("patch_donorside_sasham_host_sa_to_donor_new", f"SA:{h[:12]}", "none", None),
                        ("patch_doserand_s1_to_donor_new", f"new:{h[:12]}", "deltarand", "s1")):
                    add(run=di, phase="patch", condition=cond, direction="suppression", donor=d, host=h, layer=L,
                        target_scene=d, target_arm="new",
                        patch={"layer": L, "span": spans[(d, "new")], "source": src, "transform": tr,
                               "delta_target": f"new:{d[:12]}" if tr == "deltarand" else None,
                               "seed": seed_of("C-suppression", d, h, L, seed_tag) if seed_tag else None},
                        bitwise_vs_stage_b=sb_rep.get((cond, d, h)) if L == 11 else None)
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, 7)] == PLAN and len(rows) == 696, f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r.get("bitwise_vs_stage_b")) == 64, "replication rows")

    design = {
        "schema": "JEV_A461_G5_G2_STAGE_C_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_STAGE_C_FORWARD",
        "inputs": {"stage_a_raw_blob": BLOB_STAGE_A_RAW, "stage_b_design_blob": BLOB_STAGE_B_DESIGN,
                   "stage_b_raw_blob": BLOB_STAGE_B_RAW, "roster_blob": BLOB_ROSTER, "g5v2_questions_blob": BLOB_G5V2,
                   "corpus_sha256": CORPUS_SHA},
        "motivation": "Stage-B (f79e30e): restoration main beat SA-sham 16/16 and permuted 16/16 but whole-span "
                      "norm-matched random only 9/16; that control is a far larger perturbation than the main "
                      "patch (span cosine ~0.85), so content vs dose is confounded. Suppression main ~ donor-side "
                      "SA-sham, suggesting the host's missed conflict span is encoded like a non-conflict span. "
                      "L15 ~ 0 in both directions.",
        "donors": bdesign["donors"], "hosts": bdesign["hosts"], "patch_layers": PATCH_LAYERS,
        "capture_layers": CAPTURE_LAYERS, "plan": PLAN, "total": len(rows),
        "dose_matched_random": "per position i: target_i + u_i * ||source_i - target_i||, u_i a seeded Gaussian "
                               "direction normalised to unit length (target = the patched arm's own span at that "
                               "layer); same per-position perturbation size as the main patch, random direction",
        "preregistered_analysis": {
            "readout": "M = logit(true) - logit(false) on the C row; dM vs the Stage-A raw baseline of the patched "
                       "arm (bitwise-replayed in phase 1)",
            "H1_dose_matched_restoration_L11": "cell SUPPORTIVE iff dM_main > max(dM_doserand_s1, dM_doserand_s2); "
                                               "content-specific at L11 iff >= 10/16 cells supportive (chance per "
                                               "cell ~1/3 if direction is irrelevant) AND every donor group has a "
                                               "supportive cell AND median(dM_main - max doserand) > 0",
            "H1b_dose_matched_suppression_L11": "cell SUPPORTIVE iff dM_main < dM_doserand_s1; reported with the "
                                                "main vs donor-side SA-sham difference (Stage-B equivalence)",
            "H2_layer_localization": "for L in 11..14: median dM_main per direction; boundary = first layer whose "
                                     "|median dM_main| < 10% of its L11 value in both directions",
            "H3_encoding": "per scene and layer: delta_s(L) = mean over span positions of h_new - h_SA (C row). "
                           "Conflict direction u(L) = normalised mean delta over donors, leave-one-donor-out for "
                           "donor scores; score p_s(L) = delta_s(L) . u(L). Prediction (encoding failure): at L11 "
                           "the median p of FFF scenes (missed) < every held-out donor's p, and AUC(FTF vs FFF) >= "
                           "0.9. Profile over all 24 layers is descriptive.",
            "replication": "64 L11 rows bitwise == Stage-B rows; 248 capture forwards bitwise == Stage-A rows",
            "units": "source groups (3 donor, 4 host); cells not independent; thresholds are descriptive "
                     "decision rules, not p-values"},
        "not_claimed": ["Key-only mediation", "never-seen source groups"],
        "gpu_status": "0 Stage-C forwards; needs the user's explicit approval of 696 calls / [124,124,112,112,112,112]"}
    out.mkdir(mode=0o700)
    with (out / "stage_c_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "stage_c_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("stage_c_design.json", "stage_c_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "plan": [per_run[k] for k in range(1, 7)],
                      "manifest_blob": file_blob(out / "stage_c_manifest.jsonl"),
                      "design_blob": file_blob(out / "stage_c_design.json"),
                      "spans_verified": len(spans)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
