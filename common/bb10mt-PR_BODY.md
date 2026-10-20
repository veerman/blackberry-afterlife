## Summary

- Map `06002e0a` (BlackBerry Leap STR100-2) to `LDR_29` in `bb10mt.ini`. Without it, `info` and `flash` stop with `No valid loader found for 06002E0A`. The neighbouring `07002e0a` already uses `LDR_29`, and the probe results in `loaders.ini` record `LDR_29` working on `06002E0A`.
- Add `docs/LINUX.md`: flashing from Linux with no Windows involved.

## Tested

On a Leap STR100-2 (bootrom 5.47.0.3), from Arch Linux, with the release binary from `v3root.zip` plus this mapping:

- `bb10mt info`: hardware ID, MCT, OS 10.3.3.3216 and blocklists read correctly.
- `bb10mt flash` of the stock 10.3.3.3216 OS and radio, split from `Z30_10.3.3.3216_STA100.exe`: completed in about five minutes and booted.
- `bb10mt flash` of an AutoRoot v3 user image (`*.0.unsigned` from `root_v3.sh`) plus the stock radio: completed, booted to the home screen, root notification shown, SSH working.

## Related AutoRoot v3 issues (not in this repo)

These are in the `v3root.zip` toolkit, which I couldn't find in a public repo, so I'm listing them here.

1. **`chmod -R 777 "/apps"` in `patch.txt` breaks the Android runtime.** Android `init` skips world-writable config:

   ```
   init: skipping insecure file '/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/default.cfg'
   init: skipping insecure file '/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/init.cfg'
   init: skipping insecure file '/system/build.cfg'
   ```

   As a result zygote never starts. `shrimp` logs `Timed out waiting for .../data/apdata/system/qnx`, and `/pps/services/android/status` stays `initializing`. Every Android app hangs on its loading screen, and APK installs hang at "Initializing". getroot still succeeds, because it only needs the half-started runtime.

   Fix: add these lines after the `chmod -R 777`. With them in place, Android reports `running` and APKs install and run:

   ```
   chmod 644 "/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/default.cfg"
   chmod 644 "/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/init.cfg"
   chmod 644 "/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/autolaunch.cfg"
   chmod 644 "/apps/sys.android.gYABgKAOw1czN6neiAT72SGO.ns/native/system/build.cfg"
   ```

2. **The blog post says `use.ssh`, but `btool` checks `use.sshd`.** `patch.txt` already uses the right name.
3. **SSH from current OpenSSH clients.** `OpenSSH_6.2 QNX_Secure_Shell` drops the connection when AES-GCM is negotiated. `Ciphers aes128-ctr` plus `HostKeyAlgorithms/PubkeyAcceptedAlgorithms +ssh-rsa` works, with `scp -O` for copies. It may be worth noting that the bundled `ssh_host_rsa_key` is public, so users should generate their own.

Thanks for bb10mt. It made Linux flashing possible.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
