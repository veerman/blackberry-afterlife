#!/usr/bin/env python3
"""Install several .bar files over one Development Mode login (one on-device password prompt)."""
import http.client, os, sys
from pb_cgi import rs

def main(ip, password, bars):
    ctx = rs.ssl.SSLContext(rs.ssl.PROTOCOL_TLS_CLIENT); ctx.check_hostname = False; ctx.verify_mode = rs.ssl.CERT_NONE
    ctx.set_ciphers("ALL:@SECLEVEL=0"); ctx.minimum_version = rs.ssl.TLSVersion.TLSv1
    cookie = rs.perform_cgi_action(ip, password, "Is Running")
    b = rs.BOUNDARY.encode(); crlf = b"\r\n"
    for bar in bars:
        parts = [b"--" + b, b'Content-Disposition: form-data; name="password"', b"", password.encode(),
                 b"--" + b, b'Content-Disposition: form-data; name="command"', b"", b"Install",
                 b"--" + b, f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(bar)}"'.encode(),
                 b"Content-Type: application/zip", b"", open(bar, "rb").read(), b"--" + b + b"--", b""]
        conn = http.client.HTTPSConnection(ip, 443, context=ctx, timeout=300)
        conn.request("POST", rs.CMD_ENDPOINT, body=crlf.join(parts), headers={"User-Agent": rs.USER_AGENT,
                     "Content-Type": f"multipart/form-data; boundary={rs.BOUNDARY}", "Cookie": cookie})
        out = conn.getresponse().read().decode("utf-8", "ignore")
        res = [l for l in out.splitlines() if l.startswith(("result::", "Error"))]
        print(f"{os.path.basename(bar)}: {res[-1] if res else out.strip().splitlines()[-1:]}", flush=True)

if __name__ == "__main__":
    main(os.environ.get("PB_IP", "169.254.0.1"), os.environ["PB_PASSWORD"], sys.argv[1:])
