"""해독 결과를 다른 접근법이 읽기 쉬운 꼴로 내보낸다: solvers/relate/bases_export.json
  {id: {"bases": [...], "alt": [...], "cov": [설명된 목표값...], "tier": 1|2}}
(quirk 의 run.py/run2.py 는 b['bases'] 와 len(b['cov']) 를 읽으므로 --bases 로 바로 넘길 수 있다.)"""
import json
D = '/home/maverick/Santa2026/solvers/relate/'
out = {}
for tier, f in ((1, 'bases_scored.json'), (2, 'bases2_scored.json')):
    for pid, v in json.load(open(D + f)).items():
        out[pid] = {'bases': v['bases'], 'alt': v['alt'], 'cov': [str(t) for t in v.get('targets', [])] or list(range(v['cov'])), 'tier': tier}
json.dump(out, open(D + 'bases_export.json', 'w'), indent=0, sort_keys=True)
print('exported', len(out))
