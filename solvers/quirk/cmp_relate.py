import json,sys
sys.path.insert(0,'core')
R=json.load(open('solvers/relate/bases_export.json'))
Q={}
for f in ('bases3f.json','bases6.json'):
    for k,v in json.load(open('solvers/quirk/'+f)).items():
        Q.setdefault(k,set()).update(v['bases'])
print(len(R),len(Q))
k0=next(iter(R)); print({a:(type(b).__name__) for a,b in R[k0].items()})
new=[];diff=[];same=[]
for p,v in R.items():
    rb=set(v['bases'])
    if p not in Q: new.append(p)
    elif rb-Q[p]: diff.append(p)
    else: same.append(p)
print('relate only',len(new),'diff ints',len(diff),'subset/same',len(same))
print('rel bases not in quirk total', sum(len(set(R[p]['bases'])-Q.get(p,set())) for p in new+diff))
json.dump({p:{'bases':R[p]['bases'],'cov':{},'nt':0} for p in new+diff},open('solvers/quirk/bases_rel_new.json','w'))
json.dump(new,open('solvers/quirk/_new.json','w'));json.dump(diff,open('solvers/quirk/_diff.json','w'))
