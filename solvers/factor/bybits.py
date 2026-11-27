"""practice 에서 목표 크기(비트)별 평균 유도 비용."""
import sys, csv, json, time
from collections import defaultdict
from multiprocessing import Pool
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
import engine3 as E
CFG = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
def run(row):
    st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
    eng = E.Engine(st, tg, lim, cfg=CFG, deadline=time.time() + 6)
    rec = []
    orig = eng.apply
    def apply(steps, tag=None):
        tgt = [s[0] for s in steps if s[0] in eng.tset and s[0] not in eng.pool]
        n = orig(steps, tag)
        b = max(tgt).bit_length() if tgt else 0
        rec.append((b, n, tag, len(tgt)))
        return n
    eng.apply = apply
    eng.solve()
    return row["family"], rec
if __name__ == "__main__":
    with open(ROOT + "/data/practice_puzzles.csv") as f:
        rows = list(csv.DictReader(f))
    with Pool(5) as p:
        res = p.map(run, rows, chunksize=1)
    agg = defaultdict(lambda: [0, 0])
    for fam, rec in res:
        for b, n, tag, k in rec:
            key = (fam, min(b // 8, 7))
            agg[key][0] += n; agg[key][1] += max(k, 1) if tag != "seed" else 0
    for fam in ("multiplicative", "shared", "mixed", "independent"):
        print(fam, "  ".join("%d-%d비트: %d명령/%d목표=%.1f" % (b * 8, b * 8 + 7, agg[(fam, b)][0], agg[(fam, b)][1], agg[(fam, b)][0] / max(agg[(fam, b)][1], 1)) for b in range(8) if (fam, b) in agg))
