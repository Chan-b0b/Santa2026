"""모든 목표값의 소인수분해를 미리 구해 cache/factors_<set>.json 에 저장한다 (값 문자열 -> [[p, e], ...])."""
import sys, csv, json, time
from multiprocessing import Pool
sys.path.insert(0, "/home/maverick/Santa2026/solvers/factor")
from nt import factor

ROOT = "/home/maverick/Santa2026"

def fac(n):
    return n, sorted(factor(n).items())

def main():
    for name, path in (("practice", ROOT + "/data/practice_puzzles.csv"), ("scored", ROOT + "/data/puzzles.csv")):
        vals = set()
        with open(path) as f:
            for r in csv.DictReader(f):
                vals.update(json.loads(r["targets"]))
        vals = sorted(vals)
        t0 = time.time()
        with Pool(5) as p:
            res = p.map(fac, vals, chunksize=64)
        with open(f"{ROOT}/solvers/factor/cache/factors_{name}.json", "w") as f:
            json.dump({str(n): fs for n, fs in res}, f)
        print(name, len(vals), "values, %.1fs" % (time.time() - t0))

if __name__ == "__main__":
    main()
