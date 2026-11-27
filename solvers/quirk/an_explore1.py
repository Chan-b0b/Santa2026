import csv, json, collections, math
P=list(csv.DictReader(open('data/practice_puzzles.csv')))
c=collections.Counter((p['family'],p['design_tier']) for p in P)
for k,v in sorted(c.items()): print(k,v)
for p in P[:0]: pass
# per family: nstart, ntargets, max bits, limit bits
fam=collections.defaultdict(list)
for p in P:
    s=json.loads(p['starting_values']); t=json.loads(p['targets'])
    fam[(p['family'],p['design_tier'])].append((len(s),len(t),max(t).bit_length(),int(p['value_limit']).bit_length(), max(s)))
for k,v in sorted(fam.items()):
    import statistics as st
    print(k, 'ns',st.median(x[0] for x in v),'nt',st.median(x[1] for x in v),'maxbits',st.median(x[2] for x in v),'lim',st.median(x[3] for x in v),'maxs',st.median(x[4] for x in v))
