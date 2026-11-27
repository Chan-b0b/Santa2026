import json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(D, "diag0.json"))); ids = json.load(open(os.path.join(D, "pick20.json")))
print("퍼즐 | " + " | ".join(f"k={k}: 위치/남김/최적" for k in (1,3,5,8)))
for i, p in enumerate(ids):
    print(p, "|", " | ".join("%d/%d/%d" % (d[f"{p}:{k}"]["pos"], d[f"{p}:{k}"]["kept"], d[f"{p}:{k}"]["opt"]) for k in (1,3,5,8)))
for name, sl in (("48-55", ids[:10]), ("56+", ids[10:]), ("전체", ids)):
    print(name, " ".join("k=%d %.1f/%.1f/%.1f" % (k, *[sum(d[f"{p}:{k}"][f]/len(sl) for p in sl) for f in ("pos","kept","opt")]) for k in (1,3,5,8)))
