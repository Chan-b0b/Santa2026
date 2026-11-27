"""실험: 목표값 t 에서 작은 보정 (t ± e)/k 를 뗀 값이 '매끄러운 수'(큰 소인수 없음)이면 숨은 허브일 가능성이 높다.
그런 허브 후보들의 소인수가 퍼즐 안에서 얼마나 반복되는지 본다. 사용: exp_factors.py <scored id>..."""
import sys, json, collections
sys.path.insert(0, 'solvers/lns'); sys.path.insert(0, 'core')
from verify import load_puzzles
from nt import factor
P = load_puzzles('data/puzzles.csv')
BOUND = 1 << 14

def smooth_part(n):
    f = factor(n)
    return f if max(f) < BOUND else None

for pid in sys.argv[1:]:
    pz = P[pid]; seeds = list(pz.start)
    smalls = {0}
    base = set(seeds) | {1}
    for a in base:
        for b in base:
            for v in (a + b, abs(a - b), a * b):
                if 0 < v < 4096: smalls.add(v)
    smalls |= base
    es = sorted(x for x in smalls if x < 2000)
    hubs = {}                                   # 허브 값 -> 지지하는 목표값 집합
    for t in set(pz.targets):
        if t < (1 << 18): continue
        for k in range(1, 41):
            for e in es:
                for sgn in (1, -1):
                    num = t - sgn * e
                    if num <= 0 or num % k: continue
                    h = num // k
                    if h < (1 << 16): continue
                    hubs.setdefault(h, set()).add(t)
                    if e == 0: break
    # 매끄러운 허브 후보만
    cnt = collections.Counter(); sup = collections.defaultdict(set); nsm = 0; smooth_hubs = []
    for h, ts in hubs.items():
        f = smooth_part(h)
        if f is None or sum(f.values()) < 3: continue
        nsm += 1; smooth_hubs.append((h, f, ts))
        for p in f:
            if p >= 11: cnt[p] += 1; sup[p] |= ts
    total_h = len(hubs)
    strong = [(len(sup[p]), p) for p in cnt if len(sup[p]) >= 3]
    strong.sort(reverse=True)
    print(f"{pid} 시작값 {seeds} 목표 {len(set(pz.targets))} 허브 후보 {total_h} 그중 매끄러운 것 {nsm} ({100.0*nsm/max(total_h,1):.1f}%)")
    print('   3개 이상 목표값에 걸친 소인수(목표 수, 소인수):', strong[:25])
    multi = sorted(((len(ts), h) for h, f, ts in smooth_hubs if len(ts) >= 2), reverse=True)[:10]
    print('   2개 이상 목표값이 가리키는 매끄러운 허브:', multi)
