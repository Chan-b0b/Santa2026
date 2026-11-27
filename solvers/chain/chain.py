"""chain: 범용 수 구성 솔버.

핵심: 레지스터에 있는 값들(풀)을 곱수 m 과 가수 d 로 동시에 쓰는 역방향 beam 탐색.
  t = c*m + d,  t = c*m - d   (d 는 풀 값 또는 풀 값 둘의 연산 한 번으로 만든 값 S1)
을 반복해 t 를 풀 값 또는 S1 값까지 줄인다 (일반화된 Horner / 몫·나머지 분해).
"""
from __future__ import annotations
from bisect import bisect_left, bisect_right
from math import gcd


class Params:
    def __init__(self, **kw):
        self.W = 48            # beam 폭
        self.digits = 0        # 미리 만들 자릿수 테이블 1..digits
        self.reserve = 2       # 체인 사이에 비워 둘 레지스터 수
        self.maxcost = 150
        self.order = "asc"
        self.pol = 0           # 퇴출 정책 번호
        self.seed = 0
        self.close_shift = 3
        self.bstar = 12
        self.near = 1
        self.trace = 0
        self.f2 = 1
        self.tiepass = 0
        self.tieslack = 0
        self.alpha = 0.0       # 목표값 선택 기준: 비용 - alpha*비트수
        self.seed = 0          # 목표값 쌍의 공통 인수(gcd)를 먼저 만드는 개수 상한
        self.seed_min = 128
        self.relkeep = 0       # 남은 목표값을 나누는 풀 값을 보호
        self.rel_shift = 10
        self.hubseed = 0       # 숨은 기준값(hub)을 먼저 만드는 개수 상한
        self.vcap = 0          # 0 이 아니면 vchain (수명 기반 가상 풀) 을 쓴다. 탐색에 넣는 값 수 상한
        self.vsoft = 44        # 되살릴 값이 지나가는 구간의 동시 생존 값 수 상한
        self.tie_s1 = 0        # 같은 비용이면 S1 로 작은 값을 더 많이 새로 만드는 체인을 고른다
        self.hot = 0           # vchain: 최근 hot 개 명령 안에 쓰인 값을 가수 d 로 우선한다 (0 이면 끔)
        self.preseed = 0       # 작은 값을 미리 만드는 개수
        self.pre_lo = 512
        self.pre_hi = 4096
        self.pre_seed = 1
        self.hub_cmax = 64
        self.hub_shift = 12
        self.hub_min = 3
        self.near_shift = 6
        self.s1m = 1           # S1 곱수를 쓰는 깊이 (0 이면 끔)
        self.s1m_max = 1 << 13
        self.ubonus = 0.0
        self.bases = ()        # 해독한 숨은 밑(decode.py). 목표값보다 먼저 만든다
        self.aux = ()          # 목표값 설명(decode.explain)에 필요한 작은 값. 싸게(aux_max 이하) 만들어지는 것부터 먼저 만든다
        self.aux_max = 1
        self.aux_pre = 0       # 1 이면 밑보다 먼저 한 번 더 돈다
        self.__dict__.update(kw)


class Machine:
    def __init__(self, puzzle, params):
        self.pz = puzzle
        self.pr = params
        self.limit = puzzle.limit
        self.nreg = puzzle.registers
        self.reg = [None] * self.nreg
        self.loc = {}
        for i, v in enumerate(puzzle.start):
            self.reg[i] = v
            if v not in self.loc:
                self.loc[v] = i
        self.free = [i for i in range(self.nreg - 1, -1, -1)
                     if self.reg[i] is None or self.loc[self.reg[i]] != i]
        self.prog = []
        self.produced = set(puzzle.start)
        self.targets = set(puzzle.targets)
        self.pinned = set()
        self.rel = set()
        self.birth = {v: 0 for v in self.loc}
        self.uses = {v: 0 for v in self.loc}
        self.clock = 0
        self.dirty = True
        self.S1 = {}
        self.resid = {}
        self.mults = []

    # ---- 풀 관리 -------------------------------------------------------
    def score(self, v):
        """높을수록 남긴다."""
        if v in self.pinned:
            return 1e18
        if v in self.rel:
            return 1e9 - v.bit_length()
        pol = self.pr.pol
        b = v.bit_length()
        if pol == 0:      # 작은 값 우선
            return -b
        if pol == 1:      # 작은 값 우선 + 사용 횟수
            return -b + 6 * self.uses.get(v, 0)
        if pol == 2:      # 목표값은 조금 더 보호
            return -b + 6 * self.uses.get(v, 0) + (8 if v in self.targets else 0)
        if pol == 4:      # 목표 크기 bstar 비트 근처 우선
            return -abs(b - self.pr.bstar) + self.pr.ubonus * self.uses.get(v, 0)
        if pol == 5:      # bstar 이하는 동등, 초과는 감점
            return -max(0, b - self.pr.bstar) + self.pr.ubonus * self.uses.get(v, 0) - 0.01 * b
        if pol == 6:      # bstar 근처 우선, 작은 쪽은 덜 감점
            return -(b - self.pr.bstar if b > self.pr.bstar else 0.5 * (self.pr.bstar - b)) + self.pr.ubonus * self.uses.get(v, 0)
        if pol == 3:      # 최근 값 우선
            return self.birth.get(v, 0) * 0.02 - b + 6 * self.uses.get(v, 0)
        return -b

    def evict_one(self, protect):
        best = None
        bs = None
        for v in self.loc:
            if v in protect:
                continue
            s = self.score(v)
            if bs is None or s < bs:
                bs = s
                best = v
        if best is None:
            raise RuntimeError("퇴출할 값이 없음")
        r = self.loc.pop(best)
        self.dirty = True
        return r

    def emit(self, op, x, y, protect=()):
        a = self.loc[x]
        b = self.loc[y]
        if op == "+":
            r = x + y
        elif op == "-":
            r = x - y
        elif op == "*":
            r = x * y
        else:
            assert x % y == 0
            r = x // y
        assert 1 <= r <= self.limit, (op, x, y, r)
        self.uses[x] = self.uses.get(x, 0) + 1
        self.uses[y] = self.uses.get(y, 0) + 1
        if r in self.loc:
            return r
        if self.free:
            d = self.free.pop()
        else:
            d = self.evict_one(protect)
        self.prog.append([op, a, b, d])
        self.reg[d] = r
        self.loc[r] = d
        self.produced.add(r)
        self.clock += 1
        self.birth[r] = self.clock
        self.uses.setdefault(r, 0)
        self.dirty = True
        return r

    def trim(self):
        cap = self.nreg - self.pr.reserve
        while len(self.loc) > cap:
            self.free.append(self.evict_one(()))

    # ---- 테이블 --------------------------------------------------------
    def rebuild(self):
        limit = self.limit
        vals = sorted(self.loc)
        S1 = {}
        n = len(vals)
        for i in range(n):
            a = vals[i]
            for j in range(i, n):
                b = vals[j]          # a <= b
                s = a + b
                if s <= limit and s not in S1:
                    S1[s] = ("+", a, b)
                if b > a:
                    s = b - a
                    if s not in S1:
                        S1[s] = ("-", b, a)
                s = a * b
                if s <= limit and s not in S1:
                    S1[s] = ("*", a, b)
                if a > 1 and b % a == 0:
                    s = b // a
                    if s not in S1:
                        S1[s] = ("/", b, a)
        if 1 not in S1 and vals:
            S1[1] = ("/", vals[0], vals[0])
        for v in vals:
            S1.pop(v, None)
        self.S1 = S1
        mults = [v for v in vals if v >= 2]
        resid = {}
        rorder = self.resid_order(vals)
        for m in mults:
            d = {}
            for v in rorder:     # 같은 나머지는 먼저 나온 값이 남는다 (기본은 오름차순 = 가장 작은 값)
                r = v % m
                if r and r not in d:
                    d[r] = v
            resid[m] = d
        self.resid = resid
        self.mults = mults
        self.vals = vals
        self.S1sorted = sorted(S1)
        self.allsorted = sorted(list(S1) + vals)
        self.S1small = [x for x in self.S1sorted if 2 <= x <= self.pr.s1m_max]
        F2 = {}
        if self.pr.f2:
            S1k = self.S1sorted
            upd = F2.update
            for p in vals:
                upd({x + p: x for x in S1k})
                if p > 1:
                    upd({x * p: x for x in S1k})
                i = bisect_right(S1k, p)
                upd({p - x: x for x in S1k[:i]})
                upd({x - p: x for x in S1k[i:]})
            F2.pop(0, None)
        self.F2 = F2
        self.dirty = False

    def resid_order(self, vals):
        return vals

    # ---- 역방향 beam ----------------------------------------------------
    def find_chain(self, t, ub=None):
        """t 를 만드는 정방향 단계 목록 [(op, x, y), ...] 을 돌려준다. x, y 는 값.

        역방향 상태 v 에서의 이동 (c 가 다음 상태, 괄호 안은 명령 수):
          M   v = c*m                 (1)   m 은 풀 값
          MA  v = c*m + d             (2)   d 는 풀 값, d 가 S1 값이면 (3)
          MS  v = c*m - d             (2/3)
          N3  v = m*q + c, m*q - c    (2)   q 는 풀 값, q 가 S1 값이면 (3). 나머지 c 가 다음 상태
          N1  v = s + c, s - c        (2)   s 는 v 에 가장 가까운 S1 값
          N2  v = s*q + c, s*q - c    (3)   s 는 v/q 에 가장 가까운 S1 값
          A/S/RS  v = c + p, c - p, p - c   (1)   p 는 풀 값
          D/RD    v = c / p, p / c          (1)
        끝: c 가 풀 값이면 0, S1 값이면 1.
        """
        if self.dirty:
            self.rebuild()
        pool = self.loc
        S1 = self.S1
        resid = self.resid
        mults = self.mults
        vals = self.vals
        limit = self.limit
        pr = self.pr
        W = pr.W
        maxcost = pr.maxcost
        cshift = pr.close_shift
        nshift = pr.near_shift
        use_near = pr.near
        S1s = self.S1sorted
        nS1 = len(S1s)
        if t in pool:
            return []
        node = {t: (0, None, None, 0)}   # 값 -> (비용, 부모 값, 단계, S1 로 만든 작은 값 수)
        levels = [[] for _ in range(maxcost + 6)]
        levels[0].append(t)
        best = maxcost + 1 if ub is None else ub
        bestleaf = None
        if t in S1 and best > 1:
            best = 1
            bestleaf = t
        elif t in self.F2 and best > 2:
            best = 2
            bestleaf = t

        F2 = self.F2
        nonterm = 3 if F2 else 2
        allv = self.allsorted
        nall = len(allv)
        s1m = self.S1small if pr.s1m else ()

        tie = pr.tie_s1
        bestns = 0

        def nsof(v, step):
            """뿌리에서 이 단계까지 S1 로 새로 만드는 작은 값의 수 (동점 처리용)."""
            k = step[0]
            n = node[v][3]
            if k == "MA" or k == "MS":
                return n + step[3]
            if k == "N3":
                return n + step[4]
            if k == "M1":
                return n + 1
            if k == "MA1" or k == "MS1":
                return n + 1 + step[3]
            return n

        def add(c, cost, v, step):
            nonlocal best, bestleaf, bestns
            o = node.get(c)
            if o is not None and o[0] <= cost:
                return
            if c in pool:
                if cost < best:
                    ns = nsof(v, step)
                    node[c] = (cost, v, step, ns)
                    best = cost
                    bestleaf = c
                    bestns = ns
                elif tie and cost == best:
                    ns = nsof(v, step)
                    if ns > bestns:
                        node[c] = (cost, v, step, ns)
                        bestleaf = c
                        bestns = ns
                return
            if c in S1:
                if cost + 1 < best:
                    ns = nsof(v, step) + (1 if c < 8192 else 0)
                    node[c] = (cost, v, step, ns)
                    best = cost + 1
                    bestleaf = c
                    bestns = ns
                elif tie and cost + 1 == best:
                    ns = nsof(v, step) + (1 if c < 8192 else 0)
                    if ns > bestns:
                        node[c] = (cost, v, step, ns)
                        bestleaf = c
                        bestns = ns
                return
            if c in F2:
                if cost + 2 < best:
                    ns = nsof(v, step)
                    node[c] = (cost, v, step, ns)
                    best = cost + 2
                    bestleaf = c
                    bestns = ns
                return
            if cost + nonterm < best:
                node[c] = (cost, v, step, nsof(v, step))
                levels[cost].append(c)
                # 가까운 풀 값 / S1 값이 있으면 그 차이를 바로 다음 상태로 넣는다
                i = bisect_left(allv, c)
                lim = c >> cshift
                if i > 0:
                    x = allv[i - 1]
                    dlt = c - x
                    if dlt < lim:
                        if x in pool:
                            add(dlt, cost + 1, c, ("A", x))
                        else:
                            add(dlt, cost + 2, c, ("N1", x, 1))
                if i < nall:
                    x = allv[i]
                    dlt = x - c
                    if dlt < lim:
                        if x in pool:
                            add(dlt, cost + 1, c, ("RS", x))
                        else:
                            add(dlt, cost + 2, c, ("N1", x, -1))

        # 맨 위 상태 자체의 가까운 값 검사
        i = bisect_left(allv, t)
        lim = t >> cshift
        for x in allv[max(0, i - 1):i + 1]:
            dlt = abs(t - x)
            if 0 < dlt < lim:
                if x in pool:
                    add(dlt, 1, t, ("A", x) if x < t else ("RS", x))
                else:
                    add(dlt, 2, t, ("N1", x, 1 if x < t else -1))

        g = 0
        while g + 1 < best and g <= maxcost:
            lv = levels[g]
            if lv:
                cand = [v for v in set(lv) if node[v][0] == g]
                if len(cand) > W:
                    cand.sort()
                    cand = cand[:W]
                g1 = g + 1
                g2 = g + 2
                g3 = g + 3
                for v in cand:
                    if g1 >= best:
                        break
                    vnear = v >> nshift
                    # 곱셈 단계
                    for m in mults:
                        if m >= v:
                            break
                        q, r = divmod(v, m)
                        if r == 0:
                            add(q, g1, v, ("M", m))
                            continue
                        rm = resid[m]
                        d = rm.get(r)
                        if d is not None and d < v:
                            add((v - d) // m, g2, v, ("MA", m, d, 0))
                        d = rm.get(m - r)
                        if d is not None and v + d <= limit:
                            add((v + d) // m, g2, v, ("MS", m, d, 0))
                        if r in S1:
                            add(q, g3, v, ("MA", m, r, 1))
                        r2 = m - r
                        if r2 in S1 and v + r2 <= limit:
                            add(q + 1, g3, v, ("MS", m, r2, 1))
                        if use_near:
                            if r < vnear:
                                if q in pool:
                                    if q > 1:
                                        add(r, g2, v, ("N3", m, q, 1, 0))
                                elif q in S1:
                                    add(r, g3, v, ("N3", m, q, 1, 1))
                            if r2 < vnear and v + r2 <= limit:
                                q1 = q + 1
                                if q1 in pool:
                                    add(r2, g2, v, ("N3", m, q1, -1, 0))
                                elif q1 in S1:
                                    add(r2, g3, v, ("N3", m, q1, -1, 1))
                            # N2: v 는 s*m 근처 (s 는 S1 값)
                            lo = bisect_right(S1s, q)
                            if lo > 0:
                                sv = S1s[lo - 1]
                                c = v - sv * m
                                if c < vnear:
                                    add(c, g3, v, ("N2", sv, m, 1))
                            if lo < nS1:
                                sv = S1s[lo]
                                x = sv * m
                                c = x - v
                                if c < vnear and x <= limit:
                                    add(c, g3, v, ("N2", sv, m, -1))
                    # S1 값을 곱수로 쓰는 단계 (얕은 수준에서만)
                    if g < pr.s1m:
                        g4 = g + 4
                        for m in s1m:
                            if m >= v:
                                break
                            q, r = divmod(v, m)
                            if r == 0:
                                add(q, g2, v, ("M1", m))
                            elif g3 < best:
                                if r in pool:
                                    add(q, g3, v, ("MA1", m, r, 0))
                                elif r in S1 and g4 < best:
                                    add(q, g4, v, ("MA1", m, r, 1))
                                r2 = m - r
                                if v + r2 <= limit:
                                    if r2 in pool:
                                        add(q + 1, g3, v, ("MS1", m, r2, 0))
                                    elif r2 in S1 and g4 < best:
                                        add(q + 1, g4, v, ("MS1", m, r2, 1))
                    # 순수 덧셈/뺄셈/나눗셈 단계 (끝이 S1 또는 F2 인 경우)
                    if g2 < best:
                        for p in vals:
                            if p < v:
                                c = v - p                 # v = c + p
                                if c in S1 or c in F2:
                                    add(c, g1, v, ("A", p))
                            else:
                                c = p - v                 # v = p - c
                                if c in S1 or c in F2:
                                    add(c, g1, v, ("RS", p))
                                if p % v == 0:            # v = p / c
                                    c = p // v
                                    if c in pool or c in S1:
                                        add(c, g1, v, ("RD", p))
                            c = v + p                     # v = c - p
                            if c <= limit and (c in S1 or c in F2):
                                add(c, g1, v, ("S", p))
                            if p > 1:
                                c = v * p                 # v = c / p
                                if c <= limit and (c in S1 or c in F2):
                                    add(c, g1, v, ("D", p))
            g += 1
        if bestleaf is None:
            return None
        # 정방향 복원
        steps = []
        c = bestleaf
        if c in pool:
            pass
        elif c in S1:
            steps.append(S1[c])
        else:
            x = F2[c]
            steps.append(S1[x])
            for p in vals:
                if x + p == c:
                    steps.append(("+", x, p)); break
                if x * p == c:
                    steps.append(("*", x, p)); break
                if x - p == c:
                    steps.append(("-", x, p)); break
                if p - x == c:
                    steps.append(("-", p, x)); break
            else:
                raise RuntimeError("F2 복원 실패")
        while c != t:
            _, v, st, _ns = node[c]
            k = st[0]
            if k == "M":
                steps.append(("*", c, st[1]))
            elif k == "M1":
                steps.append(S1[st[1]])
                steps.append(("*", c, st[1]))
            elif k == "MA1" or k == "MS1":
                m, d, viaS1 = st[1], st[2], st[3]
                steps.append(S1[m])
                steps.append(("*", c, m))
                if viaS1:
                    steps.append(S1[d])
                steps.append(("+" if k == "MA1" else "-", c * m, d))
            elif k == "MA" or k == "MS":
                m, d, viaS1 = st[1], st[2], st[3]
                steps.append(("*", c, m))
                if viaS1:
                    steps.append(S1[d])
                steps.append(("+" if k == "MA" else "-", c * m, d))
            elif k == "N3":
                m, q, sign, viaS1 = st[1], st[2], st[3], st[4]
                if viaS1:
                    steps.append(S1[q])
                steps.append(("*", m, q))
                steps.append(("+" if sign > 0 else "-", m * q, c))
            elif k == "N1":
                sv, sign = st[1], st[2]
                steps.append(S1[sv])
                steps.append(("+" if sign > 0 else "-", sv, c))
            elif k == "N2":
                sv, m, sign = st[1], st[2], st[3]
                steps.append(S1[sv])
                steps.append(("*", sv, m))
                steps.append(("+" if sign > 0 else "-", sv * m, c))
            elif k == "A":
                steps.append(("+", c, st[1]))
            elif k == "S":
                steps.append(("-", c, st[1]))
            elif k == "RS":
                steps.append(("-", st[1], c))
            elif k == "D":
                steps.append(("/", c, st[1]))
            elif k == "RD":
                steps.append(("/", st[1], c))
            c = v
        return steps

    def run_steps(self, steps):
        n = len(steps)
        need = [None] * (n + 1)
        cur = set()
        need[n] = frozenset()
        for i in range(n - 1, -1, -1):
            need[i] = frozenset(cur)        # i 번째 실행 뒤에 필요한 피연산자
            cur.add(steps[i][1])
            cur.add(steps[i][2])
        for i, (op, x, y) in enumerate(steps):
            self.emit(op, x, y, need[i])

    def commit(self, t, steps, remaining):
        """찾은 체인을 실제로 내보낸다. 실패하면 False."""
        self.run_steps(steps)
        assert t in self.produced
        self.update_rel([x for x in remaining if x not in self.produced])
        self.trim()
        return True

    def build_digits(self, k):
        """1..k 를 풀에 넣고 고정한다."""
        if k <= 0:
            return
        if 1 not in self.loc:
            v = min(self.loc)
            self.emit("/", v, v)
        self.pinned.add(1)
        for d in range(2, k + 1):
            if d > self.limit:
                break
            if d not in self.loc:
                # 풀 값 둘의 연산 한 번으로 되면 그걸 쓰고, 아니면 +1
                self.emit("+", d - 1, 1)
            self.pinned.add(d)

    def preseed(self, k):
        """작은 값 k 개를 명령 1개씩으로 미리 만든다. 매번 지금 풀의 S1 값 가운데
        [pre_lo, pre_hi) 범위에서 하나를 (정해진 난수로) 골라 만들기 때문에, 뒤에 만든 값은
        처음 풀에서 보면 명령 2개 이상짜리 '깊은' 값이 된다."""
        import random
        rnd = random.Random(self.pr.pre_seed)
        lo, hi = self.pr.pre_lo, self.pr.pre_hi
        for _ in range(k):
            if self.dirty:
                self.rebuild()
            c = [v for v in self.S1sorted[bisect_left(self.S1sorted, lo):bisect_left(self.S1sorted, hi)]]
            if not c:
                c = [v for v in self.S1sorted if v < hi and v > 4]
                if not c:
                    return
            v = c[rnd.randrange(len(c))]
            op, a, b = self.S1[v]
            self.emit(op, a, b)

    def solve(self):
        pr = self.pr
        self.build_digits(pr.digits)
        if pr.preseed:
            self.preseed(pr.preseed)
        if 1 not in self.loc and pr.digits <= 0:
            pass
        order = sorted(self.targets)
        if pr.order == "desc":
            order.reverse()
        if pr.order == "cheap":
            return self.solve_cheapest()
        for t in order:
            if t in self.produced:
                continue
            steps = self.find_chain(t)
            if steps is None:
                return None
            if not self.commit(t, steps, [x for x in order if x not in self.produced]):
                return None
        return self.prog


def _update_rel(self, remaining):
    """남은 목표값과 관계가 있는 풀 값을 표시해 퇴출에서 보호한다.
    relkeep 1: 남은 목표값을 나누는 값.  2/3: 추가로 남은 목표값이 그 값의 작은 배수 근처인 값."""
    rk = self.pr.relkeep
    if not rk:
        return
    mn = self.pr.seed_min
    shift = self.pr.rel_shift
    rel = set()
    for x in self.loc:
        if x >= mn:
            xs = x >> shift
            for t in remaining:
                if t > x:
                    q, r = divmod(t, x)
                    if r == 0:
                        rel.add(x)
                        break
                    if rk >= 2 and xs and q <= 4096 and (r < xs or x - r < xs):
                        rel.add(x)
                        break
                elif rk >= 2 and xs and x - t < xs:
                    rel.add(x)
                    break
    self.rel = rel


def _seed_bases(self):
    """목표값 쌍의 gcd 중 큰 것을 먼저 만들어 풀에 넣는다 (여러 목표값이 공유하는 인수)."""
    pr = self.pr
    T = [t for t in sorted(self.targets) if t not in self.produced]
    cand = {}
    for i in range(len(T)):
        for j in range(i + 1, len(T)):
            g = gcd(T[i], T[j])
            if g >= pr.seed_min and g not in self.loc:
                cand[g] = 0
    for g in cand:
        cand[g] = sum(1 for t in T if t % g == 0)
    order = sorted(cand, key=lambda g: -(cand[g] - 1) * g.bit_length())
    chosen = []
    for g in order:
        if len(chosen) >= pr.seed:
            break
        if g in self.targets:
            continue
        chosen.append(g)
    for g in sorted(chosen):
        if g in self.loc:
            continue
        steps = self.find_chain(g)
        if steps is None:
            continue
        if pr.trace:
            print("seed", g, cand[g], len(steps))
        self.rel.add(g)
        self.run_steps(steps)
        self.rel.add(g)
        self.trim()


def _seed_hubs(self):
    """숨은 기준값(hub) 찾기: 목표값 t 를 작은 수 c 로 나눈 H = t/c 가운데,
    다른 목표값 여럿이 H 의 작은 배수 근처(H/2^hub_shift 이내)에 있는 것을 먼저 만든다."""
    pr = self.pr
    T = [t for t in sorted(self.targets) if t not in self.produced]
    Tset = set(T)
    cand = {}
    for t in T:
        if t < (1 << 16):
            continue
        for c in range(2, pr.hub_cmax + 1):
            if t % c == 0:
                h = t // c
                if h >= (1 << 14) and h not in Tset and h not in self.loc:
                    cand[h] = None
    if not cand:
        return
    sh = pr.hub_shift
    for h in cand:
        tol = h >> sh
        deps = set()
        for t in T:
            q, r = divmod(t, h)
            if q > 4096:
                continue
            if (q >= 1 and r <= tol) or h - r <= tol:
                deps.add(t)
        cand[h] = deps
    chosen = []
    covered = set()
    for h in sorted(cand, key=lambda h: (-len(cand[h]), h)):
        if len(chosen) >= pr.hubseed:
            break
        new = cand[h] - covered
        if len(new) >= pr.hub_min:
            chosen.append(h)
            covered |= cand[h]
    for h in sorted(chosen):
        if h in self.loc:
            continue
        steps = self.find_chain(h)
        if steps is None:
            continue
        if pr.trace:
            print("hub", h, len(cand[h]), "cost", len(steps))
        self.rel.add(h)
        self.run_steps(steps)
        self.rel.add(h)
        self.trim()


def _seed_given(self):
    """해독한 숨은 밑을 작은 것부터 만든다 (quirk 의 기법: 목표값이 k*a*b + r 꼴일 때 a, b 를 먼저 만든다)."""
    pr = self.pr
    for g in sorted(pr.bases):
        if g in self.loc or g < 2 or g > self.limit:
            continue
        steps = self.find_chain(g)
        if steps is None:
            continue
        if pr.trace:
            print("base", g, len(steps), steps)
        self.rel.add(g)
        self.run_steps(steps)
        self.rel.add(g)
        self.trim()


def _seed_aux(self):
    """필요한 작은 값들을 가장 싼 것부터 만든다. 하나 만들 때마다 다시 재서, 서로를 재료로 쓰게 한다."""
    pr = self.pr
    rem = [v for v in sorted(set(pr.aux)) if v not in self.loc and 2 <= v <= self.limit]
    while rem:
        best = None
        for v in rem:
            steps = self.find_chain(v, ub=(len(best[1]) if best else pr.aux_max + 1))
            if steps is not None and len(steps) <= pr.aux_max and (best is None or len(steps) < len(best[1])):
                best = (v, steps)
                if len(steps) <= 1:
                    break
        if best is None:
            break
        if pr.trace:
            print("aux", best[0], len(best[1]), best[1])
        self.run_steps(best[1])
        self.trim()
        rem = [v for v in rem if v not in self.loc]


Machine.update_rel = _update_rel
Machine.seed_aux = _seed_aux
Machine.seed_given = _seed_given
Machine.seed_bases = _seed_bases
Machine.seed_hubs = _seed_hubs


def _solve_cheapest(self):
    """남은 목표값 가운데 지금 풀에서 가장 싸게 만들어지는 것부터 만든다.
    한 번 훑어 최소 비용을 찾고, 같은 비용 이하로 되는 것들을 이어서 만든다 (tie pass)."""
    pr = self.pr
    remaining = [t for t in sorted(self.targets) if t not in self.produced]
    if pr.aux and pr.aux_pre:
        self.seed_aux()
    if pr.bases:
        self.seed_given()
    if pr.aux:
        self.seed_aux()
    if pr.hubseed:
        self.seed_hubs()
    if pr.seed:
        self.seed_bases()
    last = {t: 0 for t in remaining}

    def build(t, steps):
        if pr.trace:
            def fmt(x):
                return str(x) if x < 10**7 else f"<{x.bit_length()}b:{x}>"
            print(f"{t} ({t.bit_length()}b) cost {len(steps)}: " + " ".join(f"{op}({fmt(x)},{fmt(y)})" for op, x, y in steps))
        return self.commit(t, steps, remaining)

    while True:
        remaining = [t for t in remaining if t not in self.produced]
        if not remaining:
            break
        self.update_rel(remaining)
        remaining.sort(key=lambda t: (last[t], t))
        bestc = None
        bests = None
        bt = None
        alpha = pr.alpha
        if alpha:
            # 비용에서 "크기에 따른 기대 비용"을 뺀 값이 가장 작은 목표값을 고른다
            bestk = None
            for t in remaining:
                tb = alpha * t.bit_length()
                if bestk is None:
                    ub = None
                else:
                    ub = int(bestk + tb - 1e-9) + 1      # cost - tb < bestk  <=>  cost < bestk + tb
                    if ub <= 0:
                        continue
                steps = self.find_chain(t, ub=ub)
                if steps is None:
                    continue
                k = len(steps) - tb
                if bestk is None or k < bestk:
                    bestk = k
                    bestc = len(steps)
                    bests = steps
                    bt = t
        else:
            for t in remaining:
                steps = self.find_chain(t, ub=bestc)
                if steps is None:
                    if bestc is not None and last[t] < bestc:
                        last[t] = bestc
                    continue
                last[t] = len(steps)
                if bestc is None or len(steps) < bestc:
                    bestc = len(steps)
                    bests = steps
                    bt = t
                    if bestc <= 1:
                        break
        if bests is None:
            return None
        if not build(bt, bests):
            return None
        if pr.tiepass:
            for t in remaining:
                if t in self.produced or last[t] > bestc + pr.tieslack:
                    continue
                steps = self.find_chain(t, ub=bestc + 1)
                if steps is not None:
                    last[t] = len(steps)
                    build(t, steps)
    return self.prog


Machine.solve_cheapest = _solve_cheapest


def solve(puzzle, **kw):
    if kw.get("vcap"):
        import vchain
        return vchain.solve(puzzle, **kw)
    m = Machine(puzzle, Params(**kw))
    return m.solve()


def solve_tiny(puzzle, max_states=400000):
    """value_limit 이 작을 때: '지금까지 만든 값 집합'을 상태로 한 너비 우선 탐색 (최적해).
    상태가 max_states 를 넘으면 None."""
    limit = puzzle.limit
    start = 0
    for v in set(puzzle.start):
        start |= 1 << v
    goal = 0
    for t in puzzle.targets:
        goal |= 1 << t
    if start & goal == goal:
        return []
    parent = {start: None}
    frontier = [start]
    found = None
    while frontier and found is None:
        nxt = []
        for mask in frontier:
            vals = [v for v in range(1, limit + 1) if mask >> v & 1]
            seen_new = set()
            for i, a in enumerate(vals):
                for b in vals[i:]:
                    cands = [("+", a, b, a + b), ("*", a, b, a * b)]
                    if b > a:
                        cands.append(("-", b, a, b - a))
                    if b % a == 0:
                        cands.append(("/", b, a, b // a))
                    for op, x, y, r in cands:
                        if 1 <= r <= limit and not mask >> r & 1 and r not in seen_new:
                            seen_new.add(r)
                            nm = mask | 1 << r
                            if nm not in parent:
                                parent[nm] = (mask, op, x, y, r)
                                if nm & goal == goal:
                                    found = nm
                                    break
                                nxt.append(nm)
                    if found is not None:
                        break
                if found is not None:
                    break
            if found is not None:
                break
            if len(parent) > max_states:
                return None
        frontier = nxt
    if found is None:
        return None
    seq = []
    m = found
    while parent[m] is not None:
        pm, op, x, y, r = parent[m]
        seq.append((op, x, y, r))
        m = pm
    seq.reverse()
    loc = {}
    for i, v in enumerate(puzzle.start):
        loc.setdefault(v, i)
    nxt_reg = len(puzzle.start)
    prog = []
    for op, x, y, r in seq:
        prog.append([op, loc[x], loc[y], nxt_reg])
        loc[r] = nxt_reg
        nxt_reg += 1
    return prog


def solve_any(puzzle, deadline=None, **kw):
    if puzzle.limit <= 24:
        prog = solve_tiny(puzzle)
        if prog is not None:
            return prog
    return solve(puzzle, **kw)
