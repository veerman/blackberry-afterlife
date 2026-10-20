#!/usr/bin/env python3
"""Run bb10mt with a pty, answer the bootrom password prompt, and abort if the attempts counter ever drops (wrong password)."""
import os, pty, re, select, signal, sys, time

pw = os.environ["PB_PASSWORD"].encode() + b"\n"
log = open(sys.argv[1], "ab")
pid, fd = pty.fork()
if pid == 0:
    os.execvp(sys.argv[2], sys.argv[2:])
buf = b""; first = None
while True:
    try:
        r, _, _ = select.select([fd], [], [], 1)
        if not r:
            continue
        data = os.read(fd, 4096)
    except OSError:
        break
    if not data:
        break
    log.write(data); log.flush(); buf += data
    m = re.search(rb"Enter password \((\d+)/(\d+)\)", buf)
    if m:
        left = int(m.group(1))
        if first is None:
            first = left
        if left < first:
            log.write(f"\n!!! attempts dropped {first}->{left}: wrong password, aborting\n".encode()); log.flush()
            os.kill(pid, signal.SIGTERM); break
        os.write(fd, pw)
        buf = buf[m.end():]
_, status = os.waitpid(pid, 0)
log.write(f"\nEXIT {status}\n".encode()); log.flush()
