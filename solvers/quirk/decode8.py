"""기상천외 1회차: 몫 공약수로 빠진 정수 찾기 (절대 오프셋 기준).
decode2.expand_once 는 |r| <= a/128 만 봐서, 오프셋이 절대값으로 수천인 t = a*c + r (r 이 a 에 비해 큼) 을 놓친다.
예: practice_0145 의 3858987186 = 70932*54404 + 2658, 27655787728 = 508341*54404 + 3964.
여기서는 이미 아는 정수 a (와 허브 a*b) 로 t 를 나눈 몫 q = round(t/a) 를 |r| <= R(절대) 일 때 모으고,
서로 다른 목표의 몫끼리 gcd 가 큰 것을 새 정수 후보로 삼아 explain 으로 검증한다.
사용: decode8.py [--ctrl] [--procs N] out.json"""
import sys, json, math, collections, random
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
import decode2

R_ABS = 16384

def items_for(T, B, cov):
    out = []
    H = set()
    for i, a in enumerate(B):
        for b in B[i:]:
            if a * b >= 1 << 20: H.add(a * b)
    for t in T:
        if t in cov: continue
        for d in list(B) + sorted(H):
            if d * 256 > t: continue
            m = t % d; r = m if 2 * m <= d else m - d
            if abs(r) <= R_ABS: out.append(((t - r) // d, t, d, r))
    return out

def candidates(T, B, cov, gmin=1024):
    it = items_for(T, B, cov)
    votes = collections.defaultdict(set)
    for i in range(len(it)):
        qi, ti = it[i][0], it[i][1]
        for j in range(i):
            qj, tj = it[j][0], it[j][1]
            if ti == tj: continue
            g = math.gcd(qi, qj)
            if g < gmin: continue
            # gcd 에 섞인 작은 공통 인수(k 의 공약수)를 떼어 본다
            for s in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12):
                if g % s == 0 and g // s >= gmin and g // s not in B:
                    votes[g // s].add(ti); votes[g // s].add(tj)
    return sorted(votes, key=lambda x: (-len(votes[x]), -x))[:60], votes

def explain_strict(T, B, rabs=8192, kmax=1 << 17, hmin=1 << 24, rel=16):
    """검증용 엄격한 설명: |r| <= rabs (절대), k <= kmax. 우연히 맞을 확률이 허브 2^32 에서 2^-18 정도다."""
    cov = {}
    Bs = sorted(B)
    for t in T:
        best = None
        for i, a in enumerate(Bs):
            for b in Bs[i:]:
                h = a * b
                if h > 2 * t: break
                if h < hmin: continue
                k = (t + h // 2) // h
                if k < 1 or k > kmax: continue
                r = t - k * h
                if abs(r) <= rabs and abs(r) <= h >> rel:
                    sc = math.log2(h) - math.log2(2 * abs(r) + 1) - math.log2(k)
                    if best is None or sc > best[0]: best = (sc, (k, a, b, r))
        if best: cov[t] = best[1]
    return cov

def extend(targets, B0, rounds=6, verbose=False):
    T = sorted(t for t in set(targets) if t >= 1 << 16)
    B = [b for b in dict.fromkeys(B0) if b >= 512]
    cov = explain_strict(T, B)
    added = []
    for _ in range(rounds):
        cands, votes = candidates(T, B, cov)
        best = None
        for c in cands:
            if len(votes[c]) < 2: break
            cov2 = explain_strict(T, B + [c])
            # 거의 같은 목표 쌍(차이가 작음)은 c 하나로 늘 함께 설명되므로, 서로 다른 (k, a, b) 묶음 수로 센다
            grp = {(v[0], v[1], v[2]) for t, v in cov2.items() if c in (v[1], v[2]) and t not in cov}
            use = len({(v[0], v[1], v[2]) for v in cov2.values() if c in (v[1], v[2])})
            gain = len(grp)
            if use >= 2 and gain >= 2:
                key = (gain, use, c)
                if best is None or key > best[0]: best = (key, c, cov2)
        if best is None: break
        B.append(best[1]); added.append(best[1]); cov = best[2]
        if verbose: print('  add', best[1], 'gain', best[0][0], 'cov', len(cov), flush=True)
    return B, added, cov

def work(arg):
    pid, targets, B0 = arg
    T = sorted(t for t in set(targets) if t >= 1 << 16)
    c0 = len(decode2.explain(T, [b for b in B0 if b >= 512]))
    B, added, cov = extend(targets, B0)
    return pid, B, added, c0, len(decode2.explain(T, B)), len(T)

if __name__ == '__main__':
    from multiprocessing import Pool
    args = sys.argv[1:]
    ctrl = '--ctrl' in args
    procs = int(args[args.index('--procs') + 1]) if '--procs' in args else 8
    only = args[args.index('--ids') + 1].split(',') if '--ids' in args else None
    out = args[-1]
    P = load_puzzles('data/puzzles.csv')
    Q = {}
    for f in ('solvers/quirk/bases3f.json', 'solvers/quirk/bases6.json', 'solvers/relate/bases_export.json'):
        for k, v in json.load(open(f)).items(): Q.setdefault(k, []).extend(v['bases'])
    pids = sorted(Q) if only is None else only
    if '--null' in args:   # 무작위형 퍼즐(독립)에 다른 퍼즐의 정수를 넣는다
        C = json.load(open(args[args.index('--null') + 1]))
        rnd = random.Random(11); keys = sorted(Q)
        jobs = [(p, P[p].targets, Q[rnd.choice(keys)]) for p in sorted(P) if C[p][0] == 'indep']
    elif ctrl:   # 대조군: 다른 퍼즐의 정수를 넣는다 (같은 크기대)
        rnd = random.Random(7); keys = sorted(Q)
        jobs = [(p, P[p].targets, Q[rnd.choice([k for k in keys if k != p])]) for p in pids]
    if not ctrl and '--null' not in args:
        jobs = [(p, P[p].targets, Q[p]) for p in pids]
    res = {}
    tot0 = tot1 = nadd = npz = 0
    with Pool(procs) as pool:
        for pid, B, added, c0, c1, nt in pool.imap_unordered(work, jobs):
            tot0 += c0; tot1 += c1
            if added:
                nadd += len(added); npz += 1
                print(pid, 'added', added, 'cov', c0, '->', c1, '/', nt, flush=True)
            res[pid] = {'bases': B, 'added': added, 'c0': c0, 'c1': c1, 'nt': nt}
    print('puzzles', len(jobs), 'with additions', npz, 'new ints', nadd, 'explained', tot0, '->', tot1)
    json.dump(res, open(out, 'w'))
