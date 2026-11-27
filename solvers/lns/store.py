"""results/lns.csv 를 여러 실행기가 함께 쓸 때 서로의 결과를 덮어쓰지 않게 하는 저장 함수."""
from __future__ import annotations

import fcntl
import json
import os

from verify import check_program, read_submission, write_submission


def save_merge(path, have, puzzles):
    """파일에 있는 것과 have 를 퍼즐별로 짧은 쪽으로 합쳐 쓴다. have 도 그 결과로 갱신된다."""
    with open(str(path) + ".lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        if os.path.exists(path):
            for pid, cell in read_submission(path).items():
                if pid in have and len(have[pid]) <= cell.count("[") - 1:
                    continue
                try:
                    prog = json.loads(cell)
                except ValueError:
                    continue
                if (pid not in have or len(prog) < len(have[pid])) and pid in puzzles and check_program(puzzles[pid], prog) is None:
                    have[pid] = prog
        if have:
            write_submission(path, have)
