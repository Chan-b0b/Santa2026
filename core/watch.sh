#!/usr/bin/env bash
# 감시: results/*.csv 가 바뀌면 병합하고, 알림 조건이 되면 한 줄을 찍고 끝난다.
# 백그라운드로 띄워 둔다. 감시가 끝나면 병합도 멈추므로, 끝날 때마다 새 기준으로 다시 띄운다.
#
# 사용법:
#     core/watch.sh <기준 점수> [다음 1시간 확인 epoch]
#
#   총점이 (기준 점수 - 1000) 이하가 되면 "즉시 제출 조건"을 찍고 끝난다.
#   1시간 확인 시각을 주면, 그 시각에 총점이 기준보다 낮을 때 "1시간 확인: 개선 있음"을 찍고 끝난다.
#   개선이 없으면 확인 시각을 1시간 미루고 계속 돈다. 시각을 안 주면 병합만 한다.
#   로그는 저장소 루트의 .watch.log (WATCH_LOG 로 바꿀 수 있다).
cd "$(dirname "$0")/.." || exit 1
BASE=${1:?기준 점수를 준다}
NEXT=${2:-$(( $(date +%s) + 315360000 ))}
LOG="${WATCH_LOG:-.watch.log}"
STAMP=0
echo "$(date '+%F %T') 감시 시작: 기준 $BASE" >> "$LOG"
while true; do
  newest=$(stat -c %Y results/*.csv 2>/dev/null | sort -n | tail -1)
  if [ -n "$newest" ] && [ "$newest" -gt "$STAMP" ]; then
    STAMP=$newest
    echo "$(date '+%F %T') 병합" >> "$LOG"
    .venv/bin/python -I core/merge.py >> "$LOG" 2>&1
  fi
  total=$(tail -1 board/history.csv | cut -d, -f2)
  now=$(date +%s)
  if [ "$total" -le $((BASE - 1000)) ]; then
    echo "즉시 제출 조건: 총점 $total (기준 $BASE)"
    exit 0
  fi
  if [ "$now" -ge "$NEXT" ]; then
    if [ "$total" -lt "$BASE" ]; then
      echo "1시간 확인: 개선 있음. 총점 $total (기준 $BASE)"
      exit 0
    fi
    NEXT=$((NEXT + 3600))
    echo "$(date '+%F %T') 1시간 확인: 개선 없음. 다음 확인 $(date -d @"$NEXT" '+%F %T')" >> "$LOG"
  fi
  sleep 120
done
