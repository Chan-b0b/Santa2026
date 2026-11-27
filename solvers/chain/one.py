import sys, time
sys.path.insert(0, "/home/maverick/Santa2026/core"); sys.path.insert(0, "/home/maverick/Santa2026/solvers/chain")
from verify import load_puzzles, check_program
import chain
P = load_puzzles("/home/maverick/Santa2026/data/practice_puzzles.csv")
P.update(load_puzzles("/home/maverick/Santa2026/data/puzzles.csv"))
pid = sys.argv[1]
for kw in eval(sys.argv[2]):
    t0 = time.time()
    prog = chain.solve(P[pid], **kw)
    print(kw, len(prog) if prog else None, check_program(P[pid], prog) if prog else "", f"{time.time()-t0:.1f}s", flush=True)
