#!/bin/bash
# runs the M9 CPU self-test, then the frozen analysis as a dry run on its fake full-path output; writes M9_SELFTEST.done
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
$P A461_mech_m9_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M9_FREEZE_R1/m9_manifest.jsonl --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --g10-cf M1_INPUTS/counterfactuals.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --out $PWD/M9_SELFTEST_R1 > M9_SELFTEST_R1.log 2>&1
rc=$?
$P A461_mech_m9_analysis_v1.py --raw M9_SELFTEST_R1/T2_fullpath/raw_native_logits_m9.jsonl --design M9_FREEZE_R1/m9_design.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --m7-raw M7_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m7.jsonl --m8-raw M8_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m8.jsonl --out $PWD/M9_SELFTEST_R1/_analysis_dryrun --fake-dry-run > M9_SELFTEST_R1/_analysis_dryrun.log 2>&1
echo "selftest exit $rc analysis dryrun exit $? $(date -Is)" > M9_SELFTEST.done
