import sys
sys.path.insert(0, "/home/maverick/Santa2026/core"); sys.path.insert(0, "/home/maverick/Santa2026/solvers/chain")
from verify import load_puzzles, check_program
import chain
P = load_puzzles("/home/maverick/Santa2026/data/practice_puzzles.csv")
P.update(load_puzzles("/home/maverick/Santa2026/data/puzzles.csv"))
def fmt(x): return str(x) if x < 10**7 else f"<{x.bit_length()}b:{x}>"
def show(pid, **kw):
    p = P[pid]
    m = chain.Machine(p, chain.Params(**kw))
    m.build_digits(m.pr.digits)
    print(pid, "start", p.start, "limit", p.limit, p.limit.bit_length(), "ntargets", len(p.targets))
    for t in sorted(p.targets):
        if t in m.produced: print(t, "already"); continue
        steps = m.find_chain(t)
        n0 = len(m.prog)
        m.run_steps(steps); m.trim()
        print(f"{t} ({t.bit_length()}b) cost {len(m.prog)-n0}: ", " ".join(f"{op}({fmt(x)},{fmt(y)})" for op,x,y in steps))
    print("total", len(m.prog), "lb", p.lower_bound)
    print(sorted(m.loc))
if __name__ == "__main__":
    show(sys.argv[1], **eval(sys.argv[2]) if len(sys.argv) > 2 else {})
