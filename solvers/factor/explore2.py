"""작은 퍼즐에서 값별 최소 수식 비용(트리 모델)을 깊이별로 구해 목표가 어느 깊이에 나오는지 본다."""
import sys, csv, json, time
pid = sys.argv[1]; maxk = int(sys.argv[2])
with open("data/practice_puzzles.csv") as f:
    row = [r for r in csv.DictReader(f) if r["id"] == pid][0]
st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
cost = {v: 0 for v in st}
how = {}
levels = [list(set(st))]
t0 = time.time()
for k in range(1, maxk + 1):
    new = {}
    for i in range(0, (k - 1) // 2 + 1):
        j = k - 1 - i
        A, B = levels[i], levels[j]
        for a in A:
            for b in B:
                for v, h in ((a + b, '+'), (a * b, '*'), (a - b, '-'), (b - a, 'r-')):
                    if 1 <= v <= lim and v not in cost and v not in new:
                        new[v] = (h, a, b)
                if a % b == 0:
                    v = a // b
                    if v not in cost and v not in new: new[v] = ('/', a, b)
                if b % a == 0:
                    v = b // a
                    if v not in cost and v not in new: new[v] = ('r/', a, b)
    for v in new: cost[v] = k
    how.update(new)
    levels.append(list(new))
    print("level", k, "new", len(new), "time %.1f" % (time.time() - t0), "targets hit", [t for t in tg if t in new])
def expr(v):
    if v not in how: return str(v)
    h, a, b = how[v]
    if h.startswith('r'): h = h[1:]; a, b = b, a
    return "(" + expr(a) + h + expr(b) + ")"
for t in tg:
    print(t, cost.get(t), expr(t) if t in cost else "")
