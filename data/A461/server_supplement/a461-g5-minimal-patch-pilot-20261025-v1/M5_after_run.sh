#!/bin/bash
# waits for the M5 GPU run (pid 380814) to exit; if its receipt is COMPLETE, runs the frozen M5 analysis (CPU only)
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
while kill -0 380814 2>/dev/null; do sleep 60; done
if grep -q "\"status\": \"COMPLETE_A461_MECH_M5\"" M5_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
  $P A461_mech_m5_analysis_v1.py --raw M5_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m5.jsonl --captures M5_GPU_RUNS/ATTEMPT_R1/captures --design M5_FREEZE_R1/m5_design.json --m3-raw M3_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m3.jsonl --out $PWD/M5_ANALYSIS_R1 > M5_ANALYSIS_R1.log 2>&1
  echo "analysis exit $? $(date -Is)" > M5_AFTER_RUN.done
else
  echo "run not COMPLETE; analysis not run $(date -Is)" > M5_AFTER_RUN.done
fi
