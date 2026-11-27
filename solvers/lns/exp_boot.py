"""실험: 초반 노드(재료가 적은 노드)를 완전 탐색(모든 식 모양, MITM)으로 다시 유도하면 전용 원뿔보다 짧아지는가.
노드 x 의 재료 = x 의 후손도 전용 원뿔도 아닌 값. 재료가 MAXC 개 이하인 노드만 본다."""
import sys, json, collections, time
sys.path.insert(0, 'solvers/lns'); sys.path.insert(0, 'core')
from verify import load_puzzles, read_submission
import lns
P = load_puzzles('data/puzzles.csv'); cells = read_submission('best/best.csv')
MAXC = int(sys.argv[1]); ids = sys.argv[2:]

def levels(C, limit, K):
    """cost[v] = 최소 트리 크기(0..K), lev[k] = 크기가 정확히 k 인 값 목록"""
    cost = {c: 0 for c in C}; lev = [list(cost)]
    for k in range(1, K + 1):
        cur = {}
        for i in range(0, k):
            j = k - 1 - i
            if i > j: break
            for a in lev[i]:
                for b in lev[j]:
                    for v in (a + b, a * b, a - b, b - a):
                        if 0 < v <= limit and v not in cost and v not in cur: cur[v] = 1
                    if a % b == 0:
                        v = a // b
                        if v not in cost and v not in cur: cur[v] = 1
                    if b % a == 0:
                        v = b // a
                        if v not in cost and v not in cur: cur[v] = 1
        for v in cur: cost[v] = k
        lev.append(list(cur))
        if sum(len(l) for l in lev) > 3_000_000: break
    return cost, lev

def mincost(v, cost, lev, limit, maxk):
    if v in cost: return cost[v]
    best = None
    K = len(lev) - 1
    for i in range(0, K + 1):                 # 뿌리에서 (i, j) 로 나눔, i <= j
        for a in lev[i]:
            for b in (v - a, v + a, a - v, (v // a if a and v % a == 0 else 0), v * a, (a // v if a % v == 0 else 0)):
                if b > 0 and b <= limit and b in cost:
                    c = i + cost[b] + 1
                    if best is None or c < best: best = c
        if best is not None and best <= i + 1 + i: break
        if i + 1 >= maxk: break
    return best

tot_gain = 0; tot_len = 0; tested = 0
for pid in ids:
    pz = P[pid]; s = lns.SSA(pz, json.loads(cells[pid])); L = pz.limit
    cons = collections.defaultdict(list)
    for n in s.order:
        cons[s.A[n]].append(n)
        if s.B[n] != s.A[n]: cons[s.B[n]].append(n)
    gain = 0; rows = []
    for x in s.order[:60]:
        cone = s.private(x)
        if len(cone) < 2: continue
        forb = set(cone); st = [x]
        while st:
            y = st.pop()
            for c in cons[y]:
                if c not in forb: forb.add(c); st.append(c)
        C = sorted(set(s.val[n] for n in list(range(s.ns)) + s.order if n not in forb))
        if len(C) > MAXC or not C: continue
        tested += 1
        K = 3 if len(C) <= 8 else 2 if len(C) <= 24 else 1
        cost, lev = levels(C, L, K)
        mc = mincost(s.val[x], cost, lev, L, len(cone))
        if mc is not None and mc < len(cone):
            gain += len(cone) - mc; rows.append((s.val[x], len(C), len(cone), mc))
    tot_gain += gain; tot_len += len(s.order)
    print(pid, '명령', len(s.order), '완전 탐색으로 줄일 수 있는 합(겹침 무시)', gain, rows[:6], flush=True)
print('합계', tot_len, '예상 이득', tot_gain, '검사한 노드', tested)
