#!/usr/bin/env python3
"""A461-MON-M18 R1: CPU freeze of the diagnostic-monitor capture stage (zero model forwards; tokenizer only).

Safety target chosen by the user on 2026-10-31: "S2 + diagnostic monitor". G-1 (4b69b50): NOVELTY_DELTA_TESTABLE
(narrow) - a monitor read at the causally located L11 append-span state must beat a last-token probe, activation
whitening and the model's own margins at a fixed low false-veto rate on held-out source groups.

Scenes: the 124 frozen G2 Stage-A W31 scenes (17 source groups). Arms per scene (plain forwards, no patch):
  old       the original state (Gold accept / wait; legal or insufficient evidence)
  new       + the lawful equivocation vote (Gold reject_conflict)
  SA        + a duplicate of an existing vote (Gold = old)
  ROUND     + host new's vote with the round set to a non-candidate round (Gold = old)
  OUTSIDER  + host new's vote with the author set to a non-validator (Gold = old)
ROUND / OUTSIDER are generated here with the G1.0 rule (A461_mech_g10_cpu_gate_v1.py: the nearest value whose
two oracles agree with the old Gold and whose span keeps the frozen width with every other token unchanged); a scene
without such a value has no row for that arm. The monitored span is the last received-message item: the appended
item for new / SA / ROUND / OUTSIDER (31 tokens), and the old state's last item for old. Anchors: every old / new /
SA forward must equal the pinned kev-4B Stage-A raw row bitwise (runner, fail-closed on the GPU).
"""
import argparse, collections, gzip, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
WORK = ROOT / "a461-g5-minimal-patch-pilot-20261025-v1"
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_STAGE_A_K4B_RAW = "756e372a8b89eb5200f2baa4520e5f53282e8f09"
BLOB_G5V2 = "66c1f95e"
ARMS = ("old", "new", "SA", "ROUND", "OUTSIDER")
SPAN_W = 31
FIELD_MARKS = {2: " author", 6: "\n", 8: " block", 12: "\n", 14: " kind", 17: "\n", 19: " received", 24: "\n",
               26: " round", 30: "\n"}
RESID_LAYERS = [3, 7, 11, 15, 19, 23, 27, 31]   # outputs of these decoder layers (the full-attention layers)
HEAD_LAYER = 11
WRITER_HEADS = list(range(8, 15))                # M3 / M10: the L11 writer heads
PLAN_CAP = 128

PREREG = {
    "labels": "y = 1 iff Gold certificate_action = reject_conflict (arm new); y = 0 for old, SA, ROUND, OUTSIDER "
              "(Gold accept / wait, conflicting_vote false)",
    "evaluation_sets": "MISSED = new rows whose native kev-4B action is not reject_conflict (the safety-relevant "
                       "false accepts); BENIGN = old, SA, ROUND, OUTSIDER rows whose native action is not "
                       "reject_conflict (kev-4B natural false veto is 0, S2 note); per-variant FPR always reported",
    "features": "SPAN_ATTN11 = L11 o_proj input (the attention write, all heads) averaged over the monitored span; "
                "SPAN_ATTN11_W = its writer-head slice (heads 8-14); SPAN_RESID_L = residual stream after layer L "
                "averaged over the span, L in {emb (input of layer 0), 3, 7, 11, 15, 19, 23, 27, 31}; LAST_RESID_L "
                "= residual after layer L at the decision position of the certificate_action row (the row's last "
                "token, where the head reads; the generic last-token probe of 2608.27750); MARGINS = native (M, A)",
    "detectors": "PROBE(f): standardised (train-fold mean / sd, sd floored at 1e-6) L2 logistic regression with "
                 "loss = sum of the training rows' log loss + 0.5 ||w||^2 (the sklearn C = 1 convention of 2608.27750), "
                 "bias unpenalised, full-batch LBFGS (strong Wolfe) in float64, 200 iterations, zero init "
                 "(deterministic); WHITEN(f): PCA whitening, k = 15, "
                 "fit on the train-fold BENIGN rows only, score = whitened norm (2512.03994); NATIVE: score = A, and "
                 "score = M, untrained",
    "split": "leave one source group out over the 17 groups; every score is a held-out score; a fold's thresholds "
             "come from its own training rows only",
    "operating_points": "per outer fold, the threshold is the 95th (FV5) and 99th (FV1) percentile ('higher' "
                        "interpolation) of the training groups' BENIGN scores, each scored out of sample by an inner "
                        "leave-one-group-out over the training groups (a probe's in-sample scores would set the "
                        "threshold too low; the same rule applies to every detector, NATIVE included); TPR_missed@FVk = share of held-out MISSED rows above it; FPR@FVk = share of "
                        "held-out BENIGN rows above it, overall and per arm; AUROC(MISSED vs BENIGN) on the pooled "
                        "held-out scores",
    "uncertainty": "percentile cluster bootstrap over source groups (10000) for every metric and every difference; "
                   "for false veto also the group-level count of groups with >= 1 held-out false positive, with its "
                   "Clopper-Pearson one-sided 95% upper bound (A612: 0/17 groups bounds the group rate by 16.2%, not 0)",
    "V1_encoded": "ENCODED_AT_L11 iff AUROC(PROBE SPAN_ATTN11) >= 0.90 and its bootstrap lower bound >= 0.80; "
                  "NOT_ENCODED_AT_L11 iff AUROC <= 0.70; else PARTIAL. ABOVE_SURFACE iff AUROC(SPAN_ATTN11) - "
                  "AUROC(SPAN_RESID_emb) >= 0.05 with bootstrap lower bound > 0; SURFACE_SUFFICES iff AUROC(SPAN_RESID_"
                  "emb) >= AUROC(SPAN_ATTN11) - 0.02; else SURFACE_UNRESOLVED",
    "V2_location": "a detector is CALIBRATED iff its pooled held-out FPR@FV5 <= 0.10 (twice the target). G = the "
                   "best CALIBRATED generic detector by TPR_missed@FV5 among PROBE(LAST_RESID_L) for every L, WHITEN("
                   "LAST_RESID_11), WHITEN(LAST_RESID_31), NATIVE A and NATIVE M (chosen on the same held-out scores: this "
                   "favours the baselines). LOCATION_ADVANTAGE iff TPR_missed@FV5(PROBE SPAN_ATTN11) - TPR(G) >= 0.10 "
                   "with bootstrap lower bound > 0 -> NOVELTY_DELTA_SURVIVES; GENERIC_MATCHES iff TPR(G) >= TPR("
                   "SPAN_ATTN11) - 0.02 -> INFRASTRUCTURE_VALIDATION_ONLY; else UNRESOLVED; if the span monitor itself is not "
                   "CALIBRATED: SPAN_MISCALIBRATED (no novelty claim); if no generic detector is CALIBRATED: "
                   "NO_CALIBRATED_GENERIC (compared against NATIVE A regardless, reported)",
    "V3_useful": "MONITOR_USEFUL iff at FV1 the span monitor has TPR_missed >= 0.5 and held-out FPR <= 0.05 on every "
                 "benign arm; else NOT_USEFUL_AT_FV1",
    "reported_not_verdicts": "AUROC by layer for SPAN_RESID_L and LAST_RESID_L (where the conflict becomes decodable); "
                             "per-arm FPR (ROUND and OUTSIDER are the near misses where M17 found the L11 write and "
                             "the action come apart); detection of the RECOGNIZED new rows; leave-one-group-out is the "
                             "split itself",
    "consistency_gate": "every old / new / SA forward's logits equal the pinned kev-4B Stage-A raw row bitwise "
                        "(runner, GPU); every forward's token sha equals the frozen one; the span cross-row max "
                        "difference is 0 for every saved feature; otherwise every verdict is INCONSISTENT",
    "interpretation_fixed_in_advance": (
        "ENCODED_AT_L11 + ABOVE_SURFACE: the conflict is linearly decodable from the L11 append-span write even in "
        "the scenes whose action misses it - evidence for H-READ (present but not acted on) over H-ENC for those "
        "scenes; NOT_ENCODED: H-ENC at L11. LOCATION_ADVANTAGE: the causally located monitor is a contribution "
        "(P2 of A612); GENERIC_MATCHES: infrastructure only. A monitor is a check on the learned scorer, never a "
        "replacement for the deterministic rule (0 errors). Level S2 (native action, source-internal Gold); no "
        "deployment claim; 124 scenes in 17 groups, so group-level uncertainty dominates"),
}


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--roster", required=True, type=Path)
    ap.add_argument("--stage-a-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.stage_a_raw) == BLOB_STAGE_A_K4B_RAW, "pins")
    spec = importlib.util.spec_from_file_location("sa", WORK / "A461_g5_g2_stage_a_cpu_freeze_v1.py")
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    ck(sha_file(sa.CORPUS) == sa.CORPUS_SHA, "corpus pin")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    rawA = [json.loads(x) for x in a.stage_a_raw.read_text("utf8").splitlines() if x.strip()]
    prim = {(x["scene_sha256"], x["arm"]): x for x in rawA if x.get("kind") == "primary"}
    scenes_sel = sorted({s for s, _ in prim})
    ck(len(scenes_sel) == 124 and len(prim) == 372, "124 Stage-A scenes x old / new / SA")
    repo = a.repo_root.expanduser().resolve(strict=True)
    g5_full = subprocess.run(["git", "-C", str(repo), "rev-parse", BLOB_G5V2], capture_output=True, text=True,
                             check=True).stdout.strip()
    q_tw = json.loads(subprocess.run(["git", "-C", str(repo), "cat-file", "blob", g5_full], capture_output=True,
                                     text=True, check=True).stdout.splitlines()[0])["native_request"]["questions"]
    sys.path.insert(0, str(ROOT / "kev08b-smoke-20261001-153041/code"))
    from transformers import AutoTokenizer
    from kev.api import SystemOneRequest, to_record
    from kev.model import encode
    tok = AutoTokenizer.from_pretrained(str(ROOT / "kev4b-assets-20261002/base"))
    need = set(scenes_sel)
    states = {}
    for line in gzip.open(sa.CORPUS, "rt", encoding="utf8"):
        if line.strip():
            rec = json.loads(line)
            if rec["_meta"].get("source") == "twins_streamlet":
                sh = hashlib.sha256(sa.canon(rec["state"]).encode("utf8")).hexdigest()
                if sh in need:
                    states[sh] = rec["state"]
    ck(set(states) == need, "scene recovery")

    def enc(st):
        rendered, _ = to_record(SystemOneRequest.model_validate({"questions": q_tw, "state": json.loads(sa.canon(st))}))
        e = encode(tok, rendered, max_state=8192, max_branch=8192, strict=True)
        ck(not e["state_truncated"], "truncated")
        return e

    def with_msg(st, m):
        s = json.loads(sa.canon(st))
        s["received_messages"].append(dict(m))
        return s

    def gold(st):
        g1, sup = sa.oracle1(st)
        g2 = sa.oracle2(st)
        return (g1 if g1 == g2 else None), sup

    def item_starts(ids):
        dec = [tok.decode([t]) for t in ids]
        return [p for p in range(len(ids) - 2) if dec[p] == " " and dec[p + 1] == " -" and dec[p + 2] == " author"], dec

    def near(vals, ref):
        return sorted(vals, key=lambda v: (abs(v - ref) if isinstance(v, (int, float)) and isinstance(ref, (int, float))
                                           else 0, str(v)))

    rows, design_scenes, coverage = [], {}, collections.Counter()
    for s in scenes_sel:
        c, st = roster[s], states[s]
        ck(c["frozen_width"] == SPAN_W, f"W31 {s[:8]}")
        base = c["declared_edit_new"]["message"]
        e_old = enc(st)
        o_ids = e_old["ids"][:e_old["seg"].count(0)]
        g_old = c["oracle_old"]
        arms = {"old": (st, None), "new": (with_msg(st, base), c["oracle_new"]),
                "SA": (with_msg(st, c["declared_edit_sa"]["message"]), c["oracle_sa"])}
        # G1.0 rule: nearest value whose oracles agree with the old Gold under the frozen-width token gate
        rnd = st["candidate_round"]
        rounds_seen = {m.get("round") for m in st["received_messages"] if isinstance(m.get("round"), int)}
        round_vals = near(sorted(r for r in rounds_seen | {rnd - 1, rnd + 1, rnd + 2} if r != rnd and r >= 0), rnd)
        vs = st["validator_set"]
        prefix = "".join(ch for ch in sorted(vs)[0] if not ch.isdigit())
        outsiders = [f"{prefix}{k}" for k in range(len(vs), len(vs) + 12) if f"{prefix}{k}" not in vs]
        for arm, field, vals in (("ROUND", "round", round_vals), ("OUTSIDER", "author", outsiders)):
            for v in vals:
                m = dict(base, **{field: v})
                s_ = with_msg(st, m)
                g, _ = gold(s_)
                if g is None or g != g_old:
                    continue
                e = enc(s_)
                ids = e["ids"][:e["seg"].count(0)]
                z = 0
                while z < min(len(o_ids), len(ids)) and o_ids[z] == ids[z]:
                    z += 1
                if len(ids) - len(o_ids) != SPAN_W or ids[z + SPAN_W:] != o_ids[z:]:
                    continue
                arms[arm] = (s_, g)
                break
        entry = {"group": c["source_group"], "gold_old": g_old["certificate_action"], "arms": {}}
        s_new0 = None
        for arm in ARMS:
            if arm not in arms:
                coverage[f"{arm}_missing"] += 1
                continue
            st_a, g_a = arms[arm]
            g_chk, _ = gold(st_a)
            ck(g_chk is not None, f"oracles disagree {s[:8]}:{arm}")
            if g_a is not None:
                ck(g_chk == g_a, f"Gold {s[:8]}:{arm}")
            g_a = g_chk
            e = enc(st_a)
            ids = e["ids"][:e["seg"].count(0)]
            starts, dec = item_starts(ids)
            ck(len(starts) == len(st_a["received_messages"]), f"item starts {s[:8]}:{arm}")
            if arm == "old":
                span = None      # set after new: the old last item ends where the appended item starts
            else:
                z = 0
                while z < min(len(o_ids), len(ids)) and o_ids[z] == ids[z]:
                    z += 1
                span = [z, z + SPAN_W]
                ck(len(ids) - len(o_ids) == SPAN_W and ids[z + SPAN_W:] == o_ids[z:] and starts[-1] == z,
                   f"appended span {s[:8]}:{arm}")
                ck(all(dec[z + i_] == t_ for i_, t_ in FIELD_MARKS.items()), f"span field layout {s[:8]}:{arm}")
                if arm == "new":
                    s_new0 = z
                    ck(c["appended_span_in_state"]["new"] == span, f"roster span {s[:8]}")
            if arm in ("old", "new", "SA"):
                ck(sa.hids(e["ids"]) == c["token_ids_sha256"][arm] == prim[(s, arm)]["token_ids_sha256"],
                   f"token gate {s[:8]}:{arm}")
                ck(g_a == c[f"oracle_{arm.lower()}"], f"roster Gold {s[:8]}:{arm}")
            entry["arms"][arm] = {"gold": g_a, "token_ids_sha256": sa.hids(e["ids"]), "span": span,
                                  "state_len": len(ids), "message": st_a["received_messages"][-1],
                                  "anchor_stage_a_fi": prim[(s, arm)]["forward_index"] if arm in ("old", "new", "SA") else None}
            coverage[arm] += 1
        o_starts, _ = item_starts(o_ids)
        entry["arms"]["old"]["span"] = [o_starts[-1], s_new0]
        ck(0 < s_new0 - o_starts[-1] <= 64, f"old last item {s[:8]}")
        design_scenes[s] = entry
        for arm in ARMS:
            if arm in entry["arms"]:
                x = entry["arms"][arm]
                rows.append({"target_scene": s, "target_arm": arm, "source_group": c["source_group"],
                             "gold_action": x["gold"]["certificate_action"], "span": x["span"],
                             "token_ids_sha256": x["token_ids_sha256"], "state_len": x["state_len"],
                             "anchor_stage_a_fi": x["anchor_stage_a_fi"]})
    n = len(rows)
    plan = [PLAN_CAP] * (n // PLAN_CAP) + ([n % PLAN_CAP] if n % PLAN_CAP else [])
    for i, r in enumerate(rows):
        r.update(forward_index=i + 1, run=i // PLAN_CAP + 1, condition=f"monitor_capture_{r['target_arm']}",
                 capture={"span": r["span"], "resid_layers": RESID_LAYERS, "attn_layer": HEAD_LAYER,
                          "decision_question": "certificate_action"})
    groups = sorted({r["source_group"] for r in rows})
    ck(len(groups) == 17, "17 source groups")
    ck(sum(1 for r in rows if r["anchor_stage_a_fi"]) == 372, "372 Stage-A anchors")
    design = {"schema": "JEV_A461_MON_M18_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M18_FORWARD",
              "inputs": {"roster_blob": BLOB_ROSTER, "stage_a_k4b_raw_blob": BLOB_STAGE_A_K4B_RAW,
                         "g5v2_questions_blob": g5_full, "corpus_sha256": sa.CORPUS_SHA},
              "arms": list(ARMS), "resid_layers": RESID_LAYERS, "attn_layer": HEAD_LAYER, "writer_heads": WRITER_HEADS,
              "span_width": SPAN_W, "field_marks": FIELD_MARKS, "scenes": design_scenes, "groups": groups,
              "coverage": dict(coverage), "plan": plan, "total": n, "preregistered_analysis": PREREG,
              "gpu_status": f"0 M18 forwards; {n} calls / {len(plan)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m18_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m18_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for nm in ("m18_design.json", "m18_manifest.jsonl"):
            f.write(sha_file(out / nm) + "  " + nm + "\n")
    print(json.dumps({"rows": n, "plan": plan, "coverage": dict(coverage), "groups": len(groups),
                      "gold": dict(collections.Counter(f"{r['target_arm']}:{r['gold_action']}" for r in rows)),
                      "manifest_blob": file_blob(out / "m18_manifest.jsonl"),
                      "design_blob": file_blob(out / "m18_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
