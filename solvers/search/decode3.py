"""숨은 밑수와 허브 해독 (basescan + partnerscan).

1. basescan (C++): d 를 2^11..2^23 까지 훑어 |t mod± d| <= 64 인 목표가 우연보다 뚜렷이 많은 d 를 씨앗 밑수로 삼는다.
2. partnerscan (C++): 씨앗 a 마다 x 를 2^9..2^23 까지 훑어 허브 h = a*x 의 지지 목표(|t - k*h| <= h >> 12)를 센다.
   허브 수준에서는 15~17비트 나머지도 작으므로, 나머지가 커서 basescan 이 놓친 밑수(짝)가 여기서 잡힌다.
3. 새로 찾은 짝을 씨앗으로 한 번 더 돈다.

사용: .venv/bin/python -I solvers/search/decode3.py [--procs 5] [--ids a,b]   -> solvers/search/decode3.json
"""
import sys, os, json, subprocess, time, math
sys.path.insert(0, "/home/maverick/Santa2026/core")
sys.path.insert(0, "/home/maverick/Santa2026/solvers/search")
from multiprocessing import Pool
from verify import load_puzzles
import hubs as hubmod

ROOT = '/home/maverick/Santa2026'
HERE = ROOT + '/solvers/search'
SH = 12


def load_scan(path=HERE + '/basescan_all.txt'):
    out = {}
    for line in open(path):
        parts = line.split()
        if parts:
            out[parts[0]] = [tuple(int(x) for x in p.split(':')) for p in parts[1:]]
    return out


def partner_scan(pid, seeds, T):
    inp = ''.join('%s %d %d %s\n' % (pid, a, len(T), ' '.join(map(str, T))) for a in seeds)
    res = subprocess.run([HERE + '/partnerscan', str(SH), '512', str(1 << 22), '3'], input=inp, capture_output=True, text=True)
    out = {}
    for line in res.stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        out[int(parts[1])] = [tuple(int(x) for x in p.split(':')) for p in parts[2:]]
    return out


def strip_small(x):
    for p in (2, 3, 5, 7):
        while x % p == 0 and x // p >= 4096:
            x //= p
    return x


def popcount(x):
    return bin(x).count('1')


def select(cands, seeds, n, maxhubs=30, minsig=4.0):
    """후보 (m, h, a, x, mask, q) 에서 허브를 고른다.

    유의도 sig = sum(bits(h) - bits(r_i)) - log2(C(n, m)) - 23 (x 를 2^23 개 훑으므로) 가 큰 것부터 고른다.
    지지 목표 수만 보면 우연히 3개가 맞는 x 가 씨앗당 4~5개 나오고, 진짜 허브에서 조금 어긋난 값이 이긴다.
    새로 설명하는 목표가 2개 이상일 때만 고른다 (같은 허브의 다른 표현, 배수, 이웃 값은 빠진다).
    """
    scored = []
    deg = {}
    for m, h, a, x, mask, q in cands:
        sig = m * h.bit_length() - q - math.log2(math.comb(n, m)) - 23
        if sig >= minsig:
            scored.append([sig, m, h, a, x, mask])
            deg.setdefault(x, set()).add(a)
    # 짝 x 가 여러 씨앗과 허브를 이루면 진짜 밑수일 가능성이 높다 (조금 어긋난 이웃 값은 한 씨앗에서만 나온다).
    for c in scored:
        c[0] += 5.0 * (len(deg[c[4]]) - 1)
    scored.sort(key=lambda c: (-c[0], -c[2]))
    covered = 0
    hubs = {}
    used = []
    for sig, m, h, a, x, mask in scored:
        if h in hubs:
            continue
        new = popcount(mask & ~covered)
        if new < 2:
            # 목표가 두 허브에 함께 속할 수 있다 (예: 17933*80879 와 8966*80879). 뚜렷하고 배수 관계가 아니면 받아 준다.
            if not (new >= 1 and sig >= 30 and not any(h % g == 0 or g % h == 0 for g in hubs)):
                continue
        covered |= mask
        hubs[h] = m
        used.append((a, x))
        if len(hubs) >= maxhubs:
            break
    return hubs, used


def decode(pid, T, scan, maxseed=6, rounds=2):
    """(밑수 목록, {허브: 지지 목표 수}) 를 돌려준다."""
    n = len(T)
    seeds = hubmod.scan_bases(scan, n, maxb=maxseed) if scan else []
    if not seeds:
        return [], {}
    cands = []      # (members, h, a, x, mask, qual)
    scanned = set()
    frontier = list(seeds)
    for rnd in range(rounds):
        frontier = [a for a in frontier if a not in scanned][:maxseed]
        if not frontier:
            break
        res = partner_scan(pid, frontier, T)
        scanned.update(frontier)
        for a in frontier:
            for x, m, mask, q in res.get(a, ()):
                cands.append((m, a * x, a, x, mask, q))
        if rnd + 1 < rounds:
            hubs, used = select(cands, seeds, n)
            new = []
            for a, x in used:
                # 짝 x 는 진짜 밑수의 작은 배수일 수 있다 (씨앗이 밑수의 약수일 때). 작은 소인수를 뗀 것도 다음 씨앗으로 쓴다.
                for y in (x, strip_small(x)):
                    if y >= 4096 and y not in scanned and y not in new and not any(s % y == 0 for s in scanned):
                        new.append(y)
            frontier = new
    hubs, used = select(cands, seeds, n)
    bcount = {}
    for a, x in used:
        bcount[a] = bcount.get(a, 0) + 1
        bcount[x] = bcount.get(x, 0) + 1
    bases = sorted(bcount, key=lambda b: (-bcount[b], b))[:12]
    # 밑수 쌍의 곱(제곱 포함) 가운데 목표 하나라도 빡빡하게(h >> 13) 지지하는 것을 허브에 더한다.
    extra = []
    for i, a in enumerate(bases):
        for b in bases[i:]:
            h = a * b
            if h in hubs or h > T[-1] * 2 or h < (1 << 20):
                continue
            ms = hubmod.members(h, T, 13)
            if ms:
                extra.append((-len(ms), h))
    extra.sort()
    for c, h in extra[:16]:
        hubs[h] = -c
    return sorted(bases), hubs


_P = None
_S = None


def work(pid):
    global _P, _S
    if _P is None:
        _P = load_puzzles(ROOT + '/data/puzzles.csv')
        _S = load_scan()
    pz = _P[pid]
    T = sorted(set(pz.targets) - set(pz.start))
    t0 = time.time()
    bases, hubs = decode(pid, T, _S.get(pid))
    return pid, bases, hubs, time.time() - t0


if __name__ == '__main__':
    args = sys.argv[1:]
    procs = 5
    ids = None
    i = 0
    while i < len(args):
        if args[i] == '--procs':
            procs = min(5, int(args[i + 1])); i += 2
        elif args[i] == '--ids':
            ids = args[i + 1].split(','); i += 2
        else:
            raise SystemExit('unknown arg')
    S = load_scan()
    if ids is None:
        ids = sorted(pid for pid, sc in S.items() if sc)
    out = {}
    path = HERE + '/decode3.json'
    if os.path.exists(path) and len(ids) < 900:
        out = json.load(open(path))
    t0 = time.time()
    done = 0
    with Pool(procs) as pool:
        for pid, bases, hubs, dt in pool.imap_unordered(work, ids, chunksize=2):
            done += 1
            out[pid] = {'bases': bases, 'hubs': {str(h): m for h, m in hubs.items()}}
            if len(ids) <= 10:
                print(pid, 'bases', bases, 'hubs', sorted(hubs.items()), '%.1fs' % dt)
            elif done % 50 == 0:
                print('  .. %d/%d %.0fs' % (done, len(ids), time.time() - t0), flush=True)
    tmp = path + '.tmp'
    json.dump(out, open(tmp, 'w'))
    os.replace(tmp, path)
    nb = sum(1 for v in out.values() if v['hubs'])
    print('decoded %d puzzles with hubs (of %d scanned), %.0fs' % (nb, len(ids), time.time() - t0))
