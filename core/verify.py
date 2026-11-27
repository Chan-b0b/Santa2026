#!/usr/bin/env python3
"""Elf Calculator 채점기. 점수와 유효성 판정은 이 파일만 한다.

사용법:
    python3 -I core/verify.py best/best.csv              # 전체 제출 검사 (1,000개 모두 필요)
    python3 -I core/verify.py results/foo.csv --partial  # 일부 퍼즐만 담긴 결과 파일 검사

솔버에서 쓰는 법:
    from verify import load_puzzles, check_program, write_submission
    puzzles = load_puzzles("data/puzzles.csv")
    error = check_program(puzzles["scored_0001"], program)   # None이면 유효, 점수는 len(program)
    write_submission("results/foo.csv", {"scored_0001": program})

규칙 (대회 설명 + 샘플 제출로 확인한 것):
  - 레지스터는 puzzle.registers개. 시작값이 0번부터 차례로 들어 있고 나머지는 미정의.
  - 명령은 [op, a, b, d]. op는 + - * / 중 하나, a/b는 정의된 레지스터, d는 아무 레지스터.
  - 결과는 1 이상 value_limit 이하의 정수. 나눗셈은 나누어떨어져야 한다.
  - 모든 목표값이 한 번 이상 나와야 한다. 시작값과 같은 목표값은 이미 나온 것으로 친다.
    (샘플 제출의 scored_0597 등은 그 목표값을 명령으로 만들지 않는다.)
  - 프로그램당 명령 4,096개, 셀 131,072바이트 이하.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_INSTRUCTIONS = 4096
MAX_CELL_BYTES = 131072
OPS = ("+", "-", "*", "/")
HEADER = ["id", "program"]

csv.field_size_limit(1 << 30)  # 기본 한도가 131072자라서, 큰 셀을 우리 오류 메시지로 잡으려면 풀어야 한다.


class SubmissionError(ValueError):
    """파일 단위 형식 오류 (헤더, 열 개수, 중복 ID)."""


@dataclass(frozen=True)
class Puzzle:
    id: str
    start: tuple[int, ...]
    targets: tuple[int, ...]
    limit: int
    registers: int

    @property
    def lower_bound(self) -> int:
        """시작값에 없는 목표값 개수. 명령 하나가 값 하나만 만들기 때문에 성립하는 하한이며,
        practice_puzzles.csv의 lower_bound 열과 같은 정의다."""
        return len(set(self.targets) - set(self.start))


def load_puzzles(path) -> dict[str, Puzzle]:
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["id"]: Puzzle(
                id=row["id"],
                start=tuple(json.loads(row["starting_values"])),
                targets=tuple(json.loads(row["targets"])),
                limit=int(row["value_limit"]),
                registers=int(row["registers"]),
            )
            for row in csv.DictReader(f)
        }


def check_program(puzzle: Puzzle, program) -> str | None:
    """규칙 위반이면 사유를, 유효하면 None을 돌려준다. 유효한 프로그램의 점수는 len(program)."""
    if not isinstance(program, list):
        return "프로그램이 배열이 아님"
    if len(program) > MAX_INSTRUCTIONS:
        return f"명령 {len(program)}개로 한도 {MAX_INSTRUCTIONS}개 초과"
    n_reg, limit = puzzle.registers, puzzle.limit
    reg: list[int | None] = [None] * n_reg
    reg[: len(puzzle.start)] = puzzle.start
    missing = set(puzzle.targets) - set(puzzle.start)
    for i, ins in enumerate(program):
        if not isinstance(ins, list) or len(ins) != 4:
            return f"명령 {i}: 원소 4개짜리 배열이 아님"
        op, a, b, d = ins
        if not isinstance(op, str) or op not in OPS:
            return f"명령 {i}: 연산자 {op!r}"
        for r in (a, b, d):
            if type(r) is not int or not 0 <= r < n_reg:
                return f"명령 {i}: 레지스터 번호 {r!r}"
        x, y = reg[a], reg[b]
        if x is None or y is None:
            return f"명령 {i}: 미정의 레지스터 {a if x is None else b} 읽기"
        if op == "+":
            v = x + y
        elif op == "-":
            v = x - y
        elif op == "*":
            v = x * y
        else:
            if x % y:
                return f"명령 {i}: {x} / {y} 는 나누어떨어지지 않음"
            v = x // y
        if not 1 <= v <= limit:
            return f"명령 {i}: 결과 {v} 가 범위 1..{limit} 밖"
        reg[d] = v
        missing.discard(v)
    if missing:
        return f"목표값 {len(missing)}개 미생성 (예: {min(missing)})"
    return None


def dump_program(program) -> str:
    return json.dumps(program, separators=(",", ":"))


def check_cell(puzzle: Puzzle, cell: str) -> tuple[list | None, str | None]:
    """CSV의 program 셀 하나를 검사한다. (프로그램, None) 또는 (None, 사유)."""
    n_bytes = len(cell.encode("utf-8"))
    if n_bytes > MAX_CELL_BYTES:
        return None, f"셀 {n_bytes}바이트로 한도 {MAX_CELL_BYTES}바이트 초과"
    try:
        program = json.loads(cell)
    except ValueError as e:
        return None, f"JSON 파싱 실패: {e}"
    error = check_program(puzzle, program)
    return (None, error) if error else (program, None)


def read_submission(path) -> dict[str, str]:
    """id -> program 셀 문자열. 헤더, 열 개수, 중복 ID가 틀리면 SubmissionError."""
    cells: dict[str, str] = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = csv.reader(f)
            header = next(rows, None)
            if header != HEADER:
                raise SubmissionError(f"헤더가 {HEADER} 가 아니라 {header}")
            for line, row in enumerate(rows, start=2):
                if len(row) != 2:
                    raise SubmissionError(f"{line}번째 행: 열이 {len(row)}개")
                if row[0] in cells:
                    raise SubmissionError(f"{line}번째 행: 중복 ID {row[0]}")
                cells[row[0]] = row[1]
    except (UnicodeDecodeError, csv.Error) as e:
        raise SubmissionError(f"CSV 읽기 실패: {e}") from e
    return cells


def write_submission(path, programs: dict[str, list]) -> None:
    """id -> 프로그램을 제출 형식 CSV로 쓴다. 임시 파일에 쓴 뒤 바꿔치기하므로 중간 상태가 남지 않는다."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for pid in sorted(programs):
            w.writerow([pid, dump_program(programs[pid])])
    os.replace(tmp, path)


def score_submission(puzzles: dict[str, Puzzle], path, partial: bool = False):
    """(유효한 프로그램 id -> 프로그램, 문제 있는 id -> 사유)를 돌려준다.

    partial=False면 빠진 퍼즐도 오류로 친다. 퍼즐 목록에 없는 ID는 항상 오류다.
    """
    cells = read_submission(path)
    programs: dict[str, list] = {}
    errors: dict[str, str] = {}
    for pid, cell in cells.items():
        if pid not in puzzles:
            errors[pid] = "퍼즐 목록에 없는 ID"
            continue
        program, error = check_cell(puzzles[pid], cell)
        if error:
            errors[pid] = error
        else:
            programs[pid] = program
    if not partial:
        for pid in puzzles:
            if pid not in cells:
                errors[pid] = "제출에 없음"
    return programs, errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Elf Calculator 제출 파일 채점")
    ap.add_argument("submission")
    ap.add_argument("--puzzles", default=root / "data" / "puzzles.csv")
    ap.add_argument("--partial", action="store_true", help="일부 퍼즐만 있어도 허용")
    args = ap.parse_args()

    puzzles = load_puzzles(args.puzzles)
    try:
        programs, errors = score_submission(puzzles, args.submission, partial=args.partial)
    except SubmissionError as e:
        print(f"거부: {e}")
        return 1
    total = sum(len(p) for p in programs.values())
    lower = sum(puzzles[pid].lower_bound for pid in programs)
    print(f"유효 {len(programs)}개 / 퍼즐 {len(puzzles)}개, 명령 합계 {total} (하한 합계 {lower})")
    if errors:
        print(f"문제 {len(errors)}개:")
        for pid in sorted(errors)[:20]:
            print(f"  {pid}: {errors[pid]}")
        if len(errors) > 20:
            print(f"  ... 외 {len(errors) - 20}개")
        print("거부: 이대로 제출하면 전체가 무효")
        return 1
    print("통과" + ("" if not args.partial else " (부분 검사)") + f": 점수 {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
