#!/usr/bin/env python3
"""숨은 정수(base) 복원: 목표값이 k2*(k1*a*b + r1) 꼴일 때 a, b 를 찾는다. (pypy 권장)

quirk 의 basescan 은 |t mod a| 가 a/512 이하여야 해서, 겹친 꼴(k2 가 곱해져 보정이 커진 것)과
정수가 14~17비트로 작은 퍼즐을 놓친다. 여기서는
  1) 목표값을 작은 약수 k2 로 정확히 나눈 몫 u 들을 만든다 (끝 연산이 곱셈인 겹친 꼴을 벗긴다).
  2) 후보: 근사 제곱 u ~ k1*s^2 의 s, 목표값 쌍의 gcd 의 약수.
  3) 허브 판정: 어떤 몫 u 가 a*b 의 배수에서 min(a,b)/TOL 안에 있으면 (t, a, b) 를 '설명'으로 센다.
     (정수 하나를 1 바꾼 것보다 훨씬 작은 보정만 인정하므로 우연 확률이 쌍당 2^-14 수준이다.)
  4) 서로 다른 목표 MINT 개 이상에서 살아 있는 짝과 함께 설명에 쓰인 정수만 남긴다 (반복 가지치기).
  5) 남은 정수 a 로 round(u/(k1*a)) 에 목표 단위로 투표해 새 정수를 더하고 4) 를 다시 한다.
사용: hubs.py <id> ...
"""
import sys
from math import isqrt, gcd, log2
from collections import defaultdict

KDIV = 1 << 17
UCAP = 32
SMIN = 300
BMAX = 1 << 26
TOL = 6
MINT = 3


def quotients(t):
    out = [t]
    lim = min(KDIV, isqrt(t) + 1)
    for k in range(2, lim + 1):
        if t % k == 0:
            out.append(t // k)
            if len(out) >= UCAP:
                break
    return out


def small_divisors(g, lim=4096):
    return [d for d in range(1, min(lim, g) + 1) if g % d == 0]


def cand_squares(T, U, k1max=64, tolden=16, nu=12):
    best = {}
    tg = defaultdict(set)
    for t in T:
        for u in U[t][:nu]:
            if u < SMIN * SMIN:
                continue
            for k1 in range(1, k1max + 1):
                s = isqrt(u // k1)
                if s < SMIN:
                    break
                for ss in (s, s + 1):
                    r = u - k1 * ss * ss
                    if r < 0:
                        r = -r
                    if r * tolden <= k1 * ss and ss <= BMAX:
                        bits = log2(k1 * ss / (2 * r + 1))
                        tg[ss].add(t)
                        if bits > best.get(ss, 0):
                            best[ss] = bits
    return sorted(best, key=lambda s: (-len(tg[s]), -best[s]))


def cand_gcd(T):
    votes = defaultdict(set)
    n = len(T)
    for i in range(n):
        for j in range(i):
            g = gcd(T[i], T[j])
            if g < SMIN:
                continue
            for d in small_divisors(g):
                x = g // d
                if x < SMIN:
                    break
                if x <= BMAX:
                    votes[x].add(i)
                    votes[x].add(j)
    return sorted(votes, key=lambda x: (-len(votes[x]), -x))


def incidences(pool, T, U):
    pool = sorted(pool)
    inc = set()
    for ia, a in enumerate(pool):
        rest = pool[ia:]
        for t in T:
            for u in U[t]:
                if u < a * a:
                    break
                m = (2 * u + a) // (2 * a)
                res = u - a * m
                if res < 0:
                    res = -res
                if res * TOL > a:
                    continue
                for b in rest:
                    if b > m:
                        break
                    if m % b == 0 and res <= (a * b) >> 16:
                        inc.add((t, a, b))
    return inc


def core(inc, mint=MINT):
    cur = inc
    while True:
        sup = defaultdict(set)
        for t, a, b in cur:
            sup[a].add(t)
            sup[b].add(t)
        S = {x for x, ts in sup.items() if len(ts) >= mint}
        nxt = {e for e in cur if e[1] in S and e[2] in S}
        if len(nxt) == len(cur):
            return cur, sup
        cur = nxt


def votes_for(a, T, U, k1max=32):
    v = defaultdict(set)
    for t in T:
        for u in U[t]:
            if u < a * SMIN:
                break
            for k1 in range(1, k1max + 1):
                q = u // (k1 * a)
                if q < SMIN:
                    break
                for b in (q, q + 1):
                    if b > BMAX:
                        continue
                    r = u - k1 * a * b
                    if r < 0:
                        r = -r
                    m = a if a < b else b
                    if r * TOL <= m:
                        v[b].add(t)
    return v


def related(x, y):
    g = gcd(x, y)
    return x // g <= 64 and y // g <= 64


def dedupe(B, sup):
    """유리수 배 관계(p/q, p,q <= 64)인 정수 묶음에서 대표(설명 목표가 가장 많은 것, 같으면 큰 것)를 고른다."""
    order = sorted(B, key=lambda x: (-len(sup[x]), -x))
    kept = []
    rep = {}
    for x in order:
        for y in kept:
            if related(x, y):
                rep[x] = y
                break
        else:
            kept.append(x)
            rep[x] = x
    return kept, rep


BASEMIN = 1500


def decode(targets, verbose=False, npool=70, mint=MINT, basemin=BASEMIN, tmin=1 << 20, mincov=4):
    T = sorted(t for t in set(targets) if t >= tmin)
    if len(T) < 4:
        return [], {}
    U = {t: quotients(t) for t in T}
    sq = cand_squares(T, U)
    gc = cand_gcd(T)
    pool = []
    for src in (sq[:npool], gc[:npool]):
        for x in src:
            if x not in pool:
                pool.append(x)
    inc = incidences(pool, T, U)
    cur, sup = core(inc, mint)
    B = set(sup) if cur else set()
    for rnd in range(3):
        if not B:
            break
        new = defaultdict(set)
        for a in B:
            for b, ts in votes_for(a, T, U).items():
                if b not in B:
                    new[b] |= ts
        add = [b for b in sorted(new, key=lambda x: (-len(new[x]), -x)) if len(new[b]) >= max(3, mint)][:20]
        if not add:
            break
        pool2 = sorted(B | set(add))
        inc = incidences(pool2, T, U)
        cur, sup = core(inc, mint)
        B2 = set(sup) if cur else set()
        if B2 <= B:
            break
        B = B2
    B = {x for x in B if x >= basemin}
    if not B:
        return [], {}
    kept, rep = dedupe(B, sup)
    # 대표로 옮긴 설명
    expl = defaultdict(set)      # (a, b) -> 목표 집합
    for t, a, b in cur:
        if a in rep and b in rep:
            x, y = rep[a], rep[b]
            expl[(x, y) if x <= y else (y, x)].add(t)
    def covered(S):
        c = set()
        for (x, y), ts in expl.items():
            if x in S and y in S:
                c |= ts
        return c
    chosen = []
    cov = set()
    # 첫 선택은 쌍(또는 제곱만으로 3개 이상 설명하는 정수 하나)
    b2 = None
    for i, x in enumerate(kept):
        c = covered({x})
        if len(c) >= 3:
            key = (len(c), x * x)
            if b2 is None or key > b2[0]:
                b2 = (key, [x], c)
        for y in kept[i + 1:]:
            c = covered({x, y})
            key = (len(c), x * y)
            if b2 is None or key > b2[0]:
                b2 = (key, [x, y], c)
    if b2 is None or b2[0][0] < min(3, mincov):
        return [], {}
    chosen = sorted(b2[1], key=lambda x: -len(sup[x]))
    cov = b2[2]
    while len(chosen) < 8:
        best = None
        for x in kept:
            if x in chosen:
                continue
            c = covered(set(chosen) | {x})
            key = (len(c) - len(cov), len(sup[x]), x)
            if best is None or key > best[0]:
                best = (key, x, c)
        if best is None or best[0][0] < 2:
            break
        chosen.append(best[1])
        cov = best[2]
    if verbose:
        print('  kept', [(x, len(sup[x])) for x in kept[:14]])
    if len(cov) < mincov:
        return [], {}
    # 대안: 같은 묶음에서 설명 수가 대표와 2 이내인 가장 큰 정수
    alt = []
    for x in chosen:
        fam = [y for y in B if rep.get(y) == x and len(sup[y]) >= len(sup[x]) - 2]
        alt.append(max(fam) if fam else x)
    return chosen, {'cov': len(cov), 'alt': alt, 'n': len(T), 'targets': sorted(cov)}


if __name__ == '__main__':
    sys.path.insert(0, '/home/maverick/Santa2026/core')
    from verify import load_puzzles
    import time
    for pid in sys.argv[1:]:
        P = load_puzzles('/home/maverick/Santa2026/data/practice_puzzles.csv' if pid.startswith('practice') else '/home/maverick/Santa2026/data/puzzles.csv')
        t0 = time.time()
        B, cov = decode(P[pid].targets, verbose=True)
        print(pid, 'bases', B, cov, f'{time.time()-t0:.2f}s')
