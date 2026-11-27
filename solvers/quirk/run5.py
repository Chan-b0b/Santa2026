"""quirk 실행기 3판(2회차용): run2 와 같되 chain 설정을 여러 개 바꿔 보고, 짧은 순으로 서로 다른 원본 nlns 개를 각각 다듬는다.
사용: run5.py [--procs 5] [--budget 14] [--lns 20] [--nlns 3] [--lnsseed 40] [--bases a.json,b.json] [--only-held] [--ids a,b] [--nofinal]
  --only-held: quirk 가 지금 최단을 갖고 있는 퍼즐(best/source.csv)만."""
import sys, os, json, time, argparse, random, csv
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/relate'); sys.path.insert(0, 'solvers/chain'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles, check_program, write_submission, read_submission

P = load_puzzles('data/puzzles.csv')
OUT = 'results/quirk.csv'
BASE_CFG = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}
CHAIN_VARS = [{}, {"alpha": 0.1}, {"alpha": 0.22}, {"W": 24}, {"digits": 2}, {"digits": 6}, {"hot": 0}, {"tie_s1": 0}, {"vsoft": 42}, {"s1m": 1}]

def variants(bases, rng, nshuf=2):
    out = [tuple(bases), tuple(sorted(bases)), tuple(sorted(bases, reverse=True))]
    n = len(bases)
    for k in range(n - 1, 1, -1): out.append(tuple(bases[:k]))
    for _ in range(nshuf):
        b = list(bases); rng.shuffle(b); out.append(tuple(b))
    seen = set(); res = []
    for v in out:
        if v and v not in seen: seen.add(v); res.append(v)
    return res

def work(job):
    pid, bases, budget, lns_secs, nlns, lnsseed = job
    import solver3, chain_seed, polish
    pz = P[pid]; rng = random.Random((hash(pid) ^ lnsseed) & 0xffff)
    vs = variants(bases, rng)
    raws = {}
    def keep(prog, tag):
        if prog is None: return
        key = json.dumps(prog)
        if key not in raws: raws[key] = (prog, tag)
    # chain: 설정 × 씨앗 순서 (시간이 되는 만큼, 설정을 먼저 돈다)
    t0 = time.time()
    order = [(cv, sv) for sv in vs[:2] for cv in CHAIN_VARS] + [({}, sv) for sv in vs[2:]]
    for cv, sv in order:
        if time.time() - t0 > budget and raws: break
        try: prog = chain_seed.solve(pz, sv, cv)
        except Exception: prog = None
        keep(prog, 'chain')
    # relate
    t0 = time.time()
    for i in range(0, 6):
        c = dict(BASE_CFG)
        if i:
            c["rseed"] = lnsseed + i; c["noise"] = 1.0; c["rootpick"] = 1
            v = i % 4
            if v == 1: c["W2"] = 12
            elif v == 2: c["QN"] = 28; c["qgap"] = 14
            elif v == 3: c["s1depth"] = 1
            else: c["cshift"] = 2
        for sv in vs[:3]:
            if time.time() - t0 > budget / 2: break
            c2 = dict(c); c2["seeds"] = sv
            try: prog, log, cap = solver3.solve_once(pz, c2)
            except Exception: prog = None
            if prog is not None and check_program(pz, prog) is None: keep(prog, 'relate')
        if time.time() - t0 > budget / 2: break
    if not raws: return pid, None, None
    cand = sorted(raws.values(), key=lambda x: len(x[0]))
    best = cand[0][0]; info = [(len(p), t) for p, t in cand[:nlns]]
    for i, (p, tag) in enumerate(cand[:nlns]):
        new = polish.lns(pz, p, lns_secs, lnsseed + i)
        if new is not None and len(new) < len(best): best = new
    return pid, best, info

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procs', type=int, default=5)
    ap.add_argument('--budget', type=float, default=14)
    ap.add_argument('--lns', type=float, default=20)
    ap.add_argument('--nlns', type=int, default=3)
    ap.add_argument('--lnsseed', type=int, default=40)
    ap.add_argument('--ids', default='')
    ap.add_argument('--bases', default='solvers/quirk/bases3f.json,solvers/quirk/bases3c.json')
    ap.add_argument('--only-held', action='store_true')
    ap.add_argument('--nofinal', action='store_true')
    a = ap.parse_args()
    import decode2
    bases = {}
    for f in a.bases.split(','):
        bases.update(json.load(open(f)))          # 뒤 파일이 앞 파일을 덮는다 (배율 정리본 우선)
    cur = {pid: len(json.loads(c)) for pid, c in read_submission('best/best.csv').items()}
    held = None
    if a.only_held:
        held = {r['id'] for r in csv.DictReader(open('best/source.csv')) if r.get('source') == 'quirk'}
    ids = a.ids.split(',') if a.ids else sorted(bases)
    jobs = []
    for pid in ids:
        b = bases.get(pid)
        if not b or not b['bases']: continue
        if held is not None and pid not in held: continue
        if a.nofinal: B = list(b['bases'])
        else: B, cov = decode2.finalize(P[pid].targets, b['bases'])
        if not B: continue
        jobs.append((pid, B[:8], a.budget, a.lns, a.nlns, a.lnsseed))
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
                print(f'{pid} best {cur[pid]} quirk {len(prog)} ({len(prog)-cur[pid]:+d}) raw {info}', flush=True)
            else:
                print(f'{pid} failed', flush=True)
            if n % 10 == 0 or n == len(jobs):
                save(new); new = {}
                print(f'[{time.time()-t0:.0f}s] {n}/{len(jobs)} done, better than best(시작 시점): {better} puzzles, gain {gain}', flush=True)
    save(new)
    print(f'done {time.time()-t0:.0f}s: better {better}, gain {gain}')

if __name__ == '__main__':
    main()
