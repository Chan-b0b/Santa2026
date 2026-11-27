#!/bin/bash
# 해독 v3 을 돌리고, 밑수가 v1 과 달라진 퍼즐만 다시 푼다
cd /home/maverick/Santa2026
.tools/bin/pypy3 -I -u solvers/factor/decode2.py scored 5 > solvers/factor/run_dec3_scored.log 2>&1
IDS=$(.venv/bin/python -I -c "
import json
v1=json.load(open('solvers/factor/cache/dec2_scored_v1.json'))
v3=json.load(open('solvers/factor/cache/dec2_scored.json'))
ids=[p for p in sorted(v3) if set(v3[p]['bases'])!=set(v1.get(p,{}).get('bases',[]))]
print(','.join(ids))
")
echo "changed: $(echo $IDS | tr ',' '\n' | wc -l)" >> solvers/factor/run_dec3_scored.log
.tools/bin/pypy3 -I -u solvers/factor/run.py scored --tl 12 --ids "$IDS" --cfg '{"cap":46,"refresh":12,"beam":2,"dec2":7}' > solvers/factor/run_r6.log 2>&1
