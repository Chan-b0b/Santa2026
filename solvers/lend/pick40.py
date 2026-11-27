import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statistics, random
from lib import *
D = os.path.dirname(os.path.abspath(__file__))
old = set(json.load(open(os.path.join(D, "pick20.json"))))
rows = [(pid, statistics.median(t.bit_length() for t in pz.targets)) for pid, pz in P.items() if pid in BEST and len(pz.targets) >= 20 and pid not in old]
random.seed(11)
a = random.sample([r[0] for r in rows if 48 <= r[1] < 56], 20); c = random.sample([r[0] for r in rows if r[1] >= 56], 20)
ids = sorted(a) + sorted(c)
json.dump(ids, open(os.path.join(D, "pick40.json"), "w"))
json.dump({p: len(BEST[p]) for p in ids}, open(os.path.join(D, "pick40_bestlen.json"), "w"))
print(len(ids), sum(len(BEST[p]) for p in ids))
