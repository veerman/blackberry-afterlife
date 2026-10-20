#!/usr/bin/env python3
"""Read-only inspector for BB10 autoloader .exe files (cap.exe stub + ver2 table + .signed payloads)."""
import os, struct, sys

def cap_end(f):
    f.seek(0); mz = f.read(0x40)
    pe = struct.unpack_from('<I', mz, 0x3C)[0]
    f.seek(pe); h = f.read(0x18)
    nsec, = struct.unpack_from('<H', h, 6); optsz, = struct.unpack_from('<H', h, 20)
    f.seek(pe + 0x18 + optsz); end = 0
    for _ in range(nsec):
        s = f.read(40); rsz, rptr = struct.unpack_from('<II', s, 16)
        end = max(end, rptr + rsz)
    return end

def main(path, outdir=None):
    with open(path, 'rb') as f:
        f.seek(0, 2); total = f.tell()
        ce = cap_end(f); f.seek(ce); win = f.read(0x10000)
        ce += win.find(struct.pack('<3I', *[0x97C5D59C] * 3))  # official stubs carry extra bytes first
        f.seek(ce); hdr = f.read(0x64 + 8 * 32)
        sig = struct.unpack_from('<3I', hdr, 0)
        n, = struct.unpack_from('<I', hdr, 0x5C)
        print(f'file size {total}  cap_end 0x{ce:X}  sig {[hex(s) for s in sig]}  payloads {n}')
        offs = list(struct.unpack_from(f'<{n}Q', hdr, 0x64)) + [total]
        for i in range(n):
            o, e = offs[i], offs[i + 1]; size = e - o
            f.seek(o); head = f.read(0x40)
            f.seek(e - 560); tail = f.read(560)
            nf = struct.unpack_from('<I', head, 0x2C)[0] if head[:4] == b'mfcq' else None
            print(f'[{i}] off 0x{o:X} size {size:,}  magic {head[:4]!r}  nfiles(v2) {nf}  '
                  f'tail560[:12] {tail[:12]!r}  last8 {tail[-8:].hex()}')
            if outdir:
                out = f'{outdir}/{os.path.basename(path)[:-4]}.{i}.signed'
                f.seek(o); left = size
                with open(out, 'wb') as w:
                    while left:
                        chunk = f.read(min(left, 1 << 24)); w.write(chunk); left -= len(chunk)
                print(f'    wrote {out}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
