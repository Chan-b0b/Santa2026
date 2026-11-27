"""허브 충돌 + 약수쌍 닫힘으로 숨은 정수(밑수) 복원.

구조형 퍼즐의 목표값은 t = k*a*b + r (a, b: 숨은 정수, k, r: 작은 수) 꼴이다.
1) 허브 후보: 목표마다 h = (t - r) / k (k <= K, |r| <= R) 를 전부 모아, 서로 다른 목표 2개 이상이 같은 h 를 내면 후보로 둔다 (해시 충돌만 본다).
2) 후보 h 를 소인수분해해 약수쌍 (a, b), a*b = h 를 간선으로 둔다.
3) 닫힘 가지치기: 정수 x 는 '살아 있는 상대' 가운데 서로 나누지 않는 것이 2개 이상이고 그 간선들의 목표가 3개 이상일 때만 살아남는다.
4) 살아남은 정수를 덮는 목표 수 순으로 고른다.

사용: python hubcore.py <id>   또는  python hubcore.py scored|practice [procs]
결과: cache/hub_<mode>.json  {id: {"bases": [...], "hubs": [...], "cov": n}}
"""
import csv, json, sys, time
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


def hub_candidates(targets, K=64, R=128, hmin=1 << 14):
    cand = defaultdict(dict)
    for i, t in enumerate(targets):
        if t < hmin:
            continue
        Rt = min(R, t >> 9)
        for k in range(1, K + 1):
            lo = -((-(t - Rt)) // k)
            hi = (t + Rt) // k
            if hi < hmin:
                break
            for h in range(max(lo, hmin), hi + 1):
                cand[h][i] = (k, t - k * h)
    return {h: s for h, s in cand.items() if len(s) >= 2}


def decode(targets, start=(), K=64, R=128, amin=1 << 7, maxcand=5000, mint=3, verbose=False):
    cand = hub_candidates(targets, K, R)
    if not cand:
        return None
    if len(cand) > maxcand:
        # 지지 목표가 많은 것, 그다음 나머지 합이 작은 것부터
        ks = sorted(cand, key=lambda h: (-len(cand[h]), sum(abs(r) for _, r in cand[h].values())))[:maxcand]
        cand = {h: cand[h] for h in ks}
    edges = defaultdict(set)       # (a, b) -> 목표 인덱스 집합
    for h, sup in cand.items():
        ds = divisors(factor(h))
        ts = set(sup)
        for a in ds:
            if a < amin or a * a > h:
                continue
            edges[(a, h // a)] |= ts
    nbr = defaultdict(dict)        # x -> {y: 목표 집합}
    for (a, b), ts in edges.items():
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
            if len(tg) < mint:
                dead.append(x)
                continue
            # 서로 나누지 않는 상대가 2개 이상
            ps.sort()
            ok = False
            for i in range(len(ps)):
                for j in range(i + 1, len(ps)):
                    if ps[j] % ps[i]:
                        ok = True
                        break
                if ok:
                    break
            if not ok:
                dead.append(x)
        if not dead:
            break
        alive.difference_update(dead)
    if not alive:
        return None
    cover = {}
    for x in alive:
        tg = set()
        for y, ts in nbr[x].items():
            if y in alive:
                tg |= ts
        cover[x] = tg
    order = sorted(alive, key=lambda x: (-len(cover[x]), -x))
    tset = set(targets) | set(start)
    bases = []
    for x in order:
        if x in tset:
            continue
        red = False
        for y in bases:
            if (x % y == 0 or y % x == 0) and cover[x] <= cover[y]:
                red = True
                break
        if red:
            continue
        bases.append(x)
        if len(bases) >= 8:
            break
    allcov = set()
    for x in bases:
        allcov |= cover[x]
    hubs = sorted({a * b for (a, b) in edges if a in alive and b in alive and a in bases and b in bases})
    if verbose:
        for x in bases:
            print("  base", x, "targets", len(cover[x]), "partners", sorted(y for y in nbr[x] if y in alive)[:8])
    return {"bases": bases, "cnt": [len(cover[x]) for x in bases], "hubs": hubs[:12], "cov": len(allcov), "alive": len(alive)}


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
        return pid, decode(tg, st)
    except Exception as e:  # noqa
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
            for k, (pid, res) in enumerate(pool.imap_unordered(_one, [(pid, v[0], v[1]) for pid, v in sorted(P.items())], chunksize=4)):
                if res:
                    out[pid] = res
                if k % 100 == 99:
                    print(k + 1, "done", len(out), "decoded", "%.0fs" % (time.time() - t0), flush=True)
        with open(f"{HERE}/cache/hub_{arg}.json", "w") as f:
            json.dump(out, f)
        print("퍼즐 %d개 중 해독 %d개, %.0fs" % (len(P), len(out), time.time() - t0))
        if arg == "practice":
            from collections import Counter
            c = Counter(P[pid][2] for pid in out)
            tot = Counter(v[2] for v in P.values())
            print({k: "%d/%d" % (c[k], tot[k]) for k in tot})
    else:
        P = _load("practice" if arg.startswith("practice") else "scored")
        st, tg, fam = P[arg]
        t0 = time.time()
        res = decode(tg, st, verbose=True)
        print(arg, fam, res, "%.2fs" % (time.time() - t0))
