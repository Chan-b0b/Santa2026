"""해독기 묶음: decode2(큰 정수, 2^24 까지 훑기 + 근사 제곱 + 몫의 공약수; 빈손이면 decode4 의 완화 훑기) 와 decode3(작은 정수, 쌍 훑기) 의 합집합.
사용: decode_any.py <id>"""
import sys, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
import decode2, decode3

def decode(targets, dmax_bits=24):
    T = sorted(t for t in set(targets) if t >= 1 << 16)
    if len(T) < 3: return [], {}
    B2, _ = decode2.decode(targets, dmax_bits)
    if not B2:
        import decode4
        B2, _ = decode4.decode(targets, dmax_bits)      # 엄격한 훑기가 빈손이면 완화 훑기
    B3, _ = decode3.decode(targets)
    B = list(B2) + [b for b in B3 if b not in B2]
    if not B: return [], {}
    cov = decode2.explain(T, B, rel_bits=13)
    used = collections.Counter()
    for k, a, b, r in cov.values(): used[a] += 1; used[b] += 1
    while True:
        keep = [b for b in B if used[b] >= 2]
        if len(keep) == len(B): break
        B = keep; cov = decode2.explain(T, B, rel_bits=13)
        used = collections.Counter()
        for k, a, b, r in cov.values(): used[a] += 1; used[b] += 1
    B.sort(key=lambda b: -used[b])
    return B, cov

if __name__ == '__main__':
    pid = sys.argv[1]
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]
    B, cov = decode(p.targets)
    print(pid, 'start', p.start, 'bases', B)
    for t in sorted(p.targets):
        if t in cov:
            k, d, d2, r = cov[t]; print(f'  {t} = {k}*{d}*{d2} {r:+d}')
        else: print(f'  {t} ?')
    print(f'explained {len(cov)}/{len(p.targets)}')
