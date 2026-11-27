import json,sys,os
p=sys.argv[1]; out=sys.argv[2]
nb=json.load(open(p))
o=[]
for i,c in enumerate(nb.get('cells',[])):
    src=''.join(c.get('source',[]))
    o.append(f"\n=== [{i}] {c['cell_type']} ===\n{src}")
    if c['cell_type']=='code':
        for out_ in c.get('outputs',[]):
            if out_.get('output_type')=='stream':
                o.append("--- out ---\n"+''.join(out_.get('text',[])))
            elif 'data' in out_ and 'text/plain' in out_['data']:
                o.append("--- out ---\n"+''.join(out_['data']['text/plain']))
            elif out_.get('output_type')=='error':
                o.append("--- err ---\n"+out_.get('ename','')+out_.get('evalue',''))
open(out,'w').write('\n'.join(o))
