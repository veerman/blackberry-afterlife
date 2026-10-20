# BlackBerry Afterlife: PlayBook and Leap on Linux, in 2026

BlackBerry shut down its servers on 4 January 2022. Anything with a cloud dependency stopped working: app stores, setup wizards, BlackBerry ID, news and weather apps. The hardware is still good. This repo is a research and tinkering log for two of these devices: getting them flashed, rooted and useful again **from Linux only**, removing the dead apps, and modernizing what can be modernized.

| Device | OS | What we did | Details |
| --- | --- | --- | --- |
| **BlackBerry PlayBook** (2011 tablet, Wi-Fi 32 GB) | Tablet OS 2.1.0.1917 (QNX) | Flashed and rooted from Linux, fixed the root image's security holes, removed 20 dead apps, upgraded the Browser's TLS library so modern HTTPS sites load, started porting a modern WebKit | [playbook/](playbook/README.md) |
| **BlackBerry Leap** STR100-2 (2015 phone) | BB10 10.3.3.3216 (QNX) | Flashed stock firmware from Linux (earlier public research said this bricks the phone), rooted with a debloated, setup-skipping image, fixed an AutoRoot bug that broke all Android apps | [leap/](leap/README.md) |

## What works on each device

| | PlayBook | Leap |
| --- | --- | --- |
| Flash from Linux with `bb10mt` | Yes | Yes |
| Root | Yes, tethered: re-run after every reboot | Yes, persistent |
| Dead cloud apps removed | 20 apps (App World, Bridge, PressReader, Weather…) | Done by the AutoRoot image |
| Built-in browser on modern HTTPS sites | Yes, with our OpenSSL 1.0.2u build. Lost at each reboot, re-applied by the root script | Not needed: Firefox runs |
| Android runtime | **2.3.3** (API 10), and **pure-Java apps only**: any APK with native `.so` libraries fails | **4.3** (API 18), native ARMv7 code works |
| Android apps confirmed working | Chroma Doze 3.7.1 (white noise) | Firefox 68, VLC 3.7.1, Open Camera 1.53.1, Chroma Doze 4.4 |

## No Windows at any step

BlackBerry's only official flasher is `cap.exe`, a Windows program. Every firmware download ("autoloader") is a `.exe`: that program with the firmware images appended. **We never run it.** Our `common/al_inspect.py` (or `bb10mt split`) cuts the images out of the `.exe` on Linux, and the open-source [bb10mt](https://github.com/bb10root/bb10mt) flashes them over USB.

- **PlayBook:** Psyden's guides already included Linux bb10mt instructions. We confirmed they work and documented the missing pieces: the key format the tablet accepts, Development Mode switching off at each reboot, and why the "Signature send error" is harmless.
- **Leap:** here the outcome was genuinely uncertain. The most detailed public research ([stanw47](https://github.com/stanw47/Blackberry-Research)) saw bb10mt flashes end in a "red-blink" brick and concluded the Windows tool was indispensable. bb10mt also didn't know the Leap's hardware ID. We added the ID and worked out the plug-in order. We also found the red-blink cases came from modified OS images. Signed stock firmware, and an AutoRoot image that changes only the user partition, both flashed and booted from Linux. As far as we could find, this hadn't been documented before.

## Where the two devices overlap

Both run QNX and share BlackBerry's flashing protocol, so these parts are common:

- **The flasher.** Both are flashed with [bb10mt](https://github.com/bb10root/bb10mt), using the same Linux setup (udev rule, libfuse2) and the same "start the listener first, then plug in" trick to catch the bootloader. See [common/](common/).
- **Firmware formats.** Both use the same autoloader and `.signed` image layout (`common/al_inspect.py` reads them).
- **Android runtimes.** We analysed whether the Leap's Android 4.3 runtime could run on the PlayBook. The verdict: a long shot (17 missing libraries, 353 unresolved symbols). Scripts are in `playbook/analysis/bb10rt/`.

Everything else is device-specific, which is why each device has its own folder.

## Layout

```
common/      shared: bb10mt Leap patch + upstream PR text, udev rule, autoloader splitter
leap/        README, AutoRoot v3 fix (patch), full flashing write-up in notes/
playbook/    README, scripts, root-kit hardening patch, OpenSSL build, WebKit port patches,
             analysis scripts, write-ups in notes/
```

The repo holds only our own work. Firmware, toolkits, SDKs and anything else large or third-party is listed in `.gitignore`, and each device README says where to download it and how to rebuild everything we built.

## Ground rules we followed

- **Linux only.** No Windows, VM or Wine at any step.
- **Check hashes** of every download against the values in the READMEs.
- **Flashing wipes the device.** Both devices stayed recoverable throughout: the bootloader sits below the OS and can always be reflashed.

## License and disclaimer

Our own scripts and write-ups are under the [MIT License](LICENSE). Patches to other projects carry those projects' licenses: `common/bb10mt-leap-support.patch` is GPL-3.0 like bb10mt, and `playbook/webkit/patches/` follow WebKit's LGPL-2.1/BSD licenses.

This repo contains no BlackBerry firmware or software. It is an independent hobby project, not affiliated with or endorsed by BlackBerry Limited. "BlackBerry", "PlayBook" and "Leap" are its trademarks, used here only to name the devices. Flashing and rooting erase your device and can leave it unusable. You do this at your own risk.

## Credits

- [bb10mt](https://github.com/bb10root/bb10mt) and AutoRoot v3 by the [bb10.root.sx](https://bb10.root.sx) team.
- PlayBook root image, root scripts and GCC 9.3 toolchain by [Psyden](https://archive.org/details/PlayBook-ROOT-patch) ([toolchain](https://github.com/Psyden57/BB-PlayBook-gcc-9.3.0)).
- [stanw47/Blackberry-Research](https://github.com/stanw47/Blackberry-Research) for earlier BB10 flashing research.
- Firmware archived by the Internet Archive community.
