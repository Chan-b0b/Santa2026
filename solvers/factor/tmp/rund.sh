#!/bin/bash
# 해독 v4 (작은 밑수 확장) -> 밑수가 달라진 퍼즐 재실행(D1) -> 해독된 퍼즐 전체를 난수 씨를 바꿔 재실행(D2, best 와 차이 큰 것부터)
cd /home/maverick/Santa2026
cp solvers/factor/cache/dec2_scored.json solvers/factor/cache/dec2_scored_v3.json
.tools/bin/pypy3 -I -u solvers/factor/decode2.py scored 5 > solvers/factor/run_dec4_scored.log 2>&1
IDS=$(.venv/bin/python -I -c "
import json
v3=json.load(open('solvers/factor/cache/dec2_scored_v3.json'))
v4=json.load(open('solvers/factor/cache/dec2_scored.json'))
ids=[p for p in sorted(v4) if set(v4[p]['bases'])!=set(v3.get(p,{}).get('bases',[]))]
print(','.join(ids))
")
echo "changed: $(echo $IDS | tr ',' '\n' | wc -l)" >> solvers/factor/run_dec4_scored.log
if [ -n "$IDS" ]; then
.tools/bin/pypy3 -I -u solvers/factor/run.py scored --tl 18 --keeporder --saveevery 50 --ids "$IDS" --cfg '{"cap":46,"refresh":12,"beam":2,"dec2":7,"anchors":1}' > solvers/factor/run_r8.log 2>&1
fi
IDS2=$(.venv/bin/python -I -c "
import json,csv
v4=json.load(open('solvers/factor/cache/dec2_scored.json'))
rows={r['id']:r for r in csv.DictReader(open('board/matrix.csv'))}
ids=sorted(v4, key=lambda p: -(int(rows[p]['factor'])-int(rows[p]['best'])))
print(','.join(ids))
")
.tools/bin/pypy3 -I -u solvers/factor/run.py scored --tl 18 --keeporder --saveevery 50 --ids "$IDS2" --cfg '{"cap":46,"refresh":12,"beam":2,"dec2":7,"anchors":1,"seed":7}' > solvers/factor/run_r9.log 2>&1
