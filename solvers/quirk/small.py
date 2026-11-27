"""시작값에서의 트리 비용 닫힘과, 그 표를 이용한 작은 수의 최단 식 찾기(가운데서 만나기)."""
import sys

def levels(start, limit, depth, vmax=1 << 40, maxsize=2_000_000):
    """L[c] = 트리 비용이 정확히 c 인 값들 (값 -> 유도). 제곱은 x*x 를 비용 c(x)+1 로 친다."""
    cost = {s: 0 for s in start}; der = {s: None for s in start}
    L = [dict.fromkeys(start)]
    for d in range(1, depth + 1):
        new = {}
        def add(v, dd):
            if 1 <= v <= limit and v <= vmax and v not in cost and v not in new: new[v] = dd
        # 제곱/자기 자신 연산
        for a in L[d - 1]:
            add(a * a, ('*', a, a)); add(a + a, ('+', a, a)); add(1, ('/', a, a))
        for i in range(0, d):
            j = d - 1 - i
            if j < i: break
            for a in L[i]:
                for b in L[j]:
                    add(a + b, ('+', a, b)); add(a * b, ('*', a, b))
                    if a > b: add(a - b, ('-', a, b))
                    elif b > a: add(b - a, ('-', b, a))
                    if b and a % b == 0: add(a // b, ('/', a, b))
                    if a and b % a == 0: add(b // a, ('/', b, a))
            if len(new) > maxsize: break
        for v, dd in new.items(): cost[v] = d; der[v] = dd
        L.append(new)
        if len(new) > maxsize: break
    return cost, der, L

def expr(v, der):
    d = der.get(v)
    if d is None: return str(v)
    return '(' + expr(d[1], der) + d[0] + expr(d[2], der) + ')'

def mitm(v, cost, limit):
    """v = x op y, x 와 y 가 표에 있는 가장 싼 분해. (비용, op, x, y) 또는 None."""
    if v in cost: return (cost[v], None, v, None)
    best = None
    for x, cx in cost.items():
        if best is not None and cx + 1 >= best[0]: continue
        for op, y in (('+', v - x), ('-', v + x), ('r-', x - v)):
            if y > 0 and y in cost:
                c = cx + cost[y] + 1
                if best is None or c < best[0]: best = (c, op, x, y)
        if v % x == 0 and (v // x) in cost:
            c = cx + cost[v // x] + 1
            if best is None or c < best[0]: best = (c, '*', x, v // x)
        if v * x <= limit and (v * x) in cost:
            c = cx + cost[v * x] + 1
            if best is None or c < best[0]: best = (c, 'r/', x, v * x)
    return best

if __name__ == '__main__':
    sys.path.insert(0, 'core')
    from verify import load_puzzles
    pid = sys.argv[1]; vals = [int(x) for x in sys.argv[2].split(',')]; depth = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    p = P[pid]
    cost, der, L = levels(p.start, p.limit, depth)
    print(pid, p.start, 'levels', [len(x) for x in L])
    for v in vals:
        m = mitm(v, cost, p.limit)
        if m is None: print(v, 'not found'); continue
        c, op, x, y = m
        print(v, 'cost', c, expr(v, der) if op is None else f'{expr(x, der)} {op} {expr(y, der)}')
