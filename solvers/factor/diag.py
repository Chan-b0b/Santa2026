"""practice 에서 목표별 (family, 비트, 비용, 유도 종류, 풀 크기)를 모아 표로 본다."""
import sys, csv, json, time
from collections import defaultdict, Counter
from multiprocessing import Pool
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core"); sys.path.insert(0, ROOT + "/solvers/factor")
import engine3 as E
CFG = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
def run(row):
    st = json.loads(row["starting_values"]); tg = json.loads(row["targets"]); lim = int(row["value_limit"])
    eng = E.Engine(st, tg, lim, cfg=CFG, deadline=time.time() + 8)
    rec = []
    orig = eng.apply
    def apply(steps, tag=None):
        tgt = [s[0] for s in steps if s[0] in eng.tset and s[0] not in eng.pool]
        P = len(eng.plist)
        n = orig(steps, tag)
        if tgt:
            rec.append((max(tgt).bit_length(), n, tag, P, eng.mode))
        return n
    eng.apply = apply
    eng.solve()
    return row["family"], rec
if __name__ == "__main__":
    with open(ROOT + "/data/practice_puzzles.csv") as f:
        rows = list(csv.DictReader(f))
    with Pool(5) as p:
        res = p.map(run, rows, chunksize=1)
    for fam in ("multiplicative", "shared", "mixed", "independent"):
        print("==", fam)
        tab = defaultdict(Counter); pools = defaultdict(list)
        for f, rec in res:
            if f != fam: continue
            for b, n, tag, P, mode in rec:
                key = min(b // 8, 7)
                tab[key][min(n, 10)] += 1
                pools[key].append(P)
        for key in sorted(tab):
            c = tab[key]; tot = sum(c.values())
            ps = sorted(pools[key])
            print("  %2d-%2d비트 n=%4d 풀크기 중앙 %3d | 비용 분포:" % (key * 8, key * 8 + 7, tot, ps[len(ps) // 2]),
                  " ".join("%d:%d" % (k, c[k]) for k in sorted(c)))
