#!/bin/bash
# runs the M17 CPU self-test, then the frozen analysis as a dry run on its fake full-path output; writes M17_SELFTEST.done
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
R="--m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl"
$P A461_mech_m17_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M17_FREEZE_R1/m17_manifest.jsonl --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --g10-cf M1_INPUTS/counterfactuals.json $R --out $PWD/M17_SELFTEST_R1 > M17_SELFTEST_R1.log 2>&1
rc=$?
$P A461_mech_m17_analysis_v1.py --raw M17_SELFTEST_R1/T2_fullpath/raw_native_logits_m17.jsonl --design M17_FREEZE_R1/m17_design.json $R --m8-raw M8_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m8.jsonl --m14-raw M14_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m14.jsonl --out $PWD/M17_SELFTEST_R1/_analysis_dryrun --fake-dry-run > M17_SELFTEST_R1/_analysis_dryrun.log 2>&1
echo "selftest exit $rc analysis dryrun exit $? $(date -Is)" > M17_SELFTEST.done
