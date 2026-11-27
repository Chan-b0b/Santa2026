import sys, time, json
sys.path.insert(0, '/home/maverick/Santa2026/core'); sys.path.insert(0, '/home/maverick/Santa2026/solvers/relate')
from verify import load_puzzles, check_program
import solver3
P = load_puzzles('/home/maverick/Santa2026/data/puzzles.csv')
pid = sys.argv[1]; seeds = tuple(int(x) for x in sys.argv[2].split(',')) if len(sys.argv) > 2 and sys.argv[2] else ()
cfg = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}
for sv in [(), seeds, tuple(sorted(seeds)), tuple(sorted(seeds, reverse=True))]:
    t0 = time.time()
    c = dict(cfg); c["seeds"] = sv
    prog, log, cap = solver3.solve_once(P[pid], c)
    print(pid, sv, None if prog is None else len(prog), 'cap', cap, f'{time.time()-t0:.2f}s', check_program(P[pid], prog) if prog else log)
