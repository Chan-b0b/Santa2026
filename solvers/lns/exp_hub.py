"""실험: 여러 목표값이 명령 1~2개로 닿는 공통 값(허브) w 를 투표로 찾으면 얼마나 줄일 수 있는가.
현재 최선 프로그램의 값 전부를 재료(C)로 보고, 목표값 t 마다 t = w op c, t = w*c ± d, t = (w ± d)*c 꼴의 w 를 모은다."""
import sys, json, collections
sys.path.insert(0, 'solvers/lns'); sys.path.insert(0, 'core')
from verify import load_puzzles, read_submission
import lns
from chain_snap import Machine, Params
P = load_puzzles('data/puzzles.csv'); cells = read_submission('best/best.csv')

def analyze(pid, verbose=False):
    pz = P[pid]; s = lns.SSA(pz, json.loads(cells[pid])); L = pz.limit
    nodes = list(range(s.ns)) + s.order
    cons = collections.defaultdict(list)
    for n in s.order:
        cons[s.A[n]].append(n)
        if s.B[n] != s.A[n]: cons[s.B[n]].append(n)
    def forbidden(a):
        f = set(s.private(a)); st = [a]
        while st:
            x = st.pop()
            for c in cons[x]:
                if c not in f: f.add(c); st.append(c)
        f.add(a); return f
    forb = {t: forbidden(a) for t, a in s.req.items()}
    cone = {t: len(s.private(a)) for t, a in s.req.items()}
    cand = collections.defaultdict(dict)        # w -> {t: cost}
    allvals = set(s.val[x] for x in nodes)
    for t in s.req:
        ok = [x for x in nodes if x not in forb[t]]
        C = sorted(set(s.val[x] for x in ok)); Cs = set(C)
        def add(w, k):
            if w <= 0 or w > L or w == t or w in Cs: return
            d = cand[w]
            if t not in d or k < d[t]: d[t] = k
        for c in C:
            add(t - c, 1); add(t + c, 1); add(c - t, 1)
            if c >= 2:
                if t % c == 0: add(t // c, 1)
                add(t * c, 1)
            if c % t == 0: add(c // t, 1)
        for c in C:
            if c < 2 or c >= t: continue
            tc = t % c
            for d in C:
                dc = d % c
                if dc == tc and d < t: add((t - d) // c, 2)
                if (tc + dc) % c == 0: add((t + d) // c, 2)
            if tc == 0:
                q = t // c
                for d in C: add(q - d, 2); add(q + d, 2)
    hubs = []
    for w, d in cand.items():
        if len(d) < 2: continue
        save = sum(max(0, cone[t] - k) for t, k in d.items())
        if save >= 2: hubs.append((save, w, d))
    hubs.sort(reverse=True, key=lambda h: h[0])
    m = Machine(pz, Params(W=32, s1m=2, f2=0, near=1, maxcost=40))
    used = set(); total = 0; picked = []
    for save, w, d in hubs[:80]:
        dd = {t: k for t, k in d.items() if t not in used and cone[t] > k}
        sv = sum(cone[t] - k for t, k in dd.items())
        if sv < 2 or len(dd) < 2: continue
        def kcost(t, pool):
            """w 와 pool 값만으로 t 를 만드는 최소 명령 수 (1 또는 2), 없으면 None"""
            for c in pool:
                if t == w + c or t == w - c or t == c - w or t == w * c or (c and w % c == 0 and t == w // c) or (w and c % w == 0 and t == c // w): return 1
            for c in pool:
                if c < 2: continue
                r = t - w * c
                if r > 0 and r in pool: return 2
                if r < 0 and -r in pool: return 2
                if t % c == 0:
                    q = t // c
                    if (q > w and q - w in pool) or (w > q and w - q in pool): return 2
            return None
        for _ in range(3):                      # 서로를 재료로 쓰는 순환을 없앤다
            fb = set()
            for t in dd: fb |= forb[t]
            pool = set(s.val[x] for x in nodes if x not in fb)
            nd2 = {}
            for t in dd:
                k = kcost(t, pool)
                if k is not None and cone[t] > k: nd2[t] = k
            if len(nd2) == len(dd): dd = nd2; break
            dd = nd2
            if len(dd) < 2: break
        if len(dd) < 2: continue
        sv = sum(cone[t] - k for t, k in dd.items())
        if sv < 2: continue
        if w in pool: continue
        m.loc = dict.fromkeys(pool, 0); m.dirty = True
        st = m.find_chain(w, ub=sv)
        if st is None: continue
        gain = sv - len(st)
        if gain > 0:
            total += gain; used.update(dd); picked.append((gain, w, len(st), {t: (cone[t], k) for t, k in dd.items()}))
    print(f"{pid} 명령 {len(s.order)} 목표 {len(s.req)} 후보 {len(cand)} 공유 후보 {len(hubs)} 채택 {len(picked)} 예상 이득 {total} ({100.0*total/len(s.order):.1f}%)", flush=True)
    if verbose:
        for g in picked[:8]: print('   ', g)
    return len(s.order), total

tot = gain = 0
for pid in sys.argv[1:]:
    a, g = analyze(pid, verbose=len(sys.argv) <= 4); tot += a; gain += g
print('합계', tot, '예상 이득', gain, f'({100.0*gain/max(tot,1):.2f}%)')
