"""목표값별 비용 추정: 프로그램에서 목표가 만들어진 순서대로, 직전 목표 이후 명령 수.
CF 관계(다른 목표와의 q*t1 - p*t2 = r)도 같이 보여 준다.  사용: attrib.py <csv> <id> [thr]"""
import sys, csv, json, math
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles
from cf import relations
csv.field_size_limit(1 << 30)

def attrib(p, prog):
    reg = list(p.start) + [None] * (p.registers - len(p.start))
    T = set(p.targets) - set(p.start); out = []; last = 0; seen = set()
    for i, (op, a, b, d) in enumerate(prog):
        x, y = reg[a], reg[b]
        v = {'+': x + y, '-': x - y, '*': x * y, '/': x // y}[op]
        reg[d] = v
        if v in T and v not in seen:
            seen.add(v); out.append((v, i + 1 - last)); last = i + 1
    return out

if __name__ == '__main__':
    pid = sys.argv[2]; thr = float(sys.argv[3]) if len(sys.argv) > 3 else 10
    P = load_puzzles('data/puzzles.csv')
    best = {r['id']: json.loads(r['program']) for r in csv.DictReader(open(sys.argv[1]))}
    p = P[pid]; T = sorted(p.targets)
    print(pid, 'start', p.start, 'limit', p.limit, 'len', len(best[pid]), 'nt', len(T))
    rel = {t: [] for t in T}
    for i in range(len(T)):
        for j in range(len(T)):
            if i == j: continue
            a, b = (T[i], T[j]) if T[i] > T[j] else (T[j], T[i])
            if i < j: continue
            for sc, pp, q, r in relations(a, b):
                if thr <= sc:
                    rel[a].append((sc, f'{q}*t-{pp}*{b}={r}'))
                    rel[b].append((sc, f'{pp}*t-{q}*{a}={-r}'))
    for v, c in attrib(p, best[pid]):
        rs = sorted(rel[v], reverse=True)[:2]
        print(f'  {v:>20d} ({v.bit_length():2d}b) cost {c:2d}  ' + ' | '.join(f'{s}[{sc:.0f}]' for sc, s in rs))
