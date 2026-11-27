"""퍼즐 하나의 프로그램을 값 흐름으로 출력한다.  사용: show.py <csv> <id>"""
import sys, csv, json
sys.path.insert(0, 'core')
from verify import load_puzzles
csv.field_size_limit(1 << 30)

def factor(n):
    f = []; d = 2
    while d * d <= n and d < 2000000:
        while n % d == 0: f.append(d); n //= d
        d += 1 if d == 2 else 2
    if n > 1: f.append(n)
    return f

def show(p, prog):
    reg = list(p.start) + [None] * (p.registers - len(p.start))
    T = set(p.targets)
    print('start', p.start, 'limit', p.limit, 'ntargets', len(T), 'len', len(prog))
    for i, (op, a, b, d) in enumerate(prog):
        x, y = reg[a], reg[b]
        v = {'+': x + y, '-': x - y, '*': x * y, '/': x // y}[op]
        reg[d] = v
        mark = ' <== T' if v in T else ''
        print(f'{i:3d}: {x} {op} {y} = {v}{mark}   {"·".join(map(str,factor(v))) if v < 10**15 else ""}')

if __name__ == '__main__':
    P = load_puzzles('data/puzzles.csv')
    best = {r['id']: json.loads(r['program']) for r in csv.DictReader(open(sys.argv[1]))}
    pid = sys.argv[2]
    print('targets', sorted(P[pid].targets))
    show(P[pid], best[pid])
