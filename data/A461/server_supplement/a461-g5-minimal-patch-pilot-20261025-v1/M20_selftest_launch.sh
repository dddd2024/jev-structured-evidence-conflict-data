#!/bin/bash
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
R="--m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl"
$P A461_mech_m20_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M20_FREEZE_R1/m20_manifest.jsonl --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --g10-cf M1_INPUTS/counterfactuals.json $R --out $PWD/M20_SELFTEST_R1 > M20_SELFTEST_R1.log 2>&1
rc=$?
$P A461_mech_m20_analysis_v1.py --raw M20_SELFTEST_R1/T2_fullpath/raw_native_logits_m20.jsonl --design M20_FREEZE_R1/m20_design.json --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --out $PWD/M20_SELFTEST_R1/_analysis_dryrun --fake-dry-run > M20_SELFTEST_R1/_analysis_dryrun.log 2>&1
echo "selftest exit $rc analysis dryrun exit $? $(date -Is)" > M20_SELFTEST.done
