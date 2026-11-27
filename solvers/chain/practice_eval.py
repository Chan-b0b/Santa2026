"""연습 퍼즐 200개에 한 설정을 돌려 family 별 평균 길이를 낸다 (노트용 참고 수치).
    python3 -I solvers/chain/practice_eval.py "<설정 dict 식>" [프로세스 수]
"""
import sys, csv, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/chain")
from verify import load_puzzles, check_program
import multiprocessing as mp

KW = None
P = None


def init(kw):
    global KW, P
    KW = kw
    P = load_puzzles(ROOT + "/data/practice_puzzles.csv")


def work(pid):
    import chain
    from prune import prune
    p = P[pid]
    t0 = time.time()
    prog = chain.solve_any(p, **KW)
    if prog is None:
        return pid, None, 0
    prog = prune(p, prog)
    assert check_program(p, prog) is None
    return pid, len(prog), time.time() - t0


if __name__ == "__main__":
    kw = eval(sys.argv[1])
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    rows = list(csv.DictReader(open(ROOT + "/data/practice_puzzles.csv")))
    fam = {r["id"]: r["family"] for r in rows}
    lb = {r["id"]: int(r["lower_bound"]) for r in rows}
    agg = {}
    with mp.Pool(nproc, initializer=init, initargs=(kw,)) as pool:
        for pid, n, dt in pool.imap_unordered(work, sorted(fam), chunksize=2):
            a = agg.setdefault(fam[pid], [0, 0, 0, 0.0, 0])
            if n is None:
                a[4] += 1
                continue
            a[0] += 1; a[1] += n; a[2] += lb[pid]; a[3] += dt
    tot = 0
    for f, a in sorted(agg.items()):
        tot += a[1]
        print(f"{f:15s} 퍼즐 {a[0]:3d}  평균 길이 {a[1]/a[0]:7.1f}  목표값당 {a[1]/max(a[2],1):5.2f}  평균 {a[3]/a[0]:.2f}s  실패 {a[4]}")
    print("합계", tot)
