"""작은 숨은 정수용 해독 3판: 오프셋이 큰(수백~수천) 작은 허브 퍼즐.
(t, k, a, b, r) 를 넓게 모은 뒤(k<=4, |r|<=R), 정수들을 점, 설명을 변으로 본 그래프에서
세 정수가 서로 모두 이어진 삼각형(자기 자신과의 변 = 제곱 포함) 중 서로 다른 목표를 가장 많이 덮는 것을 찾고 넓힌다.
우연한 삼각형은 목표 3개만 덮으므로 5개 이상 덮는 것만 받아들인다.
사용: decode6.py <id> [R] [K]"""
import sys, collections, math
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
import decode3, decode2

def decode(targets, R=512, K=4, amin=128, amax=1 << 16, need=4, hmin=1 << 18, minscore=44.0):
    T = sorted(t for t in set(targets) if t >= 1 << 18)
    if len(T) < 5: return [], {}
    inc = decode3.incidences(T, K, R, amin, amax)
    edge = collections.defaultdict(dict)         # (a, b) a<=b -> {목표: 가장 작은 |r|}
    for t, k, a, b, r in inc:
        if b > 1 << 22: continue
        e = edge[(a, b)]
        if t not in e or abs(r) < e[t]: e[t] = abs(r)
    # 변의 무게: 가장 잘 맞는 목표의 놀라움(비트) + 같은 허브의 추가 목표마다 2비트
    w = {}
    for (a, b), e in edge.items():
        h = a * b
        w[(a, b)] = max(math.log2(h / (2 * r + 1)) for r in e.values()) + 2 * (len(e) - 1)
    adj = collections.defaultdict(set)
    for (a, b) in edge:
        if a != b: adj[a].add(b); adj[b].add(a)
    def score(S):
        S = sorted(S); tot = 0.0; ne = 0; ts = set()
        for i, x in enumerate(S):
            for y in S[i:]:
                if (x, y) in w: tot += w[(x, y)]; ne += 1; ts |= set(edge[(x, y)])
        return tot, ne, ts
    best = None
    def consider(S):
        nonlocal best
        sc, ne, ts = score(S)
        if ne >= 3 and sc >= minscore and len(ts) >= need and (best is None or sc > best[0]): best = (sc, list(S))
    for (a, b) in edge:
        if a != b: consider((a, b))
    for a in adj:
        nb = sorted(adj[a], key=lambda y: -w[(min(a, y), max(a, y))])[:12]
        for i, b in enumerate(nb):
            for c in nb[i + 1:]:
                consider((a, b, c))
    if best is None: return [], {}
    B = best[1]
    # 넓히기: 현재 집합의 두 정수 이상과 이어져 있고 점수를 가장 많이 올리는 정수 (변 2개 이상, 새 목표 2개 이상)
    while len(B) < 8:
        cs, cne, cts = score(B); cand = collections.Counter()
        for x in B:
            for y in adj[x]:
                if y not in B: cand[y] += 1
        bestc = None
        for y, n in cand.items():
            sc, ne, ts = score(B + [y])
            if len(ts) - len(cts) >= 1 and sc - cs >= 30 and (ne - cne >= 2 or sc - cs >= 36) and (bestc is None or sc > bestc[0]): bestc = (sc, y)
        if bestc is None: break
        B.append(bestc[1])
    # 집합 안에서 허브(변)를 2개 이상 가진 정수만 남긴다 (자기 자신과의 변 포함)
    while True:
        deg = collections.Counter()
        Ss = sorted(B)
        for i, x in enumerate(Ss):
            for y in Ss[i:]:
                if (x, y) in w:
                    deg[x] += 1
                    if y != x: deg[y] += 1
        keep = [x for x in B if deg[x] >= 2]
        if len(keep) == len(B): break
        B = keep
    if len(B) < 2: return [], {}
    cov = {}
    Bs = sorted(B)
    # 설명: 허브 크기와 무관하게 |r| <= max(R, h >> 13)
    for t in T:
        bb = None
        for i, a in enumerate(Bs):
            for b in Bs[i:]:
                h = a * b
                if h > 2 * t or h < hmin: continue
                k = (t + h // 2) // h
                if k < 1: continue
                r = t - k * h
                if abs(r) <= max(R, h >> 13) and abs(r) * 64 <= h:
                    sc = math.log2(h) - math.log2(2 * abs(r) + 1)
                    if bb is None or sc > bb[0]: bb = (sc, (k, a, b, r))
        if bb: cov[t] = bb[1]
    return B, cov

if __name__ == '__main__':
    pid = sys.argv[1]
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 512
    K = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]
    B, cov = decode(p.targets, R, K)
    print(pid, 'start', p.start, 'bases', B)
    for t in sorted(p.targets):
        if t in cov:
            k, d, dd, r = cov[t]; print(f'  {t} = {k}*{d}*{dd} {r:+d}')
        else: print(f'  {t} ?')
    print(f'explained {len(cov)}/{len(p.targets)}')
