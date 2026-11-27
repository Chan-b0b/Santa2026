"""multiplicative/shared/mixed 퍼즐에서 여러 목표가 공유하는 큰 소인수(또는 큰 공약수)를 센다."""
import sys, csv, json
from collections import defaultdict, Counter
from math import gcd
sys.path.insert(0, "/home/maverick/Santa2026/solvers/factor")
from nt import factor
with open("data/practice_puzzles.csv") as f:
    rows = list(csv.DictReader(f))
agg = defaultdict(lambda: [0, 0, 0, 0])
for r in rows:
    fam = r["family"]
    if fam == "tiny": continue
    tg = json.loads(r["targets"]); st = json.loads(r["starting_values"])
    cnt = Counter()
    for t in tg:
        for p in factor(t):
            if p > 100: cnt[p] += 1
    shared = {p for p, c in cnt.items() if c >= 2}
    nsh = sum(1 for t in tg if any(t % p == 0 for p in shared))
    # 큰 공약수 쌍
    big = 0
    for i, t in enumerate(tg):
        if any(gcd(t, u) > 1000 for j, u in enumerate(tg) if j != i): big += 1
    a = agg[fam]
    a[0] += len(tg); a[1] += nsh; a[2] += big; a[3] += len(shared)
    if fam == "multiplicative" and len(shared) and r["id"] in ("practice_0001", "practice_0007", "practice_0009", "practice_0010"):
        print(r["id"], st, sorted(shared), "targets w/ shared prime:", nsh, "/", len(tg))
for fam, a in agg.items():
    print(fam, "목표", a[0], "공유 소인수(>100) 가진 목표", a[1], "gcd>1000 쌍 있는 목표", a[2], "공유 소인수 개수", a[3])
