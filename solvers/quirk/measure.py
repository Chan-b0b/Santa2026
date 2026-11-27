"""3번: 전용 구성기를 만들 가치가 있는지 잰다. 해독된 퍼즐별 (k, r) 통계와 best 프로그램의 명령 분해."""
import sys,json,collections,math
sys.path.insert(0,'core');sys.path.insert(0,'solvers/quirk')
from verify import load_puzzles, read_submission
import decode2
P=load_puzzles('data/puzzles.csv')
best={p:json.loads(c) for p,c in read_submission('best/best.csv').items()}
Q={}
for f in ('bases3f.json','bases6.json'):
    for k,v in json.load(open('solvers/quirk/'+f)).items(): Q.setdefault(k,[]).extend(v['bases'])
R=json.load(open('solvers/relate/bases_export.json'))
for k,v in R.items(): Q.setdefault(k,[]).extend(v['bases'])
def bl(x): return max(1,abs(x)).bit_length()
rows=[]
for pid,B in sorted(Q.items()):
    B=list(dict.fromkeys(b for b in B if b>=512)); pz=P[pid]; T=sorted(set(pz.targets))
    cov=decode2.explain([t for t in T if t>=1<<16],B)
    if len(cov)<3: continue
    ks=collections.Counter(v[0] for v in cov.values()); rs=collections.Counter(v[3] for v in cov.values())
    mid=lambda c:sum(1 for x in c if 10<=bl(x)<=16)
    prog=best[pid]; reg=[None]*pz.registers; reg[:len(pz.start)]=pz.start
    Bs=set(B); Ts=set(T); hubs={}
    for a in B:
        for b in B: hubs[a*b]=1
    kh={t-v[3] for t,v in cov.items()}
    cls=collections.Counter(); seen=set(pz.start)
    for op,a,b,d in prog:
        x,y=reg[a],reg[b]
        v=x+y if op=='+' else x-y if op=='-' else x*y if op=='*' else x//y
        reg[d]=v
        if v in Ts: c='T'
        elif v in Bs: c='H'
        elif v in hubs: c='P'
        elif v in kh: c='KH'
        elif v<(1<<16): c='S'
        else: c='O'
        cls[c]+=1
    rows.append(dict(pid=pid,n=len(prog),ncov=len(cov),nt=len(T),dk=len(ks),dr=len(rs),kmid=mid(ks),rmid=mid(rs),
        kreuse=sum(c-1 for c in ks.values()),maxk=max(bl(k) for k in ks),maxr=max(bl(r) for r in rs),**{c:cls[c] for c in 'THPKSO' if False},cls=dict(cls)))
json.dump(rows,open('solvers/quirk/measure.json','w'))
N=len(rows)
print('puzzles',N,'total best len',sum(r['n'] for r in rows))
tot=collections.Counter()
for r in rows: tot.update(r['cls'])
print('class totals',dict(tot))
print('avg distinct k',sum(r['dk'] for r in rows)/N,'avg distinct r',sum(r['dr'] for r in rows)/N)
print('avg k reuse',sum(r['kreuse'] for r in rows)/N,'cov/nt',sum(r['ncov'] for r in rows)/sum(r['nt'] for r in rows))
print('k bits hist',collections.Counter(min(r['maxk'],20) for r in rows))
print('puzzles with >=3 mid(10-16bit) k or r', sum(1 for r in rows if r['kmid']+r['rmid']>=3), ' >=6',sum(1 for r in rows if r['kmid']+r['rmid']>=6))
big=[r for r in rows if r['kmid']+r['rmid']>=3 and r['cls'].get('S',0)>=10]
print('target list (mid>=3 and S>=10):',len(big),'S sum',sum(r['cls'].get('S',0) for r in big))
print('S sum all',tot['S'], 'S share',tot['S']/sum(r['n'] for r in rows))
big.sort(key=lambda r:-r['cls'].get('S',0))
for r in big[:15]: print(r['pid'],r['n'],'S',r['cls'].get('S'),'kmid',r['kmid'],'rmid',r['rmid'],'dk',r['dk'],'dr',r['dr'],r['cls'])
