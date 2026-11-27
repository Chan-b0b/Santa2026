#!/bin/bash
# k=4 를 가족별로 묶음(30개)으로 차례로 돌린다. 사용: run_k4_batches.sh <fam> <tag>
cd /home/maverick/Santa2026
fam=$1; tag=$2
for skip in $(seq 0 30 720); do
  .venv/bin/python -I -u solvers/exact/exact_run.py --fam $fam --K 4 --minc 5 --skip $skip --first 30 --tag $tag --procs 6 --tmax 900 >> solvers/exact/run_$tag.log 2>&1
done
echo ALLDONE >> solvers/exact/run_$tag.log
