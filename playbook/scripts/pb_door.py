#!/usr/bin/env python3
"""Hold the PlayBook's Development Mode door (QCONN, port 4455) open so devuser SSH stays up.

Reuses QCONNDoor from Psyden's BerryShell-V2.py; uploads ~/.ssh/playbook.pub and heartbeats until killed.
"""
import importlib.util, os, signal, sys, time

here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("berryshell", os.path.join(here, "..", "third-party", "psyden", "BerryShell-V2.py"))
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)
bs.ID_RSA_PUB_FILE = os.path.expanduser("~/.ssh/playbook.pub")

ip = os.environ.get("PB_IP", "169.254.0.1")
password = os.environ.get("PB_PASSWORD") or sys.exit("set PB_PASSWORD")

door = bs.QCONNDoor(ip, password)
signal.signal(signal.SIGTERM, lambda *_: (door.close(), sys.exit(0)))
door.conduct_handshake()
print("[+] door open; heartbeating", flush=True)
while True:
    time.sleep(4)
    door.send_heartbeat()
