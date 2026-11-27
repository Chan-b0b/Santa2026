import sys, time, json, importlib
sys.path.insert(0, '/home/maverick/Santa2026/core'); sys.path.insert(0, '/home/maverick/Santa2026/solvers/relate')
from verify import load_puzzles, check_program
mod = importlib.import_module(sys.argv[1])
P = load_puzzles('/home/maverick/Santa2026/data/puzzles.csv')
pid = sys.argv[2]
cfg = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}
if len(sys.argv) > 4: cfg.update(json.loads(sys.argv[4]))
for s in sys.argv[3].split('/'):
    sv = tuple(int(x) for x in s.split(',')) if s else ()
    t0 = time.time()
    c = dict(cfg); c["seeds"] = sv
    prog, log, cap = mod.solve_once(P[pid], c)
    print(pid, sv, None if prog is None else len(prog), 'cap', cap, f'{time.time()-t0:.2f}s', check_program(P[pid], prog) if prog else log, flush=True)
