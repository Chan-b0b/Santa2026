import sys, csv, json, time
from collections import Counter
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
import engine3 as E
pid = sys.argv[1]
with open(ROOT + "/data/practice_puzzles.csv") as f:
    row = [r for r in csv.DictReader(f) if r["id"] == pid][0]
st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
eng = E.Engine(st, tg, lim, cfg={}, deadline=time.time() + 600)
orig = eng.decomp_level
calls = [0]
def dl(v, bound):
    b, partials = orig(v, bound)
    calls[0] += 1
    if calls[0] % 40 == 0 and v.bit_length() > 50:
        F1 = eng.F1
        bits = Counter(x.bit_length() // 4 * 4 for x in F1)
        c = Counter(p[0] for p in partials)
        qb = Counter(p[1].bit_length() // 4 * 4 for p in partials)
        # how many partial q's are pair-able
        ok = 0; tried = 0
        for base, q, x, r, sign in sorted(partials)[:30]:
            tried += 1
            if eng.pair(q) is not None: ok += 1
        print("v bits", v.bit_length(), "P", len(eng.plist), "F1", len(F1), "L2", len(eng.L2), "best", b[0] if b else None,
              "partials", len(partials), "base", sorted(c.items()), "q bits", sorted(qb.items()), "pair ok %d/%d" % (ok, tried))
        print("    F1 bits hist", sorted(bits.items()))
    return b, partials
eng.decomp_level = dl
eng.solve()
print(len(eng.steps), eng.stats)
