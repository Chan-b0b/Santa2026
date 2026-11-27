"""연습 퍼즐(가족 라벨 있음)로 해독기의 적용 범위를 가족별로 잰다."""
import sys, csv, json, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles
from decode import decode
P = load_puzzles('data/practice_puzzles.csv')
fam = {r['id']: r['family'] for r in csv.DictReader(open('data/practice_puzzles.csv'))}
def work(pid):
    p = P[pid]
    if p.limit < 1 << 16: return pid, [], 0
    B, cov = decode(p.targets, 24)
    return pid, B, len(cov)
if __name__ == '__main__':
    st = collections.defaultdict(lambda: [0, 0, 0, 0])
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 6) as pool:
        for pid, B, nc in pool.imap_unordered(work, sorted(P)):
            s = st[fam[pid]]; s[0] += 1; s[1] += bool(B); s[2] += nc; s[3] += len(P[pid].targets)
            if B: print(pid, fam[pid], 'bases', B, f'explained {nc}/{len(P[pid].targets)}', flush=True)
    for f, s in sorted(st.items()): print(f, 'puzzles', s[0], 'decoded', s[1], 'targets explained', s[2], '/', s[3])
