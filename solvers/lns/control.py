"""구조 검정: 실제 목표값과 같은 크기의 난수(대조군)를 시작값 식 트리 MITM 으로 분해해 적중률을 비교한다.
사용: control.py <practice id> [K]"""
import csv, json, random, sys, time
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from closure import closure, decompose
rows = {r['id']: r for r in csv.DictReader(open('data/practice_puzzles.csv', newline='', encoding='utf-8'))}
r = rows[sys.argv[1]]; K = int(sys.argv[2]) if len(sys.argv) > 2 else 8
seeds = json.loads(r['starting_values']); targets = json.loads(r['targets']); limit = int(r['value_limit'])
t0 = time.time()
level, seen = closure(seeds, limit, K)
print(r['id'], r['family'], 'seeds', seeds, 'sizes', [len(l) for l in level], f'{time.time()-t0:.0f}s')
def stats(ts):
    sizes = []
    for t in ts:
        d = decompose(t, level, seen, limit)
        sizes.append(d[0] if d else None)
    found = [s for s in sizes if s is not None]
    return len(found), len(ts), (sum(found) / len(found) if found else 0), sorted(found)
random.seed(1)
ctrl = [random.randrange(max(2, t // 2), min(limit, t * 2)) for t in targets for _ in range(2)]
print(' 실제  :', stats(targets))
print(' 대조군:', stats(ctrl))
