import sys, random, time
sys.path.insert(0, "/home/maverick/Santa2026/core"); sys.path.insert(0, "/home/maverick/Santa2026/solvers/chain")
from verify import Puzzle
import chain

def build_F2(S1, vals, limit):
    F2 = {}
    for c in vals:
        for s in S1:
            v = s + c
            if v <= limit: F2[v] = s
            v = s * c
            if v <= limit: F2[v] = s
            if s > c: F2[s - c] = s
            elif c > s: F2[c - s] = s
    return F2

def split_cost(t, pool, S1, F2, limit):
    best = 99; info = None
    D = {}
    for v in S1: D[v] = 1
    for v in pool: D[v] = 0
    def scan(keys, c1cost):
        nonlocal best, info
        for c1 in keys:
            if c1 < 2 or c1 >= t: continue
            q, r = divmod(t, c1)
            if r in D:
                cc = F2.get(q)
                if q in D: c = c1cost + D[q] + 2 + D[r]
                elif q in F2: c = c1cost + 2 + 2 + D[r]
                else: continue
                if c < best: best = c; info = (c1, q, r, "+")
            r2 = c1 - r
            if r2 in D:
                q2 = q + 1
                if q2 in D: c = c1cost + D[q2] + 2 + D[r2]
                elif q2 in F2: c = c1cost + 2 + 2 + D[r2]
                else: continue
                if c < best: best = c; info = (c1, q2, r2, "-")
    scan(list(S1), 1)
    scan(list(F2), 2)
    return best, info

def test(T, gen, n=20, seed=1, npool=46):
    rnd = random.Random(seed)
    tc = ts = tm = 0; t0 = time.time(); hist = {}
    tb = tsc = 0
    for it in range(n):
        vals = set()
        while len(vals) < npool: vals.add(gen(rnd))
        t = rnd.randrange(2**(T-1), 2**T)
        limit = int(2**T * 1.3)
        pz = Puzzle("x", tuple(sorted(vals)), (t,), limit, 48)
        m = chain.Machine(pz, chain.Params(W=64, digits=0))
        steps = m.find_chain(t)
        c = len(steps)
        a = time.time()
        F2 = build_F2(m.S1, m.vals, limit)
        tb += time.time() - a; a = time.time()
        s, info = split_cost(t, m.loc, m.S1, F2, limit)
        tsc += time.time() - a
        tc += c; ts += s; tm += min(c, s)
        k = (c, s); hist[k] = hist.get(k, 0) + 1
    return f"chain {tc/n:.2f} split {ts/n:.2f} min {tm/n:.2f} |F2|={len(F2)} build {tb/n:.2f}s scan {tsc/n:.2f}s", sorted(hist.items())
if __name__ == "__main__":
    gens = {
      "b10": lambda r: r.randrange(2**9, 2**10),
      "b11": lambda r: r.randrange(2**10, 2**11),
      "b12": lambda r: r.randrange(2**11, 2**12),
      "b13": lambda r: r.randrange(2**12, 2**13),
      "lu6-13": lambda r: int(2**r.uniform(6, 13)),
      "lu2-12": lambda r: int(2**r.uniform(1, 12)),
    }
    for T in (40, 49, 60):
        for name, g in gens.items():
            print(T, name, test(T, g), flush=True)
