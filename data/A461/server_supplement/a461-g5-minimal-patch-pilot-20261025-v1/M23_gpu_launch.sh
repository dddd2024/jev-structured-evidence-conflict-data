#!/bin/bash
# runs the frozen M23 manifests (kev-4B, then SecJev); after each COMPLETE run, the frozen M23 analysis (CPU only)
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
P=~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
for k in k s; do
  K=$(echo $k | tr ks KS); SA=$([ $k = k ] && echo raw_k4b_stage_a || echo raw_secjev_stage_a)
  PP=$([ $k = k ] && echo M18 || echo M22); pp=$(echo $PP | tr M m)
  mkdir -p M23${K}_GPU_RUNS
  $P A461_mon_m23${k}_runner_v1.py --repo-root $HOME/wjc/jev-checkout --admission admission_m23${k}_gpu_R1.json --manifest M23_FREEZE_R1/m23${k}_manifest.jsonl --design M23_FREEZE_R1/m23${k}_design.json --stage-a-raw M18_INPUTS/$SA.jsonl --out $PWD/M23${K}_GPU_RUNS/ATTEMPT_R1 > M23${K}_GPU_R1.log 2>&1
  rc=$?
  if grep -q "\"status\": \"COMPLETE_A461_MON_M23${K}\"" M23${K}_GPU_RUNS/ATTEMPT_R1/execution_receipt.json; then
    $P A461_mon_m23_analysis_v1.py --model $k --raw M23${K}_GPU_RUNS/ATTEMPT_R1/raw_native_logits_m23$k.jsonl --captures M23${K}_GPU_RUNS/ATTEMPT_R1/captures --parent-raw ${PP}_GPU_RUNS/ATTEMPT_R1/raw_native_logits_$pp.jsonl --parent-captures ${PP}_GPU_RUNS/ATTEMPT_R1/captures --parent-analysis ${PP}_ANALYSIS_R1/${pp}_analysis.json --design M23_FREEZE_R1/m23${k}_design.json --out $PWD/M23${K}_ANALYSIS_R1 > M23${K}_ANALYSIS_R1.log 2>&1
    echo "$k run exit $rc analysis exit $? $(date -Is)" >> M23_AFTER_RUN.done
  else
    echo "$k run exit $rc not COMPLETE; analysis not run $(date -Is)" >> M23_AFTER_RUN.done
  fi
done
echo ALLDONE >> M23_AFTER_RUN.done
