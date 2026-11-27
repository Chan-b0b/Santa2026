"""허브 하나짜리 군집 해독: 연분수 관계로 목표들을 군집으로 묶고, 군집마다 t_i = k_i*H + r_i 의 H 를
오프셋 비트 합이 최소가 되도록 고른다. H 가 목표값 자신이면(이득 없음) 버린다.
출력은 run2 의 씨앗으로 쓸 허브 목록.  사용: decode7.py <id>"""
import sys, math, collections
from fractions import Fraction
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
from cf import relations

def clusters(T, thr=11.0, maxq=64):
    """CF 관계 그래프의 연결 성분. 변: (i, j, p, q) = q*T[i] ~ p*T[j]."""
    n = len(T); par = list(range(n)); edges = []
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for i in range(n):
        for j in range(i):
            best = None
            for sc, p, q, r in relations(T[i], T[j], maxq=1 << 16):
                if thr <= sc < 90 and q <= maxq and (best is None or sc > best[0]): best = (sc, p, q)
            if best:
                edges.append((i, j, best[1], best[2])); par[find(i)] = find(j)
    comp = collections.defaultdict(list)
    for i in range(n): comp[find(i)].append(i)
    return [sorted(c) for c in comp.values() if len(c) >= 2], edges

def hub_for(T, comp, edges, rmax=1 << 15):
    """군집의 배수 k_i 를 정하고(가장 작은 목표 기준 비율), 오프셋 비트 합이 최소인 H 를 찾는다."""
    i0 = comp[0]; ratio = {i0: Fraction(1)}
    adj = collections.defaultdict(list)
    for i, j, p, q in edges:
        adj[i].append((j, Fraction(q, p))); adj[j].append((i, Fraction(p, q)))     # T[j] ~ (q/p) T[i]
    st = [i0]
    while st:
        x = st.pop()
        for y, f in adj[x]:
            if y in comp and y not in ratio: ratio[y] = ratio[x] * f; st.append(y)
    if len(ratio) < len(comp): return None
    Q = 1
    for f in ratio.values(): Q = Q * f.denominator // math.gcd(Q, f.denominator)
    if Q > 4096: return None
    ks = {i: int(ratio[i] * Q) for i in comp}
    H0 = T[i0] // ks[i0]
    kmax = max(ks.values())
    W = min(rmax, max(64, rmax // 1))            # H 탐색 반폭
    best = None
    for H in range(max(2, H0 - W), H0 + W + 1):
        tot = 0.0
        for i in comp:
            r = abs(T[i] - ks[i] * H)
            tot += math.log2(r + 1)
            if best is not None and tot >= best[0]: break
        else:
            best = (tot, H)
    tot, H = best
    members = [(T[i], ks[i], T[i] - ks[i] * H) for i in comp]
    return H, members, tot

def decode(targets):
    T = sorted(t for t in set(targets) if t >= 1 << 20)
    comps, edges = clusters(T)
    hubs = []
    for comp in comps:
        if len(comp) < 3: continue
        res = hub_for(T, comp, edges)
        if res is None: continue
        H, members, tot = res
        if H in targets: continue
        hubs.append((H, members))
    hubs.sort(key=lambda x: x[0])
    return hubs

if __name__ == '__main__':
    pid = sys.argv[1]
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]
    for H, members in decode(p.targets):
        print('hub', H, ' '.join(f'[{t} = {k}H{r:+d}]' for t, k, r in members))
