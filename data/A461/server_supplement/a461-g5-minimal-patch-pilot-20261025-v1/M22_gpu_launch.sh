#!/bin/bash
# runs the frozen M22 GPU manifest; if its receipt is COMPLETE, runs the frozen M22 analysis (CPU only); writes M22_AFTER_RUN.done
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
mkdir -p M22_GPU_RUNS
$P A461_mon_m22_runner_v1.py --repo-root $HOME/wjc/jev-checkout --admission admission_m22_gpu_R1.json --manifest M22_FREEZE_R1/m22_manifest.jsonl --design M22_FREEZE_R1/m22_design.json --stage-a-raw M18_INPUTS/raw_secjev_stage_a.jsonl --out $PWD/M22_GPU_RUNS/ATTEMPT_R1 > M22_GPU_R1.log 2>&1
rc=$?
if grep -q "\"status\": \"COMPLETE_A461_MON_M22\"" M22_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
  $P A461_mon_m22_analysis_v1.py --raw M22_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m22.jsonl --captures M22_GPU_RUNS/ATTEMPT_R1/captures --design M22_FREEZE_R1/m22_design.json --out $PWD/M22_ANALYSIS_R1 > M22_ANALYSIS_R1.log 2>&1
  echo "run exit $rc analysis exit $? $(date -Is)" > M22_AFTER_RUN.done
else
  echo "run exit $rc not COMPLETE; analysis not run $(date -Is)" > M22_AFTER_RUN.done
fi
