"""씨앗(숨은 허브/공통 인수) 후보 찾기: 목표값 ± 싼 보정값 사이의 최대공약수를 모아 득표순으로 돌려준다."""
from math import gcd
from collections import Counter


def seed_candidates(pz, max_out=12, gmin=1 << 9):
    start = sorted(set(pz.start))
    T = [t for t in pz.targets if t not in pz.start]
    L = pz.limit
    # 싼 보정값: 0, ±시작값, ±(시작값 한 번 연산 결과 중 작은 것)
    near = {0}
    for s in start:
        near.add(s)
        near.add(-s)
    l1 = set()
    for i, a in enumerate(start):
        for b in start[i:]:
            for v in (a + b, a * b, b - a):
                if 0 < v <= 4096:
                    l1.add(v)
            if b % a == 0:
                l1.add(b // a)
    far = set(near)
    for v in sorted(l1)[:24]:
        far.add(v)
        far.add(-v)
    A = [(t - e, i) for i, t in enumerate(T) for e in near if t - e > gmin]
    B = [(t - e, i) for i, t in enumerate(T) for e in far if t - e > gmin]
    votes = Counter()
    seen_pairs = {}
    for a, i in A:
        for b, j in B:
            if i == j:
                continue
            g = gcd(a, b)
            if g >= gmin:
                key = (g, min(i, j), max(i, j))
                if key not in seen_pairs:
                    seen_pairs[key] = True
                    votes[g] += 1
    tset = set(pz.targets) | set(pz.start)
    out = []
    # 점수: 득표수 * 크기(비트). 한 쌍에서만 나온 작은 gcd 는 우연일 수 있어 뒤로 민다.
    scored = sorted(votes.items(), key=lambda kv: (-(kv[1] * kv[0].bit_length()), kv[0]))
    for g, v in scored:
        if g in tset or g > L:
            continue
        if v < 2 and g.bit_length() < 16:
            continue
        out.append(g)
        if len(out) >= max_out:
            break
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/maverick/Santa2026/core")
    from verify import load_puzzles
    pid = sys.argv[1]
    P = load_puzzles("/home/maverick/Santa2026/data/practice_puzzles.csv" if pid.startswith("practice") else "/home/maverick/Santa2026/data/puzzles.csv")
    import time
    t0 = time.time()
    print(seed_candidates(P[pid]), time.time() - t0)
