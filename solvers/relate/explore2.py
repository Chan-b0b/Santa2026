import sys, csv, json
from collections import Counter, defaultdict
sys.path.insert(0, 'solvers/relate')
from nt import fstr
rows = {r['id']: r for r in csv.DictReader(open('data/practice_puzzles.csv'))}
r = rows[sys.argv[1]]
s = json.loads(r['starting_values']); T = json.loads(r['targets']); L = int(r['value_limit'])
print(r['family'], s, L)
for j, t in enumerate(T):
    best = []
    for i, u in enumerate(T):
        if i == j: continue
        if u < t:
            k = (t + u // 2) // u
            e = t - k * u
            # relative significance: |e| / u  (random -> uniform in [0,0.5])
            best.append((abs(e) / u, f"{t} = {k}*{u} + {e}"))
        else:
            k = (u + t // 2) // t
            e = u - k * t
            best.append((abs(e) / t, f"{u} = {k}*{t} + {e}"))
    # pairs sum/diff
    for i, u in enumerate(T):
        for i2 in range(i + 1, len(T)):
            v = T[i2]
            if i == j or i2 == j: continue
            for val, desc in ((u + v, f"{u}+{v}"), (v - u, f"{v}-{u}")):
                e = t - val
                best.append((abs(e) / t * 30, f"{t} = {desc} + {e}"))
    best.sort()
    print(t, '|', '; '.join(f"{d} ({q:.2g})" for q, d in best[:2]))
