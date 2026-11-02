#!/bin/bash
# runs the frozen M17 GPU manifest in the foreground; if its receipt is COMPLETE, runs the frozen M17 analysis (CPU only);
# writes M17_AFTER_RUN.done in every case
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
R="--m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl"
mkdir -p M17_GPU_RUNS
$P A461_mech_m17_runner_v1.py --repo-root $HOME/wjc/jev-checkout --admission admission_m17_gpu_R1.json --manifest M17_FREEZE_R1/m17_manifest.jsonl --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --g10-cf M1_INPUTS/counterfactuals.json $R --out $PWD/M17_GPU_RUNS/ATTEMPT_R1 > M17_GPU_R1.log 2>&1
rc=$?
if grep -q "\"status\": \"COMPLETE_A461_MECH_M17\"" M17_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
  $P A461_mech_m17_analysis_v1.py --raw M17_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m17.jsonl --design M17_FREEZE_R1/m17_design.json $R --m8-raw M8_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m8.jsonl --m14-raw M14_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m14.jsonl --out $PWD/M17_ANALYSIS_R1 > M17_ANALYSIS_R1.log 2>&1
  echo "run exit $rc analysis exit $? $(date -Is)" > M17_AFTER_RUN.done
else
  echo "run exit $rc not COMPLETE; analysis not run $(date -Is)" > M17_AFTER_RUN.done
fi
