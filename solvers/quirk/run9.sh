#!/bin/bash
# decode8 정수로 run2 를 56개씩 묶어 돌린다 (묶음당 15분 이하)
cd /home/maverick/Santa2026
i=0
while read -r ids; do
  i=$((i+1))
  echo "=== chunk $i $(date +%H:%M:%S)"
  timeout 870 .venv/bin/python -I -u solvers/quirk/run2.py --nofinal --bases solvers/quirk/bases8_run.json --procs 7 --ids "$ids"
done < solvers/quirk/run9_chunks.txt
echo "=== all done $(date +%H:%M:%S)"
