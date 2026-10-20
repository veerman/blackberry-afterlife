# Shared by both devices

| File | What |
| --- | --- |
| `51-blackberry.rules` | udev rule so a normal user can reach BlackBerry USB devices (vendor `0fca`). Copy to `/etc/udev/rules.d/`, then `sudo udevadm control --reload`. |
| `al_inspect.py` | Read-only splitter for BlackBerry autoloader `.exe` files: finds the end of the Windows `cap.exe` stub and writes out each `.signed` payload. `python3 al_inspect.py <autoloader.exe> <out-dir>` |
| `bb10mt-leap-support.patch` | Our change to [bb10mt](https://github.com/bb10root/bb10mt): maps the Leap's hardware ID `06002e0a` to `LDR_29`, and adds `docs/LINUX.md`. Apply with `git am` on a clone of bb10mt. |
| `bb10mt-PR_BODY.md` | Write-up of that change for an upstream pull request. |

## Catching the bootloader (both devices)

bb10mt has to be listening before the device's bootrom appears, because the bootrom only waits a few seconds:

1. Start the bb10mt command (`info` or `flash`).
2. Unplug the device and power it off fully.
3. Plug it back in while it is off. It shows up as USB `0fca:0001`, and bb10mt connects.

The PlayBook's ID (`06001a06`) is already in bb10mt's loader table. The Leap's isn't until you apply the patch above.
