// chain: 숨은 밑(base) 후보 훑기.  quirk 의 "t = k*a*b + r" 해독 아이디어를 가능도 점수로 일반화했다.
// d 를 dmin..dmax 전부 훑어, 목표값 t 마다 r = |t mod± d| 를 구하고 r <= min(d/64, 8192) 인 것을 적중으로 본다.
// 같은 허브(서로 작은 유리수 배 관계)에 속한 목표값은 한 묶음으로 보고 묶음마다 가장 큰 증거 하나만 센다
// (허브 H 하나가 우연히 d 의 배수 근처면 그 묶음 전체가 적중하기 때문).
//   E = sum_묶음 max log2(d / (2r+1)),  k = 적중 묶음 수
//   점수(비트) = E - log2 C(묶음 수, k) - log2( (E ln2)^(k-1) / (k-1)! )      (귀무가설에서의 꼬리 확률의 -log2)
// 입력(stdin): n nc dmin dmax thr / t_1..t_n / c_1..c_n (묶음 번호 0..nc-1)
// 출력: d 점수 k 적중수 (목표번호:r ...)
#include <cstdio>
#include <cstdint>
#include <cmath>
#include <vector>
typedef unsigned long long u64;
int main() {
    int n, nc; u64 dmin, dmax; double thr;
    if (scanf("%d %d %llu %llu %lf", &n, &nc, &dmin, &dmax, &thr) != 5) return 1;
    std::vector<u64> t(n); std::vector<int> c(n);
    for (auto &x : t) if (scanf("%llu", &x) != 1) return 1;
    for (auto &x : c) if (scanf("%d", &x) != 1) return 1;
    std::vector<double> lc(nc + 1, 0.0), lf(nc + 2, 0.0);
    for (int h = 1; h <= nc; ++h) lc[h] = lc[h - 1] + log2((double)(nc - h + 1) / h);
    for (int h = 2; h <= nc + 1; ++h) lf[h] = lf[h - 1] + log2((double)h);   // lf[h] = log2(h!)
    std::vector<double> best(nc, 0.0);
    std::vector<int> touched, hi; std::vector<long long> hr;
    for (u64 d = dmin; d <= dmax; ++d) {
        u64 R = d >> 6; if (R > 8192) R = 8192;
        u64 tmin = d << 4;
        touched.clear(); hi.clear(); hr.clear();
        for (int i = 0; i < n; ++i) {
            u64 x = t[i];
            if (x < tmin) continue;
            u64 m = x % d;
            bool neg = m > d - m;
            u64 r = neg ? d - m : m;
            if (r <= R) {
                double e = log2((double)d / (double)(2 * r + 1));
                int k = c[i];
                if (best[k] == 0.0) touched.push_back(k);
                if (e > best[k]) best[k] = e;
                hi.push_back(i); hr.push_back(neg ? -(long long)r : (long long)r);
            }
        }
        if (!touched.empty()) {
            double ev = 0;
            for (int k : touched) { ev += best[k]; best[k] = 0.0; }
            int hc = (int)touched.size();
            if (hc >= 2) {
                double s = ev - lc[hc] - ((hc - 1) * log2(ev * 0.6931471805599453) - lf[hc - 1]);
                if (s >= thr) {
                    printf("%llu %.1f %d %d", d, s, hc, (int)hi.size());
                    for (size_t j = 0; j < hi.size(); ++j) printf(" %d:%lld", hi[j], hr[j]);
                    printf("\n");
                }
            }
        }
    }
    return 0;
}
