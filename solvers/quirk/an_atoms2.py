"""an_atoms.py 의 빠른 판: 목표를 인수분해해 [30, 2^17] 약수를 직접 센다(전수 나눗셈 대신).
사용: [ATOM_DMIN=500 ATOM_PMIN=50] an_atoms2.py practice | scored  (DMIN: 원자 최소값, PMIN: 원자의 가장 큰 소인수 최소값)"""
import sys, json, csv, collections, random
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles, read_submission
from nt import factorint
from an_atoms import covered, values
_fc = {}
def divisors(t, dmax=1 << 17):
    f = _fc.get(t)
    if f is None: f = _fc[t] = factorint(t)
    ds = [1]
    for p, e in f.items():
        ds = [d * p ** i for d in ds for i in range(e + 1) if d * p ** i <= dmax]
    return ds
DMIN = int(__import__('os').environ.get('ATOM_DMIN', '30')); PMIN = int(__import__('os').environ.get('ATOM_PMIN', '2'))
def _bigp(d):
    return list(factorint(d)) or [1]
def find_atoms(T, dmax=1 << 17):
    T = [t for t in T if t >= 1 << 12]; n = len(T)
    cnt = collections.Counter()
    for t in T:
        for d in divisors(t, dmax):
            if d >= 30: cnt[d] += 1
    out = {d: c for d, c in cnt.items() if c >= 3 and c >= 6 * n / d and d >= DMIN and max(_bigp(d)) >= PMIN}
    return {d: c for d, c in out.items() if not any(e != d and e % d == 0 and out[e] == c for e in out)}
if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'practice':
        PR = load_puzzles('data/practice_puzzles.csv')
        fam = {r['id']: r['family'] for r in csv.DictReader(open('data/practice_puzzles.csv'))}
        rnd = random.Random(9); st = collections.defaultdict(lambda: [0, 0, 0])
        for pid, pz in sorted(PR.items()):
            T = sorted(set(pz.targets))
            if len(T) < 6 or max(T) < 1 << 16: continue
            ctrl = [rnd.randrange(max(2, t // 2), t * 2) for t in T]
            s = st[fam[pid]]; s[0] += len(T); s[1] += covered(T, find_atoms(T)); s[2] += covered(ctrl, find_atoms(ctrl))
        for f, s in sorted(st.items()): print(f'{f:15s} targets {s[0]} covered real {s[1]/s[0]:.3f} ctrl {s[2]/s[0]:.3f}')
    else:
        P = load_puzzles('data/puzzles.csv'); C = json.load(open('solvers/quirk/family_guess.json'))
        best = {p: json.loads(c) for p, c in read_submission('best/best.csv').items()}
        tot = inb = 0; per = []; covT = allT = 0
        for pid in sorted(P):
            if C[pid][0] not in ('struct', 'mixed'): continue
            pz = P[pid]; T = sorted(set(pz.targets))
            if len(T) < 6: continue
            A = find_atoms(T); allT += len(T)
            if not A: continue
            V = values(pz, best[pid]); miss = [d for d in A if d not in V]
            tot += len(A); inb += len(A) - len(miss); c = covered(T, A); covT += c
            per.append((pid, len(A), len(miss), c, len(T), sorted(miss, key=lambda d: -A[d])[:6]))
        print('struct+mixed targets', allT, 'divisible by an atom', covT)
        print('puzzles with atoms', len(per), 'atoms', tot, 'already a value in best', inb, f'({inb/max(1,tot):.2f})')
        per.sort(key=lambda r: -r[2])
        for r in per[:15]: print(r)
        json.dump(per, open('solvers/quirk/atoms_scored.json', 'w'))
