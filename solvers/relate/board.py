import csv, sys
sys.path.insert(0, '/home/maverick/Santa2026/core')
from verify import load_puzzles
P = load_puzzles('/home/maverick/Santa2026/data/puzzles.csv')
rows = list(csv.DictReader(open('/home/maverick/Santa2026/board/matrix.csv')))
def cls(pz):
    T = pz.targets
    if pz.limit <= 64: return 'tiny'
    mx = max(T)
    top = sum(1 for t in T if len(str(t)) == len(str(mx)))
    if top >= len(T) * 0.9: return 'indep'
    if top >= len(T) * 0.35: return 'mixed'
    if mx.bit_length() <= 34: return 'mult?'
    return 'shared?'
from collections import defaultdict
names = [c for c in rows[0].keys() if c not in ('id', 'lower_bound', 'best', 'gap', 'best_by')]
agg = defaultdict(lambda: defaultdict(int))
for r in rows:
    c = cls(P[r['id']])
    a = agg[c]
    a['n'] += 1
    a['best'] += int(r['best'])
    for nm in names:
        if r[nm]:
            a[nm] += int(r[nm])
    a['by_' + r['best_by']] += 1
print('class      n   best  ' + '  '.join(f'{nm:>8s}' for nm in names) + '   wins: ' + ' '.join(names))
for c, a in sorted(agg.items()):
    print(f"{c:8s} {a['n']:4d} {a['best']/a['n']:6.1f}  " + '  '.join(f"{a[nm]/a['n']:8.1f}" for nm in names) + '   ' + ' '.join(str(a['by_' + nm]) for nm in names))
tot = {nm: sum(int(r[nm]) for r in rows if r[nm]) for nm in names}
print(tot, 'best', sum(int(r['best']) for r in rows))
