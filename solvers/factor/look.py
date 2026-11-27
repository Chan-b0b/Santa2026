import sys, csv, json
sys.path.insert(0, "/home/maverick/Santa2026/solvers/factor")
from nt import factor, fstr
fam = sys.argv[1]; n = int(sys.argv[2])
with open("/home/maverick/Santa2026/data/practice_puzzles.csv") as f:
    rows = [r for r in csv.DictReader(f) if r["family"] == fam]
for r in rows[:n]:
    st = json.loads(r["starting_values"]); tg = json.loads(r["targets"])
    print(r["id"], r["design_tier"], "start", st, "limit", r["value_limit"], "ratio %.2f" % (int(r["value_limit"]) / max(tg)))
    for t in tg:
        print("   ", t, "=", fstr(t))
