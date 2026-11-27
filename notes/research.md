# Santa 2026 – Elf Calculator: 문제 해결에 쓸 수 있는 연구 조사

작성일: 2026-11-24. 대회 설명은 [intro.txt](../intro.txt), 풀이 계획은 [PLAN.md](../PLAN.md).

## 이 문서를 읽는 법

조사는 deep-research 워크플로로 했다. 검색 갈래 5개에서 출처 22개를 읽어 주장 99개를 뽑았고, 그중 상위 25개를 주장마다 3표씩 반박 검증해 22개가 통과하고 3개가 기각됐다. 문장 끝의 표시는 근거 수준이다.

| 표시 | 뜻 |
|---|---|
| [검증] | 출처 원문과 대조하는 3표 검증을 통과한 내용 |
| [재현] | 이 문서를 쓰면서 `data/puzzles.csv`로 직접 계산한 값 |
| [README] | 공개 저장소 README에 그 수치가 적혀 있음을 확인한 것. 점수 자체는 저장소 저자의 자체 보고다 |
| [미검증] | 검색 요약만 본 내용. 원문 확인이 필요하다 |
| [추론] | 출처가 직접 말하지 않은, 대회 조건으로 옮긴 설계 판단 |

인용한 이론은 거의 전부 "1에서 시작, 나눗셈 없음, 레지스터 무제한, 값 제한 없음, 단일 타깃" 모델의 결과다. 대회 조건(여러 시작값, 정확한 나눗셈, 레지스터 48개, `value_limit`, 여러 타깃)으로 옮긴 부분은 모두 [추론]이다.

## 1. 결론

1. **공개된 점수는 이미 13만 안팎이다.** 덧셈만 쓰는 논문 기법(Bos–Coster)은 약 23.2만이 나온다 [재현]. 공개 저장소가 기록한 최신 점수는 132,515이고 [README], 상위 공개 노트북은 128,500~130,000이라고 한다 [미검증]. 자명한 하한은 26,898이다.
2. **23만에서 13만으로 내려가는 차이는 곱셈과 값 공유에서 나온다.** 공개 저장소들이 쓰는 핵심은 `v = q*b ± c` 꼴로 큰 값을 줄여 가는 탐색, 여러 타깃이 함께 쓰는 중간값 먼저 만들기, 짧은 구간의 전수 탐색, 퍼즐별로 여러 설정 중 최선 고르기다 [README].
3. **무작위에 가까운 타깃에는 보편적인 지름길이 없다.** `+ - *` 프로그램의 최단 길이는 거의 모든 n에서 log n / log log n 차수다 [검증]. 추가 절감은 타깃의 구조(공통 인수, 가까운 값, 곱 근처의 값)를 찾아 쓰는 데서 나와야 한다.
4. **정확한 최적화는 짧은 부분 문제에만 현실적이다.** 가장 가까운 두 고전 문제(덧셈 전용 다중 타깃 문제, 하드웨어의 상수 곱셈 문제)가 둘 다 NP-complete다 [검증].
5. **레지스터 48개는 덧셈 전용 해에서는 걸리지 않는다.** 동시에 살아 있는 값이 최대 40개였다 [재현]. 곱셈을 쓰는 더 강한 해에서 걸리는지는 확인하지 못했다.
6. **조사하지 못한 영역이 있다.** 레지스터 제약 이론(pebbling), 탐색 기법(simulated annealing, beam search, 강화학습 등), 과거 Santa 대회 사례는 검증을 통과한 근거가 하나도 없다. 5절에 읽어 볼 출처만 적었다.

## 2. 데이터에서 확인된 전제

조사를 시작할 때는 "퍼즐당 타깃이 수백~수천 개"라고 가정했는데 실제 데이터는 다르다. 아래 값은 `data/puzzles.csv`에서 직접 다시 계산했다 [재현]. 샘플 제출 합계만 워크플로 집계이며 [PLAN.md](../PLAN.md)의 측정과 일치한다.

| 항목 | scored 1,000개 |
|---|---|
| 퍼즐당 타깃 | 1~32개, 중앙값 30. 합계 26,902개 |
| 퍼즐당 시작값 | 1~8개, 중앙값 3. 최대 1,998 |
| 시작값에 1이 있는 퍼즐 | 4개. 나머지는 `r/r`로 1을 만드는 데 명령 1개가 든다 |
| 타깃 크기 | 1~60비트, 중앙값 39비트 |
| `value_limit` | 퍼즐의 가장 큰 타깃의 1.0~5.0배, 중앙값 2.24배 |
| 샘플 제출 | 합계 1,490,379. 퍼즐 최대 2,873. 타깃당 약 55 |

- 타깃 32개와 시작값 8개를 합쳐도 40개라서, 레지스터 압박은 중간값에서만 생긴다.
- 명령 4,096개 상한은 걸리지 않는다.
- `value_limit`이 타깃보다 조금만 크므로 "타깃을 크게 넘겼다가 빼는" 방법은 폭이 좁다.

## 3. 점수 지형 (2026-11-24 기준)

| 점수 | 방법 | 근거 |
|---|---|---|
| 1,490,379 | 샘플 제출 (1을 만든 뒤 두 배와 덧셈 반복) | 워크플로 집계, PLAN.md와 일치 |
| 340,302 | 여러 진법의 Horner 중 퍼즐별 최선 (로컬) | [README] 저장소 A |
| 288,694 | 위 + 부호 있는 이진 window (폭 4, 5, 6) | [README] 저장소 A, Kaggle 제출 확인이라고 기술 |
| 239,357 | 덧셈 전용 축소, 가장 단순한 규칙 | [재현] |
| 232,223 | 위 + "기존 두 값의 합이면 그대로 사용" 규칙 | [재현] |
| 233,968 | 저장소 A의 자체 구성만 쓴 결과 | [README] 저장소 A |
| 약 165,000 | 저장소 B의 전체 세트 환산치 | [README] 저장소 B |
| 160,175 | 공개 참조 (konbu17) | [README] 저장소 A |
| 144,248 | 공개 참조 (Hanif, 버전 4) | [README] 저장소 A |
| 142,272 | 공개 노트북 (Atakan Aldemir, joint recipes, 버전 2) | [README] 저장소 A |
| 138,645 | "공개 노트북 수준"이라고만 적힌 값 | [README] 저장소 B, 출처 노트북 미기재 |
| 135,594 | 공개 노트북 "Arithmetic Graph Rewrites" | [미검증] 검색 요약 |
| 132,515 | 저장소 A의 최신 체크포인트 (goodpjw2008 데이터셋 버전 55의 132,516 기반) | [README] 저장소 A, Kaggle 제출 확인이라고 기술 |
| 128,500~130,000 | 상위 공개 노트북 | [미검증] 검색 요약. Kaggle 페이지는 직접 읽지 못했다 |
| 26,898 | 하한: 시작값에 없는 타깃마다 명령 1개 | [재현]. PLAN.md, 저장소 B README와 일치 |

저장소 A는 `github.com/Juan-Severiano/santa-2026`, 저장소 B는 `github.com/Yukisiooisiiyo/kaggle-santa`다. 저장소 A는 100,000 미만을 목표로 적었지만 "아직 연구 중이며 실험 결과가 100,000 미만을 뒷받침하지 않는다"고 썼다 [README].

## 4. 기법별 정리

### 4.1 Bos–Coster makesequence: 여러 타깃을 위에서 아래로 줄이기

- **핵심.** 만들어야 할 값들의 집합에서 가장 큰 값 f를 꺼내 더 작은 값들의 합으로 바꾸는 일을 시작값만 남을 때까지 반복한다. 규칙은 네 가지이고 그중 "비용이 가장 낮은 것"을 고른다 [검증].
  - Approximation: 기존 두 값의 합이 f보다 조금 작으면(`a+b = f-ε`) `a+ε`를 추가한다.
  - Division: f가 3, 5, 9, 17로 나누어지면 `f/p, 2f/p, …`를 추가한다.
  - Halving: 작은 기존 값 s에 대해 `f-s, (f-s)/2, (f-s)/4, …`를 추가한다.
  - Lucas: f로 끝나는 Lucas형 수열을 추가한다.
- **출처.** Bos & Coster, "Addition chain heuristics", CWI Report CS-R8945 (CRYPTO '89), 6절. <https://ir.cwi.nl/pub/5809/5809D.pdf>
- **한계.** 규칙을 고르는 비용 함수는 논문에 윤곽만 있고 저자들도 만족스럽지 않다고 썼다 [검증]. 덧셈 전용이다. 공개 구현 `mmcloughlin/addchain`은 Division과 Lucas를 구현하지 않았다고 밝힌다.
- **대회에서의 결과 [재현].** 가장 단순한 형태만으로 샘플 제출의 약 16% 길이가 나온다.

  ```
  S = 시작값 ∪ {1} ∪ 타깃
  S의 값을 큰 것부터 꺼낸다. 시작값과 1은 건너뛴다.
    f = 꺼낸 값, s = S에서 f 다음으로 큰 값
    (선택 규칙) S 안에 a + b = f인 쌍이 있으면 그대로 쓴다
    f >= 2s 이면: f가 짝수면 f = f/2 + f/2, 홀수면 f = (f-1) + 1
    아니면:       f = s + (f-s)
    새로 생긴 값은 S에 넣는다. 꺼낸 값마다 명령 1개.
  ```

  | 규칙 | 명령 합계 | 타깃당 | 동시에 살아 있는 값 |
  |---|---|---|---|
  | 선택 규칙 없음 | 239,357 | 8.90 | 중앙값 35, 최대 40 |
  | 선택 규칙 포함 | 232,223 | 8.63 | 중앙값 35, 최대 40 |

  모든 중간값이 가장 큰 타깃 이하라서 `value_limit` 위반은 0건이고, 48개를 넘는 퍼즐도 0개다. 이 수치는 명령 개수만 센 것이고, 실제 프로그램을 만들어 [core/verify.py](../core/verify.py)로 돌려 본 것은 아니다. 살아 있는 값은 작은 값부터 계산하는 순서에서, 시작값과 1을 계속 보관한다고 보고 셌다.
- **확장 방향 [추론].** 종료 조건은 이미 "시작값만 남을 때"로 바꿨다. 다음은 Division 규칙을 "기존 값이나 작은 수로 나누어지면 곱셈 1회"로 넓히는 것, `f = a*b ± e` 규칙을 넣는 것, 비용 함수와 동점 처리를 무작위화해 여러 번 돌리는 것이다.

### 4.2 Window와 Horner: 항상 유효한 안전한 상한

- **핵심.** 타깃을 B진법 자릿수로 나누고, 자릿수 값들을 레지스터에 올린 뒤 `acc = acc*B + d`를 반복한다.
- **출처.** Bos & Coster(위 논문)는 512비트 수에서 평균 길이 605를 보고했다. 이진법 768보다 21%, Knuth의 5-window보다 5% 짧다 [검증]. 표 전체 대신 필요한 자릿수 값만 만들면 더 큰 window를 쓸 수 있다. Jindal & Saranurak Lemma 3은 `+`와 `*`만으로 `(2^k - 1) + 2m`의 상한을 준다 [검증]. <https://arxiv.org/abs/1212.2549>
- **대회에서의 위치 [추론].** 곱셈이 명령 1개라서 자릿수 하나에 명령 2개가 든다. 5비트 자릿수면 39비트 타깃에 최대 16개, 60비트 타깃에 최대 24개다. 4.1의 타깃당 8.6보다 나쁘다. 저장소 A의 실측도 같은 방향이다(진법 묶음 340,302, 부호 있는 window 추가 288,694) [README]. 논문의 21%와 5%는 두 배 연산의 비용 모델이 달라 그대로 옮겨지지 않는다.
- **쓸모.** 중간값이 타깃의 앞부분이라 타깃을 넘지 않는다. 어떤 퍼즐에도 유효한 해를 주는 첫 기준선으로 쓴다.

### 4.3 τ(n) 이론: 어디까지 줄일 수 있는가

- **핵심.** τ(n)은 1에서 시작해 `+ - *`로 n을 만드는 최단 프로그램의 길이다.
  - 모든 n ≥ 2에서 `log2 log2 n` 차수 이상, `2 log2 n` 이하다. 제곱을 k번 반복하면 `2^(2^k)`가 k단계에 나온다 [검증].
  - 거의 모든 n에서 `log n / log log n` 차수다. 길이 n인 프로그램이 표현할 수 있는 수가 최대 `2^(3n log n)`개뿐이라는 개수 세기 논법이다 [검증].
- **출처.**
  - de Melo & Svaiter, Proc. AMS 124 (1996). <https://www.ams.org/journals/proc/1996-124-05/S0002-9939-96-03173-5>
  - Moreira, Proc. AMS 125 (1997). <https://www.ams.org/journals/proc/1997-125-02/S0002-9939-97-03583-1/S0002-9939-97-03583-1.pdf>
  - Jindal & Saranurak, "Subtraction makes computing integers faster". <https://arxiv.org/abs/1212.2549>
  - Markström, "The straight line complexity of small factorials and primorials". <https://arxiv.org/abs/1306.3091>
  - OEIS A173419. <https://oeis.org/A173419>
- **대회에서의 뜻 [추론].** 정확한 나눗셈은 최댓값을 키우지 못하고 연산 종류가 4개로 늘 뿐이라 하한의 형태는 유지된다. 다만 수치로는 약하다. 상수를 무시하고 식에 넣으면 64비트 타깃 하나에 약 11개이고, 타깃 여러 개가 중간값을 공유하면 타깃당 값은 더 내려간다. 실용적으로는 "타깃당 명령 1개"(합계 26,898)가 쓸 수 있는 하한이다.
- **주의.** 시작값이 1이 아니면 논문의 공식이 그대로 성립하지 않는다(시작값 3에서 9는 명령 1개). 이 점을 무시한 주장 2건이 검증에서 기각됐다(7절).

### 4.4 뺄셈과 "곱 근처" 패턴

- **핵심.** 뺄셈은 무작위 타깃에서는 점근적 이득이 없다. 구조가 있는 수에서는 단계를 줄인다 [검증].
  - `N = 2^(2^n)`일 때 `N-1`은 뺄셈이 있으면 n+2단계, 없으면 n+3단계 이상이다. 증명된 차이는 1단계뿐이다.
  - 3359 = 15³ − 16은 `1, 2, 4, 16, 15, 225, 3375, 3359`의 7단계다. 바로 옆의 3358은 8단계가 필요하다 (OEIS A173419의 관찰이며 일반 정리는 아니다).
- **출처.** Jindal & Saranurak 3절, OEIS A173419, Bos & Coster 7절.
- **대회 적용 [추론].** 타깃 T마다 "레지스터에 있거나 싸게 만들 수 있는 a, b의 곱이 T 근처이고 나머지 `|T − a*b|`가 싸게 만들어지는" 후보를 찾는다. 저장소 B의 `v = q*b ± c` 축소 탐색이 같은 생각이다 [README]. `value_limit` 때문에 T를 넘겼다가 빼는 폭은 제한된다.
- **빈칸.** 정확한 나눗셈의 효과를 다룬 검증된 출처는 없다. 5절의 Borwein–Hobart 자료가 가장 가깝지만 내림 나눗셈과 지수적으로 큰 중간값에 의존한다.

### 4.5 정확한 탐색: 짧은 프로그램의 최적해

- **핵심.**
  - 최적 덧셈 체인은 가지치기 한계를 쓰는 깊이 우선 탐색으로 구한다. 실패하면 길이를 1 늘려 다시 한다 [검증].
  - `+ - *` 프로그램의 정확한 값은 길이별 전수 탐색으로 구하고, "계산된 값의 집합"이 같은 프로그램은 하나만 남긴다. 값이 서로 다르고 양수인 프로그램만 봐도 최적성이 유지된다 [검증].
- **출처.**
  - Thurber & Clift, "Addition chains, vector chains, and efficient computation", Discrete Mathematics 344(2), 2021. Thurber(1999)를 일반화한 새 가지치기 한계 두 개. <https://doi.org/10.1016/j.disc.2020.112200>
  - Clift, "Calculating optimal addition chains", Computing 91(3), 2011. n ≤ 2^32 전체의 최적 길이를 계산했다. <https://link.springer.com/article/10.1007/s00607-010-0118-8>
  - Markström(위)의 Definition 2.2와 탐색 절차, OEIS A173419(길이 8까지 전수 탐색).
- **대회 적용 [추론].** 대략 명령 8~9개 이하의 부분 프로그램을 다시 짧게 만드는 데와, 퍼즐의 시작값에서 k개 명령 안에 닿는 값의 표를 만드는 데 설계 패턴으로 쓴다. 저장소 B는 명령 3개까지 전수 탐색, 표를 써서 4~5개까지 한다 [README]. PLAN.md 5절의 깊이 4~6 한계와 맞는 수준이다.
- **그대로 옮겨지지 않는 부분.**
  - Thurber형 한계는 "다음 값이 현재 값의 2배 이하"라는 단조성에 기댄다. 곱셈이 있으면 "남은 k단계에 대해 현재 최댓값 ≥ 타깃^(1/2^k)" 정도의 약한 조건만 남고, 뺄셈과 나눗셈은 단조성을 깬다.
  - 레지스터가 실제로 모자라면 상태는 "살아 있는 값들 + 이미 만든 타깃 집합"이어야 한다. 버린 값을 다시 계산해야 할 수 있어 "값이 서로 다르다"는 조건이 손실을 낸다.

### 4.6 상수 곱셈 문제(MCM)와 Hcub

- **핵심.** MCM(multiple constant multiplication)은 하드웨어에서 여러 상수 곱을 덧셈, 뺄셈, 자리 이동만으로 만들 때 덧셈기 수를 최소화하는 문제다. 타깃 집합이 중간값을 공유하는 최소 연산 그래프를 찾는다는 점에서 이 대회와 구조가 같다. Hcub 알고리즘은 발표 당시 최고였던 RAG-n보다 덧셈기를 최대 20% 줄였다 [검증].
- **출처.** Voronenko & Püschel, "Multiplierless Multiple Constant Multiplication", ACM TALG 3(2), 2007. <https://spiral.ece.cmu.edu/pub-spiral/abstract.jsp?id=28>, 생성기 <https://spiral.ece.cmu.edu/mcm/gen.html>
- **대회 적용 [추론].** 자리 이동이 무료이고 레지스터와 값 제한이 없는 모델이라 수치는 옮겨지지 않는다(대회에서는 2의 거듭제곱 곱도 명령 1개). 옮길 수 있는 것은 "남은 타깃들까지의 추정 거리를 가장 많이 줄이는 중간값을 하나씩 추가한다"는 탐욕 틀이다. 저장소 B의 "여러 타깃이 2단계 안에 닿는 중간값 먼저 만들기"가 같은 틀이다 [README].
- **주의.** 20%는 저자가 보고한 최선 사례이고 2007년 기준이다. Hcub 내부 동작에 대한 위 설명은 검증 범위 밖의 배경지식이다.

### 4.7 MCM의 정수계획 정식화: 짧은 프로그램을 정확히 풀기

- **핵심.** 연산 칸 수를 휴리스틱 해의 길이로 고정하고, 칸별 "사용 여부" 이진 변수의 합을 최소화한다. 칸 수가 고정되면 순수한 결정 문제가 된다 [검증].
- **출처.** Garcia & Volkova, "Towards the Multiple Constant Multiplication at Minimal Hardware Cost", arXiv:2210.02742. <https://arxiv.org/pdf/2210.02742>
- **실험 결과 [검증].** Gurobi, 30분 제한, 벤치마크 86개에서 대부분 10초 안에 최적성을 증명하거나 시간 초과였다. 덧셈기 수 기준으로 약 2/3만 증명됐다. 난이도는 타깃 개수보다 계수 크기에 좌우됐고 12비트부터 증명이 안 됐다.
- **대회 적용 [추론, 검증 2-1 통과].** 휴리스틱 길이를 칸 상한으로 둔 CP-SAT 모델을 작은 부분 문제에 쓴다. 주의할 점은 세 가지다.
  - 대회의 `*`와 `/`는 두 레지스터 변수 사이의 연산이라 선형이 아니다.
  - CP-SAT은 64비트 정수 범위에 묶이는데 타깃이 최대 60비트다.
  - 레지스터 수와 양수 조건을 직접 추가해야 한다.
- **실전 보고.** 저장소 A는 SciPy/HiGHS로 "퍼즐 전체에서 어떤 조립법을 고를지"를 정수계획으로 풀고, CP-SAT으로 대안 프로그램 최대 8개를 재조합한다 [README].

### 4.8 계산 복잡도

- **핵심.** 1에서 시작해 여러 양의 정수를 모두 만드는 최소 덧셈 수 문제(addition-sequence problem)는 NP-complete다. MCM의 최소 덧셈기 문제도 NP-complete다 [검증].
- **출처.** Downey, Leong & Sethi, "Computing Sequences with Addition Chains", SIAM J. Comput. 10(3), 1981. <https://doi.org/10.1137/0210047> MCM 쪽은 Voronenko & Püschel(위).
- **주의.** 두 결과 모두 이 대회 문제 자체의 난해성을 증명하지는 않는다. Downey–Leong–Sethi 결과는 "타깃 하나짜리 덧셈 체인이 NP-complete"라는 뜻으로 자주 잘못 인용된다.

### 4.9 공개 저장소가 보고한 실전 기법

두 저장소 모두 README의 자체 보고이며, 코드나 점수를 직접 돌려 확인하지는 않았다.

**저장소 B** (`Yukisiooisiiyo/kaggle-santa`). practice 200개에서 32,580, 설정 하나만 쓰면 32,888.

1. 명령 3개 이하 전수 탐색. 표를 쓰면 4~5개까지.
2. 여러 타깃이 2단계 안에 닿는 중간값을 먼저 만든다.
3. 큰 값 v를 `v = q*b ± c`, `v = a ± x`, 제곱근, 반으로 나누기로 줄여 가는 최선 우선 탐색. 끝은 전수 탐색으로 마무리한다.
4. 남은 타깃 여러 개를 시도해 가장 싼 것부터 만든다.
5. 레지스터가 48개를 넘으면 크고 오래 안 쓴 값부터 버리고 작은 값은 남긴다.
6. 어떤 타깃에도 기여하지 않는 명령을 지운다.

**저장소 A** (`Juan-Severiano/santa-2026`). 공개 참조 위에 자체 개선을 얹는 방식.

- 진법 묶음, 부호 있는 이진 window, 명령 1개로 닿는 타깃 탐지, 차이와 정확한 인수 재사용.
- 정수계획으로 조립법 전역 선택, Rust로 쓴 LNS(large neighborhood search: 프로그램 일부를 허물고 다시 짓는 지역 탐색), CP-SAT 재조합, beam search, 3~8개 명령 구간 치환.
- **효과가 작거나 없었다고 보고한 것.** 공개 참조 위에 자체 개선으로 얹은 이득은 1~438개였다(160,175 → 159,737, 132,516 → 132,515). 132,542 기준선에서 인수 묶음 탐색, 구간 치환, 6~10개 타깃 묶음 최적화, 대안 656개 재조합은 이득 0이었다.

여기서 읽을 수 있는 것 [추론]: 13만대에 이른 해는 지역 탐색으로 잘 줄지 않는다. 그 아래로 가려면 구성 방법 자체가 달라야 할 가능성이 높다. 퍼즐별로 여러 설정 중 최선을 고르는 것만으로 저장소 B는 practice에서 308개를 줄였다(32,888 → 32,580).

## 5. 읽어 볼 만하지만 검증하지 못한 출처

아래는 검색 단계에서 수집됐지만 검증 대상에 들지 못했다. 요약은 검색 결과 기준이다 [미검증].

| 주제 | 출처 | 검색 요약 |
|---|---|---|
| 레지스터 배정 | Sethi, "Complete Register Allocation Problems", SIAM J. Comput. 1975. <https://www.doi.org/10.1137/0204020> | 레지스터 수가 고정된 연산 그래프 평가를 돌 놓기 게임으로 모델링. 여러 변형이 NP-complete. 트리일 때만 Sethi–Ullman이 최적 순서를 준다 |
| 체인 길이와 메모리 | Sauerbrey & Dietel, EUROCRYPT '92. <https://link.springer.com/doi/10.1007/3-540-47555-9_15> | 체인이 짧을수록 레지스터가 더 필요하다. 이진법은 레지스터 2개면 된다 |
| 시간–공간 관계 | Savage, Models of Computation 10장. <https://cs.brown.edu/people/jsavage/book/pdfs/ModelsOfComputation_Chapter10.pdf> | pebble game 교과서 정리 |
| MCM 정확 탐색 | Aksoy, Güneş & Flores, Microprocessors and Microsystems 34(5), 2010. <https://research.itu.edu.tr/en/publications/search-algorithms-for-the-multiple-constant-multiplications-probl/> | 상한과 하한을 쓰는 정확한 깊이 우선 탐색 |
| MCM 정확 탐색 | Thong, McMaster 석사논문, 2009. <https://www.ece.mcmaster.ca/~nicola/thesis/jason_masc_2009.pdf> | 휴리스틱을 가지치기에 재사용하는 최적 알고리즘 |
| MCM의 SAT 인코딩 | arXiv:1011.2685. <https://arxiv.org/pdf/1011.2685> | pseudo-Boolean SAT 인코딩 세 가지 |
| 나눗셈의 힘 | Lipton & Regan 블로그 (Borwein & Hobart 논문 소개). <https://rjlipton.com/2012/10/16/one-mans-floor-is-another-mans-ceiling/> | 내림 나눗셈으로 계승을 짧게 계산. 대회는 정확한 나눗셈만 되고 값 상한이 있어 그대로는 못 쓴다 |
| 공개 노트북 | Kaggle Code 탭. <https://www.kaggle.com/competitions/santa-2026/code> | 상위 점수 128,500~130,000. "Arithmetic Graph Rewrites" 135,594. EDA 노트북 "Inside the Elf's Calculator" |

레지스터 쪽 자료에서 나온 제안 [추론]: 먼저 레지스터 제한 없이 짧은 프로그램을 만들고, 마지막 사용 시점 분석으로 레지스터를 재배정한 뒤, 48개를 넘는 구간만 순서 변경이나 재계산으로 고친다.

## 6. 권장 순서

[PLAN.md](../PLAN.md) 4절과 방향이 같다. 이번 조사로 더하거나 바꿀 점만 적는다. 1번만 실측 근거가 있고 나머지는 [추론]이다.

1. **기준선에 4.1의 덧셈 전용 축소를 넣는다.** Horner(타깃당 16~24)보다 훨씬 짧고(타깃당 8.6) 제약 위반이 없다. 퍼즐별로 Horner와 비교해 짧은 쪽을 남긴다.
2. **공개 노트북을 먼저 읽고 채점기로 재현한다.** 공개 수준이 13만 안팎이라면 23만짜리 자체 기준선은 출발점으로 약하다. 공개 프로그램을 가져다 쓸지는 라이선스와 대회 규칙을 확인하고 정한다.
3. **축소 탐색을 주력으로 만든다.** 4.1의 틀에 `v = q*b ± c`, 기존 값으로 나누어지면 곱셈 1회, 가까운 타깃끼리의 차이를 규칙으로 넣는다. PLAN.md 3번의 양방향 탐색과 같은 것이며, 끝은 짧은 전수 탐색 표로 마무리한다.
4. **공유 중간값을 먼저 만든다.** 여러 타깃이 한두 단계 안에 닿는 값에 표를 줘서 고른다(4.6, 4.9).
5. **퍼즐별 최선 모으기.** 설정과 난수를 바꿔 여러 번 돌리고 퍼즐마다 가장 짧은 프로그램만 남긴다. 점수가 퍼즐별 합이고 숨겨진 평가 세트가 없어서 손해가 없다.
6. **구간 재합성은 기대치를 낮게 잡는다.** 저장소 A의 보고대로면 13만대 해에서 지역 탐색으로 얻은 이득은 0~1개였다.

## 7. 검증에서 기각된 주장

아래 3건은 3표 모두 반박해 본문에 쓰지 않았다.

1. "전수 탐색은 길이 9~11까지만 가능하므로 정확한 탐색의 한계는 타깃당 9~11개 명령이다." Markström 논문의 구체 수치와 결론이 출처와 맞지 않았다.
2. "`log2 log2 n + 1 ≤ τ(n) ≤ 2 log2 n`이 Santa 점수의 절대 하한과 상한을 준다." 시작값이 1이 아니면 식이 깨진다.
3. "τ(n) ≤ 정수 복잡도 ≤ 최단 덧셈 체인 ≤ 이진법 길이 ≤ 2⌊log2 n⌋의 부등식 사슬." 출처가 뒷받침하지 않았다.

덧셈 전용 프로그램이 1을 만든 뒤 대회에서 유효한 프로그램이 된다는 점은 별도로 확인됐다.

## 8. 한계와 열린 질문

**한계**

- 원문 전체를 확인하지 못한 출처가 있다. Downey–Leong–Sethi와 Thurber–Clift는 초록만 봤고, de Melo–Svaiter는 2차 자료로 확인했다.
- Hcub와 MCM 정수계획 주장은 반박 자료 검색이 예산 소진으로 생략됐다.
- Kaggle 페이지는 직접 읽지 못했다. 공개 노트북 점수와 리더보드는 빠르게 바뀌므로 직접 확인해야 한다.
- Santa 2026 토론 글, 과거 Santa 대회(2023~2025) 사례, Countdown 숫자 게임 풀이는 조사되지 않았다.

**열린 질문**

- 타깃은 어떻게 만들어졌는가? 숨은 짧은 프로그램에서 나온 수라면 그 구조를 복원하는 쪽이 일반 탐색보다 유리하다. `scored_0003`에는 차이가 635,670뿐인 타깃 쌍(56120673617898, 56120674253568)이 있다.
- 곱셈과 정확한 나눗셈 규칙 중 무엇이 실제 데이터에서 효과가 있는가? 검증된 자료가 없다.
- 곱셈 기반의 강한 해에서 레지스터 48개가 실제로 모자라는가?
- 40~60비트 규모에서 beam search, simulated annealing, CP-SAT, 구간 재합성 중 무엇이 통하는가?

## 9. 출처 목록

**검증을 통과한 주장의 출처**

- Bos & Coster, Addition chain heuristics: <https://ir.cwi.nl/pub/5809/5809D.pdf>
- Downey, Leong & Sethi, Computing Sequences with Addition Chains: <https://doi.org/10.1137/0210047>
- Thurber & Clift, Addition chains, vector chains, and efficient computation: <https://doi.org/10.1016/j.disc.2020.112200>
- Clift, Calculating optimal addition chains: <https://link.springer.com/article/10.1007/s00607-010-0118-8>
- de Melo & Svaiter, The cost of computing integers: <https://www.ams.org/journals/proc/1996-124-05/S0002-9939-96-03173-5>
- Moreira, On asymptotic estimates for arithmetic cost functions: <https://www.ams.org/journals/proc/1997-125-02/S0002-9939-97-03583-1/S0002-9939-97-03583-1.pdf>
- Jindal & Saranurak, Subtraction makes computing integers faster: <https://arxiv.org/abs/1212.2549>
- Markström, The straight line complexity of small factorials and primorials: <https://arxiv.org/abs/1306.3091>
- OEIS A173419: <https://oeis.org/A173419>
- Voronenko & Püschel, Multiplierless Multiple Constant Multiplication: <https://spiral.ece.cmu.edu/pub-spiral/abstract.jsp?id=28>, <https://spiral.ece.cmu.edu/mcm/gen.html>, <https://spiral.net/hardware/multless.html>
- Garcia & Volkova, Towards the Multiple Constant Multiplication at Minimal Hardware Cost: <https://arxiv.org/pdf/2210.02742>

**README 내용을 확인한 공개 저장소**

- <https://github.com/Juan-Severiano/santa-2026>
- <https://github.com/Yukisiooisiiyo/kaggle-santa>

**검색 요약으로만 본 Kaggle 노트북**

- <https://www.kaggle.com/code/atakanaldemir/santa-2026-joint-recipes-for-large-puzzles>
- <https://www.kaggle.com/code/bikrambasnet1/santa-2026-arithmetic-graph-rewrites>
- <https://www.kaggle.com/code/evgendvorkin/santa-2026-inside-the-elf-s-calculator>

그 밖의 미검증 출처는 5절 표에 있다.
