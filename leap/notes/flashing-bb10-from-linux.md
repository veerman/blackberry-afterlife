# Flashing Stock BB10 Firmware from Linux

Oct 2, 2026 · @Steve

> Local copy of the Claude Doc https://claude.ai/code/artifact/bc4357ac-feed-4169-8f6e-e7811c43af5e

## Summary

On 2 October 2026 we flashed official BlackBerry OS 10.3.3.3216 (OS and radio) to a BlackBerry Leap STR100-2 entirely from Linux, with no Windows, VM or Wine. The flash took about 5 minutes, the phone accepted both signed images and booted to the first-run setup screen. Twenty minutes later we flashed an AutoRoot v3 user image the same way, and the phone booted straight to the home screen: setup skipped, no BlackBerry ID, rooted.

The tool is [bb10mt](https://github.com/bb10root/bb10mt), an open-source BlackBerry 10 multitool that already speaks the phone's bootloader protocol over libusb. It needed one config line it was missing (the Leap's hardware ID) and a specific order of steps to catch the bootloader.

This matters because the only official flasher, `cap.exe` inside every autoloader, is Windows-only, and the most detailed public research had concluded that bb10mt flashes end in a red-blink brick. Neither of our cases hit that: genuine signed stock firmware and a modified user-partition image both flashed and booted from Linux. The red-blink reports involved modified system (OS) images.

## What you need

A BB10 phone, a USB data cable, a Linux PC (tested on Arch-based Omarchy, x86-64) and the files below.

| Item | Where | Check |
| --- | --- | --- |
| Stock autoloader `Z30_10.3.3.3216_STA100.exe` (3,073,914,372 B; one file for Z30, Classic/Q20 and Leap) | [Internet Archive](https://archive.org/details/z30-10333216-sta100) | MD5 `497e5a918a214c09f944fb921d3c8c19` |
| `bb10mt` Linux binary + `loaders.dat` + `bb10mt.ini` | `v3root.zip` from [bb10.root.sx](https://bb10.root.sx/blog/pre-rooted-autoloaders-v3); source at [github.com/bb10root/bb10mt](https://github.com/bb10root/bb10mt) | bb10mt SHA-256 `4d6d7406…aae57bc`, loaders.dat `37e34cb6…e907f9` |
| libusb 1.0 | distro package (`libusb`) | usually already installed |
| libfuse 2 (`libfuse.so.2`) | `sudo pacman -S fuse2` (Debian/Ubuntu: `libfuse2`) | bb10mt will not start without it |
| `al_inspect.py` (our splitter, plain Python 3) | `common/` in this repo | read-only on the input |

After splitting, the two payloads should hash to:

- OS `…STA100.0.signed` (3,010,003,896 B): SHA-256 `c91f679b615b3c28c097bbd427fa0f9805642972655c91c42749817ef3231e7c`
- Radio `…STA100.1.signed` (54,657,856 B): SHA-256 `9af6da88fb44d0c454d29ba871af94b9f2459c578743587e462e1eff5050f1cb`

## Procedure

The whole flash wipes the phone. Back up first, and do the checks in [After flashing](#after-flashing) before you start.

1. **Download and verify the autoloader.** `md5sum Z30_10.3.3.3216_STA100.exe` must print `497e5a918a214c09f944fb921d3c8c19`.
2. **Unpack the toolkit** and make it runnable: `unzip v3root.zip -d leap/v3root && chmod +x leap/v3root/bb10mt`.
3. **Install libfuse 2:** `sudo pacman -S fuse2`. Check with `ldd leap/v3root/bb10mt | grep 'not found'` (no output = good).
4. **Allow your user to talk to BlackBerry USB devices:**

   ```
   echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="0fca", MODE="0660", TAG+="uaccess"' | sudo tee /etc/udev/rules.d/51-blackberry.rules
   sudo udevadm control --reload && sudo udevadm trigger
   ```
5. **Add your phone's hardware ID to `bb10mt.ini`** if it is missing. For the Leap STR100-2 add `06002e0a=LDR_29` under `[Loaders]` (next to `07002e0a=LDR_29`). Other devices: run step 7 first; the error `No valid loader found for <ID>` gives the ID, and `loaders.ini` may already record a loader that worked for it.
6. **Split the autoloader into its two payloads.** Either `./bb10mt split -i ../firmware/Z30_10.3.3.3216_STA100.exe -o ../firmware/stock/` or our `python3 common/al_inspect.py leap/firmware/Z30_10.3.3.3216_STA100.exe leap/firmware/stock`. Confirm the SHA-256 values in [What you need](#what-you-need). Payload 0 is the OS, payload 1 the radio.
7. **Read-only test (writes nothing):** start `./bb10mt info` first, then catch the bootloader (step 8). It loads the RAM loader, prints the hardware ID, bootloader version, partition map and installed OS, then reboots the phone normally.
8. **Catch the bootloader ("listener first").** With bb10mt already running and waiting: unplug the phone, power it fully off (hold power 10–15 s if it restarts on its own), then plug it back in while off; tap power if nothing happens. The bootloader appears as `0fca:0001` for a moment and bb10mt grabs it.
9. **Flash:** start the command below, then repeat step 8.

   ```
   ./bb10mt flash -i ../firmware/stock/Z30_10.3.3.3216_STA100.0.signed,../firmware/stock/Z30_10.3.3.3216_STA100.1.signed
   ```

   Expected output: `BlackBerry Leap STR100-2 (06002E0A)` → `loader: LDR_29` → `Flashing 2 files...` → progress to 100% → `Send signature` / `Done` for each file → `Flash completed successfully!`. Don't unplug until it finishes.
10. **Confirm it booted.** About a minute later `lsusb` should show `0fca:8017` (OS running) and the phone shows "Welcome to BlackBerry". A red blinking LED instead means the OS was not accepted (see [Troubleshooting](#troubleshooting-and-safety)).

## What we learned

The Linux path was blocked by a handful of small, mostly undocumented facts rather than by anything fundamental.

| Finding | Why it mattered | Previously known? |
| --- | --- | --- |
| **Genuine stock firmware flashes fine through bb10mt.** Both payloads end in a real 560-byte `QNXH-OS-1` signature seal; bb10mt strips it and sends it with the `F9 40` SIGNATURE\_TRAILER command, just as `cap.exe` does. | The public red-blink failures ([stanw47 research, finding 11–12](https://github.com/stanw47/Blackberry-Research)) used *pre-rooted* payloads whose tail was 560 zero bytes, so bb10mt sent a fake seal. Stock firmware never hits that case. | No — notes concluded "the Windows stub is indispensable" |
| **The Leap STR100-2 is hardware ID `0x06002E0A` and uses RAM loader `LDR_29`.** | bb10mt's `bb10mt.ini` (upstream too) lists `07002e0a` but not `06002e0a`, so it stops with `No valid loader found`. `loaders.ini` (a probe log) already recorded `LDR_29` working on `06002E0A`. | Partly — in a probe log, never in the lookup table |
| **Listener first.** The bootloader only exposes its flash interface (`0fca:0001`) for a moment at power-on, and only if a host is already polling. | Starting bb10mt after the phone boots does nothing. | Known to researchers, not in any how-to |
| **A booted phone in USB mass-storage mode (`0fca:8014`) can't be rebooted into the bootloader.** It exposes only a SCSI storage interface, which Linux's `usb-storage` claims. | bb10mt waits forever on "Connecting to BootROM...". Fix: power the phone off and catch it on power-up. | No |
| **An aborted bootloader session leaves the phone stuck at `0fca:0001`**; a fresh power cycle clears it. | A second run right after a failed one silently does nothing. | No |
| **Official autoloaders carry 0x70 extra bytes** between the end of the `cap.exe` PE image and the payload table (signature `0x97C5D59C` ×3). Community-built autoloaders don't. | A parser that assumes the table starts at the PE end reads garbage. Search for the signature instead. | No |
| **One 10.3.3.3216 autoloader covers Z30, Classic/Q20 and Leap.** | No file named "STR100-2" exists; the Z30 file is the right one. | Known on forums |
| **bb10mt needs `libfuse.so.2`** (FUSE 2, not 3). | Fails at start with a missing-library error on modern distros. | No |

**Modified user-partition images also flash from Linux.** The AutoRoot v3 build replaces only the user filesystem (`.ufs`, packed by `bb10mt pack -s` with a placeholder `QNXH-OS-1` seal) and leaves the signed OS untouched. bb10mt sent it, the phone accepted it and booted. This was previously assumed to need the Windows `cap.exe`.

On our phone the bootloader reported version 5.47.0.3, a blocklist of everything below OS 10.3.3.1, and a 16 GB Samsung eMMC (`AGND3R`) with the standard dual-slot OS/radio layout.

## After flashing

A freshly flashed phone starts the setup wizard, which expects BlackBerry's servers (shut down 4 January 2022) and stalls at the Wi-Fi / BlackBerry ID screens. That is a stuck wizard, not a lockout: the bootloader sits below it and can always be reflashed.

**Before flashing, check Anti-Theft.** Settings → About (General) shows *BlackBerry ID: No information available* when no ID is signed in; Anti-Theft cannot be on without one. With an ID and Protect on, the in-OS Security Wipe can't verify the password; forum reports say an autoloader flash still goes around it, but we did not test that case.

**Getting through setup** (the [screen-reader trick](https://forums.crackberry.com/blackberry-10-os-f269/fix-bb10-devices-stuck-setup-sideloading-issue-1193846/)):

1. On "Connect to a Mobile Network", press power three times quickly to start Screen Reader; double-tap with two fingers to confirm.
2. Tap then double-tap **Skip**.
3. On the Wi-Fi screen the reader announces BlackBerry ID. When it says "Skip", double-tap at top left just under "Connect to Wi-Fi".
4. Skip BlackBerry ID creation, then turn Screen Reader off (power ×3) and tap Skip on the sign-in screen.
5. If Software Update appears, wait for it to fail and **swipe left**; don't go back to Wi-Fi. Finish the gesture tutorials.

**Easier alternative, what we ended up using:** if the screen-reader trick won't cooperate, skip setup entirely with AutoRoot v3. Its `patch.txt` sets `autorun::1` to `autorun::0`, marks the tutorials done, removes bloat apps and installs Term49 plus the root helper (SSH and app-level root stay off by default). The phone must already run stock 10.3.3.3216. Add the four `chmod 644` lines from fix 1 under "AutoRoot v3 bugs and fixes" to `patch.txt` first, or no Android app will run.

1. Build: `cd leap/v3root && ./root_v3.sh ../firmware/Z30_10.3.3.3216_STA100.exe work` (all local, a few minutes). Check the flags landed: `grep -c -a -F 'autorun::0' work/*.ufs` should print 1.
2. Flash the user image, then the stock radio, in one session (listener first, as in step 8):

   ```
   ./bb10mt flash -i work/Z30_10.3.3.3216_STA100.0.unsigned,../firmware/stock/Z30_10.3.3.3216_STA100.1.signed
   ```
3. The phone boots to the home screen. First boot is slow while the root installer and Term49 set themselves up. About a minute after the home screen appears, a "root" notification says "Congratulations! The device has been successfully rooted!": that's the success signal.

The `.exe` autoloaders the script also writes are for Windows; on Linux you flash the `.unsigned` and `.signed` files directly.

## AutoRoot v3 bugs and fixes (for the developers)

Four problems turned up after the AutoRoot v3 flash; all are fixed on our phone and in our copy of the toolkit. Items 1 and 2 belong upstream with [bb10root](https://bb10.root.sx/blog/pre-rooted-autoloaders-v3), item 3 with [bb10mt](https://github.com/bb10root/bb10mt).

1. **`chmod -R 777 "/apps"` in `patch.txt` breaks the Android runtime.** It makes the Android player's config files world-writable, and Android `init` refuses them:

   ```
   init: skipping insecure file '/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/default.cfg'
   init: skipping insecure file '/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/init.cfg'
   init: skipping insecure file '/system/build.cfg'
   ```

   Symptoms: zygote (`app_process`) never starts; `shrimp` logs *"Timed out waiting for …/data/apdata/system/qnx … Android failed to launch"*; `/pps/services/android/status` stays `state::initializing`; every Android app hangs on its loading screen and tapping an APK hangs at "Initializing". The root step itself still reports success, because getroot only needs the half-started runtime.

   Fix in `patch.txt`, right after `chmod -R 777 "/apps"`:

   ```
   chmod 644 "/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/default.cfg"
   chmod 644 "/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/init.cfg"
   chmod 644 "/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/autolaunch.cfg"
   chmod 644 "/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/system/build.cfg"
   ```

   On an already-flashed phone: run the same `chmod 644` over SSH, kill the Android processes, and start it again by writing `msg::start` / `dat::sys.android.gYABgKAOw1czN6neiAT72SGO.ns,ORIENTATION=0` / `id::x` to `/pps/services/launcher/control`. Status then reads `state::running` and apps work.
2. **The guide says `use.ssh`; the boot script checks `use.sshd`.** Following the guide literally leaves SSH off. `patch.txt` has the right name.
3. **`bb10mt.ini` lacks the Leap STR100-2.** Add `06002e0a=LDR_29` under `[Loaders]`.
4. **SSH from a modern Linux client needs old settings.** The phone runs `OpenSSH_6.2 QNX_Secure_Shell-20130711`, which drops the connection when the client picks AES-GCM. Use this `~/.ssh/config` entry, and `scp -O` for file copies:

   ```
   Host bb10
       HostName 169.254.0.1
       User root
       IdentityFile ~/.ssh/bb10_leap
       HostKeyAlgorithms +ssh-rsa
       PubkeyAcceptedAlgorithms +ssh-rsa
       Ciphers aes128-ctr,aes256-ctr
       MACs hmac-sha1,hmac-sha2-256
   ```

   The toolkit ships the author's public key in `authorized_keys2` and a host key whose private half is public. Generate your own of both (RSA; the old server has no Ed25519) before enabling SSH.

## Apps that work

The runtime is Android 4.3 (API 18, `armeabi-v7a`), confirmed from the phone's `build.prop`. APKs install by tapping them in File Manager; the phone converts them itself. Command-line installs through the installer queue are refused for plain APKs (error 532 from Downloads, `500 'Package-Id'` for an unpacked APK), so copy over SSH and tap. All four below installed and ran on 2 October 2026.

| App | Version | Source |
| --- | --- | --- |
| Firefox (Fennec F-Droid) | 68.12.0, last for Android 4.x; own NSS certificates and TLS 1.3 | [F-Droid archive](https://f-droid.org/archive/org.mozilla.fennec_fdroid_689400.apk) |
| VLC | 3.7.1 (still supports Android 4.2+) | [F-Droid](https://f-droid.org/en/packages/org.videolan.vlc/) |
| Open Camera | 1.53.1, last for Android 4.x | [F-Droid archive](https://f-droid.org/archive/net.sourceforge.opencamera_90.apk) |
| Chroma Doze (white noise) | 4.4 | [F-Droid](https://f-droid.org/en/packages/net.pmarks.chromadoze/) |

Signal is not possible: it needs Android 6.0+ and its servers reject expired clients.

## Troubleshooting and safety

| Symptom | Cause | Fix |
| --- | --- | --- |
| `error while loading shared libraries: libfuse.so.2` | FUSE 2 missing | Install `fuse2` / `libfuse2` |
| Hangs on "Connecting to BootROM...", phone keeps running | Phone booted in mass-storage mode (`0fca:8014`) | Start bb10mt, then power the phone off and plug it in while off |
| `No valid loader found for XXXXXXXX` | Hardware ID not in `bb10mt.ini` | Add `xxxxxxxx=LDR_NN`; check `loaders.ini` for a probed match |
| Prints only "Connecting to BootROM..." and exits | Bootloader stuck from an aborted session | Unplug, hold power 10–15 s, catch it again |
| Phone boots OS right after unplugging | Normal: no host listening, so the bootloader continues | Nothing to fix |
| Red blinking LED after flashing | OS image not accepted (seen with modified images) | Reflash stock; the bootloader stays reachable |

**Don't:**

- Run `bb10mt nuke` or other write commands you haven't read the source of.
- Guess the device password at the bootloader prompt: failed tries count toward the 10-attempt wipe.
- Unplug during `Flashing:`.
- Write to `boot0`/`boot1` or eMMC control registers. That is how the research Passport was permanently bricked; normal flashing never touches them.
- Flash modified OS (system) images from Linux expecting success: only stock OS images and a modified user-partition image have been tested here.

## References and credits

- [bb10mt source](https://github.com/bb10root/bb10mt) and the [AutoRoot v3 toolkit](https://bb10.root.sx/blog/pre-rooted-autoloaders-v3) by bb10root: the flasher that made this possible.
- [stanw47/Blackberry-Research](https://github.com/stanw47/Blackberry-Research): autoloader format, RAM-loader command list, the 560-byte seal finding, and listener-first entry.
- [Z30 / Classic / Leap 10.3.3.3216 autoloader](https://archive.org/details/z30-10333216-sta100) and [BlackBerry 10 Autoloaders collection](https://archive.org/details/blackberry10-autoloaders) on the Internet Archive.
- [CrackBerry: BB10 stuck at setup fix](https://forums.crackberry.com/blackberry-10-os-f269/fix-bb10-devices-stuck-setup-sideloading-issue-1193846/) and [Factory reset after 2022 with BB Protect](https://forums.crackberry.com/blackberry-10-os-f269/factory-reset-blackberry-after-2022-active-bb-protect-1194804/).
- [michioxd: skip initial setup in BB QNX](https://blog.michioxd.ch/blog/02-how-to-completely-skip-initial-setup-in-bbqnx/).
- [Sachesi](https://github.com/xsacha/Sachesi): older open-source BB10 tool with Linux USB support.
