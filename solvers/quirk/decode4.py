"""완화 해독: 엄격한 훑기(decode.py)가 아무것도 못 찾은 퍼즐에 쓴다.
R(d) = min(d >> 7, 4096), 적중 4개 이상인 d 를 후보로 하고 나머지 단계는 decode/decode2 와 같다.
사용: decode4.py <id> [shift] [cap] [hmin]"""
import sys, subprocess, os, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
import decode as d1, decode2 as d2
HERE = os.path.dirname(os.path.abspath(__file__))

def make_scan(shift, cap, hmin):
    def scan(targets, dmax, _h=3):
        inp = f"{len(targets)} {dmax} {hmin} {shift} {cap}\n" + " ".join(map(str, targets)) + "\n"
        out = subprocess.run([os.path.join(HERE, 'basescan2')], input=inp, capture_output=True, text=True).stdout
        cands = {}
        for line in out.split('\n'):
            if not line: continue
            f = line.split()
            cands[int(f[0])] = {targets[i]: int(x) for i, x in enumerate(f[2:]) if x != 'x'}
        return cands
    return scan

def decode(targets, dmax_bits=24, shift=7, cap=4096, hmin=4):
    orig = d1.scan
    d1.scan = make_scan(shift, cap, hmin)
    try:
        B, cov = d2.decode(targets, dmax_bits)
    finally:
        d1.scan = orig
    return B, cov

if __name__ == '__main__':
    pid = sys.argv[1]
    a = [int(x) for x in sys.argv[2:5]] + [7, 4096, 4][len(sys.argv) - 2:]
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]
    B, cov = decode(p.targets, 24, *a)
    print(pid, 'start', p.start, 'bases', B)
    for t in sorted(p.targets):
        if t in cov:
            k, d, dd, r = cov[t]; print(f'  {t} = {k}*{d}*{dd} {r:+d}')
    print(f'explained {len(cov)}/{len(p.targets)}')
