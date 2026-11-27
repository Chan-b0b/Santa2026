"""factor 접근법 엔진 v3 (v2 + 큰 풀/생존 구간 관리 + 작은 값 전용 L2).

풀(pool) = 레지스터에 들고 있는 값 (최대 PMAX 개, LRU 로 내보냄).
비용표:  F1 = 풀의 두 값으로 명령 1개에 만드는 값 (정확, 유도 포함)
         L2 = (F1 값) op (풀 값) 으로 명령 2개에 만드는 값의 집합 (상위집합: 오래된 항목이 섞일 수 있어 쓸 때 재검증)
         L3, L4 = 풀이 작을 때만 만드는 3, 4 명령 값 집합
목표값마다 가장 싼 유도를 찾아 싼 것부터 적용한다.

유도 종류
  one/two/chain3/pair : 범용 1~3 명령
  fsplit : t 의 약수쌍 d*e 를 약수 DP 로 재귀 분해, 약수의 비용은 비용표에서 O(1) 조회
  shift  : t -+ c (c in pool) 를 소인수분해해 fsplit   ->  t = d*e +- c
  pair12 : t = x op z, x in F1, z in L2 (4 명령)
  decomp : t = q*x +- r, x, r, q 를 비용표에서 조회. q 가 표에 없으면 빔으로 한 단계 더 내려감
"""
from __future__ import annotations

import random
import sys
import time
from math import isqrt

sys.path.insert(0, "/home/maverick/Santa2026/solvers/factor")
from nt import factor

INF = 99


def divisors_from(fac: dict) -> list:
    ds = [1]
    for p, e in fac.items():
        cur = []
        pe = 1
        for _ in range(e):
            pe *= p
            cur += [d * pe for d in ds]
        ds += cur
    return ds


class Engine:
    def __init__(self, start, targets, limit, facs=None, cfg=None, deadline=None):
        self.L = limit
        self.cfg = cfg or {}
        self.deadline = deadline
        self.cap = self.cfg.get("cap", 40)          # 동시에 살아 있는 값 수의 연성 한도 (레지스터 48개)
        self.pmax = self.cfg.get("pmax", 130)       # 풀 크기의 상한 (표 크기 때문)
        self.l2_pool = self.cfg.get("l2_pool", 28)  # 이 크기 이하면 L2 를 통째로 만든다
        self.l3_pool = self.cfg.get("l3_pool", 10)
        self.l4_pool = self.cfg.get("l4_pool", 5)
        self.M = self.cfg.get("l2s_max", 1 << 20)   # 큰 풀에서는 이 값 이하의 2 명령 값만 표로 둔다
        self.B = self.cfg.get("l2c_max", 0)   # 그리고 (F1 중간 크기 값) op (작은 풀 값) 을 이 값까지 더한다
        self.Mc = self.cfg.get("core_max", 1 << 12)
        self.F1m = []
        sd = self.cfg.get("seed")
        self.rng = random.Random(sd) if sd is not None else None
        self.pool = set()
        self.pool0 = {0}
        self.plist = []
        self.F1 = {}
        self.F1new = []
        self.F1s = []
        self.L2 = set()
        self.L3 = None
        self.L4 = None
        self.mode = 0            # 0: L2 전체(+L3/L4), 1: 작은 값 L2 만
        self.steps = []
        self.lastuse = {}
        self.live = [0]
        self.sat = -1
        self.stats = {}
        self.gfacs = facs or {}
        self.facs = {}
        self.divcache = {}
        self.tset = set(targets)
        self.protected = set(start)
        self.nstart = len(self.protected)
        self.live = [self.nstart]
        self.version = 0
        self.cache = {}
        for s in start:
            if s not in self.pool:
                self.pool.add(s)
                self.pool0.add(s)
                self.plist.append(s)
                self.lastuse[s] = -1
        self.rebuild()
        self.remaining = sorted(t for t in set(targets) if t not in self.pool)
        self.ntargets = len(self.remaining)
        self.t0 = time.time()

    # ------------------------------------------------------------ tables
    def _f1_add(self, v, plist):
        """v 와 plist 의 값들로 만드는 1 명령 값을 F1 에 넣고 새 키 목록을 돌려준다."""
        L = self.L
        F1 = self.F1
        new = []
        ap = new.append
        for c in plist:
            s = v + c
            if s <= L and s not in F1:
                F1[s] = ('+', v, c)
                ap(s)
            if v > c:
                s = v - c
                if s not in F1:
                    F1[s] = ('-', v, c)
                    ap(s)
                if v % c == 0:
                    s = v // c
                    if s not in F1:
                        F1[s] = ('/', v, c)
                        ap(s)
            else:
                s = c - v
                if s not in F1:
                    F1[s] = ('-', c, v)
                    ap(s)
                if c % v == 0:
                    s = c // v
                    if s not in F1:
                        F1[s] = ('/', c, v)
                        ap(s)
            s = v * c
            if s <= L and s not in F1:
                F1[s] = ('*', v, c)
                ap(s)
        s = v + v
        if s <= L and s not in F1:
            F1[s] = ('+', v, v)
            ap(s)
        s = v * v
        if s <= L and s not in F1:
            F1[s] = ('*', v, v)
            ap(s)
        if 1 not in F1:
            F1[1] = ('/', v, v)
            ap(1)
        return new

    def _comb(self, A, B):
        """{a op b : a in A, b in B} (한도 이하). B 가 작은 쪽."""
        L = self.L
        out = set()
        for b in B:
            out |= {a + b for a in A}
            out |= {abs(a - b) for a in A}
            lim = L // b
            out |= {a * b for a in A if a <= lim}
            if b > 1:
                out |= {a // b for a in A if a % b == 0}
            out |= {b // a for a in A if a <= b and b % a == 0}
        out.discard(0)
        return out

    def rebuild(self):
        """F1 과 L2(가능하면 L3, L4)를 처음부터 다시 만든다."""
        plist = self.plist
        self.F1 = {}
        done = []
        for v in plist:
            self._f1_add(v, done)
            done.append(v)
        self.F1new = list(self.F1)
        self.F1s = []
        self.rebuild_levels()

    def _comb_small(self, A, B, M):
        """{a op b <= M : a in A, b in B}."""
        out = set()
        for b in B:
            out |= {a + b for a in A}
            out |= {abs(a - b) for a in A}
            lim = M // b
            out |= {a * b for a in A if a <= lim}
            if b > 1:
                out |= {a // b for a in A if a % b == 0}
            out |= {b // a for a in A if a <= b and b % a == 0}
        out.discard(0)
        return {x for x in out if x <= M}

    def rebuild_levels(self):
        P = len(self.plist)
        L1 = self.F1.keys()
        self.L3 = None
        self.L4 = None
        if P > self.l2_pool:
            self.mode = 1
            M = self.M
            self.F1s = [x for x in L1 if x <= M]
            self.L2 = self._comb_small(self.F1s, [c for c in self.plist if c <= M], M)
            B = self.B
            self.F1m = [x for x in L1 if M < x <= B]
            if B > M:
                self._core_add(self.F1m, [c for c in self.plist if c <= self.Mc])
            return
        self.mode = 0
        self.L2 = self._comb(L1, self.plist)
        if P <= self.l3_pool:
            n1, n2 = len(L1), len(self.L2)
            if n2 * P * 4 + n1 * n1 * 2 <= self.cfg.get("l3_max", 700000):
                L3 = self._comb(self.L2, self.plist)
                L3 |= self._comb(L1, list(L1))
                self.L3 = L3
                if P <= self.l4_pool and len(L3) * P * 4 + n2 * n1 * 4 <= self.cfg.get("l4_max", 1200000):
                    L4 = self._comb(L3, self.plist)
                    L4 |= self._comb(self.L2, list(L1))
                    self.L4 = L4

    def _core_add(self, xs, cs):
        """L2 에 {x + c, x - c, x * c, x / c : x in xs (중간 크기 F1 값), c in cs (작은 풀 값)} 을 더한다."""
        if not xs:
            return
        L2 = self.L2
        B = self.B
        for c in cs:
            L2 |= {x + c for x in xs}
            L2 |= {x - c for x in xs}
            if c > 1:
                lim = B // c
                L2 |= {x * c for x in xs if x <= lim}
                L2 |= {x // c for x in xs if x % c == 0}

    def _add(self, v):
        """풀에 v 를 넣고 F1 을 증분 갱신한다. mode 1 이면 작은 값 L2 도 증분 갱신한다."""
        new = self._f1_add(v, self.plist)
        self.pool.add(v)
        self.pool0.add(v)
        self.plist.append(v)
        self.F1new += new
        if self.mode == 0:
            return
        M = self.M
        ns = [x for x in new if x <= M]
        L2 = self.L2
        if ns:
            add = set()
            for c in self.plist:
                if c > M:
                    continue
                add |= {x + c for x in ns}
                add |= {abs(x - c) for x in ns}
                lim = M // c
                add |= {x * c for x in ns if x <= lim}
                if c > 1:
                    add |= {x // c for x in ns if x % c == 0}
                add |= {c // x for x in ns if x <= c and c % x == 0}
            L2 |= {x for x in add if x <= M}
            self.F1s += ns
        if v <= M:
            keys = self.F1s
            add = {x + v for x in keys}
            add |= {abs(x - v) for x in keys}
            lim = M // v
            add |= {x * v for x in keys if x <= lim}
            if v > 1:
                add |= {x // v for x in keys if x % v == 0}
            add |= {v // x for x in keys if x <= v and v % x == 0}
            L2 |= {x for x in add if x <= M}
        B = self.B
        if B > M:
            nm = [x for x in new if M < x <= B]
            if nm:
                self._core_add(nm, [c for c in self.plist if c <= self.Mc])
                self.F1m += nm
            if v <= self.Mc:
                self._core_add(self.F1m, [v])
        L2.discard(0)

    def _drop(self, dead):
        """dead 값들을 풀에서 빼고 표를 다시 만든다."""
        self.plist = [u for u in self.plist if u not in dead]
        self.pool -= dead
        self.pool0 -= dead
        old_new = self.F1new
        self.rebuild()
        F1 = self.F1
        self.F1new = [k for k in old_new if k in F1]

    def _reap(self):
        """포화 구간 이전에 마지막으로 쓰인 값은 더는 레지스터에 둘 수 없으므로 풀에서 뺀다. 풀이 너무 크면 오래된 것부터 뺀다."""
        lastuse = self.lastuse
        dead = set()
        sat = self.sat
        if sat >= 0:
            dead = {u for u in self.plist if u not in self.protected and lastuse[u] < sat}
        over = len(self.plist) - len(dead) - self.pmax
        if over > 0:
            cands = sorted((u for u in self.plist if u not in self.protected and u not in dead), key=lastuse.__getitem__)
            dead |= set(cands[:over + 8])
        if dead:
            self.stats["reap"] = self.stats.get("reap", 0) + len(dead)
            self.stats["reap#"] = self.stats.get("reap#", 0) + 1
            self._drop(dead)
            return True
        return False

    def apply(self, steps, tag=None):
        pool = self.pool
        new = []
        seen = set()
        for st in steps:
            v = st[0]
            if v in pool or v in seen:
                continue
            seen.add(v)
            new.append(st)
        if not new:
            return 0
        live = self.live
        lastuse = self.lastuse
        prot = self.protected
        cap = self.cap
        for st in new:
            v, op, a, b = st
            assert a in self.pool and b in self.pool, (st, "피연산자가 풀에 없음")
            i = len(self.steps)
            for u in (a, b):
                if u in prot:
                    continue
                lu = lastuse[u]
                if lu < i:
                    for j in range(lu + 1, i + 1):
                        live[j] += 1
                        if live[j] >= cap and j > self.sat:
                            self.sat = j
                    lastuse[u] = i
            lastuse[v] = i
            self.steps.append(st)
            live.append(self.nstart)
            self._add(v)
        if not self._reap():
            if self.mode == 0:
                self.rebuild_levels()
        self.version += 1
        if tag:
            self.stats[tag] = self.stats.get(tag, 0) + len(new)
            self.stats[tag + "#"] = self.stats.get(tag + "#", 0) + 1
        return len(new)

    def timeup(self):
        return self.deadline is not None and time.time() > self.deadline

    # ------------------------------------------------------------ costs
    def cost(self, w):
        if w in self.pool:
            return 0
        if w in self.F1:
            return 1
        if w in self.L2:
            return 2
        L3 = self.L3
        if L3 is not None:
            if w in L3:
                return 3
            L4 = self.L4
            if L4 is not None and w in L4:
                return 4
        return INF

    def two_loop(self, v):
        F1 = self.F1
        L = self.L
        pool = self.pool
        for c in self.plist:
            w = v - c
            if w > 0 and w in F1 and w not in pool:
                return [(w,) + F1[w], (v, '+', w, c)]
            w = v + c
            if w <= L and w in F1 and w not in pool:
                return [(w,) + F1[w], (v, '-', w, c)]
            w = c - v
            if w > 0 and w in F1 and w not in pool:
                return [(w,) + F1[w], (v, '-', c, w)]
            if v % c == 0:
                w = v // c
                if w in F1 and w not in pool:
                    return [(w,) + F1[w], (v, '*', w, c)]
            elif c % v == 0:
                w = c // v
                if w in F1 and w not in pool:
                    return [(w,) + F1[w], (v, '/', c, w)]
            w = v * c
            if w <= L and w in F1 and w not in pool:
                return [(w,) + F1[w], (v, '/', w, c)]
        return None

    def back1(self, v):
        """v = w op c (c in pool) 인 (w, 마지막 단계) 나열."""
        L = self.L
        out = []
        ap = out.append
        for c in self.plist:
            w = v - c
            if w > 0:
                ap((w, (v, '+', w, c)))
            w = v + c
            if w <= L:
                ap((w, (v, '-', w, c)))
            w = c - v
            if w > 0:
                ap((w, (v, '-', c, w)))
            if v % c == 0:
                if c > 1 and v != c:
                    ap((v // c, (v, '*', v // c, c)))
            elif c % v == 0:
                ap((c // v, (v, '/', c, c // v)))
            w = v * c
            if w <= L and c > 1:
                ap((w, (v, '/', w, c)))
        return out

    def pair(self, v, xs=None):
        """v = x op y, x, y in F1 (3 명령). xs 를 주면 x 또는 y 가 xs 에 있는 경우만 본다."""
        F1 = self.F1
        keys = F1.keys()
        L = self.L
        pool = self.pool
        if xs is None:
            xs = keys
            full = True
        else:
            full = False

        def mk(x, y, op, a, b):
            if x in pool or y in pool:
                return None
            return [(x,) + F1[x], (y,) + F1[y], (v, op, a, b)]

        s = {v - x for x in xs if x < v} & keys
        for y in s:
            r = mk(v - y, y, '+', v - y, y)
            if r:
                return r
        s = {x - v for x in xs if x > v} & keys
        for y in s:
            r = mk(v + y, y, '-', v + y, y)
            if r:
                return r
        if not full:
            s = {x + v for x in xs} & keys
            for x in s:
                r = mk(x, x - v, '-', x, x - v)
                if r:
                    return r
        for x in xs:
            if 1 < x < v and v % x == 0:
                y = v // x
                if y in F1:
                    r = mk(x, y, '*', x, y)
                    if r:
                        return r
        lim = L // v
        if lim >= 2:
            for y in xs:
                if 1 < y <= lim and v * y in F1:
                    r = mk(v * y, y, '/', v * y, y)
                    if r:
                        return r
            if not full:
                for x in xs:
                    if x > v and x % v == 0 and x // v in F1:
                        r = mk(x, x // v, '/', x, x // v)
                        if r:
                            return r
        return None

    def derive(self, w):
        """비용표에 있는 값 w 의 실제 유도 (steps). 오래된 항목이면 None."""
        if w in self.pool:
            return []
        f = self.F1.get(w)
        if f is not None:
            return [(w,) + f]
        if w in self.L2:
            r = self.two_loop(w)
            if r is not None:
                return r
        if self.L3 is not None and w in self.L3:
            r = self.derive3(w)
            if r is not None:
                return r
        if self.L4 is not None and w in self.L4:
            r = self.derive4(w)
            if r is not None:
                return r
        return None

    def derive3(self, w):
        L2 = self.L2
        for w2, last in self.back1(w):
            if w2 in L2:
                r = self.two_loop(w2)
                if r is not None:
                    return r + [last]
        return self.pair(w)

    def _inv(self, w, x):
        L = self.L
        out = []
        if w > x:
            out.append((w - x, (w, '+', w - x, x)))
        if w + x <= L:
            out.append((w + x, (w, '-', w + x, x)))
        if x > w:
            out.append((x - w, (w, '-', x, x - w)))
        if x > 1 and w % x == 0 and w != x:
            out.append((w // x, (w, '*', w // x, x)))
        if x > 1 and w * x <= L:
            out.append((w * x, (w, '/', w * x, x)))
        if x > w and x % w == 0:
            out.append((x // w, (w, '/', x, x // w)))
        return out

    def derive4(self, w):
        L3 = self.L3
        for w2, last in self.back1(w):
            if w2 in L3:
                r = self.derive3(w2)
                if r is not None:
                    return r + [last]
        F1 = self.F1
        L2 = self.L2
        pool = self.pool
        for x, f in F1.items():
            if x in pool:
                continue
            for w2, last in self._inv(w, x):
                if w2 in L2:
                    r = self.two_loop(w2)
                    if r is not None:
                        return [(x,) + f] + r + [last]
        return None

    # ------------------------------------------------------------ cost 3
    def chain3(self, t):
        """t = (x op c) op c' (x in F1). mode 0 은 L2 조회, mode 1 은 집합 연산으로 일괄 검사."""
        b1 = self.back1(t)
        if self.mode == 0:
            L2 = self.L2
            for w, last in b1:
                if w in L2:
                    r = self.two_loop(w)
                    if r is not None:
                        return r + [last]
            return None
        keys = self.F1.keys()
        pool = self.pool
        W = {w for w, _ in b1 if w not in pool}
        L = self.L
        hit = set()
        for z in self.plist:
            h = {w - z for w in W} & keys
            if h:
                hit |= {x + z for x in h}
            h = {w + z for w in W} & keys
            if h:
                hit |= {x - z for x in h}
            h = {z - w for w in W} & keys
            if h:
                hit |= {z - x for x in h}
            if z > 1:
                h = {w // z for w in W if w % z == 0} & keys
                if h:
                    hit |= {x * z for x in h}
        if not hit:
            return None
        for w, last in b1:
            if w in hit:
                r = self.two_loop(w)
                if r is not None:
                    return r + [last]
        return None

    # ------------------------------------------------------------ factor
    def get_fac(self, w):
        f = self.gfacs.get(w)
        if f is None:
            f = self.facs.get(w)
            if f is None:
                f = factor(w)
                self.facs[w] = f
        return f

    def fsplit(self, v, fac, maxcost):
        """v 를 약수쌍으로 재귀 분해. (cost, steps) 또는 None.  약수 비용은 비용표 조회."""
        if maxcost < 1:
            return None
        c0 = self.cost(v)
        if c0 <= maxcost:
            r = self.derive(v)
            if r is not None:
                return len(r), r
        if maxcost < 3:
            return None
        divs = sorted(divisors_from(fac))
        if len(divs) > self.cfg.get("maxdiv", 400):
            return None
        cost = self.cost
        memo = {}

        def dcost(d, budget):
            """(cost, plan) 또는 None. plan = ('g', d) | ('m', d, a, b, plan_a, plan_b)"""
            c = cost(d)
            if c <= 2 or c <= budget:
                return (c, ('g', d)) if c <= budget else None
            if budget < 3:
                return None
            m = memo.get(d)
            if m is not None:
                if m[1] is not None:
                    return m[1] if m[1][0] <= budget else None
                if m[0] >= budget:
                    return None
            best = None
            bc = budget + 1
            for a in divs:
                if a * a > d:
                    break
                if a == 1 or d % a:
                    continue
                b = d // a
                ra = dcost(a, bc - 2)
                if ra is None:
                    continue
                if a == b:
                    c2 = ra[0] + 1
                    if c2 < bc:
                        bc = c2
                        best = (c2, ('m', d, a, a, ra[1], None))
                    continue
                rb = dcost(b, bc - 2 - ra[0])
                if rb is None:
                    continue
                c2 = ra[0] + rb[0] + 1
                if c2 < bc:
                    bc = c2
                    best = (c2, ('m', d, a, b, ra[1], rb[1]))
                    if bc <= 3:
                        break
            memo[d] = (budget, best)
            return best

        r = dcost(v, maxcost)
        if r is None:
            return None
        steps = []
        ok = True

        def build(plan):
            nonlocal ok
            if plan[0] == 'g':
                st = self.derive(plan[1])
                if st is None:
                    ok = False
                    return
                steps.extend(s for s in st if s not in steps)
            else:
                _, d, a, b, pa, pb = plan
                build(pa)
                if pb is not None:
                    build(pb)
                steps.append((d, '*', a, b))

        build(r[1])
        if not ok:
            return None
        seen = set()
        out = []
        for s in steps:
            if s[0] in seen or s[0] in self.pool:
                continue
            seen.add(s[0])
            out.append(s)
        return len(out), out

    def get_divs(self, w):
        d = self.divcache.get(w)
        if d is None:
            d = sorted(divisors_from(self.get_fac(w)))
            if len(d) > 2000:
                d = d[:1000] + d[-1000:]
            self.divcache[w] = d
        return d

    def shift(self, t, maxcost):
        """t = a*b + c, a*b - c, c - a*b (c in pool). a, b 의 비용은 비용표 조회.
        a 가 풀에 있고 b 가 표에 없으면 b = (x op y) +- z 꼴인지 집합 연산으로 일괄 검사한다 (비용 4)."""
        bc = maxcost + 1
        best = None
        L = self.L
        wmax = min(L, 1 << self.cfg.get("shift_maxbits", 46))   # 이보다 큰 수는 두 약수가 모두 쌀 가능성이 없어 분해하지 않는다
        pool = self.pool
        cost = self.cost
        cands = {}
        for c in self.plist:
            for w, last in ((t - c, (t, '+', t - c, c)), (t + c, (t, '-', t + c, c)), (c - t, (t, '-', c, c - t))):
                if w <= 3 or w > wmax or w in pool:
                    continue
                divs = self.get_divs(w)
                n = len(divs)
                for i in range(1, (n + 1) // 2):
                    a = divs[i]
                    ca = cost(a)
                    if ca + 2 >= bc:
                        continue
                    b = w // a
                    if a == b:
                        tot = ca + 2
                    else:
                        cb = cost(b)
                        if cb >= INF:
                            if ca == 0 and bc > 4:
                                cands[b] = (w, a, last)
                            continue
                        tot = ca + cb + 2
                    if tot < bc:
                        bc = tot
                        best = (w, a, b, last)
        if bc > 4 and cands and self.mode == 1:
            keys = self.F1.keys()
            B = set(cands)
            hit = set()
            for z in self.plist:
                h = {b - z for b in B} & keys
                if h:
                    hit |= {x + z for x in h}
                h = {b + z for b in B} & keys
                if h:
                    hit |= {x - z for x in h}
                h = {z - b for b in B} & keys
                if h:
                    hit |= {z - x for x in h}
            for b in hit:
                r = self.two_loop(b)
                if r is not None:
                    w, a, last = cands[b]
                    st = r + [(w, '*', a, b), last]
                    return 4, st
        if best is None:
            return None
        w, a, b, last = best
        sa = self.derive(a)
        if sa is None:
            return None
        if a == b:
            st = sa + [(w, '*', a, a), last]
        else:
            sb = self.derive(b)
            if sb is None:
                return None
            st = sa + [x for x in sb if x not in sa] + [(w, '*', a, b), last]
        seen = set()
        out = []
        for x in st:
            if x[0] in seen or x[0] in pool:
                continue
            seen.add(x[0])
            out.append(x)
        return len(out), out

    # ------------------------------------------------------------ pair12
    def pair12(self, t):
        """t = x op z, x in F1, z in L2 (4 명령)."""
        F1 = self.F1
        L2 = self.L2
        keys = F1.keys()
        pool = self.pool
        L = self.L
        for z in {t - x for x in keys if x < t} & L2:
            x = t - z
            if x in pool:
                continue
            r = self.two_loop(z)
            if r is not None:
                return [(x,) + F1[x]] + r + [(t, '+', x, z)]
        for z in {x - t for x in keys if x > t} & L2:
            x = t + z
            if x in pool:
                continue
            r = self.two_loop(z)
            if r is not None:
                return [(x,) + F1[x]] + r + [(t, '-', x, z)]
        lim = L - t
        for z in {x + t for x in keys if x <= lim} & L2:
            x = z - t
            if x in pool:
                continue
            r = self.two_loop(z)
            if r is not None:
                return [(x,) + F1[x]] + r + [(t, '-', z, x)]
        lim = L // t
        if lim >= 2:
            for z in {x * t for x in keys if 1 < x <= lim} & L2:
                x = z // t
                if x in pool:
                    continue
                r = self.two_loop(z)
                if r is not None:
                    return [(x,) + F1[x]] + r + [(t, '/', z, x)]
        return None

    # ------------------------------------------------------------ decomp
    def decomp_level(self, v, bound, want=True):
        """v = q*x + r 또는 q*x - r.  반환 (best, partials)
        best = (total, x, q, r, sign) : q 까지 비용표에 있는 완전한 해
        partials = [(base, q, x, r, sign)] : q 만 비용표에 없는 것"""
        pool = self.pool
        pool0 = self.pool0
        F1 = self.F1
        L2 = self.L2
        L3 = self.L3
        L4 = self.L4
        L = self.L
        cost = self.cost
        best = None
        partials = []
        pap = partials.append
        srcs = [(self.plist, 0), (F1.keys(), 1)]
        if self.mode == 0 and len(L2) <= self.cfg.get("x_l2_max", 30000):
            srcs.append((L2, 2))
        for src, cx in srcs:
            if cx + 1 >= bound:
                break
            if L3 is None:
                fl = [x for x in src if x < v and ((r := v % x) in pool0 or r in F1 or r in L2)]
                ce = [x for x in src if x < v and ((r := x - v % x) in pool or r in F1 or r in L2)]
            elif L4 is None:
                fl = [x for x in src if x < v and ((r := v % x) in pool0 or r in F1 or r in L2 or r in L3)]
                ce = [x for x in src if x < v and ((r := x - v % x) in pool or r in F1 or r in L2 or r in L3)]
            else:
                fl = [x for x in src if x < v and ((r := v % x) in pool0 or r in F1 or r in L2 or r in L3 or r in L4)]
                ce = [x for x in src if x < v and ((r := x - v % x) in pool or r in F1 or r in L2 or r in L3 or r in L4)]
            for x in fl:
                if x < 2 or (cx and x in pool) or (cx == 2 and x in F1):
                    continue
                q, r = divmod(v, x)
                if r == 0:
                    base = cx + 1
                    sign = 0
                else:
                    base = cx + cost(r) + 2
                    sign = 1
                if base >= bound:
                    continue
                cq = cost(q)
                if cq < INF:
                    tot = base + cq
                    if tot < bound:
                        bound = tot
                        best = (tot, x, q, r, sign)
                elif want:
                    pap((base, q, x, r, sign))
            for x in ce:
                if x < 2 or (cx and x in pool) or (cx == 2 and x in F1):
                    continue
                q, r = divmod(v, x)
                if r == 0:
                    continue
                q += 1
                if q * x > L:
                    continue
                r = x - r
                base = cx + cost(r) + 2
                if base >= bound:
                    continue
                cq = cost(q)
                if cq < INF:
                    tot = base + cq
                    if tot < bound:
                        bound = tot
                        best = (tot, x, q, r, -1)
                elif want:
                    pap((base, q, x, r, -1))
        return best, partials

    def _decomp_steps(self, v, x, q, r, sign, qsteps):
        """v = q*x + sign*r 의 steps. qsteps 는 q 의 유도. 실패하면 None."""
        sx = self.derive(x)
        if sx is None:
            return None
        steps = list(qsteps)
        steps += [s for s in sx if s not in steps]
        prod = q * x
        steps.append((prod, '*', q, x))
        if sign != 0:
            sr = self.derive(r)
            if sr is None:
                return None
            steps += [s for s in sr if s not in steps]
            if sign > 0:
                steps.append((v, '+', prod, r))
            else:
                steps.append((v, '-', prod, r))
        return steps

    def gen3(self, v):
        """표에 없는 값 v 의 3 명령 유도 (F1 op F1). steps 또는 None."""
        if v < 2:
            return None
        return self.pair(v)

    def decomp(self, t, maxcost, beam=4, depth=2, beta=7.0):
        """t = q*x +- r 를 depth 단계까지. (cost, steps) 또는 None."""
        bound = maxcost + 1
        best = None   # (total, chain, qsteps) chain = [(v, x, q, r, sign), ...] 바깥에서 안쪽 순
        frontier = [(0, t, ())]
        k3 = self.cfg.get("k3", 0) if self.L3 is None else 0
        for lev in range(depth):
            nxt = []
            for base0, v, chain in frontier:
                b, partials = self.decomp_level(v, bound - base0, lev + 1 < depth or bool(k3))
                if b is not None:
                    tot = base0 + b[0]
                    if tot < bound:
                        bound = tot
                        best = (tot, chain + ((v, b[1], b[2], b[3], b[4]),), None)
                if k3 and partials and lev < self.cfg.get("k3_lev", 1):
                    # q 가 표에 없어도 F1 op F1 로 3 명령에 되는지 싼 것 몇 개만 확인
                    partials.sort()
                    tried = 0
                    for base, q, x, r, sign in partials:
                        if base0 + base + 3 >= bound or tried >= k3:
                            break
                        tried += 1
                        st = self.gen3(q)
                        if st is not None:
                            bound = base0 + base + 3
                            best = (bound, chain + ((v, x, q, r, sign),), st)
                if lev + 1 < depth:
                    for base, q, x, r, sign in partials:
                        if base0 + base + 2 < bound:
                            nxt.append((base0 + base, q, chain + ((v, x, q, r, sign),)))
            if not nxt:
                break
            nxt.sort(key=lambda s: s[0] + s[1].bit_length() / beta)
            frontier = nxt[:beam]
        if best is None:
            return None
        chain = best[1]
        qin = chain[-1][2]
        steps = best[2] if best[2] is not None else self.derive(qin)
        if steps is None:
            return None
        for v, x, q, r, sign in reversed(chain):
            steps = self._decomp_steps(v, x, q, r, sign, steps)
            if steps is None:
                return None
        seen = set()
        out = []
        for s in steps:
            if s[0] in seen or s[0] in self.pool:
                continue
            seen.add(s[0])
            out.append(s)
        return len(out), out

    # ------------------------------------------------------------ mitm (mode 0)
    def _addpair(self, t, A, B):
        """t = a + b, a - b, b - a (a in A, b in B). steps 또는 None."""
        L = self.L
        for b in {t - a for a in A if a < t} & B:
            sa = self.derive(t - b)
            sb = self.derive(b)
            if sa is not None and sb is not None and sa and sb:
                return sa + [x for x in sb if x not in sa] + [(t, '+', t - b, b)]
        for b in {a - t for a in A if a > t} & B:
            sa = self.derive(t + b)
            sb = self.derive(b)
            if sa is not None and sb is not None and sa and sb:
                return sa + [x for x in sb if x not in sa] + [(t, '-', t + b, b)]
        lim = L - t
        for b in {a + t for a in A if a <= lim} & B:
            sa = self.derive(b - t)
            sb = self.derive(b)
            if sa is not None and sb is not None and sa and sb:
                return sa + [x for x in sb if x not in sa] + [(t, '-', b, b - t)]
        return None

    def mitm(self, t, maxcost):
        """mode 0 전용 범용 양방향 탐색. 풀 값으로 뒤로 k 단계 간 값이 비용표에 있는지,
        그리고 t 가 두 표 값의 합/차인지 본다. (cost, steps) 또는 None."""
        bc = maxcost + 1
        best = None
        pool = self.pool
        cost = self.cost
        F1k = self.F1.keys()
        L2, L3, L4 = self.L2, self.L3, self.L4
        # 뒤로 k 단계
        frontier = {t: ()}
        maxfront = self.cfg.get("mitm_front", 60000)
        k = 0
        P6 = 6 * len(self.plist)
        while True:
            for w, tail in frontier.items():
                c = cost(w)
                if c < INF and k + c < bc:
                    st = self.derive(w)
                    if st is not None:
                        tot = len(st) + k
                        if tot < bc:
                            bc = tot
                            best = (tot, st + list(reversed(tail)))
            if k + 2 >= bc or len(frontier) * P6 > maxfront:
                break
            nxt = {}
            for w, tail in frontier.items():
                for w2, last in self.back1(w):
                    if w2 not in nxt and w2 not in pool:
                        nxt[w2] = tail + (last,)
            frontier = nxt
            k += 1
        # 합/차 쌍: (i, j) 수준, 비용 i + j + 1
        levels = {1: F1k, 2: L2, 3: L3, 4: L4}
        for i, j in ((2, 2), (1, 3), (2, 3), (1, 4), (3, 3), (2, 4)):
            if i + j + 1 >= bc:
                break
            A, B = levels[i], levels[j]
            if A is None or B is None or len(A) > self.cfg.get("mitm_pair", 250000):
                continue
            st = self._addpair(t, A, B)
            if st is not None:
                seen = set()
                out = []
                for x in st:
                    if x[0] in seen or x[0] in pool:
                        continue
                    seen.add(x[0])
                    out.append(x)
                if len(out) < bc:
                    bc = len(out)
                    best = (bc, out)
        return best

    # ------------------------------------------------------------ hub
    def hubs(self, rem):
        """여러 목표가 '풀 값 하나와의 연산 1번'으로 닿는 공통 중간값 h 를 찾는다.
        반환: [(k, h, [(t, last_step), ...])]  k >= 2, k 큰 순."""
        pool = self.pool
        cnt = {}
        for t in rem:
            seen = set()
            for h, last in self.back1(t):
                if h in pool or h in seen:
                    continue
                seen.add(h)
                cnt.setdefault(h, []).append((t, last))
            if t % 2 == 0:
                h = t // 2
                if h not in pool and h not in seen:
                    seen.add(h)
                    cnt.setdefault(h, []).append((t, (t, '+', h, h)))
            h = isqrt(t)
            if h * h == t and h not in pool and h not in seen:
                cnt.setdefault(h, []).append((t, (t, '*', h, h)))
        out = [(len(lst), h, lst) for h, lst in cnt.items() if len(lst) >= 2]
        out.sort(key=lambda x: (-x[0], x[1]))
        return out

    def try_hub(self, rem, maxavg, hubs=None, search=0):
        """평균 비용 (c(h) + k) / k 가 maxavg 이하인 가장 좋은 hub 를 적용한다. 적용했으면 True."""
        if hubs is None:
            hubs = self.hubs(rem)
        best = None
        tset = self.tset
        nsearch = 0
        for k, h, lst in hubs:
            self_t = 1 if (h in tset and h not in self.pool) else 0   # h 자신이 목표면 그만큼 이득
            c = self.cost(h)
            st = None
            if c >= INF and search and nsearch < search:
                nsearch += 1
                st = self.gen3(h)
                if st is None and self.mode == 0:
                    r = self.mitm(h, 4)
                    if r is not None:
                        st = r[1]
                if st is not None:
                    c = len(st)
            if c >= INF:
                continue
            avg = (c + k) / (k + self_t)
            if avg <= maxavg and (best is None or avg < best[0]):
                if st is None:
                    st = self.derive(h)
                    if st is None:
                        continue
                best = (avg, h, st, lst)
        if best is None:
            return False
        avg, h, st, lst = best
        steps = list(st) + [last for _, last in lst]
        self.apply(steps, "hub")
        return True

    # ------------------------------------------------------------ deep
    def deep(self, t, maxcost, light=False):
        """목표 t 의 비용 4 이상 유도 중 가장 싼 것. (cost, steps, tag) 또는 None.
        light: 큰 목표값의 재평가에서는 거의 맞지 않는 chain3/pair12/shift 를 건너뛴다."""
        best = None
        bc = maxcost + 1
        light = light and self.mode == 1 and t.bit_length() > self.cfg.get("light_bits", 46)
        if self.mode == 1:
            r = None if light else self.chain3(t)
            if r is not None:
                return 3, r, "chain3"
        else:
            r = self.mitm(t, bc - 1)
            if r is not None and r[0] < bc:
                bc = r[0]
                best = (r[0], r[1], "mitm")
                if bc <= 4:
                    return best
        fac = self.get_fac(t)
        r = self.fsplit(t, fac, bc - 1)
        if r is not None and r[0] < bc:
            bc = r[0]
            best = (r[0], r[1], "fsplit")
            if bc <= 4:
                return best
        if bc > 4 and not light:
            r = self.pair12(t)
            if r is not None:
                bc = 4
                best = (4, r, "pair12")
        if bc > 4 and not light:
            r = self.shift(t, bc - 1)
            if r is not None and r[0] < bc:
                bc = r[0]
                best = (r[0], r[1], "shift")
        if bc > 4:
            if self.mode == 0:
                r = self.decomp(t, bc - 1, beam=self.cfg.get("beam0", 6), depth=self.cfg.get("depth0", 4), beta=self.cfg.get("beta0", 5.0))
            else:
                r = self.decomp(t, bc - 1, beam=self.cfg.get("beam", 4), depth=self.cfg.get("depth", 2))
            if r is not None and r[0] < bc:
                bc = r[0]
                best = (r[0], r[1], "decomp")
        return best

    def binary(self, t):
        """최후 수단: 1 을 만들고 이진법으로 쌓는다."""
        steps = []
        have = set(self.pool)
        if 1 not in have:
            a = self.plist[0]
            steps.append((1, '/', a, a))
            have.add(1)
        if t == 1:
            return steps
        if 2 not in have:
            steps.append((2, '+', 1, 1))
            have.add(2)
        cur = 1
        for b in bin(t)[3:]:
            nxt = cur * 2
            if nxt not in have:
                steps.append((nxt, '*', cur, 2))
                have.add(nxt)
            cur = nxt
            if b == '1':
                nxt = cur + 1
                if nxt not in have:
                    steps.append((nxt, '+', cur, 1))
                    have.add(nxt)
                cur = nxt
        return steps

    def seed(self):
        """풀에 없는 가장 작은 양의 정수를 하나 넣는다 (decomp 가 막혔을 때)."""
        k = 1
        while k in self.pool:
            k += 1
        f = self.F1.get(k)
        if f is None:
            return False
        self.apply([(k,) + f], "seed")
        return True

    # ------------------------------------------------------------- solve
    def solve(self):
        maxcost = self.cfg.get("maxcost", 18)
        refresh = self.cfg.get("refresh", 2)
        alpha = self.cfg.get("alpha", 0.16)
        jitter = self.cfg.get("jitter", 0.3)
        cache = self.cache
        rng = self.rng
        for d in self.cfg.get("preseed", ()):
            # 씨앗(여러 목표값에 걸친 공통 약수)을 먼저 만들어 풀에 넣는다
            if d in self.pool or d < 2 or d > self.L:
                continue
            c = self.cost(d)
            if c < INF:
                st = self.derive(d)
                r = (len(st), st) if st is not None else None
            else:
                r = self.deep(d, 14)
                if r is None:
                    r = self.decomp(d, 40, beam=6, depth=6, beta=4.0)
            if r is not None:
                self.apply(r[1], "preseed")
        while True:
            pool = self.pool
            rem = [t for t in self.remaining if t not in pool]
            self.remaining = rem
            if not rem:
                break
            F1 = self.F1
            hit = [t for t in rem if t in F1]
            if hit:
                for t in hit:
                    if t not in self.pool and t in self.F1:
                        self.apply([(t,) + self.F1[t]], "one")
                continue
            order = rem
            if rng is not None:
                order = list(rem)
                rng.shuffle(order)
            done = False
            L2 = self.L2
            mode = self.mode
            usehub = self.cfg.get("hub", 1) and len(rem) >= 2 and (mode == 0 or self.cfg.get("hub", 1) >= 2)
            hubs = self.hubs(rem) if usehub else []
            if hubs and self.try_hub(rem, 1.5, hubs):
                continue
            for t in order:
                if mode == 1 or t in L2:
                    r = self.two_loop(t)
                    if r is not None:
                        self.apply(r, "two")
                        done = True
                        break
            if done:
                continue
            if hubs and self.try_hub(rem, 2.0, hubs):
                continue
            # 비용 3
            new = self.F1new
            self.F1new = []
            for t in order:
                r = self.chain3(t) if mode == 0 else None
                if r is not None:
                    self.F1new = new + self.F1new
                    self.apply(r, "chain3")
                    done = True
                    break
                r = self.pair(t, new)
                if r is not None:
                    self.F1new = new + self.F1new
                    self.apply(r, "pair")
                    done = True
                    break
            if done:
                continue
            if hubs and self.try_hub(rem, self.cfg.get("hub_avg", 2.75), hubs, search=self.cfg.get("hub_search", 6)):
                continue
            # 비용 4 이상: 게으른 갱신
            ver = self.version
            late = self.timeup()
            if not late:
                for t in rem:
                    if t not in cache:
                        r = self.deep(t, maxcost)
                        cache[t] = (r[0] if r else INF, r, ver)
                        if self.timeup():
                            break
                # 시간 배분: 남은 목표값 비율보다 시간이 많이 지났으면 재평가 수를 줄인다 (마감 뒤의 싼 모드로 떨어지지 않게)
                r_eff = refresh
                if refresh > 1 and self.deadline is not None:
                    ft = (time.time() - self.t0) / max(self.deadline - self.t0, 1e-9)
                    fd = 1.0 - len(rem) / max(self.ntargets, 1)
                    if ft > 0.8 * fd + 0.15:
                        r_eff = 1
                    elif ft > 0.8 * fd + 0.05:
                        r_eff = max(1, refresh // 3)
                if r_eff:
                    stale = sorted((cache[t][2], t) for t in rem if t in cache and cache[t][2] != ver)
                    for _, t2 in stale[:r_eff]:
                        r2 = self.deep(t2, maxcost, light=True)
                        cache[t2] = (r2[0] if r2 else INF, r2, ver)
                        if self.timeup():
                            break
                bt = None
                tries = 0
                while True:
                    if rng is None:
                        cand = [(cache[t][0] - alpha * t.bit_length(), t) for t in rem if t in cache and cache[t][0] < INF]
                    else:
                        cand = [(cache[t][0] - alpha * t.bit_length() + jitter * rng.random(), t) for t in rem if t in cache and cache[t][0] < INF]
                    if not cand:
                        break
                    m = min(cand)
                    t = m[-1]
                    if cache[t][2] == ver:
                        bt = t
                        break
                    r = self.deep(t, maxcost)
                    cache[t] = (r[0] if r else INF, r, ver)
                    tries += 1
                    if tries > 6 or self.timeup():
                        if r is not None:
                            bt = t
                        break
                if bt is not None:
                    r = cache[bt][1]
                    self.apply(r[1], r[2])
                    cache.pop(bt, None)
                    continue
            # 대체 수단: 작은 목표 몇 개를 더 깊은 decomp 로 풀어 보고 가장 싼 것을 쓴다. 안 되면 작은 정수를 심고 다시.
            fbb = 2 if late else self.cfg.get("fb_beam", 6)
            beta = self.cfg.get("fb_beta", 4.0)
            nseed = self.stats.get("seed", 0)
            ktry = 1 if late else self.cfg.get("fb_k", 4)
            best = None
            for depth in (4, 9, 18):
                for t in rem[:ktry]:
                    r = self.decomp(t, (best[0] - 1) if best else 90, beam=fbb, depth=depth, beta=beta)
                    if r is not None and (best is None or r[0] < best[0]):
                        best = (r[0], r[1], t)
                if best is not None:
                    break
                if depth == 4 and nseed < self.cfg.get("seed1", 3) and self.seed():
                    best = "seeded"
                    break
            if best == "seeded":
                continue
            if best is not None:
                self.apply(best[1], "fallback")
                cache.pop(best[2], None)
                continue
            if nseed < self.cfg.get("max_seed", 10) and self.seed():
                continue
            self.apply(self.binary(rem[0]), "binary")
        return self.steps


def emit(start, steps, nreg=48):
    """값 단위 단계 목록을 레지스터 프로그램으로 바꾼다. 살아 있는 값이 nreg 를 넘으면 None."""
    last = {}
    for i, (v, op, a, b) in enumerate(steps):
        last[a] = i
        last[b] = i
    reg = {}
    free = []
    for i, s in enumerate(start):
        if s in reg or s not in last:
            free.append(i)
        else:
            reg[s] = i
    free += list(range(len(start), nreg))
    free.reverse()
    prog = []
    for i, (v, op, a, b) in enumerate(steps):
        ra, rb = reg[a], reg[b]
        if last[a] == i:
            free.append(reg.pop(a))
        if b != a and last[b] == i:
            free.append(reg.pop(b))
        if not free:
            return None
        d = free.pop()
        prog.append([op, ra, rb, d])
        if v in last and last[v] > i:
            reg[v] = d
        else:
            free.append(d)
    return prog
