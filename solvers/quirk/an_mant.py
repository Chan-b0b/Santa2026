import sys,json,collections,math,csv
sys.path.insert(0,'core');sys.path.insert(0,'solvers/quirk')
from verify import load_puzzles
import decode2
P=load_puzzles('data/puzzles.csv')
Q={}
for f in ('solvers/quirk/bases3f.json','solvers/quirk/bases6.json','solvers/relate/bases_export.json'):
    for k,v in json.load(open(f)).items(): Q.setdefault(k,[]).extend(v['bases'])
def mant(t):
    s=str(t); return int(s[0])
def hist(ts):
    c=collections.Counter(mant(t) for t in ts); n=len(ts)
    return n, ' '.join('%.3f'%(c[d]/n) for d in range(1,10))
print('benford', ' '.join('%.3f'%math.log10(1+1/d) for d in range(1,10)))
PR=list(csv.DictReader(open('data/practice_puzzles.csv')))
for fam in ('independent','mixed','shared','multiplicative'):
    ts=[t for p in PR if p['family']==fam for t in json.loads(p['targets']) if t>=1<<16]
    print('practice',fam,*hist(ts))
ex=[];un=[];unp=collections.defaultdict(list)
for pid,B in Q.items():
    B=list(dict.fromkeys(b for b in B if b>=512)); T=sorted(t for t in set(P[pid].targets) if t>=1<<16)
    cov=decode2.explain(T,B)
    if len(cov)<3: continue
    for t in T:
        (ex if t in cov else un).append(t)
        if t not in cov: unp[pid].append(t)
print('scored explained',*hist(ex))
print('scored unexplained',*hist(un))
# unexplained in puzzles: are they in a decade-uniform pattern? check min/max decade per puzzle
json.dump({k:v for k,v in unp.items()},open('/tmp/claude-1000/-home-maverick-Santa2026/b02d270e-8761-4966-9c87-d8e85794d8cf/scratchpad/unexpl.json','w'))
