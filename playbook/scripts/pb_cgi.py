#!/usr/bin/env python3
"""Send an appInstaller.cgi command (e.g. "Uninstall App") to the PlayBook's Development Mode web service."""
import http.client, importlib.util, os, sys

spec = importlib.util.spec_from_file_location("rs", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "third-party", "psyden", "PlayBook-root-setup-V3.py"))
rs = importlib.util.module_from_spec(spec); spec.loader.exec_module(rs)

def cgi(ip, password, command, full_id):
    ctx = rs.ssl.SSLContext(rs.ssl.PROTOCOL_TLS_CLIENT); ctx.check_hostname = False; ctx.verify_mode = rs.ssl.CERT_NONE
    ctx.set_ciphers("ALL:@SECLEVEL=0"); ctx.minimum_version = rs.ssl.TLSVersion.TLSv1
    cookie = rs.perform_cgi_action(ip, password, "Is Running")
    conn = http.client.HTTPSConnection(ip, 443, context=ctx)
    pn, pi = full_id[:-28], full_id[-27:].replace(".", "-")
    body = [f"--{rs.BOUNDARY}", 'Content-Disposition: form-data; name="password"', "", password,
            f"--{rs.BOUNDARY}", 'Content-Disposition: form-data; name="command"', "", command,
            f"--{rs.BOUNDARY}", 'Content-Disposition: form-data; name="package_id"', "", pi,
            f"--{rs.BOUNDARY}", 'Content-Disposition: form-data; name="package_name"', "", pn,
            f"--{rs.BOUNDARY}--", ""]
    conn.request("POST", rs.CMD_ENDPOINT, body=rs.CRLF.join(body), headers={"User-Agent": rs.USER_AGENT,
                 "Content-Type": f"multipart/form-data; boundary={rs.BOUNDARY}", "Cookie": cookie})
    return conn.getresponse().read().decode("utf-8", "ignore")

if __name__ == "__main__":
    print(cgi(os.environ.get("PB_IP", "169.254.0.1"), os.environ["PB_PASSWORD"], sys.argv[1], sys.argv[2]))
