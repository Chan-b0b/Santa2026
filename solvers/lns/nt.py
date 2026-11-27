"""작은 정수론 도구: 소인수분해(시행 나눗셈 + Pollard rho), 약수 나열."""
import math, random

_SMALL = [p for p in range(2, 2000) if all(p % q for q in range(2, int(p ** 0.5) + 1))]

def is_prime(n):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2; s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
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
    while True:
        c = random.randrange(1, n); x = y = random.randrange(0, n); d = 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n; y = (y * y + c) % n
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d

def factor(n):
    f = {}
    for p in _SMALL:
        if p * p > n:
            break
        while n % p == 0:
            f[p] = f.get(p, 0) + 1; n //= p
    stack = [n] if n > 1 else []
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if is_prime(m):
            f[m] = f.get(m, 0) + 1
        else:
            d = _rho(m); stack += [d, m // d]
    return dict(sorted(f.items()))

def fstr(n):
    return "·".join(f"{p}^{e}" if e > 1 else str(p) for p, e in factor(n).items()) if n > 1 else "1"

def divisors(n):
    ds = [1]
    for p, e in factor(n).items():
        ds = [d * p ** k for d in ds for k in range(e + 1)]
    return sorted(ds)
