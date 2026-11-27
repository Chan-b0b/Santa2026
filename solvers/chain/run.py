"""채점 퍼즐 1,000개에 chain 솔버를 돌려 results/chain.csv 를 갱신한다.

사용법 (프로젝트 루트에서):
    python3 -I solvers/chain/run.py "<설정 목록 파이썬 식>" [퍼즐당 초] [프로세스 수]
퍼즐별로 기존 프로그램보다 짧을 때만 바꾼다.
"""
import sys, time, os, json, csv
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/chain")
from verify import load_puzzles, check_program, write_submission, read_submission
import multiprocessing as mp

RESULT = ROOT + "/results/chain.csv"
PUZ = None
CONFIGS = None
BUDGET = 4.0
SEEDS = {}
SEEDFILE = ROOT + "/solvers/chain/seeds.json"


def load_existing():
    out = {}
    if os.path.exists(RESULT):
        puzzles = load_puzzles(ROOT + "/data/puzzles.csv")
        for pid, cell in read_submission(RESULT).items():
            prog = json.loads(cell)
            if pid in puzzles and check_program(puzzles[pid], prog) is None:
                out[pid] = prog
    return out


def init(configs, budget):
    global PUZ, CONFIGS, BUDGET, SEEDS
    PUZ = load_puzzles(ROOT + "/data/puzzles.csv")
    CONFIGS = configs
    BUDGET = budget
    if os.path.exists(SEEDFILE):
        SEEDS = json.load(open(SEEDFILE))


def work(args):
    pid, curlen = args
    import chain
    from prune import prune
    p = PUZ[pid]
    best = None
    bestkw = None
    t0 = time.time()
    seen = set()
    for kw0 in CONFIGS:
        if time.time() - t0 > BUDGET:
            break
        kw = dict(kw0)
        # nb: 해독한 밑(decode.py -> seeds.json) 가운데 앞에서부터 nb 개를 먼저 만든다. 밑이 없는 퍼즐은 그 설정을 건너뛴다.
        nb = kw.pop("nb", None)
        if nb is not None:
            bs = tuple(b[0] for b in SEEDS.get(pid, [])[:nb])
            if not bs:
                continue
            kw["bases"] = bs
            # auxc: 목표값 설명에 auxc 번 이상 나오는 작은 값(k, e, r)을 보조 목표로 먼저 만든다
            auxc = kw.pop("auxc", None)
            if auxc:
                import decode
                _ex, need = decode.explain(p.targets, bs)
                kw["aux"] = tuple(sorted(v for v, c in need.items() if c >= auxc))
        else:
            kw.pop("auxc", None)
        key = repr(sorted(kw.items()))
        if key in seen:
            continue
        seen.add(key)
        try:
            prog = chain.solve_any(p, deadline=t0 + BUDGET, **kw)
        except Exception as e:      # 한 설정의 실패가 전체를 막지 않게
            sys.stderr.write(f"{pid} {kw}: {type(e).__name__} {e}\n")
            continue
        if prog is None or check_program(p, prog) is not None:
            continue
        pruned = prune(p, prog)          # 쓰이지 않는 명령 제거
        if len(pruned) < len(prog) and check_program(p, pruned) is None:
            prog = pruned
        if best is None or len(prog) < len(best):
            best = prog
            bestkw = kw0
    if best is not None and (curlen is None or len(best) < curlen):
        return pid, best, bestkw
    return pid, None, None


def main():
    configs = eval(sys.argv[1])
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    nproc = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    only = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[4] not in ("", "all", "seeded") else None
    if len(sys.argv) > 4 and sys.argv[4] == "seeded":      # 밑이 해독된 퍼즐만
        sd = json.load(open(SEEDFILE))
        only = sorted(pid for pid, v in sd.items() if v)
    puzzles = load_puzzles(ROOT + "/data/puzzles.csv")
    cur = load_existing()
    ids = sorted(puzzles) if only is None else only
    jobs = [(pid, len(cur[pid]) if pid in cur else None) for pid in ids]
    t0 = time.time()
    improved = 0
    wins = {}
    with mp.Pool(nproc, initializer=init, initargs=(configs, budget)) as pool:
        for k, (pid, prog, kw) in enumerate(pool.imap_unordered(work, jobs, chunksize=4)):
            if prog is not None:
                cur[pid] = prog
                improved += 1
                wins[str(kw)] = wins.get(str(kw), 0) + 1
            if (k + 1) % 100 == 0:
                write_submission(RESULT, cur)
                print(f"{k+1}/{len(jobs)} 개선 {improved} 합계 {sum(len(v) for v in cur.values())} {time.time()-t0:.0f}s", flush=True)
    write_submission(RESULT, cur)
    print(f"끝: 프로그램 {len(cur)}개, 개선 {improved}, 합계(자체 집계, 참고용) {sum(len(v) for v in cur.values())}, {time.time()-t0:.0f}s")
    for kw, n in sorted(wins.items(), key=lambda x: -x[1])[:20]:
        print(f"  {n:4d} {kw}")


if __name__ == "__main__":
    main()
