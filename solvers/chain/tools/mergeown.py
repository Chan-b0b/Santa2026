"""chain 자신의 결과 파일 여러 개를 퍼즐별 최단으로 합쳐 results/chain.csv 에 쓴다 (check_program 통과분만).
사용: mergeown.py <csv> [<csv> ...]     (results/chain.csv 는 항상 포함)"""
import sys, json, os
ROOT = "/home/maverick/Santa2026"
sys.path.insert(0, ROOT + "/core")
from verify import load_puzzles, check_program, write_submission, read_submission
P = load_puzzles(ROOT + "/data/puzzles.csv")
RESULT = ROOT + "/results/chain.csv"
best = {}
for path in [RESULT] + sys.argv[1:]:
    if not os.path.exists(path):
        continue
    n = 0
    for pid, cell in read_submission(path).items():
        prog = json.loads(cell)
        if pid in P and check_program(P[pid], prog) is None:
            if pid not in best or len(prog) < len(best[pid]):
                best[pid] = prog
                n += 1
    print(path, "에서 채택", n)
write_submission(RESULT, best)
print("퍼즐", len(best), "합계(참고)", sum(len(v) for v in best.values()))
