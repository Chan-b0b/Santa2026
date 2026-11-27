// 작은 밑수 쌍 훑기: a <= b 를 AMIN..AMAX 에서 전부 돌며 허브 h = a*b 의 지지 목표(|t - k*h| <= h >> SH, k >= 1)를 센다.
// 밑수가 10~13비트로 작아 basescan(나머지 64 이하)과 삼각 관계(근사 허브의 상대 오차가 큼)가 못 잡는 퍼즐용.
// 입력(한 줄): id n t1 ... tn     출력: id 다음에 "a:b:members:mask" 들 (members >= MINM)
// 사용: pairscan SH AMIN AMAX MINM < in > out
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
    int SH = argc > 1 ? atoi(argv[1]) : 10;
    u64 AMIN = argc > 2 ? strtoull(argv[2], 0, 10) : 512;
    u64 AMAX = argc > 3 ? strtoull(argv[3], 0, 10) : 8192;
    int MINM = argc > 4 ? atoi(argv[4]) : 5;
    string line;
    while (getline(cin, line)) {
        istringstream is(line);
        string id; int n;
        is >> id >> n;
        vector<u64> T(n);
        vector<double> Td(n);
        u64 tmax = 0;
        for (int i = 0; i < n; i++) { is >> T[i]; Td[i] = (double)T[i]; if (T[i] > tmax) tmax = T[i]; }
        printf("%s", id.c_str());
        for (u64 a = AMIN; a < AMAX; a++) {
            for (u64 b = a; b < AMAX; b++) {
                u64 h = a * b;
                if (h > tmax) break;
                i64 tol = (i64)(h >> SH);
                i64 hs = (i64)h;
                double inv = 1.0 / (double)h;
                int m = 0;
                u64 mask = 0;
                for (int i = 0; i < n; i++) {
                    u64 q = (u64)(Td[i] * inv + 0.5);
                    i64 r = (i64)(T[i] - q * h);
                    while (r > hs / 2) { r -= hs; q++; }
                    while (r < -(hs / 2)) { r += hs; q--; }
                    if (q >= 1 && r <= tol && r >= -tol) { m++; mask |= 1ull << i; }
                }
                if (m >= MINM) printf(" %llu:%llu:%d:%llu", (unsigned long long)a, (unsigned long long)b, m, (unsigned long long)mask);
            }
        }
        printf("\n");
        fflush(stdout);
    }
    return 0;
}
