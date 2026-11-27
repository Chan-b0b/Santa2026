"""숨은 씨앗값 찾기: 서로 다른 목표의 (t - c) 들이 큰 공약수를 가지면 그 공약수가 숨은 중간값이다.

c 는 0 과 ±(작은 값: 시작값, 시작값 둘의 합/차/곱 중 작은 것).
"""
import math


def small_shifts(starts, maxval=200, maxn=40):
    vals = set(starts)
    st = sorted(set(starts))
    for i, x in enumerate(st):
        for y in st[:i + 1]:
            vals.add(x + y)
            vals.add(x * y)
            if x > y:
                vals.add(x - y)
                if x % y == 0:
                    vals.add(x // y)
    vals.add(1)
    vals = sorted(v for v in vals if 0 < v <= maxval)[:maxn]
    out = [0]
    for v in vals:
        out.append(v)
        out.append(-v)
    return out


_SMALLP = None


def strip_small(g):
    """4096 미만 소인수를 떼어 낸 나머지."""
    global _SMALLP
    if _SMALLP is None:
        n = 4096
        sieve = bytearray([1]) * n
        sieve[0] = sieve[1] = 0
        for i in range(2, 64):
            if sieve[i]:
                sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
        _SMALLP = [i for i in range(n) if sieve[i]]
    for p in _SMALLP:
        if p * p > g:
            break
        while g % p == 0:
            g //= p
    return g


def find_seeds(targets, starts, min_bits=14, shifts=None):
    """(씨앗값 -> 그 씨앗으로 나누어지는 (목표, c) 목록) 을 돌려준다."""
    T = sorted(set(targets))
    K = shifts if shifts is not None else small_shifts(starts)
    groups = []
    for t in T:
        groups.append([(t - c, c) for c in K if t - c > 1])
    prods = []
    for g in groups:
        p = 1
        for a, c in g:
            p *= a
        prods.append(p)
    total = 1
    for p in prods:
        total *= p
    lo = 1 << min_bits
    flagged = []
    for i, g in enumerate(groups):
        M = total // prods[i]
        for a, c in g:
            d = math.gcd(a, M % a)
            if d >= lo:
                d2 = strip_small(d)
                if d2 >= lo:
                    flagged.append((i, a, c))
    seeds = {}
    for x in range(len(flagged)):
        i, a, c = flagged[x]
        for y in range(x + 1, len(flagged)):
            j, b, c2 = flagged[y]
            if i == j:
                continue
            d = math.gcd(a, b)
            if d >= lo:
                d = strip_small(d)
                if d >= lo:
                    s = seeds.setdefault(d, set())
                    s.add((T[i], c))
                    s.add((T[j], c2))
    return seeds


if __name__ == '__main__':
    import sys, csv, collections, time
    sys.path.insert(0, "/home/maverick/Santa2026/core")
    from verify import load_puzzles
    path = '/home/maverick/Santa2026/data/practice_puzzles.csv'
    P = load_puzzles(path)
    fam = {r['id']: r['family'] for r in csv.DictReader(open(path))}
    agg = collections.defaultdict(lambda: [0, 0, 0, 0.0])
    for pid, pz in P.items():
        if pz.limit < 1 << 20:
            continue
        t0 = time.time()
        seeds = find_seeds(pz.targets, pz.start)
        covered = set()
        for s, users in seeds.items():
            for t, c in users:
                covered.add(t)
        a = agg[fam[pid]]
        a[0] += 1
        a[1] += len(pz.targets)
        a[2] += len(covered)
        a[3] += time.time() - t0
        if len(sys.argv) > 1 and pid in sys.argv[1:]:
            for s, users in sorted(seeds.items()):
                print(pid, 'seed', s, s.bit_length(), sorted(users))
    for f, a in sorted(agg.items()):
        print('%-15s puzzles %3d targets %5d with-seed %5d (%.0f%%)  avg time %.2fs' % (f, a[0], a[1], a[2], 100.0 * a[2] / a[1], a[3] / a[0]))
