#!/usr/bin/env python3
"""A461-MECH-M12 runner CPU self-test (zero GPU; every subprocess CUDA_VISIBLE_DEVICES="").
Same gate/ledger/refusal tests as M11 (A461_mech_m11_selftest_v1.py), plus the size gates of the subspace parts and
the cosine nulls, the wiring of the weight, dose, field-shift and null arms (pools exclude the cell's donor and host;
signs, positions, weights, shift positions, bases, 5 distinct null seeds per cell and part shared by main and round),
size bookkeeping (dose arms keep the position share; weighted arms' energy share is 1 + (w^2 - 1) e_30; nulls keep the
part's share and cosine), and identities: full with source = target (bitwise); a pool of the donor alone on the host
base = host + delta_B, as is a contrast shift whose pools are the donor's new capture; the contrast restricted to all
16 heads, weight 1 at position 30 and c kept at all 31 positions == cs1 (bitwise); weight 0 at 30 == cpos29; the
common shift at all 31 positions == cs1, also through the rescaled-shift path with factor 1, and the shift at 29-30
with factor 1 == sh2930 (float rounding); the par part on a k = 64 basis (the fake width) == cs1, as is its cosine
null (cosine 1)."""
import argparse, collections, hashlib, importlib.util, json, os, statistics, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "A461_mech_m12_runner_v1.py"
STAGE = "A461_MECH_M12_P30_FIELDS_COSNULL_GPU"
TOTAL, PLAN = 7740, [128] * 60 + [60]
RESULTS = []
# R2: children died with "libgomp: Thread creation failed" under the shared per-user thread limit
THREADS = {"OMP_NUM_THREADS": "8", "MKL_NUM_THREADS": "8"}
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
    p = Path(d) / "raw_native_logits_m12.jsonl"
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
    spec = importlib.util.spec_from_file_location("m12", RUNNER)
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
        base = dict(stage=STAGE, mode="GPU", admission_id="SELFTEST_SYNTH_M12_0001",
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
        receipt(out / "T1_preflight")["status"] == "COMPLETE_A461_MECH_M12_PREFLIGHT"
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
        return (r2["status"] == "COMPLETE_A461_MECH_M12" and len(x2) == TOTAL
                and [x["forward_index"] for x in x2] == list(range(1, TOTAL + 1))
                and brs == [(k, 128, 128, "COMPLETE") for k in range(1, 61)] + [(61, 60, 60, "COMPLETE")]
                and r2["physical_prehook_calls"] == TOTAL and r2["denied_prehook_calls"] == 0
                and r2["durable_appends"]["raw_rows"] == TOTAL and len(caps) == 44 and len(files) == 88
                and ok_files and shapes
                and len([k for k in cond if k.startswith("patch_m12_")]) == 74
                and all(v == 104 for k, v in cond.items() if k.startswith("patch_m12_"))
                # fake explicit-softmax attention is batched over rows: float32 rounding only (<= 1e-6)
                and all(c["cross_row_max_absdiff"] <= 1e-6 for c in caps),
                f"status={r2['status']} rows={len(x2)} batches={len(brs)} captures={len(caps)} files={len(files)} "
                f"(sha ok={ok_files}, shapes ok={shapes}); cross-row max {max(c['cross_row_max_absdiff'] for c in caps):.1e}")
    guarded("fake_full_path_7740_with_44_captures_and_class_files", t_full)
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
    CPOS = {"cpos29": [29], "cpos29_s05": [29], "cpos29_s025": [29]}
    S_OF = {"cpos29_s05": 0.5, "cpos29_s025": 0.25, "cs_s05": 0.5, "cw30_m1_s05": 0.5, "cw30_p2_s05": 0.5,
            "cs_s025": 0.25, "cw30_m1_s025": 0.25}
    CW = {"cw30_m1": [[30, -1.0]], "cw30_p2": [[30, 2.0]], "cw30_m1_s05": [[30, -1.0]], "cw30_p2_s05": [[30, 2.0]],
          "cw30_m1_s025": [[30, -1.0]]}
    FIELDS = {"AUTH": list(range(0, 7)), "BLOCK": list(range(7, 13)), "KIND": list(range(13, 18)),
              "RECV": list(range(18, 25)), "RKEY": list(range(25, 29))}
    SHPOS = dict({"sh2930": [29, 30], "sh0_28": list(range(29))},
                 **{f"sh_f{f}": sorted(v + [29, 30]) for f, v in FIELDS.items()},
                 **{f"sh_x{f}": [i for i in range(31) if i not in v] for f, v in FIELDS.items()})
    NULLS = tuple(f"ccos_{p_}_s{i}" for p_ in ("par", "perp") for i in range(1, 6))
    SPLIT = ("cpar16_sm", "cperp16_sm") + NULLS
    EXPECT = dict({"full": ("full", []), "meanD_host": ("pool", BULK)},
                  **{n: ("cshift", BULK) for n in ["cs1", "cs_s05", "cs_s025"] + list(CPOS) + list(CW) + list(SHPOS)
                     + list(SPLIT)})
    # c at 30 is small in the fake model, so the weighted arms may round to their w = 0 / +1 neighbours
    DISTINCT = tuple(n for n in EXPECT if n not in CW)

    def dev(x, y):
        return max(abs(u - v) for q, qb in zip(x["questions"], y["questions"]) for u, v in zip(q["logits"], qb["logits"]))

    def t_wiring():
        lg = {(x["donor"], x["host"], x["patch"]["arm"], x["source_kind"]): json.dumps(x["questions"])
              for x in x2 if x.get("patch")}
        rw = {(x["donor"], x["host"], x["patch"]["arm"], x["source_kind"]): x for x in x2 if x.get("patch")}
        keys = {(d, h, src) for (d, h, _a, src) in lg}
        arms = sorted({a_ for (_d, _h, a_, _s) in lg})
        distinct = sum(len({lg[(d, h, arm, src)] for arm in DISTINCT}) == len(DISTINCT) for d, h, src in keys)
        cs1 = max(dev(rw[(d, h, "cs1", src)], rw[(d, h, "meanD_host", src)]) for d, h, src in keys)
        cst = lambda n, d, h, s_: rw[(d, h, n, s_)]["contrast_stats"]
        sh = lambda n, d, h, s_: cst(n, d, h, s_)["energy_share"]
        split_sum = max(abs(sh("cpar16_sm", d, h, s_) + sh("cperp16_sm", d, h, s_) - 1) for d, h, s_ in keys)
        dose = max(abs(sh(n, d, h, s_) - sh("cpos29", d, h, s_)) for n in ("cpos29_s05", "cpos29_s025") for d, h, s_ in keys)
        # weighted arms: c_29 kept, c_30 scaled by w, so the energy share is 1 + (w^2 - 1) e_30 with e_30 = 1 - e(cpos29)
        wsh = max(abs(sh(n, d, h, s_) - (1 + (CW[n][0][1] ** 2 - 1) * (1 - sh("cpos29", d, h, s_))))
                  for n in CW for d, h, s_ in keys)
        e30 = max(abs(cst(n, d, h, s_)["pos_share_before"]["30"] - (1 - sh("cpos29", d, h, s_))) for n in CW
                  for d, h, s_ in keys)
        # nulls carry the part's energy share and cosine (both computed before the null replaces the part)
        nsh = max(abs(sh(n, d, h, s_) - sh("c" + n.split("_")[1] + "16_sm", d, h, s_))
                  + abs(cst(n, d, h, s_)["cos_median"] - cst("c" + n.split("_")[1] + "16_sm", d, h, s_)["cos_median"])
                  for n in NULLS for d, h, s_ in keys)
        nerr = max(cst(n, d, h, s_)["null_err"] for n in NULLS for d, h, s_ in keys)
        u_plain = max(abs(rw[(d, h, n, s_)]["alpha_stats"]["shift_u_max"] - 1) for n in SHPOS for d, h, s_ in keys)
        cnt = collections.Counter(x["patch"]["arm"] for x in x2 if x.get("patch"))
        ops_ok = all((x["patch"]["op"], x["patch"]["classes"]) == EXPECT[x["patch"]["arm"]] for x in x2 if x.get("patch"))
        return (distinct == len(keys) == 208 and sorted(arms) == sorted(EXPECT) and set(cnt.values()) == {208} and ops_ok
                and cs1 <= 1e-4 and split_sum <= 1e-4 and dose <= 1e-6 and wsh <= 1e-5 and e30 <= 3e-6
                and nsh <= 1e-9 and nerr <= 1e-6 and u_plain == 0,
                f"{len(DISTINCT)} arms distinct in {distinct}/{len(keys)} (cell, source); cs1 vs meanD_host {cs1:.1e}; "
                f"par + perp - 1 max {split_sum:.1e}; dose arms keep the position share ({dose:.1e}); weighted arms' "
                f"energy share = 1 + (w^2 - 1) e_30 (max {wsh:.1e}; e_30 {e30:.1e}); nulls keep the part's share and "
                f"cosine ({nsh:.1e}), null gate max {nerr:.1e}; field shifts unscaled ({u_plain}); {len(arms)} arms x 208; "
                f"op/classes match the frozen arm table: {ops_ok}")
    guarded("thirtyseven_arms_wiring_and_size_bookkeeping", t_wiring)

    def t_size():
        rs = [x for x in x2 if x.get("patch") and x["patch"].get("contrast_proj")]
        gate = max(x["size_rel_err"] for x in rs)
        cap = max(x["contrast_stats"]["alpha_max"] for x in rs)
        nerr = max(x["contrast_stats"].get("null_err", 0.0) for x in rs)
        cos = {n: round(statistics.median(x["contrast_stats"]["cos_median"] for x in rs if x["patch"]["arm"] == n), 4)
               for n in ("cpar16_sm", "cperp16_sm")}
        return (len(rs) == 12 * 208 and gate <= 1e-3 and cap <= 10.0 and nerr <= 1e-6,
                f"{len(rs)} subspace / null rows: runner size gate max rel err {gate:.1e}; part factor max {cap} <= 10; "
                f"cosine-null gate max {nerr:.1e}; median cosine to c of the parts {cos}")
    guarded("parts_and_cosine_nulls_pass_the_size_gates", t_size)

    def t_allrows():
        base = {(x["target_scene"], x["target_arm"]): {q["id"]: q["logits"] for q in x["questions"]} for x in x2
                if x.get("capture") and x.get("source_kind") == "host"}
        pr = [x for x in x2 if x.get("patch")]
        moved = sum({q["id"]: q["logits"] for q in x["questions"]}["conflicting_vote"] != base[(x["target_scene"], x["target_arm"])]["conflicting_vote"]
                    and {q["id"]: q["logits"] for q in x["questions"]}["certificate_action"] != base[(x["target_scene"], x["target_arm"])]["certificate_action"]
                    for x in pr)
        return (len(base) == 16 and len(pr) == 7696 and moved >= 7696 - 1040,
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
    csr = pick("cs1", "main")
    cs_d = dict(csr, condition="cshift_donor_only",
                patch=dict(csr["patch"], pool_new=[md0["patch"]["source"]], pool_round=[md0["patch"]["source"]], scale=2.0))
    c1r = pick("cs1", "round")
    ch_all = dict(c1r, condition="contrast_all_heads", patch=dict(c1r["patch"], arm="ch_all", contrast_heads=list(range(16))))
    cw1 = dict(c1r, condition="contrast_weight_1", patch=dict(c1r["patch"], arm="cw1", contrast_pos_weight=[[30, 1.0]]))
    cpp = pick("cpos29", "round")
    cpos_all = dict(cpp, condition="contrast_all_positions",
                    patch=dict(cpp["patch"], arm="cpos_all", contrast_positions=list(range(31))))
    cw0 = dict(c1r, condition="contrast_weight_0", patch=dict(c1r["patch"], arm="cw0", contrast_pos_weight=[[30, 0.0]]))
    shp = pick("sh2930", "round")
    sh_all = dict(shp, condition="shift_all_positions", patch=dict(shp["patch"], arm="sh_all", shift_positions=list(range(31))))
    sh_all_u1 = dict(shp, condition="shift_all_positions_u1",
                     patch=dict(shp["patch"], arm="sh_all_u1", shift_positions=list(range(31)), shift_scale=1.0))
    sh_u1 = dict(shp, condition="shift_2930_u1", patch=dict(shp["patch"], arm="sh_u1", shift_scale=1.0))
    cpr = pick("cpar16_sm", "round")
    par64 = dict(cpr, condition="par_full_width", patch=dict(cpr["patch"], arm="par64",
                                                             contrast_proj=dict(cpr["patch"]["contrast_proj"], k=64)))
    par64n = dict(cpr, condition="par_full_width_null", patch=dict(cpr["patch"], arm="par64n", contrast_proj=dict(
        cpr["patch"]["contrast_proj"], k=64, null_seed=12345)))
    mini = [dict(m, forward_index=i + 1, run=1) for i, m in enumerate(
        caps_rows + [idf, pool_d, cs_d, dict(c1r, condition="cs1_round"), ch_all, cw1, cpos_all, cw0,
                     dict(cpp, condition="cpos29_round"), sh_all, par64, par64n, sh_all_u1, sh_u1,
                     dict(shp, condition="sh2930_round")])]
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
              "shift_all_positions_u1_vs_cs1": dev(pr["shift_all_positions_u1"], pr["cs1_round"]),
              "shift_2930_u1_vs_sh2930": dev(pr["shift_2930_u1"], pr["sh2930_round"]),
              "par_full_width_vs_cs1": dev(pr["par_full_width"], pr["cs1_round"]),
              "par_full_width_null_vs_cs1": dev(pr["par_full_width_null"], pr["cs1_round"])}
        return (receipt(out / "T6_identity")["status"] == "COMPLETE_A461_MECH_M12" and len(pr) == 15
                and pr["identity_full"]["questions"] == base["questions"]
                and pr["contrast_all_heads"]["questions"] == pr["cs1_round"]["questions"]
                and pr["contrast_weight_1"]["questions"] == pr["cs1_round"]["questions"]
                and pr["contrast_all_positions"]["questions"] == pr["cs1_round"]["questions"]
                and abs(pr["contrast_all_heads"]["contrast_stats"]["energy_share"] - 1) < 1e-9
                and abs(pr["contrast_weight_1"]["contrast_stats"]["energy_share"] - 1) < 1e-9
                and abs(pr["contrast_all_positions"]["contrast_stats"]["energy_share"] - 1) < 1e-9
                and abs(pr["par_full_width_null"]["contrast_stats"]["cos_median"] - 1) < 1e-6
                and max(d_.values()) <= 1e-4 and abs(pr["par_full_width"]["contrast_stats"]["energy_share"] - 1) < 1e-4,
                "full no-op, all-16-heads contrast, weight 1 at position 30 and all-31-positions contrast == cs1, "
                "bitwise; weight 0 at 30 == cpos29; the rescaled-shift path with factor 1 == the plain shift; the cosine "
                "null of a cosine-1 part == cs1; max |logit diff| "
                + ", ".join(f"{k} {v:.1e}" for k, v in sorted(d_.items())))
    guarded("identities_pool_heads_positions_weights_shift_and_null", t_identity)

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
                  and p.get("shift_rescale") is None and p.get("shift_scale") is None)
            cp = p.get("contrast_proj")
            if p["arm"] in SPLIT:
                bp = cp.get("basis_pairs") or []
                ok = (ok and cp["k"] == 16 and cp["rescale"] == "contrast"
                      and cp["part"] == ("perp" if "perp" in p["arm"] else "par")
                      and cp["basis"] == "pairs" and ("null_seed" in cp) == (p["arm"] in NULLS)
                      and len(bp) == 24 and set(ids_([q_[0] for q_ in bp])) <= donors12
                      and not ({dd, hh} & set(ids_([q_[0] for q_ in bp])))
                      and all(q_[1] == q_[0].split(":")[0] + ":" + hh for q_ in bp))
            else:
                ok = ok and cp is None
            return ok
        po = all(pool_ok(x) for x in pl)
        sd = collections.defaultdict(set)
        for x in pl:
            if x["patch"]["arm"] in NULLS:
                sd[(x["donor"], x["host"], x["patch"]["contrast_proj"]["part"])].add(
                    (x["patch"]["arm"], x["patch"]["contrast_proj"]["null_seed"]))
        seeds_ok = len(sd) == 208 and all(len(v) == 5 and len({s_ for _a, s_ in v}) == 5 for v in sd.values())
        return (good == 22 and src == {"new": 3848, "ROUND": 3848} and tg == {"new": 7696} and len(pl) == 208 * 36
                and po and seeds_ok,
                f"ROUND captures (14 donors + 8 hosts) with G1.0 token sha + span, distinct from new: {good}/22; "
                f"patch sources {dict(src)}, targets {dict(tg)}; pools exclude the cell's donor and host, right kind / "
                f"arm / sign / t / heads / rescale / positions / norms / shift / weights / basis / null: {po}; 5 distinct null seeds per cell and part, shared by main and round: {seeds_ok}")
    guarded("round_arms_rebuilt_from_g10_and_used_as_sources", t_variants)

    bad_cf = out / "_tampered_g10.json"
    bad_cf.write_text(a.g10_cf.read_text("utf8").replace('"round": 1', '"round": 9', 1), encoding="utf8")
    run("T5_tampered_g10", fake_adm("pf2", "SELFTEST_PF_0002"), mode="--preflight-only", g10=bad_cf)
    guarded("tampered_g10_counterfactuals_refused", lambda: (
        receipt(out / "T5_tampered_g10")["status"] == "FAIL_A461_MECH_M12"
        and "G1.0 counterfactuals blob pin" in receipt(out / "T5_tampered_g10")["error_message"],
        "one variant round edited: refused at the blob pin"))

    run("T3_extra_lm_call", fake_adm("dbl", "SELFTEST_DBL_0001"), fault="doublefire@50")
    guarded("extra_lm_call_refused_at_prehook", lambda: (
        receipt(out / "T3_extra_lm_call")["status"] == "FAIL_A461_MECH_M12"
        and "LM pre-hook refused" in receipt(out / "T3_extra_lm_call")["error_message"]
        and receipt(out / "T3_extra_lm_call")["denied_prehook_calls"] == 1
        and receipt(out / "T3_extra_lm_call")["physical_prehook_calls"] == 50
        and len(rows(out / "T3_extra_lm_call")) == 49,
        "2nd LM call inside reserved call 50 denied before LM body; physical 50, rows 49"))

    run("T4_reuse", fake_adm("full", "SELFTEST_FULL_0001"))
    guarded("same_approval_reuse_refused_by_ledger", lambda: (
        receipt(out / "T4_reuse")["status"] == "FAIL_A461_MECH_M12"
        and f"ledger consumed {TOTAL}" in receipt(out / "T4_reuse")["error_message"]
        and receipt(out / "T4_reuse")["model_loads"] == 0,
        f"same admission from a new out dir after a complete {TOTAL}-call run: refused, 0 loads"))

    run("P1_gpu_pre_model", gpu_adm("gpu_ok"), backend="gpu", mode="--pre-model-gate-only")
    guarded("gpu_policy_v2_admission_reaches_pre_model_gate", lambda: (
        receipt(out / "P1_gpu_pre_model")["status"] == "COMPLETE_A461_MECH_M12_PRE_MODEL_GATE"
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
        extra=("--expect-batches", ",".join(["128"] * 60 + ["59", "1"])))
    guarded("gpu_plan_override_refused", lambda: (
        receipt(out / "P3_gpu_plan_override")["status"] == "FAIL_A461_MECH_M12"
        and receipt(out / "P3_gpu_plan_override")["model_loads"] == 0,
        f"refused: {receipt(out / 'P3_gpu_plan_override')['error_message'][:80]}"))
    rr = run("P4_full_gpu_outside_runs_root", gpu_adm("gpu_ok4"), backend="gpu")
    guarded("full_gpu_run_outside_runs_root_refused", lambda: (
        rr.returncode != 0 and not (out / "P4_full_gpu_outside_runs_root").exists()
        and "M12_GPU_RUNS" in rr.stderr, "refused before mkdir"))
    guarded("no_gpu_in_selftest", lambda: (
        all(receipt(d)["gpu_model_loads"] == 0 and receipt(d)["cuda_initialized"] is False
            for d in out.iterdir() if (d / "execution_receipt.json").exists())
        and not rb.GPU_RUNS_ROOT.exists(), "all receipts: gpu_model_loads=0, CUDA never initialized"))

    ok = all(r["verdict"] == "PASS" for r in RESULTS)
    res = {"schema": "JEV_A461_MECH_M12_SELFTEST_V1", "status": "PASS" if ok else "FAIL",
           "passed": sum(r["verdict"] == "PASS" for r in RESULTS), "tests": len(RESULTS), "runner_blob": runner_blob,
           "manifest_blob": rb.file_blob(a.manifest), "results": RESULTS, "gpu_calls": 0}
    (out / "selftest_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({k: res[k] for k in ("status", "passed", "tests", "runner_blob", "manifest_blob")}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
