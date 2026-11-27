"""shared 퍼즐의 군집에 숨은 중심값(hub)이 있는지: H 를 훑어 (t - H) 가 시작값에서 2 명령 이하로 되는 목표 수를 센다."""
import sys, csv, json
from collections import Counter
pid = sys.argv[1]
with open("data/practice_puzzles.csv") as f:
    row = [r for r in csv.DictReader(f) if r["id"] == pid][0]
st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
def comb(A, B):
    out = set()
    for a in A:
        for b in B:
            out.add(a + b); out.add(abs(a - b)); out.add(a * b)
            if b and a % b == 0: out.add(a // b)
            if a and b % a == 0: out.add(b // a)
    out.discard(0)
    return out
L0 = set(st); L1 = comb(L0, L0) - L0; L2 = (comb(L1, L0) | comb(L1, L1)) - L1 - L0   # L1∘L1 is cost 3 but include
cost = {}
for v in L0: cost[v] = 0
for v in L1: cost.setdefault(v, 1)
for v in comb(L1, L0): cost.setdefault(v, 2)
small = sorted(v for v in cost if v < 5000)
print(pid, st, "작은 값 수", len(small))
# 군집 찾기: 가까운 목표 묶음 (상대 차이 < 1e-3)
tg = sorted(tg)
clusters = []
cur = [tg[0]]
for t in tg[1:]:
    if t - cur[-1] < max(cur[-1] * 2e-3, 3000): cur.append(t)
    else:
        if len(cur) >= 2: clusters.append(cur)
        cur = [t]
if len(cur) >= 2: clusters.append(cur)
for cl in clusters:
    votes = Counter()
    for t in cl:
        for e in small:
            votes[t - e] += 1; votes[t + e] += 1
        votes[t] += 1
    best = votes.most_common(3)
    print("군집", cl)
    for H, n in best:
        print("   H =", H, "덮는 목표", n, "/", len(cl), [(t - H, cost.get(abs(t - H), 0 if t == H else None)) for t in cl])
