"""2회차 4번 후속: 채점 퍼즐에서 t = m*u + d (u 는 다른 목표, 1 <= m <= 16, 0 < |d| < 2^16) 인 목표 쌍을 찾고,
best 프로그램이 t 를 만드는 명령의 피연산자에 u 나 m*u 가 들어 있는지(= 이미 그 관계를 쓰는지) 센다."""
import sys, json, collections
sys.path.insert(0, 'core')
from verify import load_puzzles, read_submission
P = load_puzzles('data/puzzles.csv'); C = json.load(open('solvers/quirk/family_guess.json'))
best = {p: json.loads(c) for p, c in read_submission('best/best.csv').items()}
tot = used = 0; nopz = collections.Counter(); costs = []
for pid, pz in P.items():
    if C[pid][0] not in ('struct', 'mixed'): continue
    T = sorted(set(pz.targets)); Ts = set(T)
    pairs = {}
    for t in T:
        if t < 1 << 20: continue
        for u in T:
            if u >= t or u < 1 << 16: continue
            for m in range(1, 17):
                d = t - m * u
                if 0 < abs(d) < 1 << 16: pairs.setdefault(t, []).append((u, m)); break
    if not pairs: continue
    reg = list(pz.start) + [None] * (pz.registers - len(pz.start)); made = {}; ops = {}
    for i, (op, a, b, dd) in enumerate(best[pid]):
        x, y = reg[a], reg[b]; v = x + y if op == '+' else x - y if op == '-' else x * y if op == '*' else x // y
        reg[dd] = v
        if v in Ts and v not in made: made[v] = (x, y)
    for t, lst in pairs.items():
        tot += 1
        x, y = made.get(t, (None, None))
        ok = any(x in (u, m * u) or y in (u, m * u) or (x is not None and abs(x - m * u) < 1 << 16) or (y is not None and abs(y - m * u) < 1 << 16) for u, m in lst)
        used += ok
        if not ok: nopz[pid] += 1
print('targets with t = m*u + small:', tot, 'best builds t from u (or m*u, or a value within 2^16 of m*u):', used)
print('puzzles with unused relations:', len(nopz), 'top', nopz.most_common(10))
