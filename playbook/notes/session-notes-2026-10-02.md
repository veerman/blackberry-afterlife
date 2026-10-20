# PlayBook session notes (2026-10-02/03)

Handoff notes so this work can resume after a disconnect. Device times below are the PlayBook's clock (GMT).

## Goal

Remove broken default apps from the PlayBook to free storage, **one at a time, testing the Browser after each**. A previous attempt removed everything at once and broke the Browser.

This sits inside the bigger plan in `step-by-step-plan-2026-10-02.md`: after a fresh flash of Psyden's ROOT V1.4 image, redo every setup step one at a time and test the Browser after each, to find which step broke it before.

## Connection basics

- Plug in over USB. If the host sees `0fca:8020` (CD-ROM mode), run `eject /dev/sr0`. The device then switches to `0fca:8013` (network) and the host gets `169.254.0.2` on `enp0s20f0u2`. The PlayBook is `169.254.0.1`.
- PlayBook USB connection setting: **Mac mode**.
- **Development Mode** must be on (Settings gear, then Security, then Development Mode). It **turns off on every reboot**.
- Device password: `password`.
- Root is **tethered**. After each reboot, enable Dev Mode, then run:
  `python3 playbook/third-party/psyden/PlayBook-root-setup-V3.py --ip 169.254.0.1 --password password`
- After rooting: `ssh playbook` logs in as root with `~/.ssh/playbook` (config is in `~/.ssh/config`).
- Fallback shell is Psyden's unauthenticated qconn on port 9090, via `playbook/third-party/psyden/QCL.py` (put, get, exec). Passing arguments through `exec` with quotes doesn't work: upload a script with `put`, then `exec /bin/sh /tmp/script.sh`.
- PlayBook shell lacks `head`, `cksum` and `grep -m`. Pull output back to the host and process it there.

## App removal

Tool: `PB_PASSWORD=password python3 playbook/scripts/pb_cgi.py "Uninstall" "<full.package.id>"`
- The command is `Uninstall`; `Uninstall App` returns "Invalid command".
- To list installed apps: `python3 playbook/scripts/pb_cgi.py "List" "dummy.x.testDev_dummy0000000000000000000000"`
- Backup `.bar` files for every app on the list are in `playbook/device-backups/restore-bars/`, so any removal can be reinstalled.

Order (from step-by-step-plan-2026-10-02.md), with status:

| # | App | Package ID | Status |
|---|---|---|---|
| 1 | Accessories Store | `sys.uri.accessories_store.gYABgCDu.hhMJeFAiLPh92RpaWU` | **Removed**, Browser OK afterwards |
| 2 | Help | `sys.help.gYABgPG.Su8AzxaqqONbaanIprc` | Refused before root (`failure 535 permanent`); **removed after root** (confirms root lifts the protection), Browser OK |
| 3 | Print To Go | `sys.printoutstogo.gYABgPMP3nxNZlNieZUDetUiQio` | **Removed** after root, Browser OK |
| 4 | PressReader | `com.newspaperdirect.PRPlaybook.gYABgH6PjIOYjts_3bofsu9llxw` | **Removed** after root, Browser OK |
| 5 | Weather | `sys.weather.gYABgKOf0EhVEWtCxrbBQ00sPSg` | **Removed** after root, Browser OK |
| 6 | Music Store | `sys.musicstore.gYABgAP_fJGCaDEp_osJknksgPw` | **Removed** after root, Browser OK |
| 7 | App World | `sys.appworld.gYABgNSvaLtte_snIx7wjRsOcyM` | **Removed** after root, Browser OK |
| 8 | Bridge App 01 | `sys.bridgeApp01.gYABgCDEawLDzU7faEC9XtQaGew` | **Removed** after root, Browser OK |
| 8 | Bridge App 02 | `sys.bridgeApp02.gYABgKQs.iUwNLMlCDdenn39w9Q` | **Removed** after root, Browser OK |
| 8 | Bridge App 03 | `sys.bridgeApp03.gYABgDzHSEWE78.LHtTApjyfXEY` | **Removed** after root, Browser OK |
| 8 | Bridge App 04 | `sys.bridgeApp04.gYABgDkR.SLIz4zMs2afxJj32BQ` | **Removed** after root, Browser OK |
| 8 | Bridge App 05 | `sys.bridgeApp05.gYABgEAp.HoYsfaGs3jKkruwRMk` | **Removed** after root, Browser OK |
| 8 | Bridge BBM | `sys.bridgeBBM.gYABgPzxYrykYf4ijvmGsvE7B1Q` | **Removed** after root, Browser OK |
| 8 | Bridge SMS | `sys.bridgeSMS.gYABgCnmkzd34YfOHCmfdXDje6c` | **Removed** after root, Browser OK |
| 8 | Bridge Messages | `sys.bridgeMessages.gYABgH_nFAFLgYWPsGIizCKh7JQ` | **Removed** after root, Browser OK |
| 8 | Bridge Contacts | `sys.bridgeContacts.gYABgPggBTtmkAlbYC6VFu1Gllo` | **Removed** after root, Browser OK |
| 8 | Bridge Calendar | `sys.bridgeCalendar.gYABgMyHc.mTKnr5EXdmDe_39e8` | **Removed** after root, Browser OK |
| 8 | Bridge Tasks | `sys.bridgeTasks.gYABgGd11iGxTL7m8Y4O2kyjMXk` | **Removed** after root, Browser OK |
| 8 | Bridge MemoPad | `sys.bridgeMemoPad.gYABgNANNsbWVSWZpC4.aBaAv1E` | **Removed** after root, Browser OK |
| 9 | Bridge Browser | `sys.bridgeBrowser.gYABgFX7ZKaP5vqkK1khM4zoP0A` | **Removed** after root, Browser OK |
| 10 | `sys.bbbridge` | `sys.bbbridge.gYABgBRG3Sb5_hQ1xd8Gv8dIhY4` | **Keep**: hidden WebKit launcher service |

The "permanent" refusals are why the user chose to follow the step-by-step-plan-2026-10-02.md plan: root and harden first, then go back to removals. The last time these apps were removed, the device was rooted.

## Setup steps since the fresh flash (step-by-step-plan-2026-10-02.md plan)

| Step | What | Browser test |
|---|---|---|
| 1 | Development Mode on | OK |
| 2 | Root script run (00:59) | OK |
| 3a | Replaced the unknown preinstalled SSH key in `/accounts/devuser/.ssh/authorized_keys2` with ours (original saved as `authorized_keys2.psyden-orig`). New device host key pinned in `~/.ssh/known_hosts_playbook` (SHA256:T259sizfAlYCZkospf8ptWfKFwRtOJJbEhCA6M4/3Fs, verified against `/etc/ssh/ssh_host_rsa_key.pub`; old file saved as `known_hosts_playbook.bak-20261002`) | OK |
| 3b | Installed `playbook/device-backups/devuser-hardened/sshd_config` (key-only) to `/accounts/devuser/` and `/var/etc/ssh/`; installed hardened `sshd-watchdog.sh` (checks every 10 s instead of 1 s). Originals saved on the device with a `.psyden-orig` suffix | First test failed (launcher killed by manual process kills, see below); **OK after reboot + re-root** |
| 3c | Remove the qconn port 9090 lines from `root.sh` and `opt/www/cgi/RLogging.cgi` (hardened copies are in `playbook/device-backups/devuser-hardened/`). Done at 01:17: originals saved as `.psyden-orig`, running qconn stopped by exact PID, launcher unaffected, port 9090 closed. **QCL fallback is gone; SSH is the only way in** | OK |
| 3d-i | `chmod go-w` on root-kit scripts/config: `root.sh`, `sshd-watchdog.sh`, `sshd_config`, `restart-launcher.sh`, `symlink.sh`, `sloginfo.sh`, `opt/www/cgi/RLogging.cgi` (now `rwxr-xr-x`). Pre-3d permissions saved in `playbook/analysis/devuser-perms-before-3d.txt` | OK |
| 3d-ii | `chmod -R go-w` on `bin`, `lib`, `symlink` (`symlink/` overlays into `/base`, incl. Psyden's `launcher-secure` and patched deckard installer .pyc). Verified no group/other-writable entries left; launcher still running | OK |
| 3d-iii | `chmod -R go-w` on `opt/www` except `opt/www/log` (Dev Mode web service CGIs incl. appInstaller.cgi); then check `pb_cgi.py List` still works. Done; `log/` left 777; installer login + List still work (74 apps) | OK |
| 3d-iv | `chmod -R go-w` on `opt/webkit` (WebKit config/resources, linked via `/base/opt`; prime suspect for the original Browser break). Done (+ `opt` itself); all 154 files were untouched since Aug 29, so nothing writes there | OK — **step 3 complete, Browser still works** |

`fs1.qnx6` and `nvram` stay as they are (data files).
| 4 | App removals, one at a time (table above), now rooted + hardened | **Done**: all 20 removed, Browser OK after each |
| 5 | Home-screen layout | Done by hand by the user; order saved (see below) |
| 6 | Android runtime permissions fix (`playbook/scripts/android-perms-fix.sh`: 504 chmods on `sys.android` + `sys.android.shell` only). Pre-fix perms saved in `playbook/analysis/android-perms-before-step6.txt`. Perms alone did NOT stop the crash loop; see "Android crash loop" below | OK. Chroma Doze 1.0.25 (`playbook/bars/net.pmarks.chromadoze_25.bar`) installed via `pb_install.py`; **works** (also after runtime close/auto-relaunch) |

The OpenSSL experiment stays out entirely.

## The 3b failure: diagnosis (resolved)

Resolved: after a reboot and re-root, the 3b settings loaded on their own and the Browser worked. The cause was the manual process kills. Lesson: never `slay` by name; kill one exact PID at most, then check that `launcher-secure` is still alive.


- The Browser stuck on its splash screen and couldn't be closed.
- In the system log, the home screen asked the **launcher** to start the Browser at 01:08:04 and got no response. **The launcher process is gone**: `pidin arg` shows no launcher. Its last log entry is at 01:02:17, when it closed the Browser after the 3a test.
- So the launcher died during 3b. During 3b I stopped and restarted sshd and the watchdog several times (`slay -f sshd`, `kill <pid>` of the old watchdog, and a relaunch through qconn). One of those most likely took the launcher down. Nothing logged a crash. This is unproven.
- Problems hit while doing 3b:
  - `slay -f sshd-watchdog.sh` doesn't match the watchdog, because it runs as `/bin/sh`. Kill it by PID instead.
  - A watchdog started from an SSH session couldn't respawn sshd. Starting it through qconn with `on -d /accounts/devuser/sshd-watchdog.sh` worked: sshd came back about 10 s after being stopped.
- Before the reboot, the live state was: hardened config active, password login refused, a single watchdog running, and qconn 9090 still open.

Other observations from the log:
- The root script restarts the home screen (`sys.navigator` restarted at 00:59:54). The Browser was fine afterwards.
- The Android runtime (`app_process`) has been crash-looping with SIGSEGV every 5 s since 01:00:10, right after the root script. A `mediaserver` abort came at 00:59:50. This is the known Android permissions problem (step 6). It doesn't stop native apps from launching, but it wastes battery.
- The full system log from before the reboot was saved to the session scratchpad only, so it may be gone.

## Home-screen layout (arranged by hand, saved 2026-10-03 01:52)

**Dock (top row), left to right:** Browser · Chroma Doze · Calculator · Clock · Camera

**Grid, in order:**
1. File Manager
2. Pictures
3. Videos
4. Music
5. Docs To Go
6. Voice Notes
7. Calendar
8. Messages
9. Contacts
10. Adobe Reader
11. Setup

Exact files copied from `/accounts/1000/appdata/sys.navigator/data/` are in `playbook/layout/2026-10-03/` (`dock`, `core.all`, `catstate`, `userapps`). To restore them, the navigator has to be stopped while the files are replaced, and that is the risky process-kill path. Re-arranging by hand from the list above is safer.

## Android crash loop (cause found, fixed 01:39)

- **Running the root script orphans the Android runtime.** Its Launch/Terminate cycle leaves an old `zygote` (parent = init, own process group) plus its `system_server` running; each new zygote then segfaults every ~5 s.
- Fix used: installer `Terminate` (via `rs.perform_cgi_action(ip, pw, "Terminate")`), then `kill` the orphan zygote + system_server by exact PID (confirm with `pidin family`: ppid 1, own pgrp, not related to launcher-secure), then installer `Launch`. Result: one zygote + one system_server, no faults, launcher unaffected.
- **This will recur after every reboot + re-root.** Repeat the fix after rooting.
- **Better post-root fix (verified 01:48):** installer `Terminate`, kill the orphan pair by PID, and **skip `Launch`**. Opening any Android app (e.g. Chroma Doze) makes the launcher start the runtime itself in `hidden` mode: no window, no crash loop. Closing a visible runtime card from the app switcher also shuts it down cleanly, with no orphans.
- Side effect: installer `Launch` opens the runtime as a full-screen app (BlackBerry logo, "Initializing, Please Wait..."). It is not a reboot; tell the user to swipe up from the bottom bezel to minimize it.

## Next steps (original, now historical)

1. The user reboots the PlayBook (power button, then Restart), turns Dev Mode back on, and keeps Mac mode. If the host shows CD-ROM mode, run `eject /dev/sr0`.
2. Re-run the root script. On boot, `root.sh` copies the hardened `sshd_config` into place and starts the watchdog itself.
3. The user tests the Browser:
   - **Works**: the 3b settings are fine, and the launcher death came from the manual process kills. Don't kill processes by hand that way again. Continue with 3c, then 3d, then the removals (Help onward), testing the Browser after each.
   - **Broken**: restore the `.psyden-orig` files for `sshd_config` (both copies) and `sshd-watchdog.sh`, reboot, re-root and retest.
4. Check that `ssh playbook` works after re-rooting. If it doesn't, use the qconn 9090 fallback.

## Constraints and preferences

- Linux only. The user won't use Windows tools.
- The user doesn't want another reflash.
- Make one change at a time and have the user test the Browser after each. Wait for an explicit "Browser works" before continuing; a bare "ok" isn't a test result.

## Related files

- `step-by-step-plan-2026-10-02.md`: the step plan and removal order.
- `playbook/device-backups/devuser-orig/`, `playbook/device-backups/devuser-hardened/`: root-kit files before and after hardening.
- `playbook/scripts/pb_cgi.py`, `playbook/third-party/psyden/QCL.py`, `playbook/third-party/psyden/PlayBook-root-setup-V3.py`: tools.
- PlayBook write-up artifact: https://claude.ai/artifact/4SaPFd87Z1RavcNYFNBSwU

## TLS upgrade retry (2026-10-03): active until next reboot

- User believes the earlier "OpenSSL breaks AIR" was misattributed. Retrying with backups.
- Read-only checks: no system binary uses any of the 116 libcrypto / 19 libssl functions missing from the 1.0.2u build. The AIR fork server (`adl -airfork`, started once at boot by `SERVICE_adl` in `/scripts/startup.sh`, never respawned) preloads libssl/libcrypto/libcurl/libwebkit, so the Browser only sees new libs after that process restarts.
- `tlstest` on device: stock 1.0.0e fails google/wikipedia/github (no TLS 1.2); with `LD_LIBRARY_PATH` pointing at 1.0.2u, all connect with TLS 1.2 via the stock libcurl 7.21.3.
- Backups: `playbook/device-backups/tls-backup-stock-20261003/` (local, md5 = `playbook/device-backups/devlibs/`) and `/accounts/devuser/tls-backup-stock/` (device).
- Staged in `/var/tls102/` (world-readable; `/accounts/devuser` is 750, so apps can't read files there, which is a likely cause of the earlier AIR break). Includes a refreshed CA dir: the 90 stock certs plus current Mozilla roots, 200 hashed links.
- Switch script `playbook/scripts/tls-switch.sh` (copy on device at `/accounts/devuser/tls-new/tls-switch.sh`): process-manager links (`ln -sP`, RAM only) for libssl/libcrypto/the CA dir, then kills exactly the airfork + its multilog PIDs (passed as args) and relaunches with the boot command and environment. **A reboot reverts everything.** Log: `/accounts/devuser/tls-new/switch.log`.
- **Switched 02:10–02:11.** Overlays active; airfork relaunched (now PID 43384939 with logger 43384989), and it maps the 1.0.2u libssl/libcrypto. The first relaunch's logger failed ("unable to switch to current directory": the script ran from /accounts/devuser), so I added `cd /` to the script and relaunched once more. Launcher, navigator and SystemTray unaffected. Awaiting Browser test on old and modern HTTPS sites.

## BB10 Android 4.3 runtime on PlayBook: feasibility (offline analysis, 2026-10-03)

- Verdict: a long shot that looks workable. Roughly 60% that it boots to the framework with stub libraries; under 30% that it's fully usable (audio, camera, NDK).
- Same package design as the PlayBook's 2.3 runtime: same package IDs, `android_launcher`, QNX-ELF Android binaries, and `init.cfg` (COW fork, EGL android). ARMv7/NEON, so no CPU issue. Size: 1,106 files / 161 MB, versus 459 / 101 MB for the 2.3 runtime.
- Gaps: 17 missing libraries and 353 unresolved symbols. Hardest are `libslog2` (used by every ELF), plus libnfc / libcontext / libtrackpad_converter / a11y / libsensor needed by the core runtime libs (about 110 stubs), a few libc extras (inotify, msgserver, …) and libscreen session calls. Audio needs a new HAL (BB10 audio_manager is absent). GPU gralloc compatibility, libscreen enum skew and the NDK static linker are unverified.
- Next experiment: build stub libraries (toolchain available: `playbook/sdk` bbndk qcc / Psyden GCC 9.3), copy the runtime to a scratch directory, then run a link-only test (`DL_DEBUG=libs … app_process` usage only). No /apps or /system changes.
- Work files: scratchpad `bb10rt/` (session-only). Image reflink copies in `v3root/.bb10rt-ro/` (deletable).
- 02:16 Browser failed with "error 13". Log: `launcher: airfork() failed (Permission denied)`. The relaunched adl's `/dev/airfork` was root-owned with mode 600, but the launcher runs as uid 89 (`apps`). Fixed with `chown 89:0 /dev/airfork` (resource-manager node, non-persistent). If this is redone, add the chown to `tls-switch.sh` after `waitfor /dev/airfork`.
- 02:2x **The Browser launches again** after the `/dev/airfork` chown. It runs on the relaunched airfork, which maps OpenSSL 1.0.2u plus the refreshed CA folder. **Confirmed working (user test):** a previously working site plus https://en.wikipedia.org, https://github.com and https://www.google.com all load in the Browser. The TLS upgrade works.
- **Not persistent.** A reboot restores the stock 1.0.0e libs and certs. To re-apply after reboot + re-root: run `playbook/scripts/tls-switch.sh` (copy on device at `/accounts/devuser/tls-new/tls-switch.sh`) with `cd / && on -d /bin/sh /accounts/devuser/tls-new/tls-switch.sh <airfork PID> <airfork multilog PID>` while the Browser is closed. Get the PIDs from `pidin arg | grep -e "adl -runtime /base/air/runtimeSDK/ -airfork" -e "multilog t /var/log/airfork"`. The script now includes the `/dev/airfork` chown. Files stay staged in `/var/tls102/` (persistent).
- **Lesson:** before restarting any system resource manager, record its device node's owner and mode (`ls -la /dev/<node>`) so the replacement can match.

## Post-reboot routine (current)

1. Turn Dev Mode on (USB in Mac mode; `eject /dev/sr0` if the host shows CD-ROM mode).
2. Root: `python3 playbook/third-party/psyden/PlayBook-root-setup-V3.py --ip 169.254.0.1 --password password`
3. Android crash-loop fix: installer `Terminate`, then kill the orphaned zygote + system_server by exact PID (ppid 1, own process group), then skip `Launch`.
4. TLS upgrade: **automatic.** `root.sh` (run by step 2) now ends by calling `/accounts/devuser/tls-new/tls-switch.sh` (`on -d`, from `/`). The script finds the airfork and logger PIDs itself, aborts unless exactly one of each exists, does nothing if the overlay is already active, and logs to `/accounts/devuser/tls-new/switch.log`. **Keep the Browser closed while rooting.** Backups: `root.sh.pre-tls` on the device and in `playbook/device-backups/devuser-hardened/`.

## Cleanup

- 2026-10-20: all regenerable leftovers (analysis image copies, AutoRoot build folders, unpacked PlayBook images, about 33 GB) moved to `delete/` at the repo root. The user deletes it by hand.

## Reboot test (2026-10-03 ~02:30)

- After reboot and Dev Mode on, the root script failed at "Injecting modified start-android-core.sh" with "Path traversal failed". It aborted before writing anything.
- Likely cause (unconfirmed): step 6 (`android-perms-fix.sh`) restored official permissions, making that runtime script read-only (`chmod 555`). Before step 6 it was 777.
- Current state: device unrooted (no SSH), stock TLS active. Persistent changes remain: 20 apps removed, Chroma Doze installed, layout, `/var/tls102` staged files, hardened root-kit files.
- Rooting work stopped here at this point in the session.
