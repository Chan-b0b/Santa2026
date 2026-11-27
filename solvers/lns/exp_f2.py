"""실험: 큰 풀에서 명령 2개짜리 끝점 표(F2)를 쓰면 무작위 목표값의 사슬이 얼마나 짧아지는가.
풀 = 한 퍼즐의 최종 프로그램이 만든 값 전부(이상적인 경우). 목표값 = 같은 크기의 새 난수."""
import sys, json, time, random
sys.path.insert(0, 'solvers/lns'); sys.path.insert(0, 'core')
from bisect import bisect_right
from verify import load_puzzles, read_submission
import lns
from chain_snap import Machine, Params

pid = sys.argv[1] if len(sys.argv) > 1 else 'scored_0001'
F2MAX = 1 << int(sys.argv[2]) if len(sys.argv) > 2 else 1 << 28
P = load_puzzles('data/puzzles.csv'); cells = read_submission('best/best.csv')
pz = P[pid]; s = lns.SSA(pz, json.loads(cells[pid]))
pool = sorted(set(s.val[x] for x in list(range(s.ns)) + s.order))
print(pid, 'pool', len(pool), 'small<8192:', sum(1 for v in pool if v < 8192), 'mid<2^26:', sum(1 for v in pool if 8192 <= v < 1 << 26))

class M2(Machine):
    def rebuild(self):
        f2 = self.pr.f2; self.pr.f2 = 0
        Machine.rebuild(self)
        self.pr.f2 = f2
        if f2:
            t0 = time.time(); F2 = {}; S1k = self.S1sorted; vals = self.vals
            for p in vals:
                for x in S1k:
                    v = x + p
                    if v <= F2MAX: F2[v] = x
                    else: break
                if p > 1:
                    for x in S1k:
                        v = x * p
                        if v <= F2MAX: F2[v] = x
                        else: break
                i = bisect_right(S1k, p)
                for x in S1k[:i]:
                    if p - x <= F2MAX: F2[p - x] = x
                for x in S1k[i:]:
                    v = x - p
                    if v <= F2MAX: F2[v] = x
                    else: break
            F2.pop(0, None)
            for v in list(self.S1): F2.pop(v, None)
            for v in vals: F2.pop(v, None)
            self.F2 = F2
            print(f'  F2 {len(F2)} values <= 2^{F2MAX.bit_length()-1}, S1 {len(self.S1)}, {time.time()-t0:.0f}s', flush=True)

random.seed(7)
lo, hi = min(pz.targets), max(pz.targets)
tests = [random.randrange(lo, hi) for _ in range(40)]
for cfg in (dict(W=32, f2=0), dict(W=200, f2=0), dict(W=32, f2=1), dict(W=200, f2=1)):
    m = M2(pz, Params(s1m=2, near=1, maxcost=60, **cfg))
    m.loc = dict.fromkeys(pool, 0); m.dirty = True
    t0 = time.time(); costs = []
    for t in tests:
        st = m.find_chain(t)
        costs.append(len(st) if st is not None else 99)
    from collections import Counter
    print(cfg, 'avg', sum(costs) / len(costs), sorted(Counter(costs).items()), f'{time.time()-t0:.0f}s', flush=True)
