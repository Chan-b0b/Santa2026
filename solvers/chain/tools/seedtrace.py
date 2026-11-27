import sys, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + '/core'); sys.path.insert(0, ROOT + '/solvers/chain')
from verify import load_puzzles, check_program
import chain
pid = sys.argv[1]
seeds = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 and sys.argv[2] else []
EXTRA = eval(sys.argv[3]) if len(sys.argv) > 3 else {}
P = load_puzzles(ROOT + '/data/puzzles.csv')
def _seed(self):
    for g in seeds:
        if g in self.loc: continue
        steps = self.find_chain(g)
        print('seed', g, len(steps), steps)
        self.rel.add(g); self.run_steps(steps); self.rel.add(g); self.trim()
chain.Machine.seed_bases = _seed
CFG = dict(digits=4, W=16, pol=0, order='cheap', s1m=2, f2=0, seed=4, relkeep=2, rel_shift=12, alpha=0.16, vcap=160, vsoft=45, tie_s1=1, hot=30, trace=1); CFG.update(EXTRA)
prog = chain.solve_any(P[pid], **CFG)
print(len(prog), check_program(P[pid], prog))
