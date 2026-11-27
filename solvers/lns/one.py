"""시험용: 퍼즐 몇 개를 지정한 실행 파일로 돌려 길이 변화를 본다.
사용: one.py <bin> <secs> <ids,쉼표> [추가 인자...]   (추가 인자: seed peq cap j3 trace ...)"""
import sys, json, subprocess, os, tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, 'core')
from verify import load_puzzles, read_submission, check_program
P = load_puzzles('data/puzzles.csv')
src = os.environ.get('SRC', 'best/best.csv')
cells = read_submission(src)
binary, secs, ids, extra = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4:]
def run(pid):
    pz = P[pid]; prog = json.loads(cells[pid])
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write(f"{pz.limit} {pz.registers} {len(pz.start)} {len(pz.targets)} {len(prog)}\n" + " ".join(map(str, pz.start)) + "\n" + " ".join(map(str, pz.targets)) + "\n")
        for op, a, b, d in prog: f.write(f"{op} {a} {b} {d}\n")
    r = subprocess.run([binary, path, secs] + (extra or ['1']), capture_output=True, text=True)
    os.unlink(path)
    if r.returncode: return pid, len(prog), None, 'rc %d %s' % (r.returncode, r.stderr[-300:])
    lines = r.stdout.split('\n'); n = int(lines[0].split()[1])
    new = [[x.split()[0]] + [int(y) for y in x.split()[1:]] for x in lines[1:1 + n]]
    err = check_program(pz, new)
    return pid, len(prog), (len(new) if err is None else None), (err or r.stderr.strip().split('\n')[-1])
tot0 = tot1 = 0
with ThreadPoolExecutor(max_workers=int(os.environ.get('PROCS', '6'))) as ex:
    for pid, a, b, msg in ex.map(run, ids):
        print(pid, a, '->', b, '|', msg, flush=True)
        tot0 += a; tot1 += (b if b is not None else a)
print('합계', tot0, '->', tot1, f'({100.0*(tot0-tot1)/tot0:.2f}%)')
