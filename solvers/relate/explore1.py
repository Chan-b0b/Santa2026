import sys, csv, json
from collections import Counter, defaultdict
sys.path.insert(0, 'solvers/relate')
rows = list(csv.DictReader(open('data/practice_puzzles.csv')))

def s1_of(K, limit):
    """K op K -> value -> list of (a,op,b)"""
    S = defaultdict(list)
    K = sorted(set(K))
    for i, a in enumerate(K):
        for b in K[i:]:
            v = a + b
            if v <= limit: S[v].append((a, '+', b))
            v = a * b
            if v <= limit: S[v].append((a, '*', b))
            if b > a:
                S[b - a].append((b, '-', a))
                if b % a == 0: S[b // a].append((b, '/', a))
            else:
                S[1].append((a, '/', a))
    return S

def explain(t, K, S, limit):
    """min steps (1,2,3) to derive t from K\{t} using S1; returns (steps, desc)"""
    Kx = [k for k in K if k != t]
    ok1 = [e for e in S.get(t, []) if e[0] != t and e[2] != t]
    if ok1: return 1, ok1[0]
    # 2 step: t = x op c, x in S1 (not using t), c in K
    for c in Kx:
        cands = [(t - c, '+'), (t + c, '-'), (c - t, 'r-'), (t * c, '/'), (c * t, '/')]
        if t % c == 0: cands.append((t // c, '*'))
        if c % t == 0: cands.append((c // t, 'r/'))
        for x, op in cands:
            if x < 1 or x > limit: continue
            for e in S.get(x, []):
                if e[0] != t and e[2] != t:
                    return 2, (e, op, c)
    return None, None

fam_stats = defaultdict(Counter)
for r in rows:
    s = json.loads(r['starting_values']); T = json.loads(r['targets']); L = int(r['value_limit'])
    K = sorted(set(s) | set(T))
    S = s1_of(K, L)
    for t in T:
        if t in s: 
            fam_stats[r['family']]['start'] += 1; continue
        st, d = explain(t, K, S, L)
        fam_stats[r['family']][st] += 1
        if len(sys.argv) > 1 and r['id'] == sys.argv[1]:
            print(t, st, d)
for f, c in fam_stats.items():
    print(f, dict(c))
