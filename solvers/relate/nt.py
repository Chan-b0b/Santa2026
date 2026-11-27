"""수론 도구: 밀러-라빈, 폴라드 로, 소인수분해, 약수."""
import math, random

_SMALL = [p for p in range(2, 2000) if all(p % q for q in range(2, int(p ** 0.5) + 1))]

def is_prime(n):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True

def _rho(n):
    if n % 2 == 0:
        return 2
    rnd = random.Random(n)
    while True:
        c = rnd.randrange(1, n)
        y = rnd.randrange(0, n)
        m = 128
        g = r = q = 1
        x = ys = y
        while g == 1:
            x = y
            for _ in range(r):
                y = (y * y + c) % n
            k = 0
            while k < r and g == 1:
                ys = y
                for _ in range(min(m, r - k)):
                    y = (y * y + c) % n
                    q = q * abs(x - y) % n
                g = math.gcd(q, n)
                k += m
            r *= 2
        if g == n:
            g = 1
            while g == 1:
                ys = (ys * ys + c) % n
                g = math.gcd(abs(x - ys), n)
        if g != n:
            return g

def factor(n):
    """n의 소인수분해를 {p: e}로."""
    f = {}
    for p in _SMALL:
        if p * p > n:
            break
        while n % p == 0:
            f[p] = f.get(p, 0) + 1
            n //= p
    if n == 1:
        return f
    stack = [n]
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if is_prime(m):
            f[m] = f.get(m, 0) + 1
            continue
        d = _rho(m)
        stack.append(d)
        stack.append(m // d)
    return f

def divisors(n, cap=None):
    f = factor(n)
    ds = [1]
    for p, e in f.items():
        cur = []
        pe = 1
        for _ in range(e + 1):
            for d in ds:
                v = d * pe
                if cap is None or v <= cap:
                    cur.append(v)
            pe *= p
        ds = cur
    return sorted(ds)

def fstr(n):
    f = factor(n)
    return "*".join(f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(f.items()))
