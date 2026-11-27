import sys,json,collections,math,random
sys.path.insert(0,'core')
from verify import load_puzzles
P=load_puzzles('data/puzzles.csv'); PR=load_puzzles('data/practice_puzzles.csv')
C=json.load(open(sys.argv[1]))
def mods(t,a):
    r=t%a; return min(r,a-r)
# 1. residues mod start values (independent + mixed random half)
for grp in ('indep','mixedrand'):
    obs=collections.Counter(); exp=collections.Counter(); n=0
    ratios=[]
    for pid,pz in P.items():
        c,md=C[pid]
        if grp=='indep' and c!='indep': continue
        if grp=='mixedrand' and c!='mixed': continue
        T=[t for t in pz.targets if (c=='indep' or len(str(t))==md)]
        S=[s for s in pz.start if s>=3]
        ratios.append(pz.limit/max(pz.targets))
        for t in T:
            for s in S:
                n+=1
                r=mods(t,s)
                for th in (0,2,10):
                    if r<=th: obs[th]+=1
                    exp[th]+=min(1,(2*th+1)/s)
    print(grp,'pairs',n,' '.join('r<=%d obs %d exp %.1f'%(th,obs[th],exp[th]) for th in (0,2,10)))
    ratios.sort(); print('  lim/maxt quantiles',[round(ratios[int(q*(len(ratios)-1))],3) for q in (0,0.1,0.25,0.5,0.75,0.9,1)])
# 2. sorted gaps: normalized spacings vs exponential
for grp in ('indep',):
    sp=[]
    for pid,pz in P.items():
        if C[pid][0]!='indep': continue
        T=sorted(set(pz.targets)); d=len(str(T[0])); lo=10**(d-1); hi=10**d
        n=len(T); g=[(T[i+1]-T[i])*(n+1)/(hi-lo) for i in range(n-1)]
        sp+=g
    sp.sort(); print('indep normalized gaps quantiles (exp(1): .105 .288 .693 1.386 2.30)',[round(sp[int(q*(len(sp)-1))],3) for q in (0.1,0.25,0.5,0.75,0.9)], 'min',sp[:5])
# 3. low digits / mod 10^k patterns
c10=collections.Counter(); c1000=collections.Counter(); n=0
for pid,pz in P.items():
    if C[pid][0]!='indep': continue
    for t in pz.targets: c10[t%10]+=1; n+=1; c1000[t%1000]+=1
print('last digit',[c10[d] for d in range(10)],'n',n,' max count of t%1000',c1000.most_common(3))
# 4. gcd among targets in indep puzzle
big=0;tot=0
for pid,pz in P.items():
    if C[pid][0]!='indep': continue
    T=pz.targets
    for i in range(len(T)):
        for j in range(i):
            tot+=1
            if math.gcd(T[i],T[j])>=1000: big+=1
print('indep pair gcd>=1000',big,'of',tot,'expected ~',round(tot*0.6/1000,1))
