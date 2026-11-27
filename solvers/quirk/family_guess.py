import sys,json,collections,math,csv
sys.path.insert(0,'core');sys.path.insert(0,'solvers/quirk')
from verify import load_puzzles, read_submission
import decode2
P=load_puzzles('data/puzzles.csv')
PR=load_puzzles('data/practice_puzzles.csv')
fam={r['id']:r['family'] for r in csv.DictReader(open('data/practice_puzzles.csv'))}
best={p:len(json.loads(c)) for p,c in read_submission('best/best.csv').items()}
def cls(pz):
    t=sorted(set(pz.targets)); nd=collections.Counter(len(str(x)) for x in t)
    md,mc=nd.most_common(1)[0]; frac=mc/len(t)
    if pz.limit<64: return 'tiny',md
    if frac==1.0 and len(t)>=3: return 'indep',md
    if frac>=0.45 and mc>=4: return 'mixed',md
    return 'struct',None
cm=collections.Counter()
for pid,pz in PR.items(): cm[(fam[pid],cls(pz)[0])]+=1
print(sorted(cm.items()))
Q={}
for f in ('solvers/quirk/bases3f.json','solvers/quirk/bases6.json','solvers/relate/bases_export.json'):
    for k,v in json.load(open(f)).items(): Q.setdefault(k,[]).extend(v['bases'])
agg=collections.defaultdict(lambda:[0,0,0]); C={}
for pid,pz in P.items():
    c,md=cls(pz); C[pid]=(c,md)
    nt=len(set(pz.targets)-set(pz.start)); agg[c][0]+=1; agg[c][1]+=best[pid]; agg[c][2]+=nt
for c,(n,b,nt) in agg.items(): print(c,n,'best',b,'targets',nt,'per %.2f'%(b/nt))
cnt=collections.Counter(); per=collections.Counter()
for pid,pz in P.items():
    c,md=C[pid]
    B=list(dict.fromkeys(b for b in Q.get(pid,[]) if b>=512))
    T=sorted(t for t in set(pz.targets)-set(pz.start))
    cov=decode2.explain([t for t in T if t>=1<<16],B) if B else {}
    for t in T:
        rand = (c=='indep') or (c=='mixed' and len(str(t))==md)
        cnt[(c,'rand' if rand else 'str', 'ex' if t in cov else 'un')]+=1
        if c in('struct','mixed') and not rand and t not in cov: per[pid]+=1
for k in sorted(cnt): print(k,cnt[k])
json.dump(C,open(sys.argv[1],'w')); json.dump(per,open(sys.argv[2],'w'))
