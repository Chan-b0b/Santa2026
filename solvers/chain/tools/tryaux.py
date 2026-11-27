"""밑 + 필요한 작은 값(aux) what-if.  사용: tryaux.py <id> <밑,쉼표|auto> """
import sys, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + '/core'); sys.path.insert(0, ROOT + '/solvers/chain')
from verify import load_puzzles, check_program
import chain, decode
P = load_puzzles(ROOT + '/data/puzzles.csv')
CFG = dict(digits=4, W=16, pol=0, order='cheap', s1m=2, f2=0, seed=0, relkeep=2, rel_shift=12, alpha=0.16, vcap=160, vsoft=45, tie_s1=1, hot=30)
pid = sys.argv[1]
p = P[pid]
bs = [c[0] for c in decode.decode(p.targets)] if sys.argv[2] == 'auto' else [int(x) for x in sys.argv[2].split(',')]
ex, need = decode.explain(p.targets, bs)
print(pid, 'bases', bs, 'explained', len(ex), '/', len(p.targets), 'need', len(need))
def run(**kw):
    c = dict(CFG); c.update(kw)
    t0 = time.time(); prog = chain.solve_any(p, **c)
    ok = prog is not None and check_program(p, prog) is None
    return (len(prog) if ok else None, round(time.time() - t0, 1))
print('no bases', run())
print('bases', run(bases=tuple(bs)))
for cmin in (1, 2):
    aux = tuple(v for v, c in need.items() if c >= cmin)
    for amax in (1, 2):
        for pre in (0, 1):
            print(f'aux cmin={cmin} n={len(aux)} amax={amax} pre={pre}', run(bases=tuple(bs), aux=aux, aux_max=amax, aux_pre=pre), flush=True)
