#!/usr/bin/env python3
"""A461-MECH-M14 runner CPU self-test (zero GPU; every subprocess CUDA_VISIBLE_DEVICES="").
Same gate/ledger/refusal tests as M13 (A461_mech_m13_selftest_v1.py), plus: the full path on the real 6956-row
manifest (33 arms on 208 rows, 4 M13 replay arms on the 12 rows of the 6 subset cells); the wiring of the AB arms
(shift positions, c_30 weight 0, shift scale), the tilt arms (lam -3, -1, +1, +3 at s 7/16 and 5/16) and the 3x nulls
(pools exclude the cell's donor and host; signs, s, lam, bases, 8 distinct null seeds per cell shared by both s, main
and round; the replayed M13 null keeps its M13 seed); size bookkeeping (every tilt arm and null of a cell has the same
r share and energy share 1 + lam^2 r_share; c_30 weight 0 leaves 1 - e_30; the AB shift at half size has u = 1/2
within the 1e-3 gate); and identities: full with source = target (bitwise); a pool of the donor alone on the host base
= host + delta_B, as is a contrast shift whose pools are the donor's new capture; cs1 rebuilt from a cs arm ==
meanD_host; the contrast restricted to all 16 heads, weight 1 at position 30 and c kept at all 31 positions == the cs
arm (bitwise); weight 0 at 30 == c kept at 29, also with the AB shift (bitwise); the common shift at all 31 positions
== the cs arm; the AB shift with shift_scale 1 == the unscaled AB shift; the tilt (lam 1 and -2) and its null on a
k = 64 basis (the fake width, so r = 0) == the cs arm."""
import argparse, collections, hashlib, importlib.util, json, os, statistics, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_mech_m14_runner_v1.py"
STAGE = "A461_MECH_M14_AB_THRESHOLD_TILT3_GPU"
TOTAL, PLAN = 6956, [128] * 54 + [44]
SUBSET = ("sh_fAB_c29", "cs_s0375", "rem_p1", "rnull_s05_1")   # the M13 replays, on 6 cells only
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
    p = Path(d) / "raw_native_logits_m14.jsonl"
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
    spec = importlib.util.spec_from_file_location("m14", RUNNER)
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
        base = dict(stage=STAGE, mode="GPU", admission_id="SELFTEST_SYNTH_M14_0001",
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
        receipt(out / "T1_preflight")["status"] == "COMPLETE_A461_MECH_M14_PREFLIGHT"
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
        return (r2["status"] == "COMPLETE_A461_MECH_M14" and len(x2) == TOTAL
                and [x["forward_index"] for x in x2] == list(range(1, TOTAL + 1))
                and brs == [(k, 128, 128, "COMPLETE") for k in range(1, 55)] + [(55, 44, 44, "COMPLETE")]
                and r2["physical_prehook_calls"] == TOTAL and r2["denied_prehook_calls"] == 0
                and r2["durable_appends"]["raw_rows"] == TOTAL and len(caps) == 44 and len(files) == 88
                and ok_files and shapes
                and len([k for k in cond if k.startswith("patch_m14_")]) == 74
                and all(v == (6 if k[len("patch_m14_"):].rsplit("_", 1)[0] in SUBSET else 104)
                        for k, v in cond.items() if k.startswith("patch_m14_"))
                # fake explicit-softmax attention is batched over rows: float32 rounding only (<= 1e-6)
                and all(c["cross_row_max_absdiff"] <= 1e-6 for c in caps),
                f"status={r2['status']} rows={len(x2)} batches={len(brs)} captures={len(caps)} files={len(files)} "
                f"(sha ok={ok_files}, shapes ok={shapes}); cross-row max {max(c['cross_row_max_absdiff'] for c in caps):.1e}")
    guarded("fake_full_path_6956_with_44_captures_and_class_files", t_full)
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
    ABN = ("sh_fAB_c29", "abc_s05", "abc_s0375", "abc_s025", "abc_t05")
    SHPOS = dict({n: AB + [29, 30] for n in ABN}, ab_only_c29=AB)
    CW = {n: [[30, 0.0]] for n in SHPOS}
    SHSCALE = {"abc_t05": 0.5}
    SZ = {"_s0437": 0.4375, "_s0312": 0.3125}
    REMS = dict({"rem_p1": 1.0}, **{f"rem_{tg}{k_}": lam for k_ in SZ
                                     for tg, lam in (("m3", -3.0), ("m1", -1.0), ("p1", 1.0), ("p3", 3.0))})
    NULLS = ("rnull_s05_1",) + tuple(f"rnull3{k_}_{i}" for k_ in SZ for i in range(1, 9))
    LAM = dict(REMS, **{n: (1.0 if n == "rnull_s05_1" else 3.0) for n in NULLS})
    S_OF = dict({"cs_s0375": 0.375, "rnull_s05_1": 0.5, "abc_s05": 0.5, "abc_s0375": 0.375, "abc_s025": 0.25},
                **{f"cs{k_}": v_ for k_, v_ in SZ.items()},
                **{n: v_ for n in LAM for k_, v_ in SZ.items() if k_ in n})
    SPLIT = ()
    EXPECT = dict({"full": ("full", []), "meanD_host": ("pool", BULK)},
                  **{n: ("cshift", BULK) for n in ["cs_s0375", "cs_s0437", "cs_s0312"] + list(SHPOS) + list(LAM)})
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
        # tilt arms: r is orthogonal to c, so the energy share is 1 + lam^2 r_share, the same r_share for every arm
        # and null of a cell (a 3x null has the norm of 3 r)
        tl = [(n, d, h, s_) for (d, h, n, s_) in rw if n in LAM]
        rsh = lambda d, h, s_: cst("rem_p1_s0437", d, h, s_)["rem_energy_share"]
        rsame = max(abs(cst(n, d, h, s_)["rem_energy_share"] - rsh(d, h, s_)) for n, d, h, s_ in tl)
        tsh = max(abs(sh(n, d, h, s_) - (1 + LAM[n] ** 2 * rsh(d, h, s_))) for n, d, h, s_ in tl)
        terr = max(cst(n, d, h, s_)["tilt_err"] for n, d, h, s_ in tl)
        rmin = min(rsh(d, h, s_) for d, h, s_ in keys)
        ncos = max(abs(cst(n, d, h, s_)["null_cos_to_rem_median"]) for n, d, h, s_ in tl if n in NULLS)
        # c_30 weight 0: the energy share is 1 - e_30
        cl = [(n, d, h, s_) for (d, h, n, s_) in rw if n in CW]
        wsh = max(abs(sh(n, d, h, s_) - (1 - cst(n, d, h, s_)["pos_share_before"]["30"])) for n, d, h, s_ in cl)
        u_ok = max(abs(rw[(d, h, n, s_)]["alpha_stats"]["shift_u_max"] - SHSCALE.get(n, 1.0)) for n, d, h, s_ in cl)
        cnt = collections.Counter(x["patch"]["arm"] for x in x2 if x.get("patch"))
        ops_ok = all((x["patch"]["op"], x["patch"]["classes"]) == EXPECT[x["patch"]["arm"]] for x in x2 if x.get("patch"))
        sub_cells = {(d, h) for (d, h, n, _s) in rw if n in SUBSET}
        sub_ok = len(sub_cells) == 6 and sorted(collections.Counter(h[:8] for _d, h in sub_cells).values()) == [2, 2, 2]
        return (distinct == len(keys) == 208 and sorted(arms) == sorted(EXPECT) and ops_ok and sub_ok
                and cnt == {n: (12 if n in SUBSET else 208) for n in EXPECT}
                and rsame <= 1e-12 and tsh <= 1e-6 and terr <= 1e-6 and rmin > 0 and wsh <= 1e-6 and u_ok <= 1e-12,
                f"{len(DISTINCT)} full arms distinct in {distinct}/{len(keys)} (cell, source); {len(SUBSET)} replay arms "
                f"on 6 subset cells, 2 per host: {sub_ok}; tilt arms share r per cell ({rsame:.1e}), energy share = 1 + "
                f"lam^2 r_share (max {tsh:.1e}), tilt gate max {terr:.1e}, min r_share {rmin:.3g}, |null cos to r| "
                f"median max {ncos:.3f}; c_30 weight 0 share = 1 - e_30 ({wsh:.1e}); AB shift u as planned ({u_ok:.1e}); "
                f"{len(arms)} arms; op/classes match the frozen arm table: {ops_ok}")
    guarded("thirtyseven_arms_wiring_and_size_bookkeeping", t_wiring)

    def t_size():
        rr = [x for x in x2 if x.get("patch") and x["patch"].get("contrast_rem")]
        rh = [x for x in x2 if x.get("patch") and x["patch"].get("shift_scale")]
        terr = max(x["size_rel_err"] for x in rr)
        herr = max(x["size_rel_err"] for x in rh)
        ro = round(statistics.median(x["contrast_stats"]["rem_over_c_median"] for x in rr), 4)
        pe = round(statistics.median(x["contrast_stats"]["par_energy_share"] for x in rr), 4)
        return (len(rr) == 24 * 208 + 2 * 12 and terr <= 1e-6 and len(rh) == 208 and herr <= 1e-3,
                f"{len(rr)} tilt / null rows: tilt gate max {terr:.1e}; median ||r|| / ||c|| {ro}, median par energy "
                f"share {pe}; {len(rh)} half-size AB shift rows: shift size gate max rel err {herr:.1e}")
    guarded("tilt_and_shift_arms_pass_the_size_gates", t_size)

    def t_allrows():
        base = {(x["target_scene"], x["target_arm"]): {q["id"]: q["logits"] for q in x["questions"]} for x in x2
                if x.get("capture") and x.get("source_kind") == "host"}
        pr = [x for x in x2 if x.get("patch")]
        moved = sum({q["id"]: q["logits"] for q in x["questions"]}["conflicting_vote"] != base[(x["target_scene"], x["target_arm"])]["conflicting_vote"]
                    and {q["id"]: q["logits"] for q in x["questions"]}["certificate_action"] != base[(x["target_scene"], x["target_arm"])]["certificate_action"]
                    for x in pr)
        return (len(base) == 16 and len(pr) == 6912 and moved >= 6912 - 1040,
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
    csr = pick("cs_s0437", "main")
    cs_d = dict(csr, condition="cshift_donor_only",
                patch=dict(csr["patch"], pool_new=[md0["patch"]["source"]], pool_round=[md0["patch"]["source"]], scale=2.0))
    c1r = pick("cs_s0437", "round")
    cs1m = dict(csr, condition="cs1_main", patch=dict(csr["patch"], arm="cs1", scale=-0.5))
    ch_all = dict(c1r, condition="contrast_all_heads", patch=dict(c1r["patch"], arm="ch_all", contrast_heads=list(range(16))))
    cw1 = dict(c1r, condition="contrast_weight_1", patch=dict(c1r["patch"], arm="cw1", contrast_pos_weight=[[30, 1.0]]))
    cw0 = dict(c1r, condition="contrast_weight_0", patch=dict(c1r["patch"], arm="cw0", contrast_pos_weight=[[30, 0.0]]))
    cpp = dict(c1r, condition="cpos29_round", patch=dict(c1r["patch"], arm="cpos29", contrast_positions=[29]))
    cpos_all = dict(c1r, condition="contrast_all_positions",
                    patch=dict(c1r["patch"], arm="cpos_all", contrast_positions=list(range(31))))
    sh_all = dict(c1r, condition="shift_all_positions", patch=dict(c1r["patch"], arm="sh_all", shift_positions=list(range(31))))
    abr = pick("abc_s05", "round")
    ab_s1 = dict(abr, condition="ab_shift_scale_1", patch=dict(abr["patch"], arm="ab_s1", shift_scale=1.0))
    ab_pos = dict(abr, condition="ab_c29_via_positions",
                  patch=dict({k_: v_ for k_, v_ in abr["patch"].items() if k_ != "contrast_pos_weight"}, arm="ab_pos",
                             contrast_positions=[29]))
    rr0 = pick("rem_p1_s0437", "round")
    rem64 = dict(rr0, condition="tilt_full_width", patch=dict(rr0["patch"], arm="rem64", contrast_rem=dict(
        rr0["patch"]["contrast_rem"], k=64)))
    rem64m = dict(rr0, condition="tilt_full_width_m2", patch=dict(rr0["patch"], arm="rem64m", contrast_rem=dict(
        rr0["patch"]["contrast_rem"], k=64, lam=-2.0)))
    rem64n = dict(rr0, condition="tilt_full_width_null", patch=dict(rr0["patch"], arm="rem64n", contrast_rem=dict(
        rr0["patch"]["contrast_rem"], k=64, null_seed=12345)))
    mini = [dict(m, forward_index=i + 1, run=1) for i, m in enumerate(
        caps_rows + [idf, pool_d, cs_d, dict(c1r, condition="cs1_round"), ch_all, cw1, cw0, cpp, cpos_all, sh_all,
                     dict(abr, condition="ab_c29_round"), ab_pos, rem64, rem64m, rem64n,
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
              "tilt_full_width_vs_cs1": dev(pr["tilt_full_width"], pr["cs1_round"]),
              "tilt_full_width_m2_vs_cs1": dev(pr["tilt_full_width_m2"], pr["cs1_round"]),
              "tilt_full_width_null_vs_cs1": dev(pr["tilt_full_width_null"], pr["cs1_round"]),
              "cs1_vs_meanD_host": dev(pr["cs1_main"], pr["meanD_main"]),
              "ab_shift_scale_1_vs_unscaled": dev(pr["ab_shift_scale_1"], pr["ab_c29_round"])}
        r64 = max(pr[n]["contrast_stats"]["rem_energy_share"]
                  for n in ("tilt_full_width", "tilt_full_width_m2", "tilt_full_width_null"))
        return (receipt(out / "T6_identity")["status"] == "COMPLETE_A461_MECH_M14" and len(pr) == 18
                and pr["identity_full"]["questions"] == base["questions"]
                and pr["contrast_all_heads"]["questions"] == pr["cs1_round"]["questions"]
                and pr["contrast_weight_1"]["questions"] == pr["cs1_round"]["questions"]
                and pr["contrast_all_positions"]["questions"] == pr["cs1_round"]["questions"]
                and pr["ab_c29_via_positions"]["questions"] == pr["ab_c29_round"]["questions"]
                and abs(pr["contrast_all_heads"]["contrast_stats"]["energy_share"] - 1) < 1e-9
                and abs(pr["contrast_weight_1"]["contrast_stats"]["energy_share"] - 1) < 1e-9
                and abs(pr["contrast_all_positions"]["contrast_stats"]["energy_share"] - 1) < 1e-9
                and r64 <= 1e-9 and max(d_.values()) <= 1e-4,
                "full no-op, all-16-heads contrast, weight 1 at position 30 and all-31-positions contrast == the cs "
                "arm (cs_s0437), bitwise; the AB shift with c_30 weight 0 == with c kept at 29 only, bitwise; weight 0 "
                "at 30 == cpos29; cs1 rebuilt == meanD_host; AB shift_scale 1 == unscaled; the tilt and its null on a "
                f"k = 64 basis (r = 0, r_share max {r64:.1e}) == the cs arm; max |logit "
                "diff| " + ", ".join(f"{k} {v:.1e}" for k, v in sorted(d_.items())))
    guarded("identities_pool_heads_positions_weights_shift_and_tilt", t_identity)

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
                  and p.get("shift_rescale") is None and p.get("shift_scale") == SHSCALE.get(p["arm"]))
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
        sd = collections.defaultdict(set)
        for x in pl:
            if x["patch"]["arm"].startswith("rnull3_"):
                sd[(x["donor"], x["host"])].add((x["patch"]["arm"].rsplit("_", 1)[1],
                                                 x["patch"]["contrast_rem"]["null_seed"]))
        m13seed = lambda x: int(hashlib.sha256(f"A461_M13_RNULL|16|{x['donor']}|{x['host']}|1".encode()).hexdigest()[:8], 16)
        seeds_ok = (len(sd) == 104 and all(len(v) == 8 and len({s_ for _i, s_ in v}) == 8 for v in sd.values())
                    and all(x["patch"]["contrast_rem"]["null_seed"] == m13seed(x) for x in pl
                            if x["patch"]["arm"] == "rnull_s05_1"))
        return (good == 22 and src == {"new": 3456, "ROUND": 3456} and tg == {"new": 6912} and len(pl) == 6912 - 208
                and po and seeds_ok,
                f"ROUND captures (14 donors + 8 hosts) with G1.0 token sha + span, distinct from new: {good}/22; "
                f"patch sources {dict(src)}, targets {dict(tg)}; pools exclude the cell's donor and host, right kind / "
                f"arm / sign / t / heads / rescale / positions / norms / shift / weights / basis / null: {po}; 8 distinct null seeds per cell, shared by both s, main and round, and the M13 seed on the replayed null: {seeds_ok}")
    guarded("round_arms_rebuilt_from_g10_and_used_as_sources", t_variants)

    bad_cf = out / "_tampered_g10.json"
    bad_cf.write_text(a.g10_cf.read_text("utf8").replace('"round": 1', '"round": 9', 1), encoding="utf8")
    run("T5_tampered_g10", fake_adm("pf2", "SELFTEST_PF_0002"), mode="--preflight-only", g10=bad_cf)
    guarded("tampered_g10_counterfactuals_refused", lambda: (
        receipt(out / "T5_tampered_g10")["status"] == "FAIL_A461_MECH_M14"
        and "G1.0 counterfactuals blob pin" in receipt(out / "T5_tampered_g10")["error_message"],
        "one variant round edited: refused at the blob pin"))

    run("T3_extra_lm_call", fake_adm("dbl", "SELFTEST_DBL_0001"), fault="doublefire@50")
    guarded("extra_lm_call_refused_at_prehook", lambda: (
        receipt(out / "T3_extra_lm_call")["status"] == "FAIL_A461_MECH_M14"
        and "LM pre-hook refused" in receipt(out / "T3_extra_lm_call")["error_message"]
        and receipt(out / "T3_extra_lm_call")["denied_prehook_calls"] == 1
        and receipt(out / "T3_extra_lm_call")["physical_prehook_calls"] == 50
        and len(rows(out / "T3_extra_lm_call")) == 49,
        "2nd LM call inside reserved call 50 denied before LM body; physical 50, rows 49"))

    run("T4_reuse", fake_adm("full", "SELFTEST_FULL_0001"))
    guarded("same_approval_reuse_refused_by_ledger", lambda: (
        receipt(out / "T4_reuse")["status"] == "FAIL_A461_MECH_M14"
        and f"ledger consumed {TOTAL}" in receipt(out / "T4_reuse")["error_message"]
        and receipt(out / "T4_reuse")["model_loads"] == 0,
        f"same admission from a new out dir after a complete {TOTAL}-call run: refused, 0 loads"))

    run("P1_gpu_pre_model", gpu_adm("gpu_ok"), backend="gpu", mode="--pre-model-gate-only")
    guarded("gpu_policy_v2_admission_reaches_pre_model_gate", lambda: (
        receipt(out / "P1_gpu_pre_model")["status"] == "COMPLETE_A461_MECH_M14_PRE_MODEL_GATE"
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
        extra=("--expect-batches", ",".join(["128"] * 54 + ["43", "1"])))
    guarded("gpu_plan_override_refused", lambda: (
        receipt(out / "P3_gpu_plan_override")["status"] == "FAIL_A461_MECH_M14"
        and receipt(out / "P3_gpu_plan_override")["model_loads"] == 0,
        f"refused: {receipt(out / 'P3_gpu_plan_override')['error_message'][:80]}"))
    rr = run("P4_full_gpu_outside_runs_root", gpu_adm("gpu_ok4"), backend="gpu")
    guarded("full_gpu_run_outside_runs_root_refused", lambda: (
        rr.returncode != 0 and not (out / "P4_full_gpu_outside_runs_root").exists()
        and "M14_GPU_RUNS" in rr.stderr, "refused before mkdir"))
    guarded("no_gpu_in_selftest", lambda: (
        all(receipt(d)["gpu_model_loads"] == 0 and receipt(d)["cuda_initialized"] is False
            for d in out.iterdir() if (d / "execution_receipt.json").exists())
        and not rb.GPU_RUNS_ROOT.exists(), "all receipts: gpu_model_loads=0, CUDA never initialized"))

    ok = all(r["verdict"] == "PASS" for r in RESULTS)
    res = {"schema": "JEV_A461_MECH_M14_SELFTEST_V1", "status": "PASS" if ok else "FAIL",
           "passed": sum(r["verdict"] == "PASS" for r in RESULTS), "tests": len(RESULTS), "runner_blob": runner_blob,
           "manifest_blob": rb.file_blob(a.manifest), "results": RESULTS, "gpu_calls": 0}
    (out / "selftest_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("status", "passed", "tests", "runner_blob", "manifest_blob")}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
