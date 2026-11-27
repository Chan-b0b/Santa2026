"""2회차 1번: multiplicative 가족의 공유 인수 측정. 목표 쌍의 gcd 에서 작은 소인수(<= 50)를 뗀 '큰 공유 인수'(>= 64)를 모아
목표 중 큰 공유 인수를 가진 비율을 가족별로 센다. 대조군: 같은 크기의 무작위 정수 목록."""
import sys, json, csv, math, random, collections
sys.path.insert(0, 'core')
from verify import load_puzzles
PR = load_puzzles('data/practice_puzzles.csv')
fam = {r['id']: r['family'] for r in csv.DictReader(open('data/practice_puzzles.csv'))}
SMALL = [p for p in range(2, 51) if all(p % q for q in range(2, p))]
def strip(g):
    for p in SMALL:
        while g % p == 0: g //= p
    return g
def atoms(T, gmin=64):
    A = collections.Counter(); who = collections.defaultdict(set)
    for i in range(len(T)):
        for j in range(i):
            g = strip(math.gcd(T[i], T[j]))
            if g >= gmin: A[g] += 1; who[g] |= {T[i], T[j]}
    return A, who
def cover(T):
    A, who = atoms(T)
    c = set()
    for g in A: c |= who[g]
    return len(c)
rnd = random.Random(5)
st = collections.defaultdict(lambda: [0, 0, 0, 0])
for pid, pz in PR.items():
    f = fam[pid]
    T = sorted(t for t in set(pz.targets) if t >= 256)
    if len(T) < 4: continue
    ctrl = [rnd.randrange(t // 2, t * 2) for t in T]
    s = st[f]; s[0] += len(T); s[1] += cover(T); s[2] += cover(ctrl); s[3] += 1
for f, s in sorted(st.items()):
    print(f'{f:15s} puzzles {s[3]:3d} targets {s[0]:5d}  share a big common factor: real {s[1]/s[0]:.3f}  ctrl {s[2]/s[0]:.3f}')
