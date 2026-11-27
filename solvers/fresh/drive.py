"""drive.py <chunk> <nchunks> <secs> <log.jsonl> [--cfgs 'chain:0,chain:1,...'] : 퍼즐 목록을 나눠 새 구성+lns 실행"""
import sys, os, json, time, subprocess, tempfile
from multiprocessing import Pool
R = "/home/maverick/Santa2026"; H = R + "/solvers/fresh"
sys.path[:0] = [R + "/core", R + "/solvers/lns"]
from verify import load_puzzles, check_program, read_submission
from store import save_merge
PZ = load_puzzles(R + "/data/puzzles.csv")
OPTS = "peq=1.0 pelim=0.05 pruin=0.8 ruink=12 aware=0.5 repair=2000 beamw=32".split()
MIX = "chain:0,chain:1,chain:2,relate:0,relate:1,relate:2,search:0,search:1,search:2,factor:0"

def work(it):
    pid, sv, k, secs, seed = it
    pz = PZ[pid]; t0 = time.time()
    r = subprocess.run([R + "/.venv/bin/python", "-I", H + "/gen.py", pid, sv, str(k)], capture_output=True, text=True, timeout=300)
    last = r.stdout.strip().split("\n")[-1] if r.stdout.strip() else "NONE"
    if last == "NONE":
        return dict(pid=pid, solver=sv, cfg=k, raw=None, out=None, err=r.stderr[-200:])
    prog = json.loads(last)
    fd, path = tempfile.mkstemp(prefix="fr_", suffix=".txt", dir=os.environ.get("TMPDIR"))
    with os.fdopen(fd, "w") as f:
        f.write(f"{pz.limit} {pz.registers} {len(pz.start)} {len(pz.targets)} {len(prog)}\n")
        f.write(" ".join(map(str, pz.start)) + "\n" + " ".join(map(str, pz.targets)) + "\n")
        for op, a, b, d in prog: f.write(f"{op} {a} {b} {d}\n")
    try:
        p = subprocess.run([H + "/elf_lns", path, f"{secs:.1f}", f"seed={seed}"] + OPTS, capture_output=True, text=True, timeout=secs * 3 + 120)
    finally:
        os.unlink(path)
    ls = p.stdout.split("\n"); n = int(ls[0].split()[1]); new = [[o, int(a), int(b), int(d)] for o, a, b, d in (l.split() for l in ls[1:1 + n])]
    err = check_program(pz, new)
    return dict(pid=pid, solver=sv, cfg=k, raw=len(prog), out=len(new) if err is None else None, err=err, prog=new if err is None else None, secs=time.time() - t0)

def main():
    ch, nch, secs, log = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    mix = (sys.argv[sys.argv.index("--cfgs") + 1] if "--cfgs" in sys.argv else MIX).split(",")
    if "--ids" in sys.argv:
        puz = json.load(open(sys.argv[sys.argv.index("--ids") + 1])); ids = list(puz)[ch::nch]
    else:
        puz = json.load(open(H + "/puzzles20.json")); ids = sorted(puz)[ch::nch]
    sc = "--scale" in sys.argv
    rs = int(sys.argv[sys.argv.index("--rseed") + 1]) if "--rseed" in sys.argv else 1000
    items = [(pid, m.split(":")[0], int(m.split(":")[1]), secs * (max(0.4, min(1.0, puz[pid] / 150)) if sc else 1), rs + i * 17 + j) for i, pid in enumerate(ids) for j, m in enumerate(mix)]
    items = [(a, b, k, s, sd) for a, b, k, s, sd in items]
    out = H + "/../../results/fresh.csv"
    have = {pid: json.loads(c) for pid, c in read_submission(out).items()} if os.path.exists(out) else {}
    bestl = {pid: len(json.loads(c)) for pid, c in read_submission(R + "/best/best.csv").items()}
    t0 = time.time(); done = 0
    with Pool(5) as pool, open(log, "a") as lf:
        for r in pool.imap_unordered(work, items):
            done += 1
            prog = r.pop("prog", None); r["best"] = puz.get(r["pid"]); r["best_now"] = bestl[r["pid"]]
            lf.write(json.dumps(r) + "\n"); lf.flush()
            if prog and len(prog) < min(bestl[r["pid"]], len(have.get(r["pid"], [0] * 10 ** 9))):
                have[r["pid"]] = prog; save_merge(out, have, PZ)
                print("WIN", r["pid"], len(prog), "vs", bestl[r["pid"]], flush=True)
            print(f"{done}/{len(items)} {r['pid']} {r['solver']}:{r['cfg']} raw {r['raw']} out {r['out']} best {r['best']} {time.time()-t0:.0f}s", flush=True)
main()
