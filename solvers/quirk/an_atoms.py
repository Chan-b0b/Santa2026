"""2회차 1번: 목표 여러 개를 나누는 '원자' 인수 d (30 <= d <= 2^17, 나누는 목표 3개 이상, 기대값 n/d 의 6배 이상) 를 찾고
(a) 가족별 적용 비율(원자 하나 이상으로 나누어지는 목표 비율) 을 무작위 대조군과 비교하고
(b) 채점 퍼즐에서 그 원자가 best 프로그램에 이미 중간값(또는 그 배수 아닌 그 값 자체)으로 있는지 센다."""
import sys, json, csv, collections, random
sys.path.insert(0, 'core')
from verify import load_puzzles, read_submission
def find_atoms(T, dmax=1 << 17):
    T = [t for t in T if t >= 1 << 12]; n = len(T)
    cnt = collections.Counter()
    for t in T:
        pass
    out = {}
    for d in range(30, dmax):
        c = 0
        for t in T:
            if t % d == 0: c += 1
        if c >= 3 and c >= 6 * n / d: out[d] = c
    # 다른 원자의 배수이면서 개수가 같은 것만 남긴다(가장 큰 것)
    keep = {}
    for d, c in out.items():
        if any(e != d and e % d == 0 and out[e] == c for e in out): continue
        keep[d] = c
    return keep
def covered(T, A): return sum(1 for t in T if any(t % d == 0 for d in A))
def values(pz, prog):
    reg = list(pz.start) + [None] * (pz.registers - len(pz.start)); out = set(pz.start)
    for op, a, b, d in prog:
        x, y = reg[a], reg[b]; v = x + y if op == '+' else x - y if op == '-' else x * y if op == '*' else x // y
        reg[d] = v; out.add(v)
    return out
if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'practice':
        PR = load_puzzles('data/practice_puzzles.csv')
        fam = {r['id']: r['family'] for r in csv.DictReader(open('data/practice_puzzles.csv'))}
        rnd = random.Random(9); st = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
        for pid, pz in sorted(PR.items()):
            T = sorted(set(pz.targets))
            if len(T) < 6 or max(T) < 1 << 16: continue
            A = find_atoms(T); ctrl = [rnd.randrange(max(2, t // 2), t * 2) for t in T]; Ac = find_atoms(ctrl)
            s = st[fam[pid]]; s[0] += len(T); s[1] += covered(T, A); s[2] += covered(ctrl, Ac); s[3] += len(A); s[4] += len(Ac)
            if fam[pid] == 'multiplicative' and pid in ('practice_0108', 'practice_0001', 'practice_0010'): print(pid, sorted(A.items(), key=lambda x: -x[1])[:12])
        for f, s in sorted(st.items()): print(f'{f:15s} targets {s[0]} covered real {s[1]/s[0]:.3f} ctrl {s[2]/s[0]:.3f} atoms real {s[3]} ctrl {s[4]}')
    else:
        P = load_puzzles('data/puzzles.csv'); C = json.load(open('solvers/quirk/family_guess.json'))
        best = {p: json.loads(c) for p, c in read_submission('best/best.csv').items()}
        tot = inb = 0; per = []
        ids = [p for p in sorted(P) if C[p][0] in ('struct', 'mixed')]
        if len(sys.argv) > 2: ids = ids[int(sys.argv[2])::int(sys.argv[3])]
        for pid in ids:
            pz = P[pid]; T = sorted(set(pz.targets))
            if len(T) < 6: continue
            A = find_atoms(T)
            if not A: continue
            V = values(pz, best[pid])
            # 원자 자체, 또는 원자의 배수/약수 가운데 목표가 아닌 중간값으로 있으면 '있음'
            miss = [d for d in A if d not in V]
            tot += len(A); inb += len(A) - len(miss)
            per.append((pid, len(A), len(miss), covered(T, A), len(T), sorted(miss)[:6]))
        print('puzzles with atoms', len(per), 'atoms', tot, 'already in best', inb, f'({inb/max(1,tot):.2f})')
        per.sort(key=lambda r: -r[2])
        for r in per[:15]: print(r)
        json.dump(per, open(f'solvers/quirk/atoms_scored{"_" + sys.argv[2] if len(sys.argv) > 2 else ""}.json', 'w'))
