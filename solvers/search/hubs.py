"""숨은 허브와 밑수 찾기 (2라운드, lns/quirk 의 승자 프로그램을 해독해서 배운 구조).

구조형 퍼즐의 목표는 t = k*h + r 꼴이다. h 는 여러 목표가 함께 쓰는 허브(보통 밑수 둘의 곱 a*b),
k 와 r 은 작은 값이다. r 이 15비트까지 커서 (t - c) 의 gcd (seeds.py) 로는 대부분 놓친다.

1. 목표 쌍 (t1, t2) 의 연분수 전개에서 |q*t2 - p*t1| 이 t1/q 에 비해 아주 작은 근사분수 p/q 를 찾는다.
   그러면 t1 ~ q*h, t2 ~ p*h 이고 h 후보는 round(t1/q), round(t2/p) 다 (곱수가 큰 쪽이 h 를 정확히 고정한다).
2. 후보마다 |t - round(t/h)*h| 가 작은 목표(지지 목표)를 세고, 지지가 많은 것부터 고른다.
   같은 군집의 후보끼리는 나머지 r 들의 비용 합이 작은 쪽을 고른다.
3. 허브끼리의 gcd 와 제곱근에서 밑수를 뽑고, 밑수 쌍의 곱 가운데 목표 하나라도 지지하는 것을 허브에 더한다.
"""
import math


def _rescost(r, scost):
    if r == 0:
        return 0.0
    r = abs(r)
    c = scost.get(r)
    if c is not None:
        return 0.5 + c
    return 2.0 + r.bit_length() / 4.0


def members(h, T, shift=10, kb=None):
    """허브 h 의 지지 목표 (t, k, r): t = k*h + r, |r| <= h >> shift.

    kb 를 주면 |r| <= (k + 1) << kb 도 요구한다. 허브의 배수는 k 가 줄어 허용 폭이 좁아지므로, 큰 배수가 느슨한 허용 폭 덕에 이기는 일을 막는다.
    """
    out = []
    lim = h >> shift
    for t in T:
        k = (t + h // 2) // h
        if k < 1:
            continue
        r = t - k * h
        if abs(r) <= lim and (kb is None or abs(r) <= ((k + 1) << kb)):
            out.append((t, k, r))
    return out


def cf_candidates(T, A=1 << 10, minhub=1 << 18, qmax=1 << 22):
    cands = set()
    n = len(T)
    for i in range(n):
        t1 = T[i]
        if t1 < minhub:
            continue
        for j in range(i + 1, n):
            t2 = T[j]
            a, b = t2, t1
            p0, q0, p1, q1 = 0, 1, 1, 0
            while b:
                x = a // b
                p0, p1 = p1, x * p1 + p0
                q0, q1 = q1, x * q1 + q0
                a, b = b, a - x * b
                if q1 > qmax:
                    break
                h0 = t1 // q1
                if h0 < minhub:
                    break
                # b = |q1*t2 - p1*t1|
                if b * A < h0:
                    cands.add((t1 + q1 // 2) // q1)
                    cands.add((t2 + p1 // 2) // p1)
                    if b == 0:
                        break
    return cands


def scan_bases(scan, n, R=64, maxb=8):
    """basescan 출력 [(d, hits, mask)] 에서 밑수를 고른다: 우연 대비 놀라움이 큰 것부터, 서로 약수/배수 관계인 것은 하나만."""
    items = []
    for d, hits, mask in scan:
        lam = n * (2.0 * R + 1) / d
        lp = -lam + hits * math.log(lam) - math.lgamma(hits + 1)
        items.append((round(lp), d))
    items.sort()
    maskof = {d: mask for d, hits, mask in scan}
    chosen = []
    for lp, d in items:
        if any(c % d == 0 or d % c == 0 for c in chosen):
            continue
        chosen.append(d)
        if len(chosen) >= maxb:
            break
    # 같은 목표들을 지지하는 약수 가운데 가장 작은 것(4096 이상)으로 바꾼다. 10*a 보다 a 가 쓸모가 많다.
    out = []
    for c in chosen:
        mc = maskof[c]
        best = c
        for d, m in maskof.items():
            if d < best and d >= 4096 and c % d == 0 and (m & mc) == mc:
                best = d
        if best not in out:
            out.append(best)
    return out


def _gcost(h, mts, scost):
    """허브 후보 h 로 지지 목표들을 설명하는 비용: t = k*h + r 또는 t = (h + r1)*k + r2."""
    tot = 0.0
    for t in mts:
        k = (t + h // 2) // h
        if k < 1:
            return 1e9
        r = t - k * h
        c = _rescost(r, scost)
        if k > 1 and r != 0:
            r1 = (2 * r + k) // (2 * k)
            r2 = r - k * r1
            if r1 != 0:
                c2 = _rescost(r1, scost) + _rescost(r2, scost) + 0.5
                if c2 < c:
                    c = c2
        tot += c
    return tot


def find_hubs(targets, starts, scost=None, shift=10, min_support=3, max_clusters=24, topk=48, gmin=1 << 10, mode='pin', kb=()):
    """(허브 목록, 밑수 목록, 허브 -> 지지 목표 수) 를 돌려준다."""
    if scost is None:
        scost = {}
    T = sorted(set(targets))
    S0 = set(starts)
    cands = cf_candidates(T)
    scored = []
    for h in cands:
        if h < (1 << 16):
            continue
        ms = members(h, T, shift)
        if len(ms) < 2:
            continue
        cost = sum(_rescost(r, scost) for t, k, r in ms)
        scored.append((-len(ms), cost, h, ms))
    scored.sort(key=lambda z: (z[0], z[1], -z[2]))
    clusters = []
    covered = set()
    for negn, cost, h, ms in scored:
        if len(clusters) >= max_clusters:
            break
        mt = [t for t, k, r in ms]
        new = [t for t in mt if t not in covered]
        if len(new) < 2:
            continue
        clusters.append([h, ms, None])
        covered.update(mt)
    if not clusters and not kb:
        return [], [], {}
    # 군집마다 허브 후보: round(t/k) 와 그 근처(싼 작은 값만큼 이동), 가까운 제곱수
    small1 = sorted(s for s, c in scost.items() if c <= 1 and s < (1 << 12))[:80]
    small1 = sorted(set(small1) | set(range(1, 9)))
    for cl in clusters:
        h, ms, _ = cl
        mts = [t for t, k, r in ms]
        cset = {h}
        for t, k, r in ms:
            hq = h + (2 * r + k) // (2 * k)
            cset.add(hq)
            for sv in small1:
                cset.add(hq + sv)
                cset.add(hq - sv)
        ranked = sorted((_gcost(c, mts, scost), c) for c in cset if c > (1 << 16))
        top = ranked[:topk]
        s0 = math.isqrt(h)
        for sq in (s0 * s0, (s0 + 1) * (s0 + 1)):
            if abs(sq - h) <= (h >> shift) and all(sq != c for g, c in top):
                top.append((_gcost(sq, mts, scost), sq))
        cl[2] = top
    # 다른 군집의 후보와 큰 공약수를 갖는 후보가 진짜 허브다 (허브 = 밑수 둘의 곱).
    votes = {}
    n = len(clusters)
    for i in range(n):
        ti = clusters[i][2]
        for j in range(i + 1, n):
            tj = clusters[j][2]
            for g1, c1 in ti:
                for g2, c2 in tj:
                    if c1 == c2:
                        continue
                    g = math.gcd(c1, c2)
                    if g >= gmin:
                        votes.setdefault((i, c1), []).append(g)
                        votes.setdefault((j, c2), []).append(g)
    def valid(i, c):
        # 검증: 다른 군집과의 공약수 둘의 곱이 후보를 덮어야 한다 (c = a*b 이고 공약수는 a, b 의 배수. 제곱이면 같은 것 둘).
        vs = votes.get((i, c))
        if not vs:
            return False
        vs = sorted(set(vs), reverse=True)[:12]
        for x in vs:
            for y in vs:
                if (x * y) % c == 0:
                    return True
        return False

    lo = 1 << 9
    choice = [None] * n
    pin = [False] * n
    simple = mode == 'simple'
    for i, (h, ms, top) in enumerate(clusters):
        best = None
        for g, c in top:
            ok = 1 if (not simple and valid(i, c)) else 0
            key = (-ok, g)
            if best is None or key < best[0]:
                best = (key, c)
        choice[i] = best[1]
        pin[i] = bool(-best[0][0])
    cnt = {}
    for rnd in range(3):
        pinned = [choice[i] for i in range(n) if pin[i] or simple]
        cnt = {b: 2 for b in kb}
        for h1 in pinned:
            for b in kb:
                if h1 % b == 0 and h1 // b >= lo and h1 // b != b:
                    c = h1 // b
                    cnt[c] = cnt.get(c, 0) + 1
        for i, h1 in enumerate(pinned):
            sq = math.isqrt(h1)
            if sq * sq == h1 and sq >= lo:
                cnt[sq] = cnt.get(sq, 0) + 2
            for h2 in pinned[i + 1:]:
                g = math.gcd(h1, h2)
                if g < lo:
                    continue
                if g != h1 and g != h2:
                    cnt[g] = cnt.get(g, 0) + 1
                for c in (h1 // g, h2 // g):
                    if c >= lo:
                        cnt[c] = cnt.get(c, 0) + 1
        # 아직 고정 못 한 군집: 알려진 밑수(4096 이상)로 나누어지는 후보가 있으면 그것으로 고정한다.
        big = [b for b in cnt if b >= (1 << 12)]
        changed = False
        if big and not simple:
            for i, (h, ms, top) in enumerate(clusters):
                if pin[i]:
                    continue
                hit = None
                for g, c in top:
                    nb = 0
                    x = c
                    for b in big:
                        if x % b == 0:
                            nb += 1
                            x //= b
                            if x % b == 0:
                                nb += 1
                    if nb >= 2:
                        hit = c
                        break
                    if nb == 1 and hit is None:
                        hit = c
                if hit is not None:
                    choice[i] = hit
                    pin[i] = True
                    changed = True
        if not changed:
            break
    hubs = []
    info = {}
    for i, (h, ms, top) in enumerate(clusters):
        hp = choice[i]
        tight = len(ms) == 2 and all(abs(r) <= (h >> 16) for t, k, r in ms)
        if pin[i] or len(ms) >= min_support or tight:
            if hp not in info:
                hubs.append(hp)
                info[hp] = len(members(hp, T, shift))
    hs = set(hubs)
    bases = [b for b, c in cnt.items() if c >= 2 and b not in hs]
    if not bases:
        bases = [b for b in cnt if b not in hs]
    bases.sort(key=lambda b: (-cnt[b], b))
    bases = sorted(b for b in bases[:16] if b not in S0)
    # 다른 밑수의 배수인 것은 뺀다 (작은 쪽에서 명령 1~2개로 만들어진다).
    bases = [b for b in bases if not any(a < b and b % a == 0 for a in bases)][:10]
    # 밑수끼리 배수 관계면 작은 쪽만 남긴다 (큰 쪽은 명령 1~2개로 만들어진다).
    # 밑수 쌍의 곱 가운데 목표가 지지하는 것을 허브에 더한다.
    extra = []
    for i, a in enumerate(bases):
        for b in bases[i:]:
            h = a * b
            if h in hs or h > T[-1] * 2 or h < (1 << 20):
                continue
            ms = members(h, T, 13)
            if ms:
                extra.append((-len(ms), h))
                info[h] = len(ms)
                hs.add(h)
    extra.sort()
    hubs = [h for h in hubs + [h for c, h in extra[:24]] if h not in S0]
    return hubs, bases, info


if __name__ == '__main__':
    import sys, time
    sys.path.insert(0, "/home/maverick/Santa2026/core")
    sys.path.insert(0, "/home/maverick/Santa2026/solvers/search")
    from verify import load_puzzles
    path = '/home/maverick/Santa2026/data/puzzles.csv'
    P = load_puzzles(path)
    for pid in sys.argv[1:]:
        pz = P[pid]
        t0 = time.time()
        import solver
        scost = solver.build_small(sorted(set(pz.start)), pz.limit, 20000)[0]
        hubs, bases, info = find_hubs(pz.targets, pz.start, scost=scost)
        print(pid, 'time %.2f' % (time.time() - t0))
        print('  hubs', [(h, info[h]) for h in hubs])
        print('  bases', bases)


def decode_smalls(targets, hubs, starts=(), shift=10, rmax=1 << 17, vmax=1 << 22):
    """정확한 허브가 주어졌을 때 목표마다 t = k*h + r 또는 t = (h + r1)*k + r2 로 풀어, 필요한 작은 값 {k, |r|, |r1|, |r2|} 를 센다.

    돌려주는 값: {작은 값: 필요한 목표 수}. 이 값들을 보조 목표로 먼저 만들면 여러 목표가 나눠 쓴다.
    """
    T = sorted(set(targets))
    skip = set(T) | set(starts) | set(hubs)
    need = {}
    for t in T:
        best = None
        for h in hubs:
            if h > t + (h >> shift) or h < (1 << 16):
                continue
            k = (t + h // 2) // h
            if k < 1:
                continue
            r = t - k * h
            if abs(r) > (h >> shift):
                continue
            vals = [k] if k > 1 else []
            if r != 0:
                if abs(r) <= rmax or k == 1:
                    vals.append(abs(r))
                else:
                    r1 = (2 * r + k) // (2 * k)
                    r2 = r - k * r1
                    if r1 != 0:
                        vals.append(abs(r1))
                    if r2 != 0:
                        vals.append(abs(r2))
            size = sum(v.bit_length() for v in vals)
            if best is None or size < best[0]:
                best = (size, vals)
        if best is not None:
            for v in best[1]:
                if 2 <= v <= vmax and v not in skip:
                    need[v] = need.get(v, 0) + 1
    return need


def cluster_reps(targets, shift=10, maxreps=40):
    """연분수 후보 가운데 지지 목표가 2개 이상인 근사 허브들을 지지가 많은 순서로, 서로 가까운 것은 하나만 남겨 돌려준다."""
    T = sorted(set(targets))
    scored = []
    for h in cf_candidates(T):
        if h < (1 << 20):
            continue
        ms = members(h, T, shift)
        if len(ms) >= 2:
            # 곱수가 큰 지지 목표가 있으면 허브가 더 정확히 고정된다.
            kmax = max(k for t, k, r in ms)
            scored.append((-len(ms), -kmax, h))
    scored.sort()
    reps = []
    for negn, negk, h in scored:
        if any(abs(h - g) <= (g >> 12) for g in reps):
            continue
        reps.append(h)
        if len(reps) >= maxreps:
            break
    return reps


def _rnd(a, b):
    return (a + b // 2) // b


def tri_decode(targets, starts=(), W=1 << 15, minbase=1 << 12, reps=None, votes_only=False):
    """근사 허브들의 삼각 관계로 밑수를 정확히 복원한다.

    허브가 밑수 쌍의 곱이면 H1 ~ a*b, H2 ~ a*c, H3 ~ b*c 에서 a = sqrt(H1*H2/H3) 이다. 허브 근사의 상대 오차가
    2^-20 쯤이라 a 가 정수로 정확히 나오고, b = round(H1/a), c = round(H2/a) 도 정확하다. 제곱 허브 H ~ a^2 는 a = round(sqrt(H)).
    세 곱이 모두 근사 허브와 W 이내로 맞는 것만 받는다. 나머지가 커서 (t mod 밑수) 로는 안 보이는 퍼즐에서도 통한다.
    (밑수 목록, {정확한 허브: 지지 목표 수}) 를 돌려준다.
    """
    T = sorted(set(targets))
    if reps is None:
        reps = cluster_reps(T)
    n = len(reps)
    cnt = {}

    def vote(bs):
        for b in set(bs):
            cnt[b] = cnt.get(b, 0) + 1

    # 제곱 허브
    for k in range(n):
        y0 = math.isqrt(reps[k])
        for y in (y0, y0 + 1):
            if y < minbase or abs(y * y - reps[k]) > W:
                continue
            for i in range(n):
                if i == k:
                    continue
                x = _rnd(reps[i], y)
                if x >= minbase and x != y and abs(x * y - reps[i]) <= W:
                    vote((x, y))
    # 삼각형
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                for (Hi, Hj, Hk) in ((reps[i], reps[j], reps[k]), (reps[i], reps[k], reps[j]), (reps[j], reps[k], reps[i])):
                    a0 = math.isqrt(Hi * Hj // Hk)
                    for a in (a0, a0 + 1):
                        if a < minbase:
                            continue
                        b = _rnd(Hi, a)
                        c = _rnd(Hj, a)
                        if b < minbase or c < minbase:
                            continue
                        if abs(a * b - Hi) <= W and abs(a * c - Hj) <= W and abs(b * c - Hk) <= W:
                            vote((a, b, c))
    if votes_only:
        return cnt
    if not cnt:
        return [], {}
    S0 = set(starts)
    cand = sorted(cnt, key=lambda b: (-cnt[b], b))[:24]
    return greedy_bases(T, cand, S0)


def greedy_bases(T, cand, S0=()):
    """밑수 후보에서, 쌍의 곱(허브)이 설명하는 목표 수가 늘어나는 것만 탐욕적으로 고른다 (배수/약수 중복이 빠진다)."""
    idx = {t: i for i, t in enumerate(T)}
    pm = {}
    for i, a in enumerate(cand):
        for b in cand[i:]:
            h = a * b
            if h > T[-1] * 2 or h < (1 << 20):
                continue
            ms = members(h, T, 13, 16)
            if ms:
                m = 0
                for t, k, r in ms:
                    m |= 1 << idx[t]
                pm[(a, b)] = m
    if not pm:
        return [], {}

    def pc(x):
        return bin(x).count('1')

    # 밑수 하나가 다른 후보들과 이루는 허브 전체의 지지 목표 (동점일 때 진짜 밑수를 고르는 데 쓴다. 배수는 지지가 줄어든다).
    solo = {}
    for (a, b), m in pm.items():
        solo[a] = solo.get(a, 0) | m
        solo[b] = solo.get(b, 0) | m
    (a0, b0), m0 = max(pm.items(), key=lambda kv: (pc(kv[1]), pc(solo[kv[0][0]]) + pc(solo[kv[0][1]]), min(kv[0])))
    chosen = [a0] if a0 == b0 else [a0, b0]
    covered = m0
    while len(chosen) < 8:
        best = None
        for c in cand:
            if c in chosen:
                continue
            m = 0
            for x in chosen + [c]:
                key = (c, x) if (c, x) in pm else (x, c)
                m |= pm.get(key, 0)
            gain = pc(m & ~covered)
            key = (gain, pc(solo.get(c, 0)), c)
            if gain >= 2 and (best is None or key > best[0]):
                best = (key, c, m)
        if best is None:
            break
        chosen.append(best[1])
        covered |= best[2]
    # 후처리. 탐욕 선택은 진짜 밑수의 약수를 고르기 쉽다 (약수는 설명력이 줄지 않는다). 설명하는 목표가 그대로인 한
    # 작은 소수를 곱해 키우고(곱수가 작아진다), 빼도 설명력이 그대로인 밑수는 뺀다.
    cache = {}

    def mask_of(h):
        m = cache.get(h)
        if m is None:
            m = 0
            if (1 << 20) <= h <= T[-1] * 2:
                for t, k, r in members(h, T, 13, 16):
                    m |= 1 << idx[t]
            cache[h] = m
        return m

    def cov(bs):
        m = 0
        for i, a in enumerate(bs):
            for b in bs[i:]:
                m |= mask_of(a * b)
        return m

    def prune(chosen):
        for c in sorted(chosen):
            if len(chosen) > 2:
                trial = [x for x in chosen if x != c]
                if cov(trial) == cov(chosen):
                    chosen = trial
        return chosen

    # 다른 밑수의 작은 배수는 뺀다 (허용 폭이 허브 크기에 비례해서 큰 배수가 목표 하나를 더 설명하는 일이 있다).
    chosen = [c for c in chosen if not any(a < c and c % a == 0 and c // a <= 64 for a in chosen)]
    chosen = prune(chosen)
    # 밑수는 작은 인수만큼 모호하다 (4500*264304 = 18000*66076). 한 밑수에 p 를 곱하고 나머지에서 p 를 나누는 이동으로,
    # 전체 설명력이 늘어나는 쪽(짝끼리의 곱도 진짜 허브가 되는 쪽)을 찾는다.
    for it in range(30):
        cur = pc(cov(chosen))
        moved = False
        for i, c in enumerate(chosen):
            for p in (2, 3, 5, 7):
                if not any(x != c and x % p == 0 for x in chosen):
                    continue
                trial = [c * p if x == c else (x // p if x % p == 0 else x) for x in chosen]
                if len(set(trial)) == len(trial) and min(trial) >= 256 and pc(cov(trial)) > cur:
                    chosen = trial
                    moved = True
                    break
            if moved:
                break
        if not moved:
            break
    for it in range(80):
        done = True
        # 허브를 많이 이루는 밑수부터 올린다 (제곱 허브나 여러 짝이 인수의 자리를 정해 준다).
        order = sorted(range(len(chosen)), key=lambda i: -sum(1 for x in chosen if mask_of(chosen[i] * x)))
        for i in order:
            c = chosen[i]
            for p in (2, 3, 5, 7):
                if c * p in chosen:
                    continue
                # 이 밑수가 들어가는 허브마다 지지 목표가 하나도 빠지지 않아야 한다.
                ok = True
                for x in chosen:
                    old = mask_of(c * x)
                    nw = mask_of(c * p * (x if x != c else c * p))
                    if nw & old != old:
                        ok = False
                        break
                if ok:
                    chosen = chosen[:i] + [c * p] + chosen[i + 1:]
                    done = False
                    break
            if not done:
                break
        if done:
            break
    chosen = prune(chosen)
    hubs = {}
    for i, a in enumerate(chosen):
        for b in chosen[i:]:
            m = mask_of(a * b)
            if m:
                hubs[a * b] = pc(m)
    bases = sorted(b for b in chosen if b not in S0)
    return bases, hubs


def decode_smalls2(targets, hubs, starts=(), shift=10, rmax=1 << 17, vmax=1 << 22):
    """decode_smalls 의 두 단계 버전: 나머지를 r = k*r1 + r2 로 쪼갤 때 다른 목표가 이미 필요로 하는 값이 나오는 쪽을 고른다.

    생성기는 (h + r1)*k + r2 의 k, r1, r2 를 같은 작은 값 풀에서 뽑으므로, 여러 목표가 같은 값을 쓰는 분해가 진짜일 가능성이 높다.
    """
    T = sorted(set(targets))
    skip = set(T) | set(starts) | set(hubs)
    fixed = {}
    amb = []
    for t in T:
        best = None
        for h in hubs:
            if h > t + (h >> shift) or h < (1 << 16):
                continue
            k = (t + h // 2) // h
            if k < 1:
                continue
            r = t - k * h
            if abs(r) > (h >> shift):
                continue
            size = k.bit_length() + abs(r).bit_length()
            if best is None or size < best[0]:
                best = (size, k, r)
        if best is None:
            continue
        size, k, r = best
        if k > 1:
            fixed[k] = fixed.get(k, 0) + 1
        if r == 0:
            continue
        if k == 1 or abs(r) < k:
            fixed[abs(r)] = fixed.get(abs(r), 0) + 1
        elif r % k == 0:
            fixed[abs(r // k)] = fixed.get(abs(r // k), 0) + 1
        else:
            amb.append((k, r))
    known = set(fixed) | set(starts) | {1}
    for k, r in amb:
        best = None
        r0 = (2 * r + k) // (2 * k)
        cands = set([0, r0])
        for d in range(-3, 4):
            cands.add(d)
            cands.add(r0 + d)
        for v in known:
            if v * k <= abs(r) + rmax:
                cands.add(v)
                cands.add(-v)
        for r1 in cands:
            r2 = r - k * r1
            if abs(r2) > rmax and r1 != 0:
                continue
            vals = [abs(x) for x in (r1, r2) if x != 0]
            hit = sum(1 for x in vals if x in known)
            bits = sum(x.bit_length() for x in vals)
            key = (len(vals) - hit, bits)
            if best is None or key < best[0]:
                best = (key, vals)
        for x in best[1]:
            fixed[x] = fixed.get(x, 0) + 1
            known.add(x)
    return {v: c for v, c in fixed.items() if 2 <= v <= vmax and v not in skip}


def uni_decode(targets, starts=(), scan=None, extra=()):
    """세 해독(삼각 관계, basescan, partnerscan)의 밑수 후보를 모두 모아 설명력으로 탐욕 선택한다.

    후보가 틀려도 쌍의 곱이 목표 2개 이상을 새로 빡빡하게(h >> 13) 설명해야만 뽑히므로 잘못된 밑수는 거의 못 들어온다.
    """
    T = sorted(set(targets))
    reps = cluster_reps(T)
    cand = {}
    for W in (1 << 9, 1 << 11, 1 << 13, 1 << 15, 1 << 17):
        cnt = tri_decode(T, starts, W=W, reps=reps, votes_only=True)
        for b in sorted(cnt, key=lambda b: (-cnt[b], b))[:20]:
            cand[b] = cand.get(b, 0) + cnt[b]
    if scan:
        n = len(T)
        items = []
        for d, hits, mask in scan:
            lam = n * 129.0 / d
            items.append((-lam + hits * math.log(lam) - math.lgamma(hits + 1), d))
        items.sort()
        for lp, d in items[:40]:
            if d >= 2048:
                cand.setdefault(d, 1)
    for b in extra:
        if b >= 2048:
            cand.setdefault(b, 1)
    if len(cand) < 2:
        return [], {}
    cl = sorted(cand, key=lambda b: (-cand[b], b))[:110]
    return greedy_bases(T, cl, set(starts))
