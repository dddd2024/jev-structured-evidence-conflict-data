#!/usr/bin/env python3
"""A461-MECH-M20 R1: CPU freeze of the natural-path necessity test (zero model forwards; reads the M16 design only).

M1-M5 show sufficiency in one direction: writing a recognizing donor's L11 attention output (or its BULK context-read
part) into a failing host's append span repairs the host. M20 runs the reverse in the donors' own, unpatched-otherwise
forwards: does replacing the recognizing donor's L11 write with a failing host's write remove the donor's recognition?
Interchange arms on the 14 donors' new arm (L11 o_proj input at the span, every question row), per cross-group cell
(donor d, host h) of M1-M16 (104 cells):
  full_host   the whole L11 span write of host h            vs  full_ctrl  that of another recognizing donor d'
  bulk_host   d's BULK part replaced by host h's            vs  bulk_ctrl  replaced by donor d''s
and per donor: bulk_round_self (d's BULK replaced by its own ROUND-source BULK) and bulk_hostmean (by the mean of
the cross-group hosts' BULK). d' is fixed per cell: the next donor in roster order whose group differs from d's and
h's. Uses the M17 runner code unchanged (patch targets may be host new; here the target is the donor's new capture).
44 captures (bitwise == M1) + 4 x 104 + 2 x 14 = 488 calls.
"""
import argparse, collections, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = (Path.home() / "wjc").resolve()
BLOB_M16_DESIGN = "c061686a5a3271e2b06f418f213bce81fa3ff05a"
BLOB_M1_RAW = "298c7cdfab634cd6a6a9122fac90d41c87219c21"
HEAD_LAYER = 11
SOURCES = ("new", "ROUND")
BULK = ["OTHER_ITEMS", "CONTEXT"]
PLAN_CAP = 128

PREREG = {
    "readouts": "M = conflict margin, A = action margin, JOINT = M > 0 and A > 0, on the donor's new arm; baselines = "
                "the donor's in-run new capture (bitwise == M1)",
    "sets": "all 14 donors are strict recognizers (M > 0); 10 of them are JOINT natively (M1 / K-C captures); C_loss is "
            "scored over all cells, J_loss over the cells of the JOINT donors",
    "measures": "C_loss(arm) = share of cells whose patched donor has M <= 0; J_loss(arm) = share of JOINT-donor cells "
                "whose patched donor is not JOINT; paired dM_host - dM_ctrl per cell; per-donor majorities",
    "verdict_full": "NEC_FULL iff C_loss(full_host) - C_loss(full_ctrl) >= 0.40 and dM(full_host) < dM(full_ctrl) in "
                    ">= 75% of cells and in a majority of cells for >= 10 of 14 donors; NOT_NEC_FULL iff the difference "
                    "< 0.10; else NEC_FULL_PARTIAL",
    "verdict_bulk": "NEC_BULK: the same rule on bulk_host vs bulk_ctrl",
    "reported": "bulk_round_self and bulk_hostmean C_loss / J_loss / median dM (14 rows each); per host; leave one "
                "donor group out of each verdict",
    "consistency_gate": "the 36 M1 capture readouts bitwise (runner); every donor's new capture readout equals M1's; "
                        "otherwise INCONSISTENT",
    "interpretation_fixed_in_advance": (
        "NEC_FULL / NEC_BULK: in the donors' own forward, the L11 append-span write (its context-read part) is "
        "necessary for recognition, not only sufficient for repair in hosts - with M1-M5 a two-directional (interchange) "
        "causal role at L11; a failing host's write carries a not-conflict reading of the same context. NOT_NEC: the "
        "donor recognises through other paths as well (redundancy); M1-M5 remain sufficiency only. Level S1-S3 boundary: "
        "an interchange intervention on natural recognition (the standard's par. 3.3 'local necessity'), not a natural "
        "error path in the failing hosts"),
}


def ck(v, m):
    if not v:
        raise RuntimeError(m)


def file_blob(p):
    return subprocess.run(["git", "hash-object", str(p)], capture_output=True, text=True, check=True).stdout.strip()


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m16-design", required=True, type=Path)
    ap.add_argument("--m1-raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    ck(file_blob(a.m16_design) == BLOB_M16_DESIGN and file_blob(a.m1_raw) == BLOB_M1_RAW, "pins")
    d16 = json.loads(a.m16_design.read_text("utf8"))
    m1raw = [json.loads(x) for x in a.m1_raw.read_text("utf8").splitlines() if x.strip()]
    donors, hosts = d16["selection"]["donors"], d16["selection"]["hosts"]
    gd, gh = dict(donors), dict(hosts)
    m1_cap = {(x["target_scene"], x["target_arm"]): x for x in m1raw if x["capture"]}
    kc = d16["key_classes"]
    rows = []

    def add(**kw):
        rows.append(kw)

    for kind, sel in (("donor", donors), ("host", hosts)):
        for s, _g in sel:
            for arm in SOURCES:
                tag = f"{arm}:{s[:12]}"
                add(phase="capture", condition=f"capture_{arm}_all_rows", target_scene=s, target_arm=arm,
                    source_kind=kind,
                    capture={"tag": tag, "span": kc[tag]["span"], "rows": "all", "save": True, "layer": HEAD_LAYER,
                             "classes": kc[tag]["classes"], "partner": kc[tag]["classes"]["PARTNER"][0]},
                    bitwise_vs_m1=m1_cap[(s, arm)]["forward_index"] if (s, arm) in m1_cap else None)
    ck(sum(1 for r in rows if r["bitwise_vs_m1"]) == 36, "36 M1 bitwise anchors")
    dl = [d for d, _ in donors]

    def ctrl_of(d, h):
        i = dl.index(d)
        for k in range(1, len(dl)):
            c = dl[(i + k) % len(dl)]
            if gd[c] not in (gd[d], gh[h]):
                return c
        raise RuntimeError("no control donor")

    def patch(arm, op, d, source, pool=None):
        p = {"layer": HEAD_LAYER, "arm": arm, "op": op, "classes": [] if op == "full" else BULK,
             "span": kc[f"new:{d[:12]}"]["span"], "source": source, "target": f"new:{d[:12]}", "rows": "all"}
        if op == "pool":
            p["base"] = "target"
            p["pool"] = pool
        return p

    cells = [(d, h) for d, _ in donors for h, _ in hosts if gd[d] != gh[h]]
    ck(len(cells) == 104, "104 cells")
    for d, h in cells:
        c = ctrl_of(d, h)
        for arm, op, src, pool in (("full_host", "full", f"new:{h[:12]}", None),
                                   ("full_ctrl", "full", f"new:{c[:12]}", None),
                                   ("bulk_host", "pool", f"new:{d[:12]}", [f"new:{h[:12]}"]),
                                   ("bulk_ctrl", "pool", f"new:{d[:12]}", [f"new:{c[:12]}"])):
            ck(kc[src]["span"][1] - kc[src]["span"][0] == 31, "span width")
            add(phase="patch", condition=f"patch_m20_{arm}", direction="necessity", scope="all", source_kind="main",
                donor=d, host=h, control_donor=c, layer=HEAD_LAYER, cross_group=True, target_scene=d,
                target_arm="new", patch=patch(arm, op, d, src, pool), bitwise_vs_m3=None, bitwise_vs_m6=None)
    for d, _ in donors:
        hm = [f"new:{h[:12]}" for h, _ in hosts if gh[h] != gd[d]]
        for arm, pool in (("bulk_round_self", [f"ROUND:{d[:12]}"]), ("bulk_hostmean", hm)):
            add(phase="patch", condition=f"patch_m20_{arm}", direction="necessity", scope="all", source_kind="main",
                donor=d, host=None, control_donor=None, layer=HEAD_LAYER, cross_group=None, target_scene=d,
                target_arm="new", patch=patch(arm, "pool", d, f"new:{d[:12]}", pool), bitwise_vs_m3=None,
                bitwise_vs_m6=None)
    n = len(rows)
    plan = [PLAN_CAP] * (n // PLAN_CAP) + ([n % PLAN_CAP] if n % PLAN_CAP else [])
    for i, r in enumerate(rows):
        r.update(forward_index=i + 1, run=i // PLAN_CAP + 1)
    ck(n == 488 and collections.Counter(r["condition"] for r in rows if r["phase"] == "patch")
       == {"patch_m20_full_host": 104, "patch_m20_full_ctrl": 104, "patch_m20_bulk_host": 104,
           "patch_m20_bulk_ctrl": 104, "patch_m20_bulk_round_self": 14, "patch_m20_bulk_hostmean": 14}, "rows")
    native = {}
    for d, _ in donors:
        q = {x["id"]: dict(zip(x["keys"], x["logits"])) for x in m1_cap[(d, "new")]["questions"]}
        M = q["conflicting_vote"]["true"] - q["conflicting_vote"]["false"]
        A = q["certificate_action"]["reject_conflict"] - max(q["certificate_action"]["accept"], q["certificate_action"]["wait"])
        native[d[:12]] = {"M": M, "A": A, "JOINT": M > 0 and A > 0}
    ck(all(v["M"] > 0 for v in native.values()) and sum(v["JOINT"] for v in native.values()) == 10, "donor baselines")
    design = {"schema": "JEV_A461_MECH_M20_NATURAL_NECESSITY_DESIGN_V1", "status": "FROZEN_CPU_BEFORE_ANY_M20_FORWARD",
              "inputs": {"m16_design_blob": BLOB_M16_DESIGN, "m1_raw_blob": BLOB_M1_RAW},
              "selection": d16["selection"], "donor_native": native, "plan": plan, "total": n,
              "preregistered_analysis": PREREG,
              "gpu_status": f"0 M20 forwards; {n} calls / {len(plan)} batches under the standing GPU authorization"}
    out = a.out.expanduser().resolve(strict=False)
    out.relative_to(ROOT)
    out.mkdir(mode=0o700)
    with (out / "m20_design.json").open("x", encoding="utf8", newline="\n") as f:
        json.dump(design, f, sort_keys=True, indent=2, ensure_ascii=False)
        f.write("\n")
    with (out / "m20_manifest.jsonl").open("x", encoding="utf8", newline="\n") as f:
        for r in rows:
            f.write(canon(r) + "\n")
    with (out / "SHA256SUMS").open("x", encoding="utf8", newline="\n") as f:
        for nm in ("m20_design.json", "m20_manifest.jsonl"):
            f.write(sha_file(out / nm) + "  " + nm + "\n")
    print(json.dumps({"rows": n, "plan": plan, "manifest_blob": file_blob(out / "m20_manifest.jsonl"),
                      "design_blob": file_blob(out / "m20_design.json")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
