"""프로그램을 재생해 값 그래프로 보여 준다: 값마다 식, 사용 횟수, 목표 여부.
사용: replay.py <csv> <id> [max_lines]"""
import sys, json
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core")
from verify import load_puzzles, read_submission

def ssa_of(p, prog):
    reg = [None] * p.registers
    vals = list(p.start)          # node id -> value
    for i, v in enumerate(p.start): reg[i] = i
    nodes = []                    # (op, ia, ib, val)
    for op, a, b, d in prog:
        ia, ib = reg[a], reg[b]
        x, y = vals[ia], vals[ib]
        r = x + y if op == '+' else x - y if op == '-' else x * y if op == '*' else x // y
        nodes.append((op, ia, ib, r)); vals.append(r); reg[d] = len(vals) - 1
    return vals, nodes

def main():
    path, pid = sys.argv[1], sys.argv[2]
    P = load_puzzles(ROOT + "/data/puzzles.csv")
    p = P[pid]
    prog = json.loads(read_submission(path)[pid])
    vals, nodes = ssa_of(p, prog)
    k = len(p.start)
    uses = [0] * len(vals)
    for op, a, b, r in nodes: uses[a] += 1; uses[b] += 1
    T = set(p.targets)
    print(pid, 'start', p.start, 'ntargets', len(p.targets), 'len', len(prog), 'limit', p.limit)
    seen = set(p.start)
    def f(i):
        v = vals[i]
        tag = 'T' if v in T else ''
        return f"{v}{tag}" if v < 10**9 else f"<{v.bit_length()}b#{i}{tag}>"
    since = 0
    for j, (op, a, b, r) in enumerate(nodes):
        i = k + j
        since += 1
        mark = ''
        if r in T and r not in seen:
            mark = f'   <== TARGET ({r.bit_length()}b) cost-since-last {since}'; since = 0
        seen.add(r)
        print(f"#{i:3d} {r:>20d} = {f(a)} {op} {f(b)}  uses={uses[i]}{mark}")

if __name__ == '__main__':
    main()
