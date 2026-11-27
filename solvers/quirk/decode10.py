"""2회차: 이미 해독된 퍼즐에도 완화 훑기(decode4: R = min(d/128, 4096), 적중 4개 이상)를 돌려, 아는 정수와 짝짓지 않는
새 정수를 찾는다. 후보는 decode8 과 같은 엄격한 기준(서로 다른 (k,a,b) 묶음 2개 이상을 새로 설명)으로만 받는다.
사용: decode10.py [--procs N] [--every K --offset I] out.json"""
import sys, json, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles
import decode4, decode8
P = load_puzzles('data/puzzles.csv')
def known():
    Q = {}
    for f in ('solvers/quirk/bases3f.json', 'solvers/quirk/bases6.json', 'solvers/relate/bases_export.json', 'solvers/quirk/bases8.json'):
        for k, v in json.load(open(f)).items(): Q.setdefault(k, []).extend(v['bases'])
    return Q
def scaled(c, B):
    return any(c * m == b or (c % m == 0 and c // m == b) or (b % m == 0 and b // m == c) for b in B for m in (1, 2, 3, 4, 5, 6, 7, 8))
def work(arg):
    pid, B0 = arg
    pz = P[pid]; T = sorted(t for t in set(pz.targets) if t >= 1 << 16)
    B = [b for b in dict.fromkeys(B0) if b >= 512]
    B4, _ = decode4.decode(pz.targets, 24)
    cands = [c for c in B4 if c >= 512 and not scaled(c, B)]
    cov = decode8.explain_strict(T, B); added = []
    for c in cands:
        cov2 = decode8.explain_strict(T, B + [c])
        grp = {v[:3] for t, v in cov2.items() if c in (v[1], v[2]) and t not in cov}
        if len(grp) >= 2: B.append(c); added.append(c); cov = cov2
    if added:
        B, more, cov = decode8.extend(pz.targets, B); added += more
    return pid, B, added, len(cov)
if __name__ == '__main__':
    a = sys.argv[1:]
    procs = int(a[a.index('--procs') + 1]) if '--procs' in a else 2
    ev = int(a[a.index('--every') + 1]) if '--every' in a else 1
    off = int(a[a.index('--offset') + 1]) if '--offset' in a else 0
    Q = known(); ids = sorted(Q)[off::ev]
    out = {}; n = 0
    with Pool(procs) as pool:
        for pid, B, added, c in pool.imap_unordered(work, [(p, Q[p]) for p in ids]):
            if added:
                n += len(added); out[pid] = {'bases': B, 'added': added, 'cov': {}, 'nt': c}
                print(pid, 'added', added, 'strict cov', c, flush=True)
    print('puzzles', len(ids), 'with additions', len(out), 'new ints', n)
    json.dump(out, open(a[-1], 'w'))
