#!/usr/bin/env python3
"""Re-run every frozen A461 mechanism / monitor analysis (M1-M22) on the archived GPU outputs and compare each result
with the archived analysis JSON committed in the repository (parsed JSON, exact equality).

CPU only. The analysis scripts and the expected JSONs are read from the repository (--rounds = research/rounds);
raw logits, captures, freeze inputs and the kev-4B head come from the GPU work directory (--work), where the captures
live. Writes <out>/RECOMPUTE_MECH.json and exits 0 only if every stage is EQUAL."""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

R = lambda m: f"{m}_GPU_RUNS/ATTEMPT_R1/raw_native_logits_{m.lower()}.jsonl"
C = lambda m: f"{m}_GPU_RUNS/ATTEMPT_R1/captures"
D = lambda m: f"{m}_FREEZE_R1/{m.lower()}_design.json"
HEAD = "{home}/wjc/kev4b-assets-20261002/adapter/head.pt"

# stage: (round dir, analysis script, expected JSON relative to the round dir, extra args after --raw/--design)
STAGES = {
    "M1": ("A461_MECH_M1_ROUND_BINDING_GPU", "A461_mech_m1_analysis_v1.py", "M1_ANALYSIS_R1/m1_analysis.json", []),
    "M2": ("A461_MECH_M2_SUBLAYER_LOCUS_GPU", "A461_mech_m2_analysis_v1.py", "M2_ANALYSIS_R1/m2_analysis.json",
           ["--m1-raw", R("M1")]),
    "M3": ("A461_MECH_M3_HEAD_ROUTING_GPU", "A461_mech_m3_analysis_v1.py", "M3_ANALYSIS_R1/m3_analysis.json",
           ["--captures", C("M3"), "--m2-raw", R("M2")]),
    "M4": ("A461_MECH_M4_KEYCLASS_VALUE_GPU", "A461_mech_m4_analysis_v1.py", "M4_ANALYSIS_R1/m4_analysis.json",
           ["--m3-raw", R("M3")]),
    "M5": ("A461_MECH_M5_MAGNITUDE_DIRECTION_GPU", "A461_mech_m5_analysis_v1.py", "M5_ANALYSIS_R1/m5_analysis.json",
           ["--captures", C("M5"), "--m3-raw", R("M3")]),
    "M6": ("A461_MECH_M6_SHARED_BULK_DIRECTION_GPU", "A461_mech_m6_analysis_v1.py", "M6_ANALYSIS_R1/m6_analysis.json",
           ["--m3-raw", R("M3"), "--m5-raw", R("M5")]),
    "M7": ("A461_MECH_M7_DELTA_BASIS_MEANDIFF_GPU", "A461_mech_m7_analysis_v1.py", "M7_ANALYSIS_R1/m7_analysis.json",
           ["--m3-raw", R("M3"), "--m6-raw", R("M6")]),
    "M8": ("A461_MECH_M8_CROSS_DELTA_TWOPART_GPU", "A461_mech_m8_analysis_v1.py", "M8_ANALYSIS_R1/m8_analysis.json",
           ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m7-raw", R("M7")]),
    "M9": ("A461_MECH_M9_GAIN_HEADS_SPLIT_GPU", "A461_mech_m9_analysis_v1.py", "M9_ANALYSIS_R1/m9_analysis.json",
           ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m7-raw", R("M7"), "--m8-raw", R("M8")]),
    "M10": ("A461_MECH_M10_HEADS_POSITIONS_GPU", "A461_mech_m10_analysis_v1.py", "M10_ANALYSIS_R1/m10_analysis.json",
            ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m9-raw", R("M9")]),
    "M11": ("A461_MECH_M11_MATCHED_POSITION_SHIFT_GPU", "A461_mech_m11_analysis_v1.py", "M11_ANALYSIS_R1/m11_analysis.json",
            ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m10-raw", R("M10")]),
    "M12": ("A461_MECH_M12_P30_FIELDS_COSNULL_GPU", "A461_mech_m12_analysis_v1.py", "M12_ANALYSIS_R1/m12_analysis.json",
            ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m11-raw", R("M11")]),
    "M13": ("A461_MECH_M13_AB_SHIFT_TILT_GPU", "A461_mech_m13_analysis_v1.py", "M13_ANALYSIS_R1/m13_analysis.json",
            ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m12-raw", R("M12")]),
    "M14": ("A461_MECH_M14_AB_THRESHOLD_TILT3_GPU", "A461_mech_m14_analysis_v1.py", "M14_ANALYSIS_R1/m14_analysis.json",
            ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m13-raw", R("M13")]),
    "M15": ("A461_MECH_M15_Q1_SPLIT_NULL24_GPU", "A461_mech_m15_analysis_v1.py", "M15_ANALYSIS_R1/m15_analysis.json",
            ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m13-raw", R("M13"), "--m14-raw", R("M14")]),
    "M16": ("A461_MECH_M16_MID_WEIGHT_LINEAR_GPU", "A461_mech_m16_analysis_v1.py", "M16_ANALYSIS_R1/m16_analysis.json",
            ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m14-raw", R("M14"), "--m15-raw", R("M15")]),
    # M17: v1.1 is the analysis of record (documented deviation: anchor_of read from the frozen manifest)
    "M17": ("A461_MECH_M17_FALSE_VETO_BENIGN_GPU", "A461_mech_m17_analysis_v1_1.py",
            "M17_ANALYSIS_R1_V1_1/m17_analysis.json",
            ["--m3-raw", R("M3"), "--m6-raw", R("M6"), "--m8-raw", R("M8"), "--m14-raw", R("M14"),
             "--manifest", "M17_FREEZE_R1/m17_manifest.jsonl"]),
    "M18": ("A461_MON_M18_SPAN_MONITOR_GPU", "A461_mon_m18_analysis_v1.py", "M18_ANALYSIS_R1/m18_analysis.json",
            ["--captures", C("M18")]),
    "M19": ("A461_MECH_M19_READOUT_GAIN_GPU", "A461_mech_m19_analysis_v1.py", "M19_ANALYSIS_R1/m19_analysis.json",
            ["--captures", C("M19"), "--m18-raw", R("M18"), "--head-pt", HEAD]),
    "M20": ("A461_MECH_M20_NATURAL_NECESSITY_GPU", "A461_mech_m20_analysis_v1.py", "M20_ANALYSIS_R1/m20_analysis.json",
            ["--m1-raw", R("M1")]),
    "M21": ("A461_MECH_M21_READOUT_MEANDIFF_GPU", "A461_mech_m21_analysis_v1.py", "M21_ANALYSIS_R1/m21_analysis.json",
            ["--captures", C("M21"), "--m18-raw", R("M18"), "--head-pt", HEAD]),
    "M22": ("A461_MON_M22_SECJEV_REPLICATION_GPU", "A461_mon_m22_analysis_v1.py", "M22_ANALYSIS_R1/m22_analysis.json",
            ["--captures", C("M22")]),
}


def diff(a, b, path="$", out=None, limit=20):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}.{k}: {'missing in recompute' if k not in a else 'missing in archive'}")
            else:
                diff(a[k], b[k], f"{path}.{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f"{path}[{i}]", out, limit)
    elif a != b:
        out.append(f"{path}: recompute {str(a)[:80]} != archive {str(b)[:80]}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", required=True, type=Path, help="repository research/rounds")
    ap.add_argument("--work", required=True, type=Path, help="GPU work directory with *_GPU_RUNS and *_FREEZE_R1")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    out = a.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=False)
    home = str(Path.home())
    report = {"schema": "JEV_A461_RECOMPUTE_MECH_V1", "python": sys.version.split()[0], "stages": {}}
    for m, (rd, script, expected, extra) in STAGES.items():
        if a.only and m not in a.only:
            continue
        st = out / m
        cmd = [sys.executable, str(a.rounds / rd / script), "--raw", R(m), "--design", D(m)]
        cmd += [x.format(home=home) for x in extra] + ["--out", str(st)]
        t0 = time.time()
        p = subprocess.run(cmd, cwd=a.work, capture_output=True, text=True)
        (out / f"{m}.log").write_text(p.stdout + p.stderr, encoding="utf8")
        rec = {"script": f"{rd}/{script}", "expected": f"{rd}/{expected}", "exit": p.returncode,
               "seconds": round(time.time() - t0, 1)}
        got = st / Path(expected).name
        if p.returncode == 0 and got.exists():
            d = diff(json.loads(got.read_text("utf8")), json.loads((a.rounds / rd / expected).read_text("utf8")))
            rec["status"] = "EQUAL" if not d else "DIFF"
            rec["diffs"] = d
        else:
            rec["status"] = "FAILED"
        report["stages"][m] = rec
        print(m, rec["status"], rec["seconds"], "s", flush=True)
    report["all_equal"] = all(r["status"] == "EQUAL" for r in report["stages"].values())
    (out / "RECOMPUTE_MECH.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf8")
    print("ALL_EQUAL" if report["all_equal"] else "NOT_ALL_EQUAL")
    return 0 if report["all_equal"] else 1


if __name__ == "__main__":
    sys.exit(main())
