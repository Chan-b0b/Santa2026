"""2번: 복원된 숨은 정수들을 목표로 보고 decode 를 한 번 더 돌린다. 대조군: 같은 비트 크기의 난수."""
import sys,json,random
sys.path.insert(0,'core');sys.path.insert(0,'solvers/quirk')
import decode
R=json.load(open('solvers/relate/bases_export.json'))
Q={}
for f in ('bases3f.json','bases6.json'):
    for k,v in json.load(open('solvers/quirk/'+f)).items(): Q.setdefault(k,set()).update(v['bases'])
for k,v in R.items(): Q.setdefault(k,set()).update(v['bases'])
rng=random.Random(1)
n=0;hit=0;expl=0;chit=0;cexpl=0;tot=0;rows=[]
for p,S in sorted(Q.items()):
    B=sorted(S)
    if len([b for b in B if b>=1<<16])<3: continue
    n+=1; tot+=len(B)
    r=decode.decode(B,dmax_bits=20)
    bs,cov=r[0],r[1]
    if bs and len(cov)>=2: hit+=1; expl+=len(cov); rows.append((p,B,bs,len(cov)))
    C=[rng.randrange(1<<(b.bit_length()-1),1<<b.bit_length()) for b in B]
    r=decode.decode(C,dmax_bits=20)
    if r[0] and len(r[1])>=2: chit+=1; cexpl+=len(r[1])
print('puzzles tested',n,'ints',tot)
print('real: puzzles with structure',hit,'ints explained',expl)
print('control: ',chit,cexpl)
for x in rows[:15]: print(x)
