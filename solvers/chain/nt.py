import random, math
SMALL = [p for p in range(2, 2000) if all(p % q for q in range(2, int(p**0.5) + 1))]
def isprime(n):
    if n < 2: return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n % p == 0: return n == p
    d = n-1; s = 0
    while d % 2 == 0: d//=2; s+=1
    for a in (2,3,5,7,11,13,17,19,23,29,31,37):
        x = pow(a, d, n)
        if x in (1, n-1): continue
        for _ in range(s-1):
            x = x*x % n
            if x == n-1: break
        else: return False
    return True
def rho(n, rnd=random.Random(1)):
    if n % 2 == 0: return 2
    while True:
        c = rnd.randrange(1, n); x = y = rnd.randrange(n); d = 1
        while d == 1:
            x = (x*x + c) % n; y = (y*y + c) % n; y = (y*y + c) % n
            d = math.gcd(abs(x-y), n)
        if d != n: return d
def factor(n):
    out = []
    for p in SMALL:
        if p * p > n: break
        while n % p == 0:
            out.append(p); n //= p
    def rec(n):
        if n == 1: return
        if isprime(n): out.append(n); return
        d = rho(n); rec(d); rec(n // d)
    rec(n)
    return sorted(out)
