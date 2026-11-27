import json,sys,os
out=sys.argv[1]
for p in sys.argv[2:]:
    nb=json.load(open(p))
    name=os.path.basename(os.path.dirname(p))
    parts=[]
    for i,c in enumerate(nb.get('cells',[])):
        s=c.get('source','')
        if isinstance(s,list): s=''.join(s)
        parts.append(f"\n#### CELL {i} [{c.get('cell_type')}]\n{s}\n")
    open(os.path.join(out,name+'.txt'),'w').write(''.join(parts))
