"""shared 퍼즐에서 가까운 목표쌍의 차이가 시작값으로 얼마나 싸게 만들어지는지 본다 (작은 수의 트리 비용 DP)."""
import sys, csv, json, time
pid = sys.argv[1]; maxk = int(sys.argv[2]); CAP = int(sys.argv[3])
with open("data/practice_puzzles.csv") as f:
    row = [r for r in csv.DictReader(f) if r["id"] == pid][0]
st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
cost = {v: 0 for v in st}
how = {}
levels = [list(set(st))]
for k in range(1, maxk + 1):
    new = {}
    for i in range(0, (k - 1) // 2 + 1):
        j = k - 1 - i
        for a in levels[i]:
            for b in levels[j]:
                for v, h in ((a + b, '+'), (a * b, '*'), (a - b, '-'), (b - a, 'r-')):
                    if 1 <= v <= CAP and v not in cost and v not in new:
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
def expr(v):
    if v not in how: return str(v)
    h, a, b = how[v]
    if h.startswith('r'): h = h[1:]; a, b = b, a
    return "(" + expr(a) + h + expr(b) + ")"
print(pid, st, [len(l) for l in levels])
for i, t in enumerate(tg):
    best = None
    for j, u in enumerate(tg):
        if i == j: continue
        d = abs(t - u)
        if d in cost and (best is None or cost[d] < best[0]):
            best = (cost[d], u, d)
    # ratio structure: t ~ m*u + d
    alt = None
    for j, u in enumerate(tg):
        if u >= t: continue
        m = round(t / u)
        if m < 2: continue
        d = abs(t - m * u)
        if m in cost and (d in cost or d == 0):
            c = cost[m] + (cost[d] + 1 if d else 0) + 1
            if alt is None or c < alt[0]: alt = (c, u, m, d)
    print(t, "| diff:", (best[0] + 1, best[1], best[2], expr(best[2])) if best else None, "| mul:", alt)
