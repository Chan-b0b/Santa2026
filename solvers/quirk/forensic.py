"""숨은 구조 해독 도구: 시작값의 얕은 닫힘(S) → 목표값 t = k*h + e 의 허브 h 투표.
사용: forensic.py <id> [depth]"""
import sys, collections
sys.path.insert(0, 'core')
from verify import load_puzzles

def closure(start, limit, depth, vmax=None):
    """값 -> (비용, 유도). 트리 비용 기준, depth 단계까지."""
    cost = {s: 0 for s in start}; der = {s: None for s in start}
    levels = [set(start)]
    for d in range(1, depth + 1):
        new = {}
        for i in range(0, d):
            j = d - 1 - i
            if j < i: break
            A, B = levels[i], levels[j]
            for a in A:
                for b in B:
                    for v, dd in ((a + b, ('+', a, b)), (a * b, ('*', a, b)), (abs(a - b), ('-', max(a, b), min(a, b)))):
                        if 1 <= v <= limit and (vmax is None or v <= vmax) and v not in cost and v not in new:
                            new[v] = dd
                    if b and a % b == 0 and a // b not in cost and a // b not in new: new[a // b] = ('/', a, b)
                    if a and b % a == 0 and b // a not in cost and b // a not in new: new[b // a] = ('/', b, a)
        for v, dd in new.items(): cost[v] = d; der[v] = dd
        levels.append(set(new))
    return cost, der

def expr(v, der):
    d = der.get(v)
    if d is None: return str(v)
    return '(' + expr(d[1], der) + d[0] + expr(d[2], der) + ')'

def factor(n):
    f = []; d = 2
    while d * d <= n:
        while n % d == 0: f.append(d); n //= d
        d += 1 if d == 2 else 2
        if d > 3000000: break
    if n > 1: f.append(n)
    return f

if __name__ == '__main__':
    pid = sys.argv[1]; depth = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]
    cost, der = closure(p.start, p.limit, depth, vmax=10**6)
    S = sorted(cost)
    print(pid, 'start', p.start, 'limit', p.limit, '|S|', len(S))
    T = sorted(p.targets)
    votes = collections.defaultdict(list)
    for t in T:
        seen = set()
        for k in [1] + S:
            if k > t: continue
            for e in [0] + S + [-x for x in S]:
                if abs(e) * 8 > t: continue
                r = t - e
                if r <= 0 or r % k: continue
                h = r // k
                if h < 1000 or (h, ) in seen: continue
                c = (cost.get(k, 0) + (1 if k != 1 else 0)) + (cost.get(abs(e), 0) + (1 if e else 0))
                votes[h].append((c, t, k, e))
    # 허브: 서로 다른 목표 2개 이상
    hubs = []
    for h, lst in votes.items():
        best = {}
        for c, t, k, e in lst:
            if t not in best or c < best[t][0]: best[t] = (c, k, e)
        if len(best) >= 2:
            hubs.append((len(best), -sum(x[0] for x in best.values()), h, best))
    hubs.sort(reverse=True)
    for n, negc, h, best in hubs[:40]:
        print(f'hub {h} ({"·".join(map(str, factor(h)))}) n={n} cost={-negc}:', ', '.join(f'{t}={k}h{e:+d}' for t, (c, k, e) in sorted(best.items())))
