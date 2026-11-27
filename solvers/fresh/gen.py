"""새 프로그램 하나 만들기: gen.py pid solver k -> JSON 프로그램을 stdout 마지막 줄에 (실패면 NONE)"""
import sys, json, time, random
R = "/home/maverick/Santa2026"
sys.path[:0] = [R + "/core", R + "/solvers/" + sys.argv[2]]
from verify import load_puzzles, check_program

CHAIN = [
 dict(digits=4, W=16, pol=0, order='cheap', s1m=2, f2=0, seed=4, relkeep=2, rel_shift=12, alpha=0.16, vcap=160, vsoft=45, tie_s1=1, hot=30),
 dict(digits=3, W=16, pol=0, order='cheap', s1m=2, f2=0, seed=4, relkeep=2, rel_shift=12, alpha=0.10, vcap=160, vsoft=45, tie_s1=1, hot=30),
 dict(digits=5, W=24, pol=0, order='cheap', s1m=2, f2=0, seed=4, relkeep=2, rel_shift=12, alpha=0.25, vcap=160, vsoft=45, tie_s1=1, hot=30),
 dict(digits=4, W=16, pol=0, order='asc', s1m=2, f2=0, seed=4, relkeep=2, rel_shift=12, alpha=0.16, vcap=160, vsoft=45, tie_s1=1, hot=30),
 dict(digits=4, W=16, pol=1, order='cheap', s1m=1, f2=1, seed=0, relkeep=2, rel_shift=12, alpha=0.16, vcap=140, vsoft=42, tie_s1=1, hot=20),
 dict(digits=4, W=32, pol=0, order='cheap', s1m=2, f2=0, seed=2, relkeep=2, rel_shift=12, alpha=0.05, vcap=160, vsoft=48, tie_s1=0, hot=30, preseed=10),
]
RELATE = [
 dict(W2=6, rootK=40, rootKslack=99, relfrac=0.1, budget=0, restarts=0),
 dict(W2=6, rootK=40, rootKslack=99, relfrac=0.1, budget=0, restarts=0, rseed=11, noise=1.0, rootpick=1),
 dict(W2=12, rootK=40, rootKslack=99, relfrac=0.1, budget=0, restarts=0, rseed=12, noise=1.0, rootpick=1),
 dict(W2=6, QN=28, rootK=40, rootKslack=99, relfrac=0.1, budget=0, restarts=0, rseed=13, noise=1.0, rootpick=1),
 dict(W2=6, rootK=40, rootKslack=99, relfrac=0.1, budget=0, restarts=0, rseed=14, noise=1.5, rootpick=1),
]
SEARCH = [
 dict(), dict(seed=1), dict(evict='band', vcap=110, seed=2), dict(seed=3, ntop=3),
 dict(evict='big', vcap=130, seed=4), dict(evict='quota', vcap=110, quota=70, seed=6),
]
FACTOR = [
 dict(cap=46, refresh=6, beam=2), dict(cap=46, refresh=6, beam=2, seed=3),
 dict(cap=46, refresh=12, beam=2, seed=5), dict(cap=40, refresh=6, beam=2, seed=7),
]
CFGS = dict(chain=CHAIN, relate=RELATE, search=SEARCH, factor=FACTOR)

def make(pz, solver, k):
    if solver == "chain":
        import chain
        return chain.solve(pz, **CHAIN[k])
    if solver == "relate":
        import solver3
        p, _ = solver3.solve_puzzle(pz, RELATE[k])[:2]
        return p
    if solver == "search":
        import solver as S
        return S.solve_puzzle(pz, **SEARCH[k])
    if solver == "factor":
        import run as FR
        FR._FACS.update(FR.load_facs("scored"))
        import engine3 as E
        prog, err, st = FR._solve_cfg(pz, FACTOR[k], 20)
        return prog

if __name__ == "__main__":
    pid, solver, k = sys.argv[1], sys.argv[2], int(sys.argv[3])
    pz = load_puzzles(R + "/data/puzzles.csv")[pid]
    t0 = time.time()
    try:
        prog = make(pz, solver, k)
        ok = prog is not None and check_program(pz, prog) is None
    except Exception as e:
        sys.stderr.write(repr(e) + "\n"); ok = False
    sys.stderr.write(f"gen {solver} {k} {time.time()-t0:.1f}s len {len(prog) if ok else None}\n")
    print(json.dumps(prog) if ok else "NONE")
