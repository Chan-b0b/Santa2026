"""값 빌려주기 대 대조군. 사용: run_borrow.py <T1> <T2> <seed> <m들,쉼표> [ids파일|all-big]"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
T1, T2, SEED = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]); MS = [int(x) for x in sys.argv[4].split(",")]
D = os.path.dirname(os.path.abspath(__file__))
ids = json.load(open(os.path.join(D, sys.argv[5] if len(sys.argv) > 5 else "pick20.json")))

def helpers(pz, prog, m):
    vals, nodes = to_nodes(pz, prog); ns = len(pz.start)
    T = set(pz.targets); S = set(pz.start)
    cons = Counter(); seen = set()
    for i, (op, a, b, v) in enumerate(nodes):
        for o in {a, b}: cons[vals[o]] += 1
    c = [(n, v) for v, n in cons.items() if v not in T and v not in S]
    c.sort(key=lambda t: (-t[0], t[1]))
    return [v for n, v in c[:m]]

def job(a):
    pid, m = a
    pz = P[pid]; orig = BEST[pid]
    if m == 0:
        new, log = run_engine(pz, orig, T1 + T2, seed=SEED)
        return pid, m, len(orig), len(orig), (len(new) if new else None), new, []
    E = helpers(pz, orig, m)
    pzx = sub_puzzle(pz, extra_start=E)
    st = splice(pzx, [], pzx, orig, pz_orig=pz)
    if st is None: return pid, m, len(orig), None, None, None, E
    assert check_program(pzx, st) is None, check_program(pzx, st)
    n1, log = run_engine(pzx, st, T1, seed=SEED)
    if n1 is None: n1 = st
    vals, nodes = to_nodes(pzx, n1)
    used = sorted({vals[o] for (_, a_, b_, _) in nodes for o in (a_, b_) if vals[o] in E})
    pay = closure_prog(pz, orig, used)
    seq = seq_of(pz, pay) + seq_of(pzx, n1)
    back = allocate(pz, seq)
    if back is None or check_program(pz, back) is not None: return pid, m, len(orig), len(n1), None, None, E
    n2, log = run_engine(pz, back, T2, seed=SEED)
    return pid, m, len(orig), len(back), (len(n2) if n2 else len(back)), (n2 or back), E

out = {}
jobs = [(p, m) for p in ids for m in [0] + MS]
with ThreadPoolExecutor(5) as ex:
    for pid, m, b, back, fin, prog, E in ex.map(job, jobs):
        print(pid, "m=%d" % m, "best", b, "되돌린", back, "최종", fin, len(E), flush=True)
        out[f"{pid}:{m}"] = dict(best=b, back=back, end=fin, prog=prog, E=E)
json.dump(out, open(os.path.join(D, f"borrow_s{SEED}_{sys.argv[4]}_{T1:g}_{T2:g}_{os.path.basename(sys.argv[5]) if len(sys.argv) > 5 else 'pick20'}.json"), "w"))
