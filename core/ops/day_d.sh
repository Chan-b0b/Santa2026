#!/bin/bash
# 밤사이 줄지어 도는 실행 B (프로세스 12개). lend run P (구조형 3차) 가 끝나면 시작한다.
# 순서: lend S (구조형 408개, k=3,8 새 초반부) -> lend T (구조형 408개, k=6,10)
cd /home/maverick/Santa2026 || exit 1
PY=".venv/bin/python -I"

splice() {  # splice <태그> <목록 json> <k 목록> <설명>
  local tag=$1 ids=$2 ks=$3 log=solvers/lend/run_$1.log
  $PY -c "
import json, sys
sys.path.insert(0,'core')
from verify import read_submission
B=read_submission('best/best.csv'); ids=json.load(open('solvers/lend/$ids'))
json.dump({p:len(json.loads(B[p])) for p in ids},open('solvers/lend/${tag}_bestlen.json','w'))"
  echo "== $(date '+%F %T') $4: 초반부(k=$ks) 바꿔 끼우기, 씨 1,2, 프로세스 12" > "$log"
  $PY -u solvers/lend/run_gen.py --ids "$ids" --phase prefix --ks "$ks" --secs 30 --procs 12 --tag "$tag" >> "$log" 2>&1
  echo "== $(date '+%F %T') prefix 끝, spl 시작" >> "$log"
  $PY -u solvers/lend/run_gen.py --ids "$ids" --phase spl --ks "$ks" --seeds 1,2 --secs 45 --procs 12 --tag "$tag" --bestlen "${tag}_bestlen.json" >> "$log" 2>&1
  echo "== 끝 $(date '+%F %T')" >> "$log"
}

splice X strN.json 2,14 "구조형 408개 6차"
splice Y strN.json 7,20 "구조형 408개 7차"
echo "day_d 끝 $(date '+%F %T')"
