"""2회차 1번: 가족별 매끄러움(모든 소인수 < B) 비율. 채점 퍼즐에서 multiplicative 를 가려내는 기준을 만든다."""
import sys, json, csv, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
PR = load_puzzles('data/practice_puzzles.csv'); P = load_puzzles('data/puzzles.csv')
fam = {r['id']: r['family'] for r in csv.DictReader(open('data/practice_puzzles.csv'))}
PRIMES = [p for p in range(2, 20000) if all(p % q for q in range(2, int(p ** .5) + 1))]
def smooth(t, B=20000):
    for p in PRIMES:
        if p * p > t: break
        while t % p == 0: t //= p
    return t < B
def frac(pz):
    T = [t for t in set(pz.targets) if t >= 1 << 16]
    return sum(smooth(t) for t in T) / max(1, len(T)), len(T)
if __name__ == '__main__':
    by = collections.defaultdict(list)
    for pid, pz in PR.items(): by[fam[pid]].append(frac(pz)[0])
    for f, v in sorted(by.items()):
        v.sort(); print(f, 'n', len(v), 'smooth frac quantiles', [round(v[int(q * (len(v) - 1))], 2) for q in (0, .1, .25, .5, .75, .9, 1)])
    C = json.load(open('solvers/quirk/family_guess.json'))
    out = {}
    for pid, pz in P.items():
        f, n = frac(pz); out[pid] = f
    json.dump(out, open('solvers/quirk/smooth_frac.json', 'w'))
    for c in ('indep', 'mixed', 'struct'):
        v = sorted(out[p] for p in P if C[p][0] == c)
        print('scored', c, len(v), [round(v[int(q * (len(v) - 1))], 2) for q in (0, .1, .25, .5, .75, .9, 1)], '>=0.35:', sum(1 for x in v if x >= 0.35))
