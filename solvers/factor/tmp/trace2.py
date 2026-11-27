import sys, json, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
from verify import load_puzzles, check_program
import engine3 as E
P = load_puzzles(ROOT + "/data/puzzles.csv")
pid = sys.argv[1]; pre = json.loads(sys.argv[2])
pz = P[pid]
eng = E.Engine(pz.start, pz.targets, pz.limit, facs={}, cfg={"cap": 46, "refresh": 12, "beam": 2, "preseed": pre}, deadline=time.time() + 40)
orig = eng.apply
tset = set(pz.targets)
def apply(steps, tag=None):
    print("[%s] %d steps, pool %d" % (tag, len(steps), len(eng.pool)))
    for v, op, a, b in steps:
        print("     %s%d = %d %s %d" % ("T " if v in tset else "  ", v, a, op, b))
    return orig(steps, tag)
eng.apply = apply
steps = eng.solve()
prog = E.emit(pz.start, steps, pz.registers)
print("len", len(prog))
