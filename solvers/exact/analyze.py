import json,sys,collections
tags=sys.argv[1:]
FAMN={'indep':'indep','mixed':'mixed','struct':'구조형'}
st=collections.defaultdict(lambda:dict(puz=0,nodes=collections.Counter(),hits=collections.Counter(),saved=0,nofit=0,div=0,masks=collections.Counter(),time=0.0,nt=0,ids=set()))
seen=set()
for tag in tags:
    for l in open(f'solvers/exact/stats_{tag}.jsonl'):
        r=json.loads(l)
        if (tag[:2],r["id"]) in seen: continue
        seen.add((tag[:2],r["id"]));f=st[r["fam"]];f["puz"]+=1
        for c in r['nodes']:f['nodes'][min(c,6)]+=1
        for h in r['hits']:
            f['hits'][(min(h['c'],6),h['k'])]+=1
            f['masks'][(h['k'],h['mask'])]+=1
            f['div']+=h['div'];f['nofit']+=(not h['fit'])
        f['saved']+=r['best']-r['final'];f['time']+=sum(r['times']);f['nt']+=len(r['times'])
for fam,f in st.items():
    print(FAMN.get(fam,fam),'퍼즐',f['puz'],'본 노드',dict(sorted(f['nodes'].items())),'합',sum(f['nodes'].values()))
    print('  적중(원뿔,k):',dict(sorted(f['hits'].items())),'레지스터 못 쓴 것',f['nofit'],'나눗셈 포함',f['div'],'줄어든 합',f['saved'])
    print('  꼴(k,mask):',dict(f['masks']),'노드당 평균 초',round(f['time']/max(1,f['nt']),3))
