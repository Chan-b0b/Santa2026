import sys, json, statistics, random
sys.path.insert(0,'core')
from verify import load_puzzles, read_submission
P=load_puzzles('data/puzzles.csv'); B=read_submission('best/best.csv')
rows=[]
for pid,pz in P.items():
    m=statistics.median(t.bit_length() for t in pz.targets)
    rows.append((pid,m,len(json.loads(B[pid])),len(pz.targets)))
lo=[r for r in rows if 48<=r[1]<56]; hi=[r for r in rows if r[1]>=56]
print(len(lo),len(hi), sum(r[2] for r in rows if r[1]>=48))
random.seed(7)
sel=random.sample(lo,20)+random.sample(hi,20)
open('solvers/regfit/puzzles40.txt','w').write("\n".join(f"{r[0]} {r[1]} {r[2]} {r[3]}" for r in sel)+"\n")
