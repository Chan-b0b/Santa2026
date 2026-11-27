"""best/best.csv (또는 다른 결과 파일) 의 프로그램을 재생해 값 단위로 보여 준다.
사용: replay.py <id> [csv 경로]"""
import csv, json, sys
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core")
from verify import load_puzzles
csv.field_size_limit(10**9)
P = load_puzzles(ROOT + "/data/puzzles.csv")
pid = sys.argv[1]
path = sys.argv[2] if len(sys.argv) > 2 else ROOT + "/best/best.csv"
pz = P[pid]
prog = None
with open(path, newline="") as f:
    for r in csv.DictReader(f):
        if r["id"] == pid:
            prog = json.loads(r[[k for k in r if k != "id"][0]])
reg = list(pz.start) + [0] * (pz.registers - len(pz.start))
tset = set(pz.targets)
print(pid, "start", pz.start, "limit", pz.limit, "len", len(prog))
print("targets", pz.targets)
uses = {}
vals = []
for op, a, b, d in prog:
    x, y = reg[a], reg[b]
    v = {"+": x + y, "-": x - y, "*": x * y, "/": x // y if y else 0}[op]
    vals.append((v, op, x, y))
    uses[x] = uses.get(x, 0) + 1
    uses[y] = uses.get(y, 0) + 1
    reg[d] = v
for i, (v, op, x, y) in enumerate(vals):
    print("%3d %s%d = %d %s %d   [%db, uses %d]" % (i, "T " if v in tset else "  ", v, x, op, y, v.bit_length(), uses.get(v, 0)))
