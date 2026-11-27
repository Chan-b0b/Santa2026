// hidscan: 숨은 정수 훑기. 목표값 t 들에 대해 d 를 dmin..dmax 로 전부 훑어
// |t mod± d| <= R(d) 인 목표 수가 우연 수준(포아송 꼬리)보다 많은 d 를 출력한다.
// 입력(stdin): 줄마다 "id n t1 .. tn".  출력: "id d cnt mask(hex) r1,r2,.." (mask 는 목표 인덱스 비트)
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <string>
#include <iostream>
#include <sstream>
using namespace std;
typedef uint64_t u64; typedef int64_t i64;
int main(int argc, char** argv) {
    int R = argc > 1 ? atoi(argv[1]) : 128;
    u64 dmin = argc > 2 ? strtoull(argv[2], 0, 10) : 512;
    u64 dmaxArg = argc > 3 ? strtoull(argv[3], 0, 10) : (1ull << 24);
    int ratio = argc > 4 ? atoi(argv[4]) : 48;      // t >= ratio*d 인 목표만 센다
    double tail = argc > 5 ? atof(argv[5]) : 1e-7;
    string line;
    while (getline(cin, line)) {
        istringstream ss(line);
        string id; int n; ss >> id >> n;
        vector<u64> T(n);
        for (auto& t : T) ss >> t;
        u64 mx = 0; for (u64 t : T) if (t > mx) mx = t;
        u64 dmax = dmaxArg; if (mx / ratio < dmax) dmax = mx / ratio;
        vector<double> Td(n); for (int i = 0; i < n; i++) Td[i] = (double)T[i];
        for (u64 d = dmin; d <= dmax; d++) {
            i64 Rd = R; if ((i64)(d / 32) < Rd) Rd = d / 32;
            double inv = 1.0 / (double)d;
            u64 lim = d * (u64)ratio;
            int cnt = 0, m = 0; unsigned long long mask = 0;
            for (int i = 0; i < n; i++) {
                u64 t = T[i];
                if (t < lim) continue;
                m++;
                u64 q = (u64)(Td[i] * inv);
                i64 r = (i64)(t - q * d);
                while (r < 0) r += d;
                while (r >= (i64)d) r -= d;
                if (r <= Rd || (i64)d - r <= Rd) { cnt++; mask |= 1ull << i; }
            }
            if (cnt < 3) continue;
            double lam = m * (2.0 * Rd + 1) / (double)d;
            // 포아송 꼬리 근사: lam^cnt / cnt!
            double p = 1; for (int k = 1; k <= cnt; k++) p *= lam / k;
            if (p > tail) continue;
            printf("%s %llu %d %llx", id.c_str(), (unsigned long long)d, cnt, mask);
            for (int i = 0; i < n; i++) if (mask >> i & 1) {
                i64 r = (i64)(T[i] % d); if (r > (i64)d / 2) r -= d;
                printf(" %lld", (long long)r);
            }
            printf("\n");
        }
        printf("%s END\n", id.c_str());
        fflush(stdout);
    }
    return 0;
}
