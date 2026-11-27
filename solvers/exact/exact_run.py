#!/usr/bin/env python3
"""exact 구동기: best 프로그램을 값 그래프로 바꿔 exact(C++)를 돌리고, 적중을 적용해 results/exact.csv 에 쓴다."""
import sys, os, json, csv, subprocess, time, argparse, fcntl
from multiprocessing import Pool
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "core"))
from verify import load_puzzles, check_program, write_submission, read_submission
csv.field_size_limit(1 << 30)
EXE = os.path.join(ROOT, "solvers/exact/exact")
OUT = os.path.join(ROOT, "results/exact.csv")
PUZ = load_puzzles(os.path.join(ROOT, "data/puzzles.csv"))
FAM = json.load(open(os.path.join(ROOT, "solvers/quirk/family_guess.json")))

def best_prog(pid):
    cells = read_submission(os.path.join(ROOT, "best/best.csv"))
    return json.loads(cells[pid])

def ap(op, x, y):
    if op == '+': return x + y
    if op == '-': return x - y
    if op == '*': return x * y
    return x // y

class G:
    """값 그래프. nodes: id -> [op,a,b,val]; 시작값은 id 0..ns-1 (op None). req: 필수 노드 id 집합. order: 노드 id 목록(위상)"""
    pass

def build(p, prog):
    g = G(); ns = len(p.start); g.ns = ns; g.L = p.limit
    nodes = {}; order = []
    byval = {}
    for i, v in enumerate(p.start):
        nodes[i] = [None, -1, -1, v]; byval.setdefault(v, i)
    reg = list(p.start) + [None] * (p.registers - ns)
    regnode = list(range(ns)) + [None] * (p.registers - ns)
    nid = ns
    for op, a, b, d in prog:
        x, y = reg[a], reg[b]; v = ap(op, x, y)
        if v in byval:
            reg[d] = v; regnode[d] = byval[v]; continue
        nodes[nid] = [op, regnode[a], regnode[b], v]; byval[v] = nid
        reg[d] = v; regnode[d] = nid; order.append(nid); nid += 1
    req = set(byval[t] for t in p.targets if t in byval and byval[t] >= ns)
    # 도달 가능한 것만
    live = set(); st = list(req)
    while st:
        u = st.pop()
        if u in live or u < ns: continue
        live.add(u); st.append(nodes[u][1]); st.append(nodes[u][2])
    g.nodes = nodes; g.order = [u for u in order if u in live]; g.req = req; g.next = nid
    g.pos = {u: i for i, u in enumerate(g.order)}
    return g

def users_of(g):
    us = {}
    for u in g.order:
        for w in (g.nodes[u][1], g.nodes[u][2]):
            us.setdefault(w, set()).add(u)
    return us

def cone_of(g, v, us):
    cnt = {w: len(s) for w, s in us.items()}
    cone = {v}; st = [v]
    while st:
        w = st.pop()
        for u in {g.nodes[w][1], g.nodes[w][2]}:
            if u < g.ns or u in g.req or u in cone: continue
            cnt[u] -= 1
            if cnt[u] == 0: cone.add(u); st.append(u)
    return cone

def run_exact(g, K, minc):
    ns = g.ns; idx = {}
    for i in range(ns): idx[i] = i
    for j, u in enumerate(g.order): idx[u] = ns + j
    lines = [f"{g.L} {ns} {len(g.order)}", " ".join(str(g.nodes[i][3]) for i in range(ns))]
    for u in g.order:
        op, a, b, v = g.nodes[u]
        lines.append(f"{op} {idx[a]} {idx[b]} {1 if u in g.req else 0}")
    r = subprocess.run([EXE, str(K), str(minc)], input="\n".join(lines) + "\n", capture_output=True, text=True)
    if r.returncode != 0: raise RuntimeError("exact failed " + r.stderr[:200])
    inv = {ns + j: u for j, u in enumerate(g.order)}
    for i in range(ns): inv[i] = i
    nodes = []; hits = []; times = []
    for ln in r.stdout.splitlines():
        t = ln.split()
        if t[0] == "NODE": nodes.append((inv[int(t[1])], int(t[2])))
        elif t[0] == "HIT":
            v, c, k, mask, ns_ = inv[int(t[1])], int(t[2]), int(t[3]), int(t[4]), int(t[5])
            steps = []
            for q in range(ns_):
                op, ra, rb = t[6 + 3 * q], int(t[7 + 3 * q]), int(t[8 + 3 * q])
                steps.append((op, inv[ra] if ra >= 0 else ra, inv[rb] if rb >= 0 else rb))
            hits.append(dict(v=v, c=c, k=k, mask=mask, steps=steps))
        elif t[0] == "T": times.append((inv[int(t[1])], float(t[3])))
    return nodes, hits, times

def apply_hit(g, h, us):
    """새 그래프(G)를 돌려준다."""
    v = h["v"]; cone = cone_of(g, v, us)
    n = G(); n.ns = g.ns; n.L = g.L; n.req = set(g.req)
    n.nodes = {u: list(x) for u, x in g.nodes.items() if u not in cone}
    nxt = g.next; temps = []; val = {}
    for u in n.nodes: val[u] = n.nodes[u][3]
    def ref(r): return r if r >= 0 else temps[-1 - r]
    for j, (op, ra, rb) in enumerate(h["steps"]):
        a, b = ref(ra), ref(rb)
        x, y = val[a], val[b]
        r = ap(op, x, y)
        if j == len(h["steps"]) - 1:
            nid = v; assert r == g.nodes[v][3], "target value mismatch"
        else:
            nid = nxt; nxt += 1
        n.nodes[nid] = [op, a, b, r]; val[nid] = r; temps.append(nid)
    n.next = nxt
    # 위상 우선순위: 옛 노드는 옛 위치, 새 노드는 v 위치 바로 앞
    pri = {}
    for u in g.order:
        if u in n.nodes and u != v: pri[u] = g.pos[u]
    base = g.pos[v]
    for j, t in enumerate(temps): pri[t] = base - 0.5 + 0.01 * j if t != v else base
    n.pri = pri
    n.order = sorted(pri, key=lambda u: pri[u])
    return n

def schedule(g, p, mode):
    """emission 순서를 만들고 레지스터를 배정. 실패하면 None."""
    nodes = g.nodes; ns = g.ns
    emitted = set(); seq = []
    sys.setrecursionlimit(10000)
    def emit(u):
        if u < ns or u in emitted: return
        a, b = nodes[u][1], nodes[u][2]
        if mode & 2: 
            # 깊은 쪽 먼저
            pass
        for w in ((a, b) if not (mode & 2) else (b, a)):
            emit(w)
        emitted.add(u); seq.append(u)
    roots = g.order if mode & 1 == 0 else sorted(g.req, key=lambda u: g.pri[u] if hasattr(g, "pri") else g.pos[u])
    if mode & 1 == 0:
        for u in sorted(g.nodes, key=lambda u: g.pri[u] if u >= ns else -1):
            if u >= ns: emit(u)
    else:
        for u in roots: emit(u)
    # 레지스터
    last = {}
    for i, u in enumerate(seq):
        last[nodes[u][1]] = i; last[nodes[u][2]] = i
    R = p.registers
    free = list(range(R)); regof = {}
    for i in range(ns):
        regof[i] = i; free.remove(i)
    prog = []
    for i in range(ns):
        if i not in last: free.append(i); free.sort()
    for i, u in enumerate(seq):
        op, a, b, v = nodes[u]
        ra, rb = regof[a], regof[b]
        rel = []
        for w in {a, b}:
            if last[w] == i: rel.append(regof[w])
        free.extend(rel); free.sort()
        if not free: return None
        d = free.pop(0); regof[u] = d
        prog.append([op, ra, rb, d])
        if u not in last: free.append(d); free.sort()
    return prog

def try_schedule(g, p):
    for mode in (0, 1, 2, 3):
        prog = schedule(g, p, mode)
        if prog is not None and check_program(p, prog) is None:
            return prog
    return None

def process(args):
    pid, K, minc, tmax = args
    p = PUZ[pid]; prog = best_prog(pid); orig = len(prog)
    g = build(p, prog)
    rec = dict(id=pid, fam=FAM[pid][0], best=orig, live=len(g.order), nodes=[], hits=[], times=[], fit=0, nofit=0, steps=0)
    t0 = time.time()
    first = True; cur = g; curprog = prog
    while True:
        if len(cur.order) >= 1 and time.time() - t0 < tmax:
            nodes, hits, times = run_exact(cur, K, minc)
        else:
            break
        us = users_of(cur)
        hits.sort(key=lambda h: -(h["c"] - h["k"]))
        applied = None
        for h in hits:
            if h["k"] >= h["c"]: continue
            ng = apply_hit(cur, h, us)
            sp = try_schedule(ng, p)
            h["fit"] = sp is not None
            if first:
                rec["hits"].append(dict(v=h["v"], c=h["c"], k=h["k"], mask=h["mask"], div=any(s[0] == '/' for s in h["steps"]), fit=h["fit"]))
            if sp is not None and applied is None:
                applied = (ng, sp, h)
                if not first: break
        if first:
            rec["nodes"] = [c for _, c in nodes]; rec["times"] = [t for _, t in times]
            rec["first_time"] = time.time() - t0
        first = False
        if applied is None: break
        cur = build(p, applied[1]); curprog = applied[1]
        rec["steps"] += 1
    rec["final"] = len(curprog)
    rec["prog"] = curprog if len(curprog) < orig else None
    rec["time"] = time.time() - t0
    return rec

if __name__ == "__main__":
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--fam", default="indep"); ap_.add_argument("--K", type=int, default=3)
    ap_.add_argument("--minc", type=int, default=2); ap_.add_argument("--procs", type=int, default=6)
    ap_.add_argument("--ids", default=""); ap_.add_argument("--tag", default="k3")
    ap_.add_argument("--skip", type=int, default=0); ap_.add_argument("--tmax", type=float, default=600); ap_.add_argument("--first", type=int, default=0)
    a = ap_.parse_args()
    ids = a.ids.split(",") if a.ids else [i for i in sorted(PUZ) if FAM[i][0] in a.fam.split(",")]
    ids = ids[a.skip:]
    if a.first: ids = ids[:a.first]
    log = open(os.path.join(ROOT, f"solvers/exact/stats_{a.tag}.jsonl"), "a")
    done = 0; saved = 0
    with Pool(a.procs) as pool:
        for rec in pool.imap_unordered(process, [(i, a.K, a.minc, a.tmax) for i in ids]):
            done += 1
            prog = rec.pop("prog")
            log.write(json.dumps(rec) + "\n"); log.flush()
            if prog is not None:
                cells = read_submission(OUT) if os.path.exists(OUT) else {}
                progs = {k: json.loads(v) for k, v in cells.items()}
                bp = best_prog(rec["id"])
                if len(prog) < len(bp) and len(prog) < len(progs.get(rec["id"], [0] * 10**6)):
                    progs[rec["id"]] = prog; write_submission(OUT, progs); saved += len(bp) - len(prog)
            print(f"[{done}/{len(ids)}] {rec['id']} {rec['fam']} best={rec['best']} final={rec['final']} hits={len(rec['hits'])} steps={rec['steps']} t={rec['time']:.1f}s saved_total={saved}", flush=True)
