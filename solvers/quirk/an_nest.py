import sys,json,collections,math,random
sys.path.insert(0,'core');sys.path.insert(0,'solvers/quirk')
from verify import load_puzzles
import decode2
P=load_puzzles('data/puzzles.csv')
Q={}
for f in ('solvers/quirk/bases3f.json','solvers/quirk/bases6.json','solvers/relate/bases_export.json'):
    for k,v in json.load(open(f)).items(): Q.setdefault(k,[]).extend(v['bases'])
obs=0; exp=0.0; n=0; shared=collections.Counter(); tot_v=0
rabs=[]
for pid,B in Q.items():
    B=list(dict.fromkeys(b for b in B if b>=512)); T=sorted(t for t in set(P[pid].targets) if t>=1<<16)
    cov=decode2.explain(T,B)
    vs=collections.Counter()
    for t,(k,a,b,r) in cov.items():
        rabs.append(abs(r))
        if k>=16 and abs(r)>=4*k:
            n+=1
            c=round(r/k); r2=r-k*c
            if abs(r2)<=16: obs+=1
            exp+=min(1,33/k)
            vs[(a,b,c)]+=1
    for key,m in vs.items():
        tot_v+=1
        if m>=2: shared[m]+=1
print('targets with k>=16,|r|>=4k:',n,' |r - k*round(r/k)|<=16: obs',obs,'exp %.1f'%exp)
print('distinct v=h+c',tot_v,'shared by >=2 targets',dict(shared))
rabs.sort(); print('|r| quantiles',[rabs[int(q*(len(rabs)-1))] for q in (0.1,0.25,0.5,0.75,0.9,0.95)])
