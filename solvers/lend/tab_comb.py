import json, sys
d = json.load(open(sys.argv[1])); ids = sorted({k.split(":")[0] for k in d}); seeds = sorted({k.split(":")[1] for k in d})
tc = ts = tb = tsp = 0; wins = 0
for p in ids:
    c = [d[f"{p}:{s}:ctl"]["end"] for s in seeds]; sp = [d[f"{p}:{s}:spl"]["end"] for s in seeds]; st = d[f"{p}:{seeds[0]}:spl"]["start"]
    b = d[f"{p}:{seeds[0]}:ctl"]["best"]
    print(p, "best", b, "ctl", c, "spl시작", st, "spl", sp)
    tb += b; tc += sum(c)/len(c); ts += sum(sp)/len(sp); tsp += st
print("best 합", tb, "대조군 평균", round(tc,1), "초반교체 평균", round(ts,1), "교체 시작 합", tsp)
