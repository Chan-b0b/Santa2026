"""factor 접근법 엔진 v2.

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

import sys
import time

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
        self.pmax = self.cfg.get("pmax", 46)
        self.l3_pool = self.cfg.get("l3_pool", 10)
        self.l4_pool = self.cfg.get("l4_pool", 5)
        self.pool = set()
        self.plist = []
        self.F1 = {}
        self.F1new = []
        self.L2 = set()
        self.L3 = None
        self.L4 = None
        self.l2_stale = 0
        self.small = True
        self.steps = []
        self.lastuse = {}
        self.stats = {}
        self.gfacs = facs or {}
        self.facs = {}
        self.tset = set(targets)
        self.protected = set(start)
        self.version = 0
        self.cache = {}
        for s in start:
            if s not in self.pool:
                self.pool.add(s)
                self.plist.append(s)
                self.lastuse[s] = -1
        self.rebuild()
        self.remaining = sorted(t for t in set(targets) if t not in self.pool)

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
        self.rebuild_levels()

    def rebuild_levels(self):
        P = len(self.plist)
        L1 = self.F1.keys()
        self.L2 = self._comb(L1, self.plist)
        self.l2_stale = 0
        self.L3 = None
        self.L4 = None
        self.small = P <= self.l3_pool
        if self.small:
            n1, n2 = len(L1), len(self.L2)
            if n2 * P * 4 + n1 * n1 * 2 <= self.cfg.get("l3_max", 700000):
                L3 = self._comb(self.L2, self.plist)
                L3 |= self._comb(L1, list(L1))
                self.L3 = L3
                if P <= self.l4_pool and len(L3) * P * 4 + n2 * n1 * 4 <= self.cfg.get("l4_max", 1200000):
                    L4 = self._comb(L3, self.plist)
                    L4 |= self._comb(self.L2, list(L1))
                    self.L4 = L4
            else:
                self.small = False

    def _add(self, v):
        """풀에 v 를 넣고 F1, L2 를 증분 갱신한다 (small 모드에서는 나중에 통째로 다시 만든다)."""
        new = self._f1_add(v, self.plist)
        self.pool.add(v)
        self.plist.append(v)
        self.F1new += new
        if self.small:
            return
        L = self.L
        L2 = self.L2
        for c in self.plist:
            L2 |= {x + c for x in new}
            L2 |= {abs(x - c) for x in new}
            lim = L // c
            L2 |= {x * c for x in new if x <= lim}
            if c > 1:
                L2 |= {x // c for x in new if x % c == 0}
            L2 |= {c // x for x in new if x <= c and c % x == 0}
        keys = self.F1.keys()
        L2 |= {x + v for x in keys}
        L2 |= {abs(x - v) for x in keys}
        lim = L // v
        L2 |= {x * v for x in keys if x <= lim}
        if v > 1:
            L2 |= {x // v for x in keys if x % v == 0}
        L2 |= {v // x for x in keys if x <= v and v % x == 0}
        L2.discard(0)

    def evict(self, n, keep):
        lastuse = self.lastuse
        cands = sorted((u for u in self.plist if u not in self.protected and u not in keep), key=lastuse.__getitem__)
        dead = set(cands[:n])
        if not dead:
            return
        self.plist = [u for u in self.plist if u not in dead]
        self.pool -= dead
        self.stats["evict"] = self.stats.get("evict", 0) + len(dead)
        self.l2_stale += len(dead)
        old = self.F1
        self.F1 = {}
        done = []
        for v in self.plist:
            self._f1_add(v, done)
            done.append(v)
        F1 = self.F1
        self.F1new = [k for k in self.F1new if k in F1]
        if self.l2_stale >= self.cfg.get("l2_rebuild", 10) or len(self.plist) <= self.l3_pool:
            self.rebuild_levels()

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
        over = len(self.plist) + len(new) - self.pmax
        if over > 0:
            keep = set()
            for st in new:
                keep.add(st[2])
                keep.add(st[3])
            self.evict(over + self.cfg.get("slack", 3), keep)
        for st in new:
            v, op, a, b = st
            assert a in self.pool and b in self.pool, (st, "피연산자가 풀에 없음")
            i = len(self.steps)
            self.lastuse[a] = i
            self.lastuse[b] = i
            self.lastuse[v] = i
            self.steps.append(st)
            self._add(v)
        if self.small:
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
        L2 = self.L2
        for w, last in self.back1(t):
            if w in L2:
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

    def shift(self, t, maxcost):
        """t = w + c, w - c, c - w (c in pool), w 는 fsplit. (cost, steps) 또는 None."""
        best = None
        bc = maxcost + 1
        L = self.L
        pool = self.pool
        for c in self.plist:
            for w, last in ((t - c, (t, '+', t - c, c)), (t + c, (t, '-', t + c, c)), (c - t, (t, '-', c, c - t))):
                if w <= 1 or w > L or w in pool:
                    continue
                r = self.fsplit(w, self.get_fac(w), bc - 2)
                if r is not None and r[0] + 1 < bc:
                    bc = r[0] + 1
                    best = (bc, r[1] + [last])
                    if bc <= 4:
                        return best
        return best

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
    def _xs(self):
        pool = self.pool
        xs = [(x, 0) for x in self.plist if x > 1]
        xs += [(x, 1) for x in self.F1 if x > 1 and x not in pool]
        if self.small and len(self.L2) <= self.cfg.get("x_l2_max", 30000):
            F1 = self.F1
            xs += [(x, 2) for x in self.L2 if x > 1 and x not in pool and x not in F1]
        return xs

    def decomp_level(self, v, xs, bound):
        """v = q*x + r 또는 q*x - r.  반환 (best, partials)
        best = (total, x, q, r, sign) : q 까지 비용표에 있는 완전한 해
        partials = [(base, q, x, r, sign)] : q 만 비용표에 없는 것"""
        pool = self.pool
        F1 = self.F1
        L2 = self.L2
        L3 = self.L3
        L4 = self.L4
        L = self.L
        cost = self.cost
        best = None
        partials = []
        pap = partials.append
        for x, cx in xs:
            if x >= v:
                continue
            q, r = divmod(v, x)
            if r == 0:
                opts = ((q, 0, 0, cx + 1),)
            else:
                opts = ()
                if r in pool:
                    cr = 0
                elif r in F1:
                    cr = 1
                elif r in L2:
                    cr = 2
                elif L3 is not None and r in L3:
                    cr = 3
                elif L4 is not None and r in L4:
                    cr = 4
                else:
                    cr = INF
                if cr < INF:
                    opts = ((q, r, 1, cx + cr + 2),)
                r2 = x - r
                if (q + 1) * x <= L:
                    if r2 in pool:
                        cr = 0
                    elif r2 in F1:
                        cr = 1
                    elif r2 in L2:
                        cr = 2
                    elif L3 is not None and r2 in L3:
                        cr = 3
                    elif L4 is not None and r2 in L4:
                        cr = 4
                    else:
                        cr = INF
                    if cr < INF:
                        opts += ((q + 1, r2, -1, cx + cr + 2),)
            for qq, rr, sign, base in opts:
                if base >= bound:
                    continue
                cq = cost(qq)
                if cq < INF:
                    tot = base + cq
                    if tot < bound:
                        bound = tot
                        best = (tot, x, qq, rr, sign)
                else:
                    pap((base, qq, x, rr, sign))
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

    def decomp(self, t, maxcost, beam=4, depth=2):
        """t = q*x +- r 를 depth 단계까지. (cost, steps) 또는 None."""
        xs = self._xs()
        bound = maxcost + 1
        best = None   # (total, chain) chain = [(v, x, q, r, sign), ...] 바깥에서 안쪽 순
        frontier = [(0, t, ())]
        for lev in range(depth):
            nxt = []
            for base0, v, chain in frontier:
                b, partials = self.decomp_level(v, xs, bound - base0)
                if b is not None:
                    tot = base0 + b[0]
                    if tot < bound:
                        bound = tot
                        best = (tot, chain + ((v, b[1], b[2], b[3], b[4]),))
                if lev + 1 < depth:
                    for base, q, x, r, sign in partials:
                        if base0 + base + 2 < bound:
                            nxt.append((base0 + base, q, chain + ((v, x, q, r, sign),)))
            if not nxt:
                break
            nxt.sort(key=lambda s: s[0] + s[1].bit_length() / 7.0)
            frontier = nxt[:beam]
        if best is None:
            return None
        chain = best[1]
        qin = chain[-1][2]
        steps = self.derive(qin)
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

    # ------------------------------------------------------------ deep
    def deep(self, t, maxcost):
        """목표 t 의 비용 4 이상 유도 중 가장 싼 것. (cost, steps, tag) 또는 None."""
        best = None
        bc = maxcost + 1
        fac = self.get_fac(t)
        r = self.fsplit(t, fac, bc - 1)
        if r is not None and r[0] < bc:
            bc = r[0]
            best = (r[0], r[1], "fsplit")
            if bc <= 3:
                return best
        if bc > 4:
            r = self.pair12(t)
            if r is not None:
                bc = 4
                best = (4, r, "pair12")
        if bc > 4:
            r = self.shift(t, bc - 1)
            if r is not None and r[0] < bc:
                bc = r[0]
                best = (r[0], r[1], "shift")
        if bc > 4:
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
        maxcost = self.cfg.get("maxcost", 14)
        refresh = self.cfg.get("refresh", 2)
        cache = self.cache
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
            done = False
            L2 = self.L2
            for t in rem:
                if t in L2:
                    r = self.two_loop(t)
                    if r is not None:
                        self.apply(r, "two")
                        done = True
                        break
            if done:
                continue
            # 비용 3
            new = self.F1new
            self.F1new = []
            for t in rem:
                r = self.chain3(t)
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
                if refresh:
                    stale = sorted((cache[t][2], t) for t in rem if t in cache and cache[t][2] != ver)
                    for _, t2 in stale[:refresh]:
                        r2 = self.deep(t2, maxcost)
                        cache[t2] = (r2[0] if r2 else INF, r2, ver)
                bt = None
                tries = 0
                while True:
                    cand = [(cache[t][0], t) for t in rem if t in cache]
                    if not cand:
                        break
                    bcost, t = min(cand)
                    if bcost >= INF:
                        break
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
            # 대체 수단: 가장 작은 목표를 더 깊은 decomp 로, 안 되면 작은 정수를 심고 다시
            t = rem[0]
            if late:
                r = self.decomp(t, 40, beam=2, depth=4)
            else:
                r = self.decomp(t, 40, beam=self.cfg.get("fb_beam", 8), depth=self.cfg.get("fb_depth", 5))
            if r is not None:
                self.apply(r[1], "fallback")
                cache.pop(t, None)
                continue
            if self.stats.get("seed", 0) < self.cfg.get("max_seed", 12) and self.seed():
                continue
            self.apply(self.binary(t), "binary")
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
