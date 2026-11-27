import sys, os, re, collections
D = os.path.dirname(os.path.abspath(__file__))
frozen = None
def parse(fn):
    out = []
    for l in open(os.path.join(D, fn)):
        m = re.match(r"(\S+) k (\d+) seed (\d+) frozen (\d+) start (\S+) end (\S+)", l)
        if m: out.append((m[1], int(m[2]), int(m[3]), int(m[4]), None if m[5]=="None" else int(m[5]), None if m[6]=="None" else int(m[6])))
    return out
def summ(rows, label):
    by = collections.defaultdict(list); fz = {}
    for p, k, s, f, st, e in rows:
        if e is not None: by[p].append(e)
        fz[p] = f
    w = sum(1 for p in by if min(by[p]) < fz[p]); g = sum(fz[p] - min(by[p]) for p in by if min(by[p]) < fz[p])
    n = sum(len(v) for v in by.values())
    print(f"{label}: 퍼즐 {len(by)} 실행 {n} 짧아진 퍼즐 {w} 줄어든 합 {g}")
if __name__ == "__main__":
    spl = []; ctl = []
    for fn in sys.argv[1:]:
        r = parse(fn); (ctl if "ctl" in fn else spl).extend(r)
    for k in (3, 5, 8):
        summ([r for r in spl if r[1] == k], f"바꿔 끼움 k={k}")
    if spl: summ(spl, "바꿔 끼움 전체(k 합침)")
    if ctl: summ(ctl, "대조군")
    if spl: print("바꿔 끼운 시작 평균 증가", sum(r[4] - r[3] for r in spl if r[4]) / len([r for r in spl if r[4]]))
