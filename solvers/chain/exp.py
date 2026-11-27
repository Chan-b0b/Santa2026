import sys, time, csv, json
sys.path.insert(0, "/home/maverick/Santa2026/core"); sys.path.insert(0, "/home/maverick/Santa2026/solvers/chain")
from verify import load_puzzles, check_program
import chain
P = load_puzzles("/home/maverick/Santa2026/data/practice_puzzles.csv")
fam = {r["id"]: r["family"] for r in csv.DictReader(open("/home/maverick/Santa2026/data/practice_puzzles.csv"))}
def run(ids, **kw):
    tot = 0; t0 = time.time(); out = {}
    for i in ids:
        p = P[i]
        prog = chain.solve(p, **kw)
        if prog is None:
            print(i, "FAIL"); tot += 9999; continue
        e = check_program(p, prog)
        if e: print(i, "INVALID", e); continue
        out[i] = len(prog); tot += len(prog)
    return tot, time.time() - t0, out
if __name__ == "__main__":
    byfam = {}
    for i, f in fam.items(): byfam.setdefault(f, []).append(i)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    kws = eval(sys.argv[2])
    for kw in kws:
        res = []
        for f in (sys.argv[3].split(",") if len(sys.argv) > 3 else ("independent", "mixed", "shared", "multiplicative", "tiny")):
            ids = byfam[f][:n]
            tot, dt, out = run(ids, **kw)
            lb = sum(P[i].lower_bound for i in ids)
            res.append(f"{f[:5]} {tot/len(ids):6.1f} ({tot/max(lb,1):.2f}/t, {dt/len(ids):.2f}s)")
        print(kw, " | ".join(res), flush=True)
