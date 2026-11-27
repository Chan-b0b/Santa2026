"""해독한 정수로 목표값을 k2*(m*a*b + r1) 로 설명해 찍는다. 사용: pypy3 -I explain.py <id> [bases,...]"""
import sys, json
sys.path.insert(0, '/home/maverick/Santa2026/core'); sys.path.insert(0, '/home/maverick/Santa2026/solvers/relate')
from verify import load_puzzles
import hubs

def explain(targets, B, tolden=4):
    """t -> (k2, m, a, b, r1) 가운데 |r1| 이 가장 작은 설명."""
    out = {}
    Bs = sorted(B)
    for t in targets:
        best = None
        for u in hubs.quotients(t) if t >= 1 << 16 else [t]:
            k2 = t // u
            for i, a in enumerate(Bs):
                for b in Bs[i:]:
                    h = a * b
                    if h > 2 * u: break
                    m = (2 * u + h) // (2 * h)
                    if m < 1: continue
                    r = u - m * h
                    if abs(r) * tolden <= a:
                        key = (abs(r) * k2, k2)
                        if best is None or key < best[0]: best = (key, (k2, m, a, b, r))
        if best: out[t] = best[1]
    return out

if __name__ == '__main__':
    pid = sys.argv[1]
    P = load_puzzles('/home/maverick/Santa2026/data/practice_puzzles.csv' if pid.startswith('practice') else '/home/maverick/Santa2026/data/puzzles.csv')
    pz = P[pid]
    if len(sys.argv) > 2: B = [int(x) for x in sys.argv[2].split(',')]
    else: B, info = hubs.decode(pz.targets); print(B, info)
    ex = explain(pz.targets, B)
    print(pid, 'start', pz.start)
    for t in pz.targets:
        if t in ex:
            k2, m, a, b, r = ex[t]; print(f'  {t} = {k2} * ({m} * {a}*{b} {r:+d})')
        else: print(f'  {t} ?')
