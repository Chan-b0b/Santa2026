// 짝 밑수 훑기: 알려진 밑수 a 에 대해 x 를 XMIN..XMAX 까지 돌며 허브 h = a*x 의 지지 목표 수를 센다.
// 지지 목표: |t - round(t/h)*h| <= h >> SH. 허브 수준에서는 나머지가 15비트여도 작으므로 basescan 이 놓친 밑수가 잡힌다.
// 입력(한 줄): id a n t1 ... tn     출력: id a 다음에 "x:members:mask" 들 (members >= MINM)
// 사용: partnerscan SH XMIN XMAX MINM < in > out
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <vector>
#include <string>
#include <iostream>
#include <sstream>
using namespace std;
typedef uint64_t u64;
typedef int64_t i64;

int main(int argc, char** argv) {
    int SH = argc > 1 ? atoi(argv[1]) : 12;
    u64 XMIN = argc > 2 ? strtoull(argv[2], 0, 10) : 512;
    u64 XMAX = argc > 3 ? strtoull(argv[3], 0, 10) : (1ull << 23);
    int MINM = argc > 4 ? atoi(argv[4]) : 2;
    string line;
    while (getline(cin, line)) {
        istringstream is(line);
        string id; u64 a; int n;
        is >> id >> a >> n;
        vector<u64> T(n);
        vector<double> Td(n);
        u64 tmax = 0;
        for (int i = 0; i < n; i++) { is >> T[i]; Td[i] = (double)T[i]; if (T[i] > tmax) tmax = T[i]; }
        printf("%s %llu", id.c_str(), (unsigned long long)a);
        for (u64 x = XMIN; x < XMAX; x++) {
            unsigned __int128 hh = (unsigned __int128)a * x;
            if (hh > (unsigned __int128)tmax + (tmax >> SH)) break;
            u64 h = (u64)hh;
            i64 tol = (i64)(h >> SH);
            i64 tol2 = (i64)(h >> 18);
            double inv = 1.0 / (double)h;
            int m = 0, m2 = 0, qual = 0;
            u64 mask = 0;
            for (int i = 0; i < n; i++) {
                u64 q = (u64)(Td[i] * inv + 0.5);
                i64 r = (i64)(T[i] - q * h);
                i64 hs = (i64)h;
                while (r > hs / 2) { r -= hs; q++; }
                while (r < -(hs / 2)) { r += hs; q--; }
                if (q >= 1 && r <= tol && r >= -tol) {
                    m++; mask |= 1ull << i;
                    if (r <= tol2 && r >= -tol2) m2++;
                    u64 ar = (u64)(r < 0 ? -r : r);
                    qual += ar ? 64 - __builtin_clzll(ar) : 0;   // 나머지의 비트 수 합 (작을수록 좋다)
                }
            }
            // 지지 3개 이상이거나, 2개라도 둘 다 아주 빡빡하면(h >> 18) 출력한다.
            if (m >= MINM || m2 >= 2) printf(" %llu:%d:%llu:%d", (unsigned long long)x, m, (unsigned long long)mask, qual);
        }
        printf("\n");
        fflush(stdout);
    }
    return 0;
}
