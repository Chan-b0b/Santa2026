"""2회차 3번: mixed 퍼즐에서 한 자릿수 구간에 몰린 무작위 절반을 빼고 나머지 절반만 해독기에 넣는다.
사용: mixhalf.py practice|scored [--procs N] [--full] out.json   (--full: 비교용으로 전체 목표를 넣는다)"""
import sys, json, csv, collections
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from multiprocessing import Pool
from verify import load_puzzles
import decode_any, decode2, decode8
def split(pz):
    T = sorted(set(pz.targets)); nd = collections.Counter(len(str(t)) for t in T)
    md, mc = nd.most_common(1)[0]
    return [t for t in T if len(str(t)) != md], md
def work(arg):
    pid, pz, full = arg
    S, md = split(pz)
    inp = sorted(set(pz.targets)) if full else S
    B, cov = decode_any.decode(inp, 24)
    B, cov = decode2.finalize(inp, B) if B else ([], {})
    if B:
        B, added, _ = decode8.extend(inp, B)
    Tall = sorted(t for t in set(pz.targets) if t >= 1 << 16)
    Ts = [t for t in S if t >= 1 << 16]
    c = decode2.explain(Ts, B) if B else {}
    return pid, B, len(c), len(Ts)
if __name__ == '__main__':
    a = sys.argv[1:]; mode = a[0]; full = '--full' in a
    procs = int(a[a.index('--procs') + 1]) if '--procs' in a else 2
    if mode == 'practice':
        P = load_puzzles('data/practice_puzzles.csv')
        fam = {r['id']: r['family'] for r in csv.DictReader(open('data/practice_puzzles.csv'))}
        ids = [p for p in sorted(P) if fam[p] == 'mixed']
    else:
        P = load_puzzles('data/puzzles.csv'); C = json.load(open('solvers/quirk/family_guess.json'))
        ids = [p for p in sorted(P) if C[p][0] == 'mixed']
        if '--ids' in a: ids = a[a.index('--ids') + 1].split(',')
    out = {}; dec = 0; ex = 0; tot = 0
    with Pool(procs) as pool:
        for pid, B, c, n in pool.imap_unordered(work, [(p, P[p], full) for p in ids]):
            tot += n; ex += c; dec += bool(B)
            if B: out[pid] = {'bases': B[:8], 'cov': {}, 'nt': c}
            print(pid, 'bases', B[:8], 'struct-half explained', c, '/', n, flush=True)
    print('puzzles', len(ids), 'decoded', dec, 'struct-half targets explained', ex, '/', tot)
    json.dump(out, open(a[-1], 'w'))
