#!/usr/bin/env python3
"""Install a .bar on the PlayBook via the Development Mode appInstaller.cgi ("Install" command)."""
import http.client, os, sys
from pb_cgi import rs

def install(ip, password, bar_path):
    ctx = rs.ssl.SSLContext(rs.ssl.PROTOCOL_TLS_CLIENT); ctx.check_hostname = False; ctx.verify_mode = rs.ssl.CERT_NONE
    ctx.set_ciphers("ALL:@SECLEVEL=0"); ctx.minimum_version = rs.ssl.TLSVersion.TLSv1
    cookie = rs.perform_cgi_action(ip, password, "Is Running")
    data = open(bar_path, "rb").read()
    b = rs.BOUNDARY.encode(); crlf = b"\r\n"
    parts = [b"--" + b, b'Content-Disposition: form-data; name="password"', b"", password.encode(),
             b"--" + b, b'Content-Disposition: form-data; name="command"', b"", b"Install",
             b"--" + b, f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(bar_path)}"'.encode(),
             b"Content-Type: application/zip", b"", data,
             b"--" + b + b"--", b""]
    conn = http.client.HTTPSConnection(ip, 443, context=ctx, timeout=300)
    conn.request("POST", rs.CMD_ENDPOINT, body=crlf.join(parts), headers={"User-Agent": rs.USER_AGENT,
                 "Content-Type": f"multipart/form-data; boundary={rs.BOUNDARY}", "Cookie": cookie})
    return conn.getresponse().read().decode("utf-8", "ignore")

if __name__ == "__main__":
    print(install(os.environ.get("PB_IP", "169.254.0.1"), os.environ["PB_PASSWORD"], sys.argv[1]))
