"""숨은 정수 해독: hidscan(C++) 으로 d 를 2^24 까지 훑고, 지지 목표 집합이 같은 것 중 가장 큰 d 를 골라
점수 (지지 수 - 우연 기대치) * 비트수 순으로 서로 겹치지 않는 씨앗 목록을 만든다.

사용: .venv/bin/python -I solvers/factor/hid_decode.py scored|practice [procs]
결과: solvers/factor/cache/hid_<mode>.json  {id: [[d, cnt, mask, score], ...]}
"""
import csv, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = "/home/maverick/Santa2026"
HERE = ROOT + "/solvers/factor"


def load(mode):
    path = ROOT + "/data/" + ("practice_puzzles.csv" if mode == "practice" else "puzzles.csv")
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            out[r["id"]] = (json.loads(r["starting_values"]), json.loads(r["targets"]), r.get("family", ""))
    return out


def scan(chunk):
    inp = "".join(f"{pid} {len(tg)} " + " ".join(map(str, tg)) + "\n" for pid, tg in chunk)
    out = subprocess.run([HERE + "/hidscan"], input=inp, capture_output=True, text=True).stdout
    res = {pid: [] for pid, _ in chunk}
    for line in out.split("\n"):
        p = line.split()
        if len(p) < 4:
            continue
        res[p[0]].append((int(p[1]), int(p[2]), int(p[3], 16), [int(x) for x in p[4:]]))
    return res


def select(rows, targets, start, topk=10):
    """rows: [(d, cnt, mask, residues)] -> 씨앗 목록 [[d, cnt, mask, score]]"""
    n = len(targets)
    tset = set(targets) | set(start)
    # 같은 지지 집합에서는 가장 큰 d
    bymask = {}
    for d, cnt, mask, res in rows:
        if d in tset:
            continue
        cur = bymask.get(mask)
        if cur is None or d > cur[0]:
            bymask[mask] = (d, cnt, mask)
    cands = []
    for d, cnt, mask in bymask.values():
        lam = n * 257.0 / d
        cands.append(((cnt - 1 - lam) * d.bit_length(), d, cnt, mask))
    cands.sort(reverse=True)
    picked = []
    for sc, d, cnt, mask in cands:
        red = False
        for _, d2, _, m2 in picked:
            if mask & ~m2 == 0 and (d % d2 == 0 or d2 % d == 0):
                red = True
                break
            # 이미 고른 것들이 지지 목표를 전부 덮고 새 목표가 하나도 없으면 약한 중복으로 본다
        if red:
            continue
        picked.append((sc, d, cnt, mask))
        if len(picked) >= topk:
            break
    return [[d, cnt, mask, round(sc, 1)] for sc, d, cnt, mask in picked]


def main():
    mode = sys.argv[1]
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    P = load(mode)
    ids = sorted(P)
    chunks = [[(pid, P[pid][1]) for pid in ids[i::procs * 8]] for i in range(procs * 8)]
    t0 = time.time()
    raw = {}
    with ThreadPoolExecutor(procs) as ex:
        for k, res in enumerate(ex.map(scan, chunks)):
            raw.update(res)
            print("chunk", k, "%.0fs" % (time.time() - t0), flush=True)
    out = {}
    for pid in ids:
        sel = select(raw[pid], P[pid][1], P[pid][0])
        if sel:
            out[pid] = sel
    with open(f"{HERE}/cache/hid_{mode}.json", "w") as f:
        json.dump(out, f)
    print("퍼즐 %d개 중 씨앗 있는 퍼즐 %d개, %.0fs" % (len(ids), len(out), time.time() - t0))
    if mode == "practice":
        from collections import Counter
        c = Counter(P[pid][2] for pid in out)
        tot = Counter(v[2] for v in P.values())
        print({k: "%d/%d" % (c[k], tot[k]) for k in tot})
        cov = Counter()
        for pid, sel in out.items():
            m = 0
            for d, cnt, mask, sc in sel:
                m |= mask
            cov[P[pid][2]] += bin(m).count("1")
        print("덮인 목표 수", dict(cov))


if __name__ == "__main__":
    main()
