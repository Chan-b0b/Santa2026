import sys,json,collections,math,random
sys.path.insert(0,'core');sys.path.insert(0,'solvers/quirk')
from verify import load_puzzles, read_submission
import decode2
P=load_puzzles('data/puzzles.csv')
best={p:json.loads(c) for p,c in read_submission('best/best.csv').items()}
Q={}
for f in ('solvers/quirk/bases3f.json','solvers/quirk/bases6.json','solvers/relate/bases_export.json'):
    for k,v in json.load(open(f)).items(): Q.setdefault(k,[]).extend(v['bases'])
def vals(pz,prog):
    reg=list(pz.start)+[None]*(pz.registers-len(pz.start)); out=set(pz.start)
    for op,a,b,d in prog:
        x,y=reg[a],reg[b]; v=x+y if op=='+' else x-y if op=='-' else x*y if op=='*' else x//y
        reg[d]=v; out.add(v)
    return out
KR={}
for pid,B in Q.items():
    B=list(dict.fromkeys(b for b in B if b>=512)); T=sorted(t for t in set(P[pid].targets) if t>=1<<16)
    cov=decode2.explain(T,B)
    if len(cov)<8: continue
    KR[pid]=[v for (k,a,b,r) in cov.values() for v in (k,abs(r)) if v>=200]
def score(vs):
    bestm=None
    for m in range(200,20000):
        c=sum(1 for v in vs if v>=m//2 and min(v%m,m-v%m)<=4)
        if bestm is None or c>bestm[0]: bestm=(c,m)
    return bestm
allv=[v for vs in KR.values() for v in vs]
random.seed(3)
real=[];null=[]
pids=sorted(KR)
for pid in pids:
    vs=KR[pid]; c,m=score(vs)
    nv=random.sample(allv,len(vs)); cn,mn=score(nv)
    has = m in vals(P[pid],best[pid])
    real.append((c,m,len(vs),pid,has)); null.append(cn)
real.sort(reverse=True)
print('real top',real[:12])
print('mean real %.2f null %.2f'%(sum(r[0] for r in real)/len(real),sum(null)/len(null)))
print('null dist',sorted(null)[-10:])
sel={}
for c,m,n,pid,has in real:
    if c>=9 and not has:
        B=list(dict.fromkeys(b for b in Q[pid] if b>=512))
        T=sorted(t for t in set(P[pid].targets) if t>=1<<16)
        cov=decode2.explain(T,B); used=collections.Counter()
        for k,a,b,r in cov.values(): used[a]+=1; used[b]+=1
        B=[b for b in sorted(B,key=lambda b:-used[b]) if used[b]>=2][:7]+[m]
        sel[pid]={'bases':B,'cov':{},'nt':len(cov),'m':m,'hits':c}
print('selected',len(sel),[(p,v['m'],v['hits']) for p,v in sel.items()])
json.dump(sel,open('solvers/quirk/bases_smallm.json','w'))
