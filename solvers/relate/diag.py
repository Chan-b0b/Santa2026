import sys, csv, json, time
sys.path.insert(0, '/home/maverick/Santa2026/core'); sys.path.insert(0, '/home/maverick/Santa2026/solvers/relate')
from verify import load_puzzles
import importlib
mod = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else 'solver3')
from collections import defaultdict
P = load_puzzles('/home/maverick/Santa2026/data/practice_puzzles.csv')
fam = {r['id']: r['family'] for r in csv.DictReader(open('/home/maverick/Santa2026/data/practice_puzzles.csv'))}
agg = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
ids = sorted(P)[:int(sys.argv[2]) if len(sys.argv) > 2 else 60]
for pid in ids:
    prog, log = mod.solve_puzzle(P[pid], {})
    if prog is None: continue
    f = fam[pid]
    for t, c, kind in log:
        b = (t.bit_length() // 10) * 10
        a = agg[f][(kind, b)]
        a[0] += 1; a[1] += c
    agg[f][('len', 0)][0] += 1; agg[f][('len', 0)][1] += len(prog)
for f in agg:
    print(f)
    for k in sorted(agg[f]):
        a = agg[f][k]
        print('   ', k, 'n=%d avg=%.2f' % (a[0], a[1] / a[0]))
