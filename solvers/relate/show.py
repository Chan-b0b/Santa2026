import sys, csv
sys.path.insert(0, '/home/maverick/Santa2026/core'); sys.path.insert(0, '/home/maverick/Santa2026/solvers/relate')
from verify import load_puzzles
import importlib
mod = importlib.import_module(sys.argv[2] if len(sys.argv) > 2 else 'solver3')
pid = sys.argv[1]
P = load_puzzles('/home/maverick/Santa2026/data/practice_puzzles.csv' if pid.startswith('practice') else '/home/maverick/Santa2026/data/puzzles.csv')
pz = P[pid]
print(pz.start, pz.limit)
s = mod.Solver(pz, {})
orig = s.emit_tree
def fmt(tr):
    if type(tr) is int: return str(tr)
    return '(' + fmt(tr[1]) + tr[0] + fmt(tr[2]) + ')'
depth = [0]
def emit_tree(tr, key=True):
    if depth[0] == 0: print('   ', fmt(tr))
    depth[0] += 1
    r = orig(tr, key)
    depth[0] -= 1
    return r
s.emit_tree = emit_tree
_end = s.end_derivation
def end():
    if s.log: print(s.log[-1])
    _end()
prog = s.solve()
print(s.log[-1])
print('len', len(prog) if prog else None)
