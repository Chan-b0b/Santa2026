import json,sys,statistics as st,collections
f=sys.argv[1] if len(sys.argv)>1 else "/home/maverick/Santa2026/solvers/fresh/runs1.jsonl"
R=[json.loads(l) for l in open(f)]
R=[r for r in R if r["out"] is not None]
big=set(open('/home/maverick/Santa2026/solvers/lns/big48.txt').read().replace('\n',',').split(','))
print("runs",len(R),"wins",sum(r["out"]<r["best"] for r in R),"ties",sum(r["out"]==r["best"] for r in R))
byp=collections.defaultdict(list)
for r in R: byp[r["pid"]].append(r["out"]-r["best"])
print("puzzles won",sum(min(v)<0 for v in byp.values()),"gain sum",sum(max(0,r["best"]-r["out"]) for r in R))
print("per-puzzle min/median of (out-best):")
for p,v in sorted(byp.items()): print(" ",p,"big" if p in big else "   ",R[[r['pid'] for r in R].index(p)]["best"],min(v),st.median(v),len(v))
mins=[min(v) for v in byp.values()]
print("min<=+2:",sum(m<=2 for m in mins),"min>=+5:",sum(m>=5 for m in mins),"of",len(mins))
bys=collections.defaultdict(list)
for r in R: bys[r["solver"]].append(r)
for s,v in sorted(bys.items()):
    d=[r["out"]-r["best"] for r in v]; 
    pm=collections.defaultdict(lambda:99)
    for r in v: pm[r["pid"]]=min(pm[r["pid"]],r["out"]-r["best"])
    print(s,"n",len(v),"wins",sum(x<0 for x in d),"mean",round(st.mean(d),1),"median",st.median(d),"mean puzzle-min",round(st.mean(pm.values()),1),"raw-best mean ratio",round(st.mean(r["raw"]/r["best"] for r in v),3))
for s in sorted({(r["solver"],r["cfg"]) for r in R}):
    v=[r["out"]-r["best"] for r in R if (r["solver"],r["cfg"])==s]; print(" ",s,round(st.mean(v),1),min(v))
import math
def corr(a,b):
    ma,mb=st.mean(a),st.mean(b); return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
print("corr raw vs out (all, raw/best vs out/best):",round(corr([r["raw"]/r["best"] for r in R],[r["out"]/r["best"] for r in R]),3))
cs=[]
for p in byp:
    v=[r for r in R if r["pid"]==p]
    if len(v)>3 and len({r['raw'] for r in v})>1: cs.append(corr([r["raw"] for r in v],[r["out"] for r in v]))
print("within-puzzle corr mean",round(st.mean(cs),3))
