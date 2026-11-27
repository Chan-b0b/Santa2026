#!/bin/bash
cd /home/maverick/Santa2026
IDS=$(cat solvers/factor/tmp/hid_practice_ids.txt)
PY=.tools/bin/pypy3
$PY -I solvers/factor/run.py practice --tl 6 --ids $IDS --cfg '{"cap":46,"refresh":12,"beam":2}' --out solvers/factor/tmp/p_base.json
$PY -I solvers/factor/run.py practice --tl 6 --ids $IDS --cfg '{"cap":46,"refresh":12,"beam":2,"hidk":3}' --out solvers/factor/tmp/p_h3.json
$PY -I solvers/factor/run.py practice --tl 6 --ids $IDS --cfg '{"cap":46,"refresh":12,"beam":2,"hidk":6}' --out solvers/factor/tmp/p_h6.json
