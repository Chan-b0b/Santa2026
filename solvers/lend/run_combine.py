"""초반부 바꿔 끼우기 대 대조군. 사용: run_combine.py <secs> <seeds,쉼표> <k>"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from concurrent.futures import ThreadPoolExecutor
SECS = float(sys.argv[1]); SEEDS = [int(s) for s in sys.argv[2].split(",")]; K = int(sys.argv[3])
D = os.path.dirname(os.path.abspath(__file__))
ids = json.load(open(os.path.join(D, "pick20.json")))
diag = json.load(open(os.path.join(D, "diag0.json")))
def job(a):
    pid, seed, mode = a
    pz = P[pid]; orig = BEST[pid]
    if mode == "ctl":
        start = orig
    else:
        d = diag[f"{pid}:{K}"]
        tv = [v for _, v in target_order(pz, orig)[:K]]
        ppz = sub_puzzle(pz, tv)
        start = splice(pz, d["prog"], ppz, orig)
        if start is None: return pid, seed, mode, None, None, "splice fail"
        assert check_program(pz, start) is None
    new, log = run_engine(pz, start, SECS, seed=seed)
    return pid, seed, mode, len(start), (len(new) if new else None), new
out = {}
jobs = [(p, s, m) for p in ids for s in SEEDS for m in ("ctl", "spl")]
with ThreadPoolExecutor(5) as ex:
    for pid, seed, mode, l0, l1, new in ex.map(job, jobs):
        print(pid, seed, mode, len(BEST[pid]), l0, l1, flush=True)
        out[f"{pid}:{seed}:{mode}"] = dict(best=len(BEST[pid]), start=l0, end=l1, prog=new if isinstance(new, list) else None)
json.dump(out, open(os.path.join(D, f"combine_k{K}_{SECS:g}.json"), "w"))
