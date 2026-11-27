"""채점 퍼즐 전체를 풀어 results/search.csv 를 갱신한다 (퍼즐별로 더 짧을 때만 교체).

사용: python3 -I solvers/search/run.py [--procs 5] [--tlimit 20] [--ids a,b,c] [--maxbits B] [--minbits B] [key=value ...]
--maxbits/--minbits 는 value_limit 의 비트 수로 퍼즐을 고른다 (작은 퍼즐만 재시작을 많이 돌릴 때 쓴다).
key=value 는 Solver 인자로 전달된다 (예: width=3 ntop=3).
"""
import sys, time, os, signal, json
sys.path.insert(0, "/home/maverick/Santa2026/core")
sys.path.insert(0, "/home/maverick/Santa2026/solvers/search")
from multiprocessing import Pool
from verify import load_puzzles, check_program, write_submission, read_submission

ROOT = '/home/maverick/Santa2026'
PUZ = ROOT + '/data/puzzles.csv'
OUT = ROOT + '/results/search.csv'
_puzzles = None
_kw = {}
_tlimit = 20
_hubs = False


class TimeUp(Exception):
    pass


def _alarm(signum, frame):
    raise TimeUp()


def work(pid):
    global _puzzles
    import solver
    if _puzzles is None:
        _puzzles = load_puzzles(PUZ)
        signal.signal(signal.SIGALRM, _alarm)
    pz = _puzzles[pid]
    t0 = time.time()
    signal.alarm(_tlimit)
    try:
        if _hubs:
            prog = solver.solve_hubs(pz, **_kw)
            signal.alarm(0)
            if prog is None:
                return pid, None, 'nohub', time.time() - t0
        else:
            prog = solver.solve_puzzle(pz, **_kw)
        signal.alarm(0)
        err = check_program(pz, prog)
    except TimeUp:
        prog, err = None, 'timeout'
    except Exception as e:
        signal.alarm(0)
        prog, err = None, 'EXC ' + repr(e)
    return pid, prog, err, time.time() - t0


def load_existing(puzzles):
    progs = {}
    if os.path.exists(OUT):
        for pid, cell in read_submission(OUT).items():
            try:
                prog = json.loads(cell)
            except ValueError:
                continue
            if pid in puzzles and check_program(puzzles[pid], prog) is None:
                progs[pid] = prog
    return progs


def main():
    global _kw, _tlimit, _hubs
    args = sys.argv[1:]
    procs = 5
    ids = None
    order = 'asc'
    maxbits = 99
    minbits = 0
    kw = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--procs':
            procs = int(args[i + 1]); i += 2
        elif a == '--tlimit':
            _tlimit = int(args[i + 1]); i += 2
        elif a == '--hubs':
            _hubs = True; i += 1
        elif a == '--order':
            order = args[i + 1]; i += 2
        elif a == '--ids':
            ids = args[i + 1].split(','); i += 2
        elif a == '--maxbits':
            maxbits = int(args[i + 1]); i += 2
        elif a == '--minbits':
            minbits = int(args[i + 1]); i += 2
        elif '=' in a:
            k, v = a.split('=', 1)
            try:
                v = int(v)
            except ValueError:
                try:
                    v = float(v)
                except ValueError:
                    pass
            kw[k] = v
            i += 1
        else:
            raise SystemExit('unknown arg ' + a)
    procs = min(procs, 5)
    _kw = kw
    puzzles = load_puzzles(PUZ)
    best = load_existing(puzzles)
    if ids is None:
        ids = sorted(pid for pid, pz in puzzles.items() if minbits <= pz.limit.bit_length() <= maxbits)
    if order == 'rev':
        ids = ids[::-1]
    elif order == 'mid':
        ids = ids[len(ids) // 2:] + ids[:len(ids) // 2]
    t0 = time.time()
    improved = 0
    errs = 0
    newtotal = 0
    slow = 0.0
    done = 0
    last_save = time.time()
    with Pool(procs) as pool:
        for pid, prog, err, dt in pool.imap_unordered(work, ids, chunksize=4):
            done += 1
            slow = max(slow, dt)
            if err == 'nohub':
                continue
            if err is not None or prog is None:
                errs += 1
                print('ERR', pid, err, flush=True)
                continue
            newtotal += len(prog)
            if pid not in best or len(prog) < len(best[pid]):
                best[pid] = prog
                improved += 1
            if time.time() - last_save > 60:
                write_submission(OUT, best)
                last_save = time.time()
                print('  .. %d/%d done, %.0fs' % (done, len(ids), time.time() - t0), flush=True)
    write_submission(OUT, best)
    print('run: %d puzzles, this-run total %d, improved %d, errors %d, max time %.1fs, wall %.0fs' % (
        len(ids), newtotal, improved, errs, slow, time.time() - t0))
    print('file now has %d programs' % len(best))


if __name__ == '__main__':
    main()
