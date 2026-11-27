"""vchain: 수명(liveness) 기반 가상 풀.

chain.Machine 은 풀 값 46개를 항상 레지스터에 붙들고 있다. 실제로는 "앞으로 다시 쓰일 값"만
레지스터가 필요하다. 여기서는 명령을 SSA 로 기록하고(값 하나 = 명령 하나), 각 값이
정의 ~ 마지막 사용 구간에만 레지스터를 차지한다고 보고 동시 생존 값 수를 추적한다.
  cnt[T] = T 번째 명령을 실행할 때 살아 있어야 하는 값의 수 (정의 < T <= 마지막 사용)
오래전 값 x 를 지금 다시 쓰면 (x 의 마지막 사용, 지금] 구간의 cnt 가 1씩 는다. 그 구간의 최댓값이
여유 안에 있으면 x 는 "되살릴 수 있는 값"이고 탐색 풀에 넣는다. 그래서 탐색이 보는 풀이 48개보다 훨씬 크다.
끝에서 죽은 명령을 지우고 구간 정보로 레지스터를 배정한다 (cnt <= 47 이면 항상 성공).
"""
from __future__ import annotations
import chain
from chain import Machine, Params


class VMachine(Machine):
    def __init__(self, puzzle, params):
        super().__init__(puzzle, params)
        k = len(puzzle.start)
        self.nstart = k
        self.ssa = []                 # (op, ia, ib, 값). 결과의 id 는 k + 명령 번호
        self.known = {}               # 값 -> 가장 최근 인스턴스 id
        for i, v in enumerate(puzzle.start):
            self.known.setdefault(v, i)
        self.loc = dict(self.known)   # 탐색 풀: 값 -> id
        self.lu = [-1] * k            # id -> 마지막 사용 명령 번호 (시작값은 -1, 결과값은 자기 정의 번호)
        self.cnt = []
        self.banned = set()
        self.hard = puzzle.registers - 1
        self.suf = [0, 0]

    # ---- 명령 내기 -------------------------------------------------------
    def emit(self, op, x, y, protect=()):
        known = self.known
        ia = known[x]
        ib = known[y]
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
        if r in self.loc:
            return r
        T = len(self.ssa)
        cnt = self.cnt
        cnt.append(0)
        lu = self.lu
        for i in ((ia, ib) if ia != ib else (ia,)):
            u = lu[i]
            if u < T:
                for j in range(u + 1, T + 1):
                    cnt[j] += 1
                lu[i] = T
        self.ssa.append((op, ia, ib, r))
        nid = self.nstart + T
        lu.append(T)
        known[r] = nid
        self.loc[r] = nid
        self.produced.add(r)
        self.clock += 1
        self.birth[r] = self.clock
        self.dirty = True
        return r

    def run_steps(self, steps):
        for op, x, y in steps:
            self.emit(op, x, y)

    def trim(self):
        pass

    # ---- 되돌리기 ---------------------------------------------------------
    def checkpoint(self):
        return (len(self.ssa), list(self.cnt), list(self.lu), dict(self.known), dict(self.loc), set(self.produced))

    def rollback(self, cp):
        n, cnt, lu, known, loc, produced = cp
        del self.ssa[n:]
        self.cnt = cnt
        self.lu = lu
        self.known = known
        self.loc = loc
        self.produced = produced
        self.dirty = True

    def commit(self, t, steps, remaining):
        tries = 0
        while True:
            cp = self.checkpoint()
            self.run_steps(steps)
            cnt = self.cnt
            hard = self.hard
            bad = -1
            for j in range(len(cnt)):
                if cnt[j] > hard:
                    bad = j
                    break
            if bad < 0:
                break
            # 한도를 넘긴 구간을 지나가는 "되살린 값" 중 가장 오래된 것을 금지하고 다시 찾는다
            old_lu = cp[2]
            new_lu = self.lu
            worst = None
            for i in range(len(old_lu)):
                if new_lu[i] != old_lu[i] and old_lu[i] < bad:
                    if worst is None or old_lu[i] < old_lu[worst]:
                        worst = i
            self.rollback(cp)
            tries += 1
            if worst is None or tries > 12:
                self.banned.clear()
                return False
            v = self.puz_value(worst)
            self.banned.add(v)
            self.dirty = True
            steps = self.find_chain(t)
            if steps is None:
                self.banned.clear()
                return False
        if self.banned:
            self.banned.clear()
            self.dirty = True
        assert t in self.produced
        self.update_rel([x for x in remaining if x not in self.produced])
        return True

    def puz_value(self, i):
        if i < self.nstart:
            return self.pz.start[i]
        return self.ssa[i - self.nstart][3]

    # ---- 탐색 풀 고르기 ---------------------------------------------------
    def rebuild(self):
        T = len(self.ssa)
        cnt = self.cnt
        suf = [0] * (T + 2)
        m = 0
        for j in range(T - 1, -1, -1):
            if cnt[j] > m:
                m = cnt[j]
            suf[j] = m
        self.suf = suf
        soft = self.pr.vsoft
        lu = self.lu
        banned = self.banned
        cand = [(x, i) for x, i in self.known.items() if suf[lu[i] + 1] <= soft and x not in banned]
        vcap = self.pr.vcap
        if len(cand) > vcap:
            sc = self.score
            cand.sort(key=lambda c: -sc(c[0]))
            cand = cand[:vcap]
        self.loc = dict(cand)
        super().rebuild()

    def resid_order(self, vals):
        """가수 d 후보 순서. 최근에 쓰인(되살리는 구간이 짧은) 값을 먼저 둔다."""
        h = self.pr.hot
        if not h:
            return vals
        lim = len(self.ssa) - h
        lu = self.lu
        loc = self.loc
        hot = [v for v in vals if lu[loc[v]] >= lim]
        cold = [v for v in vals if lu[loc[v]] < lim]
        return hot + cold

    # ---- 마무리: 죽은 명령 제거 + 레지스터 배정 -----------------------------
    def finalize(self):
        k = self.nstart
        ssa = self.ssa
        n = len(ssa)
        missing = set(self.pz.targets) - set(self.pz.start)
        need = [False] * n
        for i in range(n):
            v = ssa[i][3]
            if v in missing:
                missing.discard(v)
                need[i] = True
        if missing:
            return None
        for i in range(n - 1, -1, -1):
            if need[i]:
                a, b = ssa[i][1], ssa[i][2]
                if a >= k:
                    need[a - k] = True
                if b >= k:
                    need[b - k] = True
        order = [i for i in range(n) if need[i]]
        lastuse = {}
        for pos, i in enumerate(order):
            lastuse[ssa[i][1]] = pos
            lastuse[ssa[i][2]] = pos
        reg_of = {}
        free = list(range(self.nreg - 1, k - 1, -1))
        for i in range(k):
            if i in lastuse:
                reg_of[i] = i
            else:
                free.append(i)
        prog = []
        for pos, i in enumerate(order):
            op, a, b, v = ssa[i]
            ra = reg_of[a]
            rb = reg_of[b]
            for x in ((a, b) if a != b else (a,)):
                if lastuse[x] == pos:
                    free.append(reg_of.pop(x))
            if not free:
                return None
            d = free.pop()
            prog.append([op, ra, rb, d])
            nid = k + i
            if nid in lastuse:
                reg_of[nid] = d
            else:
                free.append(d)
        return prog

    def solve(self):
        res = super().solve()
        if res is None:
            return None
        return self.finalize()


def solve(puzzle, **kw):
    m = VMachine(puzzle, Params(**kw))
    return m.solve()
