import sys, csv, json
from collections import Counter
sys.path.insert(0, "/home/maverick/Santa2026/solvers/factor")
from nt import factor, fstr
with open("/home/maverick/Santa2026/data/practice_puzzles.csv") as f:
    rows = list(csv.DictReader(f))
print(Counter((r["family"], r["design_tier"]) for r in rows))
for r in rows:
    st = json.loads(r["starting_values"]); tg = json.loads(r["targets"])
    if r["family"] in sys.argv[1].split(",") and r["design_tier"] in sys.argv[2].split(","):
        print(r["id"], r["family"], r["design_tier"], "start", st, "limit", r["value_limit"], "ratio %.2f" % (int(r["value_limit"]) / max(tg)), "n", len(tg))
        if len(sys.argv) > 3:
            for t in tg:
                print("   ", t, "=", fstr(t))
