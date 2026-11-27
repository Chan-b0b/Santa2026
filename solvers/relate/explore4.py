import sys, csv, json, time
sys.path.insert(0, 'solvers/relate')
rows = {r['id']: r for r in csv.DictReader(open('data/practice_puzzles.csv'))}
r = rows[sys.argv[1]]
s = json.loads(r['starting_values']); T = json.loads(r['targets']); L = int(r['value_limit'])
maxn = int(sys.argv[2]) if len(sys.argv) > 2 else 4
E = [dict((v, None) for v in s)]
seen = dict(E[0])
t0 = time.time()
def comb(A, B, out, same):
    for a in A:
        for b in B:
            if same and b > a: continue
            v = a + b
            if v <= L and v not in seen and v not in out: out[v] = (a, '+', b)
            v = a * b
            if v <= L and v not in seen and v not in out: out[v] = (a, '*', b)
            if a > b:
                v = a - b
                if v not in seen and v not in out: out[v] = (a, '-', b)
                if a % b == 0:
                    v = a // b
                    if v not in seen and v not in out: out[v] = (a, '/', b)
            elif b > a:
                v = b - a
                if v not in seen and v not in out: out[v] = (b, '-', a)
                if b % a == 0:
                    v = b // a
                    if v not in seen and v not in out: out[v] = (b, '/', a)
for n in range(1, maxn + 1):
    out = {}
    for i in range(0, (n - 1) // 2 + 1):
        j = n - 1 - i
        comb(E[i], E[j], out, i == j)
    E.append(out)
    seen.update(out)
    print(n, len(out), time.time() - t0, flush=True)
def expr(v):
    d = seen[v]
    if d is None: return str(v)
    return f"({expr(d[0])}{d[1]}{expr(d[2])})"
lvl = {}
for n, e in enumerate(E):
    for v in e: lvl[v] = n
for t in T:
    if t in seen:
        print(t, lvl[t], expr(t)); continue
    # MITM: t = x op y
    best = None
    for x in seen:
        for y, desc in ((t - x, '+'), (t + x, '-'), (x - t, 'r-'), (t * x, '/')):
            if y in seen:
                c = lvl[x] + lvl[y] + 1
                if best is None or c < best[0]: best = (c, x, desc, y)
        if t % x == 0 and t // x in seen:
            y = t // x
            c = lvl[x] + lvl[y] + 1
            if best is None or c < best[0]: best = (c, x, '*', y)
    if best:
        print(t, best[0], expr(best[1]), best[2], expr(best[3]))
    else:
        print(t, None)
