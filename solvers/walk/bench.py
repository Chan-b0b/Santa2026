#!/usr/bin/env python3
"""walk / lns 비교 실행기.

사용 (프로젝트 루트에서):
    .venv/bin/python -I -u solvers/walk/bench.py --bin solvers/walk/walk --ids solvers/walk/set30.txt \
        --secs 120 --seeds 1,2 --procs 5 --tag walk --out solvers/walk/bench_walk.jsonl [--opts "pu0=0.02 pu1=0.0005"] [--save]

- 출발 프로그램은 best/best.csv (--src 로 바꿀 수 있음). 퍼즐마다 고정 --secs 초.
- 모든 출력은 core/verify.py 의 check_program 으로 검사한다. 무효면 기록만 하고 버린다.
- --save: best 보다 짧고 유효한 프로그램을 results/walk.csv 에 퍼즐별 최단으로 합쳐 쓴다(잠금 + 임시 파일 교체).
- 결과 한 줄 = (퍼즐, 씨) 하나: jsonl 에 pid, seed, base(출발 길이), len(결과 길이, 무효면 null), err, stats(stderr 마지막 줄), sec.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "core"))
from verify import check_program, load_puzzles, read_submission, write_submission  # noqa: E402

PUZZLES = None
ARGS = None
SRC = None


def work(item):
    pid, seed = item
    pz = PUZZLES[pid]
    prog = SRC[pid]
    t0 = time.time()
    fd, path = tempfile.mkstemp(prefix="walk_", suffix=".txt")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(f"{pz.limit} {pz.registers} {len(pz.start)} {len(pz.targets)} {len(prog)}\n")
            f.write(" ".join(map(str, pz.start)) + "\n")
            f.write(" ".join(map(str, pz.targets)) + "\n")
            for op, a, b, d in prog:
                f.write(f"{op} {a} {b} {d}\n")
        r = subprocess.run([ARGS.bin, path, f"{ARGS.secs:.1f}", f"seed={seed}"] + ARGS.opts.split(),
                           capture_output=True, text=True, timeout=ARGS.secs * 3 + 120)
    except Exception as e:  # 한 퍼즐의 오류가 전체를 멈추지 않게 한다
        return dict(pid=pid, seed=seed, base=len(prog), len=None, err=f"실행 오류 {e!r}", stats="", sec=time.time() - t0), None
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    stats = r.stderr.strip().split("\n")[-1] if r.stderr.strip() else ""
    if r.returncode != 0:
        return dict(pid=pid, seed=seed, base=len(prog), len=None, err=f"종료 코드 {r.returncode}: {r.stderr.strip()[-300:]}", stats=stats, sec=time.time() - t0), None
    lines = r.stdout.split("\n")
    n = int(lines[0].split()[1])
    new = []
    for ln in lines[1:1 + n]:
        op, a, b, d = ln.split()
        new.append([op, int(a), int(b), int(d)])
    err = check_program(pz, new)
    if err is not None:
        return dict(pid=pid, seed=seed, base=len(prog), len=None, err=f"무효: {err}", stats=stats, sec=time.time() - t0), None
    return dict(pid=pid, seed=seed, base=len(prog), len=len(new), err=None, stats=stats, sec=time.time() - t0), new


def save_better(path, found):
    """found(pid -> 프로그램)을 path 의 것과 퍼즐별 최단으로 합쳐 쓴다."""
    with open(str(path) + ".lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        have = {}
        if os.path.exists(path):
            for pid, cell in read_submission(path).items():
                prog = json.loads(cell)
                if pid in PUZZLES and check_program(PUZZLES[pid], prog) is None:
                    have[pid] = prog
        for pid, prog in found.items():
            if check_program(PUZZLES[pid], prog) is None and (pid not in have or len(prog) < len(have[pid])):
                have[pid] = prog
        if have:
            write_submission(path, have)


def main():
    global PUZZLES, ARGS, SRC
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", required=True)
    ap.add_argument("--ids", required=True, help="퍼즐 id 파일(쉼표 또는 줄바꿈) 또는 쉼표 목록")
    ap.add_argument("--src", default=os.path.join(ROOT, "best", "best.csv"))
    ap.add_argument("--secs", type=float, default=120)
    ap.add_argument("--seeds", default="1,2")
    ap.add_argument("--procs", type=int, default=5)
    ap.add_argument("--opts", default="")
    ap.add_argument("--tag", default="run")
    ap.add_argument("--out", required=True)
    ap.add_argument("--save", action="store_true", help="best 보다 짧은 유효 프로그램을 results/walk.csv 에 쓴다")
    ARGS = ap.parse_args()
    PUZZLES = load_puzzles(os.path.join(ROOT, "data", "puzzles.csv"))
    SRC = {pid: json.loads(cell) for pid, cell in read_submission(ARGS.src).items()}
    best = {pid: json.loads(cell) for pid, cell in read_submission(os.path.join(ROOT, "best", "best.csv")).items()}
    if os.path.exists(ARGS.ids):
        ids = [x.strip() for x in open(ARGS.ids).read().replace("\n", ",").split(",") if x.strip()]
    else:
        ids = [x for x in ARGS.ids.split(",") if x]
    seeds = [int(s) for s in ARGS.seeds.split(",")]
    items = [(pid, s) for s in seeds for pid in ids]
    t0 = time.time()
    done = 0
    found = {}
    with open(ARGS.out, "a") as fo, Pool(ARGS.procs) as pool:
        for rec, new in pool.imap_unordered(work, items):
            done += 1
            rec["tag"] = ARGS.tag
            rec["bestlen"] = len(best[rec["pid"]])
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fo.flush()
            d = (rec["len"] - rec["bestlen"]) if rec["len"] is not None else None
            print(f"[{ARGS.tag}] {done}/{len(items)} {rec['pid']} seed {rec['seed']} best {rec['bestlen']} -> {rec['len']} "
                  f"({d if d is not None else rec['err']}) {rec['sec']:.0f}s | {rec['stats'][:220]}  t={time.time() - t0:.0f}s", flush=True)
            if ARGS.save and new is not None and len(new) < rec["bestlen"]:
                pid = rec["pid"]
                if pid not in found or len(new) < len(found[pid]):
                    found[pid] = new
                    save_better(os.path.join(ROOT, "results", "walk.csv"), {pid: new})
                    print(f"  저장: {pid} {rec['bestlen']} -> {len(new)}", flush=True)
    print(f"[{ARGS.tag}] 끝 {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
