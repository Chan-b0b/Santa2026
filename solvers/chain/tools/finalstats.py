"""병합 뒤 matrix.csv 로 chain 대 best 를 집계한다 (노트용)."""
import csv, json, sys, collections
ROOT = "/home/maverick/Santa2026"
sd = json.load(open(ROOT + '/solvers/chain/seeds.json'))
rows = list(csv.DictReader(open(ROOT + '/board/matrix.csv')))
def tot(rs, k): return sum(int(r[k]) for r in rs if r[k])
sed = [r for r in rows if sd.get(r['id'])]; uns = [r for r in rows if not sd.get(r['id'])]
print('전체 chain', tot(rows, 'chain'), 'best', tot(rows, 'best'))
print('밑 있음', len(sed), 'chain', tot(sed, 'chain'), 'best', tot(sed, 'best'))
print('밑 없음', len(uns), 'chain', tot(uns, 'chain'), 'best', tot(uns, 'best'))
eq = [r for r in rows if r['chain'] == r['best']]
solo = [r for r in eq if all(int(r[k]) > int(r['chain']) for k in ('factor', 'lns', 'quirk', 'relate', 'search') if r[k])]
print('best 와 같음', len(eq), '단독', len(solo))
loss = collections.defaultdict(lambda: [0, 0])
for r in rows:
    d = int(r['chain']) - int(r['best'])
    if d > 0:
        loss[r['best_by']][0] += 1; loss[r['best_by']][1] += d
print('지는 상대', dict(loss))
B = collections.defaultdict(lambda: [0, 0, 0])
for r in rows:
    lb = max(int(r['lower_bound']), 1); ratio = int(r['best']) / lb
    k = '3 미만' if ratio < 3 else '3~6' if ratio < 6 else '6 이상'
    B[k][0] += 1; B[k][1] += int(r['chain']); B[k][2] += int(r['best'])
for k, v in B.items(): print(k, v)
for name in ('factor', 'lns', 'quirk', 'relate', 'search'):
    w = l = d = 0
    for r in rows:
        if r[name]:
            a = int(r['chain']); o = int(r[name])
            if a < o: w += 1
            elif a > o: l += 1; d += a - o
    print(name, 'chain 승', w, '패', l, '진 차이', d)
