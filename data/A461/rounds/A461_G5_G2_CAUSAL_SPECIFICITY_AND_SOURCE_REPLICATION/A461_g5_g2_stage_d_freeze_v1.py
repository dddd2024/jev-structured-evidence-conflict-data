#!/usr/bin/env python3
"""A461-G5-G2 Stage-D CPU freeze (zero GPU): donor expansion screen + near-threshold repair.

Inputs (pinned): Stage-A raw (680a7811), Stage-A per-scene (in the Stage-A archive),
Stage-B design (fd2a48b3; the 4 donors), roster (1bc84bf5), G5V2 questions, corpus.

D1 screen (batches 1-2, 71 + 70 = 141): every roster scene not screened in Stage-A
  with frozen width 31 or 34 (47 scenes; the single W32 scene stays exploratory and
  excluded), arms old/new/SA on their frozen witness. Strict qualification as in
  Stage-A, reported per width stratum.
D2 repair (batches 3-4, 112 + 96 = 208): hosts = Stage-A FFF scenes with
  M_new >= -4.0 whose source group is not a donor group (8 scenes / 7 groups, all
  choosing 'wait' on their new arm). Captures (bitwise replays of Stage-A rows):
  donor new + donor SA (4 x 2) and host new (8). Patches at layers 11 and 12 into the
  HOST'S OWN NEW (missed-conflict) span: main (donor recognized new span), SA-sham
  (donor SA span), dose-matched random (host new + seeded unit direction x
  ||donor new - host new|| per position).
Total 349 calls in [71, 70, 112, 96].
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
PATCH_LAYERS = [11, 12]
HOST_M_NEW_MIN = -4.0
PLAN = [71, 70, 112, 96]


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
    ap.add_argument("--stage-a-per-scene", required=True, type=Path)
    ap.add_argument("--stage-b-design", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    ck(sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(file_blob(a.stage_a_raw) == BLOB_STAGE_A_RAW and file_blob(a.stage_b_design) == BLOB_STAGE_B_DESIGN, "pins")
    sa_raw = jsonl(a.stage_a_raw)
    per = {x["scene_sha256"]: x for x in jsonl(a.stage_a_per_scene)}
    ck(len(per) == 124, "Stage-A per-scene")

    def margin(row):
        c = next(q for q in row["questions"] if q["id"] == "conflicting_vote")
        return c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]
    sa_idx = {(r["scene_sha256"], r["arm"]): r["forward_index"] for r in sa_raw if r["kind"] == "primary"}
    sa_by = {r["forward_index"]: r for r in sa_raw}
    ck(all(abs(margin(sa_by[sa_idx[(s, arm)]]) - per[s]["M"][arm]) < 1e-5 for s in per for arm in ("old", "new", "SA")),
       "per-scene M != raw")
    bdesign = json.loads(a.stage_b_design.read_text("utf8"))
    donors = [x["scene_sha256"] for x in bdesign["donors"]]
    donor_groups = {x["source_group"] for x in bdesign["donors"]}
    roster = {r["scene_sha256"]: r for r in json.loads(git_blob(repo, BLOB_ROSTER))["candidates"]}
    q_tw = json.loads(git_blob(repo, BLOB_G5V2).splitlines()[0])["native_request"]["questions"]

    screen = sorted([s for s, r in roster.items() if s not in per and r["frozen_width"] in (31, 34)],
                    key=lambda s: (roster[s]["frozen_width"], s))
    ck(len(screen) == 47, f"screen set {len(screen)}")
    hosts = sorted([s for s, x in per.items() if x["pattern"] == "FFF" and x["M"]["new"] >= HOST_M_NEW_MIN
                    and x["source_group"] not in donor_groups], key=lambda s: (-per[s]["M"]["new"], s))
    ck(len(hosts) == 8, f"hosts {len(hosts)}")

    # fresh-encode verification of every forwarded arm and every span
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
    for s in screen + hosts + donors:
        r = roster[s]
        W = r["frozen_width"]
        full_o, o_ids = enc_ids(state_by[s])
        ck(hids(full_o) == r["token_ids_sha256"]["old"] and len(o_ids) == r["state_token_len"]["old"], "old " + s[:8])
        for arm, key in (("new", "declared_edit_new"), ("SA", "declared_edit_sa")):
            st = json.loads(canon(state_by[s]))
            st["received_messages"].append(dict(r[key]["message"]))
            full, ids = enc_ids(st)
            ck(hids(full) == r["token_ids_sha256"][arm] and len(ids) == r["state_token_len"][arm], f"{s[:8]}:{arm}")
            z = 0
            while z < min(len(o_ids), len(ids)) and o_ids[z] == ids[z]:
                z += 1
            ck(len(ids) - len(o_ids) == W and ids[z + W:] == o_ids[z:], f"span {s[:8]}:{arm}")
            ck([z, z + W] == r["appended_span_in_state"][arm], f"span != roster {s[:8]}:{arm}")
            spans[(s, arm)] = [z, z + W]

    rows = []

    def add(**kw):
        rows.append(dict(forward_index=len(rows) + 1, **kw))
    for i, (s, arm) in enumerate([(s, arm) for s in screen for arm in ("old", "new", "SA")]):
        add(run=1 if i < 71 else 2, phase="screen", condition=f"screen_{arm}", target_scene=s, target_arm=arm,
            frozen_width=roster[s]["frozen_width"], source_group=roster[s]["source_group"], cell=roster[s]["cell"])
    for s, arm in [(d, arm) for d in donors for arm in ("new", "SA")] + [(h, "new") for h in hosts]:
        add(run=3, phase="capture", condition=f"capture_{arm}", target_scene=s, target_arm=arm,
            capture={"tag": f"{arm}:{s[:12]}", "span": spans[(s, arm)], "layers": "all", "save": True},
            bitwise_vs_stage_a=sa_idx[(s, arm)])
    for di, d in enumerate(donors):
        run = 3 if di < 2 else 4
        for h in hosts:
            for L in PATCH_LAYERS:
                for cond, src, tr in (("patch_repair_donor_new_to_host_new", f"new:{d[:12]}", "none"),
                                      ("patch_sasham_donor_sa_to_host_new", f"SA:{d[:12]}", "none"),
                                      ("patch_doserand_to_host_new", f"new:{d[:12]}", "deltarand")):
                    add(run=run, phase="patch", condition=cond, direction="repair", donor=d, host=h, layer=L,
                        target_scene=h, target_arm="new",
                        patch={"layer": L, "span": spans[(h, "new")], "source": src, "transform": tr,
                               "delta_target": f"new:{h[:12]}" if tr == "deltarand" else None,
                               "seed": seed_of("D-repair", d, h, L) if tr == "deltarand" else None})
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, 5)] == PLAN and len(rows) == 349, f"plan {dict(per_run)}")

    design = {
        "schema": "JEV_A461_G5_G2_STAGE_D_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_STAGE_D_FORWARD",
        "inputs": {"stage_a_raw_blob": BLOB_STAGE_A_RAW, "stage_b_design_blob": BLOB_STAGE_B_DESIGN,
                   "roster_blob": BLOB_ROSTER, "g5v2_questions_blob": BLOB_G5V2, "corpus_sha256": CORPUS_SHA},
        "motivation": "Stage-C (8c5608c): dose-matched restoration into host SA is content-specific 16/16 at L11, "
                      "span dependence ends at L13, but hosts sat at M ~ -11 so no readout/action changed; only 4 "
                      "donors from 3 groups.",
        "D1_screen": {"scenes": [{"scene_sha256": s, "frozen_width": roster[s]["frozen_width"],
                                  "source_group": roster[s]["source_group"], "cell": roster[s]["cell"]} for s in screen],
                      "rule": "strict: C old=F, new=T, SA=F on the frozen witness (same as Stage-A); per width",
                      "excluded": "the single W32 scene (exploratory per Option A)",
                      "expected": "~1.5 donors at the Stage-A rate 4/124; new donors feed a later stage only"},
        "D2_repair": {"donors": bdesign["donors"],
                      "hosts": [{"scene_sha256": h, "source_group": per[h]["source_group"], "cell": per[h]["cell"],
                                 "M": per[h]["M"], "action": per[h]["action"]} for h in hosts],
                      "host_rule": "Stage-A FFF, M_new >= -4.0, source group not a donor group; all qualifying (8)",
                      "target": "host's own new (missed conflict) span", "layers": PATCH_LAYERS},
        "plan": PLAN, "total": len(rows),
        "preregistered_analysis": {
            "readout": "M = logit(true) - logit(false); dM vs the Stage-A host new baseline (bitwise replayed by the "
                       "host capture); action = argmax certificate_action",
            "cell": "(donor, host, layer): C_FLIP_x iff M_x > 0; ACTION_x = argmax action; SPECIFIC_FLIP iff main "
                    "flips and neither SA-sham nor dose-random flips; SPECIFIC_REJECT iff main action == "
                    "reject_conflict and neither control's action is",
            "primary": "per layer (11 and 12; both reported, no multiplicity correction claimed): number of "
                       "SPECIFIC_FLIP and SPECIFIC_REJECT cells out of 32; behavioural correction is claimed iff, at "
                       "some layer, SPECIFIC_FLIP cells involve >= 2 donor groups and >= 2 host groups AND at least "
                       "one SPECIFIC_REJECT exists",
            "secondary": "dose specificity dM_main > dM_dose per cell (replication of Stage-C with a new target arm); "
                         "dM_main - dM_sasham; per-host flip curve vs baseline M_new",
            "D1": "strict donor count per width; groups; patterns",
            "units": "source groups; cells not independent; counts are descriptive decision rules"},
        "gpu_status": "0 Stage-D forwards; needs the user's explicit approval of 349 calls / [71, 70, 112, 96]"}
    out.mkdir(mode=0o700)
    with (out / "stage_d_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "stage_d_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("stage_d_design.json", "stage_d_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "plan": [per_run[k] for k in range(1, 5)],
                      "screen_by_width": dict(collections.Counter(roster[s]["frozen_width"] for s in screen)),
                      "hosts": [(h[:12], per[h]["source_group"], round(per[h]["M"]["new"], 2)) for h in hosts],
                      "manifest_blob": file_blob(out / "stage_d_manifest.jsonl"),
                      "design_blob": file_blob(out / "stage_d_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
