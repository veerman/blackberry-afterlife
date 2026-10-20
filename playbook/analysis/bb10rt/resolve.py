import subprocess,os,re,sys,collections,glob
# Run from anywhere: data dirs sit next to this script. SYSSCAN = PlayBook system libs extracted from the official image.
R=os.path.dirname(os.path.abspath(__file__)); SYSSCAN=os.environ.get('SYSSCAN', R+'/sysscan')
def syms(path):
    out=subprocess.run(['readelf','-W','--dyn-syms','-D',path],capture_output=True,text=True).stdout
    if 'Symbol table' not in out:
        out=subprocess.run(['readelf','-W','--dyn-syms',path],capture_output=True,text=True).stdout
    d=set();u={}
    for l in out.splitlines():
        p=l.split()
        if len(p)<8 or not p[0].rstrip(':').isdigit(): continue
        typ,bind,ndx,name=p[3],p[4],p[6],p[7].split('@')[0]
        if not name: continue
        if ndx=='UND': u[name]=bind
        else: d.add(name)
    return d,u
def needed(path):
    out=subprocess.run(['readelf','-d','-W',path],capture_output=True,text=True).stdout
    return re.findall(r'NEEDED.*\[(.*)\]',out)
# PB library index
pbidx={}
for root in [SYSSCAN,R+'/pbdev']:
    for dp,dn,fn in os.walk(root):
        for f in fn:
            if '.so' in f: pbidx.setdefault(f,os.path.join(dp,f))
bbidx={}
for root in [R+'/bb10-rcfs']:
    for dp,dn,fn in os.walk(root):
        for f in fn:
            if '.so' in f: bbidx.setdefault(f,os.path.join(dp,f))
qnx=[l.strip() for l in open(R+'/bb10-apps.qnx')]+[R+'/bb10-apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/system/bin/linker']
own={os.path.basename(f):f for f in qnx}
E=set(); 
for f in qnx: E|=syms(f)[0]
ext=collections.Counter()
for f in qnx:
    for n in needed(f):
        if n not in own: ext[n]+=1
# transitive PB closure
seen=set();stack=[n for n in ext if n in pbidx]
while stack:
    n=stack.pop()
    if n in seen or n not in pbidx: continue
    seen.add(n); p=pbidx[n]; E|=syms(p)[0]
    stack+= [m for m in needed(p) if m not in seen]
missing_libs=sorted(n for n in ext if n not in pbidx and n not in own)
bbexp={}
for n in ext:
    if n in bbidx: bbexp[n]=syms(bbidx[n])[0]
unres=collections.defaultdict(lambda: collections.defaultdict(set))
for f in qnx:
    d,u=syms(f)
    nd=needed(f)
    for s,b in u.items():
        if s in E or b=='WEAK': continue
        lib=None
        for n in nd:
            if n in bbexp and s in bbexp[n]: lib=n;break
        if lib is None:
            ml=[n for n in nd if n not in pbidx and n not in own]
            if s.startswith('slog2'): lib='libslog2.so.1'
            elif len(ml)==1: lib=ml[0]+'?'
            else: lib='core(libc.so.3/libm/libsocket/IFS)?'
        unres[lib][s].add(os.path.relpath(f,R+'/bb10-apps'))
print('PB closure libs:',len(seen)); print('missing libs:',missing_libs)
for lib in sorted(unres,key=lambda k:-len(unres[k])):
    ss=unres[lib]
    users=set().union(*ss.values())
    print(f'\n## {lib}: {len(ss)} syms, {len(users)} users')
    print('  syms:',' '.join(sorted(ss)[:400]))
    print('  users:',' '.join(sorted(os.path.basename(x) for x in users)[:40]))
