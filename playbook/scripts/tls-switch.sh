#!/bin/sh
# Switch the AIR runtime (Browser) to OpenSSL 1.0.2u + refreshed CA store.
# Process-manager links only (ln -sP): nothing on disk changes, a reboot reverts everything.
# Run automatically from /accounts/devuser/root.sh after each re-root; safe to run by hand too.
# Idempotent: does nothing if the overlay is already active.
exec >> /accounts/devuser/tls-new/switch.log 2>&1
echo "=== tls-switch $(date)"
export PATH=/base/bin:/base/usr/bin:/base/sbin:/base/usr/sbin:/proc/boot
cd /

if ls -la /base/usr/lib/libssl.so.2 | grep -q /var/tls102; then
    echo "overlay already active, nothing to do"
    exit 0
fi
for f in /var/tls102/libssl.so.2 /var/tls102/libcrypto.so.2 /var/tls102/certs/a94d09e5.0; do
    [ -e $f ] || { echo "ABORT: missing $f"; exit 1; }
done

# find exactly one AIR fork server and its logger
AF=$(pidin arg | grep '^ *[0-9]* adl -runtime /base/air/runtimeSDK/ -airfork$' | awk '{print $1}')
ML=$(pidin arg | grep '^ *[0-9]* multilog t /var/log/airfork$' | awk '{print $1}')
set -- $AF; [ $# -eq 1 ] || { echo "ABORT: expected 1 airfork, found: '$AF'"; exit 1; }
set -- $ML; [ $# -eq 1 ] || { echo "ABORT: expected 1 airfork logger, found: '$ML'"; exit 1; }
echo "airfork=$AF logger=$ML"
ls -la /dev/airfork

set -x
ln -sPf /var/tls102/libssl.so.2    /base/usr/lib/libssl.so.2
ln -sPf /var/tls102/libcrypto.so.2 /base/usr/lib/libcrypto.so.2
ln -sPf /var/tls102/certs          /var/certmgr/web/user_trusted

# stop exactly the AIR fork server and its logger, nothing else
kill $AF $ML
sleep 2

# relaunch with the exact boot command and boot environment (from /scripts/startup.sh SERVICE_adl)
env -i _=/base/bin/on PATH=/base/bin:/base/usr/bin:/base/sbin:/base/usr/sbin:/base/usr/photon/bin:/base/scripts:/radio/bin:/radio/usr/bin:/radio/sbin:/radio/usr/sbin:/radio/scripts:/proc/boot:/base/bin:/base/sbin:/base/usr/bin:/base/usr/sbin:/base/opt/bin:/base/usr/sbin RTC_CLOCK_TYPE= FLASH_FONT_CFG_PATH=/etc/system/config/flash-font.cfg HMI_REMOTE=FALSE GRAPHICS_ROOT=/usr/lib/graphics/omap4430 TERM=ansi MM_INIT=/base/lib/dll/mmedia CPU=armle-v7 PERSISTENCE_DATA=/ LOGDIR=/var/log LIBIMG_CFGFILE=/etc/system/config/img.conf BOARD=winchester LD_LIBRARY_PATH=/base/usr/lib:/base/lib/dll:/base/lib:/base/lib/dll/font:/base/usr/photon/lib:/radio/usr/lib:/radio/lib/dll:/radio/lib:/proc/boot:/base/lib:/base/usr/lib:/base/lib/dll:/base/opt/lib BASEFS=/base uname_m=OMAP4430_ES2.2_HS_Winchester_Rev:07 BOARD_CONFIG=factory_sfi BOARDFILE=/base/board.tdf DECKARD_DEBUG=0 BOOT_LOADER=RIMBOOT LOCFILE=/usr/share/locale/locale.file FONTCONFIG_FILE=/etc/fontconfig/fonts.conf SYSNAME=nto ROOTFS=/ PHFONT=/dev/phfont TMPDIR=/var/tmp PHKSCOPE=1 HMI_VOLUME_SCALE=50 RTC_OPTS= LANG=C PHOTON=/dev/photon FLASHTMP=/tmp MIN_VALID_DATE_SEC=1241136000 HOME=/var DECKARD_DEBUG_SCRIPT=0 RADIOFS=/radio RTC_CLOCK_OPTS= DISK_ALIMIT=65536 BOOT_START_TIME=1790989998 MIN_VALID_DATE=200905010000.00 PPSDIR=/pps /bin/sh -c 'on -d -p 12 softlimit -w 970 adl -runtime /base/air/runtimeSDK/ -airfork 2>&1 | on -d -u logger multilog t /var/log/airfork' &
waitfor /dev/airfork 60
# the launcher (uid 89 "apps") must be able to reach the fork server, or apps fail with error 13
chown 89:0 /dev/airfork
ls -la /dev/airfork
sleep 2
pidin arg | grep -e 'adl -runtime' -e 'multilog t /var/log/airfork' -e launcher-secure -e sys.navigator
set +x
echo "=== done $(date)"
