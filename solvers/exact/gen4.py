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
    L=random.choice([20000,10**6]);n=random.randint(3,5)
    hi=random.choice([50,L]);v=[random.randint(1,min(hi,L)) for _ in range(n)]
    pool=list(v);tree=random.random()<0.7;tmp=[]
    for _ in range(4):
        for _t in range(50):
            src=pool if not tree else v+tmp[-1:]
            r=ap(random.choice('+-*/'),random.choice(src),random.choice(src),L)
            if r is not None: pool.append(r);tmp.append(r);break
    T=pool[-1]
    if T in v: continue
    out.append((L,v,T))
print(len(out))
for L,v,T in out: print(L,len(v),T,*v)
