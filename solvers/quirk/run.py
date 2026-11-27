"""quirk 실행기: 해독한 숨은 정수를 relate 솔버(읽기 전용 import)의 씨앗으로 넣어 다시 푼다.
퍼즐별로 여러 씨앗 조합과 설정을 시도해 가장 짧은 유효 프로그램을 results/quirk.csv 에 쓴다.
사용: run.py [--procs 6] [--budget 20] [--ids a,b,c] [--only-with-bases]"""
import sys, os, json, time, argparse, random
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/relate'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles, check_program, write_submission, read_submission

P = load_puzzles('data/puzzles.csv')
OUT = 'results/quirk.csv'
BASE_CFG = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}
ARGS = None

def variants(bases, extra, rng):
    """씨앗 조합 후보. bases 는 설명 범위 순서."""
    out = []
    n = len(bases)
    out.append(tuple(bases))
    for k in range(n - 1, 0, -1): out.append(tuple(bases[:k]))
    out.append(tuple(sorted(bases)))
    out.append(tuple(sorted(bases, reverse=True)))
    if extra: out.append(tuple(bases) + tuple(extra))
    for _ in range(4):
        b = list(bases); rng.shuffle(b); out.append(tuple(b))
    seen = set(); res = []
    for v in out:
        if v and v not in seen: seen.add(v); res.append(v)
    return res

def work(job):
    pid, bases, extra, cur, budget = job
    import solver3
    pz = P[pid]; t0 = time.time(); rng = random.Random(hash(pid) & 0xffff)
    best = None; tried = 0; how = None
    cfgs = [dict(BASE_CFG)]
    for i in range(1, 9):
        c = dict(BASE_CFG); c["rseed"] = i; c["noise"] = 1.0; c["rootpick"] = 1
        v = i % 4
        if v == 1: c["W2"] = 12
        elif v == 2: c["QN"] = 28; c["qgap"] = 14
        elif v == 3: c["s1depth"] = 1
        else: c["cshift"] = 2
        cfgs.append(c)
    vs = variants(bases, extra, rng)
    for ci, cfg in enumerate(cfgs):
        for sv in vs:
            if time.time() - t0 > budget and best is not None: break
            c = dict(cfg); c["seeds"] = sv
            try:
                prog, log, cap = solver3.solve_once(pz, c)
            except Exception as e:
                prog = None
            tried += 1
            if prog is not None and check_program(pz, prog) is None and (best is None or len(prog) < len(best)):
                best = prog; how = (ci, sv)
        if time.time() - t0 > budget: break
    return pid, best, how, tried, time.time() - t0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procs', type=int, default=6)
    ap.add_argument('--budget', type=float, default=20)
    ap.add_argument('--ids', default='')
    ap.add_argument('--bases', default='solvers/quirk/bases.json')
    ap.add_argument('--minexp', type=int, default=2, help='설명된 목표가 이 수 이상인 퍼즐만')
    a = ap.parse_args()
    bases = json.load(open(a.bases))
    cur = {pid: len(json.loads(c)) for pid, c in read_submission('best/best.csv').items()}
    mine = {}
    if os.path.exists(OUT):
        for pid, c in read_submission(OUT).items(): mine[pid] = json.loads(c)
    ids = a.ids.split(',') if a.ids else sorted(bases)
    jobs = []
    for pid in ids:
        b = bases.get(pid)
        if not b or not b['bases'] or len(b['cov']) < a.minexp: continue
        jobs.append((pid, b['bases'], b.get('extra', []), cur[pid], a.budget))
    print(f'{len(jobs)} puzzles with bases', flush=True)
    t0 = time.time(); n = 0; gain = 0; better = 0
    with Pool(a.procs) as pool:
        for pid, prog, how, tried, dt in pool.imap_unordered(work, jobs):
            n += 1
            if prog is not None:
                if pid not in mine or len(prog) < len(mine[pid]):
                    mine[pid] = prog
                if len(prog) < cur[pid]:
                    better += 1; gain += cur[pid] - len(prog)
                print(f'{pid} best {cur[pid]} quirk {len(prog)} ({len(prog)-cur[pid]:+d}) tried {tried} {dt:.0f}s seeds {how[1] if how else None}', flush=True)
            else:
                print(f'{pid} failed tried {tried}', flush=True)
            if n % 20 == 0 or n == len(jobs):
                write_submission(OUT, mine)
                print(f'[{time.time()-t0:.0f}s] {n}/{len(jobs)} done, better than best: {better} puzzles, gain {gain}', flush=True)
    write_submission(OUT, mine)
    print(f'done {time.time()-t0:.0f}s: better {better}, gain {gain}')

if __name__ == '__main__':
    main()
