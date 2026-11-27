"""decode_any 가 못 푼 구조형 퍼즐에 decode6(작은 정수, 그래프 방식)을 돌려 bases6.json 에 저장한다.
사용: decode6_all.py [procs]"""
import sys, json, os, time, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles
import decode6
P = load_puzzles('data/puzzles.csv')
OUTF = 'solvers/quirk/bases6.json'

def is_indep(p):
    T = [t for t in p.targets]
    digs = collections.Counter(len(str(t)) for t in T)
    return digs.most_common(1)[0][1] >= 0.9 * len(T) and max(T) >= 10 ** 10

def work(pid):
    p = P[pid]
    B, cov = decode6.decode(p.targets)
    return pid, B, {str(t): v for t, v in cov.items()}

if __name__ == '__main__':
    done = json.load(open('solvers/quirk/bases3f.json'))
    ids = [pid for pid, p in sorted(P.items()) if pid not in done and p.limit >= 1 << 20 and len(p.targets) >= 8 and not is_indep(p)]
    print(len(ids), 'puzzles', flush=True)
    out = {}; t0 = time.time()
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 2) as pool:
        for n, (pid, B, cov) in enumerate(pool.imap_unordered(work, ids), 1):
            if B and len(cov) >= 3: out[pid] = {'bases': B, 'cov': cov, 'nt': len(P[pid].targets)}
            if n % 50 == 0: print(n, 'done', f'{time.time()-t0:.0f}s', 'decoded', len(out), flush=True)
    json.dump(out, open(OUTF + '.tmp', 'w')); os.replace(OUTF + '.tmp', OUTF)
    print('done', len(out), f'{time.time()-t0:.0f}s')
