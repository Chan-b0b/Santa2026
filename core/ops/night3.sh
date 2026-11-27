#!/bin/bash
# 밤사이 줄지어 도는 실행 A (프로세스 10개). lns run16 이 끝나면 시작한다.
# 순서: lend Q (mixed+작은 indep, k=6,20) -> lns run17 (759개 3회차) -> lend R (큰 퍼즐, k=4,16) -> lns run18 (759개 3회차)
cd /home/maverick/Santa2026 || exit 1
PY=".venv/bin/python -I"

freeze() {  # freeze <목록 json> <기준 json>
  $PY -c "
import json, sys
sys.path.insert(0,'core')
from verify import read_submission
B=read_submission('best/best.csv'); ids=json.load(open('solvers/lend/$1'))
json.dump({p:len(json.loads(B[p])) for p in ids},open('solvers/lend/$2','w'))"
}
splice() {  # splice <태그> <목록 json> <k 목록> <설명>
  local tag=$1 ids=$2 ks=$3 log=solvers/lend/run_$1.log
  freeze "$ids" "${tag}_bestlen.json"
  echo "== $(date '+%F %T') $4: 초반부(k=$ks) 바꿔 끼우기, 씨 1,2, 프로세스 10" > "$log"
  $PY -u solvers/lend/run_gen.py --ids "$ids" --phase prefix --ks "$ks" --secs 30 --procs 10 --tag "$tag" >> "$log" 2>&1
  echo "== $(date '+%F %T') prefix 끝, spl 시작" >> "$log"
  $PY -u solvers/lend/run_gen.py --ids "$ids" --phase spl --ks "$ks" --seeds 1,2 --secs 45 --procs 10 --tag "$tag" --bestlen "${tag}_bestlen.json" >> "$log" 2>&1
  echo "== 끝 $(date '+%F %T')" >> "$log"
}
lns() {  # lns <번호> <씨>
  local log=solvers/lns/run$1_rest.log
  echo "== $(date '+%F %T') 48비트 미만 퍼즐 759개, best 출발 3회차(씨 $2~), 프로세스 10" > "$log"
  $PY -u solvers/lns/run_cpp.py --ids "$(cat solvers/lns/rest.txt)" --secs 20 --rounds 3 --procs 10 --seed "$2" >> "$log" 2>&1
  echo "== 끝 $(date '+%F %T')" >> "$log"
}

splice ZC strN.json 13,17 "구조형 408개 10차"
$PY -c "
import json, sys
sys.path.insert(0,'core')
from verify import read_submission
B=read_submission('best/best.csv'); ids=list(json.load(open('solvers/fresh/ids4.json')))
ids.sort(key=lambda p: len(json.loads(B[p])))
json.dump({p:len(json.loads(B[p])) for p in ids}, open('solvers/fresh/ids7.json','w'))"
echo "== $(date '+%F %T') 무작위형 247개 3회차, 퍼즐당 10회, 씨 9300, 프로세스 5 x 2" > solvers/fresh/s7.log
( for c in 0 1; do $PY -u solvers/fresh/drive.py $c 2 75 solvers/fresh/runs7.jsonl --ids solvers/fresh/ids7.json --scale --rseed 9300 --cfgs relate:0,relate:1,relate:2,relate:3,search:0,search:2,chain:0,chain:1,chain:2,search:1 > solvers/fresh/s7_$c.log 2>&1 & done; wait )
echo "== 끝 $(date '+%F %T')" >> solvers/fresh/s7.log
echo "night3 끝 $(date '+%F %T')"
