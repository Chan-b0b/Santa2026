import sys, csv, json, time, cProfile, pstats
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
import engine3 as E
pid = sys.argv[1]
cfg = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
path = ROOT + ("/data/practice_puzzles.csv" if pid.startswith("practice") else "/data/puzzles.csv")
with open(path) as f:
    row = [r for r in csv.DictReader(f) if r["id"] == pid][0]
st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
eng = E.Engine(st, tg, lim, cfg=cfg, deadline=time.time() + 60)
pr = cProfile.Profile()
pr.enable()
eng.solve()
pr.disable()
print("총", len(eng.steps), eng.stats)
pstats.Stats(pr).sort_stats("tottime").print_stats(18)
