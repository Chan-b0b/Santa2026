"""factor 솔버 실행기.

사용법 (프로젝트 루트에서):
    python3 -I solvers/factor/run.py practice [--limit N] [--tl 초] [--ids a,b]
    python3 -I solvers/factor/run.py scored   [--tl 초] [--name factor]

scored 모드는 results/<name>.csv 를 읽어 퍼즐별로 더 짧을 때만 바꿔 쓴다.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from multiprocessing import Pool

ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core")
sys.path.insert(0, ROOT + "/solvers/factor")
from verify import Puzzle, check_program, load_puzzles, score_submission, write_submission

import engine as E1
import seeds as SEEDS
import engine2 as E2
import engine3 as E3
try:
    import engine3_snap1 as E3S
except ImportError:
    E3S = None
E = E3

_FACS = {}
_CFG = {}
_HID = {}
_DEC2 = {}


def load_facs(name):
    path = f"{ROOT}/solvers/factor/cache/factors_{name}.json"
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        raw = json.load(f)
    return {int(k): {int(p): e for p, e in v} for k, v in raw.items()}


def _solve_cfg(pz, base, tl):
    """설정 하나로 풀어 (프로그램 또는 None, 사유, stats). 레지스터가 넘치면 cap 을 낮춰 다시 푼다."""
    err = "?"
    stats = {}
    for cap in (None, 36, 30):
        cfg = dict(base)
        if cap is not None:
            cfg["cap"] = cap
        eng = E.Engine(pz.start, pz.targets, pz.limit, facs=_FACS, cfg=cfg, deadline=time.time() + tl)
        steps = eng.solve()
        stats = eng.stats
        prog = E.emit(pz.start, steps, pz.registers)
        if prog is None:
            err = "레지스터 초과"
            continue
        err = check_program(pz, prog)
        if err:
            continue
        return prog, None, stats
    return None, err, stats


def solve_one(args):
    pz, tl = args
    t0 = time.time()
    try:
        base = dict(_CFG)
        sk = base.pop("seedk", None)
        budget = base.pop("budget", 0.0)      # 퍼즐당 총 시간 예산(초). 남으면 난수 씨를 바꿔 다시 푼다
        hk = base.pop("hidk", None)           # 숨은 정수 씨앗(hid_decode.py) 중 앞의 hk 개를 먼저 만든다
        hoff = base.pop("hidoff", 0)
        hmin = base.pop("hidmin", 0)
        d2 = base.pop("dec2", None)           # decode2.py 가 복원한 밑수를 먼저 만든다 (없으면 hidk 로 넘어간다)
        if d2 is not None and pz.id in _DEC2:
            bs = _DEC2[pz.id]["bases"][:d2]
            pre = sorted(bs)
            if base.pop("anchors", 0):
                # 작은 숨은 정수(닻)를 밑수보다 먼저 만든다
                import anchors as ANCH
                an = ANCH.find(pz.targets, bs)
                if not an and base.pop("anchors_only", 0):
                    return pz.id, None, "씨앗 없음", time.time() - t0, {}
                pre = sorted(an) + pre
            base.pop("anchors_only", None)
            base["preseed"] = pre
            hk = None
        elif d2 is not None and hk is None:
            return pz.id, None, "씨앗 없음", time.time() - t0, {}
        if hk is not None:
            sel = _HID.get(pz.id)
            if not sel or len(sel) <= hoff or (hmin and len(sel) < hk):
                return pz.id, None, "씨앗 없음", time.time() - t0, {}
            base["preseed"] = sorted(d for d, cnt, mask, sc in sel[hoff:hoff + hk])
        if sk is not None:
            cands = SEEDS.candidates(pz.start, pz.targets, pz.limit, facs=_FACS)
            pre = [cands[k][1] for k in sk if k < len(cands)]
            if not pre:
                return pz.id, None, "씨앗 없음", time.time() - t0, {}
            base["preseed"] = pre
        prog, err, stats = _solve_cfg(pz, base, tl)
        e1 = time.time() - t0
        k = 0
        rs0 = base.get("seed", 0) or 0
        while budget and prog is not None and len(prog) > pz.lower_bound and time.time() - t0 + e1 * 1.2 < budget and k < 60:
            k += 1
            cfg = dict(base)
            cfg["seed"] = rs0 * 1000 + k
            p2, _, st2 = _solve_cfg(pz, cfg, tl)
            if p2 is not None and len(p2) < len(prog):
                prog, stats = p2, st2
        if prog is None:
            return pz.id, None, err, time.time() - t0, stats
        return pz.id, prog, None, time.time() - t0, stats
    except Exception as e:  # noqa
        import traceback
        return pz.id, None, "예외: " + traceback.format_exc()[-600:], time.time() - t0, {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["practice", "scored"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tl", type=float, default=4.0)
    ap.add_argument("--ids", default="")
    ap.add_argument("--name", default="factor")
    ap.add_argument("--procs", type=int, default=5)
    ap.add_argument("--cfg", default="{}")
    ap.add_argument("--nowrite", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument("--engine", default="3")
    ap.add_argument("--saveevery", type=int, default=100)
    ap.add_argument("--keeporder", action="store_true", help="--ids 에 준 순서대로 푼다 (중요한 퍼즐부터)")
    args = ap.parse_args()
    global _FACS, _CFG, E, _HID, _DEC2
    E = {"1": E1, "2": E2, "3": E3, "3s": E3S}[args.engine]
    _CFG = json.loads(args.cfg)
    fam = {}
    if args.mode == "practice":
        puzzles = {}
        with open(ROOT + "/data/practice_puzzles.csv", newline="") as f:
            for r in csv.DictReader(f):
                puzzles[r["id"]] = Puzzle(r["id"], tuple(json.loads(r["starting_values"])), tuple(json.loads(r["targets"])),
                                          int(r["value_limit"]), int(r["registers"]))
                fam[r["id"]] = r["family"]
        _FACS = load_facs("practice")
    else:
        puzzles = load_puzzles(ROOT + "/data/puzzles.csv")
        _FACS = load_facs("scored")
    hp = f"{ROOT}/solvers/factor/cache/hid_{args.mode}.json"
    if os.path.exists(hp):
        with open(hp) as f:
            _HID = json.load(f)
    dp = f"{ROOT}/solvers/factor/cache/dec2_{args.mode}.json"
    if os.path.exists(dp):
        with open(dp) as f:
            _DEC2 = json.load(f)
    ids = sorted(puzzles)
    if args.ids:
        wl = args.ids.split(",")
        want = set(wl)
        if args.keeporder:
            ids = [i for i in wl if i in puzzles]
        else:
            ids = [i for i in ids if i in want or i.split("_")[1] in want]
    if args.limit:
        ids = ids[: args.limit]
    t0 = time.time()
    jobs = [(puzzles[i], args.tl) for i in ids]
    def save(progs_now, final=False):
        path = f"{ROOT}/results/{args.name}.csv"
        old = {}
        if os.path.exists(path):
            old, _ = score_submission(puzzles, path, partial=True)
        better = 0
        for pid, prog in progs_now.items():
            if pid not in old or len(prog) < len(old[pid]):
                old[pid] = prog
                better += 1
        if better:
            write_submission(path, old)
        print("  %s: %s (갱신 %d개, 총 %d개, 합계 %d)" % ("기록" if final else "중간 저장", path, better, len(old), sum(len(p) for p in old.values())), flush=True)

    res = []
    part = {}
    with Pool(args.procs) as p:
        for k, r in enumerate(p.imap_unordered(solve_one, jobs, chunksize=1)):
            res.append(r)
            if r[1] is not None:
                part[r[0]] = r[1]
            if (k + 1) % 50 == 0:
                print("[%.0fs] %d/%d 끝, 풀린 것 %d" % (time.time() - t0, k + 1, len(jobs), len(part)), flush=True)
                if args.mode == "scored" and not args.nowrite and (k + 1) % args.saveevery == 0:
                    save(part)
    progs = {}
    fails = []
    stats = defaultdict(int)
    fam_len = defaultdict(list)
    tmax = 0
    for pid, prog, err, dt, st in res:
        tmax = max(tmax, dt)
        for k, v in st.items():
            stats[k] += v
        if prog is None:
            fails.append((pid, err))
            continue
        progs[pid] = prog
        fam_len[fam.get(pid, "all")].append((len(prog), puzzles[pid].lower_bound, pid))
    noseed = [f for f in fails if f[1] == "씨앗 없음"]
    fails = [f for f in fails if f[1] != "씨앗 없음"]
    print("퍼즐 %d개, 성공 %d, 실패 %d, 씨앗 없어 건너뜀 %d, 경과 %.1fs, 최장 퍼즐 %.1fs" % (len(ids), len(progs), len(fails), len(noseed), time.time() - t0, tmax))
    for pid, err in fails[:10]:
        print("  실패", pid, err)
    if args.out:
        with open(args.out, "w") as f:
            json.dump({pid: len(p) for pid, p in progs.items()}, f)
    for f, ls in sorted(fam_len.items()):
        n = sum(l for l, _, _ in ls)
        lb = sum(b for _, b, _ in ls)
        print("  %-15s 퍼즐 %3d  명령 %6d  평균 %.1f  하한 %d  목표당 %.2f" % (f, len(ls), n, n / len(ls), lb, n / max(lb, 1)))
    tags = sorted(k for k in stats if not k.endswith("#"))
    print("  유도별 (명령수/횟수):", ", ".join(f"{k}={stats[k]}/{stats[k + '#']}" for k in tags))
    if args.mode == "scored" and not args.nowrite:
        save(progs, final=True)


if __name__ == "__main__":
    main()
