import sys, csv, json
from collections import Counter, defaultdict
sys.path.insert(0, 'solvers/relate')
rows = list(csv.DictReader(open('data/practice_puzzles.csv')))
S = 5000
show = sys.argv[1] if len(sys.argv) > 1 else None
stats = defaultdict(Counter)
for r in rows:
    s = json.loads(r['starting_values']); T = json.loads(r['targets']); L = int(r['value_limit'])
    if r['family'] == 'tiny': continue
    K = sorted(set(s) | set(T))
    for t in T:
        if t in s: continue
        Kx = [k for k in K if k != t]
        # L0 and L1 values
        X = {}
        for a in Kx:
            X[a] = (a,)
        for i, a in enumerate(Kx):
            for b in Kx[i:]:
                for v, d in ((a + b, (a, '+', b)), (a * b, (a, '*', b)), (b - a, (b, '-', a))):
                    if 1 < v <= L and v not in X: X[v] = d
                if b % a == 0 and b // a > 1 and b // a not in X: X[b // a] = (b, '/', a)
        best = None
        for x, d in X.items():
            if x < 1000: continue
            if x <= t:
                k, e = divmod(t, x)
                if e > x - e: k += 1; e -= x
                if abs(e) <= S and k <= S:
                    c = (len(d) > 1) + (k != 1) + (e != 0)
                    cand = (c, abs(e) + k, f"{t} = {k}*{d} + {e}")
                    if best is None or cand < best: best = cand
            else:
                k, e = divmod(x, t)
                if e > t - e: k += 1; e -= t
                if abs(e) <= S and k <= S:
                    c = (len(d) > 1) + (k != 1) + (e != 0)
                    cand = (c, abs(e) + k, f"{d} = {k}*{t} + {e}")
                    if best is None or cand < best: best = cand
        stats[r['family']][best[0] if best else 'none'] += 1
        if r['id'] == show:
            print(t, best)
for f, c in stats.items():
    print(f, sorted(c.items(), key=str))
