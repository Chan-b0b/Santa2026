"""정수론 도구: Miller-Rabin, Pollard rho, 약수 나열."""
import math, random

def is_prime(n):
    if n < 2: return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0: return n == p
    d = n - 1; s = 0
    while d % 2 == 0: d //= 2; s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1: break
        else: return False
    return True

def _rho(n):
    if n % 2 == 0: return 2
    while True:
        c = random.randrange(1, n); y = random.randrange(0, n); m = 128; g = r = q = 1
        while g == 1:
            x = y
            for _ in range(r): y = (y * y + c) % n
            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(m, r - k)):
                    y = (y * y + c) % n; q = q * abs(x - y) % n
                g = math.gcd(q, n); k += m
            r *= 2
        if g == n:
            g = 1
            while g == 1:
                ys = (ys * ys + c) % n; g = math.gcd(abs(x - ys), n)
        if g != n: return g

def factorint(n):
    f = {}
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47):
        while n % p == 0: f[p] = f.get(p, 0) + 1; n //= p
    st = [n] if n > 1 else []
    while st:
        m = st.pop()
        if m == 1: continue
        if is_prime(m): f[m] = f.get(m, 0) + 1; continue
        d = _rho(m); st.append(d); st.append(m // d)
    return f

def divisors(n, fac=None):
    fac = fac or factorint(n)
    ds = [1]
    for p, e in fac.items():
        ds = [d * p ** k for d in ds for k in range(e + 1)]
    return sorted(ds)

def fstr(n):
    return '·'.join(f'{p}^{e}' if e > 1 else str(p) for p, e in sorted(factorint(n).items())) if n > 1 else '1'
