import os,sys,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import elfdyn
# Run from anywhere: data dirs sit next to this script. SYSSCAN = PlayBook system libs extracted from the official image.
R=os.path.dirname(os.path.abspath(__file__)); SYSSCAN=os.environ.get('SYSSCAN', R+'/sysscan')
def idx(roots):
    m={}
    for root in roots:
        for dp,dn,fn in os.walk(root):
            for f in fn:
                p=os.path.join(dp,f)
                if '.so' in f and os.path.isfile(p): m.setdefault(f,p)
    return m
pbidx=idx([R+'/pbdev',SYSSCAN]); bbidx=idx([R+'/bb10-rcfs'])
cache={}
def P(p):
    if p not in cache: cache[p]=elfdyn.parse(p)
    return cache[p]
qnx=[R+'/'+l.strip() for l in open(R+'/bb10-apps.qnx')]+[R+'/bb10-apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/system/bin/linker']
own={os.path.basename(f) for f in qnx}
E=set()
for f in qnx: E|=P(f)['def']
ext=collections.Counter(n for f in qnx for n in P(f)['needed'] if n not in own)
seen=set(); st=[n for n in ext if n in pbidx]
while st:
    n=st.pop()
    if n in seen or n not in pbidx: continue
    seen.add(n); r=P(pbidx[n]); E|=r['def']; st+=r['needed']
print('PB closure libs loaded:',len(seen),sorted(seen))
unres=collections.defaultdict(lambda: collections.defaultdict(set))
for f in qnx:
    r=P(f)
    for s,b in r['und'].items():
        if s in E or b=='WEAK': continue
        lib=None
        for n in r['needed']:
            if n in bbidx and s in P(bbidx[n])['def']: lib=n; break
        if lib is None:
            ml=[n for n in r['needed'] if n not in pbidx and n not in own]
            if s.startswith('slog2'): lib='libslog2.so.1'
            elif len(ml)==1: lib=ml[0]+' (inferred)'
            else: lib='CORE? (libc/libm/libsocket/libz in IFS, inferred)'
        unres[lib][s].add(os.path.basename(f))
tot=set()
for lib in sorted(unres,key=lambda k:-len(unres[k])):
    ss=unres[lib]; tot|=set(ss)
    users=set().union(*ss.values())
    print(f'\n## {lib}: {len(ss)} syms, {len(users)} users')
    print('  syms:',' '.join(sorted(ss)))
    print('  users:',' '.join(sorted(users)))
print('\nTOTAL unique unresolved',len(tot))
