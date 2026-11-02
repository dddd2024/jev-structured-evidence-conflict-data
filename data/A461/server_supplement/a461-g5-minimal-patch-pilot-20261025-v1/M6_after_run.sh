#!/bin/bash
# waits for the M6 GPU run (pid in M6_GPU_R1.pid) to exit; if its receipt is COMPLETE, runs the frozen M6 analysis (CPU only)
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
PID=$(cat M6_GPU_R1.pid)
while kill -0 "$PID" 2>/dev/null; do sleep 60; done
if grep -q "\"status\": \"COMPLETE_A461_MECH_M6\"" M6_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
  $P A461_mech_m6_analysis_v1.py --raw M6_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m6.jsonl --design M6_FREEZE_R1/m6_design.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --m5-raw M5_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m5.jsonl --out $PWD/M6_ANALYSIS_R1 > M6_ANALYSIS_R1.log 2>&1
  echo "analysis exit $? $(date -Is)" > M6_AFTER_RUN.done
else
  echo "run not COMPLETE; analysis not run $(date -Is)" > M6_AFTER_RUN.done
fi
