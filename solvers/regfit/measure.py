"""사용: measure.py <bin> <secs> <list> <outprefix> <seed> [opts...] ; 퍼즐별 stderr 를 모아 RF 줄 집계. SRC 환경변수로 출발 파일."""
import sys, json, subprocess, os, tempfile, re, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, 'core')
from verify import load_puzzles, read_submission, check_program
P = load_puzzles('data/puzzles.csv'); cells = read_submission(os.environ.get('SRC','best/best.csv'))
binary, secs, lst, out, seed = sys.argv[1:6]; extra = sys.argv[6:]
ids = [l.split()[0] for l in open(lst) if l.strip()]
def run(pid):
    pz = P[pid]; prog = json.loads(cells[pid])
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write(f"{pz.limit} {pz.registers} {len(pz.start)} {len(pz.targets)} {len(prog)}\n" + " ".join(map(str, pz.start)) + "\n" + " ".join(map(str, pz.targets)) + "\n")
        for op, a, b, d in prog: f.write(f"{op} {a} {b} {d}\n")
    try:
        r = subprocess.run([binary, path, secs, f'seed={seed}'] + extra, capture_output=True, text=True, timeout=float(secs)*2+20)
    except subprocess.TimeoutExpired as e:
        os.unlink(path); return pid, len(prog), None, 'TIMEOUT'
    os.unlink(path)
    if r.returncode: return pid, len(prog), None, 'rc %d'%r.returncode
    lines = r.stdout.split('\n'); n = int(lines[0].split()[1])
    new = [[x.split()[0]] + [int(y) for y in x.split()[1:]] for x in lines[1:1 + n]]
    err = check_program(pz, new)
    return pid, len(prog), (len(new) if err is None else None), r.stderr
res = {}
with ThreadPoolExecutor(max_workers=int(os.environ.get('PROCS','5'))) as ex:
    for pid, a, b, err in ex.map(run, ids):
        rf = [l for l in err.split('\n') if l.startswith('RF ')]
        res[pid] = dict(start=a, end=b, rf=rf, last=err.strip().split('\n')[-1])
        print(pid, a, '->', b, 'RF', len(rf), flush=True)
json.dump(res, open(out, 'w'))
