"""연습 퍼즐로 family 별 평균 길이를 잰다. 사용: python3 -I solvers/search/bench.py [N per family] [procs]"""
import sys, time, csv, collections
sys.path.insert(0, "/home/maverick/Santa2026/core")
sys.path.insert(0, "/home/maverick/Santa2026/solvers/search")
from multiprocessing import Pool
from verify import load_puzzles, check_program

PATH = '/home/maverick/Santa2026/data/practice_puzzles.csv'

def work(pid):
    import solver, tiny
    puzzles = load_puzzles(PATH)
    pz = puzzles[pid]
    t0 = time.time()
    try:
        prog = solver.solve_puzzle(pz, **KW)
        err = check_program(pz, prog)
    except Exception as e:
        import traceback
        prog = []
        err = 'EXC ' + repr(e) + traceback.format_exc()[-300:]
    return pid, len(prog), err, time.time() - t0, len(set(pz.targets) - set(pz.start))

KW = {}
for a in sys.argv[3:]:
    k, v = a.split('=', 1)
    try:
        v = int(v)
    except ValueError:
        try:
            v = float(v)
        except ValueError:
            pass
    KW[k] = v

if __name__ == '__main__':
    nper = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    rows = list(csv.DictReader(open(PATH)))
    fam = {r['id']: r['family'] for r in rows}
    cnt = collections.Counter()
    ids = []
    for r in rows:
        if cnt[r['family']] < nper:
            cnt[r['family']] += 1
            ids.append(r['id'])
    t0 = time.time()
    with Pool(procs) as pool:
        res = pool.map(work, ids, chunksize=1)
    agg = collections.defaultdict(lambda: [0, 0, 0, 0.0, 0.0])
    for pid, n, err, dt, lb in res:
        a = agg[fam[pid]]
        a[0] += 1; a[1] += n; a[2] += lb; a[3] += dt; a[4] = max(a[4], dt)
        if err:
            print('ERR', pid, err)
    import json, os
    out = os.environ.get('BENCH_OUT')
    if out:
        json.dump({pid: n for pid, n, err, dt, lb in res}, open(out, 'w'))
    tot = 0
    for f, a in sorted(agg.items()):
        tot += a[1]
        print('%-15s n=%3d  avg len %7.1f  per target %5.2f  avg time %5.2f max %5.2f' % (f, a[0], a[1] / a[0], a[1] / a[2], a[3] / a[0], a[4]))
    print('total', tot, 'wall %.1f' % (time.time() - t0))
