"""practice 퍼즐에서 family 별로 유도 비용 분포를 본다."""
import sys, csv, json, time
from collections import defaultdict, Counter
from multiprocessing import Pool
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
import engine3 as E
CFG = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
def run(row):
    st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
    eng = E.Engine(st, tg, lim, cfg=CFG, deadline=time.time() + 4)
    hist = Counter()
    orig = eng.apply
    def apply(steps, tag=None):
        n = orig(steps, tag)
        hist[(tag, n)] += 1
        return n
    eng.apply = apply
    t0 = time.time()
    eng.solve()
    return row["family"], hist, len(eng.steps), time.time() - t0
if __name__ == "__main__":
    with open(ROOT + "/data/practice_puzzles.csv") as f:
        rows = list(csv.DictReader(f))
    with Pool(5) as p:
        res = p.map(run, rows, chunksize=1)
    agg = defaultdict(Counter); tot = Counter(); tm = Counter()
    for fam, h, n, dt in res:
        agg[fam].update(h); tot[fam] += n; tm[fam] += dt
    for fam in agg:
        print(fam, "총", tot[fam], "시간 %.0fs" % tm[fam])
        bycost = Counter()
        for (tag, n), c in agg[fam].items(): bycost[n] += c
        print("   비용별 목표 수:", sorted(bycost.items()))
        bytag = defaultdict(Counter)
        for (tag, n), c in agg[fam].items(): bytag[tag][n] += c
        for tag, cs in bytag.items(): print("   ", tag, sorted(cs.items()))
