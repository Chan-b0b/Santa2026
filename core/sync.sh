#!/usr/bin/env bash
# 실행 결과와 진행 기록을 **다른(비공개) 저장소**로도 올리고 싶을 때 쓴다. 선택 사항이다.
#
# 보통은 core/publish.sh 하나로 충분하다. 그것이 화면과 함께 결과·기록도 공개 저장소
# (Chan-b0b/Santa2026)에 올린다(사용자가 2026-11-27에 공개해도 된다고 정했다).
# 이 스크립트는 같은 작업 폴더에 두 번째 git 폴더(.git-state)를 두고 따로 정한 저장소로 올린다.
# 공개 저장소 주소를 원격으로 걸면 멈춘다(그쪽은 publish.sh 가 맡는다).
#
# 사용법 (샌드박스 밖, 사용자 터미널에서 돌린다. push에 사용자의 GitHub 인증이 필요하다):
#     core/sync.sh init <비공개 저장소 주소>   처음 한 번. .git-state 를 만들고 원격을 건다.
#     core/sync.sh                            바뀐 것을 커밋하고 push 한다.
#     core/sync.sh --loop                     1시간마다 되풀이한다. INTERVAL=초 로 간격을 바꾼다.
#     core/sync.sh status                     올라갈 변경을 보여 준다. 커밋하지 않는다.
#
# 올리는 것: .gitignore 에 걸리지 않는 전부. 문서(CLAUDE.md, PLAN.md, SETUP.md, notes/, reports/),
#   코드(core/, solvers/ 의 소스와 실행 기록), 결과(results/, best/, board/), 에이전트 정의(.claude/agents/).
# 안 올리는 것: .venv/, .tools/, data/(대회 자료), 컴파일한 실행 파일, 공개 노트북에서 받은 소스.
#
# 저장소를 새로 받은 머신에서는 .git 이 곧 이 저장소다. 거기서는 이렇게 돌린다:
#     STATE_GIT_DIR=.git core/sync.sh
set -u
cd "$(dirname "$0")/.." || exit 1

STATE_GIT_DIR="${STATE_GIT_DIR:-.git-state}"
BRANCH="${STATE_BRANCH:-main}"
INTERVAL="${INTERVAL:-3600}"
# 진행 현황 화면을 올리는 공개 저장소. 여기로는 올리지 않는다.
PUBLIC_REPO="${PUBLIC_REPO:-Chan-b0b/Santa2026}"

g() { git --git-dir="$STATE_GIT_DIR" --work-tree=. "$@"; }
log() { echo "$(date '+%F %T') $*"; }

check_remote() {
    local url
    url=$(g remote get-url origin 2>/dev/null) || { echo "원격이 없다. 먼저: core/sync.sh init <비공개 저장소 주소>" >&2; return 1; }
    if [ "${ALLOW_PUBLIC:-0}" != 1 ] && echo "$url" | grep -qiE "[/:]${PUBLIC_REPO}(\.git)?/?$"; then
        echo "멈춤: 원격($url)이 공개 화면 저장소다. best 프로그램과 솔버가 공개된다." >&2
        echo "비공개 저장소를 따로 만들어 'core/sync.sh init <주소>'로 걸거나, 공개해도 된다면 ALLOW_PUBLIC=1 을 준다." >&2
        return 1
    fi
}

sync_once() {
    local total
    [ -d "$STATE_GIT_DIR" ] || { echo "$STATE_GIT_DIR 가 없다. 먼저: core/sync.sh init <비공개 저장소 주소>" >&2; return 1; }
    check_remote || return 1
    g add -A . || return 1
    if ! g diff --cached --quiet; then
        total=$(tail -n 1 board/history.csv | cut -d, -f2)
        g commit -q -m "state: 총점 $total" || return 1
        log "커밋: 총점 $total"
    fi
    if ! g rev-parse -q --verify "refs/remotes/origin/$BRANCH" >/dev/null \
       || [ "$(g rev-list --count "origin/$BRANCH..HEAD")" != 0 ]; then
        if g push -q -u origin "HEAD:$BRANCH"; then
            log "push 완료"
        else
            log "push 실패. 다음 차례에 다시 시도한다"
            return 1
        fi
    fi
}

case "${1:-}" in
    init)
        url="${2:?저장소 주소를 준다: core/sync.sh init <비공개 저장소 주소>}"
        if [ ! -d "$STATE_GIT_DIR" ]; then
            git --git-dir="$STATE_GIT_DIR" init -q --initial-branch="$BRANCH" || exit 1
        fi
        if g remote get-url origin >/dev/null 2>&1; then g remote set-url origin "$url"; else g remote add origin "$url"; fi
        check_remote || exit 1
        log "준비됨: $STATE_GIT_DIR → $url. 이제 core/sync.sh 를 돌린다"
        ;;
    status)
        [ -d "$STATE_GIT_DIR" ] || { echo "$STATE_GIT_DIR 가 없다" >&2; exit 1; }
        g status --short | head -40
        echo "바뀐 경로 수: $(g status --short | wc -l)"
        ;;
    --loop)
        log "시작: ${INTERVAL}초마다 상태를 올린다"
        while :; do sync_once; sleep "$INTERVAL"; done
        ;;
    "")
        sync_once
        ;;
    *)
        echo "모르는 인자: $1" >&2
        exit 2
        ;;
esac
