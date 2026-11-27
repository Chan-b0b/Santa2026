"""해독한 밑을 넣었을 때와 뺐을 때의 chain 길이 비교.  사용: trybases.py <id> ..."""
import sys, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + '/core'); sys.path.insert(0, ROOT + '/solvers/chain')
from verify import load_puzzles, check_program
import chain, decode
P = load_puzzles(ROOT + '/data/puzzles.csv')
CFG = dict(digits=4, W=16, pol=0, order='cheap', s1m=2, f2=0, seed=4, relkeep=2, rel_shift=12, alpha=0.16, vcap=160, vsoft=45, tie_s1=1, hot=30)
for pid in sys.argv[1:]:
    p = P[pid]
    ch = decode.decode(p.targets)
    bs = [c[0] for c in ch]
    out = []
    for k in (0, 3, 5, 7):
        if k > len(bs) and k > 0 and k - 2 >= len(bs): continue
        t0 = time.time()
        prog = chain.solve_any(p, bases=tuple(bs[:k]), **CFG)
        ok = prog is not None and check_program(p, prog) is None
        out.append((k, len(prog) if ok else None, round(time.time() - t0, 1)))
    print(pid, bs, out, flush=True)
