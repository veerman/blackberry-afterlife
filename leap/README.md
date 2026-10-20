# BlackBerry Leap (STR100-2) from Linux

**Result:** stock BB10 10.3.3.3216 flashed from Linux, then a rooted image that skips the dead setup wizard and removes bloat. Android 4.3 apps such as Firefox and VLC run.

The full write-up, with every finding, is [notes/flashing-bb10-from-linux.md](notes/flashing-bb10-from-linux.md). This page is the short version.

## Key findings

- **bb10mt can flash a Leap from Linux.** It needed one config line for the Leap's hardware ID (`06002e0a=LDR_29`). That change is [../common/bb10mt-leap-support.patch](../common/bb10mt-leap-support.patch), written up as an upstream PR in `../common/bb10mt-PR_BODY.md`.
- **Signed stock firmware flashes fine.** Earlier public reports of "red-blink" bricks involved modified OS images, not stock.
- **Catch the bootloader listener-first.** Start `bb10mt`, unplug the phone, power it off fully, then plug it back in. In OS mode (USB `0fca:8014`) bb10mt can't reboot the phone itself.
- **AutoRoot v3 breaks every Android app.** Its `chmod -R 777 /apps` makes Android `init` skip its config files, so zygote never starts. Our fix adds four `chmod 644` lines: [autoroot-v3-patch.txt.diff](autoroot-v3-patch.txt.diff). The diff also turns on SSH with your own key.
- **SSH quirks:** the flag file is `use.sshd` (the guide's `use.ssh` is a typo). QNX's OpenSSH 6.2 needs `Ciphers aes128-ctr`, and `scp` needs `-O`.

## Apps

The Android runtime is 4.3 (API 18, `armeabi-v7a`). Install APKs by tapping them in File Manager; command-line installs are refused.

| App | Version | Download |
| --- | --- | --- |
| Firefox (Fennec F-Droid) | 68.12.0, the last for Android 4.x | [F-Droid archive](https://f-droid.org/archive/org.mozilla.fennec_fdroid_689400.apk) |
| VLC | 3.7.1 | [F-Droid](https://f-droid.org/en/packages/org.videolan.vlc/) |
| Open Camera | 1.53.1 | [F-Droid archive](https://f-droid.org/archive/net.sourceforge.opencamera_90.apk) |
| Chroma Doze (white noise) | 4.4 | [F-Droid](https://f-droid.org/en/packages/net.pmarks.chromadoze/) |

Signal can't work: it needs Android 6+.

## Reproduce it

Download these into this folder (they are git-ignored):

| What | Put it in | From | Check |
| --- | --- | --- | --- |
| Stock autoloader `Z30_10.3.3.3216_STA100.exe` (3.07 GB, shared by Z30, Classic and Leap) | `firmware/` | [Internet Archive](https://archive.org/details/z30-10333216-sta100) | MD5 `497e5a918a214c09f944fb921d3c8c19` |
| `v3root.zip` (bb10mt binary, loaders, AutoRoot v3 scripts) | unzip to `v3root/` | [bb10.root.sx](https://bb10.root.sx/blog/pre-rooted-autoloaders-v3) | see the write-up |

Then:

1. **Host setup:** `sudo pacman -S fuse2 libusb` (Debian/Ubuntu: `libfuse2`), and copy [../common/51-blackberry.rules](../common/51-blackberry.rules) to `/etc/udev/rules.d/`.
2. **Add the Leap** to `v3root/bb10mt.ini`: `06002e0a=LDR_29`.
3. **Split the autoloader:** `python3 common/al_inspect.py leap/firmware/Z30_10.3.3.3216_STA100.exe leap/firmware/stock`.
4. **Stock flash:** from `leap/v3root`, run `./bb10mt flash -i ../firmware/stock/Z30_10.3.3.3216_STA100.0.signed,../firmware/stock/Z30_10.3.3.3216_STA100.1.signed`, catching the phone listener-first.
5. **Rooted image:** in `leap/v3root`, apply our fix with `patch patch.txt < ../autoroot-v3-patch.txt.diff`. To use SSH, put your own keys in `patchdata/var/etc/ssh/`; otherwise drop the SSH lines. Then build with `./root_v3.sh ../firmware/Z30_10.3.3.3216_STA100.exe work` and flash `work/*.0.unsigned` together with the stock radio `.1.signed`.

**Already built:** `firmware/rooted-ssh/Z30_10.3.3.3216_STA100.0.unsigned` is the rooted image with SSH that's on our phone. Flash it with the stock radio to restore that state without rebuilding.

Step-by-step details, expected hashes and troubleshooting are in the [full write-up](notes/flashing-bb10-from-linux.md). `notes/work2-build.log` is a log of a successful image build, for comparison.
