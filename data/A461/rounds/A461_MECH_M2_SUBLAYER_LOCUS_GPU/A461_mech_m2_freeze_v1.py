#!/usr/bin/env python3
"""A461-MECH-M2 R1: CPU freeze of the layer-wise and sublayer (mixer vs MLP) locus test on kev-4B (zero forwards).

M1 (c235549) showed that the donor's L11 append-span state carries a signed conflict evaluation:
the original-vote span repairs failing hosts (53/104) while the same span with only the round changed
does not (1/104) and pushes hosts toward no-conflict. M2 asks WHERE that evaluation enters the span:
  F  formation: residual-stream (layer-output) span patches at L7, L8, L9, L10 (L11 is the pinned M1 run)
  W  writer: at L8..L11, replace ONLY the token-mixer output (linear_attn / self_attn) or ONLY the MLP
     output at the span positions with the donor's own sublayer output; the rest of the host layer is
     recomputed in host context
Every arm runs twice, source = donor new span (main) and donor ROUND span (same form, no conflict), so
each component/layer has its own specificity contrast. Units: the 104 cross-group cells of M1/K-C
(14 donors x 8 hosts minus same-group pairs). Captures: donor new, donor ROUND, host new with all 32
layer outputs plus mixer and MLP outputs at L8..L11 (bitwise == M1 captures on the readout).
36 captures + 104 x 24 patches = 2532 calls in 19 x 128 + 100.
"""
import argparse, collections, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
BLOB_ROSTER = "1bc84bf56b9dd63a77b20b5cf8d105cdfe9af5e8"
BLOB_M1_DESIGN = "f3852efc21e7b55fdc1b7370a867454730422913"
BLOB_M1_RAW = "298c7cdfab634cd6a6a9122fac90d41c87219c21"
BLOB_G10_CF = "06ee06d7942b9f1a5f09c35777d5da1149655e4d"
RESID_LAYERS = (7, 8, 9, 10)
SUB_LAYERS = (8, 9, 10, 11)
COMPONENTS = ("mixer", "mlp")
SOURCES = ("new", "ROUND")
PLAN = [128] * 19 + [100]

PREREG = {
    "readouts": "M = conflict margin; A = logit(reject_conflict) - max(accept, wait); JOINT = M > 0 and A > 0; "
                "dM = M(patch) - M(in-run host capture)",
    "units": "the 104 cross-group cells; source groups are the unit; cells share donors and hosts, counts are "
             "descriptive decision rules, not independent tests",
    "S": "S(comp, L) = #cells where the main-source patch is JOINT and the ROUND-source patch (same comp, L) is not; "
         "resid at L11 is taken from the pinned M1 raw (main and round arms)",
    "SPEC": "SPEC(comp, L) iff dM_main > dM_round in >= 75% of cells AND in a majority of cells for >= 10 of 14 donor groups",
    "F_formation": "L_f = smallest L in 7..11 with S(resid, L) >= 1/2 * S(resid, 11) and SPEC(resid, L); "
                   "reported with the full profile",
    "W_writer": "at each L in 8..11, component X in {mixer, mlp} is a SUFFICIENT_WRITER iff S(X, L) >= 1/2 * S(resid, L) "
                "and SPEC(X, L)",
    "verdict": "at L_ref = max(L_f, 8): MIXER_WRITER if only mixer is a sufficient writer; MLP_WRITER if only mlp; "
               "BOTH_SUFFICIENT if both; NEITHER_ALONE if neither (consistent with an evaluation spread over both "
               "sublayers or an interaction); the per-layer writer table is always reported",
    "interpretation_fixed_in_advance": "MIXER_WRITER: the evaluation enters the span through token mixing (context "
        "-> span) at L_ref; the failing host's deficit is in what its mixer brings into the span. MLP_WRITER: the "
        "donor's span MLP output at L_ref carries the evaluation; the deficit is in the span's own nonlinear "
        "computation (or its inputs). Sufficiency of a sublayer patch does not show necessity; no ablation is run",
    "always_reported": "S and median dM per (comp, L, source); leave-one-donor-group-out of the verdict; per host; "
                       "all nulls",
}


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", required=True, type=Path)
    ap.add_argument("--m1-design", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--g10-counterfactuals", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.roster) == BLOB_ROSTER and file_blob(a.m1_design) == BLOB_M1_DESIGN
       and file_blob(a.m1_raw) == BLOB_M1_RAW and file_blob(a.g10_counterfactuals) == BLOB_G10_CF, "pins")
    roster = {r["scene_sha256"]: r for r in json.loads(a.roster.read_text("utf8"))["candidates"]}
    m1 = json.loads(a.m1_design.read_text("utf8"))
    cf = json.loads(a.g10_counterfactuals.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    donors, hosts = m1["selection"]["donors"], m1["selection"]["hosts"]
    ck(len(donors) == 14 and len(hosts) == 8, "selection")
    gd, gh = dict(donors), dict(hosts)
    m1_cap = {(x["target_scene"], x["target_arm"]): x["forward_index"] for x in m1raw if x["capture"]}

    def span(s, arm):
        return roster[s]["appended_span_in_state"]["new"] if arm == "new" else cf[s]["ROUND"]["span"]
    rows = []

    def add(**kw):
        n = len(rows)
        rows.append(dict(forward_index=n + 1, run=n // 128 + 1, **kw))

    for s, _g in donors:
        for arm in SOURCES:
            add(phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm, source_kind="donor",
                capture={"tag": f"{arm}:{s[:12]}", "span": span(s, arm), "layers": "all", "rows": "all", "save": True,
                         "sublayers": list(SUB_LAYERS)},
                bitwise_vs_m1=m1_cap[(s, arm)])
    for h, _g in hosts:
        add(phase="capture", condition="capture_new_all_rows", target_scene=h, target_arm="new", source_kind="host",
            capture={"tag": f"new:{h[:12]}", "span": span(h, "new"), "layers": "all", "rows": "all", "save": True,
                     "sublayers": list(SUB_LAYERS)},
            bitwise_vs_m1=m1_cap[(h, "new")])
    arms = [("resid", L) for L in RESID_LAYERS] + [(c, L) for L in SUB_LAYERS for c in COMPONENTS]
    for d, _ in donors:
        for h, _ in hosts:
            if gd[d] == gh[h]:
                continue
            for comp, L in arms:
                for src in SOURCES:
                    add(phase="patch", condition=f"patch_m2_{comp}_L{L}_{'main' if src == 'new' else 'round'}",
                        direction="repair", scope="all", source_kind="main" if src == "new" else "round",
                        donor=d, host=h, layer=L, component=comp, cross_group=True, target_scene=h, target_arm="new",
                        patch={"layer": L, "component": comp, "span": span(h, "new"), "source": f"{src}:{d[:12]}",
                               "transform": "none", "rows": "all", "delta_target": None, "seed": None})
    per_run = collections.Counter(r["run"] for r in rows)
    ck([per_run[k] for k in range(1, len(PLAN) + 1)] == PLAN and len(rows) == sum(PLAN), f"plan {dict(per_run)}")
    ck(sum(1 for r in rows if r["phase"] == "patch") == 104 * 24, "104 x 24 patches")
    design = {"schema": "JEV_A461_MECH_M2_SUBLAYER_LOCUS_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M2_FORWARD",
              "model": "kev-4B (runner module f118ea59: identity, source, loader)",
              "inputs": {"roster_blob": BLOB_ROSTER, "m1_design_blob": BLOB_M1_DESIGN, "m1_raw_blob": BLOB_M1_RAW,
                         "g10_counterfactuals_blob": BLOB_G10_CF},
              "selection": {"donors": donors, "hosts": hosts},
              "resid_layers": list(RESID_LAYERS), "sub_layers": list(SUB_LAYERS), "components": list(COMPONENTS),
              "sources": list(SOURCES), "plan": PLAN, "total": len(rows),
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M2 forwards; {len(rows)} calls / {len(PLAN)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m2_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m2_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for n in ("m2_design.json", "m2_manifest.jsonl"):
            f.write(sha_file(out / n) + "  " + n + "\n")
    print(json.dumps({"rows": len(rows), "batches": len(PLAN), "patches": 104 * 24,
                      "manifest_blob": file_blob(out / "m2_manifest.jsonl"), "design_blob": file_blob(out / "m2_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
