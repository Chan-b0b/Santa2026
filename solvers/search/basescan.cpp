// 숨은 밑수 훑기: d 를 DMIN..DMAX 까지 전부 돌며 |t mod± d| <= R 인 목표 수를 센다.
// 우연 기대치(포아송)보다 뚜렷이 많은 d 만 출력한다.
// 입력(한 줄에 퍼즐 하나): id n t1 ... tn      출력: id 다음에 "d:hits:mask" 들
// 사용: basescan R DMIN DMAX BUDGET < in > out
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cmath>
#include <vector>
#include <string>
#include <iostream>
#include <sstream>
using namespace std;
typedef uint64_t u64;

static double ptail(int h, double lam) {  // P(X >= h), X ~ Poisson(lam)
    double term = exp(-lam), cdf = 0;
    for (int i = 0; i < h; i++) { cdf += term; term *= lam / (i + 1); }
    double t = 1.0 - cdf;
    return t < 0 ? 0 : t;
}

int main(int argc, char** argv) {
    int R = argc > 1 ? atoi(argv[1]) : 64;
    u64 DMIN = argc > 2 ? strtoull(argv[2], 0, 10) : 2048;
    u64 DMAX = argc > 3 ? strtoull(argv[3], 0, 10) : (1ull << 23);
    double budget = argc > 4 ? atof(argv[4]) : 0.3;
    string line;
    while (getline(cin, line)) {
        istringstream is(line);
        string id; int n;
        is >> id >> n;
        vector<u64> T(n);
        vector<double> Td(n);
        for (int i = 0; i < n; i++) { is >> T[i]; Td[i] = (double)T[i]; }
        printf("%s", id.c_str());
        u64 tmax = 0;
        for (auto t : T) if (t > tmax) tmax = t;
        u64 dmax = DMAX;
        if (dmax > tmax / 4) dmax = tmax / 4;
        // 옥타브의 1/4 구간마다 문턱을 다시 계산한다.
        u64 d = DMIN;
        while (d < dmax) {
            u64 dend = d + d / 4;
            if (dend > dmax) dend = dmax;
            double lam = n * (2.0 * R + 1) / (double)d;
            int thr = 3;
            while (thr < n && ptail(thr, lam) * (double)(dend - d) * 4 > budget) thr++;
            for (u64 x = d; x < dend; x++) {
                double inv = 1.0 / (double)x;
                int hits = 0;
                u64 mask = 0;
                for (int i = 0; i < n; i++) {
                    u64 q = (u64)(Td[i] * inv);
                    int64_t r = (int64_t)(T[i] - q * x);
                    while (r < 0) r += x;
                    while (r >= (int64_t)x) r -= x;
                    if (r <= R || r >= (int64_t)x - R) { hits++; mask |= 1ull << i; }
                }
                if (hits >= thr) printf(" %llu:%d:%llu", (unsigned long long)x, hits, (unsigned long long)mask);
            }
            d = dend;
        }
        printf("\n");
        fflush(stdout);
    }
    return 0;
}
