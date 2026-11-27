// 숨은 정수(base) 후보 찾기: d 를 전부 훑어 |t mod± d| <= R(d) 인 목표값 수를 센다.
// 입력(stdin): n dmax hmin  /  t_1 .. t_n
// 출력: d hits  (r_i ...)   — hits >= hmin 인 d 만.  r 은 목표 순서대로, 안 맞으면 x.
#include <cstdio>
#include <cstdint>
#include <vector>
#include <cstdlib>
typedef uint64_t u64;
int main() {
    int n; u64 dmax; int hmin;
    if (scanf("%d %lu %d", &n, &dmax, &hmin) != 3) return 1;
    std::vector<u64> t(n);
    for (auto &x : t) if (scanf("%lu", &x) != 1) return 1;
    std::vector<long> r(n);
    for (u64 d = 64; d <= dmax; ++d) {
        u64 R = d >> 9; if (R > 1024) R = 1024;
        int hits = 0;
        for (int i = 0; i < n; ++i) {
            if (t[i] < d * 4) { r[i] = INT64_MIN; continue; }
            u64 m = t[i] % d;
            if (m <= R) { r[i] = (long)m; ++hits; }
            else if (d - m <= R) { r[i] = -(long)(d - m); ++hits; }
            else r[i] = INT64_MIN;
        }
        if (hits >= hmin) {
            printf("%lu %d", d, hits);
            for (int i = 0; i < n; ++i) { if (r[i] == INT64_MIN) printf(" x"); else printf(" %ld", r[i]); }
            printf("\n");
        }
    }
    return 0;
}
