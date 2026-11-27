"""연습 퍼즐로 통합 해독기(decode_any + finalize)의 가족별 적용 범위를 잰다. 미해독 퍼즐 목록도 낸다."""
import sys, csv, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles
import decode_any, decode2
P = load_puzzles('data/practice_puzzles.csv')
rows = {r['id']: r for r in csv.DictReader(open('data/practice_puzzles.csv'))}
def work(pid):
    p = P[pid]
    if p.limit < 1 << 16: return pid, [], 0
    B, cov = decode_any.decode(p.targets, 24)
    B, cov = decode2.finalize(p.targets, B) if B else ([], {})
    return pid, B, len(cov)
if __name__ == '__main__':
    st = collections.defaultdict(lambda: [0, 0, 0, 0]); miss = collections.defaultdict(list)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 3) as pool:
        for pid, B, nc in pool.imap_unordered(work, sorted(P)):
            f = rows[pid]['family']; s = st[f]; s[0] += 1; s[1] += bool(B); s[2] += nc; s[3] += len(P[pid].targets)
            if B: print(pid, f, rows[pid]['design_tier'], 'bases', B, f'explained {nc}/{len(P[pid].targets)}', flush=True)
            else: miss[f].append(pid)
    for f, s in sorted(st.items()): print(f, 'puzzles', s[0], 'decoded', s[1], 'targets explained', s[2], '/', s[3])
    for f in ('shared', 'mixed'): print('undecoded', f, sorted(miss[f]))
