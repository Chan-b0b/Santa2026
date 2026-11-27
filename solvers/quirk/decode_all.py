"""전체 퍼즐에 해독기를 돌려 JSON 으로 저장한다.  사용: decode_all.py [procs] [dmax_bits] [모듈=decode] [출력=solvers/quirk/bases.json]"""
import sys, json, os, time
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles
import importlib
MOD = sys.argv[3] if len(sys.argv) > 3 else 'decode'
OUTF = sys.argv[4] if len(sys.argv) > 4 else 'solvers/quirk/bases.json'
decode = importlib.import_module(MOD).decode

P = load_puzzles('data/puzzles.csv')
BITS = int(sys.argv[2]) if len(sys.argv) > 2 else 24

def work(pid):
    p = P[pid]
    if p.limit < 1 << 16: return pid, [], {}
    B, cov = decode(p.targets, BITS)
    return pid, B, {str(t): v for t, v in cov.items()}

if __name__ == '__main__':
    procs = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    out = {}; t0 = time.time(); n = 0
    with Pool(procs) as pool:
        for pid, B, cov in pool.imap_unordered(work, sorted(P)):
            n += 1
            out[pid] = {'bases': B, 'cov': cov, 'nt': len(P[pid].targets)}
            if n % 50 == 0:
                print(f'{n} done, {time.time()-t0:.0f}s, with bases: {sum(1 for v in out.values() if v["bases"])}', flush=True)
                tmp = OUTF + '.tmp'
                json.dump(out, open(tmp, 'w')); os.replace(tmp, OUTF)
    json.dump(out, open(OUTF + '.tmp', 'w')); os.replace(OUTF + '.tmp', OUTF)
    print('done', time.time() - t0)
