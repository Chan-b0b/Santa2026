# 다른 머신에서 이어서 돌리기

이 저장소에는 문서, 코드, 결과(`results/`, `best/`), 진행 기록(`notes/`, `board/`, 실행 로그)이 들어 있다. 환경(`.venv/`, `.tools/`), 대회 자료(`data/`), 컴파일한 실행 파일은 들어 있지 않으므로 아래 순서로 다시 만든다. 끝나면 `notes/main.status.md` 맨 위부터 읽고 이어 간다.

## 1. 받기

```bash
git clone https://github.com/Chan-b0b/Santa2026.git /home/maverick/Santa2026
cd /home/maverick/Santa2026
```

**경로를 `/home/maverick/Santa2026`으로 맞춘다.** `solvers/` 아래 여러 스크립트(chain, factor, relate, fresh 등)와 `core/ops/`의 실행 스크립트에 이 절대 경로가 박혀 있다. 다른 곳에 받았으면 그 경로로 심볼릭 링크를 건다.

```bash
sudo mkdir -p /home/maverick && sudo ln -s "$(pwd)" /home/maverick/Santa2026
```

## 2. 환경

필요한 것: `uv`, `g++`(GCC 13에서 확인. Ubuntu는 `build-essential`), Python 3.12.

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python numpy numba kaggle
```

원래 머신의 판은 CPython 3.12.3, numpy 2.5.5, numba 0.68.1, kaggle 2.2.5다.

PyPy는 선택이다(표준 라이브러리만 쓰는 솔버를 빠르게 돌릴 때 쓴다. 없어도 병합, 채점, lns, walk, lend, fresh는 돈다).

```bash
UV_PYTHON_INSTALL_DIR=.tools/python uv python install pypy3.11
mkdir -p .tools/bin && ln -s ../python/pypy-3.11.*-linux-x86_64-gnu/bin/pypy3.11 .tools/bin/pypy3
```

## 3. 대회 자료

Kaggle 토큰을 `~/.kaggle/access_token`에 둔 뒤 받는다. 대회 규칙에 동의한 계정이어야 한다.

```bash
mkdir -p data
.venv/bin/python -I -m kaggle.cli competitions download -c santa-2026 -p data
cd data && unzip -o santa-2026.zip && cd ..
```

`data/puzzles.csv`, `data/practice_puzzles.csv`, `data/sample_submission.csv`가 있어야 한다.

## 4. 실행 파일 만들기

```bash
core/build.sh
```

lns, walk, exact, regfit 엔진과 숨은 정수 훑기 도구를 컴파일하고, 다른 접근법이 쓰는 lns 사본을 제자리에 복사한다.

## 5. 확인

```bash
.venv/bin/python -I core/verify.py best/best.csv     # "통과: 점수 N"
tail -1 board/history.csv                            # 둘째 칸이 같은 N이어야 한다
.venv/bin/python -I core/merge.py                    # "갱신 퍼즐 0개"가 나와야 한다
```

## 6. 이어서 돌리기

- 상태와 다음 할 일: `notes/main.status.md` 맨 위. 계획과 방법별 결과: `PLAN.md` 9절. 작업 규칙: `CLAUDE.md`.
- 병합 감시를 백그라운드로 띄운다: `core/watch.sh <알림 기준 점수>`. `results/*.csv`가 바뀌면 2분 안에 병합한다. 총점이 기준보다 1,000 낮아지면 끝나므로 그때 새 기준으로 다시 띄운다.
- 되풀이 실행의 예는 `core/ops/`에 있다(밤사이에 여러 실행을 한 줄로 이은 스크립트). 그대로 돌리는 용도가 아니라 본보기다. 앞 실행의 로그를 기다리는 줄과 이미 쓴 초반부 크기(k), 씨가 들어 있으니 고쳐서 쓴다.
  - 초반부 바꿔 끼우기: `notes/lend.md` 끝 절. 쓴 k의 기록은 `notes/main.status.md`.
  - 값 집합 걷기: `notes/walk.md`, 실행기 `solvers/walk/bench.py`.
  - 새 계보 만들어 다듬기: `notes/fresh.md`, 실행기 `solvers/fresh/drive.py`(무작위형), `drive2.py`(구조형).
- Claude Code로 이어 갈 때는 저장소 루트에서 세션을 열고 `/loop notes/main.status.md를 읽고 CLAUDE.md의 확인 절차대로 진행`을 준다. 에이전트 정의는 `.claude/agents/solver.md`에 있다.

## 7. 다시 올리기

원래 머신과 같은 스크립트를 쓴다. push 권한이 있는 GitHub 인증이 필요하다.

```bash
core/publish.sh          # 10분마다 진행 현황 화면을, 1시간마다 결과와 기록을 올린다
core/publish.sh --once   # 지금 한 번만
```

**한 번에 한 머신에서만 돌린다.** 옮길 때는 돌리던 쪽에서 `core/publish.sh --once`로 마지막 상태를 올리고 멈춘 뒤, 받는 쪽에서 `git pull` 하고 시작한다. 두 머신이 같은 결과 파일을 따로 고치면 git이 합치지 못하고 push도 실패한다. 그렇게 됐으면 한쪽의 `results/<이름>.csv`를 `results/<이름>_<머신>.csv`로 이름을 바꿔 넣고 `core/merge.py`를 돌린다. 병합은 퍼즐별로 짧은 쪽을 남기므로 잃는 것이 없다.

이 저장소는 누구나 읽을 수 있다. 비공개로 따로 올리고 싶으면 `core/sync.sh`를 쓴다(같은 내용을 두 번째 git 폴더로 다른 저장소에 올린다. 사용법은 그 파일 머리말).

## 올라가지 않는 것

| 무엇 | 왜 | 되살리는 법 |
|---|---|---|
| `.venv/`, `.tools/` | 크고 머신마다 다르다 | 2절 |
| `data/` | 대회 자료라 다시 배포하지 않는다 | 3절 |
| 컴파일한 실행 파일 | `-march=native`라 다른 CPU에서 안 돌 수 있다 | 4절 |
| `research_notes/kaggle_code/`의 노트북 소스 | 다른 참가자의 결과 프로그램이 박혀 있다 | 정리(`catalog_*.md`)는 올라간다. 소스가 필요하면 `kernels pull`로 다시 받는다 |
| 세션 임시 폴더의 로그 | 저장소 밖에 있다 | 필요한 스크립트는 `core/ops/`와 `core/watch.sh`로 옮겨 두었다 |
