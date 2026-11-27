// 정확한 최소 비용 오라클(실험용): 풀(레지스터 값들)에서 목표값 하나를 만드는 최소 명령 수를 전수 탐색으로 구한다.
// 유도는 트리 꼴(중간값 재사용 없음)로 센다. L_k = 정확히 k 개 명령으로 처음 나오는 값.
// 입력: limit npool ntargets / pool... / targets...     출력: 목표마다 "t cost" (7 은 (3,3) 분해로만 확인, 8 은 '7 초과 또는 미확인')
#include <cstdio>
#include <cstdint>
#include <vector>
#include <algorithm>
#include <unordered_set>
#include <ctime>
typedef uint64_t u64; typedef unsigned __int128 u128;
using namespace std;
static u64 LIM;
static vector<u64> L0, L1, L2, L3;
static inline bool in(const vector<u64>& v, u64 x) { return binary_search(v.begin(), v.end(), x); }
static inline void fwd(u64 a, u64 b, vector<u64>& out) {
    if (a + b <= LIM) out.push_back(a + b);
    u128 p = (u128)a * b; if (p <= LIM) out.push_back((u64)p);
    if (a > b) out.push_back(a - b); else if (b > a) out.push_back(b - a);
    if (b && a % b == 0) out.push_back(a / b);
    if (a && b % a == 0) out.push_back(b / a);
}
static inline int inv(u64 t, u64 y, u64* out) {   // x 들: x op y = t 또는 y op x = t
    int n = 0;
    if (t > y) out[n++] = t - y;
    if (t + y <= LIM) out[n++] = t + y;
    if (y > t) out[n++] = y - t;
    if (y && t % y == 0) out[n++] = t / y;
    u128 p = (u128)t * y; if (p <= LIM) out[n++] = (u64)p;
    if (t && y % t == 0) out[n++] = y / t;
    return n;
}
static void uniq(vector<u64>& v) { sort(v.begin(), v.end()); v.erase(unique(v.begin(), v.end()), v.end()); }
static void minus_(vector<u64>& v, const vector<u64>& w) {
    vector<u64> o; o.reserve(v.size());
    set_difference(v.begin(), v.end(), w.begin(), w.end(), back_inserter(o)); v.swap(o);
}
static int low(u64 x) { if (in(L0, x)) return 0; if (in(L1, x)) return 1; if (in(L2, x)) return 2; if (in(L3, x)) return 3; return 99; }
// cost <= 4 인지: 반환 4 이하의 정확한 값 또는 99
static int cost4(u64 t) {
    int c = low(t); if (c <= 3) return c;
    u64 xs[6];
    for (u64 p : L0) { int n = inv(t, p, xs); for (int i = 0; i < n; i++) if (in(L3, xs[i])) return 4; }
    for (u64 y : L1) { int n = inv(t, y, xs); for (int i = 0; i < n; i++) if (in(L2, xs[i])) return 4; }
    return 99;
}
static int cost5(u64 t) {
    int c = cost4(t); if (c <= 4) return c;
    u64 xs[6];
    for (u64 y : L1) { int n = inv(t, y, xs); for (int i = 0; i < n; i++) if (in(L3, xs[i])) return 5; }
    for (u64 y : L2) { int n = inv(t, y, xs); for (int i = 0; i < n; i++) if (in(L2, xs[i])) return 5; }
    for (u64 p : L0) { int n = inv(t, p, xs); for (int i = 0; i < n; i++) if (cost4(xs[i]) <= 4) return 5; }
    return 99;
}
static int cost6(u64 t) {
    int c = cost5(t); if (c <= 5) return c;
    u64 xs[6];
    for (u64 y : L2) { int n = inv(t, y, xs); for (int i = 0; i < n; i++) if (in(L3, xs[i])) return 6; }       // (3,2)
    for (u64 y : L1) { int n = inv(t, y, xs); for (int i = 0; i < n; i++) if (cost4(xs[i]) <= 4) return 6; }   // (4,1)
    for (u64 p : L0) { int n = inv(t, p, xs); for (int i = 0; i < n; i++) if (cost5(xs[i]) <= 5) return 6; }   // (5,0)
    return 99;
}
static int cost7part(u64 t) {      // (3,3) 만
    u64 xs[6];
    for (u64 y : L3) { int n = inv(t, y, xs); for (int i = 0; i < n; i++) if (in(L3, xs[i])) return 7; }
    return 99;
}
int main(int argc, char** argv) {
    int np, nt; if (scanf("%lu %d %d", &LIM, &np, &nt) != 3) return 1;
    L0.resize(np); for (auto& x : L0) if (scanf("%lu", &x) != 1) return 1;
    vector<u64> T(nt); for (auto& x : T) if (scanf("%lu", &x) != 1) return 1;
    int maxc = argc > 1 ? atoi(argv[1]) : 6;
    uniq(L0);
    clock_t t0 = clock();
    for (u64 a : L0) for (u64 b : L0) if (a <= b) fwd(a, b, L1);
    uniq(L1); minus_(L1, L0);
    for (u64 a : L1) for (u64 b : L0) fwd(a, b, L2);
    uniq(L2); minus_(L2, L0); minus_(L2, L1);
    { vector<u64> tmp; tmp.reserve(L2.size() * L0.size() * 3);
      for (u64 a : L2) for (u64 b : L0) fwd(a, b, tmp);
      for (size_t i = 0; i < L1.size(); i++) for (size_t j = i; j < L1.size(); j++) fwd(L1[i], L1[j], tmp);
      uniq(tmp); minus_(tmp, L0); minus_(tmp, L1); minus_(tmp, L2); L3.swap(tmp); }
    fprintf(stderr, "pool %zu L1 %zu L2 %zu L3 %zu (%.1fs)\n", L0.size(), L1.size(), L2.size(), L3.size(), double(clock() - t0) / CLOCKS_PER_SEC);
    for (u64 t : T) {
        clock_t t1 = clock();
        int c = maxc >= 6 ? cost6(t) : (maxc == 5 ? cost5(t) : cost4(t));
        if (c > 6 && maxc >= 7) c = cost7part(t);
        if (c > 7) c = 8;
        printf("%lu %d\n", t, c); fflush(stdout);
        fprintf(stderr, "  %lu cost %d (%.1fs)\n", t, c, double(clock() - t1) / CLOCKS_PER_SEC);
    }
    return 0;
}
