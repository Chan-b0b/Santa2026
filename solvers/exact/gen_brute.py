import random,sys
random.seed(int(sys.argv[1]));N=int(sys.argv[2])
def ap(o,x,y,L):
    if o=='+':r=x+y
    elif o=='-':r=x-y
    elif o=='*':r=x*y
    else:
        if y==0 or x%y: return None
        r=x//y
    return r if 1<=r<=L else None
out=[]
while len(out)<N:
    L=random.choice([60,200,1000,20000,1<<20])
    n=random.randint(3,int(sys.argv[3]) if len(sys.argv)>3 else 8)
    hi=random.choice([10,30,L])
    v=[random.randint(1,min(hi,L)) for _ in range(n)]
    pool=list(v)
    k=random.randint(1,3)
    for _ in range(k):
        for _t in range(50):
            r=ap(random.choice('+-*/'),random.choice(pool),random.choice(pool),L)
            if r is not None: pool.append(r);break
    T=pool[-1] if random.random()<0.8 else random.randint(1,L)
    if T in v: continue
    out.append((L,v,T))
print(len(out))
for L,v,T in out: print(L,len(v),T,*v)
