"""전체 퍼즐 해독 -> solvers/relate/bases_<set>.json (1단: 엄격), bases2_<set>.json (2단: 1단에서 못 찾은 퍼즐을 느슨하게).
사용: pypy3 -I decode_all.py scored|practice [tier]"""
import sys, json, time
sys.path.insert(0, '/home/maverick/Santa2026/core'); sys.path.insert(0, '/home/maverick/Santa2026/solvers/relate')
from multiprocessing import Pool
from verify import load_puzzles
import hubs
which = sys.argv[1]
tier = int(sys.argv[2]) if len(sys.argv) > 2 else 1
D = '/home/maverick/Santa2026/solvers/relate/'
P = load_puzzles('/home/maverick/Santa2026/data/' + ('practice_puzzles.csv' if which == 'practice' else 'puzzles.csv'))
def work(pid):
    try:
        if tier == 1: B, info = hubs.decode(P[pid].targets)
        elif tier == 2: B, info = hubs.decode(P[pid].targets, mint=2, basemin=600, tmin=1 << 18, mincov=5)
        else: B, info = hubs.decode(P[pid].targets, mint=2, basemin=600, tmin=1 << 18, mincov=3)
    except Exception as e:
        B, info = [], {'err': repr(e)}
    return pid, B, info
if __name__ == '__main__':
    t0 = time.time(); out = {}
    ids = sorted(P)
    if tier >= 2:
        b1 = json.load(open(D + f'bases_{which}.json'))
        if tier == 3:
            b1.update(json.load(open(D + f'bases2_{which}.json')))
        ids = [i for i in ids if i not in b1 and P[i].limit > 4096]
    with Pool(int(sys.argv[3]) if len(sys.argv) > 3 else 5) as pool:
        for pid, B, info in pool.imap_unordered(work, ids, chunksize=8):
            if B: out[pid] = {'bases': B, 'alt': info['alt'], 'cov': info['cov'], 'n': info['n'], 'targets': info['targets']}
            elif info.get('err'): print('ERR', pid, info['err'])
    name = D + (f'bases_{which}.json' if tier == 1 else f'bases{tier}_{which}.json')
    json.dump(out, open(name, 'w'), indent=0, sort_keys=True)
    print(which, 'tier', tier, 'decoded', len(out), 'of', len(ids), f'{time.time()-t0:.0f}s')
