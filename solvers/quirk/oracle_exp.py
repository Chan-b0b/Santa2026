"""오라클 실험: best 프로그램을 따라가다 목표 j 가 만들어지기 직전의 레지스터 값들을 풀로 삼아,
그 목표의 정확한 최소 비용(oracle)과 프로그램이 실제로 쓴 명령 수를 비교한다.
사용: oracle_exp.py <id> <목표 순번들, 쉼표 (프로그램에서 만들어지는 순서, 0부터)> [maxc]"""
import sys, csv, json, subprocess
sys.path.insert(0, 'core')
from verify import load_puzzles
csv.field_size_limit(1 << 30)
pid = sys.argv[1]; idx = [int(x) for x in sys.argv[2].split(',')]; maxc = sys.argv[3] if len(sys.argv) > 3 else '6'
P = load_puzzles('data/puzzles.csv'); p = P[pid]
prog = {r['id']: json.loads(r['program']) for r in csv.DictReader(open('best/best.csv'))}[pid]
reg = list(p.start) + [None] * (p.registers - len(p.start))
T = set(p.targets) - set(p.start); seen = []; snaps = []; last = 0
snap = [v for v in reg if v is not None]
for i, (op, a, b, d) in enumerate(prog):
    x, y = reg[a], reg[b]
    v = {'+': x + y, '-': x - y, '*': x * y, '/': x // y}[op]
    reg[d] = v
    if v in T and v not in seen:
        snaps.append((v, i + 1 - last, snap)); seen.append(v); last = i + 1
        snap = [u for u in reg if u is not None]
for j in idx:
    t, used, pool = snaps[j]
    inp = f"{p.limit} {len(pool)} 1\n" + " ".join(map(str, pool)) + f"\n{t}\n"
    r = subprocess.run(['solvers/quirk/oracle', maxc], input=inp, capture_output=True, text=True)
    print(f'{pid} target#{j} {t} ({t.bit_length()}b) pool {len(set(pool))} used {used} oracle {r.stdout.split()[1] if r.stdout else "?"} | {r.stderr.strip().splitlines()[0]}', flush=True)
