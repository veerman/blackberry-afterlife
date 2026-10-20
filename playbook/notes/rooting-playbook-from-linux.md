# Rooting a BlackBerry PlayBook from Linux

Oct 2, 2026 · @Steve

> **Partly out of date.** Since this was written, the Browser crash was traced to our own setup steps and fixed, and the OpenSSL upgrade now works. See `../README.md` and `session-notes-2026-10-02.md`.
>
> Local copy of the Claude Doc https://claude.ai/code/artifact/1bdd9569-6940-4cf5-b8fb-078aae4302bb. Later progress (TLS upgrade working, rooting regression) is in `session-notes-2026-10-02.md`.

## Summary

On 2 October 2026 we flashed and rooted a Wi-Fi BlackBerry PlayBook (32 GB, hardware ID `0x06001A06`) entirely from Linux, with no Windows at any step. We flashed official Tablet OS 2.1.0.1917 first to prove the path, then [Psyden's](https://archive.org/details/PlayBook-ROOT-patch) root image V1.4, then got a root SSH shell over USB using our own keys.

What is new here is mostly the detail Psyden's guide leaves out:

- why the Linux key upload fails, and the exact key the tablet accepts;
- that Development Mode switches itself off on every reboot;
- that the root image ships with serious security holes;
- that it breaks the Android runtime;
- that dotted app IDs silently fail to uninstall;
- how the home-screen layout is stored.

**Still broken:** Browser, Clock, Setup and Android apps crash on launch inside WebKit. We have not found the cause yet (see [Open problems](#open-problems)).

## What you need

| Item | Source | Check |
| --- | --- | --- |
| Official 2.1.0.1917 image `PlayBook_2.1.0.1917_R1315.signed` (1,099,891,248 B) | [playbook-root-downgrade-1.0](https://archive.org/details/playbook-root-downgrade-1.0), folder `2.1.0.1917/Official` | MD5 `794ec09697a45379711cd82e01682a0c`; ends in a genuine `QNXH-OS-1` seal |
| Root image `PlayBook_2.1.0.1917_ROOT_V1.4.EXE` (1,161,637,548 B) | [PlayBook-ROOT-patch](https://archive.org/details/PlayBook-ROOT-patch) | MD5 `1897c3fa211bcef627c5afe65b72303a`; no seal (zeros) |
| `PlayBook-root-setup-V3.py`, `BerryShell-V2.py`, `QCL.py` | same item | MD5 `bfd938db…`, `dc9f905b…`, `bb721511…` |
| `bb10mt` (Linux build) + `loaders.dat` | `v3root.zip` from [bb10.root.sx](https://bb10.root.sx/blog/pre-rooted-autoloaders-v3) | `LDR_01` already maps `06001a06` |
| libusb, libfuse 2, Python 3 with `cryptography` | distro packages; `cryptography` in a venv |  |
| A udev rule for vendor `0fca` | see the Leap write-up |  |

Psyden's root image keeps the official system partitions byte for byte (MBR, rcfs, ifs and signature all match the official image); only the user partition differs.

## Procedure

Both flashes erase the tablet. The "listener first" routine applies to every flash and `info` call: start bb10mt, unplug, power fully off, plug back in while off.

1. **Read-only check:** `./bb10mt info`. Ours reported bootrom 5.27.0.20, OS 2.1.0.1917 and an OS blocklist below 2.1.0.1281 (no downgrade without the December guide's NVRAM step).
2. **Flash official first** to prove the path: `./bb10mt flash -i PlayBook_2.1.0.1917_R1315.signed`. About 7 minutes (≈15%/min); it booted to the language screen.
3. **Flash the root image:** `./bb10mt split -i PlayBook_2.1.0.1917_ROOT_V1.4.EXE -o split/` then `./bb10mt flash -i split/PlayBook_2.1.0.1917_ROOT_V1.4.0.signed`. bb10mt reports **"Signature send error"** because the image has no seal; the PlayBook boots anyway, straight to the home screen.
4. **On the tablet:** Settings → Security → Development Mode on (it forces a device password); Settings → Storage & Sharing → USB Connections → *Connect to Mac*. The tablet appears as `0fca:8013` with a USB network link.
5. **Run the root script:** `python3 PlayBook-root-setup-V3.py --ip 169.254.0.1 --password <pw>`. It needs only Development Mode, not a devuser shell.
6. **Get in and install your key.** The image's `.ssh` folder is root-owned, so a developer-mode key upload always fails ("Unable to open authorized\_keys2"). After step 5, `qconn` runs as root on port 9090, so `python3 QCL.py --host 169.254.0.1 put mykey.pub /accounts/devuser/.ssh/authorized_keys2` installs your key, then `ssh root@169.254.0.1` works. Then apply the [security fixes](#security-problems-in-the-root-image) immediately.
7. **SSH client settings** for the tablet's old sshd: `HostKeyAlgorithms +ssh-rsa`, `PubkeyAcceptedAlgorithms +ssh-rsa`, `KexAlgorithms +diffie-hellman-group14-sha1`, `Ciphers +aes128-ctr`, `MACs +hmac-sha1`. Use `scp -O`.

**After every reboot** root is gone (tethered), and so is Development Mode. Turn Development Mode back on, then re-run step 5. If you replugged the cable, the tablet's address may have changed; check it with `ip -br addr` (the laptop gets `.2` or another address in a /30, the tablet the other one). Development Mode re-pins `169.254.0.1` once enabled.

**Developer-mode key upload (if you need it):** the tablet only accepts RSA keys of **4096 bits or more**, and BerryShell truncates the uploaded key to **720 bytes**. Only a 4096-bit key with **public exponent 3 and no comment** fits both limits. `bb10mt connect` sends the key but then drops the connection, and devuser SSH only runs while that connection stays open; BerryShell's 4-second heartbeat keeps it alive.

## Security problems in the root image

The root image works, but as shipped it leaves the tablet open to anyone on the same network. We fixed everything below within minutes of the first root run, editing the files in `/accounts/devuser` that the root step re-reads on every run, so the fixes persist.

| Problem in V1.4 | Risk | Our fix |
| --- | --- | --- |
| `RLogging.cgi` and `root.sh` start `qconn port=9090` as root | qconn has no authentication: anyone on the Wi-Fi gets a root shell | Removed both lines. Only `QCL.py` uses it; BerryShell uses the password-protected port 4455 |
| `sshd_config`: `PermitRootLogin yes`, `PasswordAuthentication yes`, `PermitEmptyPasswords yes` | Password and empty-password root logins over every interface | `PermitRootLogin without-password`, `PasswordAuthentication no`, `PermitEmptyPasswords no` |
| `.ssh/authorized_keys2` holds a third party's key (`from="169.254.0.2"`) | Someone else's key on your tablet | Replaced with your own key |
| Every root-kit script is mode 777 | Any app can edit what later runs as root | `chmod -R go-w` on the kit |
| `sshd-watchdog.sh` polls every 1 s (its comment says 10) | Battery drain | `sleep 10`; start it with `on -d` (no `nohup` on the PlayBook) |
| OTA, push, DCS and EULA URLs and the ad server point at `service.waitberry.com` | The tablet contacts a third-party server | Reset through PPS: `sls::https://cs.sl.blackberry.com/cse`, deleted `push`, `push_appid`, `dcs_url`, `eula_url`, official `ad_serving_url` |

After the fixes: port 9090 closed, a password login is answered "Permission denied (publickey)", and only our key gets root.

## Removing apps and setting the home screen

**Uninstalling** works through the Development Mode installer at `https://<tablet>/cgi-bin/appInstaller.cgi`, using the same login as the root script and the command `Uninstall` with `package_name` and `package_id`. Two traps:

- The `package_id` must use `-` where the folder name has `.` (`gYABgPG-Su8Azx…`, not `gYABgPG.Su8Azx…`). With a dot, the reply sometimes reads `result::success` while **nothing is removed**. Check `/apps` afterwards.
- Each login triggers a password prompt on the tablet. Do all actions in one session to get one prompt.

We removed App World, Music Store, PressReader, Weather, Print To Go, Accessories Store, Help and all 14 BlackBerry Bridge items. Adobe Reader, Docs To Go and AirTunes (the Music app) stay.

**Layout** is rebuilt from two plain-text defaults whenever the launcher's cache is missing:

- `/var/etc/default_order`: the grid, one `app-id,0` per line.
- `/var/etc/default_dock`: the top row, one `app-id` per line.

To change them: `slay -9` the launcher (a normal stop saves its old layout over yours), write both files, delete `catstate` and `core.all` in `/accounts/1000/appdata/sys.navigator/data/`, then relaunch with `on -d launcher-secure -U 89:0 -m 970 -t 4 -p / -v -b sys.navigator`. Settings is the status-bar gear, not an app, so it cannot go in the dock.

## Android apps

The PlayBook runtime is Android 2.3.3 (API 10) and runs **Java code only**. Any APK with native libraries (`lib/*.so`) fails, which rules out Firefox, VLC and Opera Mini. Signal is impossible (it needs Android 6+). Of the apps we wanted, only Chroma Doze 3.7.1 (white noise, minSdk 8, [F-Droid archive](https://f-droid.org/archive/net.pmarks.chromadoze_25.apk)) qualifies.

**Converting on Linux** with BlackBerry's [Command Line Tools 1.6.1](https://archive.org/details/android-apps-for-blackberry-tablet) (`apk2bar`):

1. Java 8, e.g. `mise x java@temurin-8 -- …`.
2. An Android SDK folder holding `build-tools/23.0.3/{aapt,dexdump}` (Google's `build-tools_r23.0.3-linux.zip`, SHA-1 `368f2600…`). Those binaries are 32-bit, so they need lib32 glibc, zlib and gcc-libs.
3. `ANDROID_HOME=<sdk> apk2bar app.apk -t bars -os 2.1`. The `-os 2.1` matters: without it, apps targeting newer Android get marked as BB10-only.

**Installing** the unsigned `.bar` works through the same `appInstaller.cgi` with command `Install` and the file as a multipart upload. Psyden's patched installer accepts unsigned packages. BlackBerry's Java `blackberry-deploy` fails with "peer not authenticated" against the tablet's old TLS.

**Runtime bug in the root image:** V1.4 sets every file in `sys.android*` to 777 (504 files, normally 640/555/750), so the Android runtime crashes in a loop. Restoring the official modes fixed it (zygote, servicemanager and mediaserver start), but keep `native/scripts/` and `start-android-core.sh` writable, because the root script overwrites that file. Chroma Doze still does not open; see Open problems.

## What we learned

| Finding | Why it matters |
| --- | --- |
| The PlayBook bootrom (5.27, 2011) boots images whose signature trailer is rejected | bb10mt's "Signature send error" on seal-less images is harmless here, unlike on BB10 phones |
| Psyden's image changes only the user partition; system partitions match official | Official 2.1.0.1917 is a full recovery path |
| Development Mode turns off on every reboot | The root script then fails with "Path traversal failed"; the real reply is "Device is not in the Development Mode" |
| Developer key upload needs RSA ≥ 4096 bits; BerryShell sends at most 720 bytes | Only a 4096-bit key with exponent 3 and no comment works |
| Devuser SSH only lives while the qconn "door" on 4455 is held open | `bb10mt connect` drops it; use a heartbeat |
| `.ssh` in the root image is root-owned | A devuser shell is impossible before root; get in via the root step |
| Uninstall IDs need `-` instead of `.` | Otherwise `result::success` can be a no-op |
| Layout lives in `/var/etc/default_order` and `default_dock` | Editable, but only with the launcher hard-killed |
| Root image makes the Android runtime 777 | Breaks Android; restore official modes |
| System TLS is OpenSSL 1.0.0e (`libssl.so.2`/`libcrypto.so.2`), used by libcurl 7.21.3 and WebKit | No TLS 1.2 — the reason modern HTTPS fails |
| The 2.1.0 Native SDK (gcc 4.4.2) runs on 64-bit Linux with lib32 libraries and patchelf `--no-sort` | Building for the PlayBook from Linux is possible |
| QNX `ln -sP` links live in memory | Overlays vanish on reboot — a built-in undo |

## Open problems

**Browser, Clock, Setup and Chroma Doze do not run.** Calculator, File Manager, Pictures, Camera, Calendar, Messages and Adobe Reader work. What we know:

- The failing apps are AIR apps that use WebKit (plus the Android shell). The AIR process `adl` dies about 1.5 s after launch with signal 11, code 0, at `libwebkit.so.0` offset `0xb1af10` on WebKit thread 12, in clean-up code (`r4 = 0`, called from `free`). The core dump is at `/accounts/1000/appdata/sys.browser.*/logs/adl.core`.
- It is not caused by the OpenSSL test: the crash continues with the stock libraries and after a reboot without root.
- It is not the launcher's verification (it passes), missing PPS services (identical to official), the third-party URLs or bookmarks (both restored), or saved app data (none exists).
- When we launched the browser by hand from a root shell, it crashed instead in `eglInitialize`. That may only be because the shell lacks screen permissions, but it points at the graphics stack, which all the failing apps use.
- Not yet ruled out: the uninstalled apps (including the BlackBerry Bridge service), our launcher layout edits, or a bug in Psyden's image. We never opened the Browser on an unmodified root image, so we cannot tell which.

**The OpenSSL upgrade did not work as a drop-in.** OpenSSL 1.0.2u, cross-compiled with the Native SDK (`enable-ssl2 enable-ssl3 enable-md2 enable-rfc3779`, syslog header shim, SONAMEs patched to `.so.2`), worked through the system `libcurl`. It fixed TLS 1.2 (letsencrypt.org) and google.com certificate verification. But overlaying it system-wide made every AIR app crash, so we reverted it. Next idea: give only `libcurl` the new library under a different name, leaving AIR on 1.0.0e.

**Next steps to try:**

1. Restore the original layout files from the backup and test the Browser.
2. Copy the uninstalled apps back from the official image.
3. Capture a full-permission launch log of the Browser.

## References and credits

- [Psyden: PlayBook latest root (V1.4)](https://archive.org/details/PlayBook-ROOT-patch) and [Downgrade and root (Dec 2025)](https://archive.org/details/playbook-root-downgrade-1.0), including the official images.
- [bb10mt](https://github.com/bb10root/bb10mt) and the research at [bb10.root.sx](https://bb10.root.sx) by Oleksandr.
- [BlackBerry Native SDK for Tablet OS](https://archive.org/details/native-sdk-for-blackberry-tablet) (2.1.0 Linux installer, MD5 `933c13c9…`) and [Psyden's GCC 9.3 PlayBook toolchain](https://github.com/Psyden57/BB-PlayBook-gcc-9.3.0).
- [BlackBerry Android tools for the PlayBook](https://archive.org/details/android-apps-for-blackberry-tablet) (Command Line Tools 1.6.1).
- [OpenSSL 1.0.2u](https://www.openssl.org/source/old/1.0.2/) (SHA-256 `ecd0c6ff…`).
- Companion write-up for BB10 phones: [Flashing Stock BB10 Firmware from Linux](https://claude.ai/code/artifact/bc4357ac-feed-4169-8f6e-e7811c43af5e).
