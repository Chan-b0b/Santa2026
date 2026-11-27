"""목표값이 주어진 값들에서 1~3단계로 유도되는 비율을 family 별로 본다."""
import sys, csv, json
from collections import defaultdict
sys.path.insert(0, "/home/maverick/Santa2026/solvers/factor")

def ops1(vals, limit):
    out = {}
    vs = sorted(set(vals))
    for i, a in enumerate(vs):
        for b in vs[i:]:
            for v, d in ((a + b, ('+', a, b)), (b - a, ('-', b, a)), (a * b, ('*', a, b))):
                if 1 <= v <= limit and v not in out:
                    out[v] = d
            if b % a == 0 and (b // a) not in out:
                out[b // a] = ('/', b, a)
    return out

with open("data/practice_puzzles.csv") as f:
    rows = list(csv.DictReader(f))
stat = defaultdict(lambda: [0, 0, 0, 0, 0])
for r in rows:
    st = json.loads(r["starting_values"]); tg = json.loads(r["targets"]); lim = int(r["value_limit"])
    fam = r["family"]
    known = set(st) | set(tg)
    P1 = ops1(known, lim)
    for t in tg:
        if t in st:
            continue
        others = known - {t}
        p1 = ops1(others, lim)
        s = stat[fam]
        s[0] += 1
        if t in p1:
            s[1] += 1
            continue
        # 2-step: t = x op c, x in p1, c in others
        found = False
        for c in others:
            for x in (t - c, t + c, c - t, t * c):
                if x in p1:
                    found = True; break
            if not found and t % c == 0 and t // c in p1: found = True
            if not found and c % t == 0 and c // t in p1: found = True
            if found: break
        if found:
            s[2] += 1
            continue
        # 3-step: t = x op y, x,y in p1
        for x in p1:
            for y in (t - x, t + x, x - t, t * x):
                if y in p1:
                    found = True; break
            if not found and t % x == 0 and t // x in p1: found = True
            if not found and x % t == 0 and x // t in p1: found = True
            if found: break
        if found:
            s[3] += 1
        else:
            s[4] += 1
for fam, s in stat.items():
    print(fam, "targets", s[0], "1-step", s[1], "2-step", s[2], "3-step(bal)", s[3], "none", s[4])
