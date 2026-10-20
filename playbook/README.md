# BlackBerry PlayBook from Linux

**Result:** a 2011 PlayBook (Wi-Fi 32 GB, Tablet OS 2.1.0.1917) flashed and rooted from Linux, with the root image's security holes fixed and 20 dead cloud apps removed. The built-in Browser loads modern HTTPS sites again thanks to a newer TLS library.

**Status (October 2026):** everything below worked. After the last reboot, the root script stopped working ("Path traversal failed"; see [Open problems](#open-problems)), so the tablet is currently unrooted. Its persistent changes (app removals, Chroma Doze, home-screen layout) are still in place.

## What we did, in short

| Area | What and how | Details |
| --- | --- | --- |
| **Flash** | Official 2.1.0.1917, then Psyden's ROOT V1.4 image, both with `bb10mt` on Linux. The 2011 bootrom doesn't enforce image signatures, so bb10mt's "Signature send error" is harmless here. | [notes/rooting-playbook-from-linux.md](notes/rooting-playbook-from-linux.md) |
| **Root** | Psyden's `PlayBook-root-setup-V3.py`. It is **tethered**: after every reboot, turn Development Mode back on (it switches itself off) and run the script again. | same |
| **Security fixes** | The root image opens an unauthenticated root shell (qconn on port 9090), allows empty-password SSH, and ships a stranger's SSH key. Our fixes: [root-kit-hardening.diff](root-kit-hardening.diff), plus replacing the key with your own. | same |
| **Debloat** | 20 apps removed with `scripts/pb_cgi.py Uninstall <id>`: App World, Music Store, PressReader, Weather, Print To Go, Accessories Store, Help, and all 14 BlackBerry Bridge apps. Keep `sys.bbbridge`, a hidden service the Browser uses. | [notes/session-notes-2026-10-02.md](notes/session-notes-2026-10-02.md) |
| **Browser TLS** | The system TLS library is OpenSSL 1.0.0e, which has no TLS 1.2, so most HTTPS sites fail. We rebuilt **OpenSSL 1.0.2u** as a drop-in `libssl.so.2`/`libcrypto.so.2` and refreshed the CA certificates. `scripts/tls-switch.sh` layers them over the system copies in RAM and restarts the AIR process the Browser runs in. Wikipedia, GitHub and Google load. A reboot reverts it, so the hardened `root.sh` re-applies it. | same, section "TLS upgrade" |
| **Android apps** | The runtime is **Android 2.3.3 (API 10)** and runs **pure-Java apps only**: any APK that bundles native `.so` libraries fails, which rules out Firefox and VLC. **Chroma Doze 3.7.1** (white noise) works. APKs are converted to `.bar` with BlackBerry's `apk2bar` and installed with `scripts/pb_install.py`. | [notes/rooting-playbook-from-linux.md](notes/rooting-playbook-from-linux.md#android-apps) |
| **Modern browser engine** | Early port of WPE WebKit 2.36.8. JavaScriptCore cross-compiles with Psyden's GCC 9.3; it hasn't been run on the tablet yet. | [notes/playbook-webkit-port-handoff.md](notes/playbook-webkit-port-handoff.md), [plan](notes/porting-webkit-to-playbook-plan.md) |
| **BB10's Android 4.3 on the PlayBook?** | Offline analysis only: same package design, but 17 missing libraries and 353 unresolved symbols. A long shot. | session notes, section "BB10 Android 4.3 runtime"; scripts in `analysis/bb10rt/` |

## Lessons that cost us the most time

- **Development Mode turns off on every reboot.** The root script then fails with a misleading "Path traversal failed".
- **Uninstall IDs need `-` instead of `.`.** Dotted IDs return `success` and do nothing.
- **Never kill system processes by name** (`slay`). Doing so took down the app launcher once. Kill one exact PID, then check `launcher-secure` is still running.
- **The root script orphans the Android runtime**, causing a crash loop every 5 seconds. Fix: installer `Terminate`, kill the orphaned zygote and system_server by PID, and *don't* press `Launch`. Opening an Android app starts the runtime cleanly.
- **Before restarting a system service, note its device node's owner and mode.** The relaunched AIR server came up root-only (`/dev/airfork` 600) and the Browser failed with "error 13" until we fixed it with `chown 89:0`.
- **One change at a time, with a Browser test after each.** That is how we found what broke things. The step plan is in [notes/step-by-step-plan-2026-10-02.md](notes/step-by-step-plan-2026-10-02.md).

## Open problems

1. **Re-rooting fails after the Android permissions fix.** `scripts/android-perms-fix.sh` restores official file modes. That probably makes `start-android-core.sh` read-only, so the root script can't overwrite it. Untested fix: keep that file writable.
2. **The TLS upgrade isn't persistent.** It is re-applied by `root.sh` after each re-root.
3. **The WebKit port hasn't run on the device yet.** Next step: copy `jsc` and its libraries over SSH and run it.

## Files

| Path | What |
| --- | --- |
| `scripts/pb_cgi.py` | Sends commands to the tablet's Development Mode installer (`List`, `Uninstall`, …) |
| `scripts/pb_install.py`, `pb_install_batch.py` | Install `.bar` packages |
| `scripts/pb_door.py` | Keeps the developer-mode connection (port 4455) open and uploads your key |
| `scripts/pb_flash_pw.py` | Runs `bb10mt`, answers the device-password prompt, and stops if a password attempt is used up |
| `scripts/tls-switch.sh` | Applies the OpenSSL 1.0.2u and CA overlay on the device and restarts the AIR server |
| `scripts/android-perms-fix.sh` | Restores official modes on the Android runtime (the root image sets everything to 777) |
| `root-kit-hardening.diff` | Our security fixes to Psyden's root kit (`/accounts/devuser`) |
| `openssl/build.sh`, `shim/`, `test/tlstest.c` | Reproducible OpenSSL 1.0.2u build, a missing-header shim, and an HTTPS test through the system libcurl |
| `webkit/patches/`, `webkit/qnx-compat/`, `webkit/playbook-toolchain.cmake` | The WebKit port |
| `layout/2026-10-03/` | Home-screen layout files from the navigator |
| `analysis/` | Diff of Psyden's image against official, permission snapshots, BB10 runtime analysis scripts |
| `notes/` | Full write-ups and dated session notes |

## Reproduce it

Everything here is built from public downloads. Put them where the table says (those paths are git-ignored).

| What | Put it in | From | Check |
| --- | --- | --- | --- |
| Official image `PlayBook_2.1.0.1917_R1315.signed` | `firmware/official/` | [playbook-root-downgrade-1.0](https://archive.org/details/playbook-root-downgrade-1.0), folder `2.1.0.1917/Official` | MD5 `794ec09697a45379711cd82e01682a0c` |
| Root image `PlayBook_2.1.0.1917_ROOT_V1.4.EXE` | `firmware/` | [PlayBook-ROOT-patch](https://archive.org/details/PlayBook-ROOT-patch) | MD5 `1897c3fa211bcef627c5afe65b72303a` |
| `PlayBook-root-setup-V3.py`, `BerryShell-V2.py`, `QCL.py` | `third-party/psyden/` | same item | the helper scripts load them from here |
| `bb10mt` + `loaders.dat` | `../leap/v3root/` (shared with the Leap) | `v3root.zip` from [bb10.root.sx](https://bb10.root.sx/blog/pre-rooted-autoloaders-v3) | the PlayBook's ID is already mapped |
| BlackBerry Native SDK 2.1.0 for Linux | `sdk/bbndk-2.1.0/` | [native-sdk-for-blackberry-tablet](https://archive.org/details/native-sdk-for-blackberry-tablet) | installer MD5 `933c13c934c6312a6ff45b09b790b870` |
| Psyden GCC 9.3 toolchain | `sdk/psyden-gcc9/playbook-gcc9/` | [Psyden57/BB-PlayBook-gcc-9.3.0](https://github.com/Psyden57/BB-PlayBook-gcc-9.3.0) | toolchain tarball SHA-256 `fe7c6fc8…dfabf`, target libs `8e6f5c9d…ecf0` |
| BlackBerry Command Line Tools 1.6.1 (`apk2bar`) | `third-party/blackberry.tools.SDK/` | [android-apps-for-blackberry-tablet](https://archive.org/details/android-apps-for-blackberry-tablet) | needs Java 8 |
| Chroma Doze 3.7.1 | `apks/` | [F-Droid archive](https://f-droid.org/archive/net.pmarks.chromadoze_25.apk) | |

**Flash and root:** follow [notes/rooting-playbook-from-linux.md](notes/rooting-playbook-from-linux.md), "Procedure". Then apply `root-kit-hardening.diff` to `/accounts/devuser` on the tablet and replace `.ssh/authorized_keys2` with your own key. The scripts need Python 3 with `cryptography` (`python3 -m venv .venv && .venv/bin/pip install cryptography`).

**OpenSSL 1.0.2u:** `playbook/openssl/build.sh`. It downloads and checks the source, then builds it into `playbook/openssl/out/`. Verified on 2026-10-20: it reproduces the libraries that worked on the tablet (same exports; `libssl` byte-identical). To install, stage `out/*.so.2` and a CA folder in `/var/tls102/` on the tablet and run `scripts/tls-switch.sh` with the Browser closed. Full steps are in the session notes, section "TLS upgrade".

**Android apps:** `ANDROID_HOME=<sdk-with-build-tools-23.0.3> apk2bar app.apk -t bars -os 2.1`, then `scripts/pb_install.py`. The `-os 2.1` matters. Details: [notes/rooting-playbook-from-linux.md](notes/rooting-playbook-from-linux.md#android-apps).

**WebKit (JavaScriptCore):** follow "Rebuild from scratch" in [notes/playbook-webkit-port-handoff.md](notes/playbook-webkit-port-handoff.md). Apply `webkit/patches/0001-*.patch` to a fresh `wpewebkit-2.36.8` tarball and build with `webkit/playbook-toolchain.cmake`. About 15 minutes on 18 cores.

**Known gap:** we unpacked the 2012 Native SDK installer by hand and didn't record the exact steps. Its 32-bit host tools then needed 32-bit glibc, zlib and gcc-libs (Arch: `lib32-glibc lib32-zlib lib32-gcc-libs`) and `patchelf --no-sort`.
