#!/usr/bin/env python3
"""bench_*.jsonl 을 묶음별 표로 정리한다.

사용: .venv/bin/python -I solvers/walk/table.py solvers/walk/bench_walk.jsonl solvers/walk/bench_lns.jsonl [--tags walk_s1,walk_s2]
- 기준은 solvers/walk/set30.json 의 base(고정한 best 길이).
- 퍼즐별로 같은 태그 묶음(접두어가 같은 태그, 예: walk_s1 과 walk_s2 -> walk)의 최단을 기준과 견준다.
- walk 통계: 초당 이동, 받은 비율, 값이 바뀐 상태 가운데 레지스터로 되돌린 비율.
"""
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, "set30.json")))
groups, base = S["groups"], S["base"]


def family(tag):
    return re.sub(r"_s\d+$", "", tag)


recs = []
for path in sys.argv[1:]:
    if path.startswith("--"):
        continue
    for ln in open(path):
        ln = ln.strip()
        if ln:
            recs.append(json.loads(ln))

best = defaultdict(dict)       # fam -> pid -> 최단
runs = defaultdict(lambda: defaultdict(list))
errs = defaultdict(int)
stats = defaultdict(list)
for r in recs:
    if r["pid"] not in groups:
        continue
    f = family(r["tag"])
    if r["len"] is None:
        errs[f] += 1
        continue
    b = best[f].get(r["pid"])
    best[f][r["pid"]] = r["len"] if b is None else min(b, r["len"])
    runs[f][r["pid"]].append(r["len"])
    if r.get("stats", "").startswith("start"):
        kv = dict(zip(*[iter(r["stats"].split())] * 2))
        stats[f].append((groups[r["pid"]], kv))

print("| 묶음 | 방법 | 실행 수 | 짧아진 퍼즐 수 | 줄어든 합 | 씨별 (짧아진 수/합) |")
print("|---|---|---|---|---|---|")
for g in ["bigrand", "rand", "struct", "all"]:
    for f in sorted(best):
        ids = [p for p in groups if g == "all" or groups[p] == g]
        have = [p for p in ids if p in best[f]]
        n = sum(1 for p in have if best[f][p] < base[p])
        d = sum(base[p] - best[f][p] for p in have if best[f][p] < base[p])
        nr = sum(len(runs[f][p]) for p in have)
        per = []
        for k in range(2):
            got = [(p, runs[f][p][k]) for p in have if len(runs[f][p]) > k]
            per.append(f"{sum(1 for p, l in got if l < base[p])}/{sum(base[p] - l for p, l in got if l < base[p])}")
        print(f"| {g} | {f} | {nr} | {n} | {d} | {' , '.join(per)} |")
for f in errs:
    print(f"오류(무효/실패) {f}: {errs[f]}")

for f in sorted(stats):
    by = defaultdict(list)
    for g, kv in stats[f]:
        by[g].append(kv)
        by["all"].append(kv)
    print(f"\n{f} 통계")
    print("| 묶음 | 초당 이동 | 받은 비율 | 값이 바뀐 비율 | 바뀐 상태 중 레지스터로 되돌림 | 컴파일 시도/실패 |")
    print("|---|---|---|---|---|---|")
    for g in ["bigrand", "rand", "struct", "all"]:
        L = by.get(g, [])
        if not L:
            continue
        def tot(k):
            return sum(float(x.get(k, 0)) for x in L)
        mv = tot("moves")
        acc = tot("neu") + tot("imp") + tot("grow")
        print(f"| {g} | {sum(float(x['mps']) for x in L) / len(L):.0f} | {acc / mv:.4f} | {tot('null') / mv:.4f} | "
              f"{tot('regrej') / max(1, tot('null')):.3f} | {tot('compile'):.0f}/{tot('fail'):.0f} |")
