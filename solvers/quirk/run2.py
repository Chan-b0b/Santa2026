"""quirk 실행기 2판: 해독한 숨은 정수를 relate 와 chain 두 솔버의 씨앗으로 넣어 풀고(읽기 전용 import),
엔진별 최단 프로그램을 각각 lns 재합성기 사본으로 다듬어 가장 짧은 것을 results/quirk.csv 에 쓴다.
사용: run2.py [--procs 5] [--budget 12] [--lns 15] [--bases solvers/quirk/bases2.json] [--ids a,b] [--skip-same <이전 bases json>]"""
import sys, os, json, time, argparse, random
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/relate'); sys.path.insert(0, 'solvers/chain'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles, check_program, write_submission, read_submission

P = load_puzzles('data/puzzles.csv')
OUT = 'results/quirk.csv'
BASE_CFG = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}

def variants(bases, rng, nshuf=3):
    out = [tuple(bases)]
    n = len(bases)
    for k in range(n - 1, 0, -1): out.append(tuple(bases[:k]))
    out.append(tuple(sorted(bases)))
    out.append(tuple(sorted(bases, reverse=True)))
    for _ in range(nshuf):
        b = list(bases); rng.shuffle(b); out.append(tuple(b))
    seen = set(); res = []
    for v in out:
        if v and v not in seen: seen.add(v); res.append(v)
    return res

def work(job):
    pid, bases, budget, lns_secs = job
    import solver3, chain_seed, polish
    pz = P[pid]; rng = random.Random(hash(pid) & 0xffff)
    vs = variants(bases, rng)
    # --- relate
    t0 = time.time(); best_rel = None
    cfgs = [dict(BASE_CFG)]
    for i in range(1, 5):
        c = dict(BASE_CFG); c["rseed"] = i; c["noise"] = 1.0; c["rootpick"] = 1
        v = i % 4
        if v == 1: c["W2"] = 12
        elif v == 2: c["QN"] = 28; c["qgap"] = 14
        elif v == 3: c["s1depth"] = 1
        else: c["cshift"] = 2
        cfgs.append(c)
    for cfg in cfgs:
        for sv in vs:
            if time.time() - t0 > budget and best_rel is not None: break
            c = dict(cfg); c["seeds"] = sv
            try: prog, log, cap = solver3.solve_once(pz, c)
            except Exception: prog = None
            if prog is not None and check_program(pz, prog) is None and (best_rel is None or len(prog) < len(best_rel)): best_rel = prog
        if time.time() - t0 > budget: break
    # --- chain
    t0 = time.time(); best_ch = None
    for sv in vs:
        if time.time() - t0 > budget and best_ch is not None: break
        try: prog = chain_seed.solve(pz, sv)
        except Exception: prog = None
        if prog is not None and (best_ch is None or len(prog) < len(best_ch)): best_ch = prog
        if time.time() - t0 > budget: break
    raw = [p for p in (best_rel, best_ch) if p is not None]
    if not raw: return pid, None, None
    info = (len(best_rel) if best_rel else None, len(best_ch) if best_ch else None)
    best = min(raw, key=len)
    if lns_secs > 0:
        for i, p in enumerate(raw):
            new = polish.lns(pz, p, lns_secs, 7 + i)
            if new is not None and len(new) < len(best): best = new
    return pid, best, info

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procs', type=int, default=5)
    ap.add_argument('--budget', type=float, default=12)
    ap.add_argument('--lns', type=float, default=15)
    ap.add_argument('--ids', default='')
    ap.add_argument('--bases', default='solvers/quirk/bases2.json')
    ap.add_argument('--skip-same', default='')
    ap.add_argument('--minexp', type=int, default=3)
    ap.add_argument('--nofinal', action='store_true', help='정수 목록을 거르지 않고 그대로 쓴다 (decode6 결과용)')
    a = ap.parse_args()
    bases = json.load(open(a.bases))
    old = json.load(open(a.skip_same)) if a.skip_same else {}
    cur = {pid: len(json.loads(c)) for pid, c in read_submission('best/best.csv').items()}
    ids = a.ids.split(',') if a.ids else sorted(bases)
    jobs = []
    import decode2
    for pid in ids:
        b = bases.get(pid)
        if not b or not b['bases']: continue
        if a.nofinal:
            B = list(b['bases'])
        else:
            B, cov = decode2.finalize(P[pid].targets, b['bases'], minexp=a.minexp)
        if not B: continue
        if old and pid in old and sorted(old[pid]['bases']) == sorted(B): continue
        jobs.append((pid, B[:8], a.budget, a.lns))
    print(f'{len(jobs)} puzzles', flush=True)
    t0 = time.time(); n = 0; gain = 0; better = 0
    def save(new):
        mine = {pid: json.loads(c) for pid, c in read_submission(OUT).items()} if os.path.exists(OUT) else {}
        for pid, prog in new.items():
            if pid not in mine or len(prog) < len(mine[pid]): mine[pid] = prog
        write_submission(OUT, mine)
    new = {}
    with Pool(a.procs) as pool:
        for pid, prog, info in pool.imap_unordered(work, jobs):
            n += 1
            if prog is not None:
                new[pid] = prog
                if len(prog) < cur[pid]: better += 1; gain += cur[pid] - len(prog)
                print(f'{pid} best {cur[pid]} quirk {len(prog)} ({len(prog)-cur[pid]:+d}) raw relate/chain {info}', flush=True)
            else:
                print(f'{pid} failed', flush=True)
            if n % 10 == 0 or n == len(jobs):
                save(new); new = {}
                print(f'[{time.time()-t0:.0f}s] {n}/{len(jobs)} done, better than best(시작 시점): {better} puzzles, gain {gain}', flush=True)
    save(new)
    print(f'done {time.time()-t0:.0f}s: better {better}, gain {gain}')

if __name__ == '__main__':
    main()
