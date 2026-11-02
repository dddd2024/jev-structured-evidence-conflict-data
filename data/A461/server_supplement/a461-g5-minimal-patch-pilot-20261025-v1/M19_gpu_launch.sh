#!/bin/bash
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
I="--design M19_FREEZE_R1/m19_design.json --directions M19_FREEZE_R1/m19_directions.pt --m18-design M18_FREEZE_R1/m18_design.json --m18-raw M18_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m18.jsonl"
mkdir -p M19_GPU_RUNS
$P A461_mech_m19_runner_v1.py --repo-root $HOME/wjc/jev-checkout --admission admission_m19_gpu_R1.json --manifest M19_FREEZE_R1/m19_manifest.jsonl $I --out $PWD/M19_GPU_RUNS/ATTEMPT_R1 > M19_GPU_R1.log 2>&1
rc=$?
if grep -q "\"status\": \"COMPLETE_A461_MECH_M19\"" M19_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
  $P A461_mech_m19_analysis_v1.py --raw M19_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m19.jsonl --captures M19_GPU_RUNS/ATTEMPT_R1/captures --design M19_FREEZE_R1/m19_design.json --m18-raw M18_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m18.jsonl --head-pt $HOME/wjc/kev4b-assets-20261002/adapter/head.pt --out $PWD/M19_ANALYSIS_R1 > M19_ANALYSIS_R1.log 2>&1
  echo "run exit $rc analysis exit $? $(date -Is)" > M19_AFTER_RUN.done
else
  echo "run exit $rc not COMPLETE; analysis not run $(date -Is)" > M19_AFTER_RUN.done
fi
