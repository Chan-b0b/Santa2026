"""시험(기상천외 1회차): 아는 정수 없이 decode8 의 몫 공약수를 쓰는 훑기. d 를 [2^13, 2^17] 에서 전부 보고,
|t mod d| <= 2048 인 목표의 몫 q 끼리 gcd >= 1024 이면 (d, c) 쌍 후보. 엄격한 설명으로 서로 다른 묶음 3개 이상이면 받고
decode8.extend 로 넓힌다. 사용: pairscan8.py <id> ..."""
import sys, math, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
import decode8

def scan(targets, lo=1 << 13, hi=1 << 17, R=2048):
    T = sorted(t for t in set(targets) if t >= 1 << 24)
    cands = collections.Counter()
    for d in range(lo, hi):
        it = []
        for t in T:
            m = t % d
            r = m if 2 * m <= d else m - d
            if -R <= r <= R: it.append(((t - r) // d, t))
        for i in range(len(it)):
            for j in range(i):
                g = math.gcd(it[i][0], it[j][0])
                if g >= 1024:
                    for s in (1, 2, 3, 4, 6):
                        if g % s == 0 and g // s >= 1024: cands[(d, g // s)] += 1
    return T, cands

def run(pz):
    T, cands = scan(pz.targets)
    good = []
    for (d, c), n in cands.most_common(400):
        cov = decode8.explain_strict(T, [d, c])
        grp = {v[:3] for v in cov.values()}
        if len(grp) >= 3: good.append((len(grp), d, c))
    good.sort(reverse=True)
    if not good: return [], 0
    B = [good[0][1], good[0][2]]
    for g, d, c in good[1:6]:
        for x in (d, c):
            if x not in B: B.append(x)
    B, added, cov = decode8.extend(pz.targets, B)
    return B, len({v[:3] for v in cov.values()})

if __name__ == '__main__':
    import time
    for pid in sys.argv[1:]:
        P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
        t0 = time.time(); B, n = run(P[pid])
        print(pid, 'bases', B, 'strict groups', n, '/', len(P[pid].targets), '%.0fs' % (time.time() - t0), flush=True)
