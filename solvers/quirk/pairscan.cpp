// 작은 숨은 정수용 2차원 훑기: t = k*a*b + r, |r| <= R, amin <= a <= b, a <= amax 인 (t, k, a, b, r) 를 전부 낸다.
// 입력(stdin): n K R amin amax / t_1 .. t_n      출력: ti k a b r
#include <cstdio>
#include <cstdint>
#include <vector>
#include <cmath>
typedef uint64_t u64; typedef int64_t i64;
int main() {
    int n, K; i64 R; u64 amin, amax;
    if (scanf("%d %d %ld %lu %lu", &n, &K, &R, &amin, &amax) != 5) return 1;
    std::vector<u64> t(n);
    for (auto &x : t) if (scanf("%lu", &x) != 1) return 1;
    for (int i = 0; i < n; ++i) {
        for (int k = 1; k <= K; ++k) {
            u64 q = t[i] / k;
            u64 hi = (u64)sqrtl((long double)q) + 1;
            if (hi > amax) hi = amax;
            for (u64 a = amin; a <= hi; ++a) {
                u64 m = (u64)k * a;
                u64 b = t[i] / m;
                u64 rem = t[i] - b * m;          // 0 <= rem < m
                i64 r;
                if ((i64)rem <= R) r = (i64)rem;
                else if ((i64)(m - rem) <= R) { r = -(i64)(m - rem); ++b; }
                else continue;
                if (b < a) continue;
                printf("%d %d %lu %lu %ld\n", i, k, a, b, r);
            }
        }
    }
    return 0;
}
