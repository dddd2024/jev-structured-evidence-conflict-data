#!/bin/bash
# runs the frozen M18 GPU manifest; if its receipt is COMPLETE, runs the frozen M18 analysis (CPU only); writes M18_AFTER_RUN.done
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
mkdir -p M18_GPU_RUNS
$P A461_mon_m18_runner_v1.py --repo-root $HOME/wjc/jev-checkout --admission admission_m18_gpu_R1.json --manifest M18_FREEZE_R1/m18_manifest.jsonl --design M18_FREEZE_R1/m18_design.json --stage-a-raw M18_INPUTS/raw_k4b_stage_a.jsonl --out $PWD/M18_GPU_RUNS/ATTEMPT_R1 > M18_GPU_R1.log 2>&1
rc=$?
if grep -q "\"status\": \"COMPLETE_A461_MON_M18\"" M18_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
  $P A461_mon_m18_analysis_v1.py --raw M18_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m18.jsonl --captures M18_GPU_RUNS/ATTEMPT_R1/captures --design M18_FREEZE_R1/m18_design.json --out $PWD/M18_ANALYSIS_R1 > M18_ANALYSIS_R1.log 2>&1
  echo "run exit $rc analysis exit $? $(date -Is)" > M18_AFTER_RUN.done
else
  echo "run exit $rc not COMPLETE; analysis not run $(date -Is)" > M18_AFTER_RUN.done
fi
