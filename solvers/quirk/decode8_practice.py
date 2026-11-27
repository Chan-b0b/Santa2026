"""decode8 을 연습 퍼즐(가족을 안다)에 적용해 설명되는 목표 수가 가족별로 얼마나 느는지 잰다.
처음 정수는 practice2.log(통합 해독기 결과)에서 읽는다."""
import sys, re, json, collections, csv
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles
import decode2, decode8
P = load_puzzles('data/practice_puzzles.csv')
fam = {r['id']: r['family'] for r in csv.DictReader(open('data/practice_puzzles.csv'))}
B0 = {}
for line in open('solvers/quirk/practice2.log'):
    m = re.match(r'(practice_\d+) \w+ \w+ bases (\[.*?\]) explained', line)
    if m: B0[m.group(1)] = json.loads(m.group(2))
def work(pid):
    T = sorted(t for t in set(P[pid].targets) if t >= 1 << 16)
    c0 = len(decode2.explain(T, B0[pid]))
    B, added, cov = decode8.extend(P[pid].targets, B0[pid])
    return pid, c0, len(decode2.explain(T, B)), added
if __name__ == '__main__':
    st = collections.defaultdict(lambda: [0, 0, 0, 0])
    with Pool(3) as pool:
        for pid, c0, c1, added in pool.imap_unordered(work, sorted(B0)):
            s = st[fam[pid]]; s[0] += 1; s[1] += c0; s[2] += c1; s[3] += bool(added)
            if added: print(pid, fam[pid], 'added', added, c0, '->', c1, '/', len(P[pid].targets), flush=True)
    for f, s in sorted(st.items()): print(f, 'puzzles', s[0], 'with additions', s[3], 'explained', s[1], '->', s[2])
