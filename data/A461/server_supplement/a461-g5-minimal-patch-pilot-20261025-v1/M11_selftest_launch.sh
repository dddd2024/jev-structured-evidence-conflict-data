#!/bin/bash
# runs the M11 CPU self-test, then the frozen analysis as a dry run on its fake full-path output; writes M11_SELFTEST.done
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
$P A461_mech_m11_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M11_FREEZE_R1/m11_manifest.jsonl --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --g10-cf M1_INPUTS/counterfactuals.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --out $PWD/M11_SELFTEST_R1 > M11_SELFTEST_R1.log 2>&1
rc=$?
$P A461_mech_m11_analysis_v1.py --raw M11_SELFTEST_R1/T2_fullpath/raw_native_logits_m11.jsonl --design M11_FREEZE_R1/m11_design.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --m10-raw M10_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m10.jsonl --out $PWD/M11_SELFTEST_R1/_analysis_dryrun --fake-dry-run > M11_SELFTEST_R1/_analysis_dryrun.log 2>&1
echo "selftest exit $rc analysis dryrun exit $? $(date -Is)" > M11_SELFTEST.done
