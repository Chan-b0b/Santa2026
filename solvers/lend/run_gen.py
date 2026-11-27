"""일반 실행기. 사용: run_gen.py --ids 파일 --phase prefix|spl|ctl --ks 3,5,8 --seeds 1,2 --secs 45 --procs 10 --tag A
prefix: 초반부(k별) 따로 최적화해 prefix_<tag>.json 에 저장. spl: 초반부 바꿔 끼워 lns. ctl: best 에서 lns.
퍼즐 하나(작업 하나)가 끝날 때마다 best 보다 짧으면 results/lend.csv 갱신, 로그 한 줄."""
import sys, os, argparse, time; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from concurrent.futures import ThreadPoolExecutor, as_completed
D = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--ids"); ap.add_argument("--phase"); ap.add_argument("--ks", default="5"); ap.add_argument("--seeds", default="1,2")
ap.add_argument("--secs", type=float, default=45); ap.add_argument("--procs", type=int, default=10); ap.add_argument("--tag", default="A")
ap.add_argument("--bestlen", default=None)
A = ap.parse_args()
ids = json.load(open(A.ids if os.path.isabs(A.ids) else os.path.join(D, A.ids)))
KS = [int(x) for x in A.ks.split(",")]; SEEDS = [int(x) for x in A.seeds.split(",")]
OUT = os.path.join(ROOT, "results", "lend.csv")
pfile = os.path.join(D, f"prefix_{A.tag}.json")
prefix = json.load(open(pfile)) if os.path.exists(pfile) else {}
frozen = json.load(open(os.path.join(D, A.bestlen))) if A.bestlen else {p: len(BEST[p]) for p in ids}

def save_result(pid, prog):
    cur = {k: json.loads(v) for k, v in read_submission(OUT).items()} if os.path.exists(OUT) else {}
    live = {k: json.loads(v) for k, v in read_submission(os.path.join(ROOT, "best", "best.csv")).items()}
    if pid in live and len(prog) >= len(live[pid]): return
    if pid in cur and len(cur[pid]) <= len(prog): return
    if check_program(P[pid], prog) is not None: return
    cur[pid] = prog; tmp = OUT + ".tmp"; write_submission(tmp, cur); os.replace(tmp, OUT)

def job(a):
    pid, k, seed = a; pz = P[pid]; orig = BEST[pid]; t0 = time.time()
    if A.phase == "prefix":
        tv = [v for _, v in target_order(pz, orig)[:k]]
        cl = closure_prog(pz, orig, tv); mini = sub_puzzle(pz, tv)
        new, log = run_engine(mini, cl, A.secs, seed=1)
        return a, dict(kept=len(cl), opt=len(new) if new else None, prog=new), time.time() - t0
    if A.phase == "ctl":
        start = orig; slen = len(orig)
    else:
        d = prefix.get(f"{pid}:{k}")
        if not d or not d["prog"]: return a, dict(start=None, end=None, prog=None), 0
        tv = [v for _, v in target_order(pz, orig)[:k]]
        start = splice(pz, d["prog"], sub_puzzle(pz, tv), orig)
        if start is None: return a, dict(start=None, end=None, prog=None), 0
        slen = len(start)
    new, log = run_engine(pz, start, A.secs, seed=seed)
    return a, dict(start=slen, end=len(new) if new else None, prog=new), time.time() - t0

if A.phase == "prefix": jobs = [(p, k, 1) for p in ids for k in KS]
elif A.phase == "ctl": jobs = [(p, 0, s) for p in ids for s in SEEDS]
else: jobs = [(p, k, s) for p in ids for k in KS for s in SEEDS]
res = {}
rfile = os.path.join(D, f"res_{A.tag}_{A.phase}_{A.ks}_{A.seeds}.json")
with ThreadPoolExecutor(A.procs) as ex:
    for f in as_completed([ex.submit(job, j) for j in jobs]):
        a, r, dt = f.result(); pid, k, seed = a
        if A.phase == "prefix":
            prefix[f"{pid}:{k}"] = r
            print(pid, "k", k, "kept", r["kept"], "opt", r["opt"], f"{dt:.0f}s", flush=True)
        else:
            res[f"{pid}:{k}:{seed}"] = r
            if r["prog"] and len(r["prog"]) < frozen[pid]: save_result(pid, r["prog"])
            print(pid, "k", k, "seed", seed, "frozen", frozen[pid], "start", r["start"], "end", r["end"], f"{dt:.0f}s", flush=True)
if A.phase == "prefix": json.dump(prefix, open(pfile, "w"))
else: json.dump({k: dict(v, prog=None) for k, v in res.items()}, open(rfile, "w"))
