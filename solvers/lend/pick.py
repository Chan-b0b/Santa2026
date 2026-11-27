import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistics, random, json
from lib import *
rows = []
for pid, pz in P.items():
    if pid not in BEST: continue
    b = statistics.median(t.bit_length() for t in pz.targets)
    rows.append((pid, b, len(pz.targets), len(BEST[pid])))
random.seed(7)
a = [r for r in rows if 48 <= r[1] < 56 and r[2] >= 20]; c = [r for r in rows if r[1] >= 56 and r[2] >= 20]
print(len(a), len(c))
sel = sorted(random.sample(a, 10)) + sorted(random.sample(c, 10))
json.dump([r[0] for r in sel], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pick20.json"), "w"))
for r in sel: print(*r)
