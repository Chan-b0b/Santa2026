#!/usr/bin/env python3
"""relate 솔버 실행기.

  python3 -I solvers/relate/run.py practice [N] [family]   # 연습 퍼즐로 유형별 평균 길이 측정 (파일 안 씀)
  python3 -I solvers/relate/run.py scored                  # 채점 퍼즐 전체 -> results/relate.csv (더 짧을 때만 교체)
"""
import sys
import os
import csv
import json
import time
import importlib
from multiprocessing import Pool

ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core")
sys.path.insert(0, ROOT + "/solvers/relate")
from verify import load_puzzles, check_program, write_submission, read_submission  # noqa: E402

MOD = os.environ.get("RELATE_MOD", "solver3")
CFG = json.loads(os.environ.get("RELATE_CFG", "{}"))
OUT = ROOT + "/results/relate.csv"


def work(pz):
    mod = importlib.import_module(MOD)
    t0 = time.time()
    try:
        prog, info = mod.solve_puzzle(pz, CFG)
    except Exception as e:  # noqa: BLE001
        prog, info = None, repr(e)
    return pz.id, prog, info, time.time() - t0


def load_existing():
    if not os.path.exists(OUT):
        return {}
    return {pid: json.loads(cell) for pid, cell in read_submission(OUT).items()}


def main():
    mode = sys.argv[1]
    if mode == "practice":
        puzzles = load_puzzles(ROOT + "/data/practice_puzzles.csv")
        fam = {r["id"]: r["family"] for r in csv.DictReader(open(ROOT + "/data/practice_puzzles.csv"))}
        ids = sorted(puzzles)
        if len(sys.argv) > 3:
            ids = [i for i in ids if fam[i] == sys.argv[3]]
        if len(sys.argv) > 2:
            ids = ids[: int(sys.argv[2])]
        t0 = time.time()
        stats = {}
        with Pool(5) as pool:
            for pid, prog, info, dt in pool.imap_unordered(work, [puzzles[i] for i in ids]):
                f = fam[pid]
                st = stats.setdefault(f, [0, 0, 0, 0, 0.0, 0.0])
                if prog is None:
                    st[3] += 1
                    print("FAIL", pid, f, info, flush=True)
                    continue
                st[0] += 1
                st[1] += len(prog)
                st[2] += puzzles[pid].lower_bound
                st[4] += dt
                st[5] = max(st[5], dt)
        tot = 0
        for f, st in sorted(stats.items()):
            n = max(st[0], 1)
            tot += st[1]
            print(f"{f:15s} n={st[0]:3d} fail={st[3]} avg_len={st[1]/n:7.1f} per_target={st[1]/max(st[2],1):5.2f} "
                  f"avg_t={st[4]/n:5.2f}s max_t={st[5]:5.1f}s")
        print(f"total {tot}  wall {time.time()-t0:.0f}s")
        return
    puzzles = load_puzzles(ROOT + "/data/puzzles.csv")
    ids = sorted(puzzles)
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        ids = ids[: int(sys.argv[2])]
    skip = set()
    for f in os.environ.get("RELATE_SKIP", "").split(","):
        if f:
            skip |= set(json.load(open(f)))
    ids = [i for i in ids if i not in skip]
    best = load_existing()
    t0 = time.time()
    improved = 0
    fails = 0
    done = 0
    with Pool(5) as pool:
        for pid, prog, info, dt in pool.imap_unordered(work, [puzzles[i] for i in ids], chunksize=1):
            done += 1
            if prog is None:
                fails += 1
                print("FAIL", pid, info, flush=True)
            elif check_program(puzzles[pid], prog) is None:
                if pid not in best or len(prog) < len(best[pid]):
                    best[pid] = prog
                    improved += 1
            if done % 100 == 0:
                write_submission(OUT, best)
                print(f"{done} done, {time.time()-t0:.0f}s, improved {improved}, fails {fails}", flush=True)
    write_submission(OUT, best)
    print(f"finished {done} in {time.time()-t0:.0f}s; improved {improved}; fails {fails}; "
          f"have {len(best)} programs, total {sum(len(p) for p in best.values())}")


if __name__ == "__main__":
    main()
