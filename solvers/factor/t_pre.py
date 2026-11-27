"""preseed 시험: python t_pre.py <id> <tl> <json preseed list> [cfg json]"""
import sys, json, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
from verify import load_puzzles, check_program
import engine3 as E
P = load_puzzles(ROOT + "/data/puzzles.csv")
pid = sys.argv[1]; tl = float(sys.argv[2]); pre = json.loads(sys.argv[3])
cfg = {"cap": 46, "refresh": 12, "beam": 2}
if len(sys.argv) > 4: cfg.update(json.loads(sys.argv[4]))
pz = P[pid]
for ps in ([], pre):
    c = dict(cfg); c["preseed"] = ps
    t0 = time.time()
    eng = E.Engine(pz.start, pz.targets, pz.limit, facs={}, cfg=c, deadline=time.time() + tl)
    steps = eng.solve()
    prog = E.emit(pz.start, steps, pz.registers)
    print(pid, "preseed", ps, "len", None if prog is None else len(prog), "err", None if prog is None else check_program(pz, prog), "%.1fs" % (time.time() - t0), dict(eng.stats))
