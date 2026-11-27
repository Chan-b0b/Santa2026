"""숨은 정수(밑수) 해독 2: 후보 수집 + 쌍 검증 탐욕 선택.

구조형 퍼즐의 목표값은 t = k*a*b + r (a, b: 숨은 정수, k, r: 작은 수) 꼴이다.
후보 수집
  (1) hidscan(C++): d <= 2^24 를 전부 훑어 |t mod± d| <= 128 인 목표가 우연보다 많은 d (그리고 d/j, j <= 12).
  (2) 허브 충돌: 목표마다 h = (t - r)/k (k <= 512, |r| <= 128) 를 모아 서로 다른 목표 3개 이상(2^29 이상이면 2개 이상)이 같은 h 를 내면 허브.
      허브를 소인수분해해, 지지 목표 집합이 다른 허브 2개 이상을 나누는 약수를 후보로 둔다.
쌍 검증
  후보 쌍 (a, b) 마다 h = a*b 에 대해 |t mod± h| <= max(16, h >> 13) 인 목표 집합 V(a, b) 를 구한다.
탐욕 선택
  V(a,a) | V(a,b) | V(b,b) 가 가장 큰 쌍에서 시작해, 새로 설명되는 목표가 2개 이상인 후보를 하나씩 더한다.

사용: decode2.py <id>  |  decode2.py scored|practice [procs]
결과: cache/dec2_<mode>.json  {id: {"bases": [...], "gain": [...], "cov": n}}
"""
import csv, json, subprocess, sys, time
from collections import defaultdict

ROOT = "/home/maverick/Santa2026"
HERE = ROOT + "/solvers/factor"
sys.path.insert(0, HERE)
from nt import factor


def divisors(fac):
    ds = [1]
    for p, e in fac.items():
        cur = []
        pe = 1
        for _ in range(e):
            pe *= p
            cur += [d * pe for d in ds]
        ds += cur
    return ds


def scan_rows(pid, targets):
    inp = f"{pid} {len(targets)} " + " ".join(map(str, targets)) + "\n"
    out = subprocess.run([HERE + "/hidscan"], input=inp, capture_output=True, text=True).stdout
    rows = []
    for line in out.split("\n"):
        p = line.split()
        if len(p) >= 4 and p[1] != "END":
            rows.append((int(p[1]), int(p[2]), int(p[3], 16)))
    return rows


def hub_candidates(targets, K=512, R=128, hmin=1 << 20):
    cand = defaultdict(dict)
    for i, t in enumerate(targets):
        if t < hmin:
            continue
        Rt = min(R, t >> 10)
        for k in range(1, K + 1):
            lo = -((-(t - Rt)) // k)
            hi = (t + Rt) // k
            if hi < hmin:
                break
            if lo < hmin:
                lo = hmin
            for h in range(lo, hi + 1):
                cand[h][i] = t - k * h
    out = {}
    for h, s in cand.items():
        c = len(s)
        if c >= 2:
            out[h] = s
    return out


def decode(pid, targets, start=(), verbose=False, maxc=300, maxhub=3000):
    n = len(targets)
    tset = set(targets) | set(start)
    rows = scan_rows(pid, targets)
    C = {}
    # (1) 훑기 후보
    rows.sort(key=lambda r: -(r[1] - 1 - n * 257.0 / r[0]) * r[0].bit_length())
    seen_mask = defaultdict(int)
    for d, cnt, mask in rows:
        if seen_mask[mask] >= 4:
            continue
        seen_mask[mask] += 1
        C[d] = max(C.get(d, 0), 100 + cnt)
        for j in range(2, 13):
            if d % j == 0 and d // j >= 128:
                C[d // j] = max(C.get(d // j, 0), 50 + cnt)
        if len(C) > 150:
            break
    # (2) 허브 충돌 + 약수쌍 닫힘: 살아남은 정수를 후보로
    hubs = hub_candidates(targets)
    if len(hubs) > maxhub:
        ks = sorted(hubs, key=lambda h: (-len(hubs[h]), sum(abs(r) for r in hubs[h].values())))[:maxhub]
        hubs = {h: hubs[h] for h in ks}
    nbr = defaultdict(dict)
    for h, s in hubs.items():
        ts = frozenset(s)
        for a in divisors(factor(h)):
            if a >= 128 and a * a <= h:
                b = h // a
                nbr[a][b] = ts
                nbr[b][a] = ts
    alive = set(nbr)
    while True:
        dead = []
        for x in alive:
            ps = [y for y in nbr[x] if y in alive]
            if len(ps) < 2:
                dead.append(x)
                continue
            tg = set()
            for y in ps:
                tg |= nbr[x][y]
            if len(tg) < 3:
                dead.append(x)
                continue
            ps.sort()
            ok = False
            for i in range(len(ps)):
                pi = ps[i]
                for j in range(i + 1, len(ps)):
                    if ps[j] % pi:
                        ok = True
                        break
                if ok:
                    break
            if not ok:
                dead.append(x)
        if not dead:
            break
        alive.difference_update(dead)
    for x in alive:
        tg = set()
        for y, ts in nbr[x].items():
            if y in alive:
                tg |= ts
        C[x] = max(C.get(x, 0), len(tg))
    for x in list(C):
        if x in tset:
            del C[x]
    if len(C) < 1:
        return None
    cl = sorted(C, key=lambda x: (-C[x], -x))[:maxc]
    res = _select(sorted(cl), targets, verbose)
    if res is None:
        return None
    # 짝 채우기: 고른 밑수 a 가 나누는 (t - r) 의 몫들 사이의 공약수를 새 후보로 넣고 다시 고른다
    from math import gcd
    covbits = res["covbits"]
    qs = []
    for a in res["bases"]:
        if a < (1 << 13):
            continue
        Ra = min(128, a >> 6)
        for ti, t in enumerate(targets):
            if covbits >> ti & 1 or t < a * 128:
                continue
            r = t % a
            if r > a // 2:
                r -= a
            if abs(r) <= Ra:
                qs.append((t - r) // a)
    newc = set()
    for i in range(len(qs)):
        for j in range(i + 1, len(qs)):
            g = gcd(qs[i], qs[j])
            if g >= 128 and g not in tset and g not in C:
                newc.add(g)
    if newc and len(newc) <= 200:
        res2 = _select(sorted(set(cl) | newc), targets, verbose)
        if res2 is not None and res2["cov"] > res["cov"]:
            res = res2
    res.pop("covbits", None)
    return res


def _select(cl, targets, verbose=False):
    n = len(targets)
    tmax = max(targets)
    # 쌍 검증
    V = {}
    m = len(cl)
    for i in range(m):
        a = cl[i]
        for j in range(i, m):
            h = a * cl[j]
            if h > tmax:
                break
            R2 = max(16, h >> 13)
            bits = 0
            for ti, t in enumerate(targets):
                if t + R2 < h:
                    continue
                r = t % h
                if r <= R2 or h - r <= R2:
                    bits |= 1 << ti
            if bits:
                V[(i, j)] = bits
    if not V:
        return None

    def pc(x):
        return bin(x).count("1")
    best = None
    for (i, j), bits in V.items():
        tot = bits | V.get((i, i), 0) | V.get((j, j), 0)
        key = (pc(tot), cl[i] * cl[j])
        if best is None or key > best[0]:
            best = (key, i, j, tot)
    if best[0][0] < 3:
        return None
    _, i, j, cov = best
    B = [i] if i == j else [i, j]
    gains = [pc(cov)]
    while len(B) < 7:
        bc = None
        for c in range(m):
            if c in B:
                continue
            new = V.get((c, c), 0)
            for x in B:
                new |= V.get((min(c, x), max(c, x)), 0)
            g = pc(new & ~cov)
            if g >= 2:
                key = (g, cl[c])
                if bc is None or key > bc[0]:
                    bc = (key, c, new)
        if bc is None:
            break
        B.append(bc[1])
        cov |= bc[2]
        gains.append(bc[0][0])

    # 빼도 설명되는 목표가 줄지 않는 밑수는 뺀다 (배수, 허브 자체 등). 큰 것부터 시도
    def cover_of(Bs):
        c = 0
        for ii in range(len(Bs)):
            for jj in range(ii, len(Bs)):
                x, y = Bs[ii], Bs[jj]
                c |= V.get((min(x, y), max(x, y)), 0)
        return c
    for x in sorted(B, reverse=True):
        if len(B) <= 2:
            break
        rest = [y for y in B if y != x]
        lost = bin(cover_of(B) & ~cover_of(rest)).count("1")
        mult = any(cl[x] % cl[y] == 0 for y in rest)
        if lost == 0 or (mult and lost <= 1):
            B = rest
    cov = cover_of(B)
    bases = [cl[x] for x in B]
    if verbose:
        print("  후보", len(cl))
        for x in B:
            desc = []
            for y in B:
                bits = V.get((min(x, y), max(x, y)), 0)
                if bits:
                    desc.append("%d:%d" % (cl[y], pc(bits)))
            print("  밑수", cl[x], desc)
    return {"bases": bases, "gain": gains, "cov": pc(cov), "n": n, "covbits": cov}


def _load(mode):
    path = ROOT + "/data/" + ("practice_puzzles.csv" if mode == "practice" else "puzzles.csv")
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["id"]] = (json.loads(r["starting_values"]), json.loads(r["targets"]), r.get("family", ""))
    return out


def _one(args):
    pid, st, tg = args
    try:
        return pid, decode(pid, tg, st)
    except Exception as e:  # noqa
        import traceback
        traceback.print_exc()
        return pid, None


if __name__ == "__main__":
    arg = sys.argv[1]
    if arg in ("scored", "practice"):
        from multiprocessing import Pool
        procs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        P = _load(arg)
        t0 = time.time()
        out = {}
        with Pool(procs) as pool:
            for k, (pid, res) in enumerate(pool.imap_unordered(_one, [(pid, v[0], v[1]) for pid, v in sorted(P.items())], chunksize=2)):
                if res:
                    out[pid] = res
                if k % 50 == 49:
                    print(k + 1, "done", len(out), "decoded", "%.0fs" % (time.time() - t0), flush=True)
        with open(f"{HERE}/cache/dec2_{arg}.json", "w") as f:
            json.dump(out, f)
        print("퍼즐 %d개 중 해독 %d개, %.0fs" % (len(P), len(out), time.time() - t0))
        if arg == "practice":
            from collections import Counter
            c = Counter(P[pid][2] for pid in out)
            tot = Counter(v[2] for v in P.values())
            cov = Counter()
            nn = Counter()
            for pid, r in out.items():
                cov[P[pid][2]] += r["cov"]
            for pid, v in P.items():
                nn[v[2]] += len(v[1])
            print({k: "%d/%d 퍼즐, 목표 %d/%d" % (c[k], tot[k], cov[k], nn[k]) for k in tot})
    else:
        P = _load("practice" if arg.startswith("practice") else "scored")
        st, tg, fam = P[arg]
        t0 = time.time()
        res = decode(arg, tg, st, verbose=True)
        print(arg, fam, res, "%.2fs" % (time.time() - t0))
