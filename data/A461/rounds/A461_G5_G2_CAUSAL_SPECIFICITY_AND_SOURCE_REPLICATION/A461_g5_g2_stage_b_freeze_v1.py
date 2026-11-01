#!/usr/bin/env python3
"""A461-G5-G2 Stage-B CPU freeze: donor x host causal patching design (zero GPU).

Inputs (all pinned): Stage-A raw GPU rows (blob 680a7811, 378 rows), Stage-A
per-scene analysis, frozen roster (blob 1bc84bf5), G5V2 questions (66c1f95e),
corpus (sha 2920e1c9). Outputs: stage_b_design.json (preregistered analysis
and decision rules), stage_b_manifest.jsonl (one row per physical call), and
stage_b_spans.json (fresh-encode verified spans), plus SHA256SUMS.

Design (frozen here, before any Stage-B forward):
- donors D: the 4 strict Stage-A donors (C old=F, new=T, SA=F), W31, accept cell.
- hosts H: 4 Stage-A FFF scenes (C=F on all arms) of the accept cell, from 4
  distinct source groups outside the donor groups; first 4 by scene SHA. The
  SAME hosts serve every donor (crossed 4 x 4 design).
- layers L: outputs of full-attention layers 7, 11, 15 (11 replicates the
  pilot; 23 excluded: a last-layer patch at non-readout positions is a
  structural exact null).
- per donor one batch of F(4,3) = 4 + 4H + 8HL = 116 calls; 4 batches = 464.
"""
import argparse, collections, gzip, hashlib, json, random, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
BASE = ROOT / "kev08b-smoke-20261001-153041/models/base"
SOURCE = ROOT / "a5-secjev08b-exact-parent-20261005/source/kev"
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_G5V2 = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
BLOB_STAGE_A_RAW = "680a78116e8099b19ef11298326587d7d8e76fd0"
LAYERS = [7, 11, 15]
IDENTITY_LAYER = 11
WIDTH = 31
N_HOSTS = 4
PER_DONOR = 4 + 4 * N_HOSTS + 8 * N_HOSTS * len(LAYERS)


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


def git_blob(repo, sha):
    return subprocess.run(["git", "-C", str(repo), "cat-file", "blob", sha], capture_output=True, text=True,
                          check=True).stdout


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def seed_of(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode("utf8")).hexdigest()[:12], 16)


def perm_of(seed):
    p = list(range(WIDTH))
    random.Random(seed).shuffle(p)
    ck(p != list(range(WIDTH)), "identity permutation")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--stage-a-per-scene", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    ck(sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(file_blob(a.stage_a_raw) == BLOB_STAGE_A_RAW, "Stage-A raw blob pin")
    raw = [json.loads(x) for x in a.stage_a_raw.read_text("utf8").splitlines() if x.strip()]
    per = [json.loads(x) for x in a.stage_a_per_scene.read_text("utf8").splitlines() if x.strip()]
    ck(len(raw) == 378 and len(per) == 124, "Stage-A shapes")
    roster = {r["scene_sha256"]: r for r in json.loads(git_blob(repo, BLOB_ROSTER))["candidates"]}
    q_tw = json.loads(git_blob(repo, BLOB_G5V2).splitlines()[0])["native_request"]["questions"]
    stage_a_idx = {(r["scene_sha256"], r["arm"]): r["forward_index"] for r in raw if r["kind"] == "primary"}

    def margin(row):
        c = next(q for q in row["questions"] if q["id"] == "conflicting_vote")
        return c["logits"][c["keys"].index("true")] - c["logits"][c["keys"].index("false")]
    by_idx = {r["forward_index"]: r for r in raw}
    # recompute patterns from raw (independent of the per-scene file) and cross-check
    pat = {}
    for s in {r["scene_sha256"] for r in raw if r["kind"] == "primary"}:
        pat[s] = "".join("T" if margin(by_idx[stage_a_idx[(s, arm)]]) > 0 else "F" for arm in ("old", "new", "SA"))
    ck(all(pat[x["scene_sha256"]] == x["pattern"] for x in per), "per-scene file != raw recompute")

    donors = sorted([x for x in per if x["pattern"] == "FTF"], key=lambda x: x["scene_sha256"])
    ck(len(donors) == 4 and all(x["cell"] == "accept" and x["frozen_width"] == WIDTH for x in donors), "donors")
    donor_groups = {x["source_group"] for x in donors}
    hosts, used = [], set(donor_groups)
    for x in sorted([x for x in per if x["pattern"] == "FFF" and x["cell"] == "accept"], key=lambda x: x["scene_sha256"]):
        if x["source_group"] not in used:
            hosts.append(x)
            used.add(x["source_group"])
        if len(hosts) == N_HOSTS:
            break
    ck(len(hosts) == N_HOSTS, "hosts")

    # ---- fresh-encode span verification for every donor/host arm ----
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

    def states_of(s):
        r = roster[s]
        st_old = state_by[s]
        st_new = json.loads(canon(st_old))
        st_new["received_messages"].append(dict(r["declared_edit_new"]["message"]))
        st_sa = json.loads(canon(st_old))
        st_sa["received_messages"].append(dict(r["declared_edit_sa"]["message"]))
        return {"old": st_old, "new": st_new, "SA": st_sa}

    def enc_of(state):
        rendered, meta = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(canon(state))}))
        return encode(tok, rendered, max_state=8192, max_branch=8192, strict=True), meta

    spans = {}
    for x in donors + hosts:
        s = x["scene_sha256"]
        st = states_of(s)
        enc_o, _ = enc_of(st["old"])
        o_ids = enc_o["ids"][:enc_o["seg"].count(0)]
        ck(hids(enc_o["ids"]) == roster[s]["token_ids_sha256"]["old"], "old token SHA " + s[:8])
        for arm in ("new", "SA"):
            enc_a, _ = enc_of(st[arm])
            ck(hids(enc_a["ids"]) == roster[s]["token_ids_sha256"][arm], f"token SHA {s[:8]}:{arm}")
            a_ids = enc_a["ids"][:enc_a["seg"].count(0)]
            z = 0
            while z < min(len(o_ids), len(a_ids)) and o_ids[z] == a_ids[z]:
                z += 1
            w = len(a_ids) - len(o_ids)
            ck(w == WIDTH, f"width {s[:8]}:{arm} = {w}")
            ck(a_ids[z + w:] == o_ids[z:], f"trailing suffix {s[:8]}:{arm}")
            ck([z, z + w] == roster[s]["appended_span_in_state"][arm], f"span != roster {s[:8]}:{arm}")
            spans[f"{s}:{arm}"] = {"span": [z, z + w], "state_len": len(a_ids)}
        spans[f"{s}:old"] = {"state_len": len(o_ids)}

    # ---- manifest ----
    rows = []

    def add(**kw):
        rows.append(dict(forward_index=len(rows) + 1, **kw))
    for di, d in enumerate(donors, start=1):
        ds = d["scene_sha256"]
        dspan = spans[f"{ds}:new"]["span"]
        dspan_sa = spans[f"{ds}:SA"]["span"]
        add(run=di, condition="capture_donor_old_at_new_span_coords", target_scene=ds, target_arm="old",
            capture={"tag": "donor_old", "span": dspan, "overhang_allowed": True})
        add(run=di, condition="capture_donor_new", target_scene=ds, target_arm="new",
            capture={"tag": "donor_new", "span": dspan})
        add(run=di, condition="capture_donor_sa", target_scene=ds, target_arm="SA",
            capture={"tag": "donor_sa", "span": dspan_sa})
        add(run=di, condition="baseline_donor_new_unpatched", target_scene=ds, target_arm="new",
            bitwise_vs_stage_a=stage_a_idx[(ds, "new")])
        for h in hosts:
            hs = h["scene_sha256"]
            add(run=di, condition="baseline_host_sa_unpatched", target_scene=hs, target_arm="SA",
                bitwise_vs_stage_a=stage_a_idx[(hs, "SA")])
            add(run=di, condition="capture_host_sa", target_scene=hs, target_arm="SA",
                capture={"tag": f"host_sa:{hs[:12]}", "span": spans[f"{hs}:SA"]["span"]})
            add(run=di, condition="capture_host_new", target_scene=hs, target_arm="new",
                capture={"tag": f"host_new:{hs[:12]}", "span": spans[f"{hs}:new"]["span"]})
            add(run=di, condition="patch_identity_host_sa", target_scene=hs, target_arm="SA",
                patch={"layer": IDENTITY_LAYER, "span": spans[f"{hs}:SA"]["span"],
                       "source": f"host_sa:{hs[:12]}", "transform": "none"},
                bitwise_vs_condition="baseline_host_sa_unpatched")
        for h in hosts:
            hs = h["scene_sha256"]
            for L in LAYERS:
                for cond, src, tr in (("patch_restoration_donor_new_to_host_sa", "donor_new", "none"),
                                      ("patch_sasham_donor_sa_to_host_sa", "donor_sa", "none"),
                                      ("patch_permuted_donor_new_to_host_sa", "donor_new", "permute"),
                                      ("patch_normrand_donor_new_to_host_sa", "donor_new", "normrand")):
                    sd = seed_of("restoration", ds, hs, L, tr)
                    add(run=di, condition=cond, target_scene=hs, target_arm="SA", direction="restoration",
                        donor=ds, host=hs, layer=L,
                        patch={"layer": L, "span": spans[f"{hs}:SA"]["span"], "source": src, "transform": tr,
                               "seed": sd if tr != "none" else None,
                               "perm": perm_of(sd) if tr == "permute" else None})
        for h in hosts:
            hs = h["scene_sha256"]
            for L in LAYERS:
                for cond, src, tr in (("patch_suppression_host_new_to_donor_new", f"host_new:{hs[:12]}", "none"),
                                      ("patch_donorside_sasham_host_sa_to_donor_new", f"host_sa:{hs[:12]}", "none"),
                                      ("patch_permuted_host_new_to_donor_new", f"host_new:{hs[:12]}", "permute"),
                                      ("patch_normrand_host_new_to_donor_new", f"host_new:{hs[:12]}", "normrand")):
                    sd = seed_of("suppression", ds, hs, L, tr)
                    add(run=di, condition=cond, target_scene=ds, target_arm="new", direction="suppression",
                        donor=ds, host=hs, layer=L,
                        patch={"layer": L, "span": dspan, "source": src, "transform": tr,
                               "seed": sd if tr != "none" else None,
                               "perm": perm_of(sd) if tr == "permute" else None})
    per_run = collections.Counter(r["run"] for r in rows)
    ck(dict(per_run) == {k: PER_DONOR for k in range(1, 5)} and len(rows) == 4 * PER_DONOR == 464, f"budget {per_run}")
    ck(all(r["target_scene"] in {x["scene_sha256"] for x in donors + hosts} for r in rows), "targets")

    design = {
        "schema": "JEV_A461_G5_G2_STAGE_B_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_STAGE_B_FORWARD",
        "inputs": {"stage_a_raw_blob": BLOB_STAGE_A_RAW, "roster_blob": BLOB_ROSTER, "g5v2_questions_blob": BLOB_G5V2,
                   "corpus_sha256": CORPUS_SHA},
        "donors": [{k: x[k] for k in ("scene_sha256", "source_group", "cell", "M", "action")} for x in donors],
        "hosts": [{k: x[k] for k in ("scene_sha256", "source_group", "cell", "M", "action")} for x in hosts],
        "host_selection_rule": "Stage-A pattern FFF, accept cell, source group not a donor group, distinct groups, "
                               "first 4 by scene_sha256; same hosts for every donor (crossed 4x4)",
        "layers": LAYERS, "identity_layer": IDENTITY_LAYER, "width": WIDTH,
        "layer_rationale": "outputs of full-attention layers 7/11/15 (hybrid 24-layer backbone, full attention every "
                           "4th layer); 11 = pilot replication (confirmatory), 7/15 = layer profile (exploratory); 23 "
                           "excluded as a structural exact null",
        "budget": {"formula": "F(H,L) = 4 + 4H + 8HL per donor", "H": N_HOSTS, "L": len(LAYERS),
                   "per_donor_batch": PER_DONOR, "batches": [PER_DONOR] * 4, "total": len(rows), "cap_per_batch": 128},
        "controls": {
            "restoration": ["SA-sham: donor SA span (same-author duplicate, not recognized)",
                            "permuted: donor new span with a frozen position permutation",
                            "norm-matched random: Gaussian with each position rescaled to the donor new span's "
                            "per-position L2 norm (seeded)"],
            "suppression": ["donor-side SA-sham: host SA span -> donor new",
                            "permuted: host new span permuted -> donor new",
                            "norm-matched random: Gaussian rescaled to host new span per-position norms -> donor new"],
            "determinism": ["donor new and host SA baselines bitwise == Stage-A raw logits",
                            "identity self-patch at L11 bitwise == fresh baseline", "hook liveness per patch/capture"]},
        "preregistered_analysis": {
            "readout": "M = logit(conflicting_vote=true) - logit(false) on the C row; C = M > 0",
            "restoration_cell": "(donor, host, layer): dM_x = M(host SA patched by x) - M(host SA baseline); "
                                "SUPPORTIVE iff dM_main > max(dM_sasham, dM_permuted, dM_normrand); FLIP iff "
                                "M(main) > 0",
            "suppression_cell": "(donor, host, layer): dM_x = M(donor new patched by x) - M(donor new baseline); "
                                "SUPPORTIVE iff dM_main < min(dM_donorside_sasham, dM_permuted, dM_normrand); FLIP "
                                "iff M(main) < 0",
            "confirmatory": "layer 11, both directions: report supportive cells /16 and flips /16; the claim "
                            "'specific causal carrier at L11' needs supportive cells in all 3 donor source groups "
                            "and all 4 host source groups in BOTH directions, and no control with as many flips "
                            "as the main arm",
            "exploratory": "layers 7 and 15 profile; certificate_action argmax changes; span norm/cosine "
                           "statistics; per-donor and per-host breakdown",
            "independence": "statistical unit = source group (3 donor groups, 4 host groups); the 16 cells are not "
                            "independent; sign counts are descriptive",
            "negative_outcomes": ["controls flip as often as the main arm -> no specificity claim",
                                  "supportive only within one donor group -> no cross-group claim",
                                  "restoration without suppression (or vice versa) -> report one-directional only"]},
        "not_claimed": ["Key-only mediation (needs a separate K/Q component protocol)",
                        "never-seen source groups (tier-1 does not exist)"],
        "gpu_status": "0 Stage-B forwards; requires the user's explicit approval of 464 calls / 4 x 116"}
    out.mkdir(mode=0o700)
    with (out / "stage_b_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "stage_b_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "stage_b_spans.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(spans, f, sort_keys=True, indent=2)
        f.write("\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("stage_b_design.json", "stage_b_manifest.jsonl", "stage_b_spans.json"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"donors": [(x["scene_sha256"][:12], x["source_group"]) for x in donors],
                      "hosts": [(x["scene_sha256"][:12], x["source_group"], x["M"]) for x in hosts],
                      "rows": len(rows), "per_run": dict(per_run),
                      "manifest_blob": file_blob(out / "stage_b_manifest.jsonl"),
                      "design_blob": file_blob(out / "stage_b_design.json")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
