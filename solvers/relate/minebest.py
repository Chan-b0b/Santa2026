"""best.csv 프로그램에서 '큰 값 x 큰 값' 곱셈에 2번 이상 쓰인 피연산자(숨은 정수 후보)를 센다. 분석용."""
import sys, json, csv
sys.path.insert(0, '/home/maverick/Santa2026/core')
from verify import load_puzzles, read_submission
from collections import Counter
P = load_puzzles('/home/maverick/Santa2026/data/puzzles.csv')
def bases_of(pz, prog, lo=300):
    reg = {i: v for i, v in enumerate(pz.start)}
    cnt = Counter()
    for op, a, b, d in prog:
        x, y = reg[a], reg[b]
        v = x + y if op == '+' else x - y if op == '-' else x * y if op == '*' else x // y
        if op == '*' and x >= lo and y >= lo:
            cnt[x] += 1
            if y != x: cnt[y] += 1
            else: cnt[x] += 1
        reg[d] = v
    return cnt
if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '/home/maverick/Santa2026/best/best.csv'
    sub = read_submission(src)
    rows = {r['id']: r for r in csv.DictReader(open('/home/maverick/Santa2026/board/matrix.csv'))}
    out = []
    for pid, cell in sorted(sub.items()):
        pz = P[pid]; prog = json.loads(cell)
        c = bases_of(pz, prog)
        B = [x for x, n in c.items() if n >= 2 and x.bit_length() <= 26]
        nb = sum(1 for t in pz.targets if t >= 1 << 28)
        out.append((pid, len(prog), len(pz.targets), max(pz.targets).bit_length(), len(B), sorted(B)[:8], rows[pid]['best_by'], rows[pid]['relate']))
    hist = Counter(min(o[4], 6) for o in out)
    print('num bases hist', sorted(hist.items()))
    for nbase in range(0, 7):
        sel = [o for o in out if min(o[4], 6) == nbase and o[2] >= 20 and o[3] >= 40]
        if sel:
            print(nbase, 'n', len(sel), 'avg len/target', sum(o[1] for o in sel) / sum(o[2] for o in sel), 'relate avg', sum(int(o[7]) for o in sel)/sum(o[2] for o in sel))
    if len(sys.argv) > 2:
        for o in out:
            if o[2] >= 20 and o[3] >= 40: print(*o)
