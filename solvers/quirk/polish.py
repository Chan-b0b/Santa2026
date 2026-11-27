"""quirk 결과를 lns 접근법의 C++ 재합성기(스냅숏 사본 solvers/quirk/elf_lns_snap)로 다듬는다.
사용: polish.py [--secs 20] [--procs 6] [--ids a,b] [--maxgap 30] [--rounds 1]
  --maxgap: quirk 길이가 best 보다 이만큼 넘게 길면 건너뛴다."""
import sys, os, json, time, argparse, subprocess, tempfile
sys.path.insert(0, 'core')
from multiprocessing import Pool
from verify import load_puzzles, check_program, write_submission, read_submission

P = load_puzzles('data/puzzles.csv')
BIN = 'solvers/quirk/elf_lns_snap3'
OUT = 'results/quirk.csv'
OPTS = "peq=1.0 pelim=0.05 pruin=0.8 ruink=12 aware=0.5 repair=2000 beamw=32"

def lns(pz, prog, secs, seed, opts=OPTS):
    fd, path = tempfile.mkstemp(prefix="quirk_", suffix=".txt")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(f"{pz.limit} {pz.registers} {len(pz.start)} {len(pz.targets)} {len(prog)}\n")
            f.write(" ".join(map(str, pz.start)) + "\n" + " ".join(map(str, pz.targets)) + "\n")
            for op, a, b, d in prog: f.write(f"{op} {a} {b} {d}\n")
        r = subprocess.run([BIN, path, f"{secs:.1f}", f"seed={seed}"] + opts.split(), capture_output=True, text=True, timeout=secs * 3 + 120)
    except Exception as e:
        return None
    finally:
        try: os.unlink(path)
        except OSError: pass
    if r.returncode != 0: return None
    lines = r.stdout.split("\n"); n = int(lines[0].split()[1])
    new = [[x.split()[0]] + [int(y) for y in x.split()[1:]] for x in lines[1:1 + n]]
    return new if check_program(pz, new) is None else None

def work(job):
    pid, prog, secs, seed = job
    new = lns(P[pid], prog, secs, seed)
    return pid, new

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--secs', type=float, default=20)
    ap.add_argument('--procs', type=int, default=6)
    ap.add_argument('--ids', default='')
    ap.add_argument('--maxgap', type=int, default=30)
    ap.add_argument('--rounds', type=int, default=1)
    ap.add_argument('--seed', type=int, default=11)
    a = ap.parse_args()
    for rnd in range(a.rounds):
        cur = {pid: len(json.loads(c)) for pid, c in read_submission('best/best.csv').items()}
        mine = {pid: json.loads(c) for pid, c in read_submission(OUT).items()}
        ids = a.ids.split(',') if a.ids else sorted(mine)
        jobs = [(pid, mine[pid], a.secs, a.seed + rnd) for pid in ids if pid in mine and len(mine[pid]) - cur[pid] <= a.maxgap]
        print(f'round {rnd}: {len(jobs)} puzzles', flush=True)
        t0 = time.time(); n = 0; better = 0; gain = 0
        with Pool(a.procs) as pool:
            for pid, new in pool.imap_unordered(work, jobs):
                n += 1
                old = len(mine[pid])
                if new is not None and len(new) < old:
                    # 그 사이 run.py 등이 더 짧은 것을 썼을 수 있으니 저장 직전에 다시 읽어 합친다
                    mine[pid] = new
                ln = len(mine[pid])
                if ln < cur[pid]: better += 1; gain += cur[pid] - ln
                print(f'{pid} best {cur[pid]} quirk {old} -> {ln} ({ln-cur[pid]:+d})', flush=True)
                if n % 20 == 0 or n == len(jobs):
                    disk = {p: json.loads(c) for p, c in read_submission(OUT).items()}
                    for p, pr in disk.items():
                        if p not in mine or len(pr) < len(mine[p]): mine[p] = pr
                    write_submission(OUT, mine)
                    print(f'[{time.time()-t0:.0f}s] {n}/{len(jobs)} better than best: {better} puzzles, gain {gain}', flush=True)
    print('done')

if __name__ == '__main__':
    main()
