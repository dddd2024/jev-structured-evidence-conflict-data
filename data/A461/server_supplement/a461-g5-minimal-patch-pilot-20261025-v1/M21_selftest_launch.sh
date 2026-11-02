#!/bin/bash
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
I="--design M21_FREEZE_R1/m21_design.json --directions M21_FREEZE_R1/m21_directions.pt --m18-design M18_FREEZE_R1/m18_design.json --m18-raw M18_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m18.jsonl"
$P A461_mech_m21_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M21_FREEZE_R1/m21_manifest.jsonl $I --out $PWD/M21_SELFTEST_R1 > M21_SELFTEST_R1.log 2>&1
rc=$?
$P A461_mech_m21_analysis_v1.py --raw M21_SELFTEST_R1/T2_fullpath/raw_native_logits_m21.jsonl --captures M21_SELFTEST_R1/T2_fullpath/captures --design M21_FREEZE_R1/m21_design.json --m18-raw M18_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m18.jsonl --head-pt $HOME/wjc/kev4b-assets-20261002/adapter/head.pt --out $PWD/M21_SELFTEST_R1/_analysis_dryrun --boot 200 --fake-dry-run > M21_SELFTEST_R1/_analysis_dryrun.log 2>&1
echo "selftest exit $rc analysis dryrun exit $? $(date -Is)" > M21_SELFTEST.done
