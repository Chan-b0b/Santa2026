#!/usr/bin/env python3
"""lns 실행기.

사용법 (프로젝트 루트에서):
    .tools/bin/pypy3 -I -u solvers/lns/run.py [--src best/best.csv] [--procs 8] [--ids scored_0001,scored_0002]
                                              [--every 7 --offset 0] [--passes 3] [--positions late|old|all]

입력 프로그램(기본 best/best.csv)을 퍼즐별로 다시 합성해 더 짧아진 것만 results/lns.csv 에 쓴다.
results/lns.csv 에 이미 더 짧은 것이 있으면 그대로 둔다. 50개마다 중간 저장한다.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "core"))
from verify import check_program, load_puzzles, read_submission, write_submission  # noqa: E402
import lns  # noqa: E402

PUZZLES = None
ARGS = None


def work(item):
    pid, cell = item
    pz = PUZZLES[pid]
    prog = json.loads(cell)
    t0 = time.time()
    try:
        new, info = lns.improve(pz, prog, passes=ARGS.passes, positions=ARGS.positions)
    except Exception as e:  # 한 퍼즐의 오류가 전체 실행을 멈추지 않게 한다
        return pid, None, {"error": repr(e)}, time.time() - t0
    return pid, (new if len(new) < len(prog) else None), info, time.time() - t0


def main():
    global PUZZLES, ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(ROOT, "best", "best.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "lns.csv"))
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--ids", default="")
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--positions", default="late")
    ap.add_argument("--dry", action="store_true", help="결과 파일을 쓰지 않는다")
    ARGS = ap.parse_args()
    PUZZLES = load_puzzles(os.path.join(ROOT, "data", "puzzles.csv"))
    cells = read_submission(ARGS.src)
    ids = sorted(cells)
    if ARGS.ids:
        ids = [i for i in ARGS.ids.split(",") if i in cells]
    ids = ids[ARGS.offset::ARGS.every]

    have = {}
    if os.path.exists(ARGS.out):
        for pid, cell in read_submission(ARGS.out).items():
            prog = json.loads(cell)
            if pid in PUZZLES and check_program(PUZZLES[pid], prog) is None:
                have[pid] = prog

    def save():
        if not ARGS.dry and have:
            write_submission(ARGS.out, have)

    t0 = time.time()
    done = gain = better = errors = 0
    base = 0
    with Pool(ARGS.procs) as pool:
        for pid, new, info, dt in pool.imap_unordered(work, [(i, cells[i]) for i in ids]):
            done += 1
            base += info.get("in", 0)
            if "error" in info:
                errors += 1
                print(f"오류 {pid}: {info['error']}", flush=True)
            if new is not None:
                g = info["in"] - len(new)
                gain += g
                better += 1
                if pid not in have or len(new) < len(have[pid]):
                    have[pid] = new
            if done % 50 == 0 or done == len(ids):
                save()
                print(f"{done}/{len(ids)} 개선 {better} 줄인 명령 {gain} (입력 합계 {base}) 오류 {errors} {time.time()-t0:.0f}s",
                      flush=True)
    save()


if __name__ == "__main__":
    main()
