"""퍼즐 하나의 풀이 과정을 목표별로 출력한다."""
import sys, csv, json, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
import engine3 as E
from nt import fstr
pid = sys.argv[1]
cfg = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
path = ROOT + ("/data/practice_puzzles.csv" if pid.startswith("practice") else "/data/puzzles.csv")
with open(path) as f:
    row = [r for r in csv.DictReader(f) if r["id"] == pid][0]
st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
print(pid, row.get("family"), "start", st, "limit", lim)
eng = E.Engine(st, tg, lim, cfg=cfg, deadline=time.time() + 30)
orig_apply = eng.apply
def apply(steps, tag=None):
    new = [s for s in steps if s[0] not in eng.pool]
    n = orig_apply(steps, tag)
    print("[%s +%d]" % (tag, n), "  ".join("%d=%d%s%d%s" % (v, a, op, b, "*" if v in eng.tset else "") for v, op, a, b in new))
    return n
eng.apply = apply
eng.solve()
print("총", len(eng.steps), "목표", len(tg), eng.stats)
