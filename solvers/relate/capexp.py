import sys, csv, time
from multiprocessing import Pool
sys.path.insert(0, '/home/maverick/Santa2026/core'); sys.path.insert(0, '/home/maverick/Santa2026/solvers/relate')
from verify import load_puzzles
import solver3 as solver
P = load_puzzles('/home/maverick/Santa2026/data/practice_puzzles.csv')
fam = {r['id']: r['family'] for r in csv.DictReader(open('/home/maverick/Santa2026/data/practice_puzzles.csv'))}
base = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}
def work(pid):
    out = [pid]
    for caps in ((120,), (90,), (72,), (64,)):
        c = dict(base); c['caps'] = caps
        t0 = time.time()
        r = solver.solve_once(P[pid], c)
        out.append((len(r[0]) if r[0] else None, round(time.time() - t0, 2)))
    T = P[pid].targets; mx = max(T)
    top = sum(1 for t in T if len(str(t)) == len(str(mx))) / len(T)
    out.append(round(top, 2))
    return out
if __name__ == '__main__':
    ids = [i for i in sorted(P) if fam[i] in sys.argv[1].split(',')]
    with Pool(5) as pool:
        res = pool.map(work, ids)
    for k, name in enumerate(('120', '90', '72', '64'), start=1):
        ok = [r for r in res if r[k][0] is not None]
        both = [r for r in res if r[k][0] is not None and r[4][0] is not None]
        print('cap', name, 'ok', len(ok), 'of', len(res), 'avg (when ok)', round(sum(r[k][0] for r in both) / max(1, len(both)), 1),
              'cap64 on same', round(sum(r[4][0] for r in both) / max(1, len(both)), 1), 'avg time', round(sum(r[k][1] for r in res) / len(res), 2))
