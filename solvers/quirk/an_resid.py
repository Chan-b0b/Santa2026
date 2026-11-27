import sys,json,collections,math,random
sys.path.insert(0,'core');sys.path.insert(0,'solvers/quirk')
from verify import load_puzzles
import decode2
P=load_puzzles('data/puzzles.csv')
C=json.load(open(sys.argv[1]))
Q={}
for f in ('solvers/quirk/bases3f.json','solvers/quirk/bases6.json','solvers/relate/bases_export.json'):
    for k,v in json.load(open(f)).items(): Q.setdefault(k,[]).extend(v['bases'])
random.seed(1)
def mods(t,a):
    r=t%a; return min(r,a-r)
hits=collections.Counter(); tot=collections.Counter()
thr=[1/4096,1/1024,1/256,1/64]
for pid,B in Q.items():
    c,md=C[pid]
    if c not in('struct','mixed'): continue
    pz=P[pid]; B=list(dict.fromkeys(b for b in B if b>=4096))
    if not B: continue
    T=sorted(t for t in set(pz.targets)-set(pz.start) if t>=1<<24)
    cov=decode2.explain(T,B)
    # hubs products
    H=sorted(set(a*b for i,a in enumerate(B) for b in B[i:]))
    for t in T:
        rand=(c=='mixed' and len(str(t))==md)
        grp='ex' if t in cov else ('rand' if rand else 'un')
        for kind,cand in (('base',B),('hub',[h for h in H if h<t//4])):
            for src in ('real','ctrl'):
                tt=t if src=='real' else random.randrange(t//2+1,t*2)
                if not cand: continue
                best=min(mods(tt,a)/a for a in cand)
                tot[(grp,kind,src)]+=1
                for i,th in enumerate(thr):
                    if best<=th: hits[(grp,kind,src,i)]+=1
for grp in ('ex','un','rand'):
    for kind in ('base','hub'):
        for src in ('real','ctrl'):
            n=tot[(grp,kind,src)]
            if n: print(grp,kind,src,n,' '.join('%.4f'%(hits[(grp,kind,src,i)]/n) for i in range(len(thr))))
