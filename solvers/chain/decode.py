"""chain: 숨은 밑(base) 해독. basescan(C++) 결과를 걸러 씨앗 후보 목록을 만든다.
사용: decode.py <id> ...            (한 퍼즐씩 출력)
      decode.py --all [procs]        (채점 1,000개 -> solvers/chain/seeds.json)
두 가지 근거를 쓴다.
  (1) 통계: 서로 다른 허브 묶음 여러 개가 d 의 배수 ± 작은 값이다 (basescan 점수, 비트).
  (2) 쌍 검증(quirk 의 방법): 같은 (t, r) 에서 후보 d, d' 가 d*d' | t - r 이다 (t = k*a*b + r).
"""
import sys, os, subprocess, json, time, collections
from math import gcd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "core"))
from verify import load_puzzles

DMIN = 1 << 11
DMAX = 1 << 23
THR_OUT = 6.0     # basescan 이 내보내는 최소 점수
THR_STRONG = 14.0  # 1단계(쌍 검증)에 넣는 최소 점수
THR_STAT = 27.0    # 통계만으로 받아들이는 점수
THR_PAIR = 3       # 쌍 검증된 목표 수가 이 이상이면 받아들임


def clusters(T):
    """서로 작은 유리수 배(p/q, q <= 64) 관계에 있는 목표값을 한 묶음으로."""
    n = len(T)
    par = list(range(n))
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for i in range(n):
        a = T[i]
        cap = a >> 16
        for j in range(i + 1, n):
            b = T[j]            # a <= b
            for q in range(1, 65):
                p = (b * q + a // 2) // a
                if p > 1 << 16:
                    break
                if abs(b * q - p * a) <= min((p + q) << 13, cap):
                    par[find(i)] = find(j)
                    break
    ids = {}
    cl = [ids.setdefault(find(i), len(ids)) for i in range(n)]
    return cl, len(ids)


def scan(targets, dmin=DMIN, dmax=DMAX, thr=THR_OUT):
    T = sorted(set(t for t in targets if t >= 1 << 16))
    if len(T) < 4:
        return T, [], 0
    cl, nc = clusters(T)
    if nc < 2:
        return T, [], nc
    dmax = min(dmax, max(T) >> 5)
    inp = f"{len(T)} {nc} {dmin} {dmax} {thr}\n" + " ".join(map(str, T)) + "\n" + " ".join(map(str, cl)) + "\n"
    out = subprocess.run([os.path.join(HERE, "basescan")], input=inp, capture_output=True, text=True).stdout
    L = []
    for line in out.split("\n"):
        if line:
            f = line.split()
            hits = [(int(x.split(":")[0]), int(x.split(":")[1])) for x in f[4:]]
            L.append((float(f[1]), int(f[0]), int(f[2]), hits))
    L.sort(reverse=True)
    return T, L, nc


def decode(targets, kmax=7, verbose=False, thr_strong=THR_STRONG, thr_out=THR_OUT, dmin=DMIN):
    T, L, nc = scan(targets, dmin=dmin, thr=thr_strong)
    if not L:
        return []
    Lall = L
    # 1단계: 통계 점수가 높은 후보끼리 쌍 검증
    by = collections.defaultdict(list)
    for s, d, k, hits in L:
        for i, r in hits:
            by[(i, r)].append(d)
    pv = collections.defaultdict(set)      # d -> 쌍 검증된 목표 번호
    for (i, r), ds in by.items():
        N = T[i] - r
        ds.sort()
        for x in range(len(ds)):
            d = ds[x]
            if N % (d * d) == 0:
                pv[d].add(i)
            for y in range(x + 1, len(ds)):
                d2 = ds[y]
                if d2 % d == 0:
                    continue
                if N % (d * d2) == 0:
                    pv[d].add(i); pv[d2].add(i)
    hitmap = {d: dict(hits) for s, d, k, hits in Lall}
    info = {d: (s, k, len(hits)) for s, d, k, hits in Lall}
    cand = []
    for s, d, k, hits in L:
        npv = len(pv.get(d, ()))
        if s >= THR_STAT or npv >= THR_PAIR:
            cand.append((s + 12.0 * npv, d, npv))
    cand.sort(reverse=True)
    chosen = []                # (d, 점수, 묶음, 적중, 근거 수)
    explained = set()          # 고른 밑 둘(같은 것 포함)의 곱으로 설명된 목표 번호

    def related(d):
        # 이미 고른 값과 작은 유리수 배 관계(공약수가 큼)면 같은 밑의 변형이다
        return any(gcd(d, c[0]) * 16 >= min(d, c[0]) for c in chosen)

    def newsup(d):
        """고른 밑과 짝을 이뤄(또는 제곱으로) 새로 설명되는 목표 번호."""
        new = set()
        hd = hitmap[d]
        for i, r in hd.items():
            if i in explained:
                continue
            N = T[i] - r
            if N % (d * d) == 0:
                new.add(i); continue
            for c in chosen:
                if hitmap[c[0]].get(i) == r and N % (d * c[0]) == 0:
                    new.add(i); break
        return new

    def take(d, why):
        # d 의 약수(d/j)가 더 많은 목표에 적중하면 그쪽이 진짜 밑이다 (예: 2a 대신 a)
        bj = d
        for j in range(2, 13):
            if d % j == 0 and (d // j) in hitmap and len(hitmap[d // j]) > len(hitmap[bj]):
                bj = d // j
        d = bj
        s, k, h = info[d]
        new = newsup(d)
        chosen.append((d, round(s, 1), k, h, why))
        explained.update(new)
        # d 가 들어오면서 기존 밑과의 짝으로 설명되는 것도 newsup 에 들어 있다

    for key, d, npv in cand:
        if len(chosen) >= kmax:
            break
        if related(d):
            continue
        if chosen and len(newsup(d)) < 2:
            continue
        take(d, npv)
    # 2단계: 통계 점수는 낮아도, 이미 고른 밑과 짝을 이뤄 새 목표 3개 이상을 설명하는 후보
    if chosen:
        T, Lall, nc = scan(targets, dmin=dmin, thr=thr_out)
        for s, d, k, hits in Lall:
            if d not in hitmap:
                hitmap[d] = dict(hits); info[d] = (s, k, len(hits))
        by_all = collections.defaultdict(list)
        for s, d, k, hits in Lall:
            for i, r in hits:
                by_all[(i, r)].append(d)
        while len(chosen) < kmax:
            sup = collections.defaultdict(set)
            cs = [c[0] for c in chosen]
            for c in cs:
                for i, r in hitmap[c].items():
                    if i in explained:
                        continue
                    N = T[i] - r
                    for d in by_all.get((i, r), ()):
                        if d not in cs and N % (d * c) == 0:
                            sup[d].add(i)
            best = None
            for d, st in sup.items():
                n = len(st)
                if n >= 3 and (best is None or (n, d) > best) and not related(d):
                    best = (n, d)
            if best is None:
                break
            take(best[1], best[0])
    if verbose:
        print("   묶음", nc, "후보", len(Lall), "강한 후보", len(L), "최고", [(s, d, k, len(h)) for s, d, k, h in L[:5]])
    return chosen


def _work(pid_t):
    pid, targets = pid_t
    return pid, decode(targets)


def _work_weak(pid_t):
    """느슨한 해독: 문턱을 낮춘다. 틀린 후보가 섞이므로 반드시 what-if(넣고 풀어서 짧아질 때만 채택)로 걸러 쓴다."""
    pid, targets = pid_t
    return pid, decode(targets, thr_strong=6.0, thr_out=3.0, dmin=1 << 10)


if __name__ == "__main__":
    if sys.argv[1] in ("--all", "--weak"):
        import multiprocessing as mp
        P = load_puzzles(os.path.join(ROOT, "data", "puzzles.csv"))
        nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        t0 = time.time()
        res = {}
        weak = sys.argv[1] == "--weak"
        jobs = [(pid, p.targets) for pid, p in sorted(P.items())]
        outname = "seeds.json"
        if weak:      # 엄격한 해독에서 밑이 안 나온 퍼즐만
            strong = json.load(open(os.path.join(HERE, "seeds.json")))
            jobs = [j for j in jobs if not strong.get(j[0])]
            outname = "seeds_weak.json"
            if len(sys.argv) > 3:      # 지금 chain 결과의 길이/하한 비가 이 값 이하인 퍼즐만 (난수형 제외)
                from verify import read_submission
                maxratio = float(sys.argv[3])
                cur = {pid: len(json.loads(c)) for pid, c in read_submission(os.path.join(ROOT, "results", "chain.csv")).items()}
                jobs = [j for j in jobs if cur.get(j[0], 0) <= maxratio * max(1, P[j[0]].lower_bound) and P[j[0]].limit > 64]
        with mp.Pool(nproc) as pool:
            for k, (pid, ch) in enumerate(pool.imap_unordered(_work_weak if weak else _work, jobs, chunksize=4)):
                res[pid] = ch
                if (k + 1) % 100 == 0:
                    print(f"{k+1} 완료, 밑이 나온 퍼즐 {sum(1 for v in res.values() if v)}, {time.time()-t0:.0f}s", flush=True)
        tmp = os.path.join(HERE, outname + ".tmp")
        json.dump(res, open(tmp, "w"))
        os.replace(tmp, os.path.join(HERE, outname))
        print(f"끝: 밑이 나온 퍼즐 {sum(1 for v in res.values() if v)} / {len(res)}, {time.time()-t0:.0f}s")
    else:
        for pid in sys.argv[1:]:
            P = load_puzzles(os.path.join(ROOT, "data", "practice_puzzles.csv" if pid.startswith("practice") else "puzzles.csv"))
            t0 = time.time()
            ch = decode(P[pid].targets, verbose=True) if not os.environ.get("WEAK") else decode(P[pid].targets, verbose=True, thr_strong=6.0, thr_out=3.0, dmin=1 << 10)
            print(pid, f"{time.time()-t0:.1f}s", "선택 (d, 점수, 묶음, 적중, 쌍검증):", ch)


# ---- 목표값 설명: 밑이 정해진 뒤, 각 목표값을 k*(a*b) + r 또는 k2*(k1*(a*b) + e) + r 꼴로 풀어 필요한 작은 값(k, e, r)을 모은다 ----
def _divisors(k, lim=1 << 14):
    out = []
    d = 2
    while d * d <= k and d <= lim:
        if k % d == 0:
            out.append(d)
            if k // d != d:
                out.append(k // d)
        d += 1
    out.append(k)
    return out


def explain(targets, bases, rmax=8192, small=1 << 14):
    """(설명 목록, 필요한 작은 값 Counter). 설명: (t, a, b, k1, k2, e, r)  뜻: t = k2*(k1*a*b + e) + r"""
    T = sorted(set(targets))
    bs = sorted(set(bases))
    hubs = [(bs[i] * bs[j], bs[i], bs[j]) for i in range(len(bs)) for j in range(i, len(bs))]
    hubs += [(b, b, 1) for b in bs]          # 밑 하나만 쓰는 꼴 t = k*a + r 도 본다 (k 가 작을 때만)
    exps = []
    need = collections.Counter()
    for t in T:
        best = None
        for H, a, b in hubs:
            if H > t + rmax:
                continue
            k = (t + H // 2) // H
            if k < 1 or (b == 1 and k > small):
                continue
            rt = t - k * H
            cands = []
            if abs(rt) <= rmax:
                cands.append((k, 1, 0, rt))
            else:
                for k2 in _divisors(k):
                    e = (2 * rt + k2) // (2 * k2)          # 반올림
                    r = rt - k2 * e
                    if e != 0 and abs(e) <= rmax and abs(r) <= 256:
                        cands.append((k // k2, k2, e, r))
            for k1, k2, e, r in cands:
                vals = [v for v in (k1, k2, abs(e), abs(r)) if v > 1]
                if any(v > (1 << 22) for v in vals):
                    continue
                key = (len(vals) + (0 if b > 1 else 1), sum(v.bit_length() for v in vals))
                if best is None or key < best[0]:
                    best = (key, (t, a, b, k1, k2, e, r), vals)
        if best is not None:
            exps.append(best[1])
            for v in best[2]:
                if v <= small:
                    need[v] += 1
    return exps, need
