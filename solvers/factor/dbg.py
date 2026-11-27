import sys, csv, json, time
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
import engine3 as E
from multiprocessing import Pool
def run(row):
    st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
    eng = E.Engine(st, tg, lim, deadline=time.time() + 6)
    t0 = time.time()
    eng.solve()
    return row["id"], row["family"], st, len(tg), max(tg).bit_length(), len(eng.steps), eng.stats, time.time() - t0
if __name__ == "__main__":
    with open(ROOT + "/data/practice_puzzles.csv") as f:
        rows = list(csv.DictReader(f))
    with Pool(5) as p:
        res = p.map(run, rows, chunksize=1)
    for pid, fam, st, n, bits, ln, stats, dt in res:
        if stats.get("binary") or dt > 5:
            print(pid, fam, st, "n", n, "bits", bits, "len", ln, "t %.1f" % dt, {k: v for k, v in stats.items() if k in ("binary", "seed", "fallback", "fallback#")})
