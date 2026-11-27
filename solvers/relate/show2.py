import sys, json
sys.path.insert(0, '/home/maverick/Santa2026/core'); sys.path.insert(0, '/home/maverick/Santa2026/solvers/relate')
from verify import load_puzzles
import importlib
pid = sys.argv[1]; seeds = tuple(int(x) for x in sys.argv[2].split(',')) if len(sys.argv) > 2 and sys.argv[2] else ()
mod = importlib.import_module(sys.argv[3] if len(sys.argv) > 3 else 'solver3')
P = load_puzzles('/home/maverick/Santa2026/data/practice_puzzles.csv' if pid.startswith('practice') else '/home/maverick/Santa2026/data/puzzles.csv')
pz = P[pid]
cfg = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1, "seeds": seeds}
if len(sys.argv) > 4: cfg.update(json.loads(sys.argv[4]))
s = mod.Solver(pz, cfg)
orig = s.emit_tree
def fmt(tr):
    if type(tr) is int: return str(tr)
    return '(' + fmt(tr[1]) + tr[0] + fmt(tr[2]) + ')'
depth = [0]; last = [0]
def emit_tree(tr, key=True):
    if depth[0] == 0:
        print(f'  [{len(s.vals)-last[0]:2d}] n={len(s.vals)}', fmt(tr)); last[0] = len(s.vals)
    depth[0] += 1
    r = orig(tr, key)
    depth[0] -= 1
    return r
s.emit_tree = emit_tree
try:
    prog = s.solve()
    print('len', len(prog) if prog else None)
except Exception as e:
    print('ERR', repr(e), 'vals', len(s.vals))
