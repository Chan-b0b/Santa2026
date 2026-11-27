"""작은 숨은 정수 해독: pairscan 으로 (t, k, a, b, r) 를 모두 모은 뒤, 서로를 받쳐 주는 정수만 남긴다(반복 가지치기).
사용: decode3.py <id> [K] [R]"""
import sys, subprocess, collections, math, os
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
from decode2 import explain
HERE = os.path.dirname(os.path.abspath(__file__))

def incidences(T, K=8, R=128, amin=256, amax=1 << 20):
    inp = f"{len(T)} {K} {R} {amin} {amax}\n" + " ".join(map(str, T)) + "\n"
    out = subprocess.run([os.path.join(HERE, 'pairscan')], input=inp, capture_output=True, text=True).stdout
    inc = []
    for line in out.split('\n'):
        if not line: continue
        i, k, a, b, r = map(int, line.split())
        inc.append((T[i], k, a, b, r))
    return inc

def core(inc, mint=3):
    """정수 x 가 살아남으려면: 살아 있는 상대와의 설명이 서로 다른 목표 mint 개 이상에 걸쳐 있어야 한다."""
    alive = None
    cur = inc
    for _ in range(30):
        tg = collections.defaultdict(set)
        for t, k, a, b, r in cur:
            tg[a].add(t); tg[b].add(t)
        S = {x for x, ts in tg.items() if len(ts) >= mint}
        nxt = [e for e in cur if e[2] in S and e[3] in S]
        if len(nxt) == len(cur): break
        cur = nxt
    return cur

def decode(targets, K=8, R=128, mint=3):
    T = sorted(t for t in set(targets) if t >= 1 << 18)
    if len(T) < 4: return [], {}
    inc = incidences(T, K, R)
    cur = core(inc, mint)
    tg = collections.defaultdict(set)
    for t, k, a, b, r in cur: tg[a].add(t); tg[b].add(t)
    cand = sorted(tg, key=lambda x: (-len(tg[x]), -x))[:60]
    # 탐욕: 설명되는 목표 수를 가장 많이 늘리는 정수부터
    B = []; cov = {}
    # 첫 단계는 쌍으로 고른다 (정수 하나로는 제곱만 설명되기 때문)
    best = None
    for i, d in enumerate(cand):
        for e in cand[i + 1:]:
            c2 = explain(T, [d, e], rel_bits=14)
            key = (len(c2), d * e)
            if best is None or key > best[0]: best = (key, [d, e], c2)
    if best is None or best[0][0] < 3: return [], {}
    B = best[1]; cov = best[2]
    while True:
        best = None
        for d in cand:
            if d in B: continue
            c2 = explain(T, B + [d], rel_bits=14)
            key = (len(c2) - len(cov), d)
            if best is None or key > best[0]: best = (key, d, c2)
        if best is None or best[0][0] < (2 if not B else 2): break
        B.append(best[1]); cov = best[2]
    return B, cov

if __name__ == '__main__':
    pid = sys.argv[1]
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    R = int(sys.argv[3]) if len(sys.argv) > 3 else 128
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]
    B, cov = decode(p.targets, K, R)
    print(pid, 'start', p.start, 'bases', B)
    for t in sorted(p.targets):
        if t in cov:
            k, d, d2, r = cov[t]; print(f'  {t} = {k}*{d}*{d2} {r:+d}')
        else: print(f'  {t} ?')
    print(f'explained {len(cov)}/{len(p.targets)}')
