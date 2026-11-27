"""작은 정수론 도구: Miller-Rabin, Pollard rho, 소인수분해, 약수 나열."""
import math, random

_SMALL = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]

def is_prime(n):
    if n < 2:
        return False
    for p in _SMALL:
        if n % p == 0:
            return n == p
    d = n - 1
    s = 0
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

def _rho(n):
    if n % 2 == 0:
        return 2
    if n % 3 == 0:
        return 3
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

def factorize(n):
    """n -> {p: e}"""
    res = {}
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47):
        while n % p == 0:
            res[p] = res.get(p, 0) + 1
            n //= p
    stack = [n] if n > 1 else []
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if is_prime(m):
            res[m] = res.get(m, 0) + 1
            continue
        d = _rho(m)
        stack.append(d)
        stack.append(m // d)
    return res

def divisors(n, cap=None):
    f = factorize(n)
    ds = [1]
    for p, e in f.items():
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


_PRIMES = None

def _primes():
    global _PRIMES
    if _PRIMES is None:
        n = 4096
        sieve = bytearray([1]) * n
        sieve[0] = sieve[1] = 0
        for i in range(2, 64):
            if sieve[i]:
                sieve[i * i::i] = bytearray(len(sieve[i * i::i]))
        _PRIMES = [i for i in range(n) if sieve[i]]
    return _PRIMES


def _rho_capped(n, cap):
    """반복 횟수 제한이 있는 Pollard rho. 실패하면 None."""
    if n % 2 == 0:
        return 2
    for c in (1, 3, 5):
        x = y = 2
        q = 1
        it = 0
        while it < cap:
            for _ in range(64):
                x = (x * x + c) % n
                y = (y * y + c) % n
                y = (y * y + c) % n
                q = q * abs(x - y) % n
            it += 64
            g = math.gcd(q, n)
            if g == 1:
                continue
            if g != n:
                return g
            break
    return None


def factorize_fast(n, cap=6000):
    """작은 소수 시험 나눗셈 + 제한된 rho. 못 쪼갠 합성수는 그대로 인수로 둔다."""
    res = {}
    for p in _primes():
        if p * p > n:
            break
        if n % p == 0:
            e = 0
            while n % p == 0:
                n //= p
                e += 1
            res[p] = e
    stack = [n] if n > 1 else []
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        if m < 4096 * 4096 or is_prime(m):
            res[m] = res.get(m, 0) + 1
            continue
        d = _rho_capped(m, cap)
        if d is None:
            res[m] = res.get(m, 0) + 1
            continue
        stack.append(d)
        stack.append(m // d)
    return res


def divisors_bounded(n, maxcount=400):
    f = factorize_fast(n)
    ds = [1]
    for p, e in sorted(f.items()):
        cur = []
        pe = 1
        for _ in range(e):
            pe *= p
            for d in ds:
                cur.append(d * pe)
        ds += cur
        if len(ds) > maxcount:
            ds.sort()
            ds = ds[:maxcount // 2] + ds[-maxcount // 2:]
    return ds
