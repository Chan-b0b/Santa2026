"""숨은 정수(base) 해독. 목표값이 k*a*b + r (a, b 는 숨은 정수, r 은 작음) 꼴인 퍼즐에서 a, b 를 복원한다.
  1단계: basescan (C++) 으로 d | (t - r), |r| 작음 인 d 후보를 모은다.
  2단계: 같은 (t, r) 에서 d*d' | (t - r) 인 후보 쌍만 남긴다 (우연 확률이 사실상 0).
  3단계: 목표값을 가장 많이 설명하는 base 집합을 탐욕적으로 고른다.
사용: decode.py <id> [dmax_bits]"""
import sys, subprocess, collections, math, os
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
HERE = os.path.dirname(os.path.abspath(__file__))

def scan(targets, dmax, hmin=3):
    inp = f"{len(targets)} {dmax} {hmin}\n" + " ".join(map(str, targets)) + "\n"
    out = subprocess.run([os.path.join(HERE, 'basescan')], input=inp, capture_output=True, text=True).stdout
    cands = {}
    for line in out.split('\n'):
        if not line: continue
        f = line.split()
        d = int(f[0])
        cands[d] = {targets[i]: int(x) for i, x in enumerate(f[2:]) if x != 'x'}
    return cands

def decode(targets, dmax_bits=24, verbose=False):
    T = sorted(set(targets))
    big = [t for t in T if t >= 1 << 16]
    if len(big) < 3: return [], {}
    dmax = min(1 << dmax_bits, max(big) // 4)
    cands = scan(big, dmax)
    # (t, r) -> 그 수를 나누는 후보 d 들
    by = collections.defaultdict(list)
    for d, hits in cands.items():
        for t, r in hits.items(): by[(t, r)].append(d)
    # 쌍 설명: d*d' | t - r
    expl = collections.defaultdict(list)     # t -> [(k, d, d', r)]
    for (t, r), ds in by.items():
        N = t - r; ds.sort()
        for i, d in enumerate(ds):
            if N % (d * d) == 0: expl[t].append((N // (d * d), d, d, r))
            for d2 in ds[i + 1:]:
                if N % (d * d2) == 0: expl[t].append((N // (d * d2), d, d2, r))
    # 탐욕 선택
    use = collections.defaultdict(set)      # d -> 설명에 등장하는 목표
    for t, lst in expl.items():
        for k, d, d2, r in lst: use[d].add(t); use[d2].add(t)
    B = []; covered = {}
    def cover_with(Bset):
        cov = {}
        for t, lst in expl.items():
            best = None
            for k, d, d2, r in lst:
                if d in Bset and d2 in Bset:
                    key = (k, abs(r))
                    if best is None or key < best[0]: best = (key, (k, d, d2, r))
            if best: cov[t] = best[1]
        return cov
    pool = sorted(use, key=lambda d: (-len(use[d]), -d))[:400]
    # 첫 단계는 쌍으로 고른다: 정수 하나만으로는 제곱 꼴 목표만 설명되므로, 제곱이 없는 퍼즐에서 시작을 못 한다.
    pairs = collections.defaultdict(set)
    for t, lst in expl.items():
        for k, d, d2, r in lst: pairs[(d, d2)].add(t)
    if pairs:
        d, d2 = max(pairs, key=lambda q: (len(cover_with({q[0], q[1]})), q[0] * q[1]))
        B = [d] if d == d2 else [d, d2]
        covered = cover_with(set(B))
        if len(covered) < 2:            # 한 쌍이 목표 하나만 설명하면 우연일 수 있다 (independent 퍼즐에서 오검출)
            return [], {}
    while True:
        bestd = None
        for d in pool:
            if d in B: continue
            cov = cover_with(set(B) | {d})
            # 점수: 새로 설명되는 목표 수, 동점이면 k 합이 작은 쪽(큰 d)
            gain = len(cov) - len(covered)
            ksum = sum(math.log2(v[0]) for v in cov.values())
            key = (gain, -ksum)
            if bestd is None or key > bestd[0]: bestd = (key, d, cov)
        if bestd is None: break
        need = 1 if B else 2
        if bestd[0][0] < need:
            # 기존 설명의 k 를 줄이는 것만으로는 추가하지 않는다
            break
        B.append(bestd[1]); covered = bestd[2]
    # 설명에 두 번 이상 쓰이는 정수만 남긴다
    while True:
        used = collections.Counter()
        for k, d, d2, r in covered.values():
            used[d] += 1
            if d2 != d: used[d2] += 1
        keep = [b for b in B if used[b] >= 2]
        if len(keep) == len(B): break
        B = keep; covered = cover_with(set(B))
    return B, covered

if __name__ == '__main__':
    pid = sys.argv[1]; bits = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]
    B, cov = decode(p.targets, bits)
    print(pid, 'start', p.start, 'bases', B)
    for t in sorted(p.targets):
        if t in cov:
            k, d, d2, r = cov[t]; print(f'  {t} = {k}*{d}*{d2} {r:+d}')
        else: print(f'  {t} ?')
    print(f'explained {len(cov)}/{len(p.targets)}')
