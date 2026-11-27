#!/usr/bin/env python3
"""relate 솔버: 목표값 사이의 유도 관계(t = k*x + e, t = (x+a)*k + b, t = x op y ...)를
풀(pool)에서 점진적으로 찾아 가장 싼 목표부터 만든다.

값 표현은 SSA(값 하나 = 명령 하나)이고, 끝에서 죽은 코드 제거와 레지스터 배정을 한다.
"""
import sys
import time
import random
from bisect import bisect_left

sys.path.insert(0, "/home/maverick/Santa2026/core")
from verify import check_program  # noqa: E402

INF = 10 ** 9


class Invalid(Exception):
    pass


class Solver:
    def __init__(self, pz, cfg=None):
        cfg = cfg or {}
        self.cfg = cfg
        self.pz = pz
        self.L = pz.limit
        self.QN = cfg.get("QN", 40)            # A2 를 만드는 작은 값 개수 상한
        self.QCAP = cfg.get("QCAP", 1 << 20)   # 작은 값의 크기 상한
        self.XCAP = min(self.L, cfg.get("XCAP", 1 << 30))
        self.ACAP = min(self.L, cfg.get("ACAP", 1 << 34))
        self.KCAP = cfg.get("KCAP", 1 << 17)
        self.ECAP = cfg.get("ECAP", 1 << 20)
        self.W = cfg.get("W", 6)               # 범용 빔 폭
        self.KEYMAX = cfg.get("KEYMAX", 90)
        self.cap = cfg.get("cap")              # 보존하는 값 개수 상한 (None 이면 무제한)
        self.temps = []
        self.evictable = {}
        self.clock = 0
        self.rng = random.Random(cfg.get("rseed", 0))
        self.noise = cfg.get("noise", 0.0)
        self.rootpick = cfg.get("rootpick", 1)
        self.genmode = cfg.get("gen", 2)
        self.rootK = cfg.get("rootK", 1)
        self.rootKstop = cfg.get("rootKstop", 3)
        self.rootKslack = cfg.get("rootKslack", 1)
        self.gcache = {}
        self.nder = 0
        self.W2 = cfg.get("W2", 24)
        self.s1depth = cfg.get("s1depth", 0)
        self.s1mmax = cfg.get("s1mmax", 1 << 13)
        self.cshift = cfg.get("cshift", 3)
        self.nshift = cfg.get("nshift", 6)
        self.tl = cfg.get("tl", 8.0)
        self.relmax = cfg.get("relmax", 3)
        self.relfrac = cfg.get("relfrac", 0.2)
        self.t0 = time.time()
        self.vals = []
        self.defs = []
        self.pool = {}      # 값 -> SSA 번호 (모든 만든 값)
        self.C = {}         # 값 -> 0(풀) / 1(L1)
        self.plist = []     # 핵심 값 (L1 짝짓기 대상)
        self.L1 = {}        # 값 -> (op, a, b)
        self.Q = []
        self.Qset = set()
        self.L1Q = {}       # Q 끼리 한 번 연산한 값 -> True
        self.A2 = {}        # 값 -> (op, a, b)  (a, b 중 하나는 L1Q, 하나는 Q)
        self.X3 = {}        # ac3 로 찾은 값 -> (op, a, b)
        self.X3c = {}
        self.remaining = set(pz.targets) - set(pz.start)
        # 보조 목표: 해독한 정수/작은 값. 진짜 목표보다 싸게 만들어질 때만 만들고, 안 쓰이면 finish 가 지운다.
        self.aux = set(v for v in cfg.get("aux", ()) if 1 < v <= pz.limit) - set(pz.start) - set(pz.targets)
        self.auxmax = cfg.get("auxmax", 5)
        self.remaining |= self.aux
        self.cand = {t: {} for t in self.remaining}
        self.mitm = {}
        self.bases = None
        self.fast = False
        self.log = []
        for s in pz.start:
            self.add_value(s, None, True)

    # ------------------------------------------------------------------ 풀 관리
    def add_value(self, v, d, key):
        self.vals.append(v)
        self.defs.append(d)
        if v in self.pool:
            return
        idx = len(self.vals) - 1
        self.pool[v] = idx
        self.C[v] = 0
        if v in self.remaining:
            self.remaining.discard(v)
            self.cand.pop(v, None)
            self.mitm.pop(v, None)
            key = True
        if self.fast:
            return
        if v <= self.QCAP:
            key = True
        if not key or len(self.plist) >= self.KEYMAX:
            self.temps.append(v)
            return
        self.bases = None
        L = self.L
        L1 = self.L1
        C = self.C
        plist = self.plist
        plist.append(v)
        newx = []
        for p in plist:
            s = v + p
            if s <= L and s not in C:
                C[s] = 1
                L1[s] = ("+", v, p)
                newx.append(s)
            m = v * p
            if m <= L and m not in C:
                C[m] = 1
                L1[m] = ("*", v, p)
                newx.append(m)
            if v > p:
                s = v - p
                if s not in C:
                    C[s] = 1
                    L1[s] = ("-", v, p)
                    newx.append(s)
                if v % p == 0:
                    s = v // p
                    if s not in C:
                        C[s] = 1
                        L1[s] = ("/", v, p)
                        newx.append(s)
            elif p > v:
                s = p - v
                if s not in C:
                    C[s] = 1
                    L1[s] = ("-", p, v)
                    newx.append(s)
                if p % v == 0:
                    s = p // v
                    if s not in C:
                        C[s] = 1
                        L1[s] = ("/", p, v)
                        newx.append(s)
            else:
                if 1 not in C:
                    C[1] = 1
                    L1[1] = ("/", v, v)
                    newx.append(1)
        if v <= self.QCAP and len(self.Q) < self.QN:
            self._add_small(v)
        elif d is not None:
            self.evictable[v] = self.clock
        if self.remaining:
            self.scan([v], 0)
            if newx:
                self.scan(newx, 1)

    def _pairs(self, a, b, cap):
        """a, b 한 번 연산의 결과 (값, op, 왼쪽, 오른쪽) 목록."""
        out = []
        s = a + b
        if s <= cap:
            out.append((s, "+", a, b))
        m = a * b
        if m <= cap:
            out.append((m, "*", a, b))
        if a > b:
            out.append((a - b, "-", a, b))
            if a % b == 0:
                out.append((a // b, "/", a, b))
        elif b > a:
            out.append((b - a, "-", b, a))
            if b % a == 0:
                out.append((b // a, "/", b, a))
        else:
            out.append((1, "/", a, a))
        return out

    def _add_small(self, v):
        """작은 값 v 를 Q 에 넣고 A2 (= L1Q op Q, 명령 2개짜리 값) 를 갱신한다.
        A2[값] = 그 값을 만든 L1Q 쪽 피연산자. 나머지 피연산자는 쓸 때 a2rec 로 되찾는다."""
        Q = self.Q
        L1Q = self.L1Q
        A2 = self.A2
        XCAP = self.XCAP
        ACAP = self.ACAP
        pairs = self._pairs
        old = list(L1Q)
        Q.append(v)
        self.Qset.add(v)
        newxq = []
        for q in Q:
            for val, op, a, b in pairs(v, q, XCAP):
                if val not in L1Q:
                    L1Q[val] = True
                    newxq.append(val)
        upd = A2.update
        if old:
            upd({x + v: x for x in old if x + v <= ACAP})
            if v > 1:
                upd({x * v: x for x in old if x * v <= ACAP})
                upd({x // v: x for x in old if x % v == 0})
            upd({x - v: x for x in old if x > v})
            upd({v - x: x for x in old if x < v})
            upd({v // x: x for x in old if x > 1 and v % x == 0})
        for q in Q:
            if not newxq:
                break
            upd({x + q: x for x in newxq if x + q <= ACAP})
            if q > 1:
                upd({x * q: x for x in newxq if x * q <= ACAP})
                upd({x // q: x for x in newxq if x % q == 0})
            upd({x - q: x for x in newxq if x > q})
            upd({q - x: x for x in newxq if x < q})
            upd({q // x: x for x in newxq if x > 1 and q % x == 0})

    def a2rec(self, val, x):
        """A2 값 val 과 그 L1Q 피연산자 x 로부터 (op, a, b) 를 되찾는다."""
        Qs = self.Qset
        if val > x and val - x in Qs:
            return ("+", x, val - x)
        if x > val and x - val in Qs:
            return ("-", x, x - val)
        if val + x in Qs:
            return ("-", val + x, x)
        if val % x == 0 and val // x in Qs:
            return ("*", x, val // x)
        if x % val == 0 and x // val in Qs:
            return ("/", x, x // val)
        if val * x in Qs:
            return ("/", val * x, x)
        raise Invalid

    # ------------------------------------------------------------------ 비용과 트리
    def ac(self, v):
        """v 를 만드는 데 드는 명령 수 (0, 1, 2) 또는 None."""
        c = self.C.get(v)
        if c is not None:
            return c
        if v in self.A2:
            return 2
        return None

    def tree(self, v):
        if v in self.pool:
            return v
        d = self.L1.get(v)
        if d is not None:
            return (d[0], d[1], d[2])
        x = self.A2.get(v)
        if x is not None:
            d = self.a2rec(v, x)
        else:
            d = self.X3.get(v)
            if d is None:
                raise Invalid
        return (d[0], self.tree(d[1]), self.tree(d[2]))

    def end_derivation_keep(self, v):
        """v 를 핵심 값으로 승격한 뒤 유도를 끝낸다."""
        if v in self.temps:
            self.temps.remove(v)
            idx = self.pool.pop(v)
            del self.C[v]
            # 같은 SSA 번호로 다시 등록 (핵심 값)
            self.vals.pop() if False else None
            self._promote(v, idx)
        self.end_derivation()

    def _promote(self, v, idx):
        d = self.defs[idx]
        # add_value 는 새 SSA 를 만들므로, 기록을 임시로 떼었다가 같은 정의로 다시 넣는다
        self.pool[v] = idx
        self.C[v] = 0
        save_vals, save_defs = self.vals, self.defs
        self.vals, self.defs = [], []
        del self.pool[v]
        del self.C[v]
        self.add_value(v, d, True)
        self.vals, self.defs = save_vals, save_defs
        self.pool[v] = idx
        if v in self.temps:
            self.temps.remove(v)

    def end_derivation(self):
        """유도 하나가 끝난 뒤: 임시값을 풀에서 빼고, 보존 한도를 넘으면 오래 안 쓴 값을 버린다."""
        self.clock += 1
        temps = self.temps
        if self.cap is None:
            temps.clear()
            return
        if temps:
            pool = self.pool
            C = self.C
            L1 = self.L1
            for v in temps:
                if v in pool:
                    del pool[v]
                    if v in L1:
                        C[v] = 1
                    else:
                        del C[v]
            temps.clear()
            self.X3.clear()
            self.X3c.clear()
        ev = self.evictable
        while len(self.plist) > self.cap and ev:
            v = min(ev, key=ev.get)
            self.evict(v)

    def evict(self, v):
        del self.evictable[v]
        self.plist.remove(v)
        del self.pool[v]
        C = self.C
        L1 = self.L1
        dead = [val for val, d in L1.items() if d[1] == v or d[2] == v]
        for val in dead:
            del L1[val]
            if C.get(val) == 1:
                del C[val]
        if v in L1:
            C[v] = 1
        else:
            del C[v]
        self.X3.clear()
        self.X3c.clear()
        self.bases = None

    def ac3(self, q):
        """q 를 명령 3개 이하로 만드는 법을 찾는다 (L1 op 풀, L1Q op L1, A2 op 풀). 비용 또는 None."""
        c = self.ac(q)
        if c is not None:
            return c
        if q in self.X3:
            return self.X3c[q]
        C = self.C
        A2 = self.A2
        L = self.L
        best = None
        rec = None
        for p in self.plist:
            if p < q:
                u = q - p
                c = C.get(u)
                if c is not None:
                    best = 2
                    rec = ("+", u, p)
                    break
                if best is None and u in A2:
                    best = 3
                    rec = ("+", u, p)
                if q % p == 0:
                    u = q // p
                    c = C.get(u)
                    if c is not None:
                        best = 2
                        rec = ("*", u, p)
                        break
                    if best is None and u in A2:
                        best = 3
                        rec = ("*", u, p)
            elif p > q:
                u = p - q
                c = C.get(u)
                if c is not None:
                    best = 2
                    rec = ("-", p, u)
                    break
                if best is None and u in A2:
                    best = 3
                    rec = ("-", p, u)
            u = q + p
            if u <= L:
                c = C.get(u)
                if c is not None:
                    best = 2
                    rec = ("-", u, p)
                    break
                if best is None and u in A2:
                    best = 3
                    rec = ("-", u, p)
        if best is None:
            for x in self.L1Q:
                if x < q:
                    u = q - x
                    if u in C:
                        best = 3
                        rec = ("+", u, x)
                        break
                    if q % x == 0:
                        u = q // x
                        if u in C:
                            best = 3
                            rec = ("*", u, x)
                            break
                elif x > q:
                    u = x - q
                    if u in C:
                        best = 3
                        rec = ("-", x, u)
                        break
                u = q + x
                if u <= L and u in C:
                    best = 3
                    rec = ("-", u, x)
                    break
        if best is not None:
            self.X3[q] = rec
            self.X3c[q] = best
        return best

    def sim(self, tr, new):
        """트리를 계산해 값을 돌려준다. 풀에 없는 새 값은 new 에 모은다. 불법이면 Invalid."""
        if type(tr) is int:
            return tr
        op = tr[0]
        a = self.sim(tr[1], new)
        b = self.sim(tr[2], new)
        if op == "+":
            v = a + b
        elif op == "-":
            v = a - b
        elif op == "*":
            v = a * b
        else:
            if b == 0 or a % b:
                raise Invalid
            v = a // b
        if v < 1 or v > self.L:
            raise Invalid
        if v not in self.pool:
            new.add(v)
        return v

    def tree_cost(self, tr):
        new = set()
        try:
            self.sim(tr, new)
        except Invalid:
            return None
        return len(new)

    def emit_tree(self, tr, key=True):
        if type(tr) is int:
            return tr
        a = self.emit_tree(tr[1], key)
        b = self.emit_tree(tr[2], key)
        return self.emit(tr[0], a, b, key)

    def emit(self, op, a, b, key=True):
        if op == "+":
            v = a + b
        elif op == "-":
            v = a - b
        elif op == "*":
            v = a * b
        else:
            if a % b:
                raise Invalid
            v = a // b
        if v < 1 or v > self.L:
            raise Invalid
        ev = self.evictable
        if a in ev:
            ev[a] = self.clock
        if b in ev:
            ev[b] = self.clock
        if v in self.pool:
            if v in ev:
                ev[v] = self.clock
            return v
        self.add_value(v, (op, self.pool[a], self.pool[b]), key)
        return v

    # ------------------------------------------------------------------ 관계 탐색
    def scan(self, xs, cx):
        C = self.C
        L = self.L
        KCAP = self.KCAP
        ECAP = self.ECAP
        mitm = self.mitm
        for t in self.remaining:
            lo = t // KCAP
            hi = t * KCAP
            cd = self.cand[t]
            mb = mitm.get(t)
            mbc = mb[0] if mb else 99
            for x in xs:
                if x < t:
                    d = t - x
                    c = C.get(d)
                    if c is not None and cx + c + 1 < mbc:
                        mbc = cx + c + 1
                        mitm[t] = (mbc, "+", x, d)
                    r = t % x
                    if r == 0:
                        u = t // x
                        c = C.get(u)
                        if c is not None and cx + c + 1 < mbc:
                            mbc = cx + c + 1
                            mitm[t] = (mbc, "*", x, u)
                        if x >= lo:
                            cd[x] = 0
                    elif x >= lo and (r <= ECAP or x - r <= ECAP):
                        if r * 8 < x or (x - r) * 8 < x:
                            cd[x] = 0
                elif x > t:
                    d = x - t
                    c = C.get(d)
                    if c is not None and cx + c + 1 < mbc:
                        mbc = cx + c + 1
                        mitm[t] = (mbc, "-", x, d)
                    r = x % t
                    if r == 0:
                        u = x // t
                        c = C.get(u)
                        if c is not None and cx + c + 1 < mbc:
                            mbc = cx + c + 1
                            mitm[t] = (mbc, "/", x, u)
                        if x <= hi:
                            cd[x] = 1
                    elif x <= hi and (r <= ECAP or t - r <= ECAP):
                        if r * 8 < t or (t - r) * 8 < t:
                            cd[x] = 1
                else:
                    if cx < mbc:
                        mbc = cx
                        mitm[t] = (cx, None, x, None)
                    continue
                s = t + x
                if s <= L:
                    c = C.get(s)
                    if c is not None and cx + c + 1 < mbc:
                        mbc = cx + c + 1
                        mitm[t] = (mbc, "-", s, x)
                    p = t * x
                    if p <= L:
                        c = C.get(p)
                        if c is not None and cx + c + 1 < mbc:
                            mbc = cx + c + 1
                            mitm[t] = (mbc, "/", p, x)
            if len(cd) > 120:
                self._prune(t)

    def _prune(self, t):
        cd = self.cand[t]
        sc = []
        for x, kind in cd.items():
            if kind == 0:
                k, e = divmod(t, x)
                if e > x - e:
                    k += 1
                    e = x - e
            else:
                k, e = divmod(x, t)
                if e > t - e:
                    k += 1
                    e = t - e
            sc.append((k.bit_length() + e.bit_length(), x))
        sc.sort()
        self.cand[t] = {x: cd[x] for _, x in sc[:60]}

    def eval_affine(self, t, x, kind):
        """(비용, 트리) 또는 None."""
        ac = self.ac
        cx = self.C.get(x)
        if cx is None:
            return None
        xt = self.tree(x)
        best = None
        if kind == 0:
            k, e = divmod(t, x)
            if e > x - e:
                k += 1
                e -= x
            ck = 0 if k == 1 else ac(k)
            if ck is None:
                return None
            ae = abs(e)
            ce = 0 if e == 0 else ac(ae)
            if ce is not None:
                cost = cx + (k != 1) * (1 + ck) + (e != 0) * (1 + ce)
                tr = xt if k == 1 else ("*", xt, self.tree(k))
                if e > 0:
                    tr = ("+", tr, self.tree(e))
                elif e < 0:
                    tr = ("-", tr, self.tree(-e))
                best = (cost, tr)
            if k != 1 and e != 0:
                a0 = e // k
                for a in (a0, a0 + 1):
                    if a == 0:
                        continue
                    b = e - k * a
                    ca = ac(abs(a))
                    if ca is None:
                        continue
                    cb = 0 if b == 0 else ac(abs(b))
                    if cb is None:
                        continue
                    cost = cx + 2 + ca + ck + (b != 0) * (1 + cb)
                    if best is None or cost < best[0]:
                        tr = ("+", xt, self.tree(a)) if a > 0 else ("-", xt, self.tree(-a))
                        tr = ("*", tr, self.tree(k))
                        if b > 0:
                            tr = ("+", tr, self.tree(b))
                        elif b < 0:
                            tr = ("-", tr, self.tree(-b))
                        best = (cost, tr)
        else:
            k, e = divmod(x, t)
            if e > t - e:
                k += 1
                e -= t
            ck = 0 if k == 1 else ac(k)
            if ck is None:
                return None
            ae = abs(e)
            ce = 0 if e == 0 else ac(ae)
            if ce is not None:
                cost = cx + (k != 1) * (1 + ck) + (e != 0) * (1 + ce)
                tr = xt
                if e > 0:
                    tr = ("-", tr, self.tree(e))
                elif e < 0:
                    tr = ("+", tr, self.tree(-e))
                if k != 1:
                    tr = ("/", tr, self.tree(k))
                best = (cost, tr)
            if k != 1 and e != 0:
                a0 = e // k
                for a in (a0, a0 + 1):
                    if a == 0:
                        continue
                    b = e - k * a
                    ca = ac(abs(a))
                    if ca is None:
                        continue
                    cb = 0 if b == 0 else ac(abs(b))
                    if cb is None:
                        continue
                    cost = cx + 2 + ca + ck + (b != 0) * (1 + cb)
                    if best is None or cost < best[0]:
                        tr = xt
                        if b > 0:
                            tr = ("-", tr, self.tree(b))
                        elif b < 0:
                            tr = ("+", tr, self.tree(-b))
                        tr = ("/", tr, self.tree(k))
                        tr = ("-", tr, self.tree(a)) if a > 0 else ("+", tr, self.tree(-a))
                        best = (cost, tr)
        return best

    def best_rel(self, t):
        """목표 t 의 가장 싼 관계 유도 (비용, 트리) 또는 None."""
        best = None
        m = self.mitm.get(t)
        if m is not None:
            c, op, a, b = m
            try:
                if op is None:
                    best = (c, self.tree(a))
                else:
                    best = (c, (op, self.tree(a), self.tree(b)))
            except Invalid:
                del self.mitm[t]
                m = None
        cd = self.cand[t]
        for x, kind in cd.items():
            try:
                r = self.eval_affine(t, x, kind)
            except Invalid:
                r = None
            if r is not None and (best is None or r[0] < best[0]):
                best = r
        if best is not None:
            c = self.tree_cost(best[1])
            if c is None:
                # 한도 초과 등: 느리지만 안전한 경로로 다시 고른다
                best = None
                opts = []
                if m is not None:
                    c0, op, a, b = m
                    tr = self.tree(a) if op is None else (op, self.tree(a), self.tree(b))
                    opts.append(tr)
                for x, kind in cd.items():
                    try:
                        r = self.eval_affine(t, x, kind)
                    except Invalid:
                        r = None
                    if r is not None:
                        opts.append(r[1])
                for tr in opts:
                    c = self.tree_cost(tr)
                    if c is not None and (best is None or c < best[0]):
                        best = (c, tr)
            else:
                best = (c, best[1])
        return best

    # ------------------------------------------------------------------ 범용 구성 (빔 Horner)
    def _bases(self):
        if self.bases is None:
            b = [(m, 0) for m in self.plist if m >= 2]
            C = self.C
            for m in self.L1Q:
                if m >= 2 and C.get(m) != 0:
                    b.append((m, 1))
            self.bases = b
            self.l1sorted = None
        return self.bases

    def est(self, q):
        c = self.ac(q)
        if c is not None:
            return c
        return 1 + 0.23 * q.bit_length()

    def generic(self, t, W=None):
        """t 를 만드는 (비용, 트리). 실패하면 None."""
        W = W or self.W
        ac = self.ac
        L = self.L
        bases = self._bases()
        if self.noise:
            self.rng.shuffle(bases)
        plist = self.plist
        best = None   # (total, q, chain)
        beam = {t: (0, None)}
        for level in range(80):
            nxt = {}
            bestc = best[0] if best else INF
            for q, (cost, chain) in beam.items():
                if cost + 1 >= bestc and level > 0:
                    continue
                c3 = self.ac3(q)
                if c3 is not None:
                    if cost + c3 < bestc:
                        bestc = cost + c3
                        best = (bestc, q, chain)
                    continue
                # Horner: q = qq*m + r
                for m, cm in bases:
                    if m > q:
                        continue
                    qq, r = divmod(q, m)
                    if r == 0:
                        opts = ((qq, 0, cm + 1),)
                    else:
                        opts = []
                        cr = ac(r)
                        if cr is not None:
                            opts.append((qq, r, cm + 2 + cr))
                        r2 = m - r
                        cr = ac(r2)
                        if cr is not None and (qq + 1) * m <= L:
                            opts.append((qq + 1, -r2, cm + 2 + cr))
                    for nq, rr, step in opts:
                        if nq == 1:
                            tot = cost + step - 1
                            if tot < bestc:
                                bestc = tot
                                best = (tot, 1, (0, m, rr, chain))
                            continue
                        nc = cost + step
                        cq = ac(nq)
                        if cq is not None:
                            tot = nc + cq
                            if tot < bestc:
                                bestc = tot
                                best = (tot, nq, (0, m, rr, chain))
                            continue
                        o = nxt.get(nq)
                        if o is None or nc < o[0]:
                            nxt[nq] = (nc, (0, m, rr, chain))
                # 나머지 재귀: q = x*k + e (k 는 싼 값, e 를 다시 만든다)
                for x in plist:
                    if x > q or x < 2:
                        continue
                    k, e = divmod(q, x)
                    for kk, ee in ((k, e), (k + 1, e - x)):
                        if ee == 0:
                            continue
                        ae = abs(ee)
                        if ae.bit_length() + 6 > q.bit_length():
                            continue
                        if kk == 1:
                            ck = -1
                        else:
                            ck = ac(kk)
                            if ck is None:
                                continue
                        if ee < 0 and kk * x > L:
                            continue
                        nc = cost + 2 + ck
                        ce = ac(ae)
                        if ce is not None:
                            tot = nc + ce
                            if tot < bestc:
                                bestc = tot
                                best = (tot, ae, (1, x, kk, ee > 0, chain))
                            continue
                        o = nxt.get(ae)
                        if o is None or nc < o[0]:
                            nxt[ae] = (nc, (1, x, kk, ee > 0, chain))
            if not nxt:
                break
            if self.noise:
                rnd = self.rng.random
                nz = self.noise
                items = [(c + self.est(q) + nz * rnd(), q) for q, (c, ch) in nxt.items() if c + 1 < bestc]
            else:
                items = [(c + self.est(q), q) for q, (c, ch) in nxt.items() if c + 1 < bestc]
            items.sort()
            beam = {q: nxt[q] for _, q in items[:W]}
            if not beam:
                break
        if best is None:
            return None
        tot, q, chain = best
        if q == 1 and chain is not None and chain[0] == 0 and self.ac(1) != 0:
            tr = None
        else:
            tr = self.tree(q)
        while chain is not None:
            if chain[0] == 0:
                _, m, rr, chain = chain
                tr = self.tree(m) if tr is None else ("*", tr, self.tree(m))
                if rr > 0:
                    tr = ("+", tr, self.tree(rr))
                elif rr < 0:
                    tr = ("-", tr, self.tree(-rr))
            else:
                _, x, kk, pos, chain = chain
                big = x if kk == 1 else ("*", x, self.tree(kk))
                tr = ("+", big, tr) if pos else ("-", big, tr)
        c = self.tree_cost(tr)
        if c is None:
            return None
        return (c, tr)

    def f2find(self, v):
        """v = (L1 값) op (풀 값) 꼴(명령 2개)을 찾는다. (op, a, b) 또는 None."""
        C = self.C
        L = self.L
        for p in self.plist:
            if p < v:
                u = v - p
                if u in C:
                    return ("+", u, p)
                if v % p == 0:
                    u = v // p
                    if u in C:
                        return ("*", u, p)
            elif p > v:
                u = p - v
                if u in C:
                    return ("-", p, u)
            u = v + p
            if u <= L and u in C:
                return ("-", u, p)
        return None

    def generic2(self, t, W=None):
        """비용 순서(균일 비용) 역방향 탐색. 비용 단계마다 가장 작은 값 W 개만 펼친다.

        이동: H  v = c*m + d      (m 풀 값; d 는 v 와 m 으로 합동인 풀 값이면 2, L1 값이면 3, A2 값이면 4, 0 이면 1)
              N3 v = m*k ± c      (k 가 싼 값, 나머지 c 를 이어서 만든다)
              N1 v = x ± c        (x 는 v 에 가장 가까운 풀/L1 값)
              N2 v = x*q ± c      (x 는 v/q 에 가장 가까운 풀/L1 값)
        끝: 풀(0), L1(1), A2 또는 L1 op 풀(2).
        """
        W = W or self.W2
        c0 = self.ac(t)
        if c0 is not None:
            return (c0, self.tree(t))
        C = self.C
        A2 = self.A2
        L = self.L
        pl = sorted(self.plist)
        mults = [m for m in pl if m >= 2]
        resid = {}
        for m in mults:
            d = {}
            for v in pl:
                r = v % m
                if r and r not in d:
                    d[r] = v
            resid[m] = d
        allv = sorted(C)
        nall = len(allv)
        s1m = sorted(x for x in self.L1Q if 2 <= x <= self.s1mmax and C.get(x) == 1) if self.s1depth >= 0 else []
        s1depth = self.s1depth
        cshift = self.cshift
        nshift = self.nshift
        node = {t: (0, None, None)}
        levels = {0: [t]}
        best = 90
        bestleaf = None

        def add(c, cost, par, step):
            nonlocal best, bestleaf
            o = node.get(c)
            if o is not None and o[0] <= cost:
                return
            cc = C.get(c)
            if cc is None and c in A2:
                cc = 2
            if cc is not None:
                if cost + cc < best:
                    node[c] = (cost, par, step)
                    best = cost + cc
                    bestleaf = c
                return
            if cost + 2 < best:
                node[c] = (cost, par, step)
                lv = levels.get(cost)
                if lv is None:
                    levels[cost] = [c]
                else:
                    lv.append(c)

        g = 0
        while g + 1 < best:
            lv = levels.get(g)
            if lv:
                cand = sorted(set(v for v in lv if node[v][0] == g))[:W]
                g1 = g + 1
                g2 = g + 2
                g3 = g + 3
                for v in cand:
                    if g1 >= best:
                        break
                    if g2 < best:
                        rec = self.f2find(v)
                        if rec is not None:
                            self.X3[v] = rec
                            self.X3c[v] = 2
                            best = g2
                            bestleaf = v
                            continue
                    lim = v >> cshift
                    for m in mults:
                        if m >= v:
                            break
                        q, r = divmod(v, m)
                        if r == 0:
                            add(q, g1, v, (0, m, 0))
                            continue
                        rd = resid[m]
                        d = rd.get(r)
                        if d is not None and d < v:
                            add((v - d) // m, g2, v, (0, m, d))
                        else:
                            cr = C.get(r)
                            if cr is None and r in A2:
                                cr = 2
                            if cr is not None:
                                add(q, g2 + cr, v, (0, m, r))
                        r2 = m - r
                        d = rd.get(r2)
                        if d is not None:
                            if v + d <= L:
                                add((v + d) // m, g2, v, (0, m, -d))
                        else:
                            cr = C.get(r2)
                            if cr is None and r2 in A2:
                                cr = 2
                            if cr is not None and v + r2 <= L:
                                add(q + 1, g2 + cr, v, (0, m, -r2))
                        # N3: v = m*q ± 나머지 (q 가 싼 값)
                        if r < lim:
                            if q == 1:
                                add(r, g1, v, (1, m, 1, 1))
                            else:
                                ck = C.get(q)
                                if ck is None and q in A2:
                                    ck = 2
                                if ck is not None:
                                    add(r, g2 + ck, v, (1, m, q, 1))
                        if r2 < lim and v + r2 <= L:
                            q1 = q + 1
                            ck = C.get(q1)
                            if ck is None and q1 in A2:
                                ck = 2
                            if ck is not None:
                                add(r2, g2 + ck, v, (1, m, q1, -1))
                    if g <= s1depth:
                        for m in s1m:
                            if m >= v:
                                break
                            q, r = divmod(v, m)
                            if r == 0:
                                add(q, g2, v, (0, m, 0))
                                continue
                            cr = C.get(r)
                            if cr is not None:
                                add(q, g3 + cr, v, (0, m, r))
                            r2 = m - r
                            cr = C.get(r2)
                            if cr is not None and v + r2 <= L:
                                add(q + 1, g3 + cr, v, (0, m, -r2))
                    # N1: 가장 가까운 풀/L1 값
                    i = bisect_left(allv, v)
                    if i > 0:
                        x = allv[i - 1]
                        dlt = v - x
                        if dlt < lim:
                            add(dlt, g1 + C[x], v, (2, x, 1))
                    if i < nall:
                        x = allv[i]
                        dlt = x - v
                        if 0 < dlt < lim:
                            add(dlt, g1 + C[x], v, (2, x, -1))
                    # N2: v = x*q ± c
                    lim2 = v >> nshift
                    for q in mults:
                        if q * q > v:
                            break
                        i = bisect_left(allv, v // q)
                        if i > 0:
                            x = allv[i - 1]
                            dlt = v - x * q
                            if 0 < dlt < lim2:
                                add(dlt, g2 + C[x], v, (3, x, q, 1))
                        if i < nall:
                            x = allv[i]
                            pq = x * q
                            dlt = pq - v
                            if 0 < dlt < lim2 and pq <= L:
                                add(dlt, g2 + C[x], v, (3, x, q, -1))
            g += 1
        if bestleaf is None:
            return None
        v = bestleaf
        tr = self.tree(v)
        while True:
            cost, par, step = node[v]
            if par is None:
                break
            kind = step[0]
            if kind == 0:
                _, m, d = step
                tr = self.tree(m) if v == 1 else ("*", tr, self.tree(m))
                if d > 0:
                    tr = ("+", tr, self.tree(d))
                elif d < 0:
                    tr = ("-", tr, self.tree(-d))
            elif kind == 1:
                _, m, k, sgn = step
                big = m if k == 1 else ("*", m, self.tree(k))
                tr = ("+", big, tr) if sgn > 0 else ("-", big, tr)
            elif kind == 2:
                _, x, sgn = step
                tr = ("+", self.tree(x), tr) if sgn > 0 else ("-", self.tree(x), tr)
            else:
                _, x, q, sgn = step
                big = ("*", self.tree(x), q)
                tr = ("+", big, tr) if sgn > 0 else ("-", big, tr)
            v = par
        c = self.tree_cost(tr)
        if c is None:
            return None
        return (c, tr)

    def gen(self, t, W=None):
        if self.genmode == 2:
            r = self.generic2(t, self.W2 if not self.fast else 4)
            if r is not None:
                return r
        return self.generic(t, W)

    def live_check(self):
        """지금까지의 프로그램만으로 이미 레지스터가 모자라면 바로 포기한다 (이후 사용은 수명을 늘리기만 한다)."""
        self.nder += 1
        if self.nder % 5 == 0 and len(self.vals) > self.pz.registers and self.finish() is None:
            raise Invalid("registers")

    def bootstrap(self):
        """풀에 1 과 2 를 넣어 범용 구성이 항상 성공하게 한다."""
        if 1 not in self.pool:
            a = self.plist[0]
            self.emit("/", a, a, True)
        if 2 not in self.pool and self.L >= 2:
            self.emit("+", 1, 1, True)
        if self.L >= 1 << 20 and len(self.Q) < 6:
            # 작은 값이 거의 없는 퍼즐: 3, 4, 8, 16 을 더해 작은 수를 싸게 만든다
            for op, a, b in (("+", 2, 1), ("+", 2, 2), ("+", 4, 4), ("+", 8, 8)):
                if a in self.pool and b in self.pool:
                    self.emit(op, a, b, True)
        self.end_derivation()

    # ------------------------------------------------------------------ 주 루프
    def solve(self):
        rem = self.remaining
        seeds = [sd for sd in self.cfg.get("seeds", ()) if 1 <= sd <= self.L]
        seedsort = self.cfg.get("seedsort", 0)
        while seeds:
            seeds = [sd for sd in seeds if sd not in self.pool]
            if not seeds:
                break
            sd = seeds[0]
            g = self.gen(sd)
            if g is None:
                self.bootstrap()
                g = self.gen(sd)
            if g is not None and seedsort and len(seeds) > 1:
                # 씨앗도 지금 가장 싸게 만들어지는 것부터 만든다
                for s2 in seeds[1:]:
                    g2 = self.gen(s2)
                    if g2 is not None and g2[0] < g[0]:
                        sd, g = s2, g2
            seeds.remove(sd)
            if g is None:
                continue
            self.emit_tree(g[1], False)
            if sd not in self.pool:
                continue
            self.end_derivation_keep(sd)
            self.log.append((sd, g[0], "seed"))
        bb = self.cfg.get("bbias", 0.0)
        aux = self.aux
        auxmax = self.auxmax
        while rem:
            if aux and not (rem - aux):
                break
            if not self.fast and time.time() - self.t0 > self.tl:
                self.fast = True
                for a in list(rem & aux):
                    rem.discard(a); self.cand.pop(a, None); self.mitm.pop(a, None)
            pick = None
            if not self.fast:
                for t in rem:
                    r = self.best_rel(t)
                    if r is None:
                        continue
                    c = r[0]
                    if c <= self.relmax or c <= self.relfrac * t.bit_length():
                        kk = (c - bb * t.bit_length(), t) if not self.noise else (c - bb * t.bit_length(), self.rng.random())
                        if pick is None or kk < pick[3]:
                            pick = (c, t, r[1], kk)
            if pick is not None:
                c, t, tr, _ = pick
                self.emit_tree(tr, True)
                self.end_derivation()
                self.live_check()
                self.log.append((t, c, "rel"))
                if t in rem:      # 안전장치
                    raise RuntimeError("relation did not produce target")
                continue
            if self.rootpick > 1 and len(rem) > 1:
                t = self.rng.choice(sorted(rem - aux)[: self.rootpick])
            else:
                t = min(rem - aux)
            r = None if self.fast else self.best_rel(t)
            g = self.gen(t, 2 if self.fast else None)
            if self.rootK > 1 and len(rem) > 1 and not self.fast and g is not None:
                # 남은 목표값 가운데 지금 가장 싸게 만들어지는 것을 먼저 만든다.
                # 지난번에 잰 비용(gcache)이 낮은 순서로 다시 재고, 더 나아질 수 없으면 멈춘다.
                gc = self.gcache
                bc = min(g[0], r[0]) if r is not None else g[0]
                gc[t] = bc
                others = [x for x in rem if x != t]
                others.sort(key=lambda x: (gc.get(x, -1), x))
                slack = self.rootKslack
                n_eval = 1
                for t2 in others:
                    if bc <= self.rootKstop or n_eval >= self.rootK:
                        break
                    if gc.get(t2, -1) - slack >= bc:
                        break
                    n_eval += 1
                    g2 = self.gen(t2, None)
                    if g2 is None:
                        continue
                    r2 = self.best_rel(t2)
                    c2 = min(g2[0], r2[0]) if r2 is not None else g2[0]
                    gc[t2] = c2
                    if t2 in aux and (c2 > auxmax or c2 >= bc):
                        continue
                    a2 = c2 - bb * t2.bit_length()
                    a1 = bc - bb * t.bit_length()
                    if a2 < a1 or (a2 == a1 and self.noise and self.rng.random() < 0.3):
                        bc = c2
                        t, g, r = t2, g2, r2
            if g is None and r is None:
                self.bootstrap()
                if t not in rem:
                    continue
                g = self.gen(t, 2 if self.fast else None)
                if g is None:
                    raise RuntimeError(f"no construction for {t}")
            if g is not None and (r is None or g[0] < r[0]):
                self.emit_tree(g[1], False)
                self.log.append((t, g[0], "gen"))
            else:
                self.emit_tree(r[1], True)
                self.log.append((t, r[0], "rel*"))
            self.end_derivation()
            self.live_check()
            if t in rem:
                raise RuntimeError("construction did not produce target")
        return self.finish()

    # ------------------------------------------------------------------ 마무리
    def finish(self):
        """죽은 코드 제거 + 레지스터 배정. 프로그램 또는 None(레지스터 부족)."""
        n = len(self.vals)
        nstart = len(self.pz.start)
        targets = set(self.pz.targets)
        need = [False] * n
        seen_t = set(self.pz.start)
        for i in range(nstart, n):
            v = self.vals[i]
            if v in targets and v not in seen_t:
                need[i] = True
                seen_t.add(v)
        for i in range(n - 1, nstart - 1, -1):
            if need[i]:
                d = self.defs[i]
                need[d[1]] = True
                need[d[2]] = True
        last = [-1] * n
        for i in range(nstart, n):
            if need[i]:
                d = self.defs[i]
                last[d[1]] = i
                last[d[2]] = i
        nreg = self.pz.registers
        reg = {}
        free = list(range(nreg - 1, nstart - 1, -1))
        # 시작값: 중복 값은 첫 레지스터만 pool 에 있으므로 SSA 번호 = 레지스터 번호
        for i in range(nstart):
            if last[i] >= 0:
                reg[i] = i
            else:
                free.append(i)
        prog = []
        for i in range(nstart, n):
            if not need[i]:
                continue
            op, a, b = self.defs[i]
            ra, rb = reg[a], reg[b]
            if last[a] == i:
                free.append(ra)
                del reg[a]
            if b != a and last[b] == i:
                free.append(rb)
                del reg[b]
            if not free:
                return None
            rd = free.pop()
            prog.append([op, ra, rb, rd])
            if last[i] >= 0:
                reg[i] = rd
            else:
                free.append(rd)
        return prog


def solve_once(pz, cfg):
    """한 가지 설정으로 풀어 (프로그램, 로그, cap) 또는 (None, 사유, None)."""
    last_err = None
    best = None
    caps = cfg.get("caps")
    if caps is None:
        T = pz.targets
        mx = max(T)
        top = sum(1 for t in T if len(str(t)) == len(str(mx)))
        if top >= 0.9 * len(T) and len(T) >= 12 and mx.bit_length() >= 28:
            caps = cfg.get("caps_indep", (66, 56, 48, 40, 32))           # 거의 전부 무작위 목표값
        elif top >= 0.35 * len(T) and len(T) >= 12 and mx.bit_length() >= 28:
            caps = cfg.get("caps_mixed", (72, 62, 54, 46, 38, 30))       # 무작위 목표값이 많다: 무제한 풀은 대개 레지스터가 모자란다
        else:
            caps = cfg.get("caps_struct", (None, 72, 62, 54, 46, 38, 30))
    for cap in caps:
        c = dict(cfg)
        c["cap"] = cap
        if cap is not None:
            c["QN"] = min(c.get("QN", 40), max(6, cap - c.get("qgap", 6)))
        try:
            s = Solver(pz, c)
            prog = s.solve()
        except (RuntimeError, Invalid, RecursionError) as e:
            last_err = repr(e)
            prog = None
            s = None
        if prog is None:
            last_err = last_err or "registers"
            continue
        err = check_program(pz, prog)
        if err is not None:
            last_err = err
            continue
        if best is None or len(prog) < len(best[0]):
            best = (prog, s.log, cap)
        if best is not None:
            break
    if best is not None:
        return best
    return None, last_err, None


def solve_puzzle(pz, cfg=None):
    """(프로그램, 로그) 를 돌려준다. 실패하면 (None, 사유).

    1) 기본 설정으로 한 번, 2) 씨앗 후보를 하나씩 넣어 보고 짧아지면 채택 (what-if),
    3) 남은 시간에 무작위 재시작.
    """
    cfg = dict(cfg or {})
    t0 = time.time()
    budget = cfg.get("budget", 0.0)
    if pz.limit <= 40:
        from tiny import solve_tiny
        tp = solve_tiny(pz)
        if tp is not None and check_program(pz, tp) is None:
            return tp, [("tiny", len(tp), "bfs")]
    prog, log, cap = solve_once(pz, cfg)
    best = (prog, log)
    if prog is None:
        return best
    seeds = []
    if cfg.get("use_seeds", False) and len(pz.targets) >= 4 and pz.limit > 4096:
        from seeds2 import seed_candidates
        base = dict(cfg)
        if cap is not None:
            base["caps"] = tuple(x for x in (cap, 62, 54, 46, 38, 30) if x <= cap)
        for sd in seed_candidates(pz, cfg.get("nseeds", 10)):
            if time.time() - t0 > budget * 0.6:
                break
            c = dict(base)
            c["seeds"] = tuple(seeds) + (sd,)
            p2, l2, _ = solve_once(pz, c)
            if p2 is not None and len(p2) < len(best[0]):
                best = (p2, l2)
                seeds.append(sd)
    n = 0
    r0 = cfg.get("rseed0", 0)
    while time.time() - t0 < budget and n < cfg.get("restarts", 0):
        n += 1
        c = dict(cfg)
        c["rseed"] = r0 + n
        c["noise"] = cfg.get("rnoise", 1.0)
        c["rootpick"] = cfg.get("rrootpick", 1)
        if seeds and n % 2 == 0:
            c["seeds"] = tuple(seeds)
        if cap is not None:
            c["caps"] = tuple(x for x in (cap, 62, 54, 46, 38, 30) if x <= cap)
        v = (r0 + n) % 4
        if v == 1:
            c["W2"] = max(12, 2 * cfg.get("W2", 6))
        elif v == 2:
            c["QN"] = 28
            c["qgap"] = 14
        elif v == 3:
            c["s1depth"] = 1
        else:
            c["cshift"] = 2
        p2, l2, _ = solve_once(pz, c)
        if p2 is not None and len(p2) < len(best[0]):
            best = (p2, l2)
    return best
