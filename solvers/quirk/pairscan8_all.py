"""pairscan8 를 해독 안 된 구조형·mixed 채점 퍼즐 전체(또는 --null: 무작위형)에 돌려 run2 용 JSON 을 만든다.
사용: pairscan8_all.py [--null] [--procs N] out.json"""
import sys, json
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles
import pairscan8
P = load_puzzles('data/puzzles.csv')
def work(pid):
    B, n = pairscan8.run(P[pid]); return pid, B, n
if __name__ == '__main__':
    a = sys.argv[1:]
    procs = int(a[a.index('--procs') + 1]) if '--procs' in a else 2
    C = json.load(open('solvers/quirk/family_guess.json'))
    Q = set()
    for f in ('solvers/quirk/bases3f.json', 'solvers/quirk/bases6.json', 'solvers/relate/bases_export.json'): Q |= set(json.load(open(f)))
    if '--null' in a: pids = [p for p in sorted(P) if C[p][0] == 'indep'][:60]
    else: pids = [p for p in sorted(P) if p not in Q and C[p][0] in ('struct', 'mixed')]
    out = {}; hist = {}
    with Pool(procs) as pool:
        for pid, B, n in pool.imap_unordered(work, pids):
            hist[n] = hist.get(n, 0) + 1
            if B and n >= 4:
                out[pid] = {'bases': B[:8], 'cov': {}, 'nt': n}
                print(pid, 'groups', n, 'bases', B[:8], flush=True)
    print('puzzles', len(pids), 'groups hist', sorted(hist.items()), 'kept(>=4)', len(out))
    json.dump(out, open(a[-1], 'w'))
