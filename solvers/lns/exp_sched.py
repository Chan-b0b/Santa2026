"""실험: 그래프는 그대로 두고 실행 순서만 바꾸면 레지스터 압박이 얼마나 줄어드는가."""
import sys, json, random, heapq
sys.path.insert(0, 'solvers/lns'); sys.path.insert(0, 'core')
from verify import load_puzzles, read_submission
import lns
P = load_puzzles('data/puzzles.csv'); cells = read_submission('best/best.csv')

def measure(s, order):
    """(최대 동시 생존 수, 생존 수 합, 47 이상인 시점 수). 명령 T 실행 때 결과까지 포함해 필요한 레지스터 수."""
    lu = {}
    for T, n in enumerate(order):
        lu[s.A[n]] = T; lu[s.B[n]] = T
    live = sum(1 for i in range(s.ns) if i in lu)
    peak = area = hot = 0
    for T, n in enumerate(order):
        a, b = s.A[n], s.B[n]
        if lu[a] == T: live -= 1
        if b != a and lu[b] == T: live -= 1
        need = live + 1
        peak = max(peak, need); area += need; hot += need >= 47
        if n in lu: live += 1
    return peak, area, hot

def kahn(s, order, prio):
    cons = {}; indeg = {}
    for n in order:
        d = 0
        for x in {s.A[n], s.B[n]}:
            if x >= s.ns: d += 1; cons.setdefault(x, []).append(n)
        indeg[n] = d
    h = [(prio[n], n) for n in order if indeg[n] == 0]; heapq.heapify(h); out = []
    while h:
        _, n = heapq.heappop(h); out.append(n)
        for c in cons.get(n, ()):
            indeg[c] -= 1
            if indeg[c] == 0: heapq.heappush(h, (prio[c], c))
    return out

def jit(s, order, torder):
    done = set(range(s.ns)); out = []
    def emit(n):
        if n in done: return
        for x in (s.A[n], s.B[n]): emit(x)
        done.add(n); out.append(n)
    sys.setrecursionlimit(10000)
    for n in torder: emit(n)
    return out

for pid in sys.argv[1:]:
    pz = P[pid]; s = lns.SSA(pz, json.loads(cells[pid])); order = list(s.order)
    base = measure(s, order)
    req = set(s.req.values()); pos = {n: i for i, n in enumerate(order)}
    used = set(); [used.update((s.A[n], s.B[n])) for n in order]
    sinks = [n for n in order if n not in used]
    j = jit(s, order, sorted(sinks, key=pos.get))
    res = {'원래': base, 'JIT': measure(s, j) if len(j) == len(order) else None}
    random.seed(1)
    best = dict(pos); bm = base; cur = list(order)
    for it in range(4000):
        pr = dict(best)
        k = random.choice(order); pr[k] = pr[k] + random.gauss(0, 30)
        o = kahn(s, order, pr); m = measure(s, o)
        if (m[0] <= 48) and (m[1], m[2]) <= (bm[1], bm[2]):
            bm = m; best = {n: i for i, n in enumerate(o)}
    res['순서 탐색'] = bm
    print(pid, 'N', len(order), res)
