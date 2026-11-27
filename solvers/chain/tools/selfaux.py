"""자기 결과에서 여러 번 쓰인 작은 값을 뽑아 보조 목표로 넣고 다시 푸는 실험.  사용: selfaux.py <id> [밑,쉼표|auto|none]"""
import sys, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + '/core'); sys.path.insert(0, ROOT + '/solvers/chain'); sys.path.insert(0, ROOT + '/solvers/chain/tools')
from verify import load_puzzles, check_program
import chain, decode
from replay import ssa_of
P = load_puzzles(ROOT + '/data/puzzles.csv')
CFG = dict(digits=4, W=16, pol=0, order='cheap', s1m=2, f2=0, seed=0, relkeep=2, rel_shift=12, alpha=0.16, vcap=160, vsoft=45, tie_s1=1, hot=30)
pid = sys.argv[1]
p = P[pid]
arg = sys.argv[2] if len(sys.argv) > 2 else 'auto'
bs = () if arg == 'none' else tuple(c[0] for c in decode.decode(p.targets)) if arg == 'auto' else tuple(int(x) for x in arg.split(','))

def harvest(prog, small=1 << 14, minuse=2):
    vals, nodes = ssa_of(p, prog)
    k = len(p.start)
    uses = [0] * len(vals)
    for op, a, b, r in nodes:
        uses[a] += 1; uses[b] += 1
    return tuple(sorted(set(vals[i] for i in range(k, len(vals)) if vals[i] <= small and uses[i] >= minuse)))

def run(**kw):
    c = dict(CFG); c.update(kw)
    t0 = time.time(); prog = chain.solve_any(p, **c)
    ok = prog is not None and check_program(p, prog) is None
    return prog if ok else None, round(time.time() - t0, 1)

prog, tm = run(bases=bs)
print(pid, 'bases', bs, 'pass1', len(prog), tm)
for minuse in (2, 3):
    cur = prog
    for it in range(3):
        aux = harvest(cur, minuse=minuse)
        res = []
        for amax, pre in ((1, 1), (2, 1), (1, 0)):
            pr2, tm = run(bases=bs, aux=aux, aux_max=amax, aux_pre=pre)
            res.append((len(pr2) if pr2 else None, amax, pre, pr2))
        res.sort(key=lambda x: (x[0] is None, x[0]))
        print(f'  minuse={minuse} it={it} aux n={len(aux)} ->', [(r[0], r[1], r[2]) for r in res], flush=True)
        if res[0][0] is None or res[0][0] >= len(cur): break
        cur = res[0][3]
