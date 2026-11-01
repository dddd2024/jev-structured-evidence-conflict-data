#!/usr/bin/env python3
"""A461-G5-G2 CPU source-group feasibility audit (P1, zero forwards).

Implements the P1 gate frozen in the post-run independent audit
(research/analysis/2026-10-25_A461_G5_PILOT_G1_POSTRUN_INDEPENDENT_RAW_LOGITS_AUDIT_V1.md,
commit 657ca25c, section 4): enumerate unused DEV source groups and scenes,
verify constructibility of new appended-conflict pairs (dual oracle, author /
timestamp / validator_set legality, same-token-width pairing), prevent
same-run edits from being counted as independent data, pre-define
confirmatory vs exploratory subsets, design the donor-side negative-control
set the pilot lacked, and derive the dynamic GPU budget formula (a planning
value, NOT an approval). Zero model loads, zero forwards.
"""
import argparse, collections, gzip, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
CORPUS = ROOT / "a5-secjev08b-preflight-20261005/assets/corpus/SecJev-Corpus/records/development.jsonl.gz"
CORPUS_SHA = "2920e1c9fd553e20458c0db1bf74db8fb7782124aa412009962c34e2e675ca56"
CKPT = ROOT / "a5-secjev08b-preflight-20261005/assets/specialist/SecJev-0.8B"

BLOB_G3_PAIRS = "8de45fc200d0e37be676f172d844b3ab2c6c23c7"
BLOB_G1_PAIRS = "24526c643434544b9a02587abc2d57e2c13ef627"
BLOB_A428_INPUTS = "13adf301dd67c5cc787c72b4b9ace695c52fef4e"
BLOB_G5V2_PAIRS = "66c1f95e58fe537ae808731f1979783f3ee96c4e"
BLOB_POSTRUN_AUDIT = "frozen in commit 657ca25c (report file)"

# observed donor-qualification base rates from archived logits (for sample sizing only)
QUALIFIED_OBSERVED = {"G3_confirmation": {"pairs": 26, "qualified": 1},
                      "G5_V2_search": {"pairs": 36, "qualified": 1}}


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def sha_file(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def h64(state):
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")).hexdigest()


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def save(p, v):
    with p.open("x", encoding="utf8", newline="\n") as f:
        json.dump(v, f, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def git_blob(repo, sha):
    t = subprocess.run(["git", "-C", str(repo), "cat-file", "-t", sha], capture_output=True, text=True)
    ck(t.returncode == 0 and t.stdout.strip() == "blob", f"not a blob: {sha}")
    return subprocess.run(["git", "-C", str(repo), "cat-file", "blob", sha],
                          capture_output=True, text=True, check=True).stdout


def oracle1(state):
    votes = collections.defaultdict(list)
    allowed = set(state["validator_set"])
    for e in state["received_messages"]:
        if (e.get("kind") == "vote" and e.get("round") == state["candidate_round"]
                and isinstance(e.get("received"), (int, float))
                and e["received"] <= state["decision_time"] and e.get("author") in allowed):
            votes[e["author"]].append(e["block"])
    support = {v for v, blocks in votes.items() if state["candidate_block"] in blocks}
    q = len(support) >= state["quorum_size"]
    c = any(any(b != state["candidate_block"] for b in votes[v]) for v in support)
    action = "reject_conflict" if c else "accept" if q else "wait"
    return {"conflicting_vote": c, "quorum": q, "certificate_action": action,
            "evidence_level": {"reject_conflict": 2, "accept": 0, "wait": 1}[action]}, sorted(support)


def oracle2(state):
    cand, rnd, dl, qsz = state["candidate_block"], state["candidate_round"], state["decision_time"], state["quorum_size"]
    per = {}
    for m in state["received_messages"]:
        if m.get("kind") != "vote" or m.get("round") != rnd or m.get("author") not in state["validator_set"]:
            continue
        r = m.get("received")
        if not isinstance(r, (int, float)) or r > dl:
            continue
        per.setdefault(m["author"], []).append(m["block"])
    n_sup = 0
    confl = False
    for a, blocks in per.items():
        if cand in blocks:
            n_sup += 1
            if any(b != cand for b in blocks):
                confl = True
    act = "reject_conflict" if confl else ("accept" if n_sup >= qsz else "wait")
    return {"conflicting_vote": confl, "quorum": n_sup >= qsz, "certificate_action": act}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo_root.expanduser().resolve(strict=True)
    out = a.out.expanduser().resolve(strict=False)
    ck(ROOT.is_dir() and sha_file(CORPUS) == CORPUS_SHA, "corpus pin")
    ck(str(out).startswith(str(ROOT)) and out.parent.is_dir() and not out.exists(), "out dir")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(ROOT / ".tmp"),
                      HF_HOME=str(ROOT / ".cache" / "huggingface"), TORCH_HOME=str(ROOT / ".cache" / "torch"),
                      XDG_CACHE_HOME=str(ROOT / ".cache"))
    receipt = {"schema": "JEV_A461_G5_G2_CPU_FEASIBILITY_RECEIPT_V1", "status": "INCOMPLETE",
               "run_id": "A461_G5_G2_CAUSAL_SPECIFICITY_SOURCE_REPLICATION_CPU_FEAS_R1",
               "gpu_forwards": 0, "model_loads": 0, "network_calls": 0, "tool_actions": 0,
               "test_or_calibration_rows": 0, "output_dir": str(out),
               "frozen_inputs": {"g3_pair_rows_blob": BLOB_G3_PAIRS, "g1_pair_rows_blob": BLOB_G1_PAIRS,
                                 "a428_inputs_blob": BLOB_A428_INPUTS, "g5v2_pair_rows_blob": BLOB_G5V2_PAIRS,
                                 "corpus_sha256": CORPUS_SHA}}
    produced = []
    try:
        out.mkdir(mode=0o700)
        # ---------- corpus census ----------
        scenes = {}
        group_of = {}
        for line in gzip.open(CORPUS, "rt", encoding="utf8"):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["_meta"].get("source") != "twins_streamlet":
                continue
            ck(rec["_meta"].get("split") == "development", "non-DEV")
            h = h64(rec["state"])
            scenes[h] = rec
            group_of[h] = rec["_meta"]["split_group_id"]
        ck(len(scenes) == 797, f"twins census {len(scenes)}")
        all_groups = sorted(set(group_of.values()))

        # ---------- used-scene ledger (append-only accounting per round) ----------
        used = {}   # sha64 -> round note
        # G5 V2: old arm = corpus state keyed by pair_key sha16 suffix
        g5rows = [json.loads(x) for x in git_blob(repo, BLOB_G5V2_PAIRS).splitlines() if x.strip()]
        by16 = {h64(r["state"])[:16]: h64(r["state"]) for r in scenes.values()}
        n_g5 = 0
        for r in g5rows:
            h16 = r["pair_key"].split(":", 1)[1]
            h = by16.get(h16)
            ck(h is not None, "g5 old scene missing " + r["pair_key"])
            if h not in used:
                used[h] = "G5_V2_donor_resolution"
            n_g5 += 1
        # G3: old state = new-arm state minus its appended last message (audited method)
        g3rows = [json.loads(x) for x in git_blob(repo, BLOB_G3_PAIRS).splitlines() if x.strip()]
        n_g3 = 0
        for r in g3rows:
            if r["arm"] != "new":
                continue
            st = json.loads(canon(r["native_request"]["state"]))
            st["received_messages"].pop()
            h = h64(st)
            ck(h in scenes, "g3 reconstructed old not in corpus " + r["pair_key"])
            used.setdefault(h, "G3_confirmation")
            n_g3 += 1
        # G1 pilot: same pop-last method on every twins arm with an appended-edit state
        g1rows = [json.loads(x) for x in git_blob(repo, BLOB_G1_PAIRS).splitlines() if x.strip()]
        n_g1 = 0
        for r in g1rows:
            if r.get("source") != "twins_streamlet":
                continue
            st = json.loads(canon(r["native_request"]["state"]))
            if r.get("declared_edit", {}).get("op", "").startswith("append"):
                st["received_messages"].pop()
            h = h64(st)
            if h in scenes:
                used.setdefault(h, "G1_pilot")
                n_g1 += 1
            else:
                # retimed/neutral variants may not reconstruct; mark conservatively
                used.setdefault(h64(json.loads(canon(r["native_request"]["state"]))), "G1_pilot_variant_conservative")
                n_g1 += 1
        # A428: states are corpus scenes directly
        a428 = [json.loads(x) for x in git_blob(repo, BLOB_A428_INPUTS).splitlines() if x.strip()]
        n_a428 = 0
        for r in a428:
            h = h64(r["native_request"]["state"])
            if h in scenes:
                used.setdefault(h, "A428_multiq_pilot")
                n_a428 += 1
        unused = [h for h in scenes if h not in used]
        census = {"twins_scenes": len(scenes), "dev_run_groups_total": len(all_groups),
                  "used_by_round": {"G5_V2": n_g5, "G3": n_g3, "G1_pilot_twins": n_g1, "A428": n_a428},
                  "used_scene_count": len(used), "unused_scene_count": len(unused),
                  "reuse_rule": "scene-level SHA64 ledger; rounds may share groups but G2 pairs must use scenes never used before",
                  "groups_with_unused_scenes": len({group_of[h] for h in unused})}
        save(out / "scene_reuse_ledger.json",
             {"schema": "JEV_A461_G5_G2_SCENE_REUSE_LEDGER_V1", "census": census,
              "used": [{"scene_sha256": h, "round": used[h], "source_group": group_of[h]} for h in sorted(used)]})
        produced.append("scene_reuse_ledger.json")

        # ---------- constructibility scan on unused scenes (dual oracle + legality + width) ----------
        from tokenizers import Tokenizer
        tok = Tokenizer.from_file(str(CKPT / "tokenizer.json"))
        tlen = lambda s: len(tok.encode(s).ids)
        inv = []
        for h in sorted(unused):
            rec = scenes[h]
            st = rec["state"]
            o1, support = oracle1(st)
            o2 = oracle2(st)
            if o1["conflicting_vote"] or o1["conflicting_vote"] != o2["conflicting_vote"]:
                continue
            msgs = st["received_messages"]
            recv = [e["received"] for e in msgs]
            if not all(recv[j] <= recv[j + 1] for j in range(len(recv) - 1)) or (recv and max(recv) > st["decision_time"]):
                continue
            blocks = sorted({e["block"] for e in msgs} - {st["candidate_block"]})
            if not support or not blocks:
                continue
            grp = group_of[h]
            cell = "accept" if o1["quorum"] else ("wait" if len(support) == st["quorum_size"] - 1 and
                    any(v not in {e.get("author") for e in msgs if e.get("kind") == "vote" and e.get("round") == st["candidate_round"]
                                  and isinstance(e.get("received"), (int, float)) and e["received"] <= st["decision_time"]}
                        for v in st["validator_set"]) else None)
            if cell is None:
                continue
            cl = tlen(st["candidate_block"])
            same_w = [b for b in blocks if tlen(b) == cl]
            cand_votes = [e for e in msgs if e.get("kind") == "vote" and e.get("block") == st["candidate_block"]
                          and e.get("round") == st["candidate_round"]]
            if not cand_votes:
                continue
            # construct treatment + SA and verify dual oracle + chronology on both
            mx = max(e["received"] for e in msgs)
            st_new = json.loads(canon(st))
            st_new["received_messages"].append({"author": sorted(support)[0], "block": (same_w[0] if same_w else blocks[0]),
                                                "kind": "vote", "round": st["candidate_round"], "received": mx})
            g_new1, _ = oracle1(st_new)
            g_new2 = oracle2(st_new)
            st_sa = json.loads(canon(st))
            dup = json.loads(canon(cand_votes[0]))
            dup["received"] = mx
            st_sa["received_messages"].append(dup)
            g_sa1, _ = oracle1(st_sa)
            g_sa2 = oracle2(st_sa)
            ok = (g_new1["conflicting_vote"] and g_new1["certificate_action"] == "reject_conflict"
                  and all(g_new1[k] == g_new2[k] for k in ("conflicting_vote", "quorum", "certificate_action"))
                  and g_sa1["conflicting_vote"] == o1["conflicting_vote"] and g_sa1["certificate_action"] == o1["certificate_action"]
                  and all(g_sa1[k] == g_sa2[k] for k in ("conflicting_vote", "quorum", "certificate_action"))
                  and all(e["received"] <= st["decision_time"] for e in st_new["received_messages"])
                  and sorted(e["author"] for e in st_new["received_messages"])[-1] in st["validator_set"])
            inv.append({"scene_sha256": h, "source_group": grp, "cell": cell,
                        "same_width_block_available": bool(same_w), "constructible": ok,
                        "treatment_block": same_w[0] if same_w else blocks[0],
                        "dual_oracle_constructed_arms_agree": ok})
        constructible = [r for r in inv if r["constructible"]]
        by_group = collections.Counter(r["source_group"] for r in constructible)
        by_cell = collections.Counter(r["cell"] for r in inv if r["constructible"])
        width_rate = (sum(1 for r in constructible if r["same_width_block_available"]) / len(constructible)) if constructible else 0.0
        # independence sizing: observed qualification ~2/62 pairs => need N for >=2 expected new qualified donors
        rate = sum(v["qualified"] for v in QUALIFIED_OBSERVED.values()) / sum(v["pairs"] for v in QUALIFIED_OBSERVED.values())
        need_for_2 = int(-(-(2 / rate))) if rate > 0 else None
        feasibility = {
            "schema": "JEV_A461_G5_G2_CONSTRUCTIBILITY_INVENTORY_V1",
            "unused_scenes": len(unused), "screened": len(inv),
            "constructible_pairs": len(constructible),
            "constructible_by_cell": dict(by_cell),
            "constructible_groups": len(by_group),
            "top_groups_by_inventory": dict(by_group.most_common(10)),
            "same_width_rate": round(width_rate, 4),
            "donor_qualification_base_rate_observed": round(rate, 4),
            "pairs_needed_for_expected_2_new_qualified_donors": need_for_2,
            "sizing_feasible": bool(constructible and need_for_2 and len(constructible) >= need_for_2),
            "note": "model recognition (donor qualification) is NOT assessable without forwards; this audit only establishes construction feasibility"
        }
        save(out / "constructibility_inventory.json", feasibility)
        produced.append("constructibility_inventory.json")
        lines_out = out / "constructible_scenes.jsonl"
        with lines_out.open("x", encoding="utf8", newline="\n") as f:
            for r in constructible:
                f.write(canon(r) + "\n")
        produced.append("constructible_scenes.jsonl")

        # ---------- G2 design draft (confirmatory/exploratory, negative controls, budget formula) ----------
        design = {
            "schema": "JEV_A461_G5_G2_DESIGN_DRAFT_V1",
            "id": "A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION",
            "status": "CPU_FEASIBILITY_DONE_DESIGN_DRAFT_NOT_ADMITTED",
            "novelty_delta_locked": [
                "Zhang&Nanda ICLR24: patching metric/corruption choice dependence -> G2 contributes paired same-site preregistered controls and a frozen metric (C margin on the dynamically resolved conflicting_vote row), not a new patching technique",
                "MechSparse: patching scores may not beat cheap activation-norm selectors -> G2 must report per-pair span activation norm/magnitude quantification and include a norm-matched random control so the effect is not explained by magnitude heuristics",
                "Encoded-but-Disconnected: encoded info may not causally affect output; patching nulls are meaningful -> G2 reports the restoration partial-margin case as the substantively interesting middle outcome",
                "Cell-based relational binding: generic probe/patching not novel -> G2's delta is the security-typed decision readout with per-arm executable oracle gold, not generic relational binding",
                "ACED-Bench: programmatic oracle + intervention ledgers exist -> G2's ledger is governance hygiene, not a novelty claim"
            ],
            "units_and_independence": "unit = (scene pair, source run group); donor and hosts from distinct run groups; scenes never used in G1/G3/G5V2/A428 (SHA64 ledger); same-layer repeats of run83/run114/run182 are NOT replications and stay out of confirmatory sets",
            "confirmatory_subset": "layer 11 only (G1-pilot-motivated), new source groups, donor-side matched negative controls preregistered, N sized in the feasibility inventory",
            "exploratory_subset": "layer sweep beyond 11 (including 23 as structural null control) and any additional cells, reported without selection",
            "suppression_negative_controls_mandatory": [
                "host_new -> donor_new (as in the pilot)",
                "host_SA -> donor_new (matched neutral source)",
                "host_new span position-permuted -> donor_new",
                "norm-matched random activation -> donor_new (per-pair per-layer same-site pairing, seed frozen at admission)"
            ],
            "restoration_additions": "per-pair span norm / magnitude / activation-distribution quantification reported; norm-matched random control added on the restoration side as well",
            "key_specific_attribution_gate": "a later, separate component-controlled protocol with an independently intervenable K/Q readout path is required before any 'Key-only mediation' claim; backbone layer-output span patches cannot deliver it",
            "budget_formula_dynamic": {
                "per_config": "F(H, L) = 4 + 5H + 5HL  [3 donor captures + 1 donor NEW baseline + H x (host SA baseline + host SA capture + host NEW capture + identity) + (2 restoration controls + 3 suppression controls) x H x L]",
                "calibration": "G1 pilot was 28 = 4 + 5*2 + 5*2*2 - (norm-matched controls not present); G2 adds the donor-side third control",
                "examples_not_approval": {"H2_L2": 34, "H4_L2": 64, "H4_L3": 84, "H6_L2": 94},
                "hard_cap_per_run": 128,
                "rule": "actual count derived by the runner trace from the frozen roster; admission receipt before execution; independent review + fresh user authorization required"
            },
            "stop_conditions": [
                "no new independent source-group qualified positive donor after the sized search",
                "dual-oracle disagreement on any constructed arm",
                "token alignment / same-width pairing infeasible at admission",
                "random / SA-sham controls explain the flips as well as the treatment",
                "Key-specific effect does not exceed the cheap norm-matched baseline"
            ],
            "feasibility": feasibility
        }
        save(out / "g2_design_draft.json", design)
        produced.append("g2_design_draft.json")

        verdict = "PASS" if (feasibility["sizing_feasible"] and census["groups_with_unused_scenes"] >= 5) else "HOLD"
        receipt.update(status="COMPLETE_A461_G5_G2_CPU_FEASIBILITY_" + verdict,
                       census=census, feasibility_summary={
                           "constructible_pairs": feasibility["constructible_pairs"],
                           "constructible_groups": feasibility["constructible_groups"],
                           "same_width_rate": feasibility["same_width_rate"],
                           "sizing_feasible": feasibility["sizing_feasible"],
                           "pairs_needed_for_expected_2_new_qualified_donors": need_for_2},
                       verdict=verdict,
                       gpu_blocked=True,
                       next_gate="G2 design draft requires independent review; GPU requires new admission receipt + fresh user authorization")
        code = 0
    except Exception as err:
        import traceback
        receipt.update(status="FAIL_A461_G5_G2_CPU_FEASIBILITY", error_type=type(err).__name__,
                       error_message=str(err), traceback=traceback.format_exc()[-2000:])
        code = 2
    with (out / "execution_receipt.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    produced.append("execution_receipt.json")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in produced:
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(canon(receipt))
    return code


if __name__ == "__main__":
    sys.exit(main())
