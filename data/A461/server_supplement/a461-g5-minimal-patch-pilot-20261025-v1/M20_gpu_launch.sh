#!/bin/bash
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
R="--m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl"
mkdir -p M20_GPU_RUNS
$P A461_mech_m20_runner_v1.py --repo-root $HOME/wjc/jev-checkout --admission admission_m20_gpu_R1.json --manifest M20_FREEZE_R1/m20_manifest.jsonl --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --g10-cf M1_INPUTS/counterfactuals.json $R --out $PWD/M20_GPU_RUNS/ATTEMPT_R1 > M20_GPU_R1.log 2>&1
rc=$?
if grep -q "\"status\": \"COMPLETE_A461_MECH_M20\"" M20_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
  $P A461_mech_m20_analysis_v1.py --raw M20_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m20.jsonl --design M20_FREEZE_R1/m20_design.json --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --out $PWD/M20_ANALYSIS_R1 > M20_ANALYSIS_R1.log 2>&1
  echo "run exit $rc analysis exit $? $(date -Is)" > M20_AFTER_RUN.done
else
  echo "run exit $rc not COMPLETE; analysis not run $(date -Is)" > M20_AFTER_RUN.done
fi
