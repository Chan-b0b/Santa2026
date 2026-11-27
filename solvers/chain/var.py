import sys, time, csv
sys.path.insert(0, "/home/maverick/Santa2026/core"); sys.path.insert(0, "/home/maverick/Santa2026/solvers/chain")
from verify import load_puzzles, check_program
import chain
P = load_puzzles("/home/maverick/Santa2026/data/practice_puzzles.csv")
fam = {r["id"]: r["family"] for r in csv.DictReader(open("/home/maverick/Santa2026/data/practice_puzzles.csv"))}
byfam = {}
for i, f in fam.items(): byfam.setdefault(f, []).append(i)
kws = eval(sys.argv[2])
for f in sys.argv[1].split(","):
    ids = byfam[f][:int(sys.argv[3])]
    res = []
    for kw in kws:
        row = []
        for i in ids:
            prog = chain.solve(P[i], **kw)
            assert check_program(P[i], prog) is None
            row.append(len(prog))
        res.append(row)
        print(f, kw, sum(row), row, flush=True)
    mins = [min(r[j] for r in res) for j in range(len(ids))]
    print(f, "best-of", sum(mins), mins)
