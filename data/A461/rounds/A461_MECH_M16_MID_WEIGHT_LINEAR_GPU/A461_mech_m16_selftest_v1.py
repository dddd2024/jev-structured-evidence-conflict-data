#!/usr/bin/env python3
"""A461-MECH-M16 runner CPU self-test (zero GPU; every subprocess CUDA_VISIBLE_DEVICES="").
Same gate/ledger/refusal tests as M15 (A461_mech_m15_selftest_v1.py), plus: the full path on the real 2992-row
manifest (14 arms on 208 rows; M14's abc_s0375, M15's csc29_s0375 and mw0_s0375 on the 12 rows of the 6 subset
cells); the wiring of the middle-weight arms (shift_pos_weight w at 13-28 and c_30 weight 0, pools exclude the cell's
donor and host, signs, s, w; the recorded shift weight min / max / listed match w); and identities: full with source =
target (bitwise); a pool of the donor alone on the host base = host + delta_B, as is a contrast shift whose pools are
the donor's new capture; cs1 rebuilt from a cs arm == meanD_host; the contrast restricted to all 16 heads, weight 1 at
position 30 and c kept at all 31 positions == the cs arm (bitwise); weight 0 at 30 == c kept at 29, also with the AB
shift (bitwise); the common shift at all 31 positions == the cs arm; the AB shift with shift_scale 1 == the unscaled
AB shift; the new field: weight 0 at 13-28 == the AB shift (shift_positions 0-12 + 29-30), and weight 1 at 13-28 ==
the shift at all 31 positions (both bitwise); a manifest row with shift_pos_weight and shift_positions together is
refused at the manifest check. The plain cs arm used as the identity base is built from the M16 mwp05_s05 rows by
removing the c_30 weight and the shift weights."""
import argparse, collections, hashlib, importlib.util, json, os, statistics, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_mech_m16_runner_v1.py"
STAGE = "A461_MECH_M16_MID_WEIGHT_LINEAR_GPU"
TOTAL, PLAN = 2992, [128] * 23 + [48]
SUBSET = ("abc_s0375", "csc29_s0375", "mw0_s0375")   # the M14 / M15 replays and the new-field AB arm, on 6 cells only
RESULTS = []
# R2: children died with "libgomp: Thread creation failed" under the shared per-user thread limit
THREADS = {"OMP_NUM_THREADS": "24", "MKL_NUM_THREADS": "24"}
os.environ.update(THREADS)


def rec(name, ok, ev):
    RESULTS.append({"test": name, "verdict": "PASS" if ok else "FAIL", "evidence": ev})
    print(("PASS " if ok else "FAIL ") + name + " :: " + ev[:200], flush=True)


def guarded(name, fn):
    try:
        ok, ev = fn()
    except Exception as err:
        ok, ev = False, f"test raised {type(err).__name__}: {str(err)[:200]}"
    rec(name, ok, ev)


def receipt(d):
    return json.loads((Path(d) / "execution_receipt.json").read_text("utf8"))


def rows(d):
    p = Path(d) / "raw_native_logits_m16.jsonl"
    return [json.loads(x) for x in p.read_text("utf8").splitlines() if x.strip()] if p.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--g10-cf", required=True, type=Path)
    ap.add_argument("--m3-raw", required=True, type=Path)
    ap.add_argument("--m6-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    out = a.out.expanduser().resolve()
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    (out / "_adm").mkdir()
    quota = out / "_quota"
    quota.mkdir()
    spec = importlib.util.spec_from_file_location("m16", RUNNER)
    rb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rb)
    runner_blob = rb.file_blob(RUNNER)

    def adm(name, **kw):
        p = out / "_adm" / f"{name}.json"
        p.write_text(json.dumps(kw) + "\n", encoding="utf8")
        return p

    def fake_adm(name, aid, approved=TOTAL, batches=len(PLAN)):
        return adm(name, stage=STAGE, mode="L1_FAKE", admission_id=aid, approved_max_native_forwards=approved,
                   approved_batches=batches)

    def gpu_adm(name, **over):
        base = dict(stage=STAGE, mode="GPU", admission_id="SELFTEST_SYNTH_M16_0001",
                    selftest_synthetic_not_an_authorization=True,
                    governance="JEV_SINGLE_TRIGGER_PAPER_CLAIM_AUDIT_POLICY_V2",
                    user_gpu_approval_quote="self-test synthetic quote (not a real approval)",
                    user_gpu_approval_utc="1970-01-01T00:00:00Z", approved_runner_blob=runner_blob,
                    explicit_user_gpu_approval=True, approved_max_native_forwards=TOTAL, approved_batches=len(PLAN),
                    approved_batch_plan=PLAN,
                    frozen_inputs={"manifest_blob": rb.BLOB_MANIFEST, "design_blob": rb.BLOB_DESIGN,
                                   "m1_raw_blob": rb.BLOB_M1_RAW, "g10_counterfactuals_blob": rb.BLOB_G10_CF, "m3_raw_blob": rb.BLOB_M3_RAW, "m6_raw_blob": rb.BLOB_M6_RAW,
                                   "roster_blob": rb.BLOB_ROSTER,
                                   "g5v2_questions_blob": rb.BLOB_G5V2, "corpus_sha256": rb.CORPUS_SHA},
                    model_identity_sha256=rb.v4.identity_digest(rb.v4.MODEL_IDENTITY))
        base.update(over)
        return adm(name, **base)

    def run(name, admission, backend="fake", mode=None, extra=(), fault="none", manifest=None, g10=None):
        cmd = [sys.executable, str(RUNNER), "--repo-root", str(a.repo_root), "--admission", str(admission),
               "--manifest", str(manifest or a.manifest), "--m1-raw", str(a.m1_raw),
               "--g10-cf", str(g10 or a.g10_cf), "--m3-raw", str(a.m3_raw), "--m6-raw", str(a.m6_raw),
               "--backend", backend, "--out", str(out / name), *extra]
        if mode:
            cmd.append(mode)
        if backend == "fake" and mode is None:
            cmd += ["--quota-root", str(quota)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10800,
                           env=dict(os.environ, CUDA_VISIBLE_DEVICES="", FAKE_FAULT=fault, **THREADS))
        # keep every child's exit code and output tail (R1 lost two children without a receipt)
        (out / f"_child_{name}.log").write_text(
            f"returncode={r.returncode}" + chr(10) + "--- stdout ---" + chr(10) + r.stdout[-4000:] + chr(10)
            + "--- stderr ---" + chr(10) + r.stderr[-8000:] + chr(10), encoding="utf8")
        return r

    run("T1_preflight", fake_adm("pf", "SELFTEST_PF_0001"), mode="--preflight-only")
    guarded("preflight_token_and_span_gates_on_real_manifest", lambda: (
        receipt(out / "T1_preflight")["status"] == "COMPLETE_A461_MECH_M16_PREFLIGHT"
        and receipt(out / "T1_preflight")["preflight"] == {"scenes": 22, "token_gate": "PASS", "span_gate": "PASS",
                                                          "manifest_rows": TOTAL},
        f"{receipt(out / 'T1_preflight')['preflight']}"))

    run("T2_fullpath", fake_adm("full", "SELFTEST_FULL_0001"))
    r2, x2 = receipt(out / "T2_fullpath"), rows(out / "T2_fullpath")
    caps = [x for x in x2 if x.get("capture_file")]

    def t_full():
        brs = [(b["run"], b["planned"], b["physical"], b["status"]) for b in r2["batch_receipts"]]
        cond = collections.Counter(x["condition"] for x in x2)
        files = sorted((out / "T2_fullpath" / "captures").iterdir())
        d = out / "T2_fullpath" / "captures"
        ok_files = all(hashlib.sha256((d / c[k]["name"]).read_bytes()).hexdigest() == c[k]["sha256"]
                       for c in caps for k in ("capture_file", "class_file"))
        shapes = all(c["capture_file"]["shape"] == [4, c["capture"]["span"][1] - c["capture"]["span"][0], 64]
                     for c in caps)
        return (r2["status"] == "COMPLETE_A461_MECH_M16" and len(x2) == TOTAL
                and [x["forward_index"] for x in x2] == list(range(1, TOTAL + 1))
                and brs == [(k, 128, 128, "COMPLETE") for k in range(1, 24)] + [(24, 48, 48, "COMPLETE")]
                and r2["physical_prehook_calls"] == TOTAL and r2["denied_prehook_calls"] == 0
                and r2["durable_appends"]["raw_rows"] == TOTAL and len(caps) == 44 and len(files) == 88
                and ok_files and shapes
                and len([k for k in cond if k.startswith("patch_m16_")]) == 34
                and all(v == (6 if k[len("patch_m16_"):].rsplit("_", 1)[0] in SUBSET else 104)
                        for k, v in cond.items() if k.startswith("patch_m16_"))
                # fake explicit-softmax attention is batched over rows: float32 rounding only (<= 1e-6)
                and all(c["cross_row_max_absdiff"] <= 1e-6 for c in caps),
                f"status={r2['status']} rows={len(x2)} batches={len(brs)} captures={len(caps)} files={len(files)} "
                f"(sha ok={ok_files}, shapes ok={shapes}); cross-row max {max(c['cross_row_max_absdiff'] for c in caps):.1e}")
    guarded("fake_full_path_2992_with_44_captures_and_class_files", t_full)
    def t_readout():
        import torch
        d = out / "T2_fullpath" / "captures"
        worst_file = 0.0
        for c in caps:
            x = torch.load(d / c["capture_file"]["name"], weights_only=True).float()[0]
            k = torch.load(d / c["class_file"]["name"], weights_only=True)
            ok = sorted(k["contrib"]) == sorted(["PARTNER", "ROUND_PEERS", "OTHER_ITEMS", "SELF", "CONTEXT"])
            if not ok or list(k["partner_values"].shape)[1] != 33 or list(k["partner_attention"].shape)[2] != 33:
                return False, f"class file layout at {c['capture']['tag']}"
            worst_file = max(worst_file, float((sum(t.float() for t in k["contrib"].values()) - x).abs().max()))
        recon = max(c["attn_readout_recon_maxabs"] for c in caps)
        add = max(c["class_additivity_maxabs"] for c in caps)
        return (recon < 1e-5 and add < 1e-5 and worst_file < 1e-2,
                f"5 class contributions sum to the forward's o_proj input (max abs {add:.2e}; saved fp16 files "
                f"{worst_file:.1e}); attention readout reconstructs it ({recon:.2e})")
    guarded("class_contributions_partition_and_sum_to_oproj_input", t_readout)
    BULK = ["OTHER_ITEMS", "CONTEXT"]
    HEADS, HEADS_SM = {}, ()
    CPOS = {}
    FIELDS = {"AUTH": list(range(0, 7)), "BLOCK": list(range(7, 13)), "KIND": list(range(13, 18)),
              "RECV": list(range(18, 25)), "RKEY": list(range(25, 29))}
    AB = FIELDS["AUTH"] + FIELDS["BLOCK"]
    MID = list(range(13, 29))
    Q1 = {"_s05": 0.5, "_s0375": 0.375, "_s025": 0.25}
    WT = {"m1": -1.0, "m05": -0.5, "p05": 0.5, "p15": 1.5}
    MW = dict({"mw0_s0375": 0.0}, **{f"mw{t_}{k_}": w_ for k_ in Q1 for t_, w_ in WT.items()})
    SPW = {n: [[i_, w_] for i_ in MID] for n, w_ in MW.items()}
    SHPOS = {"abc_s0375": AB + [29, 30]}
    CW = {n: [[30, 0.0]] for n in ["abc_s0375", "csc29_s0375"] + list(MW)}
    SHSCALE = {}
    LAM, NULLS, SPLIT = {}, (), ()
    S_OF = dict({"abc_s0375": 0.375, "csc29_s0375": 0.375, "mw0_s0375": 0.375},
                **{n: Q1[n[n.index("_s"):]] for n in MW if n != "mw0_s0375"})
    EXPECT = dict({"full": ("full", []), "meanD_host": ("pool", BULK)}, **{n: ("cshift", BULK) for n in CW})
    DISTINCT = tuple(n for n in EXPECT if n not in SUBSET)

    def dev(x, y):
        return max(abs(u - v) for q, qb in zip(x["questions"], y["questions"]) for u, v in zip(q["logits"], qb["logits"]))

    def t_wiring():
        lg = {(x["donor"], x["host"], x["patch"]["arm"], x["source_kind"]): json.dumps(x["questions"])
              for x in x2 if x.get("patch")}
        rw = {(x["donor"], x["host"], x["patch"]["arm"], x["source_kind"]): x for x in x2 if x.get("patch")}
        keys = {(d, h, src) for (d, h, _a, src) in lg}
        arms = sorted({a_ for (_d, _h, a_, _s) in lg})
        distinct = sum(len({lg[(d, h, arm, src)] for arm in DISTINCT}) == len(DISTINCT) for d, h, src in keys)
        cst = lambda n, d, h, s_: rw[(d, h, n, s_)]["contrast_stats"]
        sh = lambda n, d, h, s_: cst(n, d, h, s_)["energy_share"]
        # c_30 weight 0: the energy share is 1 - e_30
        cl = [(n, d, h, s_) for (d, h, n, s_) in rw if n in CW]
        wsh = max(abs(sh(n, d, h, s_) - (1 - cst(n, d, h, s_)["pos_share_before"]["30"])) for n, d, h, s_ in cl)
        al = [(n, d, h, s_) for (d, h, n, s_) in rw if n in SHPOS]
        u_ok = max(abs(rw[(d, h, n, s_)]["alpha_stats"]["shift_u_max"] - SHSCALE.get(n, 1.0)) for n, d, h, s_ in al)
        cnt = collections.Counter(x["patch"]["arm"] for x in x2 if x.get("patch"))
        ops_ok = all((x["patch"]["op"], x["patch"]["classes"]) == EXPECT[x["patch"]["arm"]] for x in x2 if x.get("patch"))
        sub_cells = {(d, h) for (d, h, n, _s) in rw if n in SUBSET}
        sub_ok = len(sub_cells) == 6 and sorted(collections.Counter(h[:8] for _d, h in sub_cells).values()) == [2, 2, 2]
        return (distinct == len(keys) == 208 and sorted(arms) == sorted(EXPECT) and ops_ok and sub_ok
                and cnt == {n: (12 if n in SUBSET else 208) for n in EXPECT}
                and wsh <= 1e-6 and u_ok <= 1e-12,
                f"{len(DISTINCT)} full arms distinct in {distinct}/{len(keys)} (cell, source); {len(SUBSET)} replay arms "
                f"on 6 subset cells, 2 per host: {sub_ok}; c_30 weight 0 share = 1 - e_30 ({wsh:.1e}); AB shift u as "
                f"planned ({u_ok:.1e}); "
                f"{len(arms)} arms; op/classes match the frozen arm table: {ops_ok}")
    guarded("seventeen_arms_wiring_and_size_bookkeeping", t_wiring)

    def t_size():
        rr = [x for x in x2 if x.get("patch") and (x["patch"].get("contrast_rem") or x["patch"].get("shift_scale"))]
        wr = [x for x in x2 if x.get("patch") and x["patch"].get("shift_pos_weight")]
        bad = [x["patch"]["arm"] for x in wr
               if not (x["patch"]["arm"] in MW and x["alpha_stats"]["shift_weight_min"] == min(MW[x["patch"]["arm"]], 1.0)
                       and x["alpha_stats"]["shift_weight_max"] == max(MW[x["patch"]["arm"]], 1.0)
                       and x["alpha_stats"]["shift_weight_listed"] == [MW[x["patch"]["arm"]]])]
        return (len(rr) == 0 and len(wr) == 12 * 208 + 12 and not bad,
                f"{len(wr)} shift-weight rows record min / max / listed weight as planned (bad {len(bad)}); "
                f"{len(rr)} tilt or shift_scale rows (none planned)")
    guarded("shift_weight_rows_record_planned_weights", t_size)

    def t_allrows():
        base = {(x["target_scene"], x["target_arm"]): {q["id"]: q["logits"] for q in x["questions"]} for x in x2
                if x.get("capture") and x.get("source_kind") == "host"}
        pr = [x for x in x2 if x.get("patch")]
        moved = sum({q["id"]: q["logits"] for q in x["questions"]}["conflicting_vote"] != base[(x["target_scene"], x["target_arm"])]["conflicting_vote"]
                    and {q["id"]: q["logits"] for q in x["questions"]}["certificate_action"] != base[(x["target_scene"], x["target_arm"])]["certificate_action"]
                    for x in pr)
        return (len(base) == 16 and len(pr) == 2948 and moved >= 2948 - 1040,
                f"host baselines={len(base)}; all-row patches moving both C and action rows: {moved}/{len(pr)} "
                f"(small arms can be tiny in the fake model)")
    guarded("all_row_patches_reach_c_and_action", t_allrows)

    # identities: the host's OWN capture as source and target leaves the forward unchanged (full bitwise); a pool
    # holding only the donor on the host base and a contrast shift whose pools are the donor's new capture are host +
    # delta_B (float rounding); the contrast restricted to all 16 heads is cs1 (bitwise); g0_2 is the M7 rcD
    # construction (meandiff host + scale * c, bitwise); the par part on a k = 64 basis (the fake width) is cs1
    man = [json.loads(x) for x in a.manifest.read_text("utf8").splitlines() if x.strip()]
    caps_rows = [m for m in man if m["phase"] == "capture"]
    h0 = next(m for m in caps_rows if m["source_kind"] == "host" and m["target_arm"] == "new")
    full0 = dict(next(m for m in man if m["phase"] == "patch" and m["target_scene"] == h0["target_scene"]
                      and m["patch"]["arm"] == "full"))
    idf = dict(full0, condition="identity_full", bitwise_vs_m3=None, patch=dict(full0["patch"], source=h0["capture"]["tag"]))
    md0 = dict(next(m for m in man if m["phase"] == "patch" and m["patch"]["arm"] == "meanD_host"
                    and m["source_kind"] == "main" and m["target_scene"] == h0["target_scene"]))
    md0["bitwise_vs_m6"] = None
    cell = lambda m: (m["donor"], m["host"], m["source_kind"])
    pool_d = dict(md0, condition="pool_donor_only", patch=dict(md0["patch"], arm="pool_d", pool=[md0["patch"]["source"]]))
    pick = lambda arm_, sk_: next(m for m in man if m["phase"] == "patch" and m["patch"]["arm"] == arm_
                                  and m["donor"] == md0["donor"] and m["host"] == md0["host"] and m["source_kind"] == sk_)
    plain = lambda m: dict(m, patch={k_: v_ for k_, v_ in m["patch"].items()
                                     if k_ not in ("contrast_pos_weight", "shift_pos_weight")})
    csr = plain(pick("mwp05_s05", "main"))
    cs_d = dict(csr, condition="cshift_donor_only",
                patch=dict(csr["patch"], pool_new=[md0["patch"]["source"]], pool_round=[md0["patch"]["source"]], scale=2.0))
    c1r = plain(pick("mwp05_s05", "round"))
    cs1m = dict(csr, condition="cs1_main", patch=dict(csr["patch"], arm="cs1", scale=-0.5))
    ch_all = dict(c1r, condition="contrast_all_heads", patch=dict(c1r["patch"], arm="ch_all", contrast_heads=list(range(16))))
    cw1 = dict(c1r, condition="contrast_weight_1", patch=dict(c1r["patch"], arm="cw1", contrast_pos_weight=[[30, 1.0]]))
    cw0 = dict(c1r, condition="contrast_weight_0", patch=dict(c1r["patch"], arm="cw0", contrast_pos_weight=[[30, 0.0]]))
    cpp = dict(c1r, condition="cpos29_round", patch=dict(c1r["patch"], arm="cpos29", contrast_positions=[29]))
    cpos_all = dict(c1r, condition="contrast_all_positions",
                    patch=dict(c1r["patch"], arm="cpos_all", contrast_positions=list(range(31))))
    sh_all = dict(c1r, condition="shift_all_positions", patch=dict(c1r["patch"], arm="sh_all", shift_positions=list(range(31))))
    abr = dict(c1r, patch=dict(c1r["patch"], arm="ab_c29", shift_positions=AB + [29, 30], contrast_pos_weight=[[30, 0.0]]))
    ab_s1 = dict(abr, condition="ab_shift_scale_1", patch=dict(abr["patch"], arm="ab_s1", shift_scale=1.0))
    ab_pos = dict(abr, condition="ab_c29_via_positions",
                  patch=dict({k_: v_ for k_, v_ in abr["patch"].items() if k_ != "contrast_pos_weight"}, arm="ab_pos",
                             contrast_positions=[29]))
    spw0 = dict(c1r, condition="spw_mid0_c29", patch=dict(c1r["patch"], arm="spw0", contrast_pos_weight=[[30, 0.0]],
                                                          shift_pos_weight=[[i_, 0.0] for i_ in MID]))
    spw1 = dict(c1r, condition="spw_all1", patch=dict(c1r["patch"], arm="spw1", shift_pos_weight=[[i_, 1.0] for i_ in MID]))
    spwh = dict(c1r, condition="spw_half", patch=dict(c1r["patch"], arm="spwh", shift_pos_weight=[[i_, 0.5] for i_ in MID]))
    mini = [dict(m, forward_index=i + 1, run=1) for i, m in enumerate(
        caps_rows + [idf, pool_d, cs_d, dict(c1r, condition="cs1_round"), ch_all, cw1, cw0, cpp, cpos_all, sh_all,
                     dict(abr, condition="ab_c29_round"), ab_pos, spw0, spw1, spwh,
                     cs1m, dict(md0, condition="meanD_main"), ab_s1])]
    mini_p = out / "_identity_manifest.jsonl"
    mini_p.write_text("".join(json.dumps(m, sort_keys=True, separators=(",", ":")) + "\n" for m in mini), encoding="utf8")
    run("T6_identity", fake_adm("ident", "SELFTEST_IDENT_0001", approved=len(mini), batches=1), manifest=mini_p,
        extra=("--expect-batches", str(len(mini)), "--allow-manifest-blob", rb.file_blob(mini_p)))

    def t_identity():
        x6 = rows(out / "T6_identity")
        base = next(x for x in x6 if x.get("capture") and x["target_scene"] == h0["target_scene"]
                    and x["target_arm"] == "new")
        pr = {x["condition"]: x for x in x6 if x.get("patch")}
        d_ = {"cshift_donor_only_vs_pool_donor": dev(pr["cshift_donor_only"], pr["pool_donor_only"]),
              "weight_0_vs_cpos29": dev(pr["contrast_weight_0"], pr["cpos29_round"]),
              "shift_all_positions_vs_cs1": dev(pr["shift_all_positions"], pr["cs1_round"]),
              "cs1_vs_meanD_host": dev(pr["cs1_main"], pr["meanD_main"]),
              "ab_shift_scale_1_vs_unscaled": dev(pr["ab_shift_scale_1"], pr["ab_c29_round"])}
        hs_ = pr["spw_half"]["alpha_stats"]
        return (receipt(out / "T6_identity")["status"] == "COMPLETE_A461_MECH_M16" and len(pr) == 18
                and pr["identity_full"]["questions"] == base["questions"]
                and pr["contrast_all_heads"]["questions"] == pr["cs1_round"]["questions"]
                and pr["contrast_weight_1"]["questions"] == pr["cs1_round"]["questions"]
                and pr["contrast_all_positions"]["questions"] == pr["cs1_round"]["questions"]
                and pr["ab_c29_via_positions"]["questions"] == pr["ab_c29_round"]["questions"]
                and abs(pr["contrast_all_heads"]["contrast_stats"]["energy_share"] - 1) < 1e-9
                and abs(pr["contrast_weight_1"]["contrast_stats"]["energy_share"] - 1) < 1e-9
                and abs(pr["contrast_all_positions"]["contrast_stats"]["energy_share"] - 1) < 1e-9
                and pr["spw_mid0_c29"]["questions"] == pr["ab_c29_round"]["questions"]
                and pr["spw_all1"]["questions"] == pr["shift_all_positions"]["questions"]
                and pr["spw_half"]["questions"] != pr["ab_c29_round"]["questions"]
                and pr["spw_half"]["questions"] != pr["shift_all_positions"]["questions"]   # w = 1/2 lies between the two
                and (hs_["shift_weight_min"], hs_["shift_weight_max"], hs_["shift_weight_listed"]) == (0.5, 1.0, [0.5])
                and max(d_.values()) <= 1e-4,
                "full no-op, all-16-heads contrast, weight 1 at position 30 and all-31-positions contrast == the cs "
                "arm (mwp05_s05 without its weights), bitwise; the AB shift with c_30 weight 0 == with c kept at 29 only, bitwise; weight 0 "
                "at 30 == cpos29; cs1 rebuilt == meanD_host; AB shift_scale 1 == unscaled; shift weight 0 at 13-28 "
                "== the AB shift and weight 1 == the all-position shift, bitwise; weight 1/2 recorded (0.5, 1); max |logit "
                "diff| " + ", ".join(f"{k} {v:.1e}" for k, v in sorted(d_.items())))
    guarded("identities_pool_heads_positions_weights_and_shift_weight", t_identity)
    bad_m = dict(spw0, condition="spw_with_positions", patch=dict(spw0["patch"], shift_positions=AB + [29, 30]))
    bad_p = out / "_bad_weight_manifest.jsonl"
    bad_p.write_text("".join(json.dumps(dict(m, forward_index=i + 1, run=1), sort_keys=True, separators=(",", ":")) + "\n"
                             for i, m in enumerate(caps_rows + [bad_m])), encoding="utf8")
    run("T7_bad_weight", fake_adm("badw", "SELFTEST_BADW_0001", approved=len(caps_rows) + 1, batches=1),
        mode="--preflight-only", manifest=bad_p,
        extra=("--expect-batches", str(len(caps_rows) + 1), "--allow-manifest-blob", rb.file_blob(bad_p)))
    guarded("shift_weight_with_shift_positions_refused", lambda: (
        receipt(out / "T7_bad_weight")["status"] == "FAIL_A461_MECH_M16"
        and "patch op/classes" in receipt(out / "T7_bad_weight")["error_message"]
        and receipt(out / "T7_bad_weight")["model_loads"] == 0,
        f"refused at the manifest check: {receipt(out / 'T7_bad_weight')['error_message'][:80]}"))

    def t_variants():
        cf = json.loads(a.g10_cf.read_text("utf8"))
        cap = {(x["target_scene"], x["target_arm"]): x for x in caps}
        good = sum(cap[(s, arm)]["token_ids_sha256"] == cf[s]["ROUND"]["token_ids_sha256"]
                   and cap[(s, arm)]["capture"]["span"] == cf[s]["ROUND"]["span"]
                   and cap[(s, arm)]["token_ids_sha256"] != cap[(s, "new")]["token_ids_sha256"]
                   for (s, arm) in cap if arm == "ROUND")
        src = collections.Counter(x["patch"]["source"].split(":")[0] for x in x2 if x.get("patch"))
        tg = collections.Counter(x["patch"]["target"].split(":")[0] for x in x2 if x.get("patch"))
        pl = [x for x in x2 if x.get("patch") and x["patch"]["op"] in ("pool", "cshift")]
        donors12 = {x["donor"][:12] for x in x2 if x.get("donor")}
        hosts12 = {x["host"][:12] for x in x2 if x.get("host")}
        ids_ = lambda tags: [t_[-12:] for t_ in tags]
        kind = lambda ids: ("donors" if set(ids) <= donors12 and len(ids) == len(set(ids)) == 12 else
                            "hosts" if set(ids) <= hosts12 and len(ids) == len(set(ids)) >= 5 else None)
        arm_of = lambda tags: {t_.split(":")[0] for t_ in tags}

        def pool_ok(x):
            p = x["patch"]
            sa = p["source"].split(":")[0]
            dd, hh = x["donor"][:12], x["host"][:12]
            tags = p["pool"] if p["op"] == "pool" else p["pool_new"] + p["pool_round"]
            ids = ids_(tags)
            if dd in ids or hh in ids:
                return False
            if p["op"] == "pool":
                return arm_of(tags) == {sa} and kind(ids) == "donors"
            want = -S_OF.get(p["arm"], 1.0) / 2 if x["source_kind"] == "main" else S_OF.get(p["arm"], 1.0) / 2
            ok = (arm_of(p["pool_new"]) == {"new"} and arm_of(p["pool_round"]) == {"ROUND"}
                  and ids_(p["pool_new"]) == ids_(p["pool_round"]) and kind(ids_(p["pool_new"])) == "donors"
                  and p["base"] == "target" and p["scale"] == want and p.get("t") is None
                  and p.get("contrast_heads") == HEADS.get(p["arm"])
                  and p.get("contrast_rescale") == ("contrast" if p["arm"] in HEADS_SM else None)
                  and p.get("contrast_positions") == CPOS.get(p["arm"])
                  and p.get("contrast_pos_weight") == CW.get(p["arm"])
                  and p.get("contrast_pos_norm_from") is None
                  and p.get("shift_positions") == SHPOS.get(p["arm"])
                  and p.get("shift_rescale") is None and p.get("shift_scale") == SHSCALE.get(p["arm"])
                  and p.get("shift_pos_weight") == SPW.get(p["arm"]))
            cp, cr = p.get("contrast_proj"), p.get("contrast_rem")
            bp_ok = lambda bp: (len(bp) == 24 and set(ids_([q_[0] for q_ in bp])) <= donors12
                                and not ({dd, hh} & set(ids_([q_[0] for q_ in bp])))
                                and all(q_[1] == q_[0].split(":")[0] + ":" + hh for q_ in bp))
            if p["arm"] in SPLIT:
                ok = (ok and cr is None and cp["k"] == 16 and cp["rescale"] == "contrast" and cp["part"] == "par"
                      and cp["basis"] == "pairs" and "null_seed" not in cp and bp_ok(cp.get("basis_pairs") or []))
            elif p["arm"] in LAM:
                ok = (ok and cp is None and cr["k"] == 16 and cr["lam"] == LAM[p["arm"]]
                      and ("null_seed" in cr) == (p["arm"] in NULLS) and bp_ok(cr.get("basis_pairs") or []))
            else:
                ok = ok and cp is None and cr is None
            return ok
        po = all(pool_ok(x) for x in pl)
        seeds_ok = not any(x["patch"].get("contrast_rem") for x in pl)
        return (good == 22 and src == {"new": 1474, "ROUND": 1474} and tg == {"new": 2948} and len(pl) == 2948 - 208
                and po and seeds_ok,
                f"ROUND captures (14 donors + 8 hosts) with G1.0 token sha + span, distinct from new: {good}/22; "
                f"patch sources {dict(src)}, targets {dict(tg)}; pools exclude the cell's donor and host, right kind / "
                f"arm / sign / t / heads / rescale / positions / norms / shift / weights / basis / null: {po}; no tilt rows: {seeds_ok}")
    guarded("round_arms_rebuilt_from_g10_and_used_as_sources", t_variants)

    bad_cf = out / "_tampered_g10.json"
    bad_cf.write_text(a.g10_cf.read_text("utf8").replace('"round": 1', '"round": 9', 1), encoding="utf8")
    run("T5_tampered_g10", fake_adm("pf2", "SELFTEST_PF_0002"), mode="--preflight-only", g10=bad_cf)
    guarded("tampered_g10_counterfactuals_refused", lambda: (
        receipt(out / "T5_tampered_g10")["status"] == "FAIL_A461_MECH_M16"
        and "G1.0 counterfactuals blob pin" in receipt(out / "T5_tampered_g10")["error_message"],
        "one variant round edited: refused at the blob pin"))

    run("T3_extra_lm_call", fake_adm("dbl", "SELFTEST_DBL_0001"), fault="doublefire@50")
    guarded("extra_lm_call_refused_at_prehook", lambda: (
        receipt(out / "T3_extra_lm_call")["status"] == "FAIL_A461_MECH_M16"
        and "LM pre-hook refused" in receipt(out / "T3_extra_lm_call")["error_message"]
        and receipt(out / "T3_extra_lm_call")["denied_prehook_calls"] == 1
        and receipt(out / "T3_extra_lm_call")["physical_prehook_calls"] == 50
        and len(rows(out / "T3_extra_lm_call")) == 49,
        "2nd LM call inside reserved call 50 denied before LM body; physical 50, rows 49"))

    run("T4_reuse", fake_adm("full", "SELFTEST_FULL_0001"))
    guarded("same_approval_reuse_refused_by_ledger", lambda: (
        receipt(out / "T4_reuse")["status"] == "FAIL_A461_MECH_M16"
        and f"ledger consumed {TOTAL}" in receipt(out / "T4_reuse")["error_message"]
        and receipt(out / "T4_reuse")["model_loads"] == 0,
        f"same admission from a new out dir after a complete {TOTAL}-call run: refused, 0 loads"))

    run("P1_gpu_pre_model", gpu_adm("gpu_ok"), backend="gpu", mode="--pre-model-gate-only")
    guarded("gpu_policy_v2_admission_reaches_pre_model_gate", lambda: (
        receipt(out / "P1_gpu_pre_model")["status"] == "COMPLETE_A461_MECH_M16_PRE_MODEL_GATE"
        and receipt(out / "P1_gpu_pre_model")["model_identity_verified"] is True
        and receipt(out / "P1_gpu_pre_model")["model_loads"] == 0
        and receipt(out / "P1_gpu_pre_model")["cuda_initialized"] is False
        and not rb.GPU_QUOTA_ROOT.exists(),
        "synthetic policy-V2 GPU admission passes all gates and stops before load; real ledger untouched"))
    tampered = out / "_tampered_manifest.jsonl"
    lines = a.manifest.read_text("utf8").splitlines()
    t0 = json.loads(lines[300])
    t0["patch"]["classes"] = ["SELF"] if t0["patch"]["classes"] != ["SELF"] else ["CONTEXT"]
    lines[300] = json.dumps(t0, sort_keys=True, separators=(",", ":"))
    tampered.write_text("\n".join(lines) + "\n", encoding="utf8")
    run("P2_gpu_tampered_manifest", gpu_adm("gpu_ok2"), backend="gpu", mode="--pre-model-gate-only", manifest=tampered)
    guarded("gpu_tampered_manifest_refused", lambda: (
        "manifest blob override refused" in receipt(out / "P2_gpu_tampered_manifest")["error_message"],
        "manifest with one patch row's key classes changed: refused before load"))
    run("P3_gpu_plan_override", gpu_adm("gpu_ok3"), backend="gpu", mode="--pre-model-gate-only",
        extra=("--expect-batches", ",".join(["128"] * 23 + ["47", "1"])))
    guarded("gpu_plan_override_refused", lambda: (
        receipt(out / "P3_gpu_plan_override")["status"] == "FAIL_A461_MECH_M16"
        and receipt(out / "P3_gpu_plan_override")["model_loads"] == 0,
        f"refused: {receipt(out / 'P3_gpu_plan_override')['error_message'][:80]}"))
    rr = run("P4_full_gpu_outside_runs_root", gpu_adm("gpu_ok4"), backend="gpu")
    guarded("full_gpu_run_outside_runs_root_refused", lambda: (
        rr.returncode != 0 and not (out / "P4_full_gpu_outside_runs_root").exists()
        and "M16_GPU_RUNS" in rr.stderr, "refused before mkdir"))
    guarded("no_gpu_in_selftest", lambda: (
        all(receipt(d)["gpu_model_loads"] == 0 and receipt(d)["cuda_initialized"] is False
            for d in out.iterdir() if (d / "execution_receipt.json").exists())
        and not rb.GPU_RUNS_ROOT.exists(), "all receipts: gpu_model_loads=0, CUDA never initialized"))

    ok = all(r["verdict"] == "PASS" for r in RESULTS)
    res = {"schema": "JEV_A461_MECH_M16_SELFTEST_V1", "status": "PASS" if ok else "FAIL",
           "passed": sum(r["verdict"] == "PASS" for r in RESULTS), "tests": len(RESULTS), "runner_blob": runner_blob,
           "manifest_blob": rb.file_blob(a.manifest), "results": RESULTS, "gpu_calls": 0}
    (out / "selftest_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("status", "passed", "tests", "runner_blob", "manifest_blob")}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
