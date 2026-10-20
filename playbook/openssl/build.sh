#!/usr/bin/env bash
# Cross-compile OpenSSL 1.0.2u for the PlayBook (QNX 6.5, ARMv7) as drop-in libssl.so.2 / libcrypto.so.2.
# Needs the BlackBerry Native SDK 2.1.0 in playbook/sdk (see playbook/README.md) and patchelf.
# Usage: playbook/openssl/build.sh [work-dir]   -> libs land in <work-dir>/out
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="${1:-$here}"
mkdir -p "$work/out"
source "$here/../sdk/bbndk-env.sh"
command -v patchelf >/dev/null || export PATH="$here/../sdk/hostlibs/patchelf/bin:$PATH"

cd "$work"
[ -f openssl-1.0.2u.tar.gz ] || curl -fLO https://www.openssl.org/source/old/1.0.2/openssl-1.0.2u.tar.gz
echo "ecd0c6ffb493dd06707d38b14bb4d8c2288bb7033735606569d8f90f89669d16  openssl-1.0.2u.tar.gz" | sha256sum -c
rm -rf openssl-1.0.2u && tar xzf openssl-1.0.2u.tar.gz
cd openssl-1.0.2u

# The PlayBook keeps the old ciphers and protocols enabled so nothing that used 1.0.0e loses a function.
CC=ntoarmv7-gcc AR=ntoarmv7-ar RANLIB=ntoarmv7-ranlib ./Configure linux-armv4 shared no-asm \
  enable-ssl2 enable-ssl3 enable-ssl3-method enable-md2 enable-rfc3779 no-zlib \
  --openssldir=/etc/openssl --prefix=/usr -D_QNX_SOURCE -march=armv7-a -mfpu=vfpv3 -mfloat-abi=softfp
# QNX: sockets live in libsocket, there is no libdl, and the SDK lacks syslog.h (libc has the functions).
sed -i -e 's|^EX_LIBS=.*|EX_LIBS= -lsocket|' -e "s|^CFLAG= |CFLAG= -I$here/shim |" Makefile
make -j"$(nproc)" build_libs

# The firmware's libcurl and WebKit link against the .so.2 names.
cp libcrypto.so.1.0.0 "$work/out/libcrypto.so.2"
cp libssl.so.1.0.0 "$work/out/libssl.so.2"
patchelf --set-soname libcrypto.so.2 "$work/out/libcrypto.so.2"
patchelf --set-soname libssl.so.2 --replace-needed libcrypto.so.1.0.0 libcrypto.so.2 "$work/out/libssl.so.2"
readelf -d "$work/out/libssl.so.2" | grep -E 'NEEDED|SONAME'
