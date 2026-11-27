import json,random,sys,csv
sys.path.insert(0,'/home/maverick/Santa2026/core')
from verify import read_submission
fam=json.load(open('/home/maverick/Santa2026/solvers/quirk/family_guess.json'))
ind=[k for k,v in fam.items() if v[0]=='indep']
big=set(open('/home/maverick/Santa2026/solvers/lns/big48.txt').read().replace('\n',',').split(','))
best={k:len(json.loads(v)) for k,v in read_submission('/home/maverick/Santa2026/best/best.csv').items()}
random.seed(2026)
B=sorted(k for k in ind if k in big); S=sorted(k for k in ind if k not in big)
print(len(ind),len(B),len(S))
pick=random.sample(B,10)+random.sample(S,10)
json.dump({k:best[k] for k in pick},open('/home/maverick/Santa2026/solvers/fresh/puzzles20.json','w'),indent=1)
print({k:best[k] for k in pick})
