#!/usr/bin/env python3
"""접근법별 결과를 퍼즐별 최단으로 병합한다.

사용법:
    python3 -I core/merge.py

입력
    results/<접근법>.csv   id,program 형식. 일부 퍼즐만 있어도 된다. 파일 이름이 접근법 이름이다.
    best/best.csv          현재 최선. 없으면 data/sample_submission.csv 로 시작한다.

출력
    best/best.csv          퍼즐별 최단. 항상 1,000개 모두 유효한, 바로 제출 가능한 파일.
    best/source.csv        id,length,source: 각 최단을 낸 접근법.
    board/matrix.csv       id,lower_bound,best,gap,best_by,<접근법별 길이>...  (빈칸 = 없음 또는 무효)
    board/history.csv      총점이 바뀔 때마다 한 줄.
    board/dashboard.html   진행 현황 화면 (dashboard.py 가 만든다. board/approaches.csv 도 함께 쌓인다).

best.csv 는 더 짧고 유효한 프로그램이 나왔을 때만 바뀐다. 길이가 같으면 기존 것을 둔다.
무효인 프로그램은 무시하고 개수만 알린다. 사유는 verify.py --partial 로 본다.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python3 -I 로 실행해도 verify 를 찾도록
from verify import SubmissionError, load_puzzles, score_submission, write_submission

ROOT = Path(__file__).resolve().parent.parent


def write_csv(path: Path, header: list[str], rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    os.replace(tmp, path)


def read_sources(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {row["id"]: row["source"] for row in csv.DictReader(f)}


def merge(args) -> int:
    puzzles = load_puzzles(args.puzzles)
    best_path = Path(args.best)
    source_path = best_path.with_name("source.csv")
    board = Path(args.board)

    # 1. 현재 최선을 읽는다. 채점기를 통과한 것만 남긴다.
    best: dict[str, list] = {}
    source: dict[str, str] = {}
    dirty = not best_path.exists()
    if best_path.exists():
        try:
            best, errors = score_submission(puzzles, best_path, partial=True)
        except SubmissionError as e:
            print(f"중단: {best_path} 를 읽을 수 없습니다 ({e}). 덮어쓰지 않고 멈춥니다.")
            return 1
        if errors:
            print(f"경고: {best_path} 에 무효 {len(errors)}개. 다른 유효한 프로그램으로 채웁니다.")
            dirty = True
        old_source = read_sources(source_path)
        source = {pid: old_source.get(pid, "?") for pid in best}
    old_total = sum(len(p) for p in best.values()) if len(best) == len(puzzles) else None

    # 2. 빈 퍼즐은 시드(샘플 제출)로 채운다.
    seed_path = Path(args.seed)
    if len(best) < len(puzzles) and seed_path.exists():
        seed, _ = score_submission(puzzles, seed_path, partial=True)
        for pid, program in seed.items():
            if pid not in best:
                best[pid] = program
                source[pid] = seed_path.stem
                dirty = True

    # 3. 접근법별 결과에서 더 짧은 것을 가져온다.
    before = {pid: len(p) for pid, p in best.items()}
    lengths: dict[str, dict[str, int]] = {}
    invalid: dict[str, int] = {}
    for path in sorted(Path(args.results).glob("*.csv")):
        try:
            programs, errors = score_submission(puzzles, path, partial=True)
        except SubmissionError as e:
            print(f"건너뜀: {path} ({e})")
            continue
        lengths[path.stem] = {pid: len(p) for pid, p in programs.items()}
        invalid[path.stem] = len(errors)
        for pid, program in programs.items():
            if pid not in best or len(program) < len(best[pid]):
                best[pid] = program
                source[pid] = path.stem

    missing = [pid for pid in puzzles if pid not in best]
    if missing:
        print(f"중단: 유효한 프로그램이 없는 퍼즐 {len(missing)}개 (예: {missing[0]}). best.csv 를 쓰지 않습니다.")
        return 1
    changed = [pid for pid in best if before.get(pid) != len(best[pid])]
    dirty = dirty or bool(changed)
    total = sum(len(p) for p in best.values())

    # 4. 새 best 는 디스크에 쓴 그대로 다시 채점해서 통과해야만 교체한다.
    if dirty:
        new_path = best_path.with_name("best.new.csv")
        write_submission(new_path, best)
        _, errors = score_submission(puzzles, new_path)
        if errors:
            pid = sorted(errors)[0]
            print(f"중단: 새 best 가 재검증에 실패 ({pid}: {errors[pid]}). 기존 best.csv 를 유지합니다.")
            os.remove(new_path)
            return 1
        os.replace(new_path, best_path)
        write_csv(source_path, ["id", "length", "source"],
                  ([pid, len(best[pid]), source[pid]] for pid in sorted(best)))
        history = board / "history.csv"
        history.parent.mkdir(parents=True, exist_ok=True)
        new_file = not history.exists()
        with open(history, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(["time", "total", "improved_puzzles", "saved"])
            w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), total, len(changed),
                        "" if old_total is None else old_total - total])

    # 5. 비교표.
    names = sorted(lengths)
    write_csv(board / "matrix.csv", ["id", "lower_bound", "best", "gap", "best_by", *names],
              ([pid, puzzles[pid].lower_bound, len(best[pid]), len(best[pid]) - puzzles[pid].lower_bound,
                source[pid], *(lengths[n].get(pid, "") for n in names)] for pid in sorted(best)))

    for name in names:
        held = sum(1 for pid, n in lengths[name].items() if n == len(best[pid]))
        won = sum(1 for pid in changed if source[pid] == name)
        print(f"{name}: 유효 {len(lengths[name])}, 무효 {invalid[name]}, 최단 보유 {held}, 이번 갱신 {won}")
    lower = sum(p.lower_bound for p in puzzles.values())
    delta = "" if old_total is None else f" (이전 {old_total}, {total - old_total:+d})"
    print(f"총점 {total}{delta}, 갱신 퍼즐 {len(changed)}개, 하한 합계 {lower}, 격차 {total - lower}")

    # 6. 진행 현황 화면. 부가 기능이라 실패해도 병합 결과에는 영향을 주지 않는다.
    try:
        import dashboard
        dashboard.build(board)
    except Exception as e:
        print(f"경고: 진행 현황 화면을 만들지 못했습니다 ({e})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="접근법별 결과를 퍼즐별 최단으로 병합")
    ap.add_argument("--puzzles", default=ROOT / "data" / "puzzles.csv")
    ap.add_argument("--results", default=ROOT / "results")
    ap.add_argument("--best", default=ROOT / "best" / "best.csv")
    ap.add_argument("--seed", default=ROOT / "data" / "sample_submission.csv")
    ap.add_argument("--board", default=ROOT / "board")
    args = ap.parse_args()

    # 여러 에이전트가 동시에 병합해도 best.csv 가 꼬이지 않도록 잠근다.
    best_dir = Path(args.best).parent
    best_dir.mkdir(parents=True, exist_ok=True)
    with open(best_dir / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return merge(args)


if __name__ == "__main__":
    sys.exit(main())
