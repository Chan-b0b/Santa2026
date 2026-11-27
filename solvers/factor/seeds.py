"""씨앗 후보 채굴: (목표값 - 싼 보정값) 들을 소인수분해해 여러 목표값에 걸친 공통 약수를 찾는다.

shared/multiplicative 유형의 목표값은 t = k*h + e (h: 숨은 기준값, k, e: 싼 작은 수) 꼴이 많고,
기준값 h 들은 서로 인수(예: practice_0004 의 669, 919)를 공유한다. t - e 의 약수를 목표값별로 모아
'몇 개의 목표값이 그 약수를 갖는가'로 투표하면 h 나 그 인수가 위로 올라온다.
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/home/maverick/Santa2026/solvers/factor")
from nt import factor


def _divs_window(fac, lo, hi, cap=400):
    ds = [1]
    for p, e in fac.items():
        cur = []
        pe = 1
        for _ in range(e):
            pe *= p
            for d in ds:
                v = d * pe
                if v <= hi:
                    cur.append(v)
        ds += cur
        if len(ds) > 20000:
            break
    out = [d for d in ds if d >= lo]
    if len(out) > cap:
        out.sort()
        out = out[-cap:]
    return out


def offsets(start, limit, maxoff=4096, maxn=48):
    """싼 보정값: 0, 시작값, 시작값 둘의 연산 한 번 (maxoff 이하)."""
    s = sorted(set(start))
    one = set()
    for i, a in enumerate(s):
        for b in s[i:]:
            for v in (a + b, abs(a - b), a * b):
                if 0 < v <= maxoff:
                    one.add(v)
            if a and b % a == 0:
                one.add(b // a)
    one.add(1)
    offs = [x for x in s if x <= maxoff]
    offs += sorted(x for x in one if x not in s)
    return offs[:maxn]


def candidates(start, targets, limit, facs=None, lo=1 << 7, topk=6):
    """[(score, d, votes)] 점수 높은 순. d 는 시작값/목표값이 아닌 공통 약수."""
    facs = facs or {}
    offs = offsets(start, limit)
    tset = set(targets)
    sset = set(start)
    votes = {}
    for i, t in enumerate(targets):
        if t < (1 << 14):
            continue
        hi = t // 2
        seen = set()
        for e in [0] + offs + [-x for x in offs]:
            w = t - e
            if w < (1 << 12) or w > limit * 4:
                continue
            f = facs.get(w)
            if f is None:
                f = factor(w)
            for d in _divs_window(f, lo, hi):
                if d not in seen:
                    seen.add(d)
                    votes.setdefault(d, set()).add(i)
    cands = []
    nt = sum(1 for t in targets if t >= (1 << 14))
    ne = 2 * len(offs) + 1
    for d, vs in votes.items():
        n = len(vs)
        if n < 2 or d in tset or d in sset:
            continue
        exp = nt * min(1.0, ne / d)          # 우연히 걸릴 기대 투표 수
        if exp < 0.05:
            need = 2
        elif exp < 0.4:
            need = 3
        else:
            need = 4 * exp + 2
        if n < need:
            continue
        cands.append(((n - 1 - exp) * d.bit_length(), d, vs))
    cands.sort(key=lambda x: (-x[0], -x[1]))
    out = []
    used = []
    for sc, d, vs in cands:
        # 같은 목표값 묶음을 설명하는 약수는 가장 점수 높은 것 하나만
        if any(vs <= u for u in used):
            continue
        used.append(vs)
        out.append((sc, d, len(vs)))
        if len(out) >= topk:
            break
    return out


if __name__ == "__main__":
    import csv, json
    pid = sys.argv[1]
    path = "/home/maverick/Santa2026/data/" + ("practice_puzzles.csv" if pid.startswith("practice") else "puzzles.csv")
    with open(path) as f:
        row = [r for r in csv.DictReader(f) if r["id"] == pid][0]
    st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
    import time
    t0 = time.time()
    for sc, d, n in candidates(st, tg, lim):
        print(sc, d, n, sorted(factor(d).items()))
    print("%.2fs" % (time.time() - t0))
