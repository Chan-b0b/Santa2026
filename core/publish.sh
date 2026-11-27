#!/usr/bin/env bash
# GitHub에 두 가지를 올린다.
#   1. board/ (진행 현황 화면). GitHub Pages가 이것을 보여 준다. 10분마다.
#   2. 실행 결과와 진행 기록(문서, 코드, results/, best/, notes/, 실행 로그). 다른 머신에서 이어서
#      돌릴 수 있게 하는 것이다. 1시간마다. 무엇이 올라가고 빠지는지는 .gitignore 가 정한다.
#
# 이 저장소는 누구나 읽을 수 있다. 사용자가 2026-11-27에 결과와 솔버를 공개해도 된다고 정했다.
# 대회 자료(data/)와 다른 참가자의 노트북 소스는 우리 것이 아니라서 .gitignore 로 빼 둔다.
#
# 사용법 (샌드박스 밖, 사용자 터미널에서 돌린다. push에 사용자의 GitHub 인증이 필요하다):
#     core/publish.sh                 10분마다 확인해서 바뀌었으면 커밋하고 push 한다. Ctrl+C 로 멈춘다.
#     core/publish.sh --once          한 번만 하고 끝낸다(화면과 결과·기록 둘 다).
#     core/publish.sh --board-only    화면만 올린다. 결과와 기록은 올리지 않는다.
#     INTERVAL=900 core/publish.sh    화면을 확인하는 간격(초)을 바꾼다.
#     STATE_INTERVAL=7200 core/publish.sh   결과와 기록을 올리는 간격(초)을 바꾼다.
#
# 화면 커밋은 board/, index.html, .nojekyll 만 담는다. 결과·기록 커밋은 .gitignore 에 걸리지 않는 전부를 담는다.
# 화면 간격은 10분보다 짧게 잡지 않는다. GitHub Pages 의 권장 한도가 시간당 빌드 10회다.
# 결과 파일은 몇 MB씩이라 자주 커밋하면 저장소가 빨리 커진다. 그래서 결과·기록은 간격을 길게 둔다.
# 한 번에 한 머신에서만 돌린다. 다른 머신에서 이어 받을 때는 먼저 git pull 한다(SETUP.md).
set -u
cd "$(dirname "$0")/.." || exit 1

INTERVAL="${INTERVAL:-600}"
STATE_INTERVAL="${STATE_INTERVAL:-3600}"
BRANCH="${BRANCH:-master}"
PATHS=(board index.html .nojekyll)
ONCE=0
STATE=1
for arg in "$@"; do
    case "$arg" in
        --once) ONCE=1 ;;
        --board-only) STATE=0 ;;
        *) echo "모르는 인자: $arg" >&2; exit 2 ;;
    esac
done

# 두 개가 동시에 돌지 않게 한다.
exec 9>.git/publish.lock
if ! flock -n 9; then
    echo "publish.sh 가 이미 돌고 있다" >&2
    exit 1
fi

log() { echo "$(date '+%F %T') $*"; }

last_state=0

publish() {
    local current total now
    current=$(git symbolic-ref --short -q HEAD)
    if [ "$current" != "$BRANCH" ]; then
        log "건너뜀: 현재 브랜치가 $BRANCH 가 아니다 (${current:-detached})"
        return 1
    fi
    total=$(tail -n 1 board/history.csv | cut -d, -f2)

    # 1. 화면. 병합 도중에 생기는 임시 파일(*.tmp<pid>)은 올리지 않는다.
    git add -A -- "${PATHS[@]}" ':(exclude)board/*.tmp*' || return 1
    if ! git diff --cached --quiet -- "${PATHS[@]}"; then
        git commit -q -m "board: 총점 $total" -- "${PATHS[@]}" || return 1
        log "커밋: 총점 $total"
    fi

    # 2. 결과와 진행 기록. 간격이 찼을 때만.
    now=$(date +%s)
    if [ "$STATE" = 1 ] && [ $((now - last_state)) -ge "$STATE_INTERVAL" ]; then
        git add -A . || return 1
        if ! git diff --cached --quiet; then
            git commit -q -m "state: 총점 $total" || return 1
            log "커밋: 결과와 진행 기록 (총점 $total)"
        fi
        last_state=$now
    fi

    # 지난번에 push 가 실패했으면 그때 쌓인 커밋도 함께 올라간다.
    if [ "$(git rev-list --count "origin/$BRANCH..HEAD")" != 0 ]; then
        if git push -q origin "$BRANCH"; then
            log "push 완료"
        else
            log "push 실패. 다음 차례에 다시 시도한다"
            return 1
        fi
    fi
}

if [ "$ONCE" != 1 ]; then
    if [ "$STATE" = 1 ]; then
        log "시작: ${INTERVAL}초마다 board/ 를, ${STATE_INTERVAL}초마다 결과와 기록을 origin/$BRANCH 로 올린다"
    else
        log "시작: ${INTERVAL}초마다 board/ 를 origin/$BRANCH 로 올린다"
    fi
fi
while :; do
    publish
    status=$?
    [ "$ONCE" = 1 ] && exit "$status"
    sleep "$INTERVAL"
done
