import sys, csv, json, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
import engine3 as E
pid = sys.argv[1]
path = ROOT + ("/data/practice_puzzles.csv" if pid.startswith("practice") else "/data/puzzles.csv")
with open(path) as f:
    row = [r for r in csv.DictReader(f) if r["id"] == pid][0]
st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
for c in sys.argv[2:]:
    cfg = json.loads(c)
    t0 = time.time()
    eng = E.Engine(st, tg, lim, cfg=cfg, deadline=time.time() + 600)
    eng.solve()
    print(c, "총", len(eng.steps), "시간 %.1f" % (time.time() - t0), {k: v for k, v in eng.stats.items() if not k.endswith("#")})
