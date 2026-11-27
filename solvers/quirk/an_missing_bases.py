"""2회차: 해독된 정수(1회차 decode8 포함) 가운데 서로 다른 (k,a,b) 묶음 3개 이상을 설명하는데 best 프로그램에 값으로 없는 것을 센다.
best 가 숨은 정수를 쓰지 않고 다른 길로 만든 퍼즐이다. 출력: missing_bases.json"""
import sys, json, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles, read_submission
import decode8
from an_atoms import values
P = load_puzzles('data/puzzles.csv')
best = {p: json.loads(c) for p, c in read_submission('best/best.csv').items()}
Q = {}
for f in ('solvers/quirk/bases3f.json', 'solvers/quirk/bases6.json', 'solvers/relate/bases_export.json', 'solvers/quirk/bases8.json'):
    for k, v in json.load(open(f)).items(): Q.setdefault(k, []).extend(v['bases'])
out = {}; tot = miss = 0; tgt_miss = 0
for pid, B in sorted(Q.items()):
    pz = P[pid]; B = [b for b in dict.fromkeys(B) if b >= 512]
    T = sorted(t for t in set(pz.targets) if t >= 1 << 16)
    cov = decode8.explain_strict(T, B)
    grp = collections.defaultdict(set); tg = collections.defaultdict(set)
    for t, v in cov.items():
        for x in (v[1], v[2]): grp[x].add(v[:3]); tg[x].add(t)
    V = values(pz, best[pid])
    # 정수의 작은 배수/약수가 있으면 있는 것으로 본다
    def present(b):
        return any(b * m in V or (b % m == 0 and b // m in V) for m in (1, 2, 3, 4, 5, 6, 7, 8))
    ms = [b for b in B if len(grp[b]) >= 3 and not present(b)]
    tot += sum(1 for b in B if len(grp[b]) >= 3); miss += len(ms)
    if ms:
        out[pid] = {'missing': ms, 'targets': len(set().union(*[tg[b] for b in ms])), 'bases': sorted(B, key=lambda b: -len(grp[b]))[:8]}
        tgt_miss += out[pid]['targets']
print('bases explaining >=3 groups', tot, 'absent from best (up to x8 scale)', miss, 'puzzles', len(out), 'targets they explain', tgt_miss)
for p in sorted(out, key=lambda p: -out[p]['targets'])[:15]: print(p, out[p]['missing'], 'explains', out[p]['targets'], 'best', len(best[p]))
json.dump(out, open('solvers/quirk/missing_bases.json', 'w'))
