"""작은 숨은 정수(닻) 찾기: 해독한 밑수로 목표를 t = k*a*b + r 로 설명한 뒤,
k 와 |r| 들이 공통으로 (작은 배수 ± 아주 작은 수) 꼴이 되는 정수 s 를 고른다.
예: scored_0011 의 k, r 은 2405 의 배수가 많다 (9620, 692640, 173160, 74555, 360750 ...)."""


def explain(targets, bases):
    """{목표: (k, r, a, b)} — 나머지가 가장 작은 설명."""
    out = {}
    bs = sorted(set(bases))
    for t in targets:
        best = None
        for i, a in enumerate(bs):
            for b in bs[i:]:
                h = a * b
                R2 = max(16, h >> 17, min(h >> 13, 1024))
                if h > t + R2:
                    continue
                k = (t + h // 2) // h
                if k < 1:
                    continue
                r = t - k * h
                if abs(r) <= R2 and (best is None or abs(r) < abs(best[1])):
                    best = (k, r, a, b)
        if best is not None:
            out[t] = best
    return out


def find(targets, bases, smin=48, smax=1 << 17, maxn=2, verbose=False):
    ex = explain(targets, bases)
    M = set()
    for t, (k, r, a, b) in ex.items():
        if k >= smin:
            M.add(k)
        if abs(r) >= smin:
            M.add(abs(r))
    M = sorted(M)
    res = []
    used = set()
    for _ in range(maxn):
        cand = set()
        for m in M:
            if m in used:
                continue
            for j in range(1, 17):
                for s in (m // j, m // j + 1):
                    if smin <= s <= smax and abs(m - j * s) <= 2:
                        cand.add(s)
        best = None
        for s in cand:
            tol = min(4, s >> 6)
            hit = [m for m in M if m not in used and m >= s - tol and min(m % s, s - m % s) <= tol]
            exp = len(M) * (2 * tol + 1) / s
            if len(hit) >= max(4, 3 * exp + 2):
                key = (len(hit), s)
                if best is None or key > best[0]:
                    best = (key, s, hit)
        if best is None:
            break
        res.append(best[1])
        used |= set(best[2])
        if verbose:
            print("  닻", best[1], "적중", len(best[2]), best[2][:12])
    return res


if __name__ == "__main__":
    import json, sys
    sys.path.insert(0, "/home/maverick/Santa2026/core")
    from verify import load_puzzles
    P = load_puzzles("/home/maverick/Santa2026/data/puzzles.csv")
    D = json.load(open("/home/maverick/Santa2026/solvers/factor/cache/dec2_scored.json"))
    for pid in sys.argv[1:]:
        ex = explain(P[pid].targets, D[pid]["bases"])
        print(pid, D[pid]["bases"], "설명", len(ex), "/", len(P[pid].targets))
        print("  k:", sorted(v[0] for v in ex.values()))
        print("  |r|:", sorted(abs(v[1]) for v in ex.values()))
        print(find(P[pid].targets, D[pid]["bases"], verbose=True))
