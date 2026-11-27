"""board/matrix.csv 에서 factor 대 best 집계. 사용: compare.py"""
import csv, json, sys, collections
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core")
from verify import load_puzzles
P = load_puzzles(ROOT + "/data/puzzles.csv")
rows = list(csv.DictReader(open(ROOT + "/board/matrix.csv")))
apps = [k for k in rows[0] if k not in ("id", "lower_bound", "best", "gap", "best_by")]
print("합계", {a: (sum(int(r[a]) for r in rows if r[a]), sum(1 for r in rows if r[a])) for a in apps}, "best", sum(int(r["best"]) for r in rows))
by = collections.Counter(); bys = collections.Counter(); solo = tie = 0
for r in rows:
    f, b = int(r["factor"]), int(r["best"])
    if f > b:
        by[r["best_by"]] += 1; bys[r["best_by"]] += f - b
    else:
        others = [int(r[a]) for a in apps if a != "factor" and r[a]]
        if all(o > f for o in others): solo += 1
        else: tie += 1
print("factor 가 지는 퍼즐", sum(by.values()), dict(by), "손실 합", dict(bys), "단독 최단", solo, "공동 최단", tie)
for a in apps:
    if a == "factor": continue
    w = l = t = d = 0
    for r in rows:
        if r[a]:
            x, f = int(r[a]), int(r["factor"])
            w += f < x; l += f > x; t += f == x; d += f - x
    print("  vs", a, "승", w, "패", l, "무", t, "합계 차", d)
try:
    D = json.load(open(ROOT + "/solvers/factor/cache/dec2_scored.json"))
except Exception:
    D = {}
agg = collections.defaultdict(lambda: [0, 0, 0, 0])
for r in rows:
    pz = P[r["id"]]
    bits = sorted(t.bit_length() for t in pz.targets)
    med = bits[len(bits) // 2]
    key = ("해독" if r["id"] in D else "미해독", "<24" if med < 24 else "24-31" if med < 32 else "32-47" if med < 48 else ">=48")
    c = agg[key]; c[0] += 1; c[1] += int(r["factor"]); c[2] += int(r["best"]); c[3] += int(r["lower_bound"])
for k in sorted(agg):
    c = agg[k]
    print(k, "퍼즐", c[0], "factor", c[1], "best", c[2], "차", c[1] - c[2], "목표당 factor %.2f best %.2f" % (c[1] / max(c[3], 1), c[2] / max(c[3], 1)))
