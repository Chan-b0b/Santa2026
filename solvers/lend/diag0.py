import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from concurrent.futures import ThreadPoolExecutor
SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 30
ids = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pick20.json")))
KS = [1, 3, 5, 8]
def job(args):
    pid, k = args
    pz = P[pid]; prog = BEST[pid]
    to = target_order(pz, prog)
    tv = [v for _, v in to[:k]]
    cl = closure_prog(pz, prog, tv)
    mini = sub_puzzle(pz, tv)
    assert check_program(mini, cl) is None
    new, log = run_engine(mini, cl, SECS, seed=1)
    return pid, k, to[k - 1][0], len(cl), (len(new) if new else None), new, log
res = {}
with ThreadPoolExecutor(5) as ex:
    for pid, k, pos, kept, opt, new, log in ex.map(job, [(p, k) for p in ids for k in KS]):
        print(pid, k, pos, kept, opt, log[-60:], flush=True)
        res[f"{pid}:{k}"] = dict(pos=pos, kept=kept, opt=opt, prog=new)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "diag0.json"), "w"))
