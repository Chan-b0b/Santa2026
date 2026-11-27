"""시험용: 퍼즐마다 여러 씨로 돌려 최선을 고른다. 사용: multi.py <bin> <secs> <ids,쉼표> <씨들,쉼표> [key=value ...]
환경변수 SRC(출발 파일), PROCS."""
import sys, json, subprocess, os, tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, 'core')
from verify import load_puzzles, read_submission, check_program
P = load_puzzles('data/puzzles.csv')
cells = read_submission(os.environ.get('SRC', 'best/best.csv'))
binary, secs, ids, seeds, extra = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4].split(','), sys.argv[5:]
def run(job):
    pid, seed = job
    pz = P[pid]; prog = json.loads(cells[pid])
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write(f"{pz.limit} {pz.registers} {len(pz.start)} {len(pz.targets)} {len(prog)}\n" + " ".join(map(str, pz.start)) + "\n" + " ".join(map(str, pz.targets)) + "\n")
        for op, a, b, d in prog: f.write(f"{op} {a} {b} {d}\n")
    r = subprocess.run([binary, path, secs, f"seed={seed}"] + extra, capture_output=True, text=True)
    os.unlink(path)
    if r.returncode: return pid, len(prog), len(prog)
    lines = r.stdout.split('\n'); n = int(lines[0].split()[1])
    new = [[x.split()[0]] + [int(y) for y in x.split()[1:]] for x in lines[1:1 + n]]
    return pid, len(prog), (len(new) if check_program(pz, new) is None else len(prog))
best = {}; base = {}
with ThreadPoolExecutor(max_workers=int(os.environ.get('PROCS', '6'))) as ex:
    for pid, a, b in ex.map(run, [(i, s) for i in ids for s in seeds]):
        base[pid] = a; best[pid] = min(best.get(pid, a), b)
t0 = sum(base.values()); t1 = sum(best.values())
print(f"씨 {len(seeds)}개 × {secs}초: 합계 {t0} -> {t1} ({100.0*(t0-t1)/t0:.2f}%)")
