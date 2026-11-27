"""프로그램을 값 수준으로 풀어 보여 준다. 사용: python3 -I solvers/search/show.py <csv> <puzzle_id> [puzzles.csv]"""
import sys, json
sys.path.insert(0, "/home/maverick/Santa2026/core")
from verify import load_puzzles, read_submission
def show(pz, prog):
    reg = [None] * pz.registers
    reg[:len(pz.start)] = pz.start
    T = set(pz.targets)
    print(pz.id, 'starts', pz.start, 'limit', pz.limit, 'targets', len(pz.targets), 'len', len(prog))
    for op, a, b, d in prog:
        x, y = reg[a], reg[b]
        v = x + y if op == '+' else x - y if op == '-' else x * y if op == '*' else x // y
        reg[d] = v
        print('   %d %s %d = %d %s' % (x, op, y, v, '  <== target' if v in T else ''))
if __name__ == '__main__':
    path = sys.argv[3] if len(sys.argv) > 3 else '/home/maverick/Santa2026/data/puzzles.csv'
    P = load_puzzles(path)
    cells = read_submission(sys.argv[1])
    show(P[sys.argv[2]], json.loads(cells[sys.argv[2]]))
