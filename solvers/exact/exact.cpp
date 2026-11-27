// exact: 노드마다 전용 원뿔을 지우고 새 명령 k개(k<원뿔 크기, k<=K)로 다시 만들 수 있는지 빠짐없이 찾는다.
// 사용: exact K [minc]   (stdin 입력) / exact brute (작은 사례 검증, stdin)
// 입력: L ns nn / 시작값 ns개 / nn줄 "op a b req" (노드: 시작값 0..ns-1, 명령 i 는 ns+i, 위상 순서)
// 출력: "NODE v cone" , "HIT v cone k mask nsteps (op ra rb)*" (ref>=0 노드, <0 이면 임시값 -1-j), "TIME sec"
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long u64;
typedef unsigned __int128 u128;
static u64 L;
static inline u64 hmix(u64 x){x^=x>>31;x*=0x9E3779B97F4A7C15ULL;x^=x>>29;x*=0xBF58476D1CE4E5B9ULL;x^=x>>32;return x;}
struct Step{char op;int ra,rb;};
typedef vector<Step> Hit;
struct Ent{u64 key;int a,b;char op;bool used;};
struct F1Table{
  vector<Ent> s;u64 mask=0;
  void init(size_t want){size_t n=64;while(n<want*2)n<<=1;s.assign(n,Ent{0,0,0,0,false});mask=n-1;}
  void ins(u64 k,int a,int b,char op){u64 h=hmix(k)&mask;while(s[h].used)h=(h+1)&mask;s[h]=Ent{k,a,b,op,true};}
};
static int ns,nn,N;
static vector<u64> val;
static F1Table F1;
static unordered_map<u64,int> VM;
static vector<char> al;
static vector<int> Alist;
static u64 T;
static inline bool apply(char op,u64 x,u64 y,u64&r){
  switch(op){case '+':r=x+y;return r<=L;case '-':if(x<=y)return false;r=x-y;return true;
  case '*':{u128 p=(u128)x*y;if(p>L)return false;r=(u64)p;return true;}
  default:if(y==0||x%y)return false;r=x/y;return r>=1;}
}
static const char OPS[4]={'+','-','*','/'};
static Step mk(int ra,u64 va,int rb,u64 vb,u64 r){
  u64 t;
  for(char o:OPS)if(apply(o,va,vb,t)&&t==r)return Step{o,ra,rb};
  for(char o:OPS)if(apply(o,vb,va,t)&&t==r)return Step{o,rb,ra};
  fprintf(stderr,"mk fail %llu %llu %llu\n",va,vb,r);exit(1);
}
static bool canMake(u64 x,u64 y,u64 r){u64 t;for(char o:OPS){if(apply(o,x,y,t)&&t==r)return true;if(apply(o,y,x,t)&&t==r)return true;}return false;}
// p 와 어떤 연산(두 방향)으로 묶어 r 이 되는 q 들
static inline int invs(u64 p,u64 r,u64*o){
  u64 c[6];int m=0;
  if(r>p)c[m++]=r-p;
  if(p>r)c[m++]=p-r;
  if(r+p<=L)c[m++]=r+p;
  if(r%p==0)c[m++]=r/p;
  if(p%r==0)c[m++]=p/r;
  if((u128)r*p<=L)c[m++]=r*p;
  int k=0;for(int i=0;i<m;i++){u64 q=c[i];if(q<1||q>L)continue;bool d=false;for(int j=0;j<k;j++)if(o[j]==q){d=true;break;}if(!d)o[k++]=q;}
  return k;
}
static inline int vmFind(u64 v){auto it=VM.find(v);if(it==VM.end())return -1;int i=it->second;return al[i]?i:-1;}
static inline const Ent* f1find(u64 k){
  u64 h=hmix(k)&F1.mask;
  while(F1.s[h].used){const Ent&e=F1.s[h];if(e.key==k&&al[e.a]&&al[e.b])return &e;h=(h+1)&F1.mask;}
  return nullptr;
}
static inline Step stepOf(const Ent*e){return Step{e->op,e->a,e->b};}
static void buildF1(){
  F1.init((size_t)N*(N+1)*2+64);
  for(int i=0;i<N;i++)for(int j=i;j<N;j++){
    u64 x=val[i],y=val[j];
    if(x+y<=L)F1.ins(x+y,i,j,'+');
    if(x>y)F1.ins(x-y,i,j,'-');else if(y>x)F1.ins(y-x,j,i,'-');
    {u128 p=(u128)x*y;if(p<=L)F1.ins((u64)p,i,j,'*');}
    if(x%y==0)F1.ins(x/y,i,j,'/');
    if(i!=j&&y%x==0)F1.ins(y/x,j,i,'/');
  }
}
struct Ctx{Hit hit;unsigned mask=0;bool found=false;
  void set(unsigned bit,const Hit&h){mask|=1u<<bit;if(!found){found=true;hit=h;}}};
static void k1(Ctx&c){const Ent*e=f1find(T);if(e)c.set(0,{stepOf(e)});}
static void k2(Ctx&c){
  u64 o[8];
  for(int ci:Alist){int m=invs(val[ci],T,o);
    for(int i=0;i<m;i++){const Ent*e=f1find(o[i]);if(e){c.set(0,{stepOf(e),mk(-1,o[i],ci,val[ci],T)});goto d1;}}}
  d1:
  {u64 xs[4];int m=0;if(T%2==0)xs[m++]=T/2;u64 r=(u64)sqrtl((long double)T);for(u64 q=(r>2?r-2:1);q<=r+2;q++)if(q*q==T)xs[m++]=q;
   for(int i=0;i<m;i++){const Ent*e=f1find(xs[i]);if(e){c.set(1,{stepOf(e),mk(-1,xs[i],-1,xs[i],T)});break;}}}
}
static void k3(Ctx&c){
  u64 o[8],o2[8];
  for(int d:Alist){int m=invs(val[d],T,o);
    for(int i=0;i<m;i++){u64 x2=o[i];
      for(int cc:Alist){int m2=invs(val[cc],x2,o2);
        for(int j=0;j<m2;j++){const Ent*e=f1find(o2[j]);if(e){
          c.set(0,{stepOf(e),mk(-1,o2[j],cc,val[cc],x2),mk(-2,x2,d,val[d],T)});goto done0;}}}}}
  done0:
  for(size_t si=0;si<F1.s.size();si++){const Ent&e=F1.s[si];if(!e.used||!al[e.a]||!al[e.b])continue;
    u64 x1=e.key;Step s0=stepOf(&e);
    {int m=invs(x1,T,o);
     for(int i=0;i<m;i++){u64 y=o[i];
       const Ent*f=f1find(y);if(f)c.set(1,{s0,stepOf(f),mk(-1,x1,-2,y,T)});
       // x2=y=(x1,m) , T=(x2,x1)
       int m2=invs(x1,y,o2);
       for(int j=0;j<m2;j++){int cn=vmFind(o2[j]);
         if(cn>=0)c.set(2,{s0,mk(-1,x1,cn,val[cn],y),mk(-2,y,-1,x1,T)});
         else if(o2[j]==x1)c.set(4,{s0,mk(-1,x1,-1,x1,y),mk(-2,y,-1,x1,T)});}
     }}
    // x2=(x1,x1)
    {u64 x2s[3];int m=0;if(x1*2<=L)x2s[m++]=2*x1;if((u128)x1*x1<=L)x2s[m++]=x1*x1;x2s[m++]=1;
     for(int i=0;i<m;i++){u64 x2=x2s[i];
       u64 oo[8];int m3=invs(x2,T,oo);
       for(int j=0;j<m3;j++){int cn=vmFind(oo[j]);if(cn>=0){c.set(3,{s0,mk(-1,x1,-1,x1,x2),mk(-2,x2,cn,val[cn],T)});break;}}
       if(canMake(x2,x1,T))c.set(4,{s0,mk(-1,x1,-1,x1,x2),mk(-2,x2,-1,x1,T)});
       if(canMake(x2,x2,T)&&x2!=1)c.set(6,{s0,mk(-1,x1,-1,x1,x2),mk(-2,x2,-2,x2,T)});
     }}
    // T=(x2,x2), x2=(x1,m)
    {u64 xs[4];int m=0;if(T%2==0)xs[m++]=T/2;u64 r=(u64)sqrtl((long double)T);for(u64 q=(r>2?r-2:1);q<=r+2;q++)if(q*q==T)xs[m++]=q;
     for(int i=0;i<m;i++){u64 x2=xs[i];int m2=invs(x1,x2,o2);
       for(int j=0;j<m2;j++){int cn=vmFind(o2[j]);if(cn>=0){c.set(5,{s0,mk(-1,x1,cn,val[cn],x2),mk(-2,x2,-2,x2,T)});break;}}}}
  }
}

// ---- k=4: 세 꼴 ----
struct KSet{vector<u64> key;vector<int> st;int cur=0;u64 mask=0;
  void init(size_t want){size_t n=64;while(n<want*2)n<<=1;key.assign(n,0);st.assign(n,0);mask=n-1;cur=0;}
  void ensure(size_t want){if(key.size()<want*2+64)init(want);}
  void clear(){cur++;}
  bool ins(u64 k){u64 h=hmix(k)&mask;while(st[h]==cur){if(key[h]==k)return false;h=(h+1)&mask;}st[h]=cur;key[h]=k;return true;}
  bool has(u64 k)const{u64 h=hmix(k)&mask;while(st[h]==cur){if(key[h]==k)return true;h=(h+1)&mask;}return false;}
};
static KSet UH,S2,S3;static vector<u64> Ulist;
void k4(Ctx&c){
  // U: 허용된 F1 값
  if(UH.key.size()<(F1.s.size()))UH.init(F1.s.size()/2+64);
  UH.clear();Ulist.clear();
  for(size_t si=0;si<F1.s.size();si++){const Ent&e=F1.s[si];if(e.used&&al[e.a]&&al[e.b]&&UH.ins(e.key))Ulist.push_back(e.key);}
  u64 o[8],o2[8];
  vector<pair<u64,int>> B1; // (z, e)  T = z ∘ e
  S2.ensure(6*Alist.size()+64);S2.clear();
  for(int e:Alist){int m=invs(val[e],T,o);for(int i=0;i<m;i++)if(S2.ins(o[i]))B1.push_back({o[i],e});}
  // (c) ((a∘b)∘(c∘d))∘e
  for(auto&pz:B1){u64 z=pz.first;int e=pz.second;
    for(u64 X:Ulist){int m=invs(X,z,o);
      for(int i=0;i<m;i++)if(UH.has(o[i])){
        const Ent*fx=f1find(X);const Ent*fy=f1find(o[i]);
        c.set(2,{stepOf(fx),stepOf(fy),mk(-1,X,-2,o[i],z),mk(-3,z,e,val[e],T)});goto dc;}}}
  dc:
  // (a) chain
  {S3.ensure(36*Alist.size()*Alist.size()+64);S3.clear();
   for(auto&pz:B1){u64 x4=pz.first;int e=pz.second;
    for(int d:Alist){int m=invs(val[d],x4,o);
      for(int i=0;i<m;i++){u64 x3=o[i];if(!S3.ins(x3*8+0))continue; // x3 한 번만 (e,d 무관하게 같은 하위 탐색)
        for(int cc:Alist){int m2=invs(val[cc],x3,o2);
          for(int j=0;j<m2;j++)if(UH.has(o2[j])){
            const Ent*f=f1find(o2[j]);
            c.set(0,{stepOf(f),mk(-1,o2[j],cc,val[cc],x3),mk(-2,x3,d,val[d],x4),mk(-3,x4,e,val[e],T)});goto da;}}}}}}
  da:
  // (b) ((a∘b)∘c)∘(d∘e)
  {S2.ensure(6*Ulist.size()+64);S2.clear();vector<pair<u64,u64>> Zs;
   for(u64 y:Ulist){int m=invs(y,T,o);for(int i=0;i<m;i++)if(S2.ins(o[i]))Zs.push_back({o[i],y});}
   for(auto&pz:Zs){u64 z=pz.first,y=pz.second;
    for(int cc:Alist){int m=invs(val[cc],z,o);
      for(int i=0;i<m;i++)if(UH.has(o[i])){
        const Ent*f=f1find(o[i]);const Ent*g=f1find(y);
        c.set(1,{stepOf(f),mk(-1,o[i],cc,val[cc],z),stepOf(g),mk(-2,z,-3,y,T)});goto db;}}}}
  db:;
}
static int searchK(int K,Ctx&c){
  for(int k=1;k<=K;k++){
    if(k==1)k1(c);else if(k==2)k2(c);else if(k==3)k3(c);else k4(c);
    if(c.found)return k;
  }
  return 0;
}
static void setup(int n,const vector<u64>&v){N=n;val=v;VM.clear();for(int i=0;i<N;i++)VM[val[i]]=i;buildF1();}
// ---- 단순 완전탐색(검증용): 임의의 DAG 프로그램 ----
static vector<u64> pool;
static bool bf(int k){
  if(k==1){u64 t;for(size_t i=0;i<pool.size();i++)for(size_t j=0;j<pool.size();j++)for(char o:OPS)if(apply(o,pool[i],pool[j],t)&&t==T)return true;return false;}
  size_t sz=pool.size();
  for(size_t i=0;i<sz;i++)for(size_t j=0;j<sz;j++)for(char o:OPS){u64 t;if(apply(o,pool[i],pool[j],t)){pool.push_back(t);bool r=bf(k-1);pool.pop_back();if(r)return true;}}
  return false;
}

// 트리형(임시값 재사용 없음) 완전탐색: 각 임시값은 정확히 한 번 쓰인다
static vector<u64> MAT;
static bool bt(int k,vector<u64>&tmp){
  if(k==0)return tmp.size()==1&&tmp[0]==T;
  if((int)tmp.size()-1>k)return false; // 남은 k 로 임시값을 하나로 합칠 수 없다
  size_t nt=tmp.size();
  // 피연산자: 재료 또는 임시값 (임시값은 소비)
  for(int xa=-(int)MAT.size();xa<(int)nt;xa++)for(int xb=-(int)MAT.size();xb<(int)nt;xb++){
    if(xa>=0&&xb>=0&&xa==xb)continue;
    u64 x=xa<0?MAT[-xa-1]:tmp[xa],y=xb<0?MAT[-xb-1]:tmp[xb];
    for(char o:OPS){u64 r;if(!apply(o,x,y,r))continue;
      vector<u64> nt2;for(size_t i=0;i<nt;i++)if((int)i!=xa&&(int)i!=xb)nt2.push_back(tmp[i]);nt2.push_back(r);
      if(bt(k-1,nt2))return true;}}
  return false;
}
int main(int argc,char**argv){
  string mode=argc>1?argv[1]:"3";
  if(mode=="brute"){
    int Kmax=argc>2?atoi(argv[2]):3;int n;u64 Lr;int ncase;
    scanf("%d",&ncase);int bad=0,hits=0;
    for(int cs=0;cs<ncase;cs++){
      scanf("%llu %d %llu",&Lr,&n,&T);L=Lr;vector<u64>v(n);for(auto&x:v)scanf("%llu",&x);
      ns=n;setup(n,v);al.assign(N,1);Alist.clear();for(int i=0;i<N;i++)Alist.push_back(i);
      Ctx c;int k1f=searchK(Kmax,c);
      if(Kmax>=4){ // 꼴 비교
        int kt=0;MAT=v;for(int k=1;k<=Kmax&&!kt;k++){vector<u64> e;if(bt(k,e))kt=k;}
        int kb=0;pool=v;for(int k=1;k<=Kmax&&!kb;k++){if(bf(k))kb=k;}
        static int cnt_ok=0,cnt_reuse=0,cnt_bad=0,cnt_none=0;
        {static int kd[6];kd[kb]++;if(cs==ncase-1)printf("kdist %d %d %d %d %d\n",kd[0],kd[1],kd[2],kd[3],kd[4]);}if(kb==0)cnt_none++;
        else if(k1f==kb)cnt_ok++;
        else if(k1f==0&&kb==4&&kt!=4)cnt_reuse++;
        else{cnt_bad++;printf("MISMATCH case %d T=%llu search=%d brute=%d tree=%d\n",cs,T,k1f,kb,kt);}
        if(cs==ncase-1)printf("brute4: ok %d reuse-only(uncovered) %d bad %d nohit %d\n",cnt_ok,cnt_reuse,cnt_bad,cnt_none);
        continue;}
      int kb=0;pool=v;for(int k=1;k<=Kmax&&!kb;k++){if(bf(k))kb=k;}
      if(k1f)hits++;if(getenv("KDIST"))printf("K %d\n",kb);
      if(k1f!=kb){bad++;printf("MISMATCH case %d T=%llu search=%d brute=%d\n",cs,T,k1f,kb);}
    }
    printf("cases %d hits %d mismatches %d\n",ncase,hits,bad);return 0;
  }
  int K=atoi(mode.c_str());int minc=argc>2?atoi(argv[2]):2;
  scanf("%llu %d %d",&L,&ns,&nn);N=ns+nn;val.assign(N,0);
  vector<int>A(N,-1),B(N,-1);vector<char>OP(N,0),REQ(N,0);
  for(int i=0;i<ns;i++)scanf("%llu",&val[i]);
  for(int i=0;i<nn;i++){char op[4];int a,b,r;scanf("%s %d %d %d",op,&a,&b,&r);int v=ns+i;OP[v]=op[0];A[v]=a;B[v]=b;REQ[v]=r;apply(op[0],val[a],val[b],val[v]);}
  // 짝수/중복 값 검사는 호출 쪽 책임
  setup(N,val);
  vector<vector<int>> users(N);
  for(int v=ns;v<N;v++){users[A[v]].push_back(v);if(B[v]!=A[v])users[B[v]].push_back(v);}
  double tt0=chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count();
  for(int v=ns;v<N;v++){
    vector<char> in(N,0);vector<int> cnt(N);for(int i=0;i<N;i++)cnt[i]=users[i].size();
    vector<int> st={v};in[v]=1;int csz=0;
    while(!st.empty()){int w=st.back();st.pop_back();csz++;
      int ops[2]={A[w],B[w]};int no=(A[w]==B[w])?1:2;
      for(int q=0;q<no;q++){int u=ops[q];if(u<ns||REQ[u]||in[u])continue;if(--cnt[u]==0){in[u]=1;st.push_back(u);}}
      // 시작값/필수 노드는 cnt 만 줄이면 의미 없음
    }
    if(csz<minc)continue;
    vector<char> desc(N,0);{vector<int> q={v};desc[v]=1;while(!q.empty()){int w=q.back();q.pop_back();for(int u:users[w])if(!desc[u]){desc[u]=1;q.push_back(u);}}}
    al.assign(N,0);Alist.clear();for(int i=0;i<N;i++)if(!in[i]&&!desc[i]){al[i]=1;Alist.push_back(i);}
    T=val[v];int Kc=min(K,csz-1);
    printf("NODE %d %d\n",v,csz);
    int vm=vmFind(T);
    if(vm>=0){printf("HIT %d %d 0 1 0\n",v,csz);continue;}
    Ctx c;double t0=chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count();
    int k=searchK(Kc,c);
    double t1=chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count();
    if(k){printf("HIT %d %d %d %u %zu",v,csz,k,c.mask,c.hit.size());for(auto&s:c.hit)printf(" %c %d %d",s.op,s.ra,s.rb);printf("\n");}
    printf("T %d %d %.4f\n",v,Kc,t1-t0);
    fflush(stdout);
  }
  printf("TIME %.3f\n",chrono::duration<double>(chrono::steady_clock::now().time_since_epoch()).count()-tt0);
}
