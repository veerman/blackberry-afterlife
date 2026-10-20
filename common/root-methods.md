# Root Methods

How we root each device, why the methods differ, and what that difference suggests for the future. For how to flash and what root gets you, see the [PlayBook](../playbook/README.md) and [Leap](../leap/README.md) READMEs.

On comparing root methods between PlayBook and Leap, it isn't about which OS is more polished. It's about whether the OS will run something from the writable part of the device when it boots. BB10 does; the PlayBook's OS doesn't.

Both devices have two kinds of storage: system partitions, which are signed by BlackBerry and you can't change, and a user partition (apps, settings), which you can. Both root kits only change the user partition. What differs is what the OS does with it at boot.

## Leap (BB10): a boot hook

BB10 added a boot-time startup list, `/var/etc/autostart.conf`, and it lives on the user partition. AutoRoot writes one line there pointing at its root installer, so the root helper starts on every boot with nothing plugged in. `autostart.conf` is a legitimate feature of the newer OS; AutoRoot just turns it into a permanent way back in.

## PlayBook (Tablet OS 2.1): no boot hook, so break in live

On the PlayBook, everything that runs at boot lives on the signed partitions, so there's no boot hook to plant root in. Psyden's script has to break in live every time:

1. It uses a path-traversal bug in the Development Mode web service to overwrite the Android runtime's startup script.
2. It starts the Android runtime, which runs that script as root.
3. It links the root kit into place with a link that lives only in memory.
4. It puts the original script back.
5. A reboot wipes the link, and Development Mode switches itself off, so you start again.

## The two roots are close relatives

Both hijack the same file, the Android runtime's `start-android-core.sh`, and Psyden credits the AutoRoot team for the trick. The difference is that on the Leap, BB10's boot list runs the hijacked file automatically.

## A lead for persistent root on the PlayBook

This also suggests a lead for persistent root on the PlayBook. That startup script sits on the user partition and runs as root whenever the Android runtime starts. Psyden deliberately restores the original. If the modified version were left in place, opening any Android app (like Chroma Doze) might root the tablet with no laptop and no Development Mode. If it breaks, the fix is rewriting one file, not a reflash.

**Untested — this is my reading of the scripts.** The open question is *why* Psyden restores the original script. If it's only cleanup, the lead holds. If the runtime won't start, or normal Android use breaks, with the modified script in place, that would kill it.
