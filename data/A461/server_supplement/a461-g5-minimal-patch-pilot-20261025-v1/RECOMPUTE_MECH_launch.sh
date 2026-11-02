#!/bin/bash
cd ~/wjc/a461-g5-minimal-patch-pilot-20261025-v1
export OMP_NUM_THREADS=24 MKL_NUM_THREADS=24
~/wjc/kev08b-smoke-20261001-153041/venv/bin/python3 ~/wjc/recompute_mech_rounds/A461_G5_G2_CAUSAL_SPECIFICITY_AND_SOURCE_REPLICATION/PAPER_CLAIM_PACKAGE_V4/recompute_mech_v1.py --rounds ~/wjc/recompute_mech_rounds --work $PWD --out $PWD/RECOMPUTE_MECH_R1 > RECOMPUTE_MECH_R1.log 2>&1
echo "exit $? $(date -Is)" > RECOMPUTE_MECH.done
