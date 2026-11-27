"""chain 2단계 실행기: 해독한 밑(bases) + 설명 보조값(aux) + 자기 결과에서 거둔 작은 값(self-aux) 반복.

사용법 (프로젝트 루트에서):
    .venv/bin/python -I -u solvers/chain/run2.py <seeded|unseeded|all|id,id,...> [퍼즐당 초] [프로세스 수] [반복 수] [최대 best/하한 비]
퍼즐마다:
  1) (밑이 있으면) 밑만 / 밑 + 설명 보조값 몇 가지 설정으로 푼다.
  2) 지금까지의 최단 프로그램에서 "두 번 이상 쓰인 작은 값"을 거둬 보조 목표로 넣고 다시 푼다. 짧아지면 되풀이한다.
results/chain.csv 는 퍼즐별로 더 짧을 때만 바꾼다. 50개마다 중간 저장한다.
"""
import sys, time, os, json
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/chain"); sys.path.insert(0, ROOT + "/solvers/chain/tools")
from verify import load_puzzles, check_program, write_submission, read_submission
import multiprocessing as mp

RESULT = ROOT + "/results/chain.csv"
SEEDFILE = os.environ.get("SEEDS", ROOT + "/solvers/chain/seeds.json")     # SEEDS=.../seeds_weak.json 으로 느슨한 해독 결과를 쓴다
BASE = dict(digits=4, W=16, pol=0, order='cheap', s1m=2, f2=0, relkeep=2, rel_shift=12, alpha=0.16, vcap=160, vsoft=45, tie_s1=1, hot=30)
PUZ = None
SEEDS = {}
BUDGET = 30.0
ITERS = 3
HARV_MIN = int(os.environ.get("HARV_MIN", "2"))        # 거둘 값의 최소 사용 횟수
HARV_SMALL = 1 << int(os.environ.get("HARV_SMALL", "14"))   # 거둘 값의 크기 상한
SKIP_INIT = bool(os.environ.get("SKIP_INIT"))          # 1 이면 밑/설명 설정을 건너뛰고 거두기 반복만 한다


def init(budget, iters):
    global PUZ, SEEDS, BUDGET, ITERS
    PUZ = load_puzzles(ROOT + "/data/puzzles.csv")
    SEEDS = json.load(open(SEEDFILE)) if os.path.exists(SEEDFILE) else {}
    BUDGET = budget
    ITERS = iters


def harvest(p, prog, small=1 << 14, minuse=2):
    """프로그램에서 minuse 번 이상 피연산자로 쓰인 small 이하의 값 (시작값 제외)."""
    from replay import ssa_of
    vals, nodes = ssa_of(p, prog)
    k = len(p.start)
    uses = [0] * len(vals)
    for op, a, b, r in nodes:
        uses[a] += 1
        uses[b] += 1
    st = set(p.start)
    return tuple(sorted(set(vals[i] for i in range(k, len(vals)) if vals[i] <= small and uses[i] >= minuse and vals[i] not in st)))


def work(args):
    pid, cur = args
    import chain, decode
    from prune import prune
    p = PUZ[pid]
    t0 = time.time()
    best = cur
    tag = None
    log = []

    def run(name, **kw):
        nonlocal best, tag
        if time.time() - t0 > BUDGET:
            return None
        c = dict(BASE)
        c.update(kw)
        try:
            prog = chain.solve_any(p, **c)
        except Exception as e:
            sys.stderr.write(f"{pid} {name}: {type(e).__name__} {e}\n")
            return None
        if prog is None or check_program(p, prog) is not None:
            return None
        pr = prune(p, prog)
        if len(pr) < len(prog) and check_program(p, pr) is None:
            prog = pr
        log.append((name, len(prog)))
        if best is None or len(prog) < len(best):
            best = prog
            tag = name
        return prog

    if p.limit <= 24:
        return pid, None, None, log
    bs = tuple(b[0] for b in SEEDS.get(pid, []))
    sd = 0 if bs else 4
    if bs and not SKIP_INIT:
        pb = run("bases", bases=bs, seed=0)
        if pb is not None and cur is not None and len(pb) > len(cur) + 6 and os.environ.get("SEEDS"):
            bs = ()          # 느슨한 해독의 밑이 틀린 것으로 보이면 버린다 (what-if)
            sd = 4
    if bs and not SKIP_INIT:
        _ex, need = decode.explain(p.targets, bs)
        a1 = tuple(sorted(need))
        a2 = tuple(sorted(v for v, c in need.items() if c >= 2))
        run("expl1", bases=bs, seed=0, aux=a1, aux_max=1, aux_pre=0)
        run("expl2", bases=bs, seed=0, aux=a1, aux_max=2, aux_pre=1)
        if a2:
            run("expl3", bases=bs, seed=0, aux=a2, aux_max=2, aux_pre=1)
    if os.environ.get("ROUND2") and best is not None:
        # 2회차 변형: 동점 처리 끄기, 세 번 이상 쓰인 값만, 더 큰 값까지 거두기, 마지막 밑 빼기
        a2 = harvest(p, best, minuse=2)
        a3 = harvest(p, best, minuse=3)
        a16 = harvest(p, best, small=1 << 17, minuse=2)
        run("r2tie", bases=bs, seed=sd, aux=a2, aux_max=2, aux_pre=1, tie_s1=0)
        if a3 != a2:
            run("r2min3", bases=bs, seed=sd, aux=a3, aux_max=2, aux_pre=1)
        if a16 != a2:
            run("r2big", bases=bs, seed=sd, aux=a16, aux_max=2, aux_pre=1)
        if len(bs) >= 3:
            run("r2drop", bases=bs[:-1], seed=sd, aux=a2, aux_max=2, aux_pre=1)
        run("r2a22", bases=bs, seed=sd, aux=a2, aux_max=2, aux_pre=1, alpha=0.22)
    # 자기 결과에서 거둔 작은 값으로 되풀이
    for it in range(ITERS):
        if best is None or time.time() - t0 > BUDGET:
            break
        before = len(best)
        aux = harvest(p, best, small=HARV_SMALL, minuse=HARV_MIN)
        if not aux:
            break
        run(f"self{it}a", bases=bs, seed=sd, aux=aux, aux_max=2, aux_pre=1)
        run(f"self{it}b", bases=bs, seed=sd, aux=aux, aux_max=1, aux_pre=1)
        if bs:
            run(f"self{it}c", bases=bs, seed=sd, aux=aux, aux_max=1, aux_pre=0)
        if len(best) >= before:
            break
    if best is not None and (cur is None or len(best) < len(cur)):
        return pid, best, tag, log
    return pid, None, None, log


def main():
    which = sys.argv[1]
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    nproc = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    iters = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    maxratio = float(sys.argv[5]) if len(sys.argv) > 5 else 99.0
    puzzles = load_puzzles(ROOT + "/data/puzzles.csv")
    cur = {}
    for pid, cell in read_submission(RESULT).items():
        prog = json.loads(cell)
        if pid in puzzles and check_program(puzzles[pid], prog) is None:
            cur[pid] = prog
    seeds = json.load(open(SEEDFILE)) if os.path.exists(SEEDFILE) else {}
    if which == "seeded":
        ids = sorted(pid for pid in puzzles if seeds.get(pid))
    elif which == "unseeded":
        ids = sorted(pid for pid in puzzles if not seeds.get(pid))
    elif which == "all":
        ids = sorted(puzzles)
    elif which == "nonrandom":      # 엄격한 해독에서 밑이 안 나온 퍼즐 (maxratio 로 난수형을 뺀다)
        strong = json.load(open(ROOT + "/solvers/chain/seeds.json"))
        ids = sorted(pid for pid in puzzles if not strong.get(pid))
    else:
        ids = which.split(",")
    # 하한 대비 길이가 maxratio 이하인 퍼즐만 (난수형 큰 퍼즐은 느리고 이득이 작다)
    ids = [pid for pid in ids if pid not in cur or len(cur[pid]) <= maxratio * max(1, puzzles[pid].lower_bound)]
    jobs = [(pid, cur.get(pid)) for pid in ids]
    t0 = time.time()
    improved = 0
    saved = 0
    wins = {}
    with mp.Pool(nproc, initializer=init, initargs=(budget, iters)) as pool:
        for k, (pid, prog, tag, log) in enumerate(pool.imap_unordered(work, jobs, chunksize=2)):
            if prog is not None:
                saved += len(cur[pid]) - len(prog) if pid in cur else 0
                cur[pid] = prog
                improved += 1
                t = tag.rstrip("abc")
                wins[t] = wins.get(t, 0) + 1
            if (k + 1) % 50 == 0:
                write_submission(RESULT, cur)
                print(f"{k+1}/{len(jobs)} 개선 {improved} 줄인 명령 {saved} 합계(참고) {sum(len(v) for v in cur.values())} {time.time()-t0:.0f}s", flush=True)
    write_submission(RESULT, cur)
    print(f"끝: 퍼즐 {len(jobs)}개 중 개선 {improved}, 줄인 명령 {saved}, 합계(자체 집계, 참고용) {sum(len(v) for v in cur.values())}, {time.time()-t0:.0f}s")
    for t, n in sorted(wins.items(), key=lambda x: -x[1]):
        print(f"  {n:4d} {t}")


if __name__ == "__main__":
    main()
