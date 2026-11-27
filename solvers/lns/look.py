"""연습 퍼즐 하나의 목표값을 소인수분해해서 보여 준다. 사용: look.py <id> [<id>...]"""
import csv, json, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from nt import fstr
rows = {r['id']: r for r in csv.DictReader(open('data/practice_puzzles.csv', newline='', encoding='utf-8'))}
for pid in sys.argv[1:]:
    r = rows[pid]
    print(f"== {pid} family={r['family']} tier={r['design_tier']} seeds={r['starting_values']} limit={r['value_limit']} lb={r['lower_bound']}")
    for t in json.loads(r['targets']):
        print(f"  {t:>20}  {t.bit_length():2}b  {fstr(t)}")
