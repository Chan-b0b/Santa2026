"""작은 퍼즐용 다중 출발 재합성: 여러 접근법의 결과(results/*.csv)를 각각 출발점으로, 난수씨를 바꿔 lns 재합성기 사본을 돌린다.
사용: multistart.py <ids,쉼표> [secs] [seeds]"""
import sys, json, glob
sys.path.insert(0, 'core'); sys.path.insert(0, 'solvers/quirk')
from verify import load_puzzles, check_program, read_submission
import polish

def starts_for(pid, P):
    out = {}
    for f in sorted(glob.glob('results/*.csv')) + ['best/best.csv']:
        try: cells = read_submission(f)
        except Exception: continue
        if pid in cells:
            prog = json.loads(cells[pid])
            if check_program(P[pid], prog) is None: out[f] = prog
    return out

if __name__ == '__main__':
    P = load_puzzles('data/puzzles.csv')
    ids = sys.argv[1].split(','); secs = float(sys.argv[2]) if len(sys.argv) > 2 else 10; nseeds = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    for pid in ids:
        st = starts_for(pid, P)
        best = min(len(p) for p in st.values()); print(pid, {f.split('/')[-1]: len(p) for f, p in st.items()})
        for f, prog in st.items():
            for s in range(nseeds):
                new = polish.lns(P[pid], prog, secs, 100 + s)
                print('  ', f.split('/')[-1], len(prog), '->', len(new) if new else None, flush=True)
