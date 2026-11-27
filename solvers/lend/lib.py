"""lend 공용 함수: 값 그래프, 초반부 추출, 레지스터 배정, 엔진 실행."""
import sys, os, json, subprocess, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "core"))
from verify import load_puzzles, read_submission, check_program, Puzzle, write_submission
BIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elf_lns")
P = load_puzzles(os.path.join(ROOT, "data", "puzzles.csv"))
BEST = {k: json.loads(v) for k, v in read_submission(os.path.join(ROOT, "best", "best.csv")).items()}
OPF = {"+": lambda x, y: x + y, "-": lambda x, y: x - y, "*": lambda x, y: x * y, "/": lambda x, y: x // y}

def to_nodes(pz, prog):
    """프로그램 -> [(op, a_node, b_node, value)], 시작값은 노드 0..ns-1. 레지스터 추적."""
    vals = list(pz.start); reg = {i: i for i in range(len(pz.start))}
    nodes = []
    for op, a, b, d in prog:
        x, y = reg[a], reg[b]
        v = OPF[op](vals[x], vals[y])
        vals.append(v); nodes.append((op, x, y, v)); reg[d] = len(vals) - 1
    return vals, nodes

def target_order(pz, prog):
    """목표값이 처음 나오는 순서: [(명령번호(1부터), 값)]"""
    vals, nodes = to_nodes(pz, prog)
    ns = len(pz.start); T = set(pz.targets) - set(pz.start); out = []; seen = set(pz.start)
    for i, (op, a, b, v) in enumerate(nodes):
        if v in T and v not in seen: out.append((i + 1, v))
        seen.add(v)
    return out

def closure_prog(pz, prog, tvals):
    """tvals 를 만드는 데 필요한 명령만 남긴 프로그램 (원래 레지스터 그대로)."""
    ns = len(pz.start)
    vals, nodes = to_nodes(pz, prog)
    # 값 -> 처음 만든 노드
    first = {}
    for i, (op, a, b, v) in enumerate(nodes): first.setdefault(v, ns + i)
    need = set(first[v] for v in tvals if v in first)
    for i in range(len(nodes) - 1, -1, -1):
        if ns + i in need:
            need.add(nodes[i][1]); need.add(nodes[i][2])
    return [prog[i] for i in range(len(prog)) if ns + i in need]

def allocate(pz, seq, nreg=None):
    """seq = [(op, valA, valB)] 값 기준 순서. 값 중복은 건너뛴다. 레지스터 배정해 프로그램 반환, 실패 시 None."""
    nreg = nreg or pz.registers
    ns = len(pz.start)
    # 값 계산과 중복 제거
    have = set(pz.start); out = []
    for op, x, y in seq:
        v = OPF[op](x, y)
        if v in have: continue
        have.add(v); out.append((op, x, y, v))
    last = {}
    for i, (op, x, y, v) in enumerate(out):
        last[x] = i; last[y] = i
    reg = {}  # value -> register
    free = list(range(nreg - 1, ns - 1, -1))
    for i, s in enumerate(pz.start):
        if s in last: reg[s] = i
        else: free.append(i)
    prog = []
    for i, (op, x, y, v) in enumerate(out):
        if x not in reg or y not in reg: return None
        rx, ry = reg[x], reg[y]
        for u in {x, y}:
            if last.get(u, -1) <= i and u in reg:
                free.append(reg[u]); del reg[u]
        # 시작값이 마지막 사용 뒤에도 자리를 지키는 것은 허용 (이미 풀림)
        if not free: return None
        d = free.pop()
        prog.append([op, rx, ry, d])
        if v in last and last[v] > i: reg[v] = d
        else: free.append(d)
    return prog

def seq_of(pz, prog):
    vals, nodes = to_nodes(pz, prog)
    return [(op, vals[a], vals[b]) for op, a, b, v in nodes]

def run_engine(pz, prog, secs, seed=1, opts=None, targets=None):
    """pz 는 Puzzle(필요하면 start/targets 바꾼 것). 반환 (프로그램 | None, 로그)."""
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="lend_", dir=os.environ.get("TMPDIR"))
    with os.fdopen(fd, "w") as f:
        f.write(f"{pz.limit} {pz.registers} {len(pz.start)} {len(pz.targets)} {len(prog)}\n")
        f.write(" ".join(map(str, pz.start)) + "\n" + " ".join(map(str, pz.targets)) + "\n")
        for op, a, b, d in prog: f.write(f"{op} {a} {b} {d}\n")
    try:
        r = subprocess.run([BIN, path, str(secs), f"seed={seed}"] + (opts or "peq=0.5 pelim=0.05 pruin=0.8 ruink=12 aware=0.5 repair=2000 beamw=32").split(), capture_output=True, text=True, timeout=secs * 3 + 120)
    finally:
        os.unlink(path)
    if r.returncode: return None, f"rc {r.returncode} {r.stderr[-200:]}"
    lines = r.stdout.split("\n"); n = int(lines[0].split()[1])
    new = [[l.split()[0]] + [int(y) for y in l.split()[1:]] for l in lines[1:1 + n]]
    if check_program(pz, new) is not None: return None, "invalid " + check_program(pz, new)
    return new, r.stderr.strip()[-120:]

def sub_puzzle(pz, targets=None, extra_start=()):
    return Puzzle(pz.id, tuple(pz.start) + tuple(extra_start), tuple(targets if targets is not None else pz.targets), pz.limit, pz.registers)

def splice(pz, prefix_prog, prefix_pz, orig_prog, pz_orig=None):
    pz_orig = pz_orig or pz
    """prefix_prog(초반부, prefix_pz 의 유효 프로그램) 뒤에 원래 프로그램에서 필요한 명령을 이어 붙여 레지스터를 배정한다."""
    pvals, pnodes = to_nodes(prefix_pz, prefix_prog)
    avail = set(pz.start) | set(pvals)
    vals, nodes = to_nodes(pz_orig, orig_prog)
    ns = len(pz_orig.start)
    first = {}
    for i, (op, a, b, v) in enumerate(nodes): first.setdefault(v, ns + i)
    stack = [first[t] for t in pz.targets if t not in avail and t in first]
    req = set()
    while stack:
        n = stack.pop()
        if n in req or n < ns: continue
        req.add(n)
        for o in (nodes[n - ns][1], nodes[n - ns][2]):
            if vals[o] not in avail: stack.append(first[vals[o]])
    seq = seq_of(prefix_pz, prefix_prog) + [(nodes[n - ns][0], vals[nodes[n - ns][1]], vals[nodes[n - ns][2]]) for n in sorted(req)]
    return allocate(pz, seq)
