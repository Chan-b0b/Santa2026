"""다중 출발 재합성 일괄 실행: 퍼즐마다 모든 접근법의 결과(results/*.csv, best)를 출발점으로 lns 재합성기 사본을 돌려
현재 best 보다 짧은 것을 results/quirk.csv 에 쓴다. 작은 퍼즐(목표 수 적음)에서 재합성이 빨라 효과가 있다.
사용: msbatch.py [--maxnt 18] [--minnt 1] [--secs 6] [--seeds 2] [--procs 4] [--ids a,b]"""
import sys, os, json, glob, time, argparse
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles, check_program, read_submission, write_submission
import polish

P = load_puzzles('data/puzzles.csv')
OUT = 'results/quirk.csv'

def work(job):
    pid, starts, secs, nseeds, seed0 = job
    pz = P[pid]; best = None; src = None
    seen = set()
    for name, prog in starts:
        key = json.dumps(prog)
        if key in seen: continue
        seen.add(key)
        for s in range(nseeds):
            new = polish.lns(pz, prog, secs, seed0 + s)
            if new is not None and (best is None or len(new) < len(best)): best = new; src = name
    return pid, best, src

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--maxnt', type=int, default=18)
    ap.add_argument('--minnt', type=int, default=1)
    ap.add_argument('--secs', type=float, default=6)
    ap.add_argument('--seeds', type=int, default=2)
    ap.add_argument('--procs', type=int, default=4)
    ap.add_argument('--ids', default='')
    ap.add_argument('--seed0', type=int, default=300)
    a = ap.parse_args()
    files = sorted(glob.glob('results/*.csv')) + ['best/best.csv']
    cells = {}
    for f in files:
        try: cells[f] = read_submission(f)
        except Exception: pass
    cur = {pid: len(json.loads(c)) for pid, c in cells['best/best.csv'].items()}
    ids = a.ids.split(',') if a.ids else [pid for pid, p in sorted(P.items()) if a.minnt <= len(p.targets) <= a.maxnt and p.limit > 64]
    jobs = []
    for pid in ids:
        st = []
        for f, c in cells.items():
            if pid in c:
                prog = json.loads(c[pid])
                if check_program(P[pid], prog) is None: st.append((os.path.basename(f), prog))
        jobs.append((pid, st, a.secs, a.seeds, a.seed0))
    print(f'{len(jobs)} puzzles', flush=True)
    t0 = time.time(); n = 0; gain = 0; better = 0; new = {}
    def save():
        mine = {pid: json.loads(c) for pid, c in read_submission(OUT).items()} if os.path.exists(OUT) else {}
        for pid, prog in new.items():
            if pid not in mine or len(prog) < len(mine[pid]): mine[pid] = prog
        write_submission(OUT, mine)
    with Pool(a.procs) as pool:
        for pid, prog, src in pool.imap_unordered(work, jobs):
            n += 1
            if prog is not None and len(prog) < cur[pid]:
                new[pid] = prog; better += 1; gain += cur[pid] - len(prog)
                print(f'{pid} best {cur[pid]} -> {len(prog)} (from {src})', flush=True)
            if n % 10 == 0 or n == len(jobs):
                if new: save(); new.clear()
                print(f'[{time.time()-t0:.0f}s] {n}/{len(jobs)} better {better} gain {gain}', flush=True)
    print('done')

if __name__ == '__main__':
    main()
