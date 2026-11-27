"""기상천외 1회차: best 프로그램의 중간값을 처음 정수 후보로 쓰는 해독 (해독기가 빈손인 퍼즐용).
lns 가 숨은 정수를 스스로 일부 만들어 쓰고 있을 수 있으므로, best 의 중간값 가운데 512 ~ 2^26 인 것을
decode8.explain_strict 로 검사해 서로 다른 (k, a, b) 묶음 2개 이상에 쓰이는 것만 남기고, decode8.extend 로 넓힌다.
사용: decode9.py [--null] [--all] [--procs N] out.json   (--all: results/*.csv 의 프로그램 중간값도 후보로)   (--null: 무작위형 퍼즐에 같은 절차, 오검출률 측정)"""
import sys, json, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles, read_submission
import decode2, decode8

def values(pz, prog):
    reg = list(pz.start) + [None] * (pz.registers - len(pz.start)); out = []
    for op, a, b, d in prog:
        x, y = reg[a], reg[b]
        v = x + y if op == '+' else x - y if op == '-' else x * y if op == '*' else x // y
        reg[d] = v; out.append(v)
    return out

def prune(T, B):
    while B:
        cov = decode8.explain_strict(T, B)
        grp = collections.defaultdict(set)
        for v in cov.values():
            grp[v[1]].add(v[:3]); grp[v[2]].add(v[:3])
        keep = [b for b in B if len(grp[b]) >= 2]
        if len(keep) == len(B): return B, cov
        B = keep
    return [], {}

def work(arg):
    pid, pz, progs = arg
    T = sorted(t for t in set(pz.targets) if t >= 1 << 16)
    Ts = set(pz.targets)
    cand = sorted({v for prog in progs for v in values(pz, prog) if 512 <= v < 1 << 26 and v not in Ts})
    B, cov = prune(T, cand)
    if not B: return pid, [], [], 0, 0, len(T)
    c0 = len(cov)
    B2, added, cov2 = decode8.extend(pz.targets, B)
    B2, cov2 = prune(T, B2)
    return pid, B2, added, c0, len(cov2), len(T)

if __name__ == '__main__':
    from multiprocessing import Pool
    args = sys.argv[1:]
    procs = int(args[args.index('--procs') + 1]) if '--procs' in args else 3
    P = load_puzzles('data/puzzles.csv')
    srcs = ['best/best.csv'] + (sorted(__import__('glob').glob('results/*.csv')) if '--all' in args else [])
    progs = collections.defaultdict(list)
    for f in srcs:
        for p, c in read_submission(f).items(): progs[p].append(json.loads(c))
    C = json.load(open('solvers/quirk/family_guess.json'))
    Q = set()
    for f in ('solvers/quirk/bases3f.json', 'solvers/quirk/bases6.json', 'solvers/relate/bases_export.json'): Q |= set(json.load(open(f)))
    if '--null' in args: pids = [p for p in sorted(P) if C[p][0] == 'indep']
    else: pids = [p for p in sorted(P) if p not in Q and C[p][0] in ('struct', 'mixed')]
    res = {}; npz = 0; tot = 0
    with Pool(procs) as pool:
        for pid, B, added, c0, c1, nt in pool.imap_unordered(work, [(p, P[p], progs[p]) for p in pids]):
            if B:
                npz += 1; tot += c1
                print(pid, 'bases', B, 'added', added, 'strict cov', c0, '->', c1, '/', nt, flush=True)
                res[pid] = {'bases': B, 'cov': {}, 'nt': c1, 'added': added}
    print('puzzles', len(pids), 'with bases', npz, 'strict explained', tot)
    json.dump(res, open(args[-1], 'w'))
