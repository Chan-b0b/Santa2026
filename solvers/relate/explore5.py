import sys, time
start = [int(x) for x in sys.argv[1].split(',')]
L = int(sys.argv[2])
T = [int(x) for x in sys.argv[3].split(',')]
maxn = int(sys.argv[4]) if len(sys.argv) > 4 else 4
E = [dict((v, None) for v in start)]
seen = dict(E[0])
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
t0 = time.time()
for n in range(1, maxn + 1):
    out = {}
    for i in range(0, (n - 1) // 2 + 1):
        comb(E[i], E[n - 1 - i], out, i == n - 1 - i)
    E.append(out); seen.update(out)
    print(n, len(out), round(time.time() - t0, 1), flush=True)
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
    best = []
    for x in seen:
        for y, desc in ((t - x, '+'), (t + x, '-'), (x - t, 'r-'), (t * x, '/')):
            if y in seen:
                best.append((lvl[x] + lvl[y] + 1, x, desc, y))
        if t % x == 0 and t // x in seen:
            best.append((lvl[x] + lvl[t // x] + 1, x, '*', t // x))
    best.sort()
    for b in best[:3]:
        print(t, b[0], expr(b[1]), b[2], expr(b[3]))
    if not best: print(t, None)
