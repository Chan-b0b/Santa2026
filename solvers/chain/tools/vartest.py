"""설정 변형 대 보조값 무작위 부분집합 비교 실험.  사용: vartest.py <id> ..."""
import sys, time, json, random
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + '/core'); sys.path.insert(0, ROOT + '/solvers/chain'); sys.path.insert(0, ROOT + '/solvers/chain/tools')
from verify import load_puzzles, check_program, read_submission
import chain
import run2
P = load_puzzles(ROOT + '/data/puzzles.csv')
SEEDS = json.load(open(ROOT + '/solvers/chain/seeds.json'))
CUR = read_submission(ROOT + '/results/chain.csv')
for pid in sys.argv[1:]:
    p = P[pid]
    cur = json.loads(CUR[pid])
    bs = tuple(b[0] for b in SEEDS.get(pid, []))
    aux = run2.harvest(p, cur)
    def run(aux=aux, **kw):
        c = dict(run2.BASE); c.update(dict(bases=bs, seed=0 if bs else 4, aux=aux, aux_max=2, aux_pre=1)); c.update(kw)
        t0 = time.time(); prog = chain.solve_any(p, **c)
        ok = prog is not None and check_program(p, prog) is None
        return (len(prog) if ok else None, round(time.time() - t0, 1))
    print(pid, 'cur', len(cur), 'bases', len(bs), 'aux', len(aux), flush=True)
    print('  base', run())
    for name, kw in (('W32', dict(W=32)), ('a.10', dict(alpha=0.10)), ('a.22', dict(alpha=0.22)), ('s1m3', dict(s1m=3)), ('f2', dict(f2=1)), ('hot0', dict(hot=0)), ('tie0', dict(tie_s1=0)), ('vs43', dict(vsoft=43)), ('dig2', dict(digits=2)), ('dig0', dict(digits=0)), ('amax3', dict(aux_max=3))):
        print('  ', name, run(**kw), flush=True)
    rnd = random.Random(1)
    out = []
    for k in range(6):
        sub = tuple(v for v in aux if rnd.random() < 0.75)
        out.append(run(aux=sub)[0])
    print('   subsets', out, flush=True)
