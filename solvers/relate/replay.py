"""승자 프로그램 재생: replay.py <id> [csv]  — SSA 형태로 값과 식을 찍는다. 목표값은 T 표시."""
import sys, json, csv
sys.path.insert(0, '/home/maverick/Santa2026/core')
from verify import load_puzzles, read_submission
pid = sys.argv[1]
src = sys.argv[2] if len(sys.argv) > 2 else '/home/maverick/Santa2026/best/best.csv'
P = load_puzzles('/home/maverick/Santa2026/data/puzzles.csv')
pz = P[pid]
prog = json.loads(read_submission(src)[pid])
reg = {i: v for i, v in enumerate(pz.start)}
T = set(pz.targets)
print(pid, 'start', pz.start, 'limit', pz.limit, 'nT', len(pz.targets), 'len', len(prog))
uses = {}
vals = list(pz.start)
for op, a, b, d in prog:
    x, y = reg[a], reg[b]
    v = x + y if op == '+' else x - y if op == '-' else x * y if op == '*' else x // y
    reg[d] = v
    uses[x] = uses.get(x, 0) + 1; uses[y] = uses.get(y, 0) + 1
    vals.append((v, op, x, y))
seen = set(pz.start)
for i, e in enumerate(vals[len(pz.start):]):
    v, op, x, y = e
    print(f"{i:4d} {'T' if v in T else ' '} {v} = {x} {op} {y}   [uses {uses.get(v,0)}]{' DUP' if v in seen else ''}")
    seen.add(v)
