#!/bin/bash
# runs the frozen M14 GPU manifest in the foreground; if its receipt is COMPLETE, runs the frozen M14 analysis (CPU only);
# writes M14_AFTER_RUN.done in every case (no pid file: the M6 watcher lost its pid twice)
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
mkdir -p M14_GPU_RUNS
$P A461_mech_m14_runner_v1.py --repo-root $HOME/wjc/jev-checkout --admission admission_m14_gpu_R1.json --manifest M14_FREEZE_R1/m14_manifest.jsonl --m1-raw M1_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m1.jsonl --g10-cf M1_INPUTS/counterfactuals.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --out $PWD/M14_GPU_RUNS/ATTEMPT_R1 > M14_GPU_R1.log 2>&1
rc=$?
if grep -q "\"status\": \"COMPLETE_A461_MECH_M14\"" M14_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
  $P A461_mech_m14_analysis_v1.py --raw M14_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m14.jsonl --design M14_FREEZE_R1/m14_design.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m6-raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --m13-raw M13_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m13.jsonl --out $PWD/M14_ANALYSIS_R1 > M14_ANALYSIS_R1.log 2>&1
  echo "run exit $rc analysis exit $? $(date -Is)" > M14_AFTER_RUN.done
else
  echo "run exit $rc not COMPLETE; analysis not run $(date -Is)" > M14_AFTER_RUN.done
fi
