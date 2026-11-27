"""relate 솔버(읽기 전용으로 가져다 씀)에 씨앗 값을 넣어 길이를 비교한다.
사용: seedtest.py <id> <씨앗,쉼표> [cfg json]"""
import sys, json, time
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/relate')
from verify import load_puzzles, check_program
import solver3

def run(pz, seeds, cfg=None):
    c = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}
    c.update(cfg or {})
    if seeds: c["seeds"] = tuple(seeds)
    prog, log, cap = solver3.solve_once(pz, c)
    return prog, log, cap

if __name__ == '__main__':
    pid = sys.argv[1]
    seeds = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 and sys.argv[2] else []
    cfg = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    P = load_puzzles('data/practice_puzzles.csv' if pid.startswith('practice') else 'data/puzzles.csv')
    pz = P[pid]
    for sd in ([], seeds):
        t0 = time.time()
        prog, log, cap = run(pz, sd, cfg)
        print('seeds', sd, '->', len(prog) if prog else None, check_program(pz, prog) if prog else log, f'cap={cap} {time.time()-t0:.1f}s')
        if sd and prog and '-v' in sys.argv:
            for l in log: print('   ', l)
