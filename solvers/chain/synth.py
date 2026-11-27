import sys, random, time
sys.path.insert(0, "/home/maverick/Santa2026/core"); sys.path.insert(0, "/home/maverick/Santa2026/solvers/chain")
from verify import Puzzle
import chain
def test(T, gen, W=32, n=40, seed=1, npool=46):
    rnd = random.Random(seed)
    tot = 0; t0 = time.time()
    hist = {}
    for it in range(n):
        vals = set()
        while len(vals) < npool: vals.add(gen(rnd))
        t = rnd.randrange(2**(T-1), 2**T)
        pz = Puzzle("x", tuple(sorted(vals)), (t,), int(2**T * 1.3), 48)
        m = chain.Machine(pz, chain.Params(W=W, digits=0))
        steps = m.find_chain(t)
        c = len(steps) if steps is not None else 99
        tot += c; hist[c] = hist.get(c, 0) + 1
    return tot / n, sorted(hist.items()), (time.time() - t0) / n
if __name__ == "__main__":
    T = int(sys.argv[1])
    gens = {
      "1..46": None,
      "b10": lambda r: r.randrange(2**9, 2**10),
      "b11": lambda r: r.randrange(2**10, 2**11),
      "b12": lambda r: r.randrange(2**11, 2**12),
      "b13": lambda r: r.randrange(2**12, 2**13),
      "b14": lambda r: r.randrange(2**13, 2**14),
      "b16": lambda r: r.randrange(2**15, 2**16),
      "lu2-12": lambda r: int(2**r.uniform(1, 12)),
      "lu6-13": lambda r: int(2**r.uniform(6, 13)),
      "lu8-14": lambda r: int(2**r.uniform(8, 14)),
      "lu8-16": lambda r: int(2**r.uniform(8, 16)),
      "lu4-20": lambda r: int(2**r.uniform(4, 20)),
      "lu8-24": lambda r: int(2**r.uniform(8, 24)),
      "u4096": lambda r: r.randrange(2, 4096),
      "u16384": lambda r: r.randrange(2, 16384),
    }
    cnt = [0]
    def seq(r):
        cnt[0] += 1; return (cnt[0] % 46) + 1
    gens["1..46"] = seq
    for name, g in gens.items():
        for W in (32, 256):
            print(T, name, W, test(T, g, W=W), flush=True)
