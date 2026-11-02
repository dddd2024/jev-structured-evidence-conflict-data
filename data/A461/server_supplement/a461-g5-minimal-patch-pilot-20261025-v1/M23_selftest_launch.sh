#!/bin/bash
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
$P A461_mon_m23k_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M23_FREEZE_R1/m23k_manifest.jsonl --design M23_FREEZE_R1/m23k_design.json --stage-a-raw M18_INPUTS/raw_k4b_stage_a.jsonl --out $PWD/M23K_SELFTEST_R1 > M23K_SELFTEST_R1.log 2>&1
rk=$?
$P A461_mon_m23s_selftest_v1.py --repo-root ~/wjc/jev-checkout --manifest M23_FREEZE_R1/m23s_manifest.jsonl --design M23_FREEZE_R1/m23s_design.json --stage-a-raw M18_INPUTS/raw_secjev_stage_a.jsonl --out $PWD/M23S_SELFTEST_R1 > M23S_SELFTEST_R1.log 2>&1
echo "k exit $rk s exit $? $(date -Is)" > M23_SELFTEST.done
