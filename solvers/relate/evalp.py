"""연습 퍼즐 중 해독된 것에서 설정 비교 (파일 안 씀). 사용: pypy3 -I evalp.py <mod> '<cfg json>' [variant: bases|alt|none]"""
import sys, json, time, importlib
ROOT = '/home/maverick/Santa2026'
sys.path.insert(0, ROOT + '/core'); sys.path.insert(0, ROOT + '/solvers/relate')
from multiprocessing import Pool
from verify import load_puzzles, check_program
P = load_puzzles(ROOT + '/data/practice_puzzles.csv')
B = json.load(open(ROOT + '/solvers/relate/bases_practice.json'))
MOD = sys.argv[1]; CFG = json.loads(sys.argv[2]); VAR = sys.argv[3] if len(sys.argv) > 3 else 'bases'
def work(pid):
    mod = importlib.import_module(MOD)
    c = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}; c.update(CFG)
    if VAR not in ('none', 'all'): c["seeds"] = tuple(B[pid][VAR])
    try: prog, log, cap = mod.solve_once(P[pid], c)
    except Exception as e: prog = None
    if prog is None or check_program(P[pid], prog) is not None: return pid, None
    return pid, len(prog)
if __name__ == '__main__':
    t0 = time.time()
    ids = sorted(B) if VAR != 'all' else sorted(P)
    with Pool(int(sys.argv[4]) if len(sys.argv) > 4 else 5) as pool: res = dict(pool.map(work, ids, chunksize=1))
    ok = [v for v in res.values() if v is not None]
    print(MOD, CFG, VAR, 'n', len(ok), 'fail', len(res) - len(ok), 'total', sum(ok), f'{time.time()-t0:.0f}s')
