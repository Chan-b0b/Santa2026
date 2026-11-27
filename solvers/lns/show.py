"""현재 최선 프로그램의 값 그래프를 보여 준다: 노드별 값, 식, 쓰이는 횟수, 목표 여부. 사용: show.py <scored id> [src.csv]"""
import sys, json, collections
sys.path.insert(0, 'solvers/lns'); sys.path.insert(0, 'core')
from verify import load_puzzles, read_submission
import lns
from nt import fstr
P = load_puzzles('data/puzzles.csv')
pid = sys.argv[1]; src = sys.argv[2] if len(sys.argv) > 2 else 'best/best.csv'
pz = P[pid]; s = lns.SSA(pz, json.loads(read_submission(src)[pid]))
uses = collections.Counter()
for n in s.order: uses[s.A[n]] += 1; uses[s.B[n]] += 1
req = set(s.req.values())
print(f"{pid} 시작값 {list(pz.start)} 한도 {pz.limit} 목표 {len(pz.targets)} 명령 {len(s.order)}")
name = {i: f"s{i}" for i in range(s.ns)}
for k, n in enumerate(s.order):
    name[n] = f"v{k}"
for k, n in enumerate(s.order):
    a, b = s.A[n], s.B[n]
    va, vb = s.val[a], s.val[b]
    tag = 'T' if n in req else ' '
    print(f"{tag} v{k:<3} = {name[a]:>5} {s.op[n]} {name[b]:<5} = {s.val[n]:<22} [{va} {s.op[n]} {vb}]  쓰임 {uses[n]}")
