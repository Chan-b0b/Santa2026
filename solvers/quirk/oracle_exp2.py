"""오라클 실험 2: best 프로그램에서 j 번째 목표가 만들어진 직후의 레지스터 풀에서, 남은 목표 전부의 정확한 최소 비용 분포를 본다.
사용: oracle_exp2.py <id> <j들 쉼표> [maxc]"""
import sys, csv, json, subprocess, collections
sys.path.insert(0, 'core')
from verify import load_puzzles
csv.field_size_limit(1 << 30)
pid = sys.argv[1]; js = [int(x) for x in sys.argv[2].split(',')]; maxc = sys.argv[3] if len(sys.argv) > 3 else '6'
P = load_puzzles('data/puzzles.csv'); p = P[pid]
prog = {r['id']: json.loads(r['program']) for r in csv.DictReader(open('best/best.csv'))}[pid]
reg = list(p.start) + [None] * (p.registers - len(p.start))
T = set(p.targets) - set(p.start); seen = []; pools = {}; pos = {}
for i, (op, a, b, d) in enumerate(prog):
    x, y = reg[a], reg[b]
    v = {'+': x + y, '-': x - y, '*': x * y, '/': x // y}[op]
    reg[d] = v
    if v in T and v not in seen:
        seen.append(v); pools[len(seen)] = [u for u in reg if u is not None]; pos[len(seen)] = i + 1
print(pid, 'len', len(prog), 'targets', len(T), 'per target', round(len(prog) / len(T), 2))
for j in js:
    pool = pools[j]; rem = [t for t in T if t not in seen[:j]]
    inp = f"{p.limit} {len(pool)} {len(rem)}\n" + " ".join(map(str, pool)) + "\n" + " ".join(map(str, rem)) + "\n"
    r = subprocess.run(['solvers/quirk/oracle', maxc], input=inp, capture_output=True, text=True)
    costs = [int(l.split()[1]) for l in r.stdout.strip().split('\n')]
    left = len(prog) - pos[j]
    print(f' after {j} targets (instr {pos[j]}): remaining {len(rem)}, program spends {left} more ({left/len(rem):.2f}/target); oracle cost dist {sorted(collections.Counter(costs).items())} | {r.stderr.strip().splitlines()[0]}', flush=True)
