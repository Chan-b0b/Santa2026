import sys, csv
sys.path.insert(0, "/home/maverick/Santa2026/core")
from verify import load_puzzles
P = load_puzzles("/home/maverick/Santa2026/data/practice_puzzles.csv")
fam = {r["id"]: r["family"] for r in csv.DictReader(open("/home/maverick/Santa2026/data/practice_puzzles.csv"))}
def s1(vals, limit):
    out = {}
    vals = sorted(vals)
    for i, a in enumerate(vals):
        for b in vals[i:]:
            for v, e in ((a+b, ("+", a, b)), (b-a, ("-", b, a)), (a*b, ("*", a, b))):
                if 1 <= v <= limit and v not in out: out[v] = e
            if a > 0 and b % a == 0 and b//a not in out: out[b//a] = ("/", b, a)
    return out
def probe(pid, verbose=False):
    p = P[pid]
    known = set(p.start) | set(p.targets)
    S1 = s1(known, p.limit)
    n1 = n2 = 0
    res = []
    for t in p.targets:
        if t in p.start: continue
        others = known - {t}
        S1o = s1(others, p.limit) if len(others) < 60 else S1
        if t in S1o:
            n1 += 1; res.append((t, 1, S1o[t])); continue
        found = None
        for c in others:
            for v, e in ((t - c, "+"), (t + c, "-"), (c - t, "r-"), (t * c, "/")):
                if v > 0 and v in S1o and v != t:
                    found = (S1o[v], e, c); break
            if found: break
            if t % c == 0 and (t // c) in S1o:
                found = (S1o[t//c], "*", c); break
        if found:
            n2 += 1; res.append((t, 2, found))
        else:
            res.append((t, None, None))
    if verbose:
        for r in res: print("   ", r)
    return n1, n2, len(res)
if __name__ == "__main__":
    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0, 0])
    for pid in sorted(P)[:80]:
        a, b, n = probe(pid)
        f = fam[pid]
        agg[f][0] += a; agg[f][1] += b; agg[f][2] += n
    for f, (a, b, n) in agg.items(): print(f, "1op", a, "2op", b, "of", n)
    probe("practice_0007", True)
