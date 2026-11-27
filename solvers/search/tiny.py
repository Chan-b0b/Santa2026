"""value_limit 이 작은 퍼즐의 최적해: 가진 값 집합(비트마스크)을 상태로 한 BFS.

레지스터 48개 >= 값의 종류 수이므로 만든 값을 전부 보관할 수 있고,
명령 하나는 새 값 하나를 더하는 것과 같다. 따라서 BFS 깊이가 곧 최소 명령 수다.
"""
def solve_tiny(pz, max_states=2000000):
    L = pz.limit
    start = 0
    for v in pz.start:
        start |= 1 << v
    goal = 0
    for t in pz.targets:
        goal |= 1 << t
    if start & goal == goal:
        return []
    parent = {start: None}
    frontier = [start]
    found = None
    while frontier and found is None:
        nxt = []
        for st in frontier:
            vals = [v for v in range(1, L + 1) if st >> v & 1]
            seen = 0
            for i, x in enumerate(vals):
                for y in vals[:i + 1]:
                    for op, v, a, b in (('+', x + y, x, y), ('-', x - y, x, y), ('*', x * y, x, y),
                                        ('/', x // y if x % y == 0 else 0, x, y)):
                        if 1 <= v <= L and not (st >> v & 1) and not (seen >> v & 1):
                            seen |= 1 << v
                            ns = st | (1 << v)
                            if ns not in parent:
                                parent[ns] = (st, op, a, b, v)
                                if ns & goal == goal:
                                    found = ns
                                    break
                                nxt.append(ns)
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
    steps = []
    st = found
    while parent[st] is not None:
        ps, op, a, b, v = parent[st]
        steps.append((op, a, b, v))
        st = ps
    steps.reverse()
    reg = {}
    for i, v in enumerate(pz.start):
        reg.setdefault(v, i)
    used = len(pz.start)
    prog = []
    for op, a, b, v in steps:
        prog.append([op, reg[a], reg[b], used])
        reg[v] = used
        used += 1
    return prog
