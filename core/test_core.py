#!/usr/bin/env python3
"""채점기와 병합 코드의 규칙 검사.  python3 -I core/test_core.py"""
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from verify import (MAX_CELL_BYTES, MAX_INSTRUCTIONS, Puzzle, SubmissionError, check_cell,
                    check_program, read_submission, score_submission, write_submission)

# 대회 설명의 예시 퍼즐: 시작값 3 에서 1, 2, 5, 8 을 만든다.
TOY = Puzzle("toy", start=(3,), targets=(1, 2, 5, 8), limit=9, registers=48)
TOY_PROGRAM = [["/", 0, 0, 1], ["-", 0, 1, 2], ["+", 0, 2, 3], ["+", 0, 3, 4]]


def rejected(puzzle, program, word):
    error = check_program(puzzle, program)
    assert error is not None and word in error, (program, error)


def test_rules():
    assert check_program(TOY, TOY_PROGRAM) is None
    # 목표를 다 만든 뒤의 명령, 같은 값을 다시 만드는 명령도 합법이다 (비용만 든다).
    assert check_program(TOY, TOY_PROGRAM + [["+", 1, 1, 2]]) is None
    # 목적지는 소스와 같아도 되고, 소스 둘이 같아도 된다. 덮어쓴 값도 만든 것으로 친다.
    assert check_program(TOY, [["/", 0, 0, 1], ["-", 0, 1, 0], ["+", 0, 0, 0], ["+", 0, 1, 0],
                               ["-", 0, 1, 0], ["+", 0, 0, 0]]) is None

    rejected(TOY, TOY_PROGRAM[:3], "미생성")
    rejected(TOY, [["-", 0, 0, 1]], "범위")                       # 0
    rejected(TOY, [["/", 0, 0, 1], ["-", 1, 0, 2]], "범위")        # 음수
    rejected(TOY, [["*", 0, 0, 1], ["+", 1, 0, 2]], "범위")        # 12 > 한도 9
    rejected(TOY, [["+", 0, 0, 1], ["/", 0, 1, 2]], "나누어떨어지지")  # 3 / 6
    rejected(TOY, [["+", 0, 1, 2]], "미정의")
    rejected(TOY, [["+", 0, 0, 48]], "레지스터")
    rejected(TOY, [["+", 0, 0, -1]], "레지스터")
    rejected(TOY, [["+", 0, 0, 1.0]], "레지스터")
    rejected(TOY, [["+", 0, 0, True]], "레지스터")
    rejected(TOY, [["%", 0, 0, 1]], "연산자")
    rejected(TOY, [["+-", 0, 0, 1]], "연산자")
    rejected(TOY, [["+", 0, 0]], "4개")
    rejected(TOY, {"a": 1}, "배열")

    # 시작값과 같은 목표값은 이미 만든 것으로 친다.
    assert check_program(Puzzle("p", (5, 6, 7), (5, 8), 8, 48), [["/", 0, 0, 3], ["+", 2, 3, 3]]) is None
    assert Puzzle("p", (5, 6, 7), (5, 8), 8, 48).lower_bound == 1

    # 길이 한도: 4,096개는 통과, 4,097개는 거부.
    one = Puzzle("one", (1,), (1,), 1, 48)
    assert check_program(one, [["*", 0, 0, 0]] * MAX_INSTRUCTIONS) is None
    rejected(one, [["*", 0, 0, 0]] * (MAX_INSTRUCTIONS + 1), "한도")

    # 셀 크기 한도와 JSON 오류.
    assert check_cell(one, "[" + " " * (MAX_CELL_BYTES - 2) + "]")[1] is None
    assert "바이트" in check_cell(one, "[" + " " * (MAX_CELL_BYTES - 1) + "]")[1]
    assert "JSON" in check_cell(one, "[[")[1]


def test_files(tmp: Path):
    puzzles = {"toy": TOY, "p": Puzzle("p", (5, 6, 7), (5, 8), 8, 48)}
    path = tmp / "sub.csv"
    write_submission(path, {"toy": TOY_PROGRAM})
    assert path.read_text().splitlines()[0] == "id,program"
    programs, errors = score_submission(puzzles, path)
    assert programs == {"toy": TOY_PROGRAM} and errors == {"p": "제출에 없음"}
    assert score_submission(puzzles, path, partial=True)[1] == {}

    for text in ("program,id\n", "id,program\ntoy,[],extra\n", "id,program\ntoy,[]\ntoy,[]\n"):
        path.write_text(text)
        try:
            read_submission(path)
        except SubmissionError:
            continue
        raise AssertionError(text)
    path.write_text('id,program\nnope,[]\n')
    assert "없는 ID" in score_submission(puzzles, path, partial=True)[1]["nope"]


def test_merge(tmp: Path):
    """병합: 더 짧고 유효할 때만 교체, 무효와 동점은 무시, best 는 항상 전체가 유효."""
    with open(tmp / "puzzles.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "starting_values", "targets", "value_limit", "registers"])
        w.writerow(["toy", "[3]", "[1, 2, 5, 8]", 9, 48])
        w.writerow(["p", "[5, 6, 7]", "[5, 8]", 8, 48])
    long_p = [["/", 0, 0, 3], ["+", 2, 3, 3], ["/", 0, 0, 4]]
    short_p = [["/", 0, 0, 3], ["+", 2, 3, 3]]
    write_submission(tmp / "seed.csv", {"toy": TOY_PROGRAM + [["+", 1, 1, 5]], "p": long_p})

    def run():
        r = subprocess.run(
            [sys.executable, "-I", str(HERE / "merge.py"), "--puzzles", str(tmp / "puzzles.csv"),
             "--results", str(tmp / "results"), "--best", str(tmp / "best" / "best.csv"),
             "--seed", str(tmp / "seed.csv"), "--board", str(tmp / "board")],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        with open(tmp / "board" / "matrix.csv", newline="") as f:
            return {row["id"]: row for row in csv.DictReader(f)}

    m = run()                                    # 결과가 없으면 시드가 그대로 best
    assert (m["toy"]["best"], m["p"]["best"], m["p"]["best_by"]) == ("5", "3", "seed")

    write_submission(tmp / "results" / "a.csv", {"toy": TOY_PROGRAM})               # toy 개선
    write_submission(tmp / "results" / "b.csv", {"toy": TOY_PROGRAM[:3], "p": short_p})  # toy 무효, p 개선
    m = run()
    assert (m["toy"]["best"], m["toy"]["best_by"], m["toy"]["a"], m["toy"]["b"]) == ("4", "a", "4", "")
    assert (m["p"]["best"], m["p"]["best_by"], m["p"]["gap"], m["p"]["a"]) == ("2", "b", "1", "")

    write_submission(tmp / "results" / "a.csv", {"toy": TOY_PROGRAM + [["+", 1, 1, 5]]})  # 나빠져도 best 유지
    write_submission(tmp / "results" / "c.csv", {"p": [["+", 2, 3, 3], ["/", 0, 0, 3]]})  # 동점이지만 무효
    m = run()
    assert (m["toy"]["best"], m["toy"]["best_by"], m["p"]["best_by"]) == ("4", "a", "b")
    programs, errors = score_submission(
        {"toy": TOY, "p": Puzzle("p", (5, 6, 7), (5, 8), 8, 48)}, tmp / "best" / "best.csv")
    assert not errors and programs == {"toy": TOY_PROGRAM, "p": short_p}
    assert len((tmp / "board" / "history.csv").read_text().splitlines()) == 3  # 헤더 + 시드 + 개선 1회
    page = (tmp / "board" / "dashboard.html").read_text(encoding="utf-8")       # 병합할 때마다 화면도 갱신된다
    assert '"puzzles":2' in page and "__DATA__" not in page
    snapshots = (tmp / "board" / "approaches.csv").read_text().splitlines()
    assert snapshots[0] == "time,approach,valid,total,held" and any(",a,1,4,1" in s for s in snapshots)


if __name__ == "__main__":
    test_rules()
    with tempfile.TemporaryDirectory() as d:
        test_files(Path(d))
    with tempfile.TemporaryDirectory() as d:
        test_merge(Path(d))
    print("모두 통과")
