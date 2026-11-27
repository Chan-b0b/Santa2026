#!/usr/bin/env python3
"""해독한 숨은 정수(hubs.py -> bases_scored.json)를 씨앗으로 넣어 relate 솔버를 다시 돌린다.
퍼즐별로 씨앗 조합/순서와 설정을 바꿔 가며 가장 짧은 유효 프로그램을 찾고, 기존 results/relate.csv 보다 짧을 때만 바꾼다.
사용: pypy3 -I solvers/relate/runseeds.py [--budget 10] [--ids a,b] [--dry] [--mod solver3] [--bases file]
"""
import sys, os, json, time, argparse, random, importlib
ROOT = '/home/maverick/Santa2026'
sys.path.insert(0, ROOT + '/core'); sys.path.insert(0, ROOT + '/solvers/relate')
from multiprocessing import Pool
from verify import load_puzzles, check_program, write_submission, read_submission

P = load_puzzles(ROOT + '/data/puzzles.csv')
OUT = ROOT + '/results/relate.csv'
BASE_CFG = {"W2": 6, "rootK": 40, "rootKslack": 99, "relfrac": 0.1}
MOD = 'solver3'


def variants(bases, alt, rng):
    out = [tuple(bases), tuple(alt), tuple(sorted(bases)), tuple(sorted(alt)), tuple(sorted(bases, reverse=True))]
    for k in range(len(bases) - 1, 1, -1):
        out.append(tuple(bases[:k]))
        out.append(tuple(sorted(alt[:k])))
    mix = [max(a, b) for a, b in zip(bases, alt)]
    out.append(tuple(sorted(mix, reverse=True)))
    for _ in range(3):
        b = list(alt); rng.shuffle(b); out.append(tuple(b))
    seen = set(); res = []
    for v in out:
        if v and v not in seen:
            seen.add(v); res.append(v)
    return res


def work(job):
    pid, bases, alt, budget, rs0, prev = job
    mod = importlib.import_module(MOD)
    pz = P[pid]; t0 = time.time(); rng = random.Random(len(pid) * 7919 + int(pid[-4:]) + rs0)
    best = None; how = None; tried = 0
    cfgs = [dict(BASE_CFG)] if rs0 == 0 else []
    for i in range(rs0 + 1, rs0 + 13):
        c = dict(BASE_CFG); c["rseed"] = i; c["noise"] = 1.0; c["rootpick"] = 1
        v = i % 4
        if v == 1: c["W2"] = 12
        elif v == 2: c["QN"] = 28; c["qgap"] = 14
        elif v == 3: c["s1depth"] = 1
        else: c["cshift"] = 2
        if i % 3 == 0: c["seedsort"] = 1
        cfgs.append(c)
    vs = variants(bases, alt, rng)
    if prev:
        # 지난 실행에서 가장 좋았던 씨앗 조합을 먼저, 나머지는 설정마다 두 개씩만 돌려 가며 시도
        vs = [prev] + [v for v in vs if v != prev]
        rot = vs[1:]
        plan = []
        for ci, cfg in enumerate(cfgs):
            extra = [rot[(2 * ci + k) % len(rot)] for k in range(2)] if rot else []
            plan.append((cfg, [prev] + extra))
    else:
        plan = [(cfg, vs) for cfg in cfgs]
    done = False
    for ci, (cfg, vlist) in enumerate(plan):
        for sv in vlist:
            if time.time() - t0 > budget and best is not None:
                done = True; break
            c = dict(cfg); c["seeds"] = sv
            try:
                prog, log, cap = mod.solve_once(pz, c)
            except Exception:
                prog = None
            tried += 1
            if prog is not None and check_program(pz, prog) is None and (best is None or len(prog) < len(best)):
                best = prog; how = (ci, sv)
            if time.time() - t0 > 3 * budget:
                done = True; break
        if done: break
    return pid, best, how, tried, time.time() - t0


def main():
    global MOD
    ap = argparse.ArgumentParser()
    ap.add_argument('--budget', type=float, default=10)
    ap.add_argument('--ids', default='')
    ap.add_argument('--dry', action='store_true')
    ap.add_argument('--mod', default='solver3')
    ap.add_argument('--bases', default=ROOT + '/solvers/relate/bases_scored.json')
    ap.add_argument('--procs', type=int, default=5)
    ap.add_argument('--rs0', type=int, default=0)
    ap.add_argument('--prev', default='')
    a = ap.parse_args()
    MOD = a.mod
    bases = {}
    for f in a.bases.split(','):
        bases.update(json.load(open(f)))
    prev = {}
    import re
    for f in a.prev.split(','):
        if not f: continue
        for line in open(f):
            m = re.match(r'(scored_\d+) relate \S+ -> \d+ .* seeds \(([^)]*)\)', line)
            if m:
                prev[m.group(1)] = tuple(int(x) for x in m.group(2).replace(' ', '').split(',') if x)
    mine = {pid: json.loads(c) for pid, c in read_submission(OUT).items()}
    cur = {pid: len(json.loads(c)) for pid, c in read_submission(ROOT + '/best/best.csv').items()}
    ids = a.ids.split(',') if a.ids else sorted(bases)
    jobs = [(pid, bases[pid]['bases'], bases[pid]['alt'], a.budget, a.rs0, prev.get(pid)) for pid in ids if pid in bases]
    print(f'{len(jobs)} puzzles with bases, mod {MOD}', flush=True)
    t0 = time.time(); n = 0; gain = 0; better = 0; beatbest = 0
    with Pool(a.procs, initializer=_init, initargs=(MOD,)) as pool:
        for pid, prog, how, tried, dt in pool.imap_unordered(work, jobs):
            n += 1
            old = len(mine[pid]) if pid in mine else None
            if prog is not None:
                if old is None or len(prog) < old:
                    gain += (old - len(prog)) if old else 0; better += 1
                    if not a.dry: mine[pid] = prog
                if len(prog) < cur[pid]: beatbest += 1
                print(f'{pid} relate {old} -> {len(prog)} (best {cur[pid]}) tried {tried} {dt:.0f}s seeds {how[1] if how else None} cfg {how[0] if how else None}', flush=True)
            else:
                print(f'{pid} failed tried {tried}', flush=True)
            if n % 25 == 0 or n == len(jobs):
                if not a.dry: write_submission(OUT, mine)
                print(f'[{time.time()-t0:.0f}s] {n}/{len(jobs)} improved {better} gain {gain} beat-best {beatbest}', flush=True)
    if not a.dry: write_submission(OUT, mine)
    print(f'done {time.time()-t0:.0f}s: improved {better}, gain {gain}, beat-best {beatbest}')


def _init(m):
    global MOD
    MOD = m


if __name__ == '__main__':
    main()
