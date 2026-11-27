"""씨앗(해독 정수)을 넣은 구성: gen2.py pid solver(relate|chain) k  (프로젝트 루트에서 실행)"""
import sys, json, time, random, os
R = "/home/maverick/Santa2026"; os.chdir(R)
sys.path[:0] = ["core", "solvers/relate", "solvers/chain", "solvers/quirk"]
from verify import load_puzzles, check_program
BASES = json.load(open(R + "/solvers/fresh/bases_pick.json"))
BASE_CFG = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}
# k: (정수 선택 방식, 설정)
VAR = {
 0: ("full", {}), 1: ("sorted", dict(rseed=1, noise=1.0, rootpick=1)), 2: ("shuf", dict(rseed=2, noise=1.0, rootpick=1, W2=12)),
 3: ("half", {}), 4: ("shuf", dict(rseed=4, noise=1.0, rootpick=1, QN=28, qgap=14)), 5: ("rsorted", dict(rseed=5, noise=1.0, rootpick=1)),
 6: ("full", {}), 7: ("sorted", {}), 8: ("shuf", dict(seed=0)), 9: ("half", {}),
}
def pick(b, mode, rng):
    b = list(b)
    if mode == "sorted": return sorted(b)
    if mode == "rsorted": return sorted(b, reverse=True)
    if mode == "shuf": rng.shuffle(b); return b
    if mode == "half": return b[:max(1, (len(b) + 1) // 2)]
    return b
if __name__ == "__main__":
    pid, solver, k = sys.argv[1], sys.argv[2], int(sys.argv[3])
    pz = load_puzzles("data/puzzles.csv")[pid]; t0 = time.time()
    mode, cfg = VAR[k]; sv = pick(BASES[pid], mode, random.Random(k * 7 + 1)); prog = None
    try:
        if solver == "relate":
            import solver3
            c = dict(BASE_CFG); c.update(cfg); c["seeds"] = tuple(sv)
            prog, _, _ = solver3.solve_once(pz, c)
        else:
            import chain_seed
            prog = chain_seed.solve(pz, sv, cfg)
        ok = prog is not None and check_program(pz, prog) is None
    except Exception as e:
        sys.stderr.write(repr(e) + "\n"); ok = False
    sys.stderr.write(f"gen2 {solver} {k} {mode} nb={len(sv)} {time.time()-t0:.1f}s len {len(prog) if ok else None}\n")
    print(json.dumps(prog) if ok else "NONE")
