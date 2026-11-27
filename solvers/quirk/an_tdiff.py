"""2회차 4번: 설명 안 되는 목표 t 가 다른 목표 u 의 작은 배수 + 설명되는 값인지 본다.
t - m*u (m = 1..16, 그리고 t - u/m 꼴은 생략) 가 (a) 엄격한 k*a*b + r 로 설명되거나 (b) |.| < 2^16 이면 적중.
대조군: t 를 같은 크기의 난수로 바꾼다. 연습 shared/mixed (practice2.log 의 정수 + decode8 확장)."""
import sys, re, json, csv, random, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
import decode8
P = load_puzzles('data/practice_puzzles.csv')
fam = {r['id']: r['family'] for r in csv.DictReader(open('data/practice_puzzles.csv'))}
B0 = {}
for line in open('solvers/quirk/practice2.log'):
    m = re.match(r'(practice_\d+) \w+ \w+ bases (\[.*?\]) explained', line)
    if m: B0[m.group(1)] = json.loads(m.group(2))
rnd = random.Random(4)
st = collections.Counter()
for pid in sorted(B0):
    if fam[pid] not in ('shared', 'mixed'): continue
    pz = P[pid]; T = sorted(t for t in set(pz.targets) if t >= 1 << 16)
    B, added, cov = decode8.extend(pz.targets, B0[pid])
    H = sorted({a * b for i, a in enumerate(B) for b in B[i:] if a * b >= 1 << 24})
    def hit(t):
        for u in T:
            if u == t: continue
            for m in range(1, 17):
                d = t - m * u
                if d == 0: continue
                ad = abs(d)
                if ad < 1 << 16: return 'small'
                if ad < 1 << 24: continue
                for h in H:
                    if h > 2 * ad: break
                    k = (ad + h // 2) // h
                    if 1 <= k <= 1 << 17 and abs(ad - k * h) <= min(8192, h >> 16): return 'hub'
        return None
    for t in T:
        if t in cov: continue
        for src, tt in (('real', t), ('ctrl', rnd.randrange(t // 2, t * 2))):
            st[(src, 'n')] += 1
            r = hit(tt)
            if r: st[(src, r)] += 1
for src in ('real', 'ctrl'):
    n = st[(src, 'n')]; print(src, 'unexplained targets', n, 'small diff', st[(src, 'small')], 'hub-explained diff', st[(src, 'hub')])
