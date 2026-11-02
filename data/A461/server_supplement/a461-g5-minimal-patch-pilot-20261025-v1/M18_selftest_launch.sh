#!/bin/bash
# runs the M18 CPU self-test, then the frozen analysis as a dry run on its fake full-path output; writes M18_SELFTEST.done
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
$P A461_mon_m18_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M18_FREEZE_R1/m18_manifest.jsonl --design M18_FREEZE_R1/m18_design.json --stage-a-raw M18_INPUTS/raw_k4b_stage_a.jsonl --out $PWD/M18_SELFTEST_R1 > M18_SELFTEST_R1.log 2>&1
rc=$?
$P A461_mon_m18_analysis_v1.py --raw M18_SELFTEST_R1/T2_fullpath/raw_native_logits_m18.jsonl --captures M18_SELFTEST_R1/T2_fullpath/captures --design M18_FREEZE_R1/m18_design.json --out $PWD/M18_SELFTEST_R1/_analysis_dryrun --boot 200 --fake-dry-run > M18_SELFTEST_R1/_analysis_dryrun.log 2>&1
echo "selftest exit $rc analysis dryrun exit $? $(date -Is)" > M18_SELFTEST.done
