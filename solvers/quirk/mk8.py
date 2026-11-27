"""bases8.json(decode8 결과)에서 정수가 더해진 퍼즐만 골라 run2.py 용 정수 목록을 만든다.
정수는 설명에 쓰인 횟수 순으로 정렬한다(run2 는 앞 8개만 쓴다). 사용: mk8.py in.json out.json"""
import sys, json, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
import decode2
P = load_puzzles('data/puzzles.csv')
R = json.load(open(sys.argv[1])); out = {}
for pid, v in R.items():
    if not v['added']: continue
    T = sorted(t for t in set(P[pid].targets) if t >= 1 << 16)
    B = list(dict.fromkeys(v['bases']))
    cov = decode2.explain(T, B)
    used = collections.Counter()
    for k, a, b, r in cov.values():
        used[a] += 1
        if b != a: used[b] += 1
    B = [b for b in sorted(B, key=lambda b: -used[b]) if used[b] >= 2]
    out[pid] = {'bases': B, 'cov': {}, 'nt': len(cov), 'gain': v['c1'] - v['c0'], 'added': v['added']}
json.dump(out, open(sys.argv[2], 'w'))
g = sorted(out, key=lambda p: -out[p]['gain'])
print(len(out), 'puzzles; top gains:', [(p, out[p]['gain']) for p in g[:20]])
