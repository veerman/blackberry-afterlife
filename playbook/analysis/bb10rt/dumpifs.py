import struct,sys,os
f,out=sys.argv[1],sys.argv[2]
d=open(f,'rb').read()
p=int(sys.argv[3]) if len(sys.argv)>3 else d.find(b'imagefs')
sig,flags,isz,hdsz,diroff=struct.unpack_from('<7sBIII',d,p)
q=p+diroff
end=p+hdsz
n=0
while q<end:
    size,extoff,ino,mode,gid,uid,mtime=struct.unpack_from('<HHIIIII',d,q)
    if size==0: break
    body=q+24
    t=mode&0o170000
    if t==0o100000:
        off,fsz=struct.unpack_from('<II',d,body)
        name=d[body+8:q+size].split(b'\0')[0].decode()
        dst=os.path.join(out,name); os.makedirs(os.path.dirname(dst),exist_ok=True)
        open(dst,'wb').write(d[p+off:p+off+fsz]); n+=1
    elif t==0o120000:
        so,ss=struct.unpack_from('<HH',d,body)
        name=d[body+4:q+size].split(b'\0')[0].decode()
        tgt=d[body+4+so:body+4+so+ss].decode()
        print('LINK',name,'->',tgt)
    q+=size
print('files',n)
