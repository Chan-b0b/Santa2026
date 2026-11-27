# fresh: 새로 구성한 프로그램을 lns로 다듬어 best와 견주기

코드 `solvers/fresh/`(`gen.py` 구성, `drive.py` 구성+lns+기록, `analyze.py` 집계, `pick.py` 퍼즐 뽑기), 결과 `results/fresh.csv`, 실행 기록 `solvers/fresh/runs1.jsonl`(1단계), `runs2.jsonl`(2단계), 로그 `c0~c4.log`, `s2_0~3.log`.

## 방법
- 무작위형(family_guess indep 247개)에서 큰 퍼즐 10개(big48.txt), 아닌 퍼즐 10개를 시드 2026으로 뽑아 `puzzles20.json`에 best 길이와 함께 고정.
- 퍼즐당 새 구성 10개: chain(vchain 설정 3종), relate(solver3, rseed/noise/W2 3종), search(VARIANTS 3종), factor(1종). 구성기는 고치지 않고 불러 썼다.
- 각 구성을 `elf_lns`(run_cpp 기본 옵션, 75초, 씨 다름)로 다듬는다. 총 200회.

## 1단계 결과 (200회, 무효 0)
- 이긴 실행 7회(3.5%), 이긴 퍼즐 4개(0010, 0096, 0121, 0446), 동률 16회, 줄어든 합 10(퍼즐별 최대 이득 3+4+1+2).
- 퍼즐별 최솟값-best: 이김 -4,-3,-2,-1 / 0이 5개 / +1~+2 4개 / +3~+7 7개. 최솟값이 +2 이내인 퍼즐 13/20, +5 이상 3/20. 큰 퍼즐 10개 중 이긴 것은 0446 하나, 큰 퍼즐 최솟값은 -2~+7.
- 중앙값(퍼즐별 "다듬은 길이-best"): 작은 퍼즐 1~4, 큰 퍼즐 6~13.
- 솔버별(실행 수, 이긴 수, 평균 차이, 퍼즐별 최솟값 평균): chain 60/1/+5.2/3.0, search 60/2/+5.9/3.5, relate 60/4/+8.2/5.6, factor 20/0/+4.5/4.5. relate는 평균이 가장 나쁘지만 편차가 커서 이긴 횟수가 많다.
- 원출력/best 평균: chain 1.09, search 1.09, factor 1.08, relate 1.14. 원출력과 다듬은 길이의 상관(퍼즐 내부 평균) 0.46, 비율로 전체를 묶으면 0.08.
- 판단: 이긴 실행 4회 이상 -> 2단계.

## 2단계 (일부)
무작위형 나머지 227개 중 무작위 24개, 퍼즐당 10회(relate 4, search 3, chain 3), lns 75초 x min(1,n/150)(하한 0.4). 240회: 이긴 21회, 이긴 퍼즐 8개, 줄어든 합 12(발견 당시 best 기준). 이긴 실행의 솔버 수는 1~2단계 합쳐 relate 13, search 8, chain 7.
이 때 results/fresh.csv: 유효 11개, 명령 합계 1644. 나중에 확인하니 메인 병합이 반영해 best와 같아진 퍼즐이 10개, 아직 1 짧은 것이 0279 하나.

## 효과 없던 것
- 원출력 길이로 미리 고르기(상관 낮음). factor는 이긴 적 없음(20회). 큰 퍼즐은 거의 못 이김(최솟값 평균 +3).
- 이득의 대부분은 짧은(150 이하) 퍼즐에 몰린다.

## 남은 일 (메인 세션)
나머지 203개를 같은 방식으로: 15분에 퍼즐 약 6개. 예)
`for c in 0 1 2 3; do .venv/bin/python -I -u solvers/fresh/drive.py $c 4 75 solvers/fresh/runs3.jsonl --ids <ids.json> --scale --rseed 9000 --cfgs relate:0,relate:1,relate:2,relate:3,search:0,search:2,chain:0,chain:1,chain:2,search:1 > solvers/fresh/s3_$c.log 2>&1; done`
(`ids.json`은 `{퍼즐id: best길이}`; 후보는 `solvers/fresh/indep_rest.json`의 25번째부터.) 전부 돌리면 약 8시간(프로세스 5개).

## 구조형·mixed 시험
코드 `solvers/fresh/gen2.py`(씨앗 구성), `drive2.py`(drive.py 사본, gen2 호출), 퍼즐 `puzzles30.json`(best 길이 포함), 씨앗 `bases_pick.json`(퍼즐마다 bases8, bases3f, bases6, bases_rel_new 중 정수가 가장 많은 목록의 앞 8개, 그대로 사용), 기록 `runs5.jsonl`, 로그 `s5_0~4.log`.
- 퍼즐 30개: 구조형 15(큰 퍼즐 2), mixed 15(큰 퍼즐 3). 퍼즐당 10회 = relate(solver3.solve_once, seeds) 6회 + chain(chain_seed.solve) 4회, lns 75초 x min(1, n/150)(하한 0.4). 씨앗 방식: full(목록 그대로), sorted, 섞기, 앞쪽 절반, 내림차순(relate만). 300회, 무효 0.
- 이긴 실행 7회(2.3%), 동률 15회, 이긴 퍼즐 3개(0696, 0210, 0806), 줄어든 합 4(0696 -1, 0210 -2, 0806 -1). 전부 구조형. 합 4로 보면 구조형 150회 중 7회 이김, mixed 150회 중 0회(최솟값도 +0 이상, 평균 +9.5).
- 퍼즐별 최솟값-best: 구조형 15개 -2,-1,-1,0,0,0,1,1,1,1,1,3,4,4,4 / mixed 15개 0,0,0,1,2,2,3,4,5,5,6,7,9,10 (+0 ~ +10). 최솟값 +2 이내 17/30, +5 이상 6/30(전부 mixed).
- 가족별 평균(다듬은 길이-best): 구조형 +5.2(중앙값 3), mixed +9.5(중앙값 8). 원출력은 best의 1.21배.
- 솔버별: chain 120회 4승 평균 +8.9, relate 180회 3승 평균 +6.3. 씨앗 방식별 평균: 섞은 chain +17.3(이 방식만 크게 나쁨, 그래도 1승), 나머지 +5.5~+7.1. 이긴 7회는 방식에 고루 퍼져 있어 특정 방식이 낫다고 할 근거는 없다.
- 판단: 이긴 실행 6회 이상이라 기준은 넘지만 구조형에만 해당. mixed는 접는다(최솟값이 대부분 best+3 이상, 이긴 적 없음). 구조형은 이득이 작다(퍼즐당 1~2).
- 넓히는 명령(메인 세션): 해독 정수가 2개 이상인 구조형 335개, 변형은 `relate:0,relate:2,relate:3,relate:5,chain:6,chain:7,chain:9`(섞은 chain 제외 7개)로, 6~7퍼즐씩 15분 묶음. 5프로세스, 다른 실행과 겹치면 300회에 80분이 걸렸다(335개 x 7회면 약 8시간 이상).
`for c in 0 1 2 3; do .venv/bin/python -I -u solvers/fresh/drive2.py $c 4 75 solvers/fresh/runs6.jsonl --ids <ids.json> --scale --rseed 9500 --cfgs relate:0,relate:2,relate:3,relate:5,chain:6,chain:7,chain:9 > solvers/fresh/s6_$c.log 2>&1; done`  (`bases_pick.json` 에 키가 있는 구조형 id 6~7개씩)
