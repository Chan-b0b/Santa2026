"""results/search.csv 의 프로그램마다 compact() (중복 계산 제거 + 레지스터 재배정)를 적용한다."""
import sys, json
sys.path.insert(0, "/home/maverick/Santa2026/core")
sys.path.insert(0, "/home/maverick/Santa2026/solvers/search")
from verify import load_puzzles, check_program, write_submission, read_submission
import solver

OUT = '/home/maverick/Santa2026/results/search.csv'
P = load_puzzles('/home/maverick/Santa2026/data/puzzles.csv')
cells = read_submission(OUT)
progs = {}
saved = 0
for pid, cell in cells.items():
    pz = P[pid]
    prog = json.loads(cell)
    if check_program(pz, prog) is not None:
        continue
    c = solver.compact(pz, prog)
    if c is not None and len(c) < len(prog) and check_program(pz, c) is None:
        saved += len(prog) - len(c)
        prog = c
    progs[pid] = prog
write_submission(OUT, progs)
print('programs', len(progs), 'instructions saved', saved)
