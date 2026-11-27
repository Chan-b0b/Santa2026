"""연분수로 목표값 쌍의 숨은 관계 찾기: q*t1 - p*t2 = r (작음).
점수 = log2(t2) - log2(q) - log2(|r|+1) - log2(p)  (무작위 쌍이면 대략 <= 0 근처)"""
import sys, math, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles

def relations(t1, t2, maxq=1 << 20):
    """t1 >= t2. 수렴분수 p/q ~ t1/t2 마다 (score, p, q, r) 를 낸다. r = q*t1 - p*t2."""
    out = []
    a, b = t1, t2
    p0, q0, p1, q1 = 0, 1, 1, 0
    while b:
        k = a // b
        p0, q0, p1, q1 = p1, q1, k * p1 + p0, k * q1 + q0
        a, b = b, a - k * b
        if q1 > maxq: break
        r = q1 * t1 - p1 * t2
        if r == 0:
            out.append((99.0, p1, q1, 0)); break
        sc = math.log2(t2) - math.log2(q1) - math.log2(abs(r) + 1) - math.log2(p1)
        out.append((sc, p1, q1, r))
    return out

if __name__ == '__main__':
    pid = sys.argv[1]; thr = float(sys.argv[2]) if len(sys.argv) > 2 else 6
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]; T = sorted(p.targets)
    print(pid, p.start, p.limit)
    deg = collections.Counter()
    for i in range(len(T)):
        for j in range(i):
            for sc, pp, q, r in relations(T[i], T[j]):
                if sc >= thr:
                    print(f'  {q}*{T[i]} - {pp}*{T[j]} = {r}   score {sc:.1f}')
                    deg[T[i]] += 1; deg[T[j]] += 1
    print('related targets', len(deg), '/', len(T))
    print('unrelated:', [t for t in T if t not in deg])
