import sys, json, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
from verify import load_puzzles, check_program
import engine3 as E
P = load_puzzles(ROOT + "/data/puzzles.csv")
for pid in sys.argv[2:]:
    pz = P[pid]
    t0 = time.time()
    eng = E.Engine(pz.start, pz.targets, pz.limit, facs={}, cfg={"cap": 46, "refresh": 12, "beam": 2}, deadline=time.time() + float(sys.argv[1]))
    steps = eng.solve()
    prog = E.emit(pz.start, steps, pz.registers)
    print(pid, "len", None if prog is None else len(prog), "%.1fs" % (time.time() - t0), "fallback", eng.stats.get("fallback#", 0), flush=True)
