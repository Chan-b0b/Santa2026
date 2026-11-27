#!/bin/bash
# decode8 근접 실패(best +3 이내) 퍼즐을 lns 30초로 다시 구성·다듬기 (두 묶음, 묶음당 15분 이하)
cd /home/maverick/Santa2026
i=0
while read -r ids; do
  i=$((i+1)); echo "=== chunk $i $(date +%H:%M:%S)"
  timeout 870 .venv/bin/python -I -u solvers/quirk/run2.py --nofinal --bases solvers/quirk/bases8_run.json --procs 8 --lns 30 --ids "$ids"
done < solvers/quirk/run11_chunks.txt
echo "=== all done $(date +%H:%M:%S)"
