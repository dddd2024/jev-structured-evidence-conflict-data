#!/bin/bash
# runs the M13 CPU self-test, then the frozen analysis as a dry run on its fake full-path output; writes M13_SELFTEST.done
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
$P A461_mech_m13_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M13_FREEZE_R1/m13_manifest.jsonl --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --g10-cf M1_INPUTS/counterfactuals.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --out $PWD/M13_SELFTEST_R1 > M13_SELFTEST_R1.log 2>&1
rc=$?
$P A461_mech_m13_analysis_v1.py --raw M13_SELFTEST_R1/T2_fullpath/raw_native_logits_m13.jsonl --design M13_FREEZE_R1/m13_design.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --m12-raw M12_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m12.jsonl --out $PWD/M13_SELFTEST_R1/_analysis_dryrun --fake-dry-run > M13_SELFTEST_R1/_analysis_dryrun.log 2>&1
echo "selftest exit $rc analysis dryrun exit $? $(date -Is)" > M13_SELFTEST.done
