"""끝난 프로그램에서 목표별 '전용 단계 수'와, 최종 풀에서 다시 유도했을 때의 비용을 비교한다."""
import sys, csv, json, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
import engine3 as E
pid = sys.argv[1]
with open(ROOT + "/data/practice_puzzles.csv") as f:
    row = [r for r in csv.DictReader(f) if r["id"] == pid][0]
st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
eng = E.Engine(st, tg, lim, cfg={}, deadline=time.time() + 600)
eng.solve()
steps = eng.steps
prod = {v: i for i, (v, op, a, b) in enumerate(steps)}
users = {}
for i, (v, op, a, b) in enumerate(steps):
    users.setdefault(a, set()).add(i); users.setdefault(b, set()).add(i)
tset = set(tg)
tot_priv = 0; gain = 0; nleaf = 0
for t in tg:
    if t not in prod: continue
    if users.get(t):
        continue
    nleaf += 1
    R = {prod[t]}
    stack = [prod[t]]
    while stack:
        i = stack.pop()
        v, op, a, b = steps[i]
        for u in (a, b):
            j = prod.get(u)
            if j is None or j in R or u in tset: continue
            if users[u] <= R:
                R.add(j); stack.append(j)
    priv = len(R)
    # 최종 풀에서 재유도 (t 를 풀에서 잠시 뺀다)
    inpool = t in eng.pool
    if inpool:
        eng.pool.discard(t); eng.pool0.discard(t)
    r = eng.deep(t, priv - 1) if priv >= 4 else None
    ok = r is not None and all(s[2] != t and s[3] != t for s in r[1])
    if inpool:
        eng.pool.add(t); eng.pool0.add(t)
    if ok:
        gain += priv - r[0]
    tot_priv += priv
    print(t.bit_length(), "전용", priv, "재유도", (r[0], r[2]) if ok else None)
print(pid, "총", len(steps), "잎 목표", nleaf, "/", len(tg), "전용 합", tot_priv, "잠재 절감", gain)
