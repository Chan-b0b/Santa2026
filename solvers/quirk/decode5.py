"""짝이 훑기 후보가 아닌 경우의 해독: 후보 d 하나의 적중 목표들에서 몫 (t - r)/d 의 공약수 g 를 짝으로 삼는다.
짝이 작으면(2^13 미만) 그 짝과 곱해 여러 목표를 설명하는 상대를 표결로 찾는다(R=1024, k<=64).
decode_any 가 빈손인 퍼즐에 쓴다.  사용: decode5.py <id>"""
import sys, math, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
import decode as d1, decode2 as d2

def hub_from_candidate(hits, d):
    """hits: {t: r}. (g, 지지 목표 수) — g 는 몫들의 공약수. 하나를 빼고도 본다."""
    cof = [(t - r) // d for t, r in hits.items()]
    n = len(cof)
    best = (0, 0)
    def ok(g, m): return (g >= 256 and m >= 3) or (g >= 64 and m >= 4)
    g = 0
    for c in cof: g = math.gcd(g, c)
    if ok(g, n): best = (g, n)
    if n >= 4:
        for i in range(n):
            g = 0
            for j, c in enumerate(cof):
                if j != i: g = math.gcd(g, c)
            if ok(g, n - 1) and (n - 1, g) > (best[1], best[0]): best = (g, n - 1)
    return best

def partners(T, a, R=1024, K=64, minvotes=3):
    votes = collections.defaultdict(set)
    for t in T:
        for k in range(1, K + 1):
            m = k * a
            lo = -(-(t - R) // m); hi = (t + R) // m
            if lo < 512: break
            for d in range(lo, hi + 1): votes[d].add(t)
    out = [(len(ts), d) for d, ts in votes.items() if len(ts) >= minvotes]
    out.sort(reverse=True)
    return out

def decode(targets, dmax_bits=24):
    T = sorted(t for t in set(targets) if t >= 1 << 16)
    if len(T) < 4: return [], {}
    dmax = min(1 << dmax_bits, max(T) // 4)
    cands = d1.scan(T, dmax)
    hubs = []
    for d, hits in cands.items():
        if d < 512: continue
        g, m = hub_from_candidate(hits, d)
        if g and d * g >= 1 << 24: hubs.append((m, d * g, d, g))
    if not hubs: return [], {}
    hubs.sort(reverse=True)
    m, H, d, g = hubs[0]
    B = [d, g]
    # 같은 허브를 다른 d 로 본 것들 중 가장 큰 d 를 쓴다 (g 가 k 의 공약수를 먹은 경우를 줄인다)
    for a in list(B):
        if a < 1 << 13:
            for nv, dd in partners(T, a)[:6]:
                if dd not in B and dd >= 512: B.append(dd)
    cov = d2.explain(T, B, hmin=1 << 20)
    for _ in range(6):
        gg = d2.expand_once(T, B, cov)
        if gg is None: break
        B.append(gg)
        cov2 = d2.explain(T, B, hmin=1 << 20)
        if len(cov2) <= len(cov): B.pop(); break
        cov = cov2
    # 두 번 이상 쓰이는 것만
    while True:
        used = collections.Counter()
        for k, a, b, r in cov.values():
            used[a] += 1
            if b != a: used[b] += 1
        keep = [b for b in B if used[b] >= 2]
        if len(keep) == len(B): break
        B = keep; cov = d2.explain(T, B, hmin=1 << 20)
    if len(cov) < 3: return [], {}
    B.sort(key=lambda b: -used[b])
    return B, cov

if __name__ == '__main__':
    pid = sys.argv[1]
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]
    B, cov = decode(p.targets)
    print(pid, 'start', p.start, 'bases', B)
    for t in sorted(p.targets):
        if t in cov:
            k, d, dd, r = cov[t]; print(f'  {t} = {k}*{d}*{dd} {r:+d}')
        else: print(f'  {t} ?')
    print(f'explained {len(cov)}/{len(p.targets)}')
