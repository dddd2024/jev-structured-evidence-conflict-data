#!/bin/bash
# runs the frozen M7 GPU manifest in the foreground; if its receipt is COMPLETE, runs the frozen M7 analysis (CPU only);
# writes M7_AFTER_RUN.done in every case (no pid file: the M6 watcher lost its pid twice)
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
mkdir -p M7_GPU_RUNS
$P A461_mech_m7_runner_v1.py --repo-root $HOME/wjc/jev-checkout --admission admission_m7_gpu_R1.json --manifest M7_FREEZE_R1/m7_manifest.jsonl --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --g10-cf M1_INPUTS/counterfactuals.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --out $PWD/M7_GPU_RUNS/ATTEMPT_R1 > M7_GPU_R1.log 2>&1
rc=$?
if grep -q "\"status\": \"COMPLETE_A461_MECH_M7\"" M7_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
  $P A461_mech_m7_analysis_v1.py --raw M7_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m7.jsonl --design M7_FREEZE_R1/m7_design.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --out $PWD/M7_ANALYSIS_R1 > M7_ANALYSIS_R1.log 2>&1
  echo "run exit $rc analysis exit $? $(date -Is)" > M7_AFTER_RUN.done
else
  echo "run exit $rc not COMPLETE; analysis not run $(date -Is)" > M7_AFTER_RUN.done
fi
