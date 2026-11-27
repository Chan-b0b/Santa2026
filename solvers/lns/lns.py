#!/usr/bin/env python3
"""lns: 완성된 프로그램을 다시 합성해 줄인다.

1. 유효한 프로그램을 SSA(값 하나 = 명령 하나)로 바꾸고 죽은 명령을 지운다.
2. 목표값 t 하나를 골라, t 를 만드는 명령과 t 만을 위해 존재하던 조상 명령(전용 사슬)을 떼어 낸다.
3. t 를 처음 쓰는 명령 바로 앞(쓰는 명령이 없으면 프로그램 끝)에서 t 를 다시 유도한다.
   그 시점까지 만들어진 값 가운데 레지스터 수명을 늘려도 48개를 넘지 않는 값 전부가 풀이다.
   처음 만들 때는 앞쪽 목표값일수록 풀이 작았으므로, 뒤로 옮기면 더 짧은 사슬이 나온다.
4. 새 사슬이 더 짧고 레지스터 배정이 되면 채택한다.

탐색은 chain 접근법의 find_chain(일반화된 Horner 역방향 beam)을 사본(chain_snap.py)으로 빌려 쓴다.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "core"))
from chain_snap import Machine, Params  # noqa: E402
from verify import check_program  # noqa: E402


def apply(op, x, y):
    if op == "+":
        return x + y
    if op == "-":
        return x - y
    if op == "*":
        return x * y
    return x // y


class SSA:
    def __init__(self, pz, program):
        self.pz = pz
        self.ns = ns = len(pz.start)
        self.val = list(pz.start)
        self.op = [None] * ns
        self.A = [-1] * ns
        self.B = [-1] * ns
        reg = {i: i for i in range(ns)}
        order = []
        for op, ra, rb, rd in program:
            x, y = reg[ra], reg[rb]
            self.val.append(apply(op, self.val[x], self.val[y]))
            self.op.append(op)
            self.A.append(x)
            self.B.append(y)
            nid = len(self.val) - 1
            reg[rd] = nid
            order.append(nid)
        first = {}
        for i in list(range(ns)) + order:
            first.setdefault(self.val[i], i)
        self.req = {}                       # 목표값 -> 그 값을 내는 노드 (시작값에 있는 목표값은 제외)
        for t in set(pz.targets):
            i = first[t]
            if i >= ns:
                self.req[t] = i
        self.order = order
        self.dce()
        self.fail = ""

    # ---- 기본 연산 -----------------------------------------------------
    def dce(self):
        need = set(self.req.values())
        ns = self.ns
        for n in reversed(self.order):
            if n in need:
                a, b = self.A[n], self.B[n]
                if a >= ns:
                    need.add(a)
                if b >= ns:
                    need.add(b)
        self.order = [n for n in self.order if n in need]

    def emit(self, order=None):
        """마지막 사용 시점으로 레지스터를 배정해 프로그램을 만든다. 레지스터가 모자라면 None."""
        order = self.order if order is None else order
        ns, nreg = self.ns, self.pz.registers
        A, B = self.A, self.B
        lu = {}
        for T, n in enumerate(order):
            lu[A[n]] = T
            lu[B[n]] = T
        regof = {}
        free = list(range(nreg - 1, ns - 1, -1))
        for i in range(ns - 1, -1, -1):
            if i in lu:
                regof[i] = i
            else:
                free.append(i)
        prog = []
        for T, n in enumerate(order):
            a, b = A[n], B[n]
            ra, rb = regof[a], regof[b]
            if lu[a] == T:
                free.append(regof.pop(a))
            if b != a and lu[b] == T:
                free.append(regof.pop(b))
            if not free:
                return None
            rd = free.pop()
            prog.append([self.op[n], ra, rb, rd])
            if n in lu:
                regof[n] = rd
            else:
                free.append(rd)
        return prog

    def liveness(self, order, hole):
        """pos, lu, acr.  acr[T] = T 번째 명령을 실행할 때, 그 전에 만들어졌고 그 뒤에도 쓰이는 값의 수.
        hole 노드(정의가 빠진 목표값)는 세지 않는다."""
        A, B = self.A, self.B
        n = len(order)
        pos = {x: i for i, x in enumerate(order)}
        lu = {}
        for T, x in enumerate(order):
            lu[A[x]] = T
            lu[B[x]] = T
        diff = [0] * (n + 2)
        for x, l in lu.items():
            if x == hole:
                continue
            d = pos.get(x, -1)
            if l > d + 1:
                diff[d + 1] += 1
                diff[l] -= 1
        acr = []
        c = 0
        for T in range(n):
            c += diff[T]
            acr.append(c)
        return pos, lu, acr

    def private(self, a):
        """a 의 정의를 지우면 함께 죽는 노드 목록 (a 포함)."""
        A, B, ns = self.A, self.B, self.ns
        uses = {}
        for n in self.order:
            x, y = A[n], B[n]
            uses[x] = uses.get(x, 0) + 1
            uses[y] = uses.get(y, 0) + 1
        R = set(self.req.values())
        removed = [a]
        work = [A[a], B[a]]
        while work:
            x = work.pop()
            if x < ns:
                continue
            uses[x] -= 1
            if uses[x] == 0 and x not in R:
                removed.append(x)
                work.append(A[x])
                work.append(B[x])
        return removed

    def pool_at(self, order0, pos, lu, acr, p, hole, cap):
        """order0 의 p 번째 명령 바로 앞에서 쓸 수 있는 값 -> (노드, 이미 살아 있는가, 마지막 사용)."""
        M = [0] * (p + 1)
        for k in range(p - 1, -1, -1):
            M[k] = acr[k] if acr[k] > M[k + 1] else M[k + 1]
        pool = {}
        val = self.val
        for x in list(range(self.ns)) + order0[:p]:
            if x == hole:
                continue
            d = pos.get(x, -1)
            l = lu.get(x, d)
            if l >= p:
                alive = True
            else:
                start = l if l > d else d + 1
                if M[start] > cap:
                    continue
                alive = False
            v = val[x]
            o = pool.get(v)
            if o is None or (alive and not o[1]) or (alive == o[1] and l > o[2]):
                pool[v] = (x, alive, l)
        return pool

    # ---- 이동 ----------------------------------------------------------
    def try_target(self, t, m, slack=2, positions="late"):
        """목표값 t 를 다시 유도한다. 줄어든 명령 수를 돌려준다 (0 이면 변화 없음)."""
        self.fail = ""
        a = self.req[t]
        removed = self.private(a)
        oldcost = len(removed)
        if oldcost <= 1:
            return 0
        rs = set(removed)
        order = self.order
        order0 = [n for n in order if n not in rs]
        n0 = len(order0)
        A, B = self.A, self.B
        pos, lu, acr = self.liveness(order0, a)
        pc = n0
        for T, n in enumerate(order0):
            if A[n] == a or B[n] == a:
                pc = T
                break
        cands = [pc]
        if positions != "late":
            oldpos = order.index(a)
            p_old = sum(1 for n in order[:oldpos] if n not in rs)
            if p_old < pc:
                if positions == "all":
                    step = max(1, (pc - p_old) // 4)
                    cands += list(range(pc - step, p_old, -step))
                cands.append(p_old)
        cap = 46 - slack
        for p in cands:
            pool = self.pool_at(order0, pos, lu, acr, p, a, cap)
            if t in pool:                                   # 같은 값이 이미 있다: 그 노드를 쓰게 한다
                y = pool[t][0]
                saved = [(n, A[n], B[n]) for n in order0 if A[n] == a or B[n] == a]
                for n, _, _ in saved:
                    if A[n] == a:
                        A[n] = y
                    if B[n] == a:
                        B[n] = y
                if self.emit(order0) is not None:
                    self.req[t] = y
                    self.order = order0
                    return oldcost
                for n, x, y0 in saved:
                    A[n], B[n] = x, y0
                self.fail = "reg"
                continue
            m.loc = dict.fromkeys(pool, 0)
            m.dirty = True
            steps = m.find_chain(t, ub=oldcost)
            if steps is None:
                continue
            nval = len(self.val)
            keep = (self.op[a], A[a], B[a])
            valmap = {v: e[0] for v, e in pool.items()}
            new = []
            for op, x, y in steps:
                v = apply(op, x, y)
                if v in valmap:
                    continue
                nx, ny = valmap[x], valmap[y]
                if v == t:
                    nid = a
                    self.op[a], A[a], B[a] = op, nx, ny
                else:
                    nid = len(self.val)
                    self.val.append(v)
                    self.op.append(op)
                    A.append(nx)
                    B.append(ny)
                valmap[v] = nid
                new.append(nid)
            ok = valmap.get(t) == a and len(new) < oldcost
            if ok:
                order1 = order0[:p] + new + order0[p:]
                if self.emit(order1) is not None:
                    self.order = order1
                    return oldcost - len(new)
                self.fail = "reg"
            del self.val[nval:], self.op[nval:], A[nval:], B[nval:]
            self.op[a], A[a], B[a] = keep
        return 0

    def merge_dups(self):
        """같은 값을 두 번 만든 곳이 있으면 뒤의 것을 앞의 것으로 바꿔 본다."""
        saved_total = 0
        A, B = self.A, self.B
        again = True
        while again:
            again = False
            seen = {}
            for n in list(range(self.ns)) + self.order:
                v = self.val[n]
                x = seen.get(v)
                if x is None:
                    seen[v] = n
                    continue
                users = [(u, A[u], B[u]) for u in self.order if A[u] == n or B[u] == n]
                for u, _, _ in users:
                    if A[u] == n:
                        A[u] = x
                    if B[u] == n:
                        B[u] = x
                old_order = self.order
                self.dce()
                if self.emit() is not None:
                    saved_total += len(old_order) - len(self.order)
                    again = True
                    break
                self.order = old_order
                for u, a0, b0 in users:
                    A[u], B[u] = a0, b0
        return saved_total


DEFAULT = dict(W=32, s1m=2, f2=0, near=1, maxcost=60, seed=0, relkeep=0)


def improve(pz, program, passes=3, positions="late", params=None, stats=None):
    """프로그램을 줄여 본다. (새 프로그램, 정보) 를 돌려준다. 새 프로그램은 항상 유효하다."""
    s = SSA(pz, program)
    m = Machine(pz, Params(**(params or DEFAULT)))
    info = {"in": len(program), "dce": len(s.order)}
    info["dup"] = s.merge_dups()
    moves = 0
    for _ in range(passes):
        gain = 0
        for t in sorted(s.req, key=lambda t: s.order.index(s.req[t])):
            if t not in s.req:
                continue
            g = s.try_target(t, m, 2, positions)
            if not g and s.fail == "reg":
                g = s.try_target(t, m, 8, positions)
            if g:
                gain += g
                moves += 1
        if not gain:
            break
    prog = s.emit()
    if prog is None:
        return program, info
    err = check_program(pz, prog)
    if err is not None:
        raise RuntimeError(f"{pz.id}: lns 결과가 무효: {err}")
    info["out"] = len(prog)
    info["moves"] = moves
    return (prog if len(prog) < len(program) else program), info
