"""숨은 정수 해독 2판: decode.py 의 엄격한 1차 결과에서 출발해 넓힌다.
  - 근사 제곱 t ~ k*s^2 로 2^24 넘는 정수도 잡는다.
  - 이미 찾은 정수 a 로 t - r 을 나눈 몫들의 공약수에서 새 정수를 찾는다.
  - 설명 기준을 허브 크기에 비례하게 풀어(|r| <= a*b >> 13) 겹친 꼴(k2*(k1*a*b + r1) + r2)도 설명한다.
사용: decode2.py <id>"""
import sys, math, collections, os
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
from decode import decode as decode1

def explain(T, B, rel_bits=13, hmin=1 << 24):
    cov = {}
    Bs = sorted(B)
    for t in T:
        best = None
        for i, a in enumerate(Bs):
            for b in Bs[i:]:
                h = a * b
                if h > 2 * t: break
                if h < hmin: continue          # 작은 허브는 우연히 맞기 쉽고, 씨앗으로 쓸 가치도 없다
                k = (t + h // 2) // h
                if k < 1: continue
                r = t - k * h
                if abs(r) <= (h >> rel_bits):
                    sc = math.log2(h) - math.log2(2 * abs(r) + 1)
                    if best is None or sc > best[0]: best = (sc, (k, a, b, r))
        if best: cov[t] = best[1]
    return cov

def finalize(targets, B, bmin=512, minexp=3):
    """씨앗으로 쓸 정수만 남긴다: bmin 이상, 허브 2^24 이상인 설명에 두 번 이상 쓰이고, 전체 설명이 minexp 개 이상."""
    T = sorted(t for t in set(targets) if t >= 1 << 16)
    B = [b for b in B if b >= bmin]
    while B:
        cov = explain(T, B)
        used = collections.Counter()
        for k, a, b, r in cov.values():
            used[a] += 1
            if b != a: used[b] += 1
        keep = [b for b in B if used[b] >= 2]
        if len(keep) == len(B):
            if len(cov) < minexp: return [], {}
            B.sort(key=lambda b: -used[b])
            return B, cov
        B = keep
    return [], {}

def canonicalize(targets, B, rounds=20):
    """정수의 배율을 정리한다: b 를 2, 3, 5, 7 로 곱하거나 나눠서 (설명되는 목표 수, -k 의 비트 합)이 좋아지면 바꾼다.
    예: [46367, 788342, 274570] -> [92734, 394171, 549140]. 제곱 꼴(394171^2 - 25206)이 새로 설명된다."""
    T = sorted(t for t in set(targets) if t >= 1 << 16)
    B = list(B)
    def score(BB):
        cov = explain(T, BB)
        return (len(cov), -sum(math.log2(v[0]) for v in cov.values()))
    cur = score(B)
    for _ in range(rounds):
        improved = False
        for i in range(len(B)):
            for m in (2, 3, 5, 7):
                for nb in (B[i] * m, B[i] // m if B[i] % m == 0 else None):
                    if nb is None or nb < 256 or nb in B: continue
                    BB = B[:i] + [nb] + B[i + 1:]
                    sc = score(BB)
                    if sc > cur: B, cur, improved = BB, sc, True
        if not improved: break
    return B

def near_squares(T, kmax=16, rmax=4096, smin=1 << 24):
    out = set()
    for t in T:
        for k in range(1, kmax + 1):
            s = math.isqrt(t // k)
            for ss in (s, s + 1):
                r = t - k * ss * ss
                if ss >= smin and abs(r) <= rmax and abs(r) * 4096 < ss: out.add(ss)
    return out

def expand_once(T, B, cov):
    cof = []
    for t in T:
        if t in cov: continue
        for a in B:
            if a * 16 > t: continue
            m = t % a; r = m if m * 2 <= a else m - a
            if abs(r) <= min(a >> 7, 4096): cof.append(((t - r) // a, t))
    votes = collections.defaultdict(set)
    for i in range(len(cof)):
        ci, ti = cof[i]
        for j in range(i):
            cj, tj = cof[j]
            if ti == tj: continue
            g = math.gcd(ci, cj)
            if g >= 1024 and g not in B:
                votes[g].add(ti); votes[g].add(tj)
    if not votes: return None
    g = max(votes, key=lambda x: (len(votes[x]), x))
    return g

def decode(targets, dmax_bits=24):
    T = sorted(t for t in set(targets) if t >= 1 << 16)
    if len(T) < 3: return [], {}
    B, _ = decode1(targets, dmax_bits)
    for s in near_squares(T):
        if s not in B: B.append(s)
    if not B: return [], {}
    cov = explain(T, B)
    for _ in range(8):
        g = expand_once(T, B, cov)
        if g is None: break
        B.append(g)
        cov2 = explain(T, B)
        if len(cov2) <= len(cov):
            B.pop(); break
        cov = cov2
    # 쓰이지 않는 정수 제거
    used = collections.Counter()
    for k, a, b, r in cov.values(): used[a] += 1; used[b] += 1
    while True:
        keep = [b for b in B if used[b] >= 2]
        if len(keep) == len(B): break
        B = keep; cov = explain(T, B)
        used = collections.Counter()
        for k, a, b, r in cov.values(): used[a] += 1; used[b] += 1
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
            k, d, d2, r = cov[t]; print(f'  {t} = {k}*{d}*{d2} {r:+d}')
        else: print(f'  {t} ?')
    print(f'explained {len(cov)}/{len(p.targets)}')
