# PlayBook WebKit port: handoff notes

Oct 4, 2026 · @Steve

> Local copy of the Claude Doc https://claude.ai/code/artifact/4e3cb4ed-8165-48f2-ab0d-d828a52a53ec

## Where things stand

JavaScriptCore from WPE WebKit 2.36.8 (2022) cross-compiles cleanly for the PlayBook (QNX 6.5, ARMv7) with Psyden's GCC 9.3. It has not been run on the device yet, and it uses the C\_LOOP interpreter (no JIT).

Everything lives under `~/Projects/blackberry/playbook/webkit/`:

| Path | What it is |
| --- | --- |
| `wpewebkit-2.36.8/` | WebKit source, a git repo: commit 1 is the pristine tarball, commit 2 is the PlayBook port |
| `patches/0001-*.patch` | The port as a single patch, for reapplying to a fresh tarball |
| `build-jsc4/bin/jsc` | JavaScript shell, ARM QNX PIE executable, 258 KB |
| `build-jsc4/lib/libJavaScriptCore.so.1.0.0` | JavaScriptCore + WTF + bmalloc, 10 MB unstripped, built at -O3 |
| `sysroot/` | Libraries we built for the device; today only ICU 71 (`lib/`, `include/unicode/`) |
| `qnx-compat/qnx_compat.h` | Header force-included into every compile to work around QNX header bugs |
| `playbook-toolchain.cmake` | CMake cross toolchain file |
| `icu-src/`, `icu-host/`, `icu-arm2/` | ICU 71 source, host build (needed for cross build), ARM build |
| `tools-venv/`, `hosttools/` | Pinned CMake 3.25 + Ninja (Python venv), gperf 3.1 |
| `*.log` | Configure and build logs from the last runs |

The `jsc` binary has build-host RPATHs baked in. On the device, set `LD_LIBRARY_PATH` to wherever `libJavaScriptCore.so.1`, the three `libicu*.so.71` files and GCC 9.3's `libstdc++.so.6` and `libgcc_s.so.1` are copied. The stock firmware's libstdc++ is GCC 4.4's, which is too old.

## Decisions made

| Decision | Why |
| --- | --- |
| Port **WPE WebKit**, not RIM's 2012 WebKit-PlayBook branch | WPE is built for embedded boards with about 1 GB of RAM and still maintains 32-bit ARM. Forward-porting RIM's code would mean crossing 12 years of WebKit history. |
| Target **WebKit 2.36** first | 2.36 needs GCC 8.3, and GCC 9.3 already works for this device. Since June 2024, WebKit needs GCC 11.2 and C++23. |
| Plan a **second toolchain stage** (GCC 13 or 14) for current WebKit | GCC 9.3's libstdc++ has none of the C++20 headers (`<span>`, `<concepts>`, `<bit>`). |
| Start with the **JSCOnly** port | It needs no GLib or graphics, so it tests the compiler, the C library gaps and threading cheaply. |
| Test on the **real device, not an emulator** | QEMU user mode only runs Linux binaries, nothing emulates the OMAP4, and RIM's simulator is x86 while GCC 9.3 targets only ARM. |
| **Keep audio and video** | A browser without media isn't useful to the owner. |
| Media through **QNX `mm-renderer`**, not GStreamer + FFmpeg | The dual 1 GHz Cortex-A9 is too slow for software video decoding. `mm-renderer` is what RIM's browser used and should give hardware H.264 decoding. That means writing a custom `MediaPlayerPrivate` backend. |
| Root over SSH for testing, no app signing | The device is rooted (tethered), so binaries can be copied and run directly. Debug tokens and BlackBerry's signing servers aren't needed. |

## Rebuild from scratch

Host: Arch-based Linux (Omarchy), 18 cores, 46 GB RAM. A clean JSC build takes about 15 minutes at `-j18`. Set `W=~/Projects/blackberry/playbook/webkit`.

1. **Toolchain environment.** Always `source playbook/sdk/psyden-gcc9/playbook-gcc9/env.sh` first. The `arm-blackberry-qnx8eabi-gcc` wrapper refuses to run unless `QNX_HOST`, `QNX_TARGET` and `QNX_PREBUILT_GCCLIB` are all set; setting only some of them fails CMake's compiler check.
2. **Host tools.** `python3 -m venv $W/tools-venv && $W/tools-venv/bin/pip install "cmake<3.26" ninja`. Build gperf 3.1 from ftp.gnu.org into `$W/hosttools`. Then `gem install --user-install getoptlong` and export `GEM_PATH=$(ruby -e 'print Gem.user_dir'):$(ruby -e 'print Gem.default_dir')`. Put `tools-venv/bin` and `hosttools/bin` first on `PATH`.
3. **ICU 71, host build.** Untar `icu4c-71_1-src.tgz` to `icu-src`, then in `icu-host/`: `../icu-src/source/runConfigureICU Linux --disable-tests --disable-samples && make -j18`.
4. **ICU 71, ARM build.** In `icu-arm2/`, with `C="-O2 -march=armv7-a -mfpu=neon -mfloat-abi=softfp -include $W/qnx-compat/qnx_compat.h"`: `CFLAGS="$C" CXXFLAGS="$C -std=c++17" ../icu-src/source/configure --host=arm-unknown-nto-qnx6.5.0eabi --with-cross-build=$W/icu-host --prefix=$W/sysroot --disable-tests --disable-samples --disable-extras --disable-tools && make -j18 && make install`.
5. **Fix the ICU data library.** See the problems table (ICU data rows): set `e_flags` to `0x05000000` on `icu-arm2/data/out/tmp/icudt71l_dat.o`, relink with `$CC -shared -nostdlib -Wl,-soname,libicudata.so.71 -o $W/sysroot/lib/libicudata.so.71 <that .o>`, delete `libicudataso.71*` and point `libicudata.so` at `libicudata.so.71`.
6. **Source.** Untar `wpewebkit-2.36.8.tar.xz` from wpewebkit.org/releases, then `git am $W/patches/0001-*.patch`.
7. **Configure and build JSC.**

```
mkdir build-jsc && cd build-jsc
cmake -G Ninja $W/wpewebkit-2.36.8 -DPORT=JSCOnly \
  -DCMAKE_TOOLCHAIN_FILE=$W/playbook-toolchain.cmake \
  -DCMAKE_BUILD_TYPE=Release -DDEVELOPER_MODE=OFF \
  -DENABLE_API_TESTS=OFF -DICU_ROOT=$W/sysroot
ninja -k 0 -j18 jsc
```

Use `-k 0` so one build shows every failing file. Never run two `ninja` processes in the same build directory; we did once by accident.

## Problems hit and how each was fixed

These are in the order we hit them. Most will come back when building GLib, libsoup, OpenSSL and WebCore, so reuse the fixes rather than rediscovering them.

| Symptom | Cause | Fix |
| --- | --- | --- |
| `fatal error: $QNX_HOST not set` (or `$QNX_PREBUILT_GCCLIB`) | Psyden's gcc wrapper checks its environment | Source the full `env.sh`, including inside CMake runs |
| `fatal error: span: No such file` (also `<concepts>`, `<bit>`) | libstdc++ 9 has no C++20 headers | Stay on WebKit 2.36 or build a newer GCC |
| `'::memset' has not been declared; did you mean 'std::memset'?` | QNX `sys/select.h` declares `memset` only inside `std::` and sets `__MEMSET_DEFINED`, so `string.h` then skips the global declaration | `qnx_compat.h` includes `<string.h>` first, force-included with `-include` |
| `call of overloaded 'pow(double, int)' is ambiguous` (also `fmod`) | QNX's Dinkumware `math.h` adds C++ inline overloads and generic `_TGEN` templates that clash with libstdc++ `<cmath>` | `#define _NO_CPP_INLINES 1` and `#define _HAS_GENERIC_TEMPLATES 0` in `qnx_compat.h` |
| ICU installs `libicudataso.71.1` plus a 5 KB `libicudata.so.71` | ICU's `mh-qnx` names the data library wrongly; `libicudata.so.71` is only the stub, and `libicuuc` links against it, so ICU would find no data on the device | Relink `icudt71l_dat.o` by hand with SONAME `libicudata.so.71` |
| `libicudata.so has EABI version 0, but target ... has EABI version 5` | `genccode` writes the data `.o` with `e_flags = 0` | Patch byte offset 0x24 (`e_flags`) to `0x05000000` before relinking |
| `add_subdirectory given source "ThirdParty/capstone"` | WPE release tarballs omit capstone, which JSCOnly requires on ARM | Only use capstone if the directory exists (`OptionsJSCOnly.cmake`) |
| `if given arguments ... Unknown arguments specified` in `WebKitMacros.cmake` | CMake 4 is stricter about `if()` with empty variables | Use CMake 3.25 (`pip install "cmake<3.26"`) |
| `cannot load such file -- getoptlong` | Ruby 3.4 dropped the gem | `gem install --user-install getoptlong` + `GEM_PATH` |
| `undefined method 'exists?' for class File` | Ruby 3.4 removed `File.exists?` | `sed s/File.exists?/File.exist?/` across `Source/` |
| `unorm2_getNFCInstance` / `U8_NEXT_OR_FFFD` not declared | The toolchain's built-in include dir ships ICU 4.6 headers, which shadowed ours | `-I$W/sysroot/include` in the toolchain flags, ahead of the system dirs |
| `sys/ucontext.h: No such file` (39 files) | QNX has `<ucontext.h>`, with ARM registers in `uc_mcontext.cpu.gpr[16]` | New `OS(QNX)` macro, `HAVE_MACHINE_CONTEXT` for QNX on ARM, QNX branches in `MachineContext.h` |
| `pthread_getattr_np` not declared | QNX has no way to query another thread's stack | `StackBounds.cpp`: origin = `__tls()`, bound = `__tls()->__stackaddr` (current thread only) |
| `SA_RESTART` not declared | QNX never restarts interrupted system calls | Use `SA_SIGINFO` alone on QNX, with a FIXME (see risks) |
| `mincore` not declared | Not in QNX's libc | Skip `updatePercentageOfPagedOutPages` on QNX; it has no swap, so the value is always zero |
| `rm -rf *` after `cd` blocked by Claude Code | A failed `cd` could wipe the wrong directory | Use a new build directory (`build-jsc2`, `3`, `4`) instead of emptying one |

## PlayBook and QNX facts learned

- **Compiler predefines:** `__QNXNTO__`, `__QNX__`, `__unix__`, `__thumb2__`, `__ARM_ARCH 7`. Because `__unix__` is set, WebKit's `OS(UNIX)` turns on automatically; QNX-specific code needs our new `OS(QNX)`.
- **Target triple:** the compiler is `arm-blackberry-qnx8eabi`. Autotools `config.sub` doesn't know that name, so pass `--host=arm-unknown-nto-qnx6.5.0eabi` and set `CC`/`CXX` explicitly. ICU maps `*-*-nto*` to its QNX settings.
- **ABI flags:** `-march=armv7-a -mtune=cortex-a9 -mfpu=neon -mfloat-abi=softfp -mthumb`. Soft-float ABI (EABI5 `0x5000200`) matches the system libraries.
- **Dynamic loader** is `/usr/lib/ldqnx.so.2`. The system libraries are `libc.so.3`, `libm.so.2` and `libsocket.so.3`; sockets are not in libc.
- **libc gaps** (SDK 6.5 headers): no `posix_memalign`, `aligned_alloc`, `epoll`, `eventfd`, `memfd_create`, `getrandom`, `pthread_getattr_np`, `mincore` or `SA_RESTART`. It does have `clock_gettime`, `shm_open`, `pthread_setname_np`, `poll` and `pthread_attr_getstack`.
- **Per-thread data** (`struct _thread_local_storage`, `<sys/storage.h>`) sits at the top of each thread's stack. `__tls()` returns it, and `__stackaddr` is the stack's lowest address.
- **Registers:** `ucontext_t.uc_mcontext.cpu.gpr[16]`, indexed by `ARM_REG_SP` (13), `ARM_REG_FP` (11), `ARM_REG_LR` (14), `ARM_REG_PC` (15) from `<arm/context.h>`.
- **Native SDK 2.1 sysroot** (`playbook/sdk/bbndk-2.1.0/target/qnx6/armle-v7`) has `libEGL`, `libGLESv2`, `libscreen`, `libfreetype`, `libfontconfig`, `libsqlite3`, `libxml2`, `libpng`, `libjpeg`, `libz`, `libcurl.so.2`, `libssl.so.2` (OpenSSL 1.0.0e) and ICU 4.6. ICU 4.6 and OpenSSL 1.0.0e are too old for WebKit.
- **WebKit's minimum GCC by version:** 6.0 (2.24), 7.3 (2.26 to 2.34), 8.3 (2.36), 11.2 plus C++23 (since June 2024).
- **JIT status:** JSC picked C\_LOOP because `PlatformEnable.h` has no QNX case. JavaScriptCore's 32-bit ARMv7 JIT is still maintained upstream (Igalia, 2025), while MIPS JIT was dropped in 2024.

## Known risks and unverified code

None of the port has run yet. Test these first on the device:

| Risk | What could go wrong | How to check or fix |
| --- | --- | --- |
| Garbage collector pauses threads with a signal, without `SA_RESTART` | A thread blocked in `read`, `poll` or `sem_wait` gets `EINTR` during GC, and code that doesn't retry fails | Run a GC-heavy script in `jsc` with worker threads. Proper fix: pause with `ThreadCtl(_NTO_TCTL_ONE_THREAD_HOLD)` and read registers through `/proc/<pid>/as` with `devctl(DCMD_PROC_GETGREG)` |
| Main-thread stack bounds | `__tls()->__stackaddr` may not describe the main thread's growable stack, which could trigger false stack-overflow errors or miss real overflows | Run deep recursion in `jsc` and compare with `pidin mem` |
| Frame pointer register | We copied Linux and map FP to r11, but Thumb-2 code uses r7 | Only matters for the sampling profiler and JIT. Revisit when the JIT is enabled. |
| bmalloc and Gigacage on 32-bit QNX | Large virtual memory reservations may fail under QNX's address-space limits | If `jsc` fails at startup, retry with `-DUSE_SYSTEM_MALLOC=ON` |
| Library versions on the device | `jsc` needs GCC 9.3's `libstdc++.so.6`, not the firmware's | Ship our copies alongside and set `LD_LIBRARY_PATH` |
| Rooting is currently broken | Last attempt stopped at "Path traversal failed" injecting `start-android-core.sh`, probably because the Android permissions fix made it read-only (555) | See `session-notes-2026-10-02.md`, "Reboot test". Must be fixed before any device test. |

## Next steps

1. **Fix rooting**, then copy `jsc`, `libJavaScriptCore.so.1`, the ICU 71 libraries and GCC 9.3's `libstdc++`/`libgcc_s` to the device and run a test script over SSH.
2. **Turn on the ARMv7 JIT:** add QNX to `PlatformEnable.h`, confirm `mmap` with `PROT_EXEC` works for a non-system process, and fix the frame-pointer mapping.
3. **Cross-build the next set of libraries** into `sysroot/`: GLib, libsoup (or the curl network backend), OpenSSL 1.1.1 or 3.x, harfbuzz, a newer freetype, libwebp, libepoxy and woff2. Reuse `qnx_compat.h` and add stand-ins for the missing libc functions as they appear.
4. **Build the full WPE port** with a small libwpe backend that draws into a QNX Screen window through EGL and GLES 2.0. Start with CPU rendering, then try the SGX540.
5. **Media:** write a `MediaPlayerPrivate` backend on QNX `mm-renderer` for hardware H.264 and AAC, and an audio output on `io-audio` for Web Audio. Check whether `mm-renderer` can take a byte stream, which Media Source Extensions (YouTube) need.
6. **Toolchain stage 2:** build GCC 13 or 14 for `arm-blackberry-qnx8eabi`, using Psyden's GCC 9.3 patches as the starting point, to move toward current WebKit.

## Sources

- [WebKitGTK/WPE GCC requirement history](https://trac.webkit.org/wiki/WebKitGTK/GCCRequirement?version=26): minimum GCC per release up to 2.36
- [WebKit: GCC 11.2 and C++23](https://webkit.org/?p=11186): the June 2024 bump
- [WebKit compiler support policy](https://docs.webkit.org/Ports/WebKitGTK%20and%20WPE%20WebKit/GCCRequirement.html)
- [Igalia WebKit WIP 19 (2025)](https://blogs.igalia.com/webkit/blog/2025/wip-19/): ARMv7 JSC status
- [WPE WebKit 2.36.8 release tarball](https://wpewebkit.org/releases/wpewebkit-2.36.8.tar.xz)
- [ICU 71.1 release](https://github.com/unicode-org/icu/releases/tag/release-71-1)
- Local: `session-notes-2026-10-02.md` (rooting and device access) and the earlier planning doc, Porting WebKit to the BlackBerry PlayBook
