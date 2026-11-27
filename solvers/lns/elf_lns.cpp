// elf_lns: 값 그래프(SSA DAG) 위의 재합성 탐색.
//
// 이동 1 (노드 재유도): 노드 하나(목표값 또는 중간값)를 골라 그 노드만을 위해 존재하던 조상(전용 원뿔)을 떼어 내고,
//   그 노드의 후손이 아닌 나머지 모든 값을 재료로 같은 값을 더 적은(또는 같은) 명령으로 다시 만든다.
// 이동 2 (중간값 제거): 여러 곳에서 쓰이는 중간값 x 를 금지하고, x 를 쓰던 노드들을 x 없이 다시 만든다.
//   늘어난 명령 수가 x 와 그 전용 조상의 수보다 적으면 채택한다.
// 바뀐 그래프는 위상 정렬 후 레지스터 48개로 실제 배정이 되는 경우에만 채택한다.
//
// 사용: elf_lns <입력> <초> [key=value ...]
//   seed=1 peq=0.5 cap=500 j3=1 trace=0 schedinit=3000 schedevery=40 repair=400 pelim=0.25 maxb=7 elimcons=4
// 입력:  limit nreg ns nt nprog / 시작값들 / 목표값들 / nprog 줄의 "op a b d"
// 출력(stdout): "LEN n" 다음에 n 줄의 "op a b d".  통계는 stderr.
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long u64;
typedef unsigned __int128 u128;
static const int INF = 1 << 20;
static const u64 MULMAX = 1ULL << 17;   // 나머지 표를 만드는 곱수의 상한
static const int SMALLMAX = 8192;       // 뿌리에서 곱수로 써 보는 S1 값의 상한
static const int SH = 5;                // 근처값 이동: 나머지가 v >> SH 미만일 때만 재귀

struct Node { u64 val; int a, b; char op; char alive; char req; };
static inline u64 hmix(u64 x) { x ^= x >> 31; x *= 0x9E3779B97F4A7C15ULL; x ^= x >> 29; x *= 0xBF58476D1CE4E5B9ULL; x ^= x >> 32; return x; }
static const char OPC[4] = {'+', '-', '*', '/'};

struct Ent { u64 key; int a; int b; };                 // a < 0 이면 빈 칸
struct Table {
    vector<Ent> s; u64 mask = 0; size_t cnt = 0;
    void init(size_t want) { size_t n = 64; while (n < want) n <<= 1; s.assign(n, Ent{0, -1, 0}); mask = n - 1; cnt = 0; }
    bool full() const { return cnt * 10 > s.size() * 7; }
    bool ins(u64 key, int a, int b, int cap) {
        u64 h = hmix(key) & mask; int dup = 0;
        while (s[h].a >= 0) { if (s[h].key == key && ++dup >= cap) return false; h = (h + 1) & mask; }
        s[h] = Ent{key, a, b}; cnt++; return true;
    }
};

enum Form : unsigned char { F_NONE, F_S1, F_L2, F_M, F_MA, F_MS, F_MAS, F_MSS, F_NP, F_NM, F_NPS, F_NMS, F_A, F_RS, F_N1, F_M1, F_MA1, F_MS1, F_J3 };
struct Rec { u64 v; int stamp; int cost; int lb; unsigned char form; char s1done, l2done, j3done; int p1, p2, p3; u64 child; };
struct Step { char op; int x, y; u64 val; };
struct Snap { vector<Node> nd; vector<int> order; vector<double> prio; };

struct Solver {
    u64 L; int nreg, ns;
    vector<Node> nd;
    vector<int> order;
    vector<double> prio;
    vector<int> uses, forb, lastUse, indeg;
    vector<char> ban;
    vector<vector<int>> cons;
    int stamp = 1;
    Table VM, S1, RS;
    vector<int> mults, smallS1;
    vector<pair<u64, int>> SV;          // (S1 값, 칸) 정렬 목록. 표를 다시 만들 때만 갱신한다
    mt19937_64 rng;
    chrono::steady_clock::time_point tStart = chrono::steady_clock::now();
    // 설정
    double pEq = 1.0, pElim = 0.25, pRuin = 0.0, pUp = 0.0; int ruinK = 3, ruinSel = 0, ruinOrd = 0, upMax = 2;
    double pAware = 0.0; bool awareNow = false; int regMargin = 2;
    int dfsMaxB = 5, beamW = 16; long nBeam = 0;
    int bestLen = INF; vector<array<int, 4>> bestProg;     // 나빠지는 이동을 허용할 때를 위한 최선 기록
    Snap bestSnap; double lastBestTime = 0, lastKickTime = 0; double kickEvery = 0; int kickK = 24, kickSlack = 6; long nKick = 0;
    bool inExc = false; int lcap = -1, lmode = 0; double lcapT = 3, pWalk = 0.3, cycleStart = 0; long nWalk = 0, nWalkUp = 0, nCycle = 0;
    void noteBest() { if (!inExc && (int)order.size() < bestLen) { vector<array<int, 4>> pr; if (regs(order, &pr)) { bestLen = (int)order.size(); bestProg.swap(pr); lastBestTime = elapsed(); if (kickEvery > 0 || lcap > 0) { bestSnap.nd = nd; bestSnap.order = order; bestSnap.prio = prio; } } } }
    // 최선 상태로 돌아간 뒤 크게 허물어 일부러 조금 나빠진 상태에서 다시 시작한다
    void kick() {
        if (!bestSnap.nd.empty() && (int)order.size() > bestLen) { nd = bestSnap.nd; order = bestSnap.order; prio = bestSnap.prio; forb.assign(nd.size(), 0); ban.assign(nd.size(), 0); stamp = 1; snapTaken = false; computeUses(); rebuildTables(); }
        for (int t = 0; t < 30 && !order.empty(); t++) { int x = order[rng() % order.size()]; if (tryRuin(x, kickK, kickSlack)) { nKick++; break; } }
        lastKickTime = elapsed();
    }
    long expCap = 500;
    int useJ3 = 1, trace = 0, schedInit = 3000, schedEvery = 40, schedIters = 150, repairIters = 400, maxBudget = 12, elimCons = 4;
    // 탐색 상태
    vector<pair<u64, int>> ctx;
    static const int MSIZE = 1 << 14;
    vector<Rec> recs; int mstamp = 0, mcount = 0;
    long expansions = 0; bool aborted = false;
    vector<Step> steps; unordered_map<u64, int> built;
    Snap snap; bool snapTaken = false; bool banActive = false;
    int lastDeltaBits = 0; double biasT = 0;       // 같은 비용 이동에서 값의 비트 합이 늘면 exp(-증가/biasT) 확률로만 채택 (0 이면 끔)
    int sinceRebuild = 0, sinceSched = 0; long gen = 0;
    // 통계
    long nEval = 0, nImp = 0, nEq = 0, nRegFail = 0, nRegFailImp = 0, nAbort = 0, nMerge = 0, nRepair = 0, nElimTry = 0, nElim = 0, nBiasRej = 0, nRuinTry = 0, nRuin = 0, nRuinEq = 0;

    double elapsed() const { return chrono::duration<double>(chrono::steady_clock::now() - tStart).count(); }
    double unif() { return uniform_real_distribution<double>(0, 1)(rng); }
    bool ok(int i) const { return nd[i].alive && forb[i] != stamp && !ban[i]; }
    int inC(u64 v) const {
        u64 h = hmix(v) & VM.mask;
        while (VM.s[h].a >= 0) { if (VM.s[h].key == v) { int i = VM.s[h].a; if (ok(i)) return i; } h = (h + 1) & VM.mask; }
        return -1;
    }
    bool slotOk(int h) const { return ok(S1.s[h].a) && ok(S1.s[h].b >> 3); }
    int s1find(u64 v) const {
        u64 h = hmix(v) & S1.mask;
        while (S1.s[h].a >= 0) { if (S1.s[h].key == v && slotOk((int)h)) return (int)h; h = (h + 1) & S1.mask; }
        return -1;
    }
    int resfind(int cid, u64 r, u64 maxd) const {
        u64 key = ((u64)cid << 20) | r, h = hmix(key) & RS.mask;
        while (RS.s[h].a >= 0) { if (RS.s[h].key == key) { int d = RS.s[h].a; if (ok(d) && nd[d].val <= maxd) return d; } h = (h + 1) & RS.mask; }
        return -1;
    }
    void s1ins(u64 key, int a, int b, int op) {
        if (S1.ins(key, a, (b << 3) | op, 3) && key <= (u64)SMALLMAX && smallS1[key] < 0) smallS1[key] = 1;
    }
    void s1pair(int i, int j) {
        u64 x = nd[i].val, y = nd[j].val; int a = i, b = j;
        if (x > y) { swap(x, y); swap(a, b); }
        if (x + y <= L) s1ins(x + y, a, b, 0);
        if (y > x) s1ins(y - x, b, a, 1);
        if (x >= 2) {
            u128 p = (u128)x * y; if (p <= L) s1ins((u64)p, a, b, 2);
            if (y > x && y % x == 0) s1ins(y / x, b, a, 3);
        }
    }
    void resins(int cid, int did) {
        u64 m = nd[cid].val, r = nd[did].val % m; if (!r) return;
        RS.ins(((u64)cid << 20) | r, did, 0, 3);
    }
    static bool isMult(u64 v) { return v >= 2 && v <= MULMAX; }
    void aliveList(vector<int> &al) const { al.clear(); for (int i = 0; i < ns; i++) al.push_back(i); for (int n : order) al.push_back(n); }

    // 죽은 노드를 버리고 번호를 다시 매긴 뒤 표를 전부 다시 만든다. 노드 번호가 바뀐다.
    void rebuildTables() {
        vector<int> remap(nd.size(), -1); vector<Node> nn; vector<double> np;
        for (int i = 0; i < ns; i++) { remap[i] = i; nn.push_back(nd[i]); np.push_back(prio[i]); }
        for (int n : order) { remap[n] = (int)nn.size(); nn.push_back(nd[n]); np.push_back(prio[n]); }
        for (size_t i = ns; i < nn.size(); i++) { nn[i].a = remap[nn[i].a]; nn[i].b = remap[nn[i].b]; }
        for (int &n : order) n = remap[n];
        nd.swap(nn); prio.swap(np);
        forb.assign(nd.size(), 0); ban.assign(nd.size(), 0); stamp = 1;
        computeUses();
        vector<int> al; aliveList(al); size_t n = al.size();
        VM.init(n * 4 + 256);
        for (int i : al) VM.ins(nd[i].val, i, 0, 8);
        S1.init((n * (n + 1) / 2 * 4 + 30 * 8 * n * 4) * 3 / 2);
        smallS1.assign(SMALLMAX + 1, -1);
        s1ins(1, 0, 0, 3);
        for (size_t i = 0; i < n; i++) for (size_t j = i; j < n; j++) s1pair(al[i], al[j]);
        mults.clear(); for (int i : al) if (isMult(nd[i].val)) mults.push_back(i);
        RS.init((mults.size() + 60) * (n + 60) * 2 + 1024);
        for (int c : mults) for (int d : al) resins(c, d);
        SV.clear();
        if (useJ3) { for (size_t h = 0; h < S1.s.size(); h++) if (S1.s[h].a >= 0) SV.push_back({S1.s[h].key, (int)h}); sort(SV.begin(), SV.end()); }
        sinceRebuild = 0; gen++;
    }
    void addToTables(int id) {
        vector<int> al; aliveList(al);
        VM.ins(nd[id].val, id, 0, 8);
        for (int j : al) s1pair(id, j);
        for (int c : mults) if (nd[c].alive) resins(c, id);
        if (isMult(nd[id].val)) { mults.push_back(id); for (int d : al) resins(id, d); }
    }

    // ---- 그래프 보조 -----------------------------------------------------
    void computeUses() {
        size_t N = nd.size();
        uses.assign(N, 0); if (cons.size() < N) cons.resize(N);
        for (int i = 0; i < ns; i++) cons[i].clear();
        for (int n : order) cons[n].clear();
        for (int n : order) { int a = nd[n].a, b = nd[n].b; uses[a]++; uses[b]++; cons[a].push_back(n); if (b != a) cons[b].push_back(n); }
    }
    // order 에서 죽은 노드를 빼고 새 노드를 붙인다 (위상 순서는 schedule 이 다시 잡는다)
    void refreshOrder(const vector<int> &added) {
        vector<int> o2; for (int n : order) if (nd[n].alive) o2.push_back(n);
        for (int id : added) o2.push_back(id);
        order.swap(o2); computeUses();
    }
    void ensureSnap() { if (!snapTaken) { snap.nd = nd; snap.order = order; snap.prio = prio; snapTaken = true; } }
    void restoreSnap() { nd = snap.nd; order = snap.order; prio = snap.prio; forb.resize(nd.size()); ban.assign(nd.size(), 0); computeUses(); snapTaken = false; }
    // 우선순위 순서를 지키는 위상 정렬
    bool schedule(vector<int> &out) {
        size_t N = nd.size(); indeg.assign(N, 0);
        priority_queue<pair<double, int>, vector<pair<double, int>>, greater<pair<double, int>>> pq;
        for (int n : order) { int a = nd[n].a, b = nd[n].b, d = 0; if (a >= ns) d++; if (b >= ns && b != a) d++; indeg[n] = d; if (!d) pq.push({prio[n], n}); }
        out.clear();
        while (!pq.empty()) {
            int n = pq.top().second; pq.pop(); out.push_back(n);
            for (int c : cons[n]) if (--indeg[c] == 0) pq.push({prio[c], c});
        }
        return out.size() == order.size();
    }
    // 레지스터 배정. prog 가 주어지면 명령을 채운다.
    bool regs(const vector<int> &ord, vector<array<int, 4>> *prog) {
        size_t N = nd.size(); lastUse.assign(N, -1);
        for (size_t T = 0; T < ord.size(); T++) { lastUse[nd[ord[T]].a] = (int)T; lastUse[nd[ord[T]].b] = (int)T; }
        vector<int> regof; vector<int> freeList;
        if (prog) { regof.assign(N, -1); prog->clear(); }
        int freecnt = 0;
        for (int r = nreg - 1; r >= ns; r--) { freecnt++; if (prog) freeList.push_back(r); }
        for (int i = ns - 1; i >= 0; i--) { if (lastUse[i] >= 0) { if (prog) regof[i] = i; } else { freecnt++; if (prog) freeList.push_back(i); } }
        for (size_t T = 0; T < ord.size(); T++) {
            int n = ord[T], a = nd[n].a, b = nd[n].b, ra = 0, rb = 0;
            if (prog) { ra = regof[a]; rb = regof[b]; }
            if (lastUse[a] == (int)T) { freecnt++; if (prog) freeList.push_back(regof[a]); }
            if (b != a && lastUse[b] == (int)T) { freecnt++; if (prog) freeList.push_back(regof[b]); }
            if (!freecnt) return false;
            freecnt--;
            int rd = 0;
            if (prog) { rd = freeList.back(); freeList.pop_back(); prog->push_back({(int)nd[n].op, ra, rb, rd}); regof[n] = rd; }
            if (lastUse[n] < 0) { freecnt++; if (prog) freeList.push_back(rd); }
        }
        return true;
    }
    // 순서의 레지스터 압박: 생존 수 합 + 46 이상인 시점에 벌점. peak 는 필요한 레지스터 수의 최댓값.
    long measure(const vector<int> &ord, int &peak, long *over = nullptr) {
        size_t N = nd.size(); lastUse.assign(N, -1);
        for (size_t T = 0; T < ord.size(); T++) { lastUse[nd[ord[T]].a] = (int)T; lastUse[nd[ord[T]].b] = (int)T; }
        int live = 0; for (int i = 0; i < ns; i++) if (lastUse[i] >= 0) live++;
        long cost = 0, ov = 0; peak = 0;
        for (size_t T = 0; T < ord.size(); T++) {
            int n = ord[T], a = nd[n].a, b = nd[n].b;
            if (lastUse[a] == (int)T) live--;
            if (b != a && lastUse[b] == (int)T) live--;
            int need = live + 1; if (need > peak) peak = need;
            cost += need; if (need >= nreg - 2) cost += 50;
            if (need > nreg) ov += need - nreg;
            if (lastUse[n] >= 0) live++;
        }
        if (over) *over = ov;
        return cost;
    }
    // 그래프는 그대로 두고 실행 순서만 바꿔 레지스터 압박을 줄인다
    void optimizeOrder(int iters) {
        if (order.size() < 4) return;
        int pk; long bc = measure(order, pk);
        normal_distribution<double> g(0.0, 30.0);
        vector<int> sched;
        for (int it = 0; it < iters; it++) {
            int k = order[rng() % order.size()];
            double keep = prio[k]; prio[k] = keep + g(rng);
            if (!schedule(sched)) { prio[k] = keep; continue; }
            int pk2; long c = measure(sched, pk2);
            if (pk2 <= nreg && c <= bc) { bc = c; order = sched; for (size_t i = 0; i < order.size(); i++) prio[order[i]] = (double)i; }
            else prio[k] = keep;
        }
    }
    // 레지스터가 넘치는 순서를 고쳐 본다. 성공하면 sched 에 유효한 순서를 넣는다.
    bool repairOrder(vector<int> &sched, int iters) {
        vector<double> savePrio = prio; vector<int> cur, tmp; int pk; long best, o2;
        if (!schedule(cur)) return false;
        measure(cur, pk, &best);
        normal_distribution<double> g(0.0, 40.0);
        for (int it = 0; it < iters && best > 0; it++) {
            int k = order[rng() % order.size()];
            double keep = prio[k]; prio[k] = keep + g(rng);
            if (!schedule(tmp)) { prio[k] = keep; continue; }
            measure(tmp, pk, &o2);
            if (o2 <= best) { best = o2; cur.swap(tmp); } else prio[k] = keep;
        }
        if (best == 0) { sched = cur; nRepair++; return true; }
        prio = savePrio; return false;
    }

    // ---- 탐색 ------------------------------------------------------------
    Rec *memoGet(u64 v) {
        u64 h = hmix(v) & (MSIZE - 1);
        while (recs[h].stamp == mstamp) { if (recs[h].v == v) return &recs[h]; h = (h + 1) & (MSIZE - 1); }
        if (mcount > MSIZE / 2) { aborted = true; return nullptr; }
        mcount++;
        recs[h] = Rec{v, mstamp, INF, 0, F_NONE, 0, 0, 0, 0, 0, 0, 0};
        return &recs[h];
    }
    bool leaf2(u64 v, Rec *m) {
        size_t n = ctx.size(), st = rng() % n;
        for (size_t k = 0; k < n; k++) {
            auto &pr = ctx[(st + k) % n]; u64 cv = pr.first; int cid = pr.second, e, kind = -1;
            if (v > cv && (e = s1find(v - cv)) >= 0) kind = 0;
            else if (v + cv <= L && (e = s1find(v + cv)) >= 0) kind = 1;
            else if (cv > v && (e = s1find(cv - v)) >= 0) kind = 2;
            else if (cv >= 2 && v % cv == 0 && (e = s1find(v / cv)) >= 0) kind = 3;
            else if (cv >= 2 && (u128)v * cv <= L && (e = s1find(v * cv)) >= 0) kind = 4;
            else if (cv > v && cv % v == 0 && (e = s1find(cv / v)) >= 0) kind = 5;
            if (kind >= 0) { m->form = F_L2; m->p1 = e; m->p2 = cid; m->p3 = kind; return true; }
        }
        return false;
    }
    // v = w1 op w2, 둘 다 S1 값 (명령 3개)
    bool join3(u64 v, Rec *m) {
        size_t n = SV.size(); if (!n) return false;
        {   // 합
            size_t i = 0, j = n - 1;
            while (i <= j && j < n) {
                u64 s = SV[i].first + SV[j].first;
                if (s == v) { if (slotOk(SV[i].second) && slotOk(SV[j].second)) { m->form = F_J3; m->p1 = SV[i].second; m->p2 = SV[j].second; m->p3 = 0; return true; } i++; }
                else if (s < v) i++; else { if (!j) break; j--; }
            }
        }
        {   // 차: w1 - w2 = v
            size_t i = 0, j = 0;
            while (i < n && j < n) {
                u64 a = SV[j].first, c = SV[i].first;
                if (a < c + v) j++;
                else if (a > c + v) i++;
                else { if (slotOk(SV[i].second) && slotOk(SV[j].second)) { m->form = F_J3; m->p1 = SV[j].second; m->p2 = SV[i].second; m->p3 = 1; return true; } i++; }
            }
        }
        for (size_t i = 0; i < n; i++) {   // 곱, 몫
            u64 w = SV[i].first; if (w < 2) continue;
            bool sq = (u128)w * w <= v, mulok = (u128)v * w <= L;
            if (!sq && !mulok) break;
            if (sq && v % w == 0 && slotOk(SV[i].second)) { int e = s1find(v / w); if (e >= 0) { m->form = F_J3; m->p1 = SV[i].second; m->p2 = e; m->p3 = 2; return true; } }
            if (mulok && slotOk(SV[i].second)) { int e = s1find(v * w); if (e >= 0) { m->form = F_J3; m->p1 = e; m->p2 = SV[i].second; m->p3 = 3; return true; } }
        }
        return false;
    }
    int solve(u64 v, int b, int depth) {
        if (inC(v) >= 0) return 0;
        if (b <= 0) return INF;
        Rec *m = memoGet(v); if (!m) return INF;
        if (m->cost <= b) return m->cost;
        if (m->lb >= b) return INF;
        if (!m->s1done) { m->s1done = 1; int e = s1find(v); if (e >= 0) { m->cost = 1; m->form = F_S1; m->p1 = e; return 1; } }
        if (b == 1) { m->lb = 1; return INF; }
        if (!m->l2done) { m->l2done = 1; if (leaf2(v, m)) { m->cost = 2; return 2; } }
        if (b == 2) { m->lb = 2; return INF; }
        if (depth == 0 && useJ3 && !m->j3done) { m->j3done = 1; if (join3(v, m)) { m->cost = 3; return 3; } }
        if (++expansions > expCap) { aborted = true; return INF; }
        int best = INF, lim = b;
        auto tryc = [&](int sc, u64 child, unsigned char form, int p1, int p2, int p3) {
            int rb = lim - sc; if (rb < 0 || child == 0 || child >= v) return;
            int c = solve(child, rb, depth + 1);
            if (c <= rb) { best = sc + c; lim = best - 1; m->form = form; m->p1 = p1; m->p2 = p2; m->p3 = p3; m->child = child; }
        };
        size_t n = ctx.size(), st = rng() % n;
        for (size_t k = 0; k < n && lim >= 3 && !aborted; k++) {
            auto &pr = ctx[(st + k) % n]; u64 cv = pr.first; int cid = pr.second;
            if (cv < 2 || cv >= v) continue;
            u64 q = v / cv, r = v - q * cv;
            if (r == 0) { tryc(1, q, F_M, cid, 0, 0); continue; }
            if (cv <= MULMAX) {
                int d = resfind(cid, r, v - 1);
                if (d >= 0) tryc(2, (v - nd[d].val) / cv, F_MA, cid, d, 0);
                d = resfind(cid, cv - r, L - v);
                if (d >= 0) tryc(2, (v + nd[d].val) / cv, F_MS, cid, d, 0);
                int e = s1find(r); if (e >= 0) tryc(3, q, F_MAS, cid, e, 0);
                if (v + (cv - r) <= L) { e = s1find(cv - r); if (e >= 0) tryc(3, q + 1, F_MSS, cid, e, 0); }
            }
            if (q >= 2 && r < (v >> SH)) {
                int qi = inC(q);
                if (qi >= 0) tryc(2, r, F_NP, cid, qi, 0);
                else { int e = s1find(q); if (e >= 0) tryc(3, r, F_NPS, cid, e, 0); }
            }
            u64 r2 = cv - r;
            if (r2 < (v >> SH) && (u128)(q + 1) * cv <= L) {
                int qi = inC(q + 1);
                if (qi >= 0) tryc(2, r2, F_NM, cid, qi, 0);
                else { int e = s1find(q + 1); if (e >= 0) tryc(3, r2, F_NMS, cid, e, 0); }
            }
        }
        if (lim >= 3 && !aborted) {                       // 가까운 풀 값
            size_t idx = lower_bound(ctx.begin(), ctx.end(), make_pair(v, -1)) - ctx.begin();
            for (int k = 1; k <= 2; k++) if (idx >= (size_t)k) { u64 y = ctx[idx - k].first, r = v - y; if (r < (v >> 3)) tryc(1, r, F_A, ctx[idx - k].second, 0, 0); }
            for (int k = 0; k < 2; k++) if (idx + k < n) { u64 y = ctx[idx + k].first, r = y - v; if (r < (v >> 3)) tryc(1, r, F_RS, ctx[idx + k].second, 0, 0); }
        }
        if (lim >= 3 && !aborted) {                       // 풀 값 둘의 합/차에 가까운 경우
            for (size_t k = 0; k < n && lim >= 3; k++) {
                u64 av = ctx[k].first; int aid = ctx[k].second;
                if (av < v) {
                    u64 w = v - av; size_t j = lower_bound(ctx.begin(), ctx.end(), make_pair(w, -1)) - ctx.begin();
                    for (int t = 0; t < 2; t++) {
                        size_t jj = j + t; if (jj < 1 || jj - 1 >= n) continue; jj--;
                        u64 bv = ctx[jj].first; if (bv > av) continue;      // a >= b 만 본다
                        u64 y = av + bv; if (y > L || y == v) continue;
                        if (y < v) { if (v - y < (v >> SH)) tryc(2, v - y, F_N1, aid, ctx[jj].second, 0); }
                        else if (y - v < (v >> SH)) tryc(2, y - v, F_N1, aid, ctx[jj].second, 2);
                    }
                } else if (av > v) {
                    u64 w = av - v; size_t j = lower_bound(ctx.begin(), ctx.end(), make_pair(w, -1)) - ctx.begin();
                    for (int t = 0; t < 2; t++) {
                        size_t jj = j + t; if (jj < 1 || jj - 1 >= n) continue; jj--;
                        u64 bv = ctx[jj].first; if (bv >= av) continue;
                        u64 y = av - bv; if (y == v) continue;
                        if (y < v) { if (v - y < (v >> SH)) tryc(2, v - y, F_N1, aid, ctx[jj].second, 1); }
                        else if (y - v < (v >> SH)) tryc(2, y - v, F_N1, aid, ctx[jj].second, 3);
                    }
                }
            }
        }
        if (depth <= 1 && lim >= 3 && !aborted) {         // S1 값을 곱수로
            for (int mv = 2; mv <= SMALLMAX && (u64)mv < v && lim >= 3; mv++) {
                if (smallS1[mv] < 0) continue;
                u64 q = v / mv, r = v % mv;
                if (r == 0) { if (inC(mv) >= 0) continue; int e = s1find(mv); if (e >= 0) tryc(2, q, F_M1, e, 0, 0); continue; }
                int d = inC(r), d2 = (v + (mv - r) <= L) ? inC(mv - r) : -1;
                if (d < 0 && d2 < 0) continue;
                if (inC(mv) >= 0) continue;
                int e = s1find(mv); if (e < 0) continue;
                if (d >= 0) tryc(3, q, F_MA1, e, d, 0);
                if (d2 >= 0) tryc(3, q + 1, F_MS1, e, d2, 0);
            }
        }
        if (best <= b) { m->cost = best; return best; }
        if (!aborted) m->lb = b;
        return INF;
    }
    u64 refval(int ref) const { return ref >= 0 ? nd[ref].val : steps[-1 - ref].val; }
    int emit(char op, int x, int y) {
        u64 a = refval(x), b = refval(y), v;
        switch (op) { case '+': v = a + b; break; case '-': v = a - b; break; case '*': v = a * b; break; default: v = a / b; }
        int id = inC(v); if (id >= 0) return id;
        auto it = built.find(v); if (it != built.end()) return it->second;
        steps.push_back(Step{op, x, y, v});
        int ref = -(int)steps.size(); built[v] = ref; return ref;
    }
    int emitS1(int slot) { const Ent &e = S1.s[slot]; return emit(OPC[e.b & 7], e.a, e.b >> 3); }
    int build(u64 v) {
        int id = inC(v); if (id >= 0) return id;
        auto it = built.find(v); if (it != built.end()) return it->second;
        Rec *m = memoGet(v);
        int ref = 0, c = m->p1;
        switch (m->form) {
        case F_S1: ref = emitS1(m->p1); break;
        case F_L2: { int w = emitS1(m->p1), cc = m->p2;
            switch (m->p3) { case 0: ref = emit('+', w, cc); break; case 1: ref = emit('-', w, cc); break; case 2: ref = emit('-', cc, w); break;
                             case 3: ref = emit('*', w, cc); break; case 4: ref = emit('/', w, cc); break; default: ref = emit('/', cc, w); }
            break; }
        case F_M: { int q = build(m->child); ref = emit('*', q, c); break; }
        case F_MA: { int q = build(m->child); int p = emit('*', q, c); ref = emit('+', p, m->p2); break; }
        case F_MS: { int q = build(m->child); int p = emit('*', q, c); ref = emit('-', p, m->p2); break; }
        case F_MAS: { int q = build(m->child); int p = emit('*', q, c); int s = emitS1(m->p2); ref = emit('+', p, s); break; }
        case F_MSS: { int q = build(m->child); int p = emit('*', q, c); int s = emitS1(m->p2); ref = emit('-', p, s); break; }
        case F_NP: { int r = build(m->child); int p = emit('*', c, m->p2); ref = emit('+', p, r); break; }
        case F_NM: { int r = build(m->child); int p = emit('*', c, m->p2); ref = emit('-', p, r); break; }
        case F_NPS: { int r = build(m->child); int qq = emitS1(m->p2); int p = emit('*', c, qq); ref = emit('+', p, r); break; }
        case F_NMS: { int r = build(m->child); int qq = emitS1(m->p2); int p = emit('*', c, qq); ref = emit('-', p, r); break; }
        case F_A: { int r = build(m->child); ref = emit('+', c, r); break; }
        case F_RS: { int r = build(m->child); ref = emit('-', c, r); break; }
        case F_N1: { int r = build(m->child); int y = emit((m->p3 & 1) ? '-' : '+', c, m->p2); ref = emit((m->p3 & 2) ? '-' : '+', y, r); break; }
        case F_J3: { int w1 = emitS1(m->p1), w2 = emitS1(m->p2); ref = emit(OPC[m->p3], w1, w2); break; }
        case F_M1: { int q = build(m->child); int mm = emitS1(c); ref = emit('*', q, mm); break; }
        case F_MA1: { int q = build(m->child); int mm = emitS1(c); int p = emit('*', q, mm); ref = emit('+', p, m->p2); break; }
        case F_MS1: { int q = build(m->child); int mm = emitS1(c); int p = emit('*', q, mm); ref = emit('-', p, m->p2); break; }
        default: fprintf(stderr, "build: 형식 없음\n"); exit(3);
        }
        return ref;
    }

    // ---- 긴 사슬용 역방향 beam ---------------------------------------------
    // 비용 층마다 값이 작은 상태 beamW 개만 펼친다. 성공하면 steps 를 채우고 실제 명령 수를 돌려준다.
    struct BState { u64 v; int parent; unsigned char form; int p1, p2; int cost; };
    vector<BState> bst;
    int emitFrom(unsigned char form, int ch, int p1, int p2) {
        switch (form) {
        case F_M: return emit('*', ch, p1);
        case F_MA: { int p = emit('*', ch, p1); return emit('+', p, p2); }
        case F_MS: { int p = emit('*', ch, p1); return emit('-', p, p2); }
        case F_MAS: { int p = emit('*', ch, p1); int sv = emitS1(p2); return emit('+', p, sv); }
        case F_MSS: { int p = emit('*', ch, p1); int sv = emitS1(p2); return emit('-', p, sv); }
        case F_NP: { int p = emit('*', p1, p2); return emit('+', p, ch); }
        case F_NM: { int p = emit('*', p1, p2); return emit('-', p, ch); }
        case F_NPS: { int qq = emitS1(p2); int p = emit('*', p1, qq); return emit('+', p, ch); }
        case F_NMS: { int qq = emitS1(p2); int p = emit('*', p1, qq); return emit('-', p, ch); }
        case F_A: return emit('+', p1, ch);
        case F_RS: return emit('-', p1, ch);
        default: fprintf(stderr, "emitFrom: 형식 없음\n"); exit(3);
        }
    }
    int beamDerive(u64 v0, int maxcost) {
        bst.clear(); unordered_map<u64, int> seen;
        vector<vector<int>> layers(maxcost + 4);
        bst.push_back(BState{v0, -1, F_NONE, 0, 0, 0}); layers[0].push_back(0); seen[v0] = 0;
        int best = maxcost + 1, bestState = -1, bestKind = 0, bestSlot = -1; Rec l2{};
        auto consider = [&](u64 w, int cost, int par, unsigned char form, int p1, int p2) {
            if (w == 0 || cost >= best) return;
            if (inC(w) >= 0) { best = cost; bst.push_back(BState{w, par, form, p1, p2, cost}); bestState = (int)bst.size() - 1; bestKind = 0; return; }
            if (cost + 1 < best) { int e = s1find(w); if (e >= 0) { best = cost + 1; bst.push_back(BState{w, par, form, p1, p2, cost}); bestState = (int)bst.size() - 1; bestKind = 1; bestSlot = e; return; } }
            if (cost + 2 >= best) return;
            auto it = seen.find(w); if (it != seen.end() && it->second <= cost) return;
            seen[w] = cost;
            bst.push_back(BState{w, par, form, p1, p2, cost}); layers[cost].push_back((int)bst.size() - 1);
        };
        size_t n = ctx.size();
        for (int g = 0; g + 2 < best && g <= maxcost; g++) {
            vector<int> lv = layers[g]; if (lv.empty()) continue;
            sort(lv.begin(), lv.end(), [&](int a, int b) { return bst[a].v < bst[b].v; });
            lv.erase(unique(lv.begin(), lv.end(), [&](int a, int b) { return bst[a].v == bst[b].v; }), lv.end());
            if ((int)lv.size() > beamW) {
                for (int i = 0; i < beamW; i++) if (rng() % 8 == 0) { size_t j = beamW + rng() % min((size_t)beamW, lv.size() - beamW); swap(lv[i], lv[j]); }
                lv.resize(beamW);
            }
            for (int si : lv) {
                if (g + 2 >= best) break;
                u64 v = bst[si].v;
                if (seen[v] < g) continue;
                { Rec tmp{}; if (leaf2(v, &tmp)) { best = g + 2; bestState = si; bestKind = 2; l2 = tmp; continue; } }
                size_t st = rng() % n;
                for (size_t k = 0; k < n && g + 2 < best; k++) {
                    auto &pr = ctx[(st + k) % n]; u64 cv = pr.first; int cid = pr.second;
                    if (cv < 2 || cv >= v) continue;
                    u64 q = v / cv, r = v - q * cv;
                    if (r == 0) { consider(q, g + 1, si, F_M, cid, 0); continue; }
                    if (cv <= MULMAX) {
                        int d = resfind(cid, r, v - 1);
                        if (d >= 0) consider((v - nd[d].val) / cv, g + 2, si, F_MA, cid, d);
                        d = resfind(cid, cv - r, L - v);
                        if (d >= 0) { u64 ch = (v + nd[d].val) / cv; if (ch < v) consider(ch, g + 2, si, F_MS, cid, d); }
                        if (g + 3 < best) {
                            int e = s1find(r); if (e >= 0) consider(q, g + 3, si, F_MAS, cid, e);
                            if (v + (cv - r) <= L) { e = s1find(cv - r); if (e >= 0) consider(q + 1, g + 3, si, F_MSS, cid, e); }
                        }
                    }
                    if (q >= 2 && r < (v >> SH)) {
                        int qi = inC(q);
                        if (qi >= 0) consider(r, g + 2, si, F_NP, cid, qi);
                        else if (g + 3 < best) { int e = s1find(q); if (e >= 0) consider(r, g + 3, si, F_NPS, cid, e); }
                    }
                    u64 r2 = cv - r;
                    if (r2 < (v >> SH) && (u128)(q + 1) * cv <= L) {
                        int qi = inC(q + 1);
                        if (qi >= 0) consider(r2, g + 2, si, F_NM, cid, qi);
                        else if (g + 3 < best) { int e = s1find(q + 1); if (e >= 0) consider(r2, g + 3, si, F_NMS, cid, e); }
                    }
                }
                size_t idx = lower_bound(ctx.begin(), ctx.end(), make_pair(v, -1)) - ctx.begin();
                for (int k = 1; k <= 2; k++) if (idx >= (size_t)k) { u64 y = ctx[idx - k].first, r = v - y; if (r < (v >> 3)) consider(r, g + 1, si, F_A, ctx[idx - k].second, 0); }
                for (int k = 0; k < 2; k++) if (idx + k < n) { u64 y = ctx[idx + k].first, r = y - v; if (r < (v >> 3)) consider(r, g + 1, si, F_RS, ctx[idx + k].second, 0); }
            }
        }
        if (bestState < 0) return INF;
        steps.clear(); built.clear();
        int ref, cur = bestState;
        if (bestKind == 0) ref = inC(bst[cur].v);
        else if (bestKind == 1) ref = emitS1(bestSlot);
        else {
            int w = emitS1(l2.p1), cc = l2.p2;
            switch (l2.p3) { case 0: ref = emit('+', w, cc); break; case 1: ref = emit('-', w, cc); break; case 2: ref = emit('-', cc, w); break;
                             case 3: ref = emit('*', w, cc); break; case 4: ref = emit('/', w, cc); break; default: ref = emit('/', cc, w); }
        }
        while (bst[cur].parent >= 0) { ref = emitFrom(bst[cur].form, ref, bst[cur].p1, bst[cur].p2); cur = bst[cur].parent; }
        if (ref >= 0 || -1 - ref != (int)steps.size() - 1 || refval(ref) != v0) return INF;
        nBeam++;
        return (int)steps.size();
    }

    // ---- 이동 ------------------------------------------------------------
    // x 를 떼어 냈을 때 함께 죽는 노드 (x 포함). 금지(ban)된 노드와 목표 노드는 남긴다.
    void coneOf(int x, vector<int> &cone) {
        cone.assign(1, x);
        vector<int> work{nd[x].a, nd[x].b}, touched;
        while (!work.empty()) {
            int y = work.back(); work.pop_back();
            if (y < ns) continue;
            touched.push_back(y);
            if (--uses[y] == 0 && !nd[y].req && !ban[y]) { cone.push_back(y); work.push_back(nd[y].a); work.push_back(nd[y].b); }
        }
        for (int y : touched) uses[y]++;
    }
    // 레지스터 인식: x 의 현재 자리 p 에서 쓸 수 없는 값(뒤에 만들어지는 값, 수명을 p 까지 늘리면 레지스터가 넘치는 값)을 금지한다.
    // forb 에 현재 stamp 를 찍으므로 rederive 가 stamp 를 올린 직후에 불러야 한다.
    void markUnaffordable(int x) {
        vector<int> ord = order;
        stable_sort(ord.begin(), ord.end(), [&](int a, int b) { return prio[a] < prio[b]; });
        size_t N = nd.size(); vector<int> pos(N, -1), lu(N, -1);
        for (size_t T = 0; T < ord.size(); T++) pos[ord[T]] = (int)T;
        for (size_t T = 0; T < ord.size(); T++) { lu[nd[ord[T]].a] = (int)T; lu[nd[ord[T]].b] = (int)T; }
        int p = pos[x]; if (p < 0) return;
        vector<int> need(ord.size(), 0);
        int live = 0; for (int i = 0; i < ns; i++) if (lu[i] >= 0) live++;
        for (size_t T = 0; T < ord.size(); T++) {
            int n = ord[T], a = nd[n].a, b = nd[n].b;
            if (lu[a] == (int)T) live--;
            if (b != a && lu[b] == (int)T) live--;
            need[T] = live + 1;
            if (lu[n] >= 0) live++;
        }
        vector<int> M(p + 2, 0);                       // M[k] = max(need[k..p-1])
        for (int k = p - 1; k >= 0; k--) M[k] = max(M[k + 1], need[k]);
        int lim = nreg - 1 - regMargin;
        auto check = [&](int y, int d) {
            if (forb[y] == stamp) return;
            if (d >= p) { forb[y] = stamp; return; }
            int l = lu[y]; if (l < d) l = d;
            if (l >= p) return;                         // p 를 지나 살아 있다: 공짜
            int st = l > d ? l : d + 1;
            if (st < 0) st = 0;
            if (st < p && M[st] > lim) forb[y] = stamp;
        };
        for (int i = 0; i < ns; i++) check(i, -1);
        for (int n : ord) if (n != x) check(n, pos[n]);
    }
    // x 를 다시 유도해 그래프에 적용한다. 표 갱신과 순서 검사는 호출자가 한다.
    // 반환: 새 비용 - 기존 원뿔 크기. 못 찾으면 INF (그래프는 그대로).
    int rederive(int x, int extra, bool allowEq, vector<int> &added, bool &merged) {
        merged = false; added.clear();
        vector<int> cone; coneOf(x, cone);
        int oldcost = (int)cone.size();
        stamp++;
        for (int y : cone) forb[y] = stamp;
        vector<int> q{x};
        for (size_t i = 0; i < q.size(); i++) for (int c : cons[q[i]]) if (forb[c] != stamp) { forb[c] = stamp; q.push_back(c); }
        if (awareNow) markUnaffordable(x);
        u64 v = nd[x].val;
        int dupNode = inC(v);
        if (dupNode >= 0) {                                   // 같은 값이 다른 곳에 있다: 그 노드로 합친다
            ensureSnap();
            for (int c : cons[x]) { if (nd[c].a == x) nd[c].a = dupNode; if (nd[c].b == x) nd[c].b = dupNode; }
            for (int y : cone) nd[y].alive = 0;
            if (nd[x].req) { nd[x].req = 0; nd[dupNode].req = 1; }
            merged = true; refreshOrder(added);
            return -oldcost;
        }
        int maxb = oldcost + extra; if (!allowEq && extra == 0) maxb--;
        if (maxb > maxBudget) maxb = maxBudget;
        if (maxb < 1) return INF;
        ctx.clear();
        for (int i = 0; i < ns; i++) if (ok(i)) ctx.push_back({nd[i].val, i});
        for (int n : order) if (ok(n)) ctx.push_back({nd[n].val, n});
        if (ctx.empty()) return INF;
        sort(ctx.begin(), ctx.end());
        ctx.erase(unique(ctx.begin(), ctx.end(), [](const pair<u64, int> &a, const pair<u64, int> &b) { return a.first == b.first; }), ctx.end());
        mstamp++; mcount = 0; expansions = 0; aborted = false;
        int found = INF, dmax = min(maxb, dfsMaxB); bool viaBeam = false;
        for (int b = 1; b <= dmax && !aborted; b++) { int r = solve(v, b, 0); if (r <= b) { found = r; break; } }
        if (aborted) nAbort++;
        if (found > dmax && maxb > dmax && beamW > 0) { found = beamDerive(v, maxb); viaBeam = found <= maxb; }
        if (found > maxb) return INF;
        if (!viaBeam) {
            steps.clear(); built.clear();
            int ref = build(v);
            if (ref >= 0 || -1 - ref != (int)steps.size() - 1) return INF;
        }
        int newcost = (int)steps.size();
        if (newcost > oldcost + extra) return INF;
        if (newcost == oldcost && !banActive) {               // 같은 값 집합이면 변화가 없다
            vector<u64> A, B; for (int y : cone) A.push_back(nd[y].val); for (auto &s : steps) B.push_back(s.val);
            sort(A.begin(), A.end()); sort(B.begin(), B.end()); if (A == B) return INF;
        }
        lastDeltaBits = 0;
        for (int y : cone) if (y != x) lastDeltaBits -= 64 - __builtin_clzll(nd[y].val);
        for (size_t i = 0; i + 1 < steps.size(); i++) lastDeltaBits += 64 - __builtin_clzll(steps[i].val);
        ensureSnap();
        for (int y : cone) if (y != x) nd[y].alive = 0;
        vector<int> newid(steps.size());
        for (size_t i = 0; i < steps.size(); i++) {
            auto res = [&](int r) { return r >= 0 ? r : newid[-1 - r]; };
            int a = res(steps[i].x), b = res(steps[i].y);
            if (i + 1 == steps.size()) { nd[x].op = steps[i].op; nd[x].a = a; nd[x].b = b; newid[i] = x; }
            else {
                int id = (int)nd.size(); nd.push_back(Node{steps[i].val, a, b, steps[i].op, 1, 0});
                prio.push_back(prio[x] - 0.9 + 0.8 * (double)(i + 1) / (double)(steps.size() + 1));
                forb.push_back(0); ban.push_back(0); newid[i] = id; added.push_back(id);
            }
        }
        refreshOrder(added);
        return newcost - oldcost;
    }
    // 새 순서를 찾는다. x >= 0 이면 x 와 그 새 노드들의 위치를 바꿔 가며 시도한다.
    bool place(int x, const vector<int> &added, bool improving, vector<int> &sched) {
        if (schedule(sched) && regs(sched, nullptr)) return true;
        if (x >= 0) {
            double keepP = prio[x]; vector<double> keepA; for (int id : added) keepA.push_back(prio[id]);
            auto put = [&](double at) {
                prio[x] = at; for (size_t i = 0; i < added.size(); i++) prio[added[i]] = at - 0.8 + 0.7 * (double)(i + 1) / (double)(added.size() + 2);
                return schedule(sched) && regs(sched, nullptr);
            };
            if (!cons[x].empty()) { double mn = 1e300; for (int c : cons[x]) mn = min(mn, prio[c]); if (put(mn - 0.05)) return true; }
            vector<char> mine(nd.size(), 0); mine[x] = 1; for (int id : added) mine[id] = 1;
            double mx = -1e300;
            auto see = [&](int n) { for (int o : {nd[n].a, nd[n].b}) if (!mine[o]) mx = max(mx, prio[o]); };
            see(x); for (int id : added) see(id);
            if (mx > -1e200 && mx + 0.9 < keepP - 0.5 && put(mx + 0.9)) return true;
            prio[x] = keepP; for (size_t i = 0; i < added.size(); i++) prio[added[i]] = keepA[i];
        }
        if (improving && repairIters > 0) return repairOrder(sched, repairIters);
        return false;
    }
    void commit(const vector<int> &sched, const vector<int> &added) {
        order = sched;
        for (size_t i = 0; i < order.size(); i++) prio[order[i]] = (double)i;
        computeUses(); snapTaken = false;
        noteBest();
        if (schedEvery > 0 && ++sinceSched >= schedEvery) { optimizeOrder(schedIters); sinceSched = 0; }
        if (++sinceRebuild >= 30 || S1.full() || RS.full()) rebuildTables();
        else for (int id : added) if (nd[id].alive) addToTables(id);
    }
    bool tryNode(int x, int extra = 0, bool banOne = false) {
        nEval++; snapTaken = false;
        vector<int> added; bool merged;
        bool allowEq = pEq > 0 && unif() < pEq;
        if (banOne) allowEq = true;
        int bo = -1;
        if (banOne) { int o = (rng() & 1) ? nd[x].a : nd[x].b; if (o >= ns && nd[o].alive) { ban[o] = 1; bo = o; } banActive = true; }
        int d = rederive(x, extra, allowEq, added, merged);
        if (banOne) { if (bo >= 0) ban[bo] = 0; banActive = false; }
        if (d >= INF) return false;
        bool improving = merged || d < 0;
        if (!improving && biasT > 0 && lastDeltaBits > 0 && unif() > exp(-(double)lastDeltaBits / biasT)) { restoreSnap(); nBiasRej++; return false; }
        vector<int> sched;
        if (!place(merged ? -1 : x, added, improving, sched)) { restoreSnap(); nRegFail++; if (improving) nRegFailImp++; return false; }
        commit(sched, added);
        if (merged) nMerge++; else if (d < 0) nImp++; else nEq++;
        if (banOne && d > 0) nWalkUp++;
        if (trace && improving) fprintf(stderr, "T %.1f %zu\n", elapsed(), order.size());
        return true;
    }
    // 목표 노드에서 닿지 않는 노드를 지운다
    void dce() {
        vector<char> need(nd.size(), 0); vector<int> st;
        for (int n : order) if (nd[n].alive && nd[n].req) { need[n] = 1; st.push_back(n); }
        while (!st.empty()) { int n = st.back(); st.pop_back(); for (int o : {nd[n].a, nd[n].b}) if (o >= ns && !need[o]) { need[o] = 1; st.push_back(o); } }
        for (int n : order) if (!need[n]) nd[n].alive = 0;
        vector<int> none; refreshOrder(none);
    }
    // 서로 얽힌 노드 k 개의 정의를 한꺼번에 떼어 내고 다시 만든다
    bool tryRuin(int x, int k, int slack = 0) {
        vector<int> R{x}, pool;
        auto neigh = [&](int n) {
            for (int o : {nd[n].a, nd[n].b}) if (o >= ns) { pool.push_back(o); for (int c : cons[o]) if (c != n) pool.push_back(c); }
            for (int c : cons[n]) pool.push_back(c);
        };
        if (ruinSel == 2) {                                   // 아무 노드나
            for (int t = 0; t < 4 * k && (int)R.size() < k; t++) { int y = order[rng() % order.size()]; if (find(R.begin(), R.end(), y) == R.end()) R.push_back(y); }
        } else if (ruinSel == 1) {                            // 이웃을 따라 자라는 덩어리
            for (int t = 0; t < 6 * k && (int)R.size() < k; t++) {
                pool.clear(); neigh(R[rng() % R.size()]);
                if (pool.empty()) continue;
                int y = pool[rng() % pool.size()];
                if (find(R.begin(), R.end(), y) == R.end()) R.push_back(y);
            }
        } else {                                              // x 의 바로 이웃
            neigh(x);
            shuffle(pool.begin(), pool.end(), rng);
            for (int y : pool) { if ((int)R.size() >= k) break; if (find(R.begin(), R.end(), y) == R.end()) R.push_back(y); }
        }
        if (R.size() < 2) return false;
        nRuinTry++; snapTaken = false; ensureSnap();
        size_t before = order.size();
        for (int y : R) { nd[y].a = 0; nd[y].b = 0; ban[y] = 1; }       // 임시 정의: 피연산자를 놓아 준다
        dce();
        vector<int> H; for (int y : R) if (nd[y].alive) H.push_back(y);
        int removed = (int)before - ((int)order.size() - (int)H.size());
        if (ruinOrd == 1) shuffle(H.begin(), H.end(), rng);
        else if (ruinOrd == 2) sort(H.begin(), H.end(), [&](int a, int b) { return nd[a].val > nd[b].val; });
        else sort(H.begin(), H.end(), [&](int a, int b) { return nd[a].val < nd[b].val; });
        banActive = true;
        int used = 0; bool fail = false; vector<int> allAdded;
        for (size_t i = 0; i < H.size(); i++) {
            int y = H[i]; ban[y] = 0;
            if (!nd[y].alive) continue;
            int allow = removed - used - (int)(H.size() - 1 - i) + slack;
            if (allow < 1) { fail = true; break; }
            vector<int> added; bool merged;
            int d = rederive(y, allow - 1, true, added, merged);
            if (d >= INF) { fail = true; break; }
            if (!merged) used += d + 1;
            for (int id : added) allAdded.push_back(id);
        }
        banActive = false;
        for (size_t i = 0; i < ban.size(); i++) ban[i] = 0;
        if (!fail) {
            dce();
            int now = (int)order.size();
            bool improving = now < (int)before;
            int up = (pUp > 0 && (int)before - bestLen < upMax && unif() < pUp) ? 1 : 0;
            if (slack > up) up = slack;
            if (now > (int)before + up || (slack == 0 && !improving && now == (int)before && unif() >= pEq)) fail = true;
            else {
                vector<int> keep; for (int id : allAdded) if (nd[id].alive) keep.push_back(id);
                vector<int> sched;
                if (place(-1, keep, improving || slack > 0, sched)) {
                    commit(sched, keep);
                    if (improving) { nRuin++; if (trace) fprintf(stderr, "T %.1f %zu (ruin)\n", elapsed(), order.size()); } else nRuinEq++;
                    return true;
                }
                nRegFail++; if (improving) nRegFailImp++;
            }
        }
        restoreSnap();
        return false;
    }

    // ---- 우회 이동: 그래프를 일부러 바꾼 채 가벼운 이동을 돌리고, 되돌리거나 확정한다 ----
    double pHold = 0, pHelp = 0; int holdIters = 300, holdK = 2;
    long nHoldTry = 0, nHoldOk = 0, nHoldGain = 0, nHelpTry = 0, nHelpOk = 0;
    void stepMove(int x) {
        awareNow = pAware > 0 && unif() < pAware;
        double u = unif();
        if (u < pElim) tryElim(x); else if (u < pElim + pRuin) tryRuin(x, 2 + (int)(rng() % (ruinK - 1))); else tryNode(x);
    }
    void restoreOuter(const Snap &o) { nd = o.nd; order = o.order; prio = o.prio; forb.assign(nd.size(), 0); ban.assign(nd.size(), 0); stamp = 1; snapTaken = false; computeUses(); rebuildTables(); }
    bool excursion(int mode, int k) {
        if (order.size() < 12) return false;
        Snap o; o.nd = nd; o.order = order; o.prio = prio; snapTaken = false;
        int before = (int)order.size();
        vector<u64> held; u64 helperVal = 0;
        vector<int> sched;
        if (mode == 0) {
            vector<int> reqs; for (int n : order) if (nd[n].req) reqs.push_back(n);
            if (reqs.size() < 4) return false;
            shuffle(reqs.begin(), reqs.end(), rng);
            for (int i = 0; i < k && i < (int)reqs.size(); i++) { held.push_back(nd[reqs[i]].val); nd[reqs[i]].req = 0; }
            dce();
            if ((int)order.size() >= before) { restoreOuter(o); return false; }
            nHoldTry++;
        } else {
            vector<int> al; aliveList(al);
            int h = -1;
            for (int t = 0; t < 20 && h < 0; t++) {
                int a = al[rng() % al.size()], b = al[rng() % al.size()]; if (a == b) continue;
                char op = "+-*/"[rng() % 4]; u64 X = nd[a].val, Y = nd[b].val, v;
                if (op == '+') v = X + Y; else if (op == '-') { if (X <= Y) continue; v = X - Y; } else if (op == '*') { u128 p = (u128)X * Y; if (p > L) continue; v = (u64)p; } else { if (Y < 2 || X % Y) continue; v = X / Y; }
                if (v < 1 || v > L || inC(v) >= 0) continue;
                h = (int)nd.size(); nd.push_back(Node{v, a, b, op, 1, 1}); prio.push_back(max(prio[a], prio[b]) + 0.01); forb.push_back(0); ban.push_back(0);
                order.push_back(h); helperVal = v;
            }
            if (h < 0) { restoreOuter(o); return false; }
            computeUses(); nHelpTry++;
        }
        if (!(schedule(sched) && regs(sched, nullptr))) { restoreOuter(o); return false; }
        order = sched; for (size_t i = 0; i < order.size(); i++) prio[order[i]] = (double)i; computeUses();
        if (mode == 1) addToTables((int)(find(order.begin(), order.end(), (int)nd.size() - 1) - order.begin()) >= 0 ? (int)nd.size() - 1 : 0);
        inExc = true;
        for (int it = 0; it < holdIters && !order.empty(); it++) stepMove(order[rng() % order.size()]);
        inExc = false;
        stamp++;
        vector<int> keep;
        if (mode == 1) {
            int h = -1; for (int n : order) if (nd[n].val == helperVal) { h = n; break; }
            if (h >= 0) nd[h].req = 0;
            dce();
            if ((int)order.size() >= before) { restoreOuter(o); return false; }
            if (!place(-1, keep, true, sched)) { restoreOuter(o); return false; }
            commit(sched, keep); nHelpOk++; return true;
        }
        vector<int> ph;
        for (u64 t : held) {
            int e = inC(t);
            if (e >= 0) { nd[e].req = 1; continue; }
            int id = (int)nd.size(); nd.push_back(Node{t, 0, 0, '+', 1, 1}); prio.push_back(1e6 + id); forb.push_back(0); ban.push_back(1);
            ph.push_back(id); order.push_back(id);
        }
        computeUses();
        sort(ph.begin(), ph.end(), [&](int a, int b) { return nd[a].val < nd[b].val; });
        int cur = (int)order.size(), used = 0; bool fail = false; vector<int> allAdded;
        banActive = true;
        for (int y : ph) {
            ban[y] = 0;
            int extra = before - cur - used; if (extra < 0) { fail = true; break; }
            vector<int> added; bool merged;
            int d = rederive(y, extra, true, added, merged);
            if (d >= INF) { fail = true; break; }
            used += d; for (int id : added) allAdded.push_back(id);
            if (!merged) allAdded.push_back(y);
        }
        banActive = false;
        for (size_t i = 0; i < ban.size(); i++) ban[i] = 0;
        if (!fail) {
            dce();
            int now = (int)order.size();
            if (now > before || (now == before && unif() >= pEq)) fail = true;
            else {
                for (int id : allAdded) if (nd[id].alive) keep.push_back(id);
                if (place(-1, keep, now < before, sched)) { commit(sched, keep); nHoldOk++; if (now < before) nHoldGain++; return true; }
            }
        }
        restoreOuter(o); return false;
    }

    // 길이 상한 순환: 최선에서 시작해 상한을 +lcap 에서 0 으로 줄이며 조리법 하나만 바꾸는 걷기를 허용한다
    int capNow() {
        double t = elapsed();
        if (t - cycleStart >= lcapT) {
            cycleStart = t; nCycle++;
            if (!bestSnap.nd.empty() && (int)order.size() > bestLen) { nd = bestSnap.nd; order = bestSnap.order; prio = bestSnap.prio; forb.assign(nd.size(), 0); ban.assign(nd.size(), 0); stamp = 1; snapTaken = false; computeUses(); rebuildTables(); }
        }
        double ph = (t - cycleStart) / lcapT;
        if (lmode == 0) return (int)(lcap * (1.0 - ph) + 0.5);
        static const int plan[9] = {1, 2, 2, 1, 1, 1, 0, 0, 0};
        return plan[min(8, (int)(ph * 9))] * lcap / 2;
    }
    // 중간값 x 를 없애 본다
    bool tryElim(int x) {
        if (nd[x].req || (int)cons[x].size() < 2 || (int)cons[x].size() > elimCons) return false;
        nElimTry++; snapTaken = false;
        vector<int> coneX{x}, work{nd[x].a, nd[x].b}, touched;      // x 가 안 쓰이게 되면 함께 죽는 노드
        while (!work.empty()) {
            int y = work.back(); work.pop_back();
            if (y < ns) continue;
            touched.push_back(y);
            if (--uses[y] == 0 && !nd[y].req) { coneX.push_back(y); work.push_back(nd[y].a); work.push_back(nd[y].b); }
        }
        for (int y : touched) uses[y]++;
        int S = (int)coneX.size() - 1;
        vector<int> users = cons[x];
        sort(users.begin(), users.end(), [&](int a, int b) { return prio[a] < prio[b]; });
        for (int y : coneX) ban[y] = 1;
        banActive = true;
        vector<int> allAdded; bool fail = false;
        for (int y : users) {
            if (!nd[y].alive || (nd[y].a != x && nd[y].b != x)) continue;
            vector<int> added; bool merged;
            int d = rederive(y, S, true, added, merged);
            if (d >= INF) { fail = true; break; }
            if (d > 0) S -= d;
            for (int id : added) allAdded.push_back(id);
        }
        banActive = false;
        for (size_t i = 0; i < ban.size(); i++) ban[i] = 0;
        if (!fail && uses[x] != 0) fail = true;
        if (!fail) {                                              // 쓰이지 않게 된 노드를 지운다
            vector<char> need(nd.size(), 0); vector<int> st;
            for (int n : order) if (nd[n].req) { need[n] = 1; st.push_back(n); }
            while (!st.empty()) { int n = st.back(); st.pop_back(); for (int o : {nd[n].a, nd[n].b}) if (o >= ns && !need[o]) { need[o] = 1; st.push_back(o); } }
            for (int n : order) if (!need[n]) nd[n].alive = 0;
            vector<int> keep; for (int id : allAdded) if (nd[id].alive) keep.push_back(id);
            vector<int> none; refreshOrder(none);
            vector<int> sched;
            if (place(-1, keep, true, sched)) {
                commit(sched, keep); nElim++;
                if (trace) fprintf(stderr, "T %.1f %zu (elim)\n", elapsed(), order.size());
                return true;
            }
            nRegFail++; nRegFailImp++;
        }
        if (snapTaken) restoreSnap();
        return false;
    }
};

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: elf_lns <in> <seconds> [key=value ...]\n"); return 2; }
    FILE *f = fopen(argv[1], "r"); if (!f) { perror("open"); return 2; }
    double seconds = atof(argv[2]);
    Solver S; u64 seed = 1;
    for (int i = 3; i < argc; i++) {
        string kv = argv[i]; size_t e = kv.find('='); if (e == string::npos) { fprintf(stderr, "인자 형식: key=value (%s)\n", argv[i]); return 2; }
        string k = kv.substr(0, e); double val = atof(kv.c_str() + e + 1);
        if (k == "seed") seed = (u64)val; else if (k == "peq") S.pEq = val; else if (k == "cap") S.expCap = (long)val;
        else if (k == "j3") S.useJ3 = (int)val; else if (k == "trace") S.trace = (int)val; else if (k == "schedinit") S.schedInit = (int)val;
        else if (k == "schedevery") S.schedEvery = (int)val; else if (k == "repair") S.repairIters = (int)val; else if (k == "pelim") S.pElim = val;
        else if (k == "bias") S.biasT = val; else if (k == "pruin") S.pRuin = val; else if (k == "ruink") S.ruinK = max(2, (int)val); else if (k == "ruinsel") S.ruinSel = (int)val; else if (k == "pup") S.pUp = val; else if (k == "kick") S.kickEvery = val; else if (k == "kickk") S.kickK = (int)val; else if (k == "kickslack") S.kickSlack = (int)val; else if (k == "aware") S.pAware = val; else if (k == "dfsmax") S.dfsMaxB = (int)val; else if (k == "beamw") S.beamW = (int)val; else if (k == "regmargin") S.regMargin = (int)val; else if (k == "upmax") S.upMax = (int)val; else if (k == "ruinord") S.ruinOrd = (int)val; else if (k == "maxb") S.maxBudget = (int)val; else if (k == "elimcons") S.elimCons = (int)val; else if (k == "lcap") S.lcap = (int)val; else if (k == "lmode") S.lmode = (int)val; else if (k == "lcapt") S.lcapT = val; else if (k == "walk") S.pWalk = val; else if (k == "hold") S.pHold = val; else if (k == "help") S.pHelp = val; else if (k == "holditers") S.holdIters = (int)val; else if (k == "holdk") S.holdK = (int)val;
        else { fprintf(stderr, "모르는 인자 %s\n", k.c_str()); return 2; }
    }
    S.rng.seed(seed);
    int nt, nprog; u64 lim;
    if (fscanf(f, "%llu %d %d %d %d", &lim, &S.nreg, &S.ns, &nt, &nprog) != 5) return 2;
    S.L = lim;
    vector<u64> targets(nt);
    for (int i = 0; i < S.ns; i++) { u64 v; if (fscanf(f, "%llu", &v) != 1) return 2; S.nd.push_back(Node{v, -1, -1, 0, 1, 0}); }
    for (int i = 0; i < nt; i++) if (fscanf(f, "%llu", &targets[i]) != 1) return 2;
    vector<int> reg(S.nreg, -1); for (int i = 0; i < S.ns; i++) reg[i] = i;
    vector<int> ord;
    for (int i = 0; i < nprog; i++) {
        char op; int a, b, d; if (fscanf(f, " %c %d %d %d", &op, &a, &b, &d) != 4) return 2;
        int x = reg[a], y = reg[b]; u64 X = S.nd[x].val, Y = S.nd[y].val, v;
        switch (op) { case '+': v = X + Y; break; case '-': v = X - Y; break; case '*': v = X * Y; break; default: v = X / Y; }
        S.nd.push_back(Node{v, x, y, op, 1, 0}); reg[d] = (int)S.nd.size() - 1; ord.push_back(reg[d]);
    }
    fclose(f);
    if (S.lcap < 0) { u64 mx = 0; for (u64 t : targets) mx = max(mx, t); S.lcap = (mx < (1ULL << 40)) ? 4 : 0; }
    // 필요한 노드만 남긴다
    unordered_map<u64, int> first;
    for (int i = 0; i < S.ns; i++) first.emplace(S.nd[i].val, i);
    for (int n : ord) first.emplace(S.nd[n].val, n);
    for (u64 t : targets) { auto it = first.find(t); if (it == first.end()) { fprintf(stderr, "입력 프로그램이 목표값 %llu 를 만들지 않음\n", t); return 4; } if (it->second >= S.ns) S.nd[it->second].req = 1; }
    vector<char> need(S.nd.size(), 0);
    for (int n : ord) if (S.nd[n].req) need[n] = 1;
    for (int i = (int)ord.size() - 1; i >= 0; i--) { int n = ord[i]; if (need[n]) { need[S.nd[n].a] = 1; need[S.nd[n].b] = 1; } else S.nd[n].alive = 0; }
    for (int n : ord) if (need[n]) S.order.push_back(n);
    S.prio.assign(S.nd.size(), -1); for (size_t i = 0; i < S.order.size(); i++) S.prio[S.order[i]] = (double)i;
    S.forb.assign(S.nd.size(), 0); S.ban.assign(S.nd.size(), 0);
    S.recs.assign(Solver::MSIZE, Rec{0, -1, INF, 0, F_NONE, 0, 0, 0, 0, 0, 0, 0});
    S.computeUses();
    vector<array<int, 4>> prog;
    if (!S.regs(S.order, &prog)) { fprintf(stderr, "입력 프로그램의 레지스터 배정 실패\n"); return 4; }
    size_t startLen = S.order.size();
    S.rebuildTables();
    if (S.schedInit > 0) S.optimizeOrder(S.schedInit);
    S.noteBest();
    S.tStart = chrono::steady_clock::now();
    long iters = 0;
    vector<int> cand; size_t ci = 0; long candGen = -1;
    while (S.elapsed() < seconds && !S.order.empty()) {
        if (S.kickEvery > 0 && S.elapsed() - max(S.lastBestTime, S.lastKickTime) > S.kickEvery) { S.kick(); continue; }
        if (candGen != S.gen || ci >= cand.size()) { cand = S.order; shuffle(cand.begin(), cand.end(), S.rng); ci = 0; candGen = S.gen; }
        if (S.pHold > 0 && S.unif() < S.pHold) { S.excursion(0, 1 + (int)(S.rng() % S.holdK)); continue; }
        if (S.pHelp > 0 && S.unif() < S.pHelp) { S.excursion(1, 0); continue; }
        int x = cand[ci++];
        if (x >= (int)S.nd.size() || !S.nd[x].alive) continue;
        if (S.lcap > 0) { long g0 = S.gen; int cn = S.capNow(); if (S.gen != g0) continue; int room = S.bestLen + cn - (int)S.order.size(); if (room > 0 && S.unif() < S.pWalk) { S.nWalk++; S.tryNode(x, room, true); iters++; continue; } }
        S.awareNow = S.pAware > 0 && S.unif() < S.pAware;
        double u = S.unif();
        if (u < S.pElim) S.tryElim(x); else if (u < S.pElim + S.pRuin) S.tryRuin(x, 2 + (int)(S.rng() % (S.ruinK - 1))); else S.tryNode(x);
        iters++;
    }
    S.noteBest();
    if (S.bestLen >= INF) { fprintf(stderr, "최종 레지스터 배정 실패\n"); return 5; }
    prog = S.bestProg;
    printf("LEN %zu\n", prog.size());
    for (auto &p : prog) printf("%c %d %d %d\n", (char)p[0], p[1], p[2], p[3]);
    fprintf(stderr, "walk %ld/%ld cyc %ld ", S.nWalkUp, S.nWalk, S.nCycle);
    fprintf(stderr, "hold %ld/%ld(%ld) help %ld/%ld ", S.nHoldOk, S.nHoldTry, S.nHoldGain, S.nHelpOk, S.nHelpTry);
    fprintf(stderr, "kick %ld beam %ld ruin %ld+%ld/%ld ", S.nKick, S.nBeam, S.nRuin, S.nRuinEq, S.nRuinTry);
    fprintf(stderr, "start %zu end %zu iters %ld eval %ld imp %ld eq %ld merge %ld elim %ld/%ld regfail %ld (imp %ld) repair %ld abort %ld\n",
            startLen, prog.size(), iters, S.nEval, S.nImp, S.nEq, S.nMerge, S.nElim, S.nElimTry, S.nRegFail, S.nRegFailImp, S.nRepair, S.nAbort);
    return 0;
}
