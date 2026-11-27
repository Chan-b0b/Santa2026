"""combine/borrow 결과 JSON 에서 best 보다 짧고 check_program 을 통과한 것만 results/lend.csv 에 쓴다."""
import sys, os, glob, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
D = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(ROOT, "results", "lend.csv")
cur = {}
if os.path.exists(out):
    for k, v in read_submission(out).items(): cur[k] = json.loads(v)
for f in glob.glob(os.path.join(D, "combine_*.json")) + glob.glob(os.path.join(D, "borrow_*.json")):
    for key, r in json.load(open(f)).items():
        if not r.get("prog") or r.get("end") is None: continue
        pid = key.split(":")[0]; pz = P[pid]
        if len(r["prog"]) < len(BEST[pid]) and check_program(pz, r["prog"]) is None and (pid not in cur or len(r["prog"]) < len(cur[pid])):
            cur[pid] = r["prog"]
cur = {p: c for p, c in cur.items() if len(c) < len(BEST[p])}
if cur:
    tmp = out + ".tmp"; write_submission(tmp, cur); os.replace(tmp, out)
    print(len(cur), "퍼즐", {p: (len(BEST[p]), len(c)) for p, c in cur.items()})
