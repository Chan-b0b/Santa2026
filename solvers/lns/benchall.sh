#!/bin/bash
# 사용: benchall.sh <bin> <태그> "<씨들>" [opts...]
bin=$1; tag=$2; seeds=$3; shift 3
for s in $seeds; do /home/maverick/Santa2026/solvers/lns/bench.sh $bin $tag $s "$@"; done
