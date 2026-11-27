#!/bin/bash
# 사용: bench.sh <bin> <태그> <씨> [opts...]   구조형 25 + 무작위형 19 퍼즐 x 30초, 프로세스 5개
cd /home/maverick/Santa2026
bin=$1; tag=$2; seed=$3; shift 3
base="peq=0.5 pelim=0.05 pruin=0.8 ruink=12 aware=0.5 repair=2000 beamw=32"
for set in ${SETS:-struct random}; do
  PROCS=5 .venv/bin/python -I solvers/lns/one.py $bin 30 $(cat solvers/lns/bench_$set.txt) seed=$seed $base "$@" > solvers/lns/bench_${tag}_${set}_$seed.log 2>&1
done
