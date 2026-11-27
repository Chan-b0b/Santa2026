// walk: 값 집합 걷기 (value-set walk).
//
// 상태는 값의 집합 V (시작값 S, 목표값 T 포함). 비용 |V \ S|.
// 유효: S 에서 "V 안의 두 값의 한 번 연산 결과가 V 에 있으면 유도됨"을 되풀이해 V 전부가 유도된다.
// 이동: V 의 쌍 결과 가운데 V 와의 관계가 minrel 개 이상인 w 를 넣고, 필요 없어진 값을 무작위 순서로 지운다.
//   크기가 늘지 않으면 받고, 늘면 확률 pu (pu0 -> pu1 로 기하 감소) 로 받는다.
// 삭제 판정: 값마다 비트셋 rho(v) (비트 x = x 없이 v 를 유도할 수 있음) 의 최소 고정점.
//   x 를 지울 수 있다 <=> 모든 목표 t 에서 rho(t) 의 비트 x 가 1.  (rosswade 정리 5)
// 프로그램으로 되돌리기: 우선순위 목록 스케줄(조리법은 그때 고름) + 수명 기준 조리법 다시 고르기
//   + 48 레지스터 검사, 넘치면 우선순위를 흔드는 수리.
//
// 사용: walk <입력> <초> [key=value ...]
//   seed=1 pu0=0.02 pu1=0.0005 minrel=2 repair=2000 back=0 check=0 trace=0
// 입력/출력 형식은 elf_lns 와 같다.
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long u64;
typedef unsigned __int128 u128;

static inline u64 hmix(u64 x) { x ^= x >> 31; x *= 0x9E3779B97F4A7C15ULL; x ^= x >> 29; x *= 0xBF58476D1CE4E5B9ULL; x ^= x >> 32; return x; }

struct VMap {   // 값 -> 칸, 지우기 지원(선형 탐사, 뒤로 당기기)
    vector<u64> key; vector<int> val; u64 mask = 0;
    void init(size_t n) { size_t s = 16; while (s < n * 4) s <<= 1; key.assign(s, 0); val.assign(s, -1); mask = s - 1; }
    int get(u64 k) const { u64 h = hmix(k) & mask; while (key[h]) { if (key[h] == k) return val[h]; h = (h + 1) & mask; } return -1; }
    void put(u64 k, int v) { u64 h = hmix(k) & mask; while (key[h] && key[h] != k) h = (h + 1) & mask; key[h] = k; val[h] = v; }
    void erase(u64 k) {
        u64 h = hmix(k) & mask; while (key[h] && key[h] != k) h = (h + 1) & mask;
        if (!key[h]) return;
        key[h] = 0; val[h] = -1;
        u64 j = h;
        while (true) {
            j = (j + 1) & mask; if (!key[j]) break;
            u64 home = hmix(key[j]) & mask;
            bool between = (h <= j) ? (home > h && home <= j) : (home > h || home <= j);
            if (!between) { key[h] = key[j]; val[h] = val[j]; key[j] = 0; val[j] = -1; h = j; }
        }
    }
};

struct PEnt { u64 key; int cnt; int cpos; };
struct PTable {   // 쌍 결과 값 -> 관계 수. 지우지 않고 cnt 를 0 으로 둔다(가끔 다시 만든다)
    vector<PEnt> s; u64 mask = 0; size_t used = 0;
    void init(size_t want) { size_t n = 1024; while (n < want) n <<= 1; s.assign(n, PEnt{0, 0, -1}); mask = n - 1; used = 0; }
    PEnt *get(u64 k) { u64 h = hmix(k) & mask; while (s[h].key) { if (s[h].key == k) return &s[h]; h = (h + 1) & mask; } return nullptr; }
    PEnt *ins(u64 k) { u64 h = hmix(k) & mask; while (s[h].key) { if (s[h].key == k) return &s[h]; h = (h + 1) & mask; } s[h] = PEnt{k, 0, -1}; used++; return &s[h]; }
};

struct Rc { int a, b; char op; };
static const int WMAX = 16;

struct Walk {
    u64 L = 0; int nreg = 48, ns = 0;
    vector<u64> S, T;             // 시작값(레지스터 순서), 목표값(중복 제거, 시작값 제외)
    unordered_set<u64> tset;
    int cap = 0, W = 0;
    vector<u64> val; vector<char> pres, isS, isT;
    vector<vector<Rc>> rec; vector<vector<int>> users;
    vector<u64> rho, rhoSave;
    vector<int> plist, ppos, freeSl, tslots;
    VMap vm; PTable pt; vector<u64> cand;
    vector<double> prio;
    vector<u64> hA, hB; vector<char> hOp;
    int nonStart = 0, minrel = 2;
    mt19937_64 rng;
    // 설정
    double pu0 = 0.02, pu1 = 0.0005, back = 0, secs = 10; int repairIters = 2000, checkEvery = 0, trace = 0, probe = 0, probe2 = 0, regMode = 1, placeMode = 1; long rslack = 0; long nRegRej = 0;
    double compileShare = 0.3;
    // 통계
    long nMove = 0, nNoCand = 0, nNeu = 0, nImp = 0, nGrow = 0, nRej = 0, nCompile = 0, nCompileFail = 0, nBack = 0, nRemoved = 0, nRhoFull = 0, nCheck = 0, nNull = 0;
    double tCompile = 0; long candSum = 0;
    // 최선
    int bestLen = INT_MAX, bestSet = INT_MAX; vector<array<int, 4>> bestProg;
    vector<u64> bestVals; vector<double> bestPrio; vector<u64> bestHA, bestHB; vector<char> bestHOp;
    double lastBestT = 0;
    chrono::steady_clock::time_point t0 = chrono::steady_clock::now();
    double elapsed() const { return chrono::duration<double>(chrono::steady_clock::now() - t0).count(); }
    double unif() { return uniform_real_distribution<double>(0, 1)(rng); }

    u64 *R(int v) { return &rho[(size_t)v * W]; }
    static bool bit(const u64 *m, int x) { return (m[x >> 6] >> (x & 63)) & 1; }

    template <class F> void pairResults(u64 x, u64 y, F f) {
        u64 a = min(x, y), b = max(x, y);
        if (a + b <= L) f(a + b);
        if (b > a) f(b - a);
        if (a >= 2) { u128 p = (u128)a * b; if (p <= L) f((u64)p); if (b % a == 0) f(b / a); }
    }
    void candAdd(PEnt *e) { if (e->cpos < 0) { e->cpos = (int)cand.size(); cand.push_back(e->key); } }
    void candDel(PEnt *e) {
        if (e->cpos < 0) return;
        int p = e->cpos; u64 last = cand.back(); cand[p] = last; cand.pop_back(); e->cpos = -1;
        if (p < (int)cand.size()) pt.get(last)->cpos = p;
    }
    void pairInc(u64 r) { PEnt *e = pt.ins(r); e->cnt++; if (e->cnt >= minrel && vm.get(r) < 0) candAdd(e); }
    void pairDec(u64 r) { PEnt *e = pt.get(r); e->cnt--; if (e->cnt < minrel) candDel(e); }
    static void removeOne(vector<int> &U, int x) { for (size_t i = 0; i < U.size(); i++) if (U[i] == x) { U[i] = U.back(); U.pop_back(); return; } }
    void addRec(int v, int a, int b, char op) { rec[v].push_back(Rc{a, b, op}); users[a].push_back(v); if (b != a) users[b].push_back(v); }

    int insertVal(u64 w, bool start, int at = -1) {
        int sw;
        if (at < 0) { sw = freeSl.back(); freeSl.pop_back(); }
        else { sw = at; for (size_t i = 0; i < freeSl.size(); i++) if (freeSl[i] == at) { freeSl[i] = freeSl.back(); freeSl.pop_back(); break; } }
        val[sw] = w; pres[sw] = 1; vm.put(w, sw); ppos[sw] = (int)plist.size(); plist.push_back(sw);
        isS[sw] = start; isT[sw] = !start && tset.count(w);
        rec[sw].clear(); users[sw].clear();
        if (PEnt *e = pt.get(w)) candDel(e);
        for (int x : plist) pairResults(w, val[x], [&](u64 r) { pairInc(r); });
        // w 의 조리법 (w 자신은 재료가 아님)
        for (int x : plist) {
            if (x == sw) continue;
            u64 X = val[x]; int y;
            // 빼기와 나누기는 x 를 앞 재료(피감수, 피제수)로 둘 때만 센다 (같은 조리법을 두 번 넣지 않게)
            if (w > X) { u64 Y = w - X; if (X <= Y && (y = vm.get(Y)) >= 0) addRec(sw, x, y, '+'); }
            if (X > w && (y = vm.get(X - w)) >= 0 && y != sw) addRec(sw, x, y, '-');
            if (X >= 2 && w % X == 0) { u64 Y = w / X; if (Y >= X && (y = vm.get(Y)) >= 0 && y != sw) addRec(sw, x, y, '*'); }
            if (X % w == 0) { u64 Y = X / w; if ((y = vm.get(Y)) >= 0 && y != sw) addRec(sw, x, y, '/'); }
        }
        // w 를 재료로 쓰는 다른 값의 조리법 (x == sw 도 포함: 2w, w*w, w/w)
        for (int x : plist) {
            u64 X = val[x]; int z;
            if (w + X <= L && (z = vm.get(w + X)) >= 0 && z != sw && z != x) addRec(z, sw, x, '+');
            if (w > X && (z = vm.get(w - X)) >= 0 && z != x && z != sw) addRec(z, sw, x, '-');
            if (x != sw && X > w && (z = vm.get(X - w)) >= 0 && z != x && z != sw) addRec(z, x, sw, '-');
            if (X >= 2 && w >= 2 && (u128)w * X <= L && (z = vm.get(w * X)) >= 0 && z != sw && z != x) addRec(z, sw, x, '*');
            if (X >= 2 && w % X == 0 && (z = vm.get(w / X)) >= 0 && z != x && z != sw) addRec(z, sw, x, '/');
            if (x != sw && w >= 2 && X % w == 0 && (z = vm.get(X / w)) >= 0 && z != x && z != sw) addRec(z, x, sw, '/');
        }
        if (!start) nonStart++;
        return sw;
    }
    void deleteVal(int u) {
        u64 w = val[u];
        for (int x : plist) pairResults(w, val[x], [&](u64 r) { pairDec(r); });
        for (int v : users[u]) {
            if (!pres[v] || v == u) continue;
            auto &Rv = rec[v];
            for (size_t i = 0; i < Rv.size();) {
                if (Rv[i].a == u || Rv[i].b == u) {
                    int o = Rv[i].a == u ? Rv[i].b : Rv[i].a;
                    if (o != u) removeOne(users[o], v);
                    Rv[i] = Rv.back(); Rv.pop_back();
                } else i++;
            }
        }
        for (auto &r : rec[u]) { removeOne(users[r.a], u); if (r.b != r.a) removeOne(users[r.b], u); }
        rec[u].clear(); users[u].clear();
        pres[u] = 0; vm.erase(w);
        int p = ppos[u], last = plist.back(); plist[p] = last; ppos[last] = p; plist.pop_back();
        freeSl.push_back(u);
        if (!isS[u]) nonStart--;
        PEnt *e = pt.get(w); if (e && e->cnt >= minrel) candAdd(e);
    }

    // ---- rho 고정점 ----
    vector<int> wq; vector<char> inq;
    bool relax(int v) {
        u64 tmp[WMAX]; for (int k = 0; k < W; k++) tmp[k] = 0;
        for (auto &r : rec[v]) { const u64 *a = R(r.a), *b = R(r.b); for (int k = 0; k < W; k++) tmp[k] |= a[k] & b[k]; }
        tmp[v >> 6] &= ~(1ULL << (v & 63));
        u64 *cur = R(v); bool ch = false;
        for (int k = 0; k < W; k++) if (tmp[k] != cur[k]) { ch = true; cur[k] = tmp[k]; }
        return ch;
    }
    void runQueue() {
        for (size_t i = 0; i < wq.size(); i++) {
            int v = wq[i]; inq[v] = 0;
            if (!pres[v] || isS[v]) continue;
            if (relax(v)) for (int u : users[v]) if (!inq[u] && pres[u]) { inq[u] = 1; wq.push_back(u); }
            if (wq.size() > (1u << 20)) { // 메모리 보호: 앞부분을 버린다
                wq.erase(wq.begin(), wq.begin() + i + 1); i = (size_t)-1;
            }
        }
        wq.clear();
    }
    void rhoFull() {
        nRhoFull++;
        vector<int> ord; ord.reserve(plist.size());
        for (int v : plist) {
            u64 *r = R(v);
            if (isS[v]) for (int k = 0; k < W; k++) r[k] = ~0ULL;
            else { for (int k = 0; k < W; k++) r[k] = 0; ord.push_back(v); }
        }
        sort(ord.begin(), ord.end(), [&](int a, int b) { return prio[a] < prio[b]; });
        wq.clear(); for (int v : ord) { inq[v] = 1; wq.push_back(v); }
        runQueue();
    }
    void rhoInc(int sw) { u64 *r = R(sw); for (int k = 0; k < W; k++) r[k] = 0; wq.clear(); inq[sw] = 1; wq.push_back(sw); runQueue(); }

    // ---- 삭제 루프 ----
    vector<int> rcands, dl;
    struct RemEnt { u64 v; int slot; double pr; u64 ha, hb; char ho; };
    vector<RemEnt> remLog;
    void undoMove(int sw) {
        if (pres[sw]) deleteVal(sw);
        for (int i = (int)remLog.size() - 1; i >= 0; i--) {
            auto &e = remLog[i]; int s = insertVal(e.v, false, e.slot);
            prio[s] = e.pr; hA[s] = e.ha; hB[s] = e.hb; hOp[s] = e.ho;
        }
        memcpy(rho.data(), rhoSave.data(), rho.size() * sizeof(u64));
    }
    int removalLoop(int prot) {
        int removed = 0;
        while (true) {
            u64 M[WMAX]; for (int k = 0; k < W; k++) M[k] = ~0ULL;
            for (int t : tslots) { const u64 *r = R(t); for (int k = 0; k < W; k++) M[k] &= r[k]; }
            rcands.clear();
            for (int v : plist) if (!isS[v] && !isT[v] && v != prot && bit(M, v)) rcands.push_back(v);
            if (rcands.empty()) { if (prot >= 0 && removed > 0) { prot = -1; continue; } break; }
            int x = rcands[rng() % rcands.size()];
            dl.clear(); for (int v : plist) if (!bit(R(v), x)) dl.push_back(v);
            for (int v : dl) { remLog.push_back(RemEnt{val[v], v, prio[v], hA[v], hB[v], hOp[v]}); deleteVal(v); }
            removed += (int)dl.size();
            if (prot >= 0 && !pres[prot]) prot = -1;
            rhoFull();
        }
        nRemoved += removed;
        return removed;
    }

    // ---- 초기화 ----
    void reinit(const vector<u64> &vals, const vector<double> &pr, const vector<u64> &ha, const vector<u64> &hb, const vector<char> &ho) {
        size_t n0 = S.size() + vals.size();
        cap = (int)(((n0 + 1 + 160) + 63) / 64 * 64); if (cap > WMAX * 64) cap = WMAX * 64;
        W = cap / 64;
        val.assign(cap, 0); pres.assign(cap, 0); isS.assign(cap, 0); isT.assign(cap, 0);
        rec.assign(cap, {}); users.assign(cap, {}); rho.assign((size_t)cap * W, 0); rhoSave.assign((size_t)cap * W, 0);
        ppos.assign(cap, -1); plist.clear(); freeSl.clear(); for (int i = cap - 1; i >= 1; i--) freeSl.push_back(i);
        prio.assign(cap, 0); hA.assign(cap, 0); hB.assign(cap, 0); hOp.assign(cap, 0); inq.assign(cap, 0);
        vm.init(cap); pt.init((size_t)cap * cap * 3); cand.clear(); nonStart = 0;
        for (size_t i = 0; i < S.size(); i++) { int s = insertVal(S[i], true); prio[s] = -1e9 + (double)i; }
        for (size_t i = 0; i < vals.size(); i++) {
            if (vm.get(vals[i]) >= 0) continue;
            int s = insertVal(vals[i], false); prio[s] = pr[i]; hA[s] = ha[i]; hB[s] = hb[i]; hOp[s] = ho[i];
        }
        tslots.clear(); for (u64 t : T) { int s = vm.get(t); if (s < 0) { fprintf(stderr, "목표값 %llu 없음\n", t); exit(4); } tslots.push_back(s); }
        rhoFull();
        for (int v : plist) if (!bit(R(v), 0)) { fprintf(stderr, "초기 상태에서 유도 안 되는 값 %llu\n", val[v]); exit(4); }
    }
    void maybeRebuildPT() {
        if (pt.used * 10 < pt.s.size() * 6) return;
        size_t live = 0; for (auto &e : pt.s) if (e.key && e.cnt > 0) live++;
        pt.init(max(live * 3, (size_t)plist.size() * plist.size() * 3)); cand.clear();
        for (size_t i = 0; i < plist.size(); i++) for (size_t j = i; j < plist.size(); j++) pairResults(val[plist[i]], val[plist[j]], [&](u64 r) { pairInc(r); });
    }

    // ---- 프로그램으로 되돌리기 ----
    vector<int> cpos_, corder, crc, clast;
    vector<char> cem;
    int schedule() {   // 우선순위 목록 스케줄. 반환: 내보낸 값 수 (실패하면 -1)
        cpos_.assign(cap, INT_MIN); cem.assign(cap, 0); crc.assign(cap, -1); corder.clear();
        vector<char> inh(cap, 0);
        for (int v : plist) if (isS[v]) { cem[v] = 1; cpos_[v] = -1; }
        priority_queue<pair<double, int>, vector<pair<double, int>>, greater<pair<double, int>>> pq;
        auto ready = [&](int v) { for (auto &r : rec[v]) if (cem[r.a] && cem[r.b]) return true; return false; };
        for (int v : plist) if (!isS[v] && ready(v)) { inh[v] = 1; pq.push({prio[v], v}); }
        int k = 0;
        while (!pq.empty()) {
            int v = pq.top().second; pq.pop();
            if (cem[v]) continue;
            int best = -1; long bs = LONG_MIN;
            for (int i = 0; i < (int)rec[v].size(); i++) {
                auto &r = rec[v][i]; if (!cem[r.a] || !cem[r.b]) continue;
                if (r.op == hOp[v] && val[r.a] == hA[v] && val[r.b] == hB[v]) { best = i; break; }
                long sc = (long)min(cpos_[r.a], cpos_[r.b]) * 4096 + max(cpos_[r.a], cpos_[r.b]);
                if (sc > bs) { bs = sc; best = i; }
            }
            crc[v] = best; cem[v] = 1; cpos_[v] = k++; corder.push_back(v);
            for (int u : users[v]) if (pres[u] && !cem[u] && !inh[u] && ready(u)) { inh[u] = 1; pq.push({prio[u], u}); }
        }
        if (k != nonStart) return -1;
        return k;
    }
    void dceOrder() {   // 목표에서 닿지 않는 값을 뺀다
        vector<char> need(cap, 0);
        for (int t : tslots) need[t] = 1;
        for (int i = (int)corder.size() - 1; i >= 0; i--) { int v = corder[i]; if (!need[v]) continue; auto &r = rec[v][crc[v]]; need[r.a] = 1; need[r.b] = 1; }
        vector<int> o2; for (int v : corder) if (need[v]) o2.push_back(v); else cpos_[v] = INT_MIN;
        if (o2.size() != corder.size()) { corder.swap(o2); for (size_t i = 0; i < corder.size(); i++) cpos_[corder[i]] = (int)i; }
    }
    void rechoose() {   // 순서는 그대로 두고 재료 수명을 덜 늘리는 조리법으로 바꾼다
        for (int pass = 0; pass < 2; pass++) {
            vector<int> l1(cap, INT_MIN), l2(cap, INT_MIN);
            auto addUse = [&](int a, int p) { if (p == l1[a]) return; if (p > l1[a]) { l2[a] = l1[a]; l1[a] = p; } else if (p > l2[a]) l2[a] = p; };
            for (int v : corder) { auto &r = rec[v][crc[v]]; addUse(r.a, cpos_[v]); addUse(r.b, cpos_[v]); }
            bool any = false;
            for (int v : corder) {
                if (rec[v].size() < 2) continue;
                int p = cpos_[v];
                auto ext = [&](int a) { int lo = (l1[a] == p) ? l2[a] : l1[a]; int d = isS[a] ? -1 : cpos_[a]; if (lo < d) lo = d; return p > lo ? p - lo : 0; };
                int best = crc[v]; long bc;
                { auto &r = rec[v][crc[v]]; bc = ext(r.a) + (r.b != r.a ? ext(r.b) : 0); }
                for (int i = 0; i < (int)rec[v].size(); i++) {
                    auto &r = rec[v][i];
                    if (cpos_[r.a] == INT_MIN || cpos_[r.b] == INT_MIN || cpos_[r.a] >= p || cpos_[r.b] >= p) continue;
                    long c = ext(r.a) + (r.b != r.a ? ext(r.b) : 0);
                    if (c < bc) { bc = c; best = i; }
                }
                if (best != crc[v]) { crc[v] = best; any = true; }
            }
            if (!any) break;
            dceOrder();
        }
    }
    long measure(int &peak, long &over) {
        clast.assign(cap, -1);
        for (size_t T_ = 0; T_ < corder.size(); T_++) { auto &r = rec[corder[T_]][crc[corder[T_]]]; clast[r.a] = (int)T_; clast[r.b] = (int)T_; }
        int live = 0; for (int v : plist) if (isS[v] && clast[v] >= 0) live++;
        long cost = 0; over = 0; peak = 0;
        for (size_t T_ = 0; T_ < corder.size(); T_++) {
            int v = corder[T_]; auto &r = rec[v][crc[v]];
            if (clast[r.a] == (int)T_) live--;
            if (r.b != r.a && clast[r.b] == (int)T_) live--;
            int need = live + 1; if (need > peak) peak = need;
            cost += need; if (need > nreg) over += need - nreg;
            if (clast[v] >= 0) live++;
        }
        return cost;
    }
    bool evalOrder(int &len, long &over) {
        if (schedule() < 0) return false;
        dceOrder(); rechoose();
        int pk; measure(pk, over); len = (int)corder.size();
        return true;
    }
    bool emitProg(vector<array<int, 4>> &prog) {
        clast.assign(cap, -1);
        for (size_t T_ = 0; T_ < corder.size(); T_++) { auto &r = rec[corder[T_]][crc[corder[T_]]]; clast[r.a] = (int)T_; clast[r.b] = (int)T_; }
        vector<int> regof(cap, -1), freeList;
        for (int r = nreg - 1; r >= ns; r--) freeList.push_back(r);
        for (int i = ns - 1; i >= 0; i--) { int s = vm.get(S[i]); if (s >= 0 && clast[s] >= 0 && regof[s] < 0) regof[s] = i; else freeList.push_back(i); }
        prog.clear();
        for (size_t T_ = 0; T_ < corder.size(); T_++) {
            int v = corder[T_]; auto &r = rec[v][crc[v]];
            int ra = regof[r.a], rb = regof[r.b];
            if (ra < 0 || rb < 0) return false;
            if (clast[r.a] == (int)T_) freeList.push_back(ra);
            if (r.b != r.a && clast[r.b] == (int)T_) freeList.push_back(rb);
            if (freeList.empty()) return false;
            int rd = freeList.back(); freeList.pop_back();
            prog.push_back({(int)r.op, ra, rb, rd}); regof[v] = rd;
            if (clast[v] < 0) freeList.push_back(rd);
        }
        return true;
    }
    // 성공하면 prog 에 프로그램, prio 와 조리법 힌트를 새 순서로 고친다
    bool compile(vector<array<int, 4>> &prog, int iters) {
        double tc = elapsed(); nCompile++;
        int len; long over;
        bool ok = evalOrder(len, over); long over0 = over;
        if (ok && over > 0 && iters > 0) {
            normal_distribution<double> g(0.0, max(5.0, plist.size() / 8.0));
            vector<int> nsv; for (int v : plist) if (!isS[v]) nsv.push_back(v);
            // 우선순위를 지금 순서의 자리로 맞춘다
            for (size_t i = 0; i < corder.size(); i++) prio[corder[i]] = (double)i;
            long bestOver = over;
            for (int it = 0; it < iters && bestOver > 0; it++) {
                int v = nsv[rng() % nsv.size()]; double keep = prio[v]; prio[v] += g(rng);
                long o2; int l2;
                if (!evalOrder(l2, o2) || o2 > bestOver) { prio[v] = keep; continue; }
                bestOver = o2;
            }
            ok = evalOrder(len, over) && over == 0;
            if (trace >= 2) fprintf(stderr, "C set %d len %d over0 %ld best %ld\n", nonStart, len, over0, bestOver);
        }
        ok = ok && over == 0 && emitProg(prog);
        if (ok) {
            for (size_t i = 0; i < corder.size(); i++) { int v = corder[i]; prio[v] = (double)i; auto &r = rec[v][crc[v]]; hA[v] = val[r.a]; hB[v] = val[r.b]; hOp[v] = r.op; }
        } else nCompileFail++;
        tCompile += elapsed() - tc;
        return ok;
    }
    void saveBest() {
        bestVals.clear(); bestPrio.clear(); bestHA.clear(); bestHB.clear(); bestHOp.clear();
        for (int v : corder) { bestVals.push_back(val[v]); bestPrio.push_back(prio[v]); bestHA.push_back(hA[v]); bestHB.push_back(hB[v]); bestHOp.push_back(hOp[v]); }
    }
    void tryBest() {
        if (nonStart >= bestLen) return;
        if (tCompile > compileShare * elapsed() + 0.5) return;
        vector<array<int, 4>> prog;
        if (compile(prog, repairIters) && (int)prog.size() < bestLen) {
            bestLen = (int)prog.size(); bestProg.swap(prog); saveBest(); lastBestT = elapsed();
            if (trace) fprintf(stderr, "T %.2f best %d set %d moves %ld\n", elapsed(), bestLen, nonStart, nMove);
        }
    }

    // ---- 이동 ----
    void setNewPrio(int sw) {
        double best = 1e300; int bi = -1;
        for (int i = 0; i < (int)rec[sw].size(); i++) { auto &r = rec[sw][i]; double m = max(prio[r.a], prio[r.b]); if (m < best) { best = m; bi = i; } }
        prio[sw] = (bi >= 0 ? best : 0) + 0.5;
        if (bi >= 0) { auto &r = rec[sw][bi]; hA[sw] = val[r.a]; hB[sw] = val[r.b]; hOp[sw] = rec[sw][bi].op; } else hOp[sw] = 0;
    }
    void move(double pu) {
        nMove++;
        if (cand.empty() || freeSl.empty()) { nNoCand++; return; }
        candSum += (long)cand.size();
        maybeRebuildPT();
        u64 w = cand[rng() % cand.size()];
        int old = nonStart;
        memcpy(rhoSave.data(), rho.data(), rho.size() * sizeof(u64));
        remLog.clear();
        int sw = insertVal(w, false);
        setNewPrio(sw);
        rhoInc(sw);
        int removed = removalLoop(sw);
        if (nonStart > old) {
            if (unif() < pu) { nGrow++; return; }
            deleteVal(sw); memcpy(rho.data(), rhoSave.data(), rho.size() * sizeof(u64)); nRej++; return;
        }
        if (pres[sw]) {
            nNull++;   // w 가 남은 이동 (실제로 값이 바뀐 이동)
            if (placeMode == 1 && !remLog.empty()) { double m = 1e300; for (auto &e : remLog) m = min(m, e.pr); prio[sw] = m; }
            if (regMode) {
                int len; long over;
                bool ok = evalOrder(len, over);
                if (!ok || over > rslack) { undoMove(sw); nRegRej++; return; }
                for (size_t i = 0; i < corder.size(); i++) { int v = corder[i]; prio[v] = (double)i; auto &r = rec[v][crc[v]]; hA[v] = val[r.a]; hB[v] = val[r.b]; hOp[v] = r.op; }
            }
            if (probe > 0 && nNull % probe == 0) {
                int len; long over; int pk = 0; bool ok = evalOrder(len, over);
                if (ok) { measure(pk, over); }
                fprintf(stderr, "P t %.1f set %d len %d over %ld peak %d\n", elapsed(), nonStart, len, over, pk);
            }
        }
        if (nonStart < old) nImp++; else nNeu++;
        if (nonStart < bestSet) bestSet = nonStart;
        tryBest();
    }

    // ---- 단순 구현과 대조 ----
    bool naiveDerive(int excl, vector<char> &der) {   // excl 을 뺀 V 에서 S 로부터 닫힘
        der.assign(cap, 0);
        vector<int> dlist; for (int v : plist) if (isS[v]) { der[v] = 1; dlist.push_back(v); }
        bool ch = true;
        while (ch) {
            ch = false;
            size_t n = dlist.size();
            for (size_t i = 0; i < n; i++) for (size_t j = 0; j < n; j++) {
                u64 a = val[dlist[i]], b = val[dlist[j]]; u64 rs[4]; int nr = 0;
                if (a + b <= L) rs[nr++] = a + b;
                if (a > b) rs[nr++] = a - b;
                if ((u128)a * b <= L) rs[nr++] = a * b;
                if (b >= 1 && a % b == 0) rs[nr++] = a / b;
                for (int k = 0; k < nr; k++) { int s = vm.get(rs[k]); if (s >= 0 && s != excl && !der[s]) { der[s] = 1; dlist.push_back(s); ch = true; } }
            }
        }
        return true;
    }
    void selfCheck() {
        nCheck++;
        // 조리법 목록
        for (int v : plist) {
            if (isS[v]) continue;
            set<tuple<int, int, char>> A, B;
            for (auto &r : rec[v]) { int a = r.a, b = r.b; if ((r.op == '+' || r.op == '*') && val[a] > val[b]) swap(a, b); A.insert({a, b, r.op}); }
            for (int a : plist) for (int b : plist) {
                if (a == v || b == v) continue;
                u64 x = val[a], y = val[b];
                if (x <= y && x + y == val[v]) B.insert({a, b, '+'});
                if (x > y && x - y == val[v]) B.insert({a, b, '-'});
                if (x <= y && (u128)x * y == val[v]) B.insert({a, b, '*'});
                if (y >= 1 && x % y == 0 && x / y == val[v]) B.insert({a, b, '/'});
            }
            if (A != B) { fprintf(stderr, "CHECK 조리법 불일치 v=%llu (%zu vs %zu)\n", val[v], A.size(), B.size()); exit(9); }
        }
        // 쌍 표
        unordered_map<u64, int> cnt;
        for (size_t i = 0; i < plist.size(); i++) for (size_t j = i; j < plist.size(); j++) pairResults(val[plist[i]], val[plist[j]], [&](u64 r) { cnt[r]++; });
        size_t nc = 0;
        for (auto &kv : cnt) { PEnt *e = pt.get(kv.first); if (!e || e->cnt != kv.second) { fprintf(stderr, "CHECK 쌍 표 불일치 %llu\n", kv.first); exit(9); } if (kv.second >= minrel && vm.get(kv.first) < 0) { nc++; if (e->cpos < 0) { fprintf(stderr, "CHECK 후보 빠짐\n"); exit(9); } } }
        for (auto &e : pt.s) if (e.key && e.cnt > 0 && !cnt.count(e.key)) { fprintf(stderr, "CHECK 쌍 표 여분\n"); exit(9); }
        if (nc != cand.size()) { fprintf(stderr, "CHECK 후보 수 %zu vs %zu\n", nc, cand.size()); exit(9); }
        // rho
        vector<char> der;
        naiveDerive(-1, der);
        for (int v : plist) if (!der[v] || !bit(R(v), 0)) { fprintf(stderr, "CHECK 유도 불가 값\n"); exit(9); }
        for (int x : plist) {
            if (isS[x]) continue;
            naiveDerive(x, der);
            for (int v : plist) {
                if (v == x) continue;
                if ((bool)der[v] != bit(R(v), x)) { fprintf(stderr, "CHECK rho 불일치 v=%llu x=%llu naive=%d rho=%d\n", val[v], val[x], der[v], bit(R(v), x)); exit(9); }
            }
            if (bit(R(x), x)) { fprintf(stderr, "CHECK rho 자기 비트\n"); exit(9); }
        }
    }
};

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: walk <in> <seconds> [key=value ...]\n"); return 2; }
    FILE *f = fopen(argv[1], "r"); if (!f) { perror("open"); return 2; }
    Walk Wk; Wk.secs = atof(argv[2]); u64 seed = 1;
    for (int i = 3; i < argc; i++) {
        string kv = argv[i]; size_t e = kv.find('='); if (e == string::npos) { fprintf(stderr, "인자 형식: key=value (%s)\n", argv[i]); return 2; }
        string k = kv.substr(0, e); double v = atof(kv.c_str() + e + 1);
        if (k == "seed") seed = (u64)v; else if (k == "pu0") Wk.pu0 = v; else if (k == "pu1") Wk.pu1 = v; else if (k == "minrel") Wk.minrel = (int)v;
        else if (k == "repair") Wk.repairIters = (int)v; else if (k == "back") Wk.back = v; else if (k == "check") Wk.checkEvery = (int)v; else if (k == "trace") Wk.trace = (int)v;
        else if (k == "cshare") Wk.compileShare = v; else if (k == "probe") Wk.probe = (int)v; else if (k == "probe2") Wk.probe2 = (int)v;
        else if (k == "reg") Wk.regMode = (int)v; else if (k == "rslack") Wk.rslack = (long)v; else if (k == "place") Wk.placeMode = (int)v;
        else { fprintf(stderr, "모르는 인자 %s\n", k.c_str()); return 2; }
    }
    Wk.rng.seed(seed);
    int nt, nprog; u64 lim;
    if (fscanf(f, "%llu %d %d %d %d", &lim, &Wk.nreg, &Wk.ns, &nt, &nprog) != 5) return 2;
    Wk.L = lim;
    for (int i = 0; i < Wk.ns; i++) { u64 v; if (fscanf(f, "%llu", &v) != 1) return 2; Wk.S.push_back(v); }
    unordered_set<u64> sset(Wk.S.begin(), Wk.S.end());
    for (int i = 0; i < nt; i++) { u64 v; if (fscanf(f, "%llu", &v) != 1) return 2; if (!sset.count(v) && !Wk.tset.count(v)) { Wk.tset.insert(v); Wk.T.push_back(v); } }
    vector<u64> reg(Wk.nreg, 0); for (int i = 0; i < Wk.ns; i++) reg[i] = Wk.S[i];
    vector<u64> vals, ha, hb; vector<char> ho; vector<double> pr; unordered_set<u64> seen(sset);
    vector<array<int, 4>> inProg;
    for (int i = 0; i < nprog; i++) {
        char op; int a, b, d; if (fscanf(f, " %c %d %d %d", &op, &a, &b, &d) != 4) return 2;
        inProg.push_back({(int)op, a, b, d});
        u64 X = reg[a], Y = reg[b], v;
        switch (op) { case '+': v = X + Y; break; case '-': v = X - Y; break; case '*': v = X * Y; break; default: v = X / Y; }
        reg[d] = v;
        if (seen.insert(v).second) { vals.push_back(v); pr.push_back((double)i); ha.push_back(X); hb.push_back(Y); ho.push_back(op); }
    }
    fclose(f);
    Wk.bestLen = nprog; Wk.bestProg = inProg;
    Wk.reinit(vals, pr, ha, hb, ho);
    int startSet = Wk.nonStart;
    Wk.removalLoop(-1);
    {
        vector<array<int, 4>> prog;
        if (Wk.compile(prog, Wk.repairIters)) {
            if ((int)prog.size() < Wk.bestLen) { Wk.bestLen = (int)prog.size(); Wk.bestProg.swap(prog); }
            Wk.saveBest();
        } else {
            fprintf(stderr, "초기 컴파일 실패 (집합 %d)\n", Wk.nonStart);
            Wk.saveBest();
        }
    }
    Wk.bestSet = Wk.nonStart;
    int initSet = Wk.nonStart;
    Wk.t0 = chrono::steady_clock::now(); Wk.tCompile = 0;
    double lastTrace = 0;
    while (true) {
        double t = Wk.elapsed(); if (t >= Wk.secs) break;
        double pu = Wk.pu0 * pow(Wk.pu1 / Wk.pu0, min(1.0, t / Wk.secs));
        for (int k = 0; k < 64; k++) {
            Wk.move(pu);
            if (Wk.checkEvery > 0 && Wk.nMove % Wk.checkEvery == 0) Wk.selfCheck();
        }
        if (Wk.back > 0 && t - Wk.lastBestT > Wk.back && Wk.nonStart > Wk.bestLen && !Wk.bestVals.empty()) {
            Wk.reinit(Wk.bestVals, Wk.bestPrio, Wk.bestHA, Wk.bestHB, Wk.bestHOp); Wk.lastBestT = t; Wk.nBack++;
        }
        if (Wk.trace && t - lastTrace > 5) { lastTrace = t; fprintf(stderr, "T %.1f cur %d bestset %d best %d moves %ld cand %zu\n", t, Wk.nonStart, Wk.bestSet, Wk.bestLen, Wk.nMove, Wk.cand.size()); }
    }
    double tt = Wk.elapsed();
    printf("LEN %zu\n", Wk.bestProg.size());
    for (auto &p : Wk.bestProg) printf("%c %d %d %d\n", (char)p[0], p[1], p[2], p[3]);
    fprintf(stderr, "start %d initset %d/%d end %d bestset %d cur %d moves %ld mps %.0f neu %ld imp %ld grow %ld rej %ld null %ld nocand %ld cand %.0f removed %ld compile %ld fail %ld tcomp %.2f back %ld rhofull %ld check %ld regrej %ld\n",
            nprog, startSet, initSet, Wk.bestLen, Wk.bestSet, Wk.nonStart, Wk.nMove, Wk.nMove / max(tt, 1e-9), Wk.nNeu, Wk.nImp, Wk.nGrow, Wk.nRej, Wk.nNull, Wk.nNoCand,
            Wk.nMove ? (double)Wk.candSum / Wk.nMove : 0.0, Wk.nRemoved, Wk.nCompile, Wk.nCompileFail, Wk.tCompile, Wk.nBack, Wk.nRhoFull, Wk.nCheck, Wk.nRegRej);
    return 0;
}
