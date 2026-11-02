#!/bin/bash
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
$P A461_mon_m22_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M22_FREEZE_R1/m22_manifest.jsonl --design M22_FREEZE_R1/m22_design.json --stage-a-raw M18_INPUTS/raw_secjev_stage_a.jsonl --out $PWD/M22_SELFTEST_R1 > M22_SELFTEST_R1.log 2>&1
rc=$?
$P A461_mon_m22_analysis_v1.py --raw M22_SELFTEST_R1/T2_fullpath/raw_native_logits_m22.jsonl --captures M22_SELFTEST_R1/T2_fullpath/captures --design M22_FREEZE_R1/m22_design.json --out $PWD/M22_SELFTEST_R1/_analysis_dryrun --boot 200 --fake-dry-run > M22_SELFTEST_R1/_analysis_dryrun.log 2>&1
echo "selftest exit $rc analysis dryrun exit $? $(date -Is)" > M22_SELFTEST.done
