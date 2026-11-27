"""value_limit 이 작은 퍼즐의 정확해: 값 집합(비트마스크)을 상태로 한 너비 우선 탐색."""


def solve_tiny(pz, max_limit=40, max_states=400000):
    """최단 프로그램(명령 목록)을 돌려준다. 범위를 벗어나거나 상태가 너무 많으면 None."""
    L = pz.limit
    if L > max_limit:
        return None
    start_mask = 0
    for s in pz.start:
        start_mask |= 1 << s
    goal = 0
    for t in pz.targets:
        goal |= 1 << t
    if start_mask & goal == goal:
        return []
    parent = {start_mask: None}
    frontier = [start_mask]
    found = None
    while frontier and found is None:
        nxt = []
        for mask in frontier:
            vals = [v for v in range(1, L + 1) if mask >> v & 1]
            cand = {}
            for i, a in enumerate(vals):
                for b in vals[i:]:
                    s = a + b
                    if s <= L and not mask >> s & 1 and s not in cand:
                        cand[s] = ("+", a, b)
                    m = a * b
                    if m <= L and not mask >> m & 1 and m not in cand:
                        cand[m] = ("*", a, b)
                    if b > a:
                        d = b - a
                        if not mask >> d & 1 and d not in cand:
                            cand[d] = ("-", b, a)
                        if b % a == 0:
                            q = b // a
                            if not mask >> q & 1 and q not in cand:
                                cand[q] = ("/", b, a)
                    else:
                        if not mask & 2 and 1 not in cand:
                            cand[1] = ("/", a, a)
            for v, ins in cand.items():
                nm = mask | (1 << v)
                if nm in parent:
                    continue
                parent[nm] = (mask, ins, v)
                if nm & goal == goal:
                    found = nm
                    break
                nxt.append(nm)
            if found is not None:
                break
            if len(parent) > max_states:
                return None
        frontier = nxt
    if found is None:
        return None
    steps = []
    m = found
    while parent[m] is not None:
        pm, ins, v = parent[m]
        steps.append((ins, v))
        m = pm
    steps.reverse()
    # 레지스터 배정: 값마다 새 레지스터 (값이 L 개 이하라 48 개를 넘지 않게 확인)
    reg = {}
    for i, s in enumerate(pz.start):
        reg.setdefault(s, i)
    nxt_reg = len(pz.start)
    prog = []
    for (op, a, b), v in steps:
        if nxt_reg >= pz.registers:
            return None
        prog.append([op, reg[a], reg[b], nxt_reg])
        reg[v] = nxt_reg
        nxt_reg += 1
    return prog
