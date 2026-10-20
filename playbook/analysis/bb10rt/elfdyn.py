import struct
def parse(path):
    d=open(path,'rb').read()
    if d[:4]!=b"\x7fELF": return {"needed":[],"def":set(),"und":{}}
    phoff,=struct.unpack_from('<I',d,28); phentsz,phnum=struct.unpack_from('<HH',d,42)
    loads=[];dyn=None
    for i in range(phnum):
        t,off,va,pa,fsz,msz,fl,al=struct.unpack_from('<8I',d,phoff+i*phentsz)
        if t==1: loads.append((va,off,fsz))
        if t==2: dyn=(off,fsz)
    if not dyn: return {'needed':[],'def':set(),'und':{}}
    def v2o(v):
        for va,off,fsz in loads:
            if va<=v<va+fsz: return v-va+off
        return None
    ents={};needed=[]
    o,sz=dyn
    for i in range(0,sz,8):
        tag,val=struct.unpack_from('<iI',d,o+i)
        if tag==0: break
        if tag==1: needed.append(val)
        else: ents.setdefault(tag,val)
    stro=v2o(ents[5]); symo=v2o(ents[6])
    def s(off):
        e=d.index(b'\0',stro+off); return d[stro+off:e].decode('latin1')
    nsym=0
    if 4 in ents:
        nsym=struct.unpack_from('<II',d,v2o(ents[4]))[1]
    elif 0x6ffffef5 in ents:
        h=v2o(ents[0x6ffffef5]); nb,so,bs,sh=struct.unpack_from('<4I',d,h)
        bk=h+16+bs*4; ch=bk+nb*4
        buckets=struct.unpack_from('<%dI'%nb,d,bk); mx=max(buckets)
        if mx:
            while True:
                hv,=struct.unpack_from('<I',d,ch+(mx-so)*4); 
                if hv&1: break
                mx+=1
            nsym=mx+1
        else: nsym=so
    df=set();und={}
    for i in range(1,nsym):
        nm,val,sz,info,oth,shn=struct.unpack_from('<IIIBBH',d,symo+i*16)
        n=s(nm); bind=info>>4; typ=info&15
        if not n: continue
        if shn==0: und[n]='WEAK' if bind==2 else 'GLOBAL'
        elif bind in (1,2) : df.add(n)
    return {'needed':[s(x) for x in needed],'def':df,'und':und,'soname':s(ents[14]) if 14 in ents else None}
