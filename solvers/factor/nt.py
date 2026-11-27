"""정수론 도구: Miller-Rabin, Pollard rho(Brent), 소인수분해, 약수 나열."""
from math import gcd
import random

_SMALL = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for p in _SMALL:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _SMALL:
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


def _rho(n: int) -> int:
    if n % 2 == 0:
        return 2
    rnd = random.Random(n)
    while True:
        y, c, m = rnd.randrange(1, n), rnd.randrange(1, n), 128
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
                g = gcd(q, n)
                k += m
            r *= 2
        if g == n:
            g = 1
            while g == 1:
                ys = (ys * ys + c) % n
                g = gcd(abs(x - ys), n)
        if g != n:
            return g


_SP = [p for p in range(2, 2000) if all(p % q for q in range(2, int(p ** 0.5) + 1))]
_fcache: dict = {}


def factor(n: int) -> dict:
    """n의 소인수분해 {p: e}."""
    if n in _fcache:
        return _fcache[n]
    n0 = n
    f: dict = {}
    for p in _SP:
        if p * p > n:
            break
        while n % p == 0:
            f[p] = f.get(p, 0) + 1
            n //= p
    stack = [n] if n > 1 else []
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
    _fcache[n0] = f
    return f


def divisors(n: int, cap: int | None = None) -> list:
    ds = [1]
    for p, e in factor(n).items():
        cur = []
        pe = 1
        for _ in range(e):
            pe *= p
            for d in ds:
                v = d * pe
                if cap is None or v <= cap:
                    cur.append(v)
        ds += cur
    return ds


def fstr(n: int) -> str:
    f = factor(n)
    return "*".join(f"{p}^{e}" if e > 1 else f"{p}" for p, e in sorted(f.items())) or "1"
