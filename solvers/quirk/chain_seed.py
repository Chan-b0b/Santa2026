"""chain 솔버(읽기 전용 import)에 해독한 정수를 씨앗으로 넣는다: Machine.seed_bases 를 바꿔 끼운다.
사용: chain_seed.py <id> <씨앗,쉼표>"""
import sys, time
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/chain')
from verify import load_puzzles, check_program

CFG = dict(digits=4, W=16, pol=0, order='cheap', s1m=2, f2=0, seed=4, relkeep=2, rel_shift=12, alpha=0.16, vcap=160, vsoft=45, tie_s1=1, hot=30)

def solve(pz, bases, kw=None):
    import chain
    from prune import prune
    bases = list(bases)
    def _seed(self):
        for g in bases:
            if g in self.loc or g < 1 or g > self.limit: continue
            steps = self.find_chain(g)
            if steps is None: continue
            self.rel.add(g); self.run_steps(steps); self.rel.add(g); self.trim()
    orig = chain.Machine.seed_bases
    if bases: chain.Machine.seed_bases = _seed
    try:
        c = dict(CFG); c.update(kw or {})
        prog = chain.solve_any(pz, **c)
    finally:
        chain.Machine.seed_bases = orig
    if prog is None or check_program(pz, prog) is not None: return None
    pr = prune(pz, prog)
    if len(pr) < len(prog) and check_program(pz, pr) is None: prog = pr
    return prog

if __name__ == '__main__':
    pid = sys.argv[1]
    seeds = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 and sys.argv[2] else []
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    for sd in ([], seeds):
        t0 = time.time(); prog = solve(P[pid], sd)
        print('seeds', sd, '->', len(prog) if prog else None, f'{time.time()-t0:.1f}s')
