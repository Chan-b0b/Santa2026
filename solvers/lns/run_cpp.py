#!/usr/bin/env python3
"""elf_lns(C++) 실행기.

사용법 (프로젝트 루트에서):
    g++ -O2 -march=native -std=c++17 -o solvers/lns/elf_lns solvers/lns/elf_lns.cpp
    .venv/bin/python -I -u solvers/lns/run_cpp.py --secs 20 --procs 12 [--src best/best.csv] [--ids a,b] [--every 10 --offset 0]
                                                  [--opts "peq=1.0 pelim=0.05 pruin=0.8 ruink=12 aware=0.5 repair=2000 beamw=32"] [--seed 1] [--rounds 1] [--dry]

입력 프로그램(기본: best/best.csv 와 results/lns.csv 중 퍼즐별로 짧은 쪽)을 퍼즐마다 --secs 초씩 재합성한다.
core/verify.py 의 check_program 을 통과하고 더 짧아진 것만 results/lns.csv 에 쓴다. 25개마다 중간 저장한다.
--rounds N 이면 전체를 N 번 되풀이한다(매번 그때까지의 최선에서 다시 시작, 난수씨는 바뀐다).
"""
from __future__ import annotations

import argparse
import hashlib
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
from verify import check_program, load_puzzles, read_submission, write_submission  # noqa: E402,F401
sys.path.insert(0, HERE)
from store import save_merge  # noqa: E402

BIN = os.path.join(HERE, "elf_lns")
PUZZLES = None
ARGS = None


def work(item):
    pid, prog, seed, secs = item
    pz = PUZZLES[pid]
    t0 = time.time()
    fd, path = tempfile.mkstemp(prefix="elf_", suffix=".txt")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(f"{pz.limit} {pz.registers} {len(pz.start)} {len(pz.targets)} {len(prog)}\n")
            f.write(" ".join(map(str, pz.start)) + "\n")
            f.write(" ".join(map(str, pz.targets)) + "\n")
            for op, a, b, d in prog:
                f.write(f"{op} {a} {b} {d}\n")
        r = subprocess.run([BIN, path, f"{secs:.1f}", f"seed={seed}"] + ARGS.opts.split(),
                           capture_output=True, text=True, timeout=secs * 3 + 120)
    except Exception as e:  # 한 퍼즐의 오류가 전체를 멈추지 않게 한다
        return pid, None, f"실행 오류 {e!r}", time.time() - t0
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if r.returncode != 0:
        return pid, None, f"종료 코드 {r.returncode}: {r.stderr.strip()[-200:]}", time.time() - t0
    lines = r.stdout.split("\n")
    n = int(lines[0].split()[1])
    new = []
    for ln in lines[1:1 + n]:
        op, a, b, d = ln.split()
        new.append([op, int(a), int(b), int(d)])
    err = check_program(pz, new)
    if err is not None:
        return pid, None, f"무효: {err}", time.time() - t0
    return pid, new, r.stderr.strip(), time.time() - t0


def main():
    global PUZZLES, ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(ROOT, "best", "best.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "lns.csv"))
    ap.add_argument("--secs", type=float, default=20)
    ap.add_argument("--procs", type=int, default=12)
    ap.add_argument("--ids", default="")
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--opts", default="peq=1.0 pelim=0.05 pruin=0.8 ruink=12 aware=0.5 repair=2000 beamw=32", help="elf_lns 에 넘길 key=value 설정들")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--from-src", action="store_true", help="results/lns.csv 에 더 짧은 것이 있어도 --src 의 프로그램에서 출발한다")
    ap.add_argument("--slow-scale", type=float, default=1.0, help="목표값당 명령이 6.3개 이상인 퍼즐(무작위형)의 시간 배율")
    ap.add_argument("--max-tries", type=int, default=0, help="같은 출발 프로그램을 이 횟수만큼 돌렸으면 건너뛴다 (0 이면 제한 없음). 기록은 solvers/lns/seen.json")
    ap.add_argument("--dry", action="store_true", help="결과 파일을 쓰지 않는다")
    ap.add_argument("--verbose", action="store_true")
    ARGS = ap.parse_args()
    PUZZLES = load_puzzles(os.path.join(ROOT, "data", "puzzles.csv"))

    def load(path):
        out = {}
        if os.path.exists(path):
            for pid, cell in read_submission(path).items():
                try:
                    prog = json.loads(cell)
                except ValueError:
                    continue
                if pid in PUZZLES and check_program(PUZZLES[pid], prog) is None:
                    out[pid] = prog
        return out

    have = load(ARGS.out)                      # results/lns.csv 에 이미 있는 것
    t0 = time.time()
    for rnd in range(ARGS.rounds):
        src = load(ARGS.src)                   # 다른 접근법이 best 를 갱신했을 수 있으니 매 회 다시 읽는다
        cur = dict(src)
        if not ARGS.from_src:
            for pid, prog in have.items():
                if pid not in cur or len(prog) < len(cur[pid]):
                    cur[pid] = prog
        best = load(os.path.join(ROOT, "best", "best.csv"))
        ref = {pid: min(len(best[pid]) if pid in best else 10 ** 9, len(have[pid]) if pid in have else 10 ** 9) for pid in cur}
        ids = sorted(cur)
        if ARGS.ids:
            ids = [i for i in ARGS.ids.split(",") if i in cur]
        ids = ids[ARGS.offset::ARGS.every]
        base = sum(len(cur[i]) for i in ids)
        done = gain = better = errors = 0
        # 같은 출발 프로그램을 이미 여러 번 돌렸으면 건너뛴다
        seen_path = os.path.join(HERE, "seen.json")
        seen = {}
        if ARGS.max_tries > 0 and os.path.exists(seen_path):
            try:
                seen = json.load(open(seen_path, encoding="utf-8"))
            except ValueError:
                seen = {}
        tag = os.path.basename(ARGS.src) if ARGS.from_src else "best"
        def key(i):
            return f"{tag}:{i}"
        def sig(i):
            return hashlib.sha1(json.dumps(cur[i], separators=(",", ":")).encode()).hexdigest()[:16]
        if ARGS.max_tries > 0:
            n0 = len(ids)
            ids = [i for i in ids if not (seen.get(key(i), [None, 0])[0] == sig(i) and seen[key(i)][1] >= ARGS.max_tries)]
            print(f"출발 {tag}: {n0}개 중 {len(ids)}개 실행 (나머지는 같은 프로그램을 이미 {ARGS.max_tries}번 돌림)", flush=True)
        # 이미 하한(목표값당 명령 1개)인 퍼즐은 건너뛰고, 시간은 프로그램 길이에 비례해 준다 (길이 150 이 기준)
        ids = [i for i in ids if len(cur[i]) > PUZZLES[i].lower_bound]
        def secs_for(i):
            n = len(cur[i]); lb = max(1, PUZZLES[i].lower_bound)
            return ARGS.secs * min(1.5, max(0.15, n / 150.0)) * (ARGS.slow_scale if n / lb >= 6.3 else 1.0)
        items = [(i, cur[i], ARGS.seed + 1000 * rnd + k, secs_for(i)) for k, i in enumerate(ids)]
        with Pool(ARGS.procs) as pool:
            for pid, new, msg, dt in pool.imap_unordered(work, items):
                done += 1
                if ARGS.max_tries > 0:
                    h = sig(pid); old = seen.get(key(pid), [None, 0])
                    seen[key(pid)] = [h, (old[1] if old[0] == h else 0) + 1]
                if new is None:
                    errors += 1
                    print(f"오류 {pid}: {msg}", flush=True)
                else:
                    g = ref[pid] - len(new)
                    if ARGS.verbose:
                        print(f"  {pid} {len(cur[pid])} -> {len(new)}  [{msg}] {dt:.0f}s", flush=True)
                    if g > 0:
                        gain += g
                        better += 1
                        ref[pid] = len(new)
                    if pid not in have or len(new) < len(have[pid]):
                        have[pid] = new
                if done % 25 == 0 or done == len(ids):
                    if not ARGS.dry and have:
                        save_merge(ARGS.out, have, PUZZLES)
                    if ARGS.max_tries > 0 and not ARGS.dry:
                        tmp = seen_path + f".tmp{os.getpid()}"
                        json.dump(seen, open(tmp, "w", encoding="utf-8"))
                        os.replace(tmp, seen_path)
                    print(f"회차 {rnd + 1}/{ARGS.rounds} {done}/{len(ids)} 지금까지의 최선보다 짧아진 퍼즐 {better} 줄인 명령 {gain} "
                          f"(출발 합계 {base}) 오류 {errors} {time.time() - t0:.0f}s", flush=True)
    if not ARGS.dry and have:
        save_merge(ARGS.out, have, PUZZLES)


if __name__ == "__main__":
    main()
