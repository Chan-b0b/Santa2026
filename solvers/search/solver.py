"""search 접근법 본체: 풀 기반 양방향 탐색 + 작은 값 표(S) + 근사 분해 fallback.

용어
  풀(pool)  : 지금 레지스터에 들어 있는 값들 (최대 48개, LRU 축출, 시작값은 고정).
  F1        : 풀의 두 값으로 명령 1개에 만들 수 있는 값 (value -> (op, x, y)).
  S         : 시작값만으로 트리 비용 k 이하에 만들 수 있는 값 표 (정적).
  C         : value -> 지금 추가로 드는 명령 수 (풀 0, F1 1, S 는 트리 비용).
탐색
  cheap(t)  : t = u op p (p 는 풀, u 는 C) 또는 t = q*p ± r (q, r 는 C). 풀에서 역방향 1단계.
  deep(t)   : t = u op w (w 는 F1, u 는 C). 역방향 1단계를 F1 까지 넓힌 것.
  plan(t)   : 위가 실패하면 가까운 값(덧셈 근사)이나 q*x±r 분해로 잔차를 줄여 가며 재귀.
"""
import sys
import time
import bisect

sys.path.insert(0, "/home/maverick/Santa2026/solvers/search")
import nt

sys.path.insert(0, "/home/maverick/Santa2026/core")
sys.setrecursionlimit(10000)


def build_small(starts, limit, max_entries=60000, max_level=8):
    """시작값에서 트리 비용 k 이하로 만들 수 있는 값 표. (cost, how, levels)"""
    cost = {s: 0 for s in starts}
    how = {}
    levels = [sorted(set(starts))]
    for k in range(1, max_level + 1):
        new = {}
        full = False
        for i in range(0, (k - 1) // 2 + 1):
            j = k - 1 - i
            A = levels[i]
            B = levels[j]
            for x in A:
                for y in B:
                    s = x + y
                    if s <= limit and s not in cost and s not in new:
                        new[s] = ('+', x, y)
                    if x > y:
                        d = x - y
                        if d not in cost and d not in new:
                            new[d] = ('-', x, y)
                        if x % y == 0:
                            q = x // y
                            if q not in cost and q not in new:
                                new[q] = ('/', x, y)
                    elif y > x:
                        d = y - x
                        if d not in cost and d not in new:
                            new[d] = ('-', y, x)
                        if y % x == 0:
                            q = y // x
                            if q not in cost and q not in new:
                                new[q] = ('/', y, x)
                    else:
                        if 1 not in cost and 1 not in new:
                            new[1] = ('/', x, y)
                    p = x * y
                    if p <= limit and p not in cost and p not in new:
                        new[p] = ('*', x, y)
                if len(cost) + len(new) > max_entries:
                    full = True
                    break
            if full:
                break
        for v in new:
            cost[v] = k
        how.update(new)
        levels.append(list(new))
        if full:
            break
    return cost, how, levels


class Overflow(Exception):
    """가상 풀 모드에서 살아 있는 값이 레지스터 수를 넘을 때."""


def assign(puzzle, vsteps):
    """값 수준 단계 목록에 레지스터를 배정한다 (죽은 명령 제거 + 인스턴스별 수명 분석). 실패하면 None."""
    nreg = puzzle.registers
    n = len(vsteps)
    # 뒤에서부터: 필요한 값만 남긴다. 같은 값이 여러 번 만들어지면 쓰임 직전의 것만 남는다.
    need = set(puzzle.targets) - set(puzzle.start)
    keep = [False] * n
    for i in range(n - 1, -1, -1):
        op, x, y, v = vsteps[i]
        if v in need:
            keep[i] = True
            need.discard(v)
            need.add(x)
            need.add(y)
    seq = [st for st, k in zip(vsteps, keep) if k]
    # 인스턴스별 마지막 사용 시점
    cur = {}
    for v in puzzle.start:
        cur.setdefault(v, -1)
    lastinst = {}
    use_inst = []
    for i, (op, x, y, v) in enumerate(seq):
        if x not in cur or y not in cur:
            return None
        ix, iy = cur[x], cur[y]
        lastinst[(x, ix)] = i
        lastinst[(y, iy)] = i
        use_inst.append((ix, iy))
        cur[v] = i
    where = {}
    free = []
    for i, v in enumerate(puzzle.start):
        if (v, -1) in where or (v, -1) not in lastinst:
            free.append(i)
        else:
            where[(v, -1)] = i
    free.extend(range(len(puzzle.start), nreg))
    free.reverse()
    out = []
    for i, (op, x, y, v) in enumerate(seq):
        kx = (x, use_inst[i][0])
        ky = (y, use_inst[i][1])
        if kx not in where or ky not in where:
            return None
        ra, rb = where[kx], where[ky]
        if lastinst[kx] == i:
            free.append(where.pop(kx))
        if ky != kx and lastinst[ky] == i:
            free.append(where.pop(ky))
        if not free:
            return None
        d = free.pop()
        out.append([op, ra, rb, d])
        if (v, i) in lastinst:
            where[(v, i)] = d
        else:
            free.append(d)
    return out


class Solver:
    EST_A = 1.5
    EST_B = 1.0 / 6.0

    def __init__(self, puzzle, small_entries=60000, pool_cap=48, maxdepth=14,
                 width=3, ntop=2, deadline=None, order='est', knear=12, refine=16, evict='lru', bucket_w=10, t2_n=30, width2=1, t2_near=0, use_chain=1, use_plan=1, chain_budget=100, astar_w=1.0, keep_bits=14, band_bits=12, band_lo=0.5,
                 f1_nodes=6, f1_rc=2, f1_minbits=18, f1_xbits=10, use_hub=0,
                 est_a=0.8, est_b=0.15, replan_len=12, replan_chunk=3, replan_max=6,
                 use_seeds=1, seed_bits=14, seed_users=2, seed_ratio=3, seed_max=10, seed_disc=1.0, quota=30, c2_nodes=2, c2_bits=0, use_div=1, seed=None,
                 virtual=1, vcap=160, deep_try=90, aux=None, aux_max=9):
        self.pz = puzzle
        self.limit = puzzle.limit
        self.nreg = puzzle.registers
        self.pool = {}          # value -> register
        self.free = []
        self.stamp = {}
        self.clock = 0
        self.prog = []
        self.starts = set(puzzle.start)
        for i, v in enumerate(puzzle.start):
            if v in self.pool:
                self.free.append(i)
            else:
                self.pool[v] = i
                self.stamp[v] = 0
        for i in range(len(puzzle.start), self.nreg):
            self.free.append(i)
        self.free.reverse()
        self.pool_cap = min(pool_cap, self.nreg)
        self.remaining = set(puzzle.targets) - self.starts
        # 보조 목표(숨은 허브와 밑수): 목표처럼 만들되 안 쓰이면 assign() 이 지운다.
        self.auxset = set(a for a in (aux or ()) if 1 <= a <= puzzle.limit and a not in self.starts and a not in self.remaining)
        self.aux_max = aux_max
        self.remaining |= self.auxset
        self.pins = set()
        self.Scost, self.Show, levels = build_small(sorted(self.starts), self.limit, small_entries)
        # S-곱 후보로 쓸 싼 S 값들 (최대 약 6000개)
        slow = []
        for lv in levels:
            if len(slow) + len(lv) > 6000 and slow:
                break
            slow.extend(lv)
        self.Slow = [a for a in slow if a >= 2]
        self.Ssorted = sorted(self.Scost)
        self.F1 = {}
        self.dirty = True
        self.maxdepth = maxdepth
        # 숨은 씨앗값: 서로 직접 관계가 없는 여러 목표의 (t - c) 가 공유하는 큰 약수.
        self.aux = {}
        self.protect = set()
        self.seed_users = {}
        if use_seeds and len(self.remaining) >= 3 and self.limit > (1 << 24):
            import seeds as seedmod
            found = seedmod.find_seeds(sorted(self.remaining - self.auxset), sorted(self.starts), min_bits=seed_bits)
            for sd, users in found.items():
                ts = sorted(set(t for t, c in users))
                if sd in self.remaining or sd in self.starts:
                    continue
                if sd * seed_ratio > ts[0]:
                    continue
                # 직접 관계(t_j ~ q*t_i ± 작은 값)로 묶이는 목표는 하나로 센다.
                indep = []
                for t in ts:
                    ok = True
                    for u in indep:
                        r = t % u
                        if min(r, u - r) < (u >> 10):
                            ok = False
                            break
                    if ok:
                        indep.append(t)
                if len(indep) >= seed_users:
                    self.seed_users[sd] = set(ts)
        self.use_seeds = use_seeds
        self.seed_disc = seed_disc
        self.last_amort = 99
        self.virtual = virtual
        self.t2_key = None
        self.t2_vals = []
        self.deep_calls = 0
        self.deep_hits = 0
        self.deep_try = deep_try
        self.nban = 0
        self.banned = set()
        if virtual:
            self.pool = {v: True for v in self.pool}
            self.pool_cap = vcap
            self.vsteps = []
            self.born = {v: -1 for v in self.starts}
            self.lastuse = {v: -1 for v in self.starts}
            self.L = []
            self.CAP = self.nreg - 1 - len(self.starts)
        self.c2_nodes = c2_nodes
        self.rng = None
        if seed is not None:
            import random
            self.rng = random.Random(seed)
            self.EST_B = est_b * self.rng.uniform(0.85, 1.2)
            self.EST_A = est_a + self.rng.uniform(-0.6, 0.4)
        self.use_div = use_div
        self.c2_bits = c2_bits
        self.knear = knear
        self.width2 = width2
        self.t2_n = t2_n
        self.t2_near = t2_near
        self.use_chain = use_chain
        self.use_plan = use_plan
        self.chain_budget = chain_budget
        self.astar_w = astar_w
        self.replan_len = replan_len
        self.replan_chunk = replan_chunk
        self.replan_max = replan_max
        if seed is None:
            self.EST_A = est_a
            self.EST_B = est_b
        self.use_hub = use_hub
        self.f1_nodes = f1_nodes
        self.f1_rc = f1_rc
        self.f1_minbits = f1_minbits
        self.f1_xbits = f1_xbits
        self.evict = evict
        self.keep_bits = keep_bits
        self.quota = quota
        self.band_bits = band_bits
        self.band_lo = band_lo
        self.bucket_w = bucket_w
        self.ntop_refine = refine
        self.divcache = {}
        self.width = width
        self.ntop = ntop
        self.deadline = deadline
        self.order = order
        self.log = []

    # ---------- 풀 관리 ----------
    def refresh(self):
        if not self.dirty:
            return
        limit = self.limit
        F1 = {}
        pool = self.pool
        if self.virtual and self.L:
            # 수명 한도가 꽉 찬 시점을 건너야 하는 값은 다시 쓸 수 없으므로 탐색 풀에서 뺀다.
            L = self.L
            cap = self.CAP
            full = -1
            for k in range(len(L) - 1, -1, -1):
                if L[k] >= cap:
                    full = k
                    break
            if full >= 0:
                lastuse = self.lastuse
                starts = self.starts
                for w in [w for w in pool if w not in starts and lastuse[w] < full]:
                    del pool[w]
        vals = sorted(pool)
        n = len(vals)
        for i in range(n):
            x = vals[i]
            for j in range(i):
                y = vals[j]
                s = x + y
                if s <= limit and s not in F1:
                    F1[s] = ('+', x, y)
                p = x * y
                if p <= limit and p not in F1:
                    F1[p] = ('*', x, y)
                d = x - y
                if d not in F1:
                    F1[d] = ('-', x, y)
                if x % y == 0:
                    q = x // y
                    if q not in F1:
                        F1[q] = ('/', x, y)
            s = x + x
            if s <= limit and s not in F1:
                F1[s] = ('+', x, x)
            p = x * x
            if p <= limit and p not in F1:
                F1[p] = ('*', x, x)
        if vals and 1 not in F1:
            F1[1] = ('/', vals[0], vals[0])
        for v in vals:
            F1.pop(v, None)
        self.F1 = F1
        self.F1list = list(F1)
        C = dict(self.Scost)
        C.update(dict.fromkeys(F1, 1))
        C.update(dict.fromkeys(vals, 0))
        self.C = C
        self.poolvals = vals
        self.c2vals = vals if self.c2_bits <= 0 else [v for v in vals if v.bit_length() <= self.c2_bits]
        self.sortedL = sorted(self.F1list + vals)
        self.dirty = False
        self.t2mark = set()
        self.t2done = False
        self.sortedT2 = []
        self.F1big = None

    def ensure_t2(self):
        """풀의 작은 값들로 명령 2개에 만들 수 있는 값(T2)을 C 에 비용 2로 넣는다.

        조리법은 저장하지 않고 필요할 때 t2_recipe() 로 다시 찾는다."""
        if self.t2done:
            return
        self.t2done = True
        n = self.t2_n
        if n <= 0:
            return
        small = self.poolvals[:n]
        limit = self.limit
        key = tuple(small)
        C = self.C
        if key == self.t2_key:
            # 재료가 그대로면 지난번 T2 를 다시 쓴다.
            new = [v for v in self.t2_vals if C.get(v, 9) > 2]
            self.t2mark = set(new)
            C.update(dict.fromkeys(new, 2))
            return
        A = set()
        for i, x in enumerate(small):
            for y in small[:i + 1]:
                A.add(x + y)
                A.add(x * y)
                if x != y:
                    A.add(x - y)
                    if x % y == 0:
                        A.add(x // y)
        A.add(1)
        A = [a for a in A if a <= limit]
        T = set()
        for p in small:
            T.update([a + p for a in A])
            T.update([a * p for a in A])
            T.update([a - p for a in A if a > p])
            T.update([p - a for a in A if a < p])
            T.update([a // p for a in A if a % p == 0])
            T.update([p // a for a in A if p % a == 0])
        Scost = self.Scost
        vals = [v for v in T if v <= limit and Scost.get(v, 9) > 2]
        self.t2_key = key
        self.t2_vals = vals
        new = [v for v in vals if C.get(v, 9) > 2]
        self.t2mark = set(new)
        C.update(dict.fromkeys(new, 2))
        if self.t2_near:
            new.sort()
            self.sortedT2 = new

    def t2_recipe(self, v):
        """T2 값 v = u op p (u 는 풀/F1, p 는 풀) 를 다시 찾는다."""
        C = self.C
        limit = self.limit
        for p in self.poolvals:
            if p < v:
                u = v - p
                if C.get(u, 9) <= 1:
                    return ('+', u, p)
                if v % p == 0:
                    u = v // p
                    if C.get(u, 9) <= 1:
                        return ('*', u, p)
            elif p > v:
                u = p - v
                if C.get(u, 9) <= 1:
                    return ('-', p, u)
                if p % v == 0:
                    u = p // v
                    if C.get(u, 9) <= 1:
                        return ('/', p, u)
            u = v + p
            if C.get(u, 9) <= 1:
                return ('-', u, p)
            u = v * p
            if u <= limit and C.get(u, 9) <= 1:
                return ('/', u, p)
        raise KeyError(v)

    def pick_evict(self):
        """탐색 풀이 찼을 때 뺄 값을 정책에 따라 고른다."""
        pool = self.pool
        cand = None
        cs = None
        stamp = self.stamp
        starts = self.starts
        pins = self.pins
        protect = self.protect
        if self.evict == 'lru':
            for u in pool:
                if u in starts or u in pins or u in protect:
                    continue
                s = stamp[u]
                if cs is None or s < cs:
                    cs = s
                    cand = u
        elif self.evict == 'big':
            # 가장 큰 값을 뺀다 (작은 값 = 곱수/자릿수 재료를 남긴다).
            for u in pool:
                if u in starts or u in pins or u in protect:
                    continue
                if cs is None or u > cs:
                    cs = u
                    cand = u
        elif self.evict == 'band':
            # band_bits 근처 크기의 값을 남긴다: 거기서 가장 먼 값을 뺀다 (작은 쪽은 덜 벌점).
            bb = self.band_bits
            lo = self.band_lo
            for u in pool:
                if u in starts or u in pins or u in protect:
                    continue
                b = u.bit_length()
                dist = (b - bb) if b > bb else (bb - b) * lo
                s = (dist, -stamp[u])
                if cs is None or s > cs:
                    cs = s
                    cand = u
        elif self.evict == 'quota':
            # 작은 값(keep_bits 이하)은 quota 개까지 두고, 넘으면 작은 값 중 LRU 를,
            # 아니면 큰 값 중 LRU 를 뺀다. 큰 값(목표, 허브)과 작은 값(곱수, 자릿수)을 함께 유지한다.
            kb = self.keep_bits
            nsmall = 0
            for u in pool:
                if u.bit_length() <= kb:
                    nsmall += 1
            want_small = nsmall > self.quota
            alt = None
            als = None
            for u in pool:
                if u in starts or u in pins or u in protect:
                    continue
                st = stamp[u]
                if (u.bit_length() <= kb) == want_small:
                    if cs is None or st < cs:
                        cs = st
                        cand = u
                elif als is None or st < als:
                    als = st
                    alt = u
            if cand is None:
                cand = alt
        elif self.evict == 'mid':
            # keep_bits 이하의 값은 보호하고, 그보다 큰 값 중 가장 오래 안 쓴 것을 뺀다.
            kb = self.keep_bits
            for u in pool:
                if u in starts or u in pins or u in protect:
                    continue
                s = (0 if u.bit_length() > kb else 1, stamp[u])
                if cs is None or s < cs:
                    cs = s
                    cand = u
        else:
            # 크기 구간별 균형: 가장 붐비는 구간에서 가장 오래 안 쓴 값을 뺀다.
            w = self.bucket_w
            cnt = {}
            for u in pool:
                b = u.bit_length() // w
                cnt[b] = cnt.get(b, 0) + 1
            for u in pool:
                if u in starts or u in pins or u in protect:
                    continue
                s = (-cnt[u.bit_length() // w], stamp[u])
                if cs is None or s < cs:
                    cs = s
                    cand = u
        return cand

    def emit(self, op, x, y):
        pool = self.pool
        if op == '+':
            v = x + y
        elif op == '-':
            v = x - y
        elif op == '*':
            v = x * y
        else:
            assert x % y == 0
            v = x // y
        assert 1 <= v <= self.limit, (op, x, y, v)
        self.clock += 1
        self.stamp[x] = self.clock
        self.stamp[y] = self.clock
        if v in pool:
            self.stamp[v] = self.clock
            return v
        if self.virtual:
            return self.emit_virtual(op, x, y, v)
        ra, rb = pool[x], pool[y]
        if self.free and len(pool) < self.pool_cap:
            d = self.free.pop()
        else:
            d = pool.pop(self.pick_evict())
        self.prog.append([op, ra, rb, d])
        pool[v] = d
        self.stamp[v] = self.clock
        self.remaining.discard(v)
        self.dirty = True
        return v

    def emit_virtual(self, op, x, y, v):
        """가상 풀 모드: 레지스터 대신 값의 수명 구간을 센다.

        L[k] = k번째 명령 시점에 살아 있어야 하는 (시작값이 아닌) 값의 수. CAP 을 넘으면 Overflow.
        """
        pool = self.pool
        L = self.L
        cap = self.CAP
        born = self.born
        lastuse = self.lastuse
        starts = self.starts
        tau = len(self.vsteps)
        if v in born and v not in self.banned:
            # 전에 만든 값: 수명을 늘릴 여유가 있으면 명령 없이 되살린다.
            lu = lastuse[v]
            if lu + 1 >= tau or max(L[lu + 1:tau]) <= cap - 2:
                if len(pool) >= self.pool_cap:
                    pool.pop(self.pick_evict(), None)
                pool[v] = True
                self.stamp[v] = self.clock
                self.dirty = True
                return v
        L.append(0)
        bad = None
        for w in ((x,) if x == y else (x, y)):
            if w in starts:
                continue
            lu = lastuse[w]
            for k in range(lu + 1, tau + 1):
                c = L[k] + 1
                L[k] = c
                if c > cap:
                    bad = w
            lastuse[w] = tau
        if bad is not None:
            raise Overflow(bad)
        self.vsteps.append((op, x, y, v))
        born[v] = tau
        lastuse[v] = tau
        if len(pool) >= self.pool_cap:
            pool.pop(self.pick_evict(), None)
        pool[v] = True
        self.stamp[v] = self.clock
        self.remaining.discard(v)
        self.dirty = True
        return v

    def run_steps(self, steps):
        """계획을 실행한다. 가상 풀 모드에서 수명 한도를 넘으면 되돌리고 문제의 값을 돌려준다."""
        # 계획 안에서 나중에 다시 쓰일 값만 축출 금지로 묶는다.
        last = {}
        for i, (op, x, y, v) in enumerate(steps):
            last[x] = i
            last[y] = i
        pins = set(last)
        self.pins = pins
        if self.virtual:
            snap = (len(self.vsteps), list(self.L), dict(self.lastuse), dict(self.born), dict(self.pool),
                    dict(self.stamp), self.clock, set(self.remaining))
        try:
            for i, (op, x, y, v) in enumerate(steps):
                r = self.emit(op, x, y)
                assert r == v, (op, x, y, v, r)
                if last[x] == i:
                    pins.discard(x)
                if last.get(y) == i:
                    pins.discard(y)
        except Overflow as e:
            n, self.L, self.lastuse, self.born, self.pool, self.stamp, self.clock, self.remaining = snap
            del self.vsteps[n:]
            self.pins = set()
            self.dirty = True
            return e.args[0]
        self.pins = set()
        return None

    # ---------- 전개 ----------
    def expand(self, v, steps, have):
        """C 에 있는 값 v 를 만드는 단계를 steps 에 덧붙인다."""
        if v in self.pool or v in have:
            return
        h = self.F1.get(v)
        if h is None:
            if v in self.t2mark:
                h = self.t2_recipe(v)
            else:
                h = self.Show[v]
        op, x, y = h
        self.expand(x, steps, have)
        self.expand(y, steps, have)
        steps.append((op, x, y, v))
        have.add(v)

    def recipe_steps(self, t, rec, steps=None, have=None):
        if steps is None:
            steps = []
            have = set()
        kind = rec[0]
        if kind == 'd':
            self.expand(t, steps, have)
        elif kind == 'b':
            _, op, a, b = rec
            self.expand(a, steps, have)
            self.expand(b, steps, have)
            if t not in have:
                steps.append((op, a, b, t))
                have.add(t)
        elif kind == 'v':
            # t = (p - e) / b + d
            _, pp, b, e, d = rec
            pool = self.pool
            self.expand(b, steps, have)
            m = pp
            if e != 0:
                ae = e if e > 0 else -e
                self.expand(ae, steps, have)
                m = pp - e
                if m not in have and m not in pool:
                    steps.append(('-' if e > 0 else '+', pp, ae, m))
                    have.add(m)
            y = m // b
            if y not in have and y not in pool:
                steps.append(('/', m, b, y))
                have.add(y)
            if d != 0:
                ad = d if d > 0 else -d
                self.expand(ad, steps, have)
                if t not in have:
                    steps.append(('+' if d > 0 else '-', y, ad, t))
                    have.add(t)
        else:  # 'q': t = q*x + r (sign=1) or q*x - r (sign=-1)
            _, x, q, r, sign = rec
            self.expand(x, steps, have)
            self.expand(q, steps, have)
            self.expand(r, steps, have)
            m = q * x
            if m not in have and m not in self.pool:
                steps.append(('*', q, x, m))
                have.add(m)
            if t not in have:
                steps.append(('+' if sign > 0 else '-', m, r, t))
                have.add(t)
        return steps

    # ---------- 정확 탐색 ----------
    def cheap(self, t, bound=99):
        """풀 값 하나를 피연산자로 하는 정확한 유도. (cost, recipe) / recipe 없으면 None."""
        C = self.C
        get = C.get
        best = None
        c = get(t)
        if c is not None and c < bound:
            bound = c
            best = ('d',)
            if c <= 1:
                return bound, best
        limit = self.limit
        usediv = self.use_div
        for p in self.poolvals:
            if p < t:
                u = t - p
                c = get(u)
                if c is not None and c + 1 < bound:
                    bound = c + 1
                    best = ('b', '+', u, p)
                q, r = divmod(t, p)
                if r == 0:
                    c = get(q)
                    if c is not None and c + 1 < bound:
                        bound = c + 1
                        best = ('b', '*', q, p)
                elif p > 1 and bound > 2:
                    cq = get(q)
                    if cq is not None:
                        cr = get(r)
                        if cr is not None and cq + cr + 2 < bound:
                            bound = cq + cr + 2
                            best = ('q', p, q, r, 1)
                    cq = get(q + 1)
                    if cq is not None and (q + 1) * p <= limit:
                        cr = get(p - r)
                        if cr is not None and cq + cr + 2 < bound:
                            bound = cq + cr + 2
                            best = ('q', p, q + 1, p - r, -1)
            elif p > t:
                u = p - t
                c = get(u)
                if c is not None and c + 1 < bound:
                    bound = c + 1
                    best = ('b', '-', p, u)
                if p % t == 0:
                    u = p // t
                    c = get(u)
                    if c is not None and c + 1 < bound:
                        bound = c + 1
                        best = ('b', '/', p, u)
                elif bound > 3 and usediv:
                    # 나눗셈 관계: t = (p - e) / b ± d  (b, e, d 는 C)
                    b0 = p // t
                    for b in (b0, b0 + 1):
                        if b < 2:
                            continue
                        cb = get(b)
                        if cb is None:
                            continue
                        e = p % b
                        for e2, y in ((e, p // b), (e - b, p // b + 1)):
                            if e2 == 0:
                                c1 = cb + 1
                            else:
                                ce = get(e2 if e2 > 0 else -e2)
                                if ce is None or p - e2 > limit:
                                    continue
                                c1 = cb + 2 + ce
                            d = t - y
                            if d == 0:
                                tot = c1
                            else:
                                cd = get(d if d > 0 else -d)
                                if cd is None:
                                    continue
                                tot = c1 + 1 + cd
                            if tot < bound:
                                bound = tot
                                best = ('v', p, b, e2, d)
            u = t + p
            c = get(u)
            if c is not None and c + 1 < bound:
                bound = c + 1
                best = ('b', '-', u, p)
            u = t * p
            if u <= limit:
                c = get(u)
                if c is not None and c + 1 < bound:
                    bound = c + 1
                    best = ('b', '/', u, p)
        return bound, best

    def hub_scan(self, rem, maxc=2):
        """여러 목표가 함께 쓰는 중간값 u (C 비용 maxc 이하)를 찾는다.

        t = u op p (p 는 풀) 꼴만 본다. (점수, -목표수, u, [(t, op, a, b), ...]) 중 최선을 돌려준다.
        점수 = (C[u] + 목표수) / 목표수 = 목표 하나당 명령 수.
        """
        C = self.C
        get = C.get
        limit = self.limit
        cand = {}
        for t in rem:
            for p in self.poolvals:
                if p < t:
                    u = t - p
                    c = get(u)
                    if c is not None and 0 < c <= maxc:
                        cand.setdefault(u, {}).setdefault(t, ('+', u, p))
                    if t % p == 0:
                        u = t // p
                        c = get(u)
                        if c is not None and 0 < c <= maxc:
                            cand.setdefault(u, {}).setdefault(t, ('*', u, p))
                elif p > t:
                    u = p - t
                    c = get(u)
                    if c is not None and 0 < c <= maxc:
                        cand.setdefault(u, {}).setdefault(t, ('-', p, u))
                    if p % t == 0:
                        u = p // t
                        c = get(u)
                        if c is not None and 0 < c <= maxc:
                            cand.setdefault(u, {}).setdefault(t, ('/', p, u))
                u = t + p
                c = get(u)
                if c is not None and 0 < c <= maxc:
                    cand.setdefault(u, {}).setdefault(t, ('-', u, p))
                u = t * p
                if u <= limit:
                    c = get(u)
                    if c is not None and 0 < c <= maxc:
                        cand.setdefault(u, {}).setdefault(t, ('/', u, p))
            # u op u 꼴 (제곱, 두 배)
        best = None
        for u, ts in cand.items():
            k = len(ts)
            if k < 2:
                continue
            key = ((C[u] + k) / k, -k, u)
            if best is None or key < best[0]:
                best = (key, u, ts)
        return best

    def deep(self, t, bound=99):
        """F1 값 하나(w, 비용 1)를 피연산자로 하는 정확한 유도. 비용 = C[u] + 2."""
        C = self.C
        F = self.F1list
        best = None
        h = [(C[t - w], w) for w in F if (t - w) in C]
        if h:
            c, w = min(h)
            if c + 2 < bound:
                bound = c + 2
                best = ('b', '+', t - w, w)
        if bound <= 3:
            return bound, best
        h = [(C[t + w], w) for w in F if (t + w) in C]
        if h:
            c, w = min(h)
            if c + 2 < bound:
                bound = c + 2
                best = ('b', '-', t + w, w)
        h = [(C[w - t], w) for w in F if (w - t) in C]
        if h:
            c, w = min(h)
            if c + 2 < bound:
                bound = c + 2
                best = ('b', '-', w, w - t)
        h = [(C[t // w], w) for w in F if t % w == 0 and (t // w) in C]
        if h:
            c, w = min(h)
            if c + 2 < bound:
                bound = c + 2
                best = ('b', '*', t // w, w)
        h = [(C[t * w], w) for w in F if (t * w) in C]
        if h:
            c, w = min(h)
            if c + 2 < bound:
                bound = c + 2
                best = ('b', '/', t * w, w)
        h = [(C[w // t], w) for w in F if w % t == 0 and (w // t) in C]
        if h:
            c, w = min(h)
            if c + 2 < bound:
                bound = c + 2
                best = ('b', '/', w, w // t)
        return bound, best

    # ---------- 근사 분해 ----------
    def est(self, v):
        c = self.C.get(v)
        if c is not None:
            return c
        return self.EST_A + v.bit_length() * self.EST_B

    def candidates(self, t, light=False):
        """(추정 총비용, kind, data) 목록. kind 0: t = x ± r, kind 1: t = q*x ± r."""
        est = self.est
        C = self.C
        limit = self.limit
        cands = []
        L = self.sortedL
        i = bisect.bisect_left(L, t)
        K = self.knear
        cap = t >> 2
        for k in range(i - K, i + K):
            if 0 <= k < len(L):
                x = L[k]
                r = t - x if t > x else x - t
                if 0 < r <= cap:
                    cands.append((C[x] + 1 + est(r), 0, (x, r)))
        L = self.Ssorted
        i = bisect.bisect_left(L, t)
        for k in (i - 2, i - 1, i, i + 1):
            if 0 <= k < len(L):
                x = L[k]
                r = t - x if t > x else x - t
                if 0 < r <= cap and C[x] > 1:
                    cands.append((C[x] + 1 + est(r), 0, (x, r)))
        L = self.sortedT2
        if L:
            i = bisect.bisect_left(L, t)
            K2 = self.t2_near
            for k in range(i - K2, i + K2):
                if 0 <= k < len(L):
                    x = L[k]
                    r = t - x if t > x else x - t
                    if 0 < r <= cap:
                        cands.append((3 + est(r), 0, (x, r)))
        for x in self.poolvals:
            if x < 2 or x >= t:
                continue
            q, r = divmod(t, x)
            if r == 0:
                cands.append((1 + est(q), 1, (x, q, 0, 1)))
            else:
                cands.append((2 + est(q) + est(r), 1, (x, q, r, 1)))
                if (q + 1) * x <= limit:
                    cands.append((2 + est(q + 1) + est(x - r), 1, (x, q + 1, x - r, -1)))
        if not light:
            for a, b in [(a, t // a) for a in self.Slow if (t // a) in C]:
                if a >= t:
                    continue
                r = t - a * b
                ca = C[a] + C[b]
                if r == 0:
                    cands.append((ca + 1, 1, (a, b, 0, 1)))
                else:
                    cands.append((ca + 2 + est(r), 1, (a, b, r, 1)))
            for a, b in [(a, t // a + 1) for a in self.Slow if (t // a + 1) in C]:
                if a >= t or a * b > limit:
                    continue
                r = a * b - t
                cands.append((C[a] + C[b] + 2 + est(r), 1, (a, b, r, -1)))
            # 약수 분해: t = d * e
            for d in self.divisors(t):
                if d < 2 or d * d > t:
                    continue
                e = t // d
                cd = C.get(d)
                ce = C.get(e)
                if cd is not None:
                    cands.append((cd + 1 + est(e), 1, (d, e, 0, 1)))
                elif ce is not None:
                    cands.append((ce + 1 + est(d), 1, (e, d, 0, 1)))
                else:
                    cands.append((1 + est(d) + est(e), 1, (d, e, 0, 1)))
        cands.sort()
        return cands

    def divisors(self, t):
        ds = self.divcache.get(t)
        if ds is None:
            ds = nt.divisors_bounded(t, 400)
            self.divcache[t] = ds
        return ds

    def refine(self, cands, top):
        """상위 후보의 미지 부분을 cheap() 으로 정확히 평가해 추정을 고친다."""
        C = self.C
        out = []
        n = 0
        memo = {}
        for e, kind, data in cands:
            if n >= top:
                out.append((e, kind, data))
                continue
            n += 1
            parts = (data[1],) if kind == 0 else ((data[0], data[1]) if data[2] == 0 else data[:3])
            tot = (C[data[0]] + 1) if kind == 0 else (1 if data[2] == 0 else 2)
            for v in parts:
                c = C.get(v)
                if c is None:
                    if v not in memo:
                        b, rec = self.cheap(v)
                        memo[v] = b if rec is not None else None
                    c = memo[v]
                    if c is None:
                        c = self.EST_A + v.bit_length() * self.EST_B
                tot += c
            out.append((tot, kind, data))
        out.sort()
        return out

    def plan(self, t, depth=0):
        """t 를 만드는 단계 목록. 실패하면 None."""
        bound, rec = self.cheap(t)
        if rec is not None and bound <= 2:
            return self.recipe_steps(t, rec)
        if depth <= 1 and bound > 3:
            bound, rec2 = self.deep(t, bound)
            if rec2 is not None:
                rec = rec2
        best = self.recipe_steps(t, rec) if rec is not None else None
        if depth >= self.maxdepth:
            return best if best is not None else self.binary_steps(t)
        if best is not None and len(best) <= 3:
            return best
        cands = self.candidates(t, light=(depth >= 3))
        cands = self.refine(cands, self.ntop_refine)
        width = self.width if depth == 0 else self.width2
        tried = 0
        for e, kind, data in cands:
            if tried >= width:
                break
            if best is not None and e >= len(best):
                break
            tried += 1
            steps = []
            have = set()
            ok = True
            if kind == 0:
                x, r = data
                sub = self.plan(r, depth + 1)
                if sub is None:
                    continue
                self.expand(x, steps, have)
                for s in sub:
                    if s[3] not in have:
                        steps.append(s)
                        have.add(s[3])
                if t not in have:
                    if x > t:
                        steps.append(('-', x, r, t))
                    else:
                        steps.append(('+', x, r, t))
            else:
                x, q, r, sign = data
                parts = [x, q] if r == 0 else [x, q, r]
                for v in parts:
                    if v in self.pool or v in have:
                        continue
                    if v in self.C and self.C[v] <= 1:
                        self.expand(v, steps, have)
                        continue
                    sub = self.plan(v, depth + 1)
                    if sub is None:
                        ok = False
                        break
                    for s in sub:
                        if s[3] not in have:
                            steps.append(s)
                            have.add(s[3])
                if not ok:
                    continue
                m = q * x
                if r == 0:
                    if t not in have:
                        steps.append(('*', q, x, t))
                else:
                    if m not in have and m not in self.pool:
                        steps.append(('*', q, x, m))
                        have.add(m)
                    if t not in have:
                        steps.append(('+' if sign > 0 else '-', m, r, t))
            if best is None or len(steps) < len(best):
                best = steps
        if best is None:
            best = self.binary_steps(t)
        return best

    def inv6(self, t, p):
        """t = u op p (left=True) 또는 t = p op u (left=False) 가 되는 (u, op, left) 목록."""
        res = []
        limit = self.limit
        if t > p:
            res.append((t - p, '+', True))
            if t % p == 0:
                res.append((t // p, '*', True))
        elif p > t:
            res.append((p - t, '-', False))
            if p % t == 0:
                res.append((p // t, '/', False))
        if t + p <= limit:
            res.append((t + p, '-', True))
        if t * p <= limit:
            res.append((t * p, '/', True))
        return res

    def chain_search(self, t, budget=150, ub=None, seeds_on=True):
        """t 에서 거꾸로 내려가는 최단 사슬 탐색 (best-first).

        간선: v = q*x ± r (x 는 풀, r 은 C) -> q,  v = x ± r (x 는 풀/F1 의 가까운 값) -> r,
              v = d*e (d 는 C) -> e.  끝: v 가 C 에 있거나 cheap(v) 로 정확히 풀릴 때.
        """
        import heapq
        C = self.C
        get = C.get
        limit = self.limit
        A = self.EST_A
        B = self.EST_B
        W = self.astar_w
        pool = self.poolvals
        L = self.sortedL
        K = self.knear
        f1_nodes = self.f1_nodes
        f1_rc = self.f1_rc
        f1_min = 1 << self.f1_minbits
        F1big = self.F1big
        if F1big is None:
            lo = 1 << self.f1_xbits
            F1big = self.F1big = [x for x in self.F1list if x >= lo]
        n_f1 = 0
        seedlist = []
        if seeds_on and self.seed_users:
            remaining = self.remaining
            disc = self.seed_disc
            for sd, users in self.seed_users.items():
                if sd in C and C[sd] <= 1:
                    continue
                k = len(users & remaining)
                if k >= 1:
                    seedlist.append((sd, (A + sd.bit_length() * B) / (1 + disc * (k - 1))))
        nodes = [(t, 0, -1, None)]          # (value, g, parent index, edge)
        seen = {t: 0}
        heap = [(W * (A + t.bit_length() * B), 0, 0)]
        best_total = ub if ub is not None else 10 ** 9
        best_leaf = None                      # (node index, cheap recipe)
        n_exp = 0
        cnt = 1
        while heap and n_exp < budget:
            f, _, idx = heapq.heappop(heap)
            v, g, par, edge = nodes[idx]
            if g + 1 >= best_total:
                continue
            if seen.get(v, 99) < g:
                continue
            n_exp += 1
            b, rec = self.cheap(v, best_total - g)
            if rec is not None and g + b < best_total:
                best_total = g + b
                best_leaf = (idx, rec)
                if b <= 1:
                    continue
            if n_exp <= self.c2_nodes and best_total - g > 3:
                # 역방향 2단계: v = u op p (p 는 풀), u 는 cheap() 으로 정확히 풀리는 값.
                bb = best_total - g - 1
                for p in self.c2vals:
                    for u, op, left in self.inv6(v, p):
                        if u in C:
                            continue
                        b2, rec2 = self.cheap(u, bb)
                        if rec2 is not None and b2 < bb:
                            bb = b2
                            nodes.append((u, g + 1, idx, (4, op, p, left)))
                            best_total = g + 1 + b2
                            best_leaf = (len(nodes) - 1, rec2)
            if g + 3 >= best_total:
                continue
            ch = []
            for x in pool:
                if x < 2 or x >= v:
                    continue
                q, r = divmod(v, x)
                if r == 0:
                    ch.append((q, 1, (1, x, 0, 1)))
                else:
                    c = get(r)
                    if c is not None:
                        ch.append((q, 2 + c, (1, x, r, 1)))
                    c = get(x - r)
                    if c is not None and (q + 1) * x <= limit:
                        ch.append((q + 1, 2 + c, (1, x, x - r, -1)))
            if n_f1 < f1_nodes and v > f1_min:
                # F1 값을 곱수로: v = q*x ± r, x 는 F1 (비용 1), r 은 풀/F1.
                n_f1 += 1
                for x, r in [(x, r) for x, r in [(x, v % x) for x in F1big if x < v]
                             if r in C or (x - r) in C or r == 0]:
                    if r == 0:
                        ch.append((v // x, 2, (1, x, 0, 1)))
                        continue
                    c = get(r)
                    if c is not None and c <= f1_rc:
                        ch.append((v // x, 3 + c, (1, x, r, 1)))
                    c = get(x - r)
                    if c is not None and c <= f1_rc and (v // x + 1) * x <= limit:
                        ch.append((v // x + 1, 3 + c, (1, x, x - r, -1)))
            if seedlist:
                for x, sc in seedlist:
                    if x >= v:
                        continue
                    q, r = divmod(v, x)
                    if r == 0:
                        ch.append((q, sc + 1, (3, x, 0, 1)))
                    else:
                        c = get(r)
                        if c is not None and c <= 2:
                            ch.append((q, sc + 2 + c, (3, x, r, 1)))
                        c = get(x - r)
                        if c is not None and c <= 2 and (q + 1) * x <= limit:
                            ch.append((q + 1, sc + 2 + c, (3, x, x - r, -1)))
            i = bisect.bisect_left(L, v)
            cap = v >> 2
            for k in range(i - K, i + K):
                if 0 <= k < len(L):
                    x = L[k]
                    r = v - x if v > x else x - v
                    if 0 < r <= cap:
                        ch.append((r, C[x] + 1, (0, x, 1 if v > x else -1)))
            if idx == 0 or g <= 2:
                for d in self.divisors(v):
                    if d < 2 or d >= v:
                        continue
                    c = get(d)
                    if c is not None and c <= 3:
                        ch.append((v // d, 1 + c, (2, d)))
            for u, c, e in ch:
                ng = g + c
                if ng + 1 >= best_total:
                    continue
                if seen.get(u, 99) <= ng:
                    continue
                seen[u] = ng
                cu = get(u)
                h = cu if cu is not None else A + u.bit_length() * B
                nodes.append((u, ng, idx, e))
                heapq.heappush(heap, (ng + W * h, cnt, len(nodes) - 1))
                cnt += 1
        if best_leaf is None:
            return None
        amort = best_total
        idx, rec = best_leaf
        v = nodes[idx][0]
        steps = self.recipe_steps(v, rec)
        have = set(st[3] for st in steps)
        while nodes[idx][2] >= 0:
            v, g, par, e = nodes[idx]
            pv = nodes[par][0]
            if e[0] == 1 or e[0] == 3:
                _, x, r, sign = e
                if e[0] == 3 and x not in have and x not in self.pool:
                    sub = self.chain_search(x, budget, seeds_on=False)
                    if sub is None:
                        sub = self.plan(x)
                    for st in sub:
                        if st[3] not in have and st[3] not in self.pool:
                            steps.append(st)
                            have.add(st[3])
                else:
                    self.expand(x, steps, have)
                if r == 0:
                    if pv not in have and pv not in self.pool:
                        steps.append(('*', v, x, pv))
                        have.add(pv)
                else:
                    self.expand(r, steps, have)
                    m = v * x
                    if m not in have and m not in self.pool:
                        steps.append(('*', v, x, m))
                        have.add(m)
                    if pv not in have and pv not in self.pool:
                        steps.append(('+' if sign > 0 else '-', m, r, pv))
                        have.add(pv)
            elif e[0] == 0:
                _, x, sign = e
                self.expand(x, steps, have)
                if pv not in have and pv not in self.pool:
                    steps.append(('+', x, v, pv) if sign > 0 else ('-', x, v, pv))
                    have.add(pv)
            elif e[0] == 4:
                _, op, p, left = e
                if pv not in have and pv not in self.pool:
                    steps.append((op, v, p, pv) if left else (op, p, v, pv))
                    have.add(pv)
            else:
                _, d = e
                self.expand(d, steps, have)
                if pv not in have and pv not in self.pool:
                    steps.append(('*', v, d, pv))
                    have.add(pv)
            idx = par
        self.last_amort = amort
        return steps

    def binary_steps(self, v):
        """항상 성공하는 최후 수단: 1 에서 두 배와 +1 로 v 를 만든다."""
        steps = []
        have = set()
        if 1 not in self.pool:
            if 1 in self.F1:
                self.expand(1, steps, have)
            else:
                p = self.poolvals[0]
                steps.append(('/', p, p, 1))
                have.add(1)
        acc = 1
        for ch in bin(v)[3:]:
            nxt = acc + acc
            if nxt not in have and nxt not in self.pool:
                steps.append(('+', acc, acc, nxt))
                have.add(nxt)
            acc = nxt
            if ch == '1':
                nxt = acc + 1
                if nxt not in have and nxt not in self.pool:
                    steps.append(('+', acc, 1, nxt))
                    have.add(nxt)
                acc = nxt
        return steps

    # ---------- 주 루프 ----------
    def solve(self):
        replans = 0
        while self.remaining:
            self.refresh()
            best = None
            bc = 99
            bt = None
            if self.seed_users:
                remaining = self.remaining
                prot = set()
                for sd in list(self.seed_users):
                    live = self.seed_users[sd] & remaining
                    if not live:
                        del self.seed_users[sd]
                    elif sd in self.pool:
                        prot.add(sd)
                self.protect = prot
            rem = sorted(self.remaining)
            if self.rng is not None:
                self.rng.shuffle(rem)
            for t in rem:
                b, rec = self.cheap(t, bc)
                if rec is not None and b < bc:
                    bc, best, bt = b, rec, t
                    if bc <= 1:
                        break
            if bc >= 2 and self.use_hub and len(rem) > 1:
                hub = self.hub_scan(rem)
                if hub is not None and hub[0][0] < bc:
                    (score, negk, u), u, ts = hub
                    steps = []
                    have = set()
                    self.expand(u, steps, have)
                    for t, (op, a, b) in ts.items():
                        if t not in have:
                            steps.append((op, a, b, t))
                            have.add(t)
                    self.log.append((u, len(steps)))
                    bad = self.run_steps(steps)
                    if bad is not None:
                        self.ban(bad)
                    continue
            if bc > 2 and (self.deep_hits > 0 or self.deep_calls < self.deep_try):
                # deep 은 임의값 퍼즐에서는 거의 안 맞으므로, 처음 deep_try 번 동안 한 번도 안 맞으면 끈다.
                for t in rem:
                    self.deep_calls += 1
                    b, rec = self.deep(t, bc)
                    if rec is not None and b < bc:
                        self.deep_hits += 1
                        bc, best, bt = b, rec, t
                        if bc <= 3:
                            break
            steps = self.recipe_steps(bt, best) if best is not None else None
            if steps is None or len(steps) > 3:
                # 막힘: 근사 분해. 추정이 싼 목표 몇 개만 실제로 계획한다.
                self.ensure_t2()
                scored = []
                for t in rem:
                    cs = self.candidates(t, light=True)
                    e0 = cs[0][0] if cs else 99
                    if self.rng is not None:
                        e0 *= self.rng.uniform(0.9, 1.1)
                    scored.append((e0, t))
                scored.sort()
                scost = len(steps) if steps is not None else 99
                for e, t in scored[:self.ntop]:
                    if steps is not None and e >= scost:
                        break
                    pl = None
                    pc = 99
                    if self.use_chain:
                        pl = self.chain_search(t, self.chain_budget)
                        if pl is not None:
                            pc = min(len(pl), self.last_amort)
                    if self.use_plan or pl is None:
                        pl2 = self.plan(t)
                        if pl2 is not None and (pl is None or len(pl2) < pc):
                            pl = pl2
                            pc = len(pl2)
                    if pl is not None and (steps is None or pc < scost):
                        steps, bt, scost = pl, t, pc
            assert steps is not None, 'no plan'
            if bt in self.auxset and len(steps) > self.aux_max:
                # 보조 목표가 너무 비싸면 포기한다.
                self.remaining.discard(bt)
                self.auxset.discard(bt)
                continue
            if self.replan_len and len(steps) > self.replan_len and replans < self.replan_max:
                # 긴 계획은 앞부분만 실행하고 풀이 풍부해진 뒤 다시 계획한다 (안 쓰인 명령은 dce 가 지운다).
                replans += 1
                bad = self.run_steps(steps[:self.replan_chunk])
                if bad is not None:
                    self.ban(bad)
                else:
                    self.log.append((0, self.replan_chunk))
                continue
            bad = self.run_steps(steps)
            if bad is not None:
                self.ban(bad)
                continue
            replans = 0
            self.log.append((bt, len(steps)))
            assert bt in self.pool or bt not in self.remaining
        if self.virtual:
            prog = assign(self.pz, self.vsteps)
            assert prog is not None, 'register assignment failed'
            return prog
        return self.prog

    def ban(self, w):
        """수명 한도 때문에 못 쓰는 값을 탐색 풀에서 뺀다 (시작값은 항상 남는다)."""
        self.nban += 1
        assert self.nban < 2000, 'too many overflows'
        if w not in self.starts:
            self.pool.pop(w, None)
            self.banned.add(w)
        self.dirty = True


def dce(puzzle, prog):
    """쓰이지 않는 명령 제거 (목표값을 처음 만드는 명령은 유지)."""
    n = len(prog)
    reg = [None] * puzzle.registers
    reg[:len(puzzle.start)] = puzzle.start
    missing = set(puzzle.targets) - set(puzzle.start)
    needed_first = [False] * n
    for i, (op, a, b, d) in enumerate(prog):
        x, y = reg[a], reg[b]
        v = x + y if op == '+' else x - y if op == '-' else x * y if op == '*' else x // y
        reg[d] = v
        if v in missing:
            missing.discard(v)
            needed_first[i] = True
    live = set()
    keep = [False] * n
    for i in range(n - 1, -1, -1):
        op, a, b, d = prog[i]
        if d in live or needed_first[i]:
            keep[i] = True
            live.discard(d)
            live.add(a)
            live.add(b)
    return [ins for ins, k in zip(prog, keep) if k]


def compact(puzzle, prog):
    """값 수준으로 풀어 중복 계산과 죽은 명령을 지우고, 수명 분석으로 레지스터를 다시 배정한다.

    축출됐다가 다시 만든 값을 한 번만 만들게 된다. 레지스터가 모자라면 None.
    """
    nreg = puzzle.registers
    reg = [None] * nreg
    reg[:len(puzzle.start)] = puzzle.start
    seen = set(puzzle.start)
    seq = []
    for op, a, b, d in prog:
        x, y = reg[a], reg[b]
        v = x + y if op == '+' else x - y if op == '-' else x * y if op == '*' else x // y
        reg[d] = v
        if v not in seen:
            seen.add(v)
            seq.append((op, x, y, v))
    # 필요한 명령만 남긴다 (목표이거나 뒤에서 쓰이는 값).
    need = set(puzzle.targets) - set(puzzle.start)
    keep = [False] * len(seq)
    for i in range(len(seq) - 1, -1, -1):
        op, x, y, v = seq[i]
        if v in need:
            keep[i] = True
            need.add(x)
            need.add(y)
    seq = [st for st, k in zip(seq, keep) if k]
    last = {}
    for i, (op, x, y, v) in enumerate(seq):
        last[x] = i
        last[y] = i
    where = {}
    free = []
    for i, v in enumerate(puzzle.start):
        if v in where or v not in last:
            free.append(i)
        else:
            where[v] = i
    free.extend(range(len(puzzle.start), nreg))
    free.reverse()
    out = []
    for i, (op, x, y, v) in enumerate(seq):
        ra, rb = where[x], where[y]
        if last[x] == i:
            free.append(where.pop(x))
        if y != x and last[y] == i:
            free.append(where.pop(y))
        if not free:
            return None
        d = free.pop()
        out.append([op, ra, rb, d])
        if v in last:
            where[v] = d
        else:
            free.append(d)
    return out


def finish(pz, prog):
    """dce 뒤에 compact 를 시도하고, 유효하고 더 짧으면 그것을 쓴다."""
    from verify import check_program
    prog = dce(pz, prog)
    c = compact(pz, prog)
    if c is not None and len(c) < len(prog) and check_program(pz, c) is None:
        return c
    return prog


VARIANTS = [
    dict(evict='big', vcap=110, est_a=1.5, est_b=1.0 / 6.0),
    dict(seed=1),
    dict(evict='band', vcap=110, seed=2),
    dict(seed=3, ntop=3),
    dict(evict='big', vcap=130, seed=4),
    dict(seed=5),
    dict(evict='quota', vcap=110, quota=70, seed=6),
    dict(seed=7),
]


def solve_puzzle(pz, tbudget=0.0, vstart=0, **kw):
    """퍼즐 하나를 풀어 프로그램을 돌려준다 (검증은 호출자가 한다).

    tbudget 초가 남아 있는 동안 설정/난수를 바꿔 다시 풀고 가장 짧은 것을 고른다.
    """
    if pz.limit <= 64:
        import tiny
        prog = tiny.solve_tiny(pz)
        if prog is not None:
            return prog
    t0 = time.time()
    from verify import check_program
    try:
        best = finish(pz, Solver(pz, **kw).solve())
        if check_program(pz, best) is not None:
            raise AssertionError('invalid')
    except AssertionError:
        kw = dict(kw)
        kw['virtual'] = 0
        best = finish(pz, Solver(pz, **kw).solve())
    last = time.time() - t0
    i = vstart
    while tbudget > 0 and i < vstart + 400 and time.time() - t0 + last < tbudget:
        t1 = time.time()
        kw2 = dict(kw)
        if i < len(VARIANTS):
            kw2.update(VARIANTS[i])
        else:
            kw2.update(dict(seed=i))
        i += 1
        try:
            prog = finish(pz, Solver(pz, **kw2).solve())
        except AssertionError:
            continue
        last = time.time() - t1
        if len(prog) < len(best):
            from verify import check_program
            if check_program(pz, prog) is None:
                best = prog
    return best


_SCAN = None


def load_scan(path='/home/maverick/Santa2026/solvers/search/basescan_all.txt'):
    """basescan 출력 파일을 읽는다: id -> [(d, hits, mask)]."""
    global _SCAN
    if _SCAN is None:
        _SCAN = {}
        try:
            for line in open(path):
                parts = line.split()
                if not parts:
                    continue
                _SCAN[parts[0]] = [tuple(int(x) for x in p.split(':')) for p in parts[1:]]
        except IOError:
            pass
    return _SCAN


def hub_aux(pz, mode='pin', scan=False, **hk):
    """숨은 허브와 밑수 후보 (hubs.py). (허브 목록, 밑수 목록) 을 돌려준다.

    scan=True 면 basescan(C++) 이 찾은 밑수를 함께 쓴다.
    """
    import hubs as hubmod
    if pz.limit <= (1 << 24):
        return [], []
    scost = build_small(sorted(set(pz.start)), pz.limit, 20000)[0]
    kb = ()
    if scan:
        sc = load_scan().get(pz.id)
        if sc:
            n = len(set(pz.targets) - set(pz.start))
            kb = tuple(hubmod.scan_bases(sc, n))
        if not kb:
            return [], []
    hs, bs, info = hubmod.find_hubs(pz.targets, pz.start, scost=scost, mode=mode, kb=kb, **hk)
    # 지지 목표가 3개 이상인 허브도 밑수도 없으면 우연(임의값 퍼즐)으로 본다.
    if not bs and not any(info[h] >= 3 for h in hs):
        return [], []
    return hs, bs


_D3 = None


def load_d3(path='/home/maverick/Santa2026/solvers/search/decode3.json'):
    """decode3.py 의 해독 결과: id -> {'bases': [...], 'hubs': {h: 지지 수}}."""
    global _D3
    if _D3 is None:
        import json
        try:
            _D3 = json.load(open(path))
        except IOError:
            _D3 = {}
    return _D3


_PS = None


def load_ps(path='/home/maverick/Santa2026/solvers/search/pairscan_all.txt'):
    """pairscan 출력에서 퍼즐별 밑수 후보(지지 목표가 많은 순서로 110개까지)를 만든다."""
    global _PS
    if _PS is None:
        _PS = {}
        try:
            for line in open(path):
                parts = line.split()
                if len(parts) < 2:
                    continue
                sc = {}
                for p in parts[1:]:
                    a, b, m, mask = (int(x) for x in p.split(':'))
                    sc[a] = sc.get(a, 0) | mask
                    sc[b] = sc.get(b, 0) | mask
                _PS[parts[0]] = sorted(sc, key=lambda v: (-bin(sc[v]).count('1'), -v))[:110]
        except IOError:
            pass
    return _PS


def aux_variants(pz, modes):
    """해독 방식마다 보조 목표 목록을 만든다. [(이름, 보조 목표 목록)]"""
    import hubs as hubmod
    out = []
    seen = set()

    def add(name, aux):
        key = tuple(sorted(set(aux)))
        if len(key) >= 2 and key not in seen:
            seen.add(key)
            out.append((name, list(key)))

    for m in modes:
        if m == 'd3':
            ent = load_d3().get(pz.id)
            if not ent or not ent['hubs']:
                continue
            hs = [int(h) for h in ent['hubs']]
            bs = list(ent['bases'])
        elif m == 'uni':
            # 세 해독의 밑수 후보를 모아 설명력으로 고른 것 (hubs.uni_decode)
            if pz.limit <= (1 << 30):
                continue
            ent = load_d3().get(pz.id) or {}
            bs, hd = hubmod.uni_decode(pz.targets, pz.start, scan=load_scan().get(pz.id), extra=ent.get('bases', ()))
            if len(bs) < 2 or sum(hd.values()) < 6:
                continue
            hs = list(hd)
            need2 = hubmod.decode_smalls2(pz.targets, hs, pz.start)
            add('uni+all2', hs + bs + list(need2))
            add('uni+sm12', hs + bs + [v for v, c in need2.items() if c >= 2 or v < 4096])
            continue
        elif m == 'ps':
            # 작은 밑수(2^9~2^13) 퍼즐: pairscan(C++) 이 지지 목표 5개 이상인 a*b 를 전부 찾아 둔 것에서 밑수를 고른다.
            cl = load_ps().get(pz.id)
            if not cl:
                continue
            T = sorted(set(pz.targets) - set(pz.start))
            bs, hd = hubmod.greedy_bases(T, cl, set(pz.start))
            if len(bs) < 2 or sum(hd.values()) < 5:
                continue
            hs = list(hd)
            need2 = hubmod.decode_smalls2(pz.targets, hs, pz.start)
            add('ps+all2', hs + bs + list(need2))
            add('ps+sm12', hs + bs + [v for v, c in need2.items() if c >= 2 or v < 4096])
            add('ps+cnt2', hs + bs + [v for v, c in need2.items() if c >= 2])
            continue
        elif m == 'uni2':
            if pz.limit <= (1 << 30):
                continue
            ent = load_d3().get(pz.id) or {}
            bs, hd = hubmod.uni_decode(pz.targets, pz.start, scan=load_scan().get(pz.id), extra=ent.get('bases', ()))
            if len(bs) < 2 or sum(hd.values()) < 6:
                continue
            hs = list(hd)
            need2 = hubmod.decode_smalls2(pz.targets, hs, pz.start)
            add('uni+cnt2', hs + bs + [v for v, c in need2.items() if c >= 2])
            add('uni', hs + bs)
            continue
        elif m in ('tri', 'tri2'):
            # 삼각 관계 해독을 허용 오차 W 를 바꿔 가며 돌리고, 설명하는 목표가 많은 해독 둘을 쓴다.
            if pz.limit <= (1 << 30):
                continue
            T = sorted(set(pz.targets) - set(pz.start))
            reps = hubmod.cluster_reps(T)
            decs = []
            for W in (1 << 9, 1 << 11, 1 << 13, 1 << 15, 1 << 17):
                bs, hd = hubmod.tri_decode(T, pz.start, W=W, reps=reps)
                if len(bs) >= 2 and sum(hd.values()) >= 6:
                    decs.append((-sum(hd.values()), W, bs, hd))
            decs.sort(key=lambda d: (d[0], d[1]))
            used = set()
            k = 0
            for negs, W, bs, hd in decs:
                key = tuple(bs)
                if key in used:
                    continue
                used.add(key)
                hs = list(hd)
                need = hubmod.decode_smalls(pz.targets, hs, pz.start)
                if m == 'tri':
                    add('tri%d+sm' % k, hs + bs + [v for v, c in need.items() if c >= 2])
                    add('tri%d' % k, hs + bs)
                else:
                    # 작은 값 보조 목표를 더 넓게: 전부, 또는 4096 미만이거나 두 번 이상 필요한 것
                    need2 = hubmod.decode_smalls2(pz.targets, hs, pz.start)
                    add('tri%d+all2' % k, hs + bs + list(need2))
                    add('tri%d+sm12' % k, hs + bs + [v for v, c in need2.items() if c >= 2 or v < 4096])
                    add('tri%d+cnt2' % k, hs + bs + [v for v, c in need2.items() if c >= 2])
                k += 1
                if k >= 1:
                    break
            continue
        elif m == 'scan':
            hs, bs = hub_aux(pz, mode='pin', scan=True)
        else:
            hs, bs = hub_aux(pz, mode=m)
        if len(hs) + len(bs) < 2:
            continue
        if m == 'd3':
            # 허브가 정확하면 목표마다 t = k*h + r 의 k, r 도 미리 알 수 있다. 여러 목표가 나눠 쓰도록 보조 목표로 넣는다.
            need2 = hubmod.decode_smalls2(pz.targets, hs, pz.start)
            add(m + '+all2', hs + bs + list(need2))
            add(m + '+cnt2', hs + bs + [v for v, c in need2.items() if c >= 2])
            add(m, hs + bs)
        else:
            add(m, hs + bs)
            add(m + '-b', hs)
    return out


def solve_hubs(pz, seeds=(None,), modes=('simple', 'pin'), verbose=False, **kw):
    """허브/밑수를 보조 목표로 넣어 푼다. 가장 짧은 프로그램을 돌려준다 (허브가 없으면 None).

    해독 방식(modes)과 보조 목표 구성을 바꿔 가며 풀어 최단을 고른다.
    """
    from verify import check_program
    if isinstance(modes, str):
        modes = tuple(modes.split('+'))
    if isinstance(seeds, int):
        # seeds=k: 난수 씨 k 하나로만 돈다 (0 이면 기본 설정)
        seeds = (seeds if seeds else None,)
    variants = aux_variants(pz, modes)
    if not variants:
        return None
    best = None
    for sd in seeds:
        for name, aux in variants:
            kw2 = dict(kw)
            kw2['aux'] = aux
            if sd is not None:
                kw2['seed'] = sd
            try:
                prog = finish(pz, Solver(pz, **kw2).solve())
            except AssertionError:
                continue
            if verbose:
                print('   ', pz.id, name, len(aux), len(prog), flush=True)
            if (best is None or len(prog) < len(best)) and check_program(pz, prog) is None:
                best = prog
    return best


if __name__ == '__main__':
    from verify import load_puzzles, check_program
    import csv
    path = '/home/maverick/Santa2026/data/practice_puzzles.csv'
    puzzles = load_puzzles(path)
    fam = {r['id']: r['family'] for r in csv.DictReader(open(path))}
    ids = sys.argv[1:]
    for pid in ids:
        pz = puzzles[pid]
        t0 = time.time()
        s = Solver(pz)
        prog = s.solve()
        prog2 = dce(pz, prog)
        err = check_program(pz, prog2)
        print(pid, fam[pid], 'targets', len(pz.targets), 'len', len(prog), len(prog2), 'err', err,
              'time %.2f' % (time.time() - t0), flush=True)
        print('   ', [c for t, c in s.log], flush=True)
