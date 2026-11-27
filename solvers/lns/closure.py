"""시작값에서 식 트리 크기(연산 수)별로 만들 수 있는 값의 집합 E_k 와, 목표값의 최소 트리 분해(MITM).

E_0 = 시작값, E_k = 연산 k개짜리 식 트리의 값(공유 없음). 사용: closure.py <practice id> [K]
"""
import csv, json, sys, time
sys.path.insert(0, __file__.rsplit('/', 1)[0])

def closure(seeds, limit, K, cap=3_000_000):
    """level[k] = {값: (op, a, b)}  값이 처음 나온 최소 k 에만 넣는다."""
    seen = {}
    level = [dict()]
    for s in seeds:
        if s not in seen:
            seen[s] = 0; level[0][s] = None
    for k in range(1, K + 1):
        cur = {}
        for i in range(0, k):
            j = k - 1 - i
            if i > j:
                break
            A, B = level[i], level[j]
            for a in A:
                for b in B:
                    for op, v in (('+', a + b), ('*', a * b), ('-', a - b), ('-', b - a)):
                        if 0 < v <= limit and v not in seen and v not in cur:
                            cur[v] = (op, a, b) if not (op == '-' and v == b - a) else ('-', b, a)
                    if b and a % b == 0:
                        v = a // b
                        if v not in seen and v not in cur: cur[v] = ('/', a, b)
                    if a and b % a == 0:
                        v = b // a
                        if v not in seen and v not in cur: cur[v] = ('/', b, a)
                if len(cur) > cap:
                    break
            if len(cur) > cap:
                break
        for v in cur: seen[v] = k
        level.append(cur)
    return level, seen

def expr(v, level, seen, depth=0):
    k = seen[v]
    if k == 0: return str(v)
    op, a, b = level[k][v]
    return f"({expr(a, level, seen)}{op}{expr(b, level, seen)})"

def decompose(t, level, seen, limit):
    """t 의 최소 트리 크기 분해: 직접(E_k) 또는 t = a op b (a, b 는 closure 안). (크기, 식) 또는 None."""
    best = None
    if t in seen:
        return seen[t], expr(t, level, seen)
    for a, ka in seen.items():
        for op, b in (('+', t - a), ('-', t + a), ('*', t // a if t % a == 0 else 0), ('/', t * a)):
            if b > 0 and b in seen and b <= limit:
                c = ka + seen[b] + 1
                if best is None or c < best[0]:
                    best = (c, a, op, b)
    if best is None:
        return None
    c, a, op, b = best
    if op == '+': s = f"{expr(a, level, seen)} + {expr(b, level, seen)}"
    elif op == '-': s = f"{expr(b, level, seen)} - {expr(a, level, seen)}"
    elif op == '*': s = f"{expr(a, level, seen)} * {expr(b, level, seen)}"
    else: s = f"{expr(b, level, seen)} / {expr(a, level, seen)}"
    return c, s

if __name__ == '__main__':
    rows = {r['id']: r for r in csv.DictReader(open('data/practice_puzzles.csv', newline='', encoding='utf-8'))}
    r = rows[sys.argv[1]]; K = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    seeds = json.loads(r['starting_values']); targets = json.loads(r['targets']); limit = int(r['value_limit'])
    t0 = time.time()
    level, seen = closure(seeds, limit, K)
    print(f"{r['id']} {r['family']} seeds={seeds} sizes={[len(l) for l in level]} {time.time()-t0:.1f}s")
    tot = 0; miss = 0
    for t in targets:
        d = decompose(t, level, seen, limit)
        if d is None:
            miss += 1; print(f"  {t:>18} {t.bit_length():2}b  -")
        else:
            tot += d[0]; print(f"  {t:>18} {t.bit_length():2}b  {d[0]:2}  {d[1]}")
    print(f"found {len(targets)-miss}/{len(targets)}, tree-size sum {tot}")
