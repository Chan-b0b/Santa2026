"""factor 접근법의 핵심 엔진.

풀(pool) = 지금까지 만든 값 전체. F1 = 풀의 두 값으로 명령 1개에 만들 수 있는 값 표.
목표값마다 가장 싼 유도(derivation)를 찾아 싼 것부터 적용한다.

유도 종류
  one    : t 가 F1 에 있음 (1 명령)
  two    : t = x op c, x in F1, c in pool (2 명령)
  pair   : t = x op y, x, y in F1 (3 명령)
  chain3 : t = (x op c) op c', x in F1 (3 명령)
  fsplit : t 의 약수쌍 d*e 를 약수 DP 로 재귀 분해 (핵심: 소인수분해 기반)
  shift  : t -+ c (c in pool) 를 소인수분해해서 fsplit
  horner : 위가 다 실패하면 t = q*x +- r 꼴 사슬을 빔 탐색 (범용 대체 수단)
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
        self.pool = set()
        self.plist = []
        self.F1 = {}
        self.steps = []
        self.facs = facs or {}
        self.cfg = cfg or {}
        self.deadline = deadline
        self.stats = {}
        self.tset = set(targets)
        self.cap = self.cfg.get("cap", 40)        # 동시에 살아 있는 값 수의 연성 한도 (레지스터 48개)
        self.nstart = len(set(start))
        self.live = [self.nstart]                 # live[j] = 단계 j-1 과 j 사이에 살아 있는 값 수 (시작값은 항상 포함)
        self.lastuse = {}                         # 값 -> 마지막으로 쓰인(또는 정의된) 단계 번호
        self.sat = -1                             # live[j] >= cap 인 가장 큰 j
        self.protected = set(start)
        for s in start:
            if s not in self.pool:
                self._add(s)
        self.remaining = sorted(t for t in set(targets) if t not in self.pool)

    # ---------------------------------------------------------------- pool
    def _add(self, v):
        L = self.L
        sd = self.F1.setdefault
        for c in self.plist:
            s = v + c
            if s <= L:
                sd(s, ('+', v, c))
            if v > c:
                sd(v - c, ('-', v, c))
                if v % c == 0:
                    sd(v // c, ('/', v, c))
            else:
                sd(c - v, ('-', c, v))
                if c % v == 0:
                    sd(c // v, ('/', c, v))
            p = v * c
            if p <= L:
                sd(p, ('*', v, c))
        if v + v <= L:
            sd(v + v, ('+', v, v))
        if v * v <= L:
            sd(v * v, ('*', v, v))
        sd(1, ('/', v, v))
        self.pool.add(v)
        self.plist.append(v)

    def apply(self, steps, tag=None):
        n = 0
        for st in steps:
            v = st[0]
            if v in self.pool:
                continue
            i = len(self.steps)
            for u in (st[2], st[3]):
                if u in self.protected:
                    continue
                lu = self.lastuse[u]
                if lu < i:
                    live = self.live
                    for j in range(lu + 1, i + 1):
                        live[j] += 1
                        if live[j] >= self.cap and j > self.sat:
                            self.sat = j
                    self.lastuse[u] = i
            self.steps.append(st)
            self.live.append(self.nstart)
            self.lastuse[v] = i
            self._add(v)
            n += 1
        self._reap()
        if tag:
            self.stats[tag] = self.stats.get(tag, 0) + n
            self.stats[tag + "#"] = self.stats.get(tag + "#", 0) + 1
        return n

    def _reap(self):
        """포화 구간 이전에 마지막으로 쓰인 값은 더는 레지스터에 둘 수 없으므로 풀에서 뺀다."""
        sat = self.sat
        if sat < 0:
            return
        lastuse = self.lastuse
        dead = [u for u in self.plist if u not in self.protected and lastuse[u] < sat]
        if not dead:
            return
        for u in dead:
            self.pool.discard(u)
        keep = [u for u in self.plist if u in self.pool]
        self.plist = []
        self.pool = set()
        self.F1 = {}
        for u in keep:
            self._add(u)
        self.stats["reap"] = self.stats.get("reap", 0) + len(dead)
        self.stats["reap#"] = self.stats.get("reap#", 0) + 1

    def timeup(self):
        return self.deadline is not None and time.time() > self.deadline

    # ------------------------------------------------------------ generic
    def one(self, v):
        if v in self.pool:
            return []
        d = self.F1.get(v)
        if d is not None:
            return [(v,) + d]
        return None

    def two(self, v):
        F1 = self.F1
        L = self.L
        for c in self.plist:
            w = v - c
            if w > 0 and w in F1:
                return [(w,) + F1[w], (v, '+', w, c)]
            w = v + c
            if w <= L and w in F1:
                return [(w,) + F1[w], (v, '-', w, c)]
            w = c - v
            if w > 0 and w in F1:
                return [(w,) + F1[w], (v, '-', c, w)]
            if v % c == 0:
                w = v // c
                if w in F1:
                    return [(w,) + F1[w], (v, '*', w, c)]
            elif c % v == 0:
                w = c // v
                if w in F1:
                    return [(w,) + F1[w], (v, '/', c, w)]
            w = v * c
            if w <= L and w in F1:
                return [(w,) + F1[w], (v, '/', w, c)]
        return None

    def gen2(self, v):
        """비용 2 이하의 범용 유도. (cost, steps) 또는 None."""
        if v in self.pool:
            return 0, []
        d = self.F1.get(v)
        if d is not None:
            return 1, [(v,) + d]
        r = self.two(v)
        if r is not None:
            return 2, r
        return None

    def back1(self, v):
        """v = w op c (c in pool) 인 (w, 마지막 단계) 나열."""
        L = self.L
        out = []
        for c in self.plist:
            w = v - c
            if w > 0:
                out.append((w, (v, '+', w, c)))
            w = v + c
            if w <= L:
                out.append((w, (v, '-', w, c)))
            w = c - v
            if w > 0:
                out.append((w, (v, '-', c, w)))
            if v % c == 0:
                if c > 1 and v != c:
                    out.append((v // c, (v, '*', v // c, c)))
            elif c % v == 0:
                out.append((c // v, (v, '/', c, c // v)))
            w = v * c
            if w <= L and c > 1:
                out.append((w, (v, '/', w, c)))
        return out

    def pair(self, v, divs=None):
        """v = x op y, x, y in F1. 3 명령."""
        F1 = self.F1
        keys = F1.keys()
        L = self.L
        s = {v - x for x in keys if x < v} & keys
        if s:
            y = min(s)
            x = v - y
            return [(x,) + F1[x], (y,) + F1[y], (v, '+', x, y)]
        s = {x - v for x in keys if x > v} & keys
        if s:
            y = min(s)
            x = v + y
            return [(x,) + F1[x], (y,) + F1[y], (v, '-', x, y)]
        if divs is None:
            cand = [x for x in keys if v % x == 0 and x > 1 and x < v]
        else:
            cand = [x for x in divs if x in F1 and x > 1 and x < v]
        for x in cand:
            y = v // x
            if y in F1:
                return [(x,) + F1[x], (y,) + F1[y], (v, '*', x, y)]
        if v * 2 <= L:
            lim = L // v
            for y in keys:
                if 1 < y <= lim and v * y in F1:
                    x = v * y
                    return [(x,) + F1[x], (y,) + F1[y], (v, '/', x, y)]
        return None

    def chain3(self, v):
        for w, last in self.back1(v):
            if w in self.pool:
                continue
            r = self.two(w)
            if r is not None:
                return r + [last]
        return None

    def gen3(self, v, divs=None):
        r = self.gen2(v)
        if r is not None:
            return r
        r = self.pair(v, divs)
        if r is not None:
            return 3, r
        if len(self.plist) <= self.cfg.get("chain3_pool", 24):
            r = self.chain3(v)
            if r is not None:
                return 3, r
        return None

    # ------------------------------------------------------------- factor
    def fsplit(self, v, fac, maxcost, deep=False):
        """v 를 약수쌍으로 재귀 분해. (cost, steps) 또는 None.

        dcost(d) = min(범용 비용(d), min_{d=a*b} dcost(a)+dcost(b)+1) 을 약수 위에서 메모이제이션.
        """
        if fac is None:
            fac = factor(v)
        primes = sorted(fac)
        divs = sorted(divisors_from(fac))
        ndiv = len(divs)
        maxdiv = self.cfg.get("maxdiv", 600)
        memo = {}
        gen = self.gen3 if deep else self.gen2
        pool = self.pool
        F1 = self.F1

        def dcost(d, budget):
            """budget 이하의 유도. 반환 (cost, steps) 또는 None."""
            if d in pool:
                return 0, []
            if budget <= 0:
                return None
            f = F1.get(d)
            if f is not None:
                return 1, [(d,) + f]
            if budget == 1:
                return None
            m = memo.get(d)
            if m is not None and m[0] >= budget:
                return m[1]
            best = gen(d)
            if best is not None and best[0] > budget:
                best = None
            bc = best[0] if best is not None else budget + 1
            if bc > 3 or (bc > 2 and best is None):
                # 곱으로 쪼개기: 비용 >= 3 (a, b 가 둘 다 풀에 있으면 d 는 F1 에 있었을 것)
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
                        c = ra[0] + 1
                        if c < bc:
                            bc = c
                            best = (c, ra[1] + [(d, '*', a, a)])
                        continue
                    rb = dcost(b, bc - 2 - ra[0])
                    if rb is None:
                        continue
                    st = ra[1] + [s for s in rb[1] if s not in ra[1]] + [(d, '*', a, b)]
                    c = len(st)
                    if c < bc:
                        bc = c
                        best = (c, st)
                        if bc <= 3:
                            break
            memo[d] = (budget, best)
            return best

        if ndiv > maxdiv:
            # 약수가 너무 많으면 범용 비용만 본다
            r = gen(v)
            return r if r is not None and r[0] <= maxcost else None
        return dcost(v, maxcost)

    def shift(self, t, maxcost, cands=None):
        """t = w + c, w - c, c - w (c in pool), w 는 fsplit. (cost, steps) 또는 None."""
        best = None
        bc = maxcost + 1
        L = self.L
        for c in (cands if cands is not None else self.plist):
            for w, last in ((t - c, (t, '+', t - c, c)), (t + c, (t, '-', t + c, c)), (c - t, (t, '-', c, c - t))):
                if w <= 1 or w > L or w in self.pool:
                    continue
                r = self.fsplit(w, None, bc - 2)
                if r is not None and r[0] + 1 < bc:
                    bc = r[0] + 1
                    best = (bc, r[1] + [last])
                    if bc <= 3:
                        return best
        return best

    def deep(self, t, maxcost):
        """목표 t 의 가장 싼 유도 (비용 3 이상 구간). (cost, steps, tag) 또는 None."""
        fac = self.facs.get(t)
        if fac is None:
            fac = factor(t)
        divs = None
        best = None
        bc = maxcost + 1
        r = self.pair(t)
        if r is not None:
            return 3, r, "pair"
        if len(self.plist) <= self.cfg.get("chain3_pool", 24):
            r = self.chain3(t)
            if r is not None:
                return 3, r, "chain3"
        r = self.fsplit(t, fac, bc - 1, deep=len(self.plist) <= self.cfg.get("deep_pool", 12))
        if r is not None and r[0] < bc:
            bc = r[0]
            best = (r[0], r[1], "fsplit")
            if bc <= 3:
                return best
        if not self.timeup():
            r = self.shift(t, bc - 1)
            if r is not None and r[0] < bc:
                bc = r[0]
                best = (r[0], r[1], "shift")
        return best

    # ------------------------------------------------------------- horner
    def horner(self, t, beam=8, maxdepth=8):
        """t = q*x +- r 사슬 빔 탐색. x 는 pool/F1, r 은 pool/F1/0. steps 반환 (항상 성공하도록 마지막엔 이진법)."""
        pool = self.pool
        F1 = self.F1
        L = self.L
        xs = [(x, 0) for x in self.plist if x > 1]
        if self.cfg.get("horner_f1", True):
            xs += [(x, 1) for x in F1 if x > 1 and x not in pool]
        best_total = INF
        best_sol = None
        # state: (cost, v, trail)  trail: list of (x, q, r, sign) applied outer->inner
        frontier = [(0, t, ())]
        seen = {t: 0}
        for depth in range(maxdepth):
            cand = {}
            for cost, v, trail in frontier:
                g = self.gen2(v)
                if g is not None:
                    tot = cost + g[0]
                    if tot < best_total:
                        best_total = tot
                        best_sol = (g[1], trail)
                    continue
                if cost + 3 >= best_total:
                    continue
                for x, cx in xs:
                    if x >= v:
                        continue
                    q, r = divmod(v, x)
                    if r == 0:
                        c = cx + 1
                        mv = (x, q, 0, 0)
                    else:
                        if r in pool:
                            c = cx + 2
                            mv = (x, q, r, 1)
                        elif (x - r) in pool and (q + 1) * x <= L:
                            c = cx + 2
                            q += 1
                            mv = (x, q, x - r, -1)
                        elif r in F1:
                            c = cx + 3
                            mv = (x, q, r, 1)
                        elif (x - r) in F1 and (q + 1) * x <= L:
                            c = cx + 3
                            q += 1
                            mv = (x, q, x - r, -1)
                        else:
                            continue
                    nc = cost + c
                    if nc >= best_total:
                        continue
                    old = cand.get(q)
                    if old is None or old[0] > nc:
                        cand[q] = (nc, q, trail + (mv,))
            if not cand:
                break
            items = sorted(cand.values(), key=lambda s: s[0] + s[1].bit_length() / 5.0)
            frontier = items[:beam]
        if best_sol is None:
            return None
        steps = list(best_sol[0])
        trail = best_sol[1]
        # 안쪽(마지막 trail)부터 바깥으로 조립
        cur = None
        vals = []
        # 재구성: trail[i] 는 v_i = q_i * x_i + sign * r_i, v_{i+1} = q_i
        # 가장 안쪽 q 는 gen2 로 만든 값
        seq = list(trail)
        for (x, q, r, sign) in reversed(seq):
            if x not in pool:
                st = (x,) + F1[x]
                if st not in steps:
                    steps.append(st)
            prod = q * x
            steps.append((prod, '*', q, x))
            if sign != 0:
                if r not in pool:
                    st = (r,) + F1[r]
                    if st not in steps:
                        steps.append(st)
                if sign > 0:
                    steps.append((prod + r, '+', prod, r))
                else:
                    steps.append((prod - r, '-', prod, r))
        return steps

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
        bits = bin(t)[3:]
        cur = 1
        for b in bits:
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

    # -------------------------------------------------------------- solve
    def solve(self):
        maxcost = self.cfg.get("maxcost", 6)
        while self.remaining:
            rem = [t for t in self.remaining if t not in self.pool]
            self.remaining = rem
            if not rem:
                break
            progressed = False
            for t in rem:
                d = self.F1.get(t)
                if d is not None and t not in self.pool:
                    self.apply([(t,) + d], "one")
                    progressed = True
            if progressed:
                continue
            for t in rem:
                r = self.two(t)
                if r is not None:
                    self.apply(r, "two")
                    progressed = True
                    break
            if progressed:
                continue
            best = None
            if not self.timeup():
                for t in rem:
                    bound = (best[0] - 1) if best is not None else maxcost
                    if bound < 3:
                        break
                    r = self.deep(t, bound)
                    if r is not None and (best is None or r[0] < best[0]):
                        best = r
                        if r[0] <= 3:
                            break
            if best is not None:
                self.apply(best[1], best[2])
                continue
            t = rem[0]
            st = self.horner(t)
            if st is not None:
                self.apply(st, "horner")
            else:
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
