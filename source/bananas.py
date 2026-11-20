#!/usr/bin/env python3
"""Minimal BaNaNaS (OpenTTD content service) client.
Usage: bananas.py list <type> [filter]     (type: 1=basegfx 2=newgrf 5=scenario ...)
       bananas.py get <outdir> <id> [<id>...]  (numeric content ids from 'list')
"""
import socket, struct, sys, os, urllib.request

HOST, PORT = "content.openttd.org", 3978
MIRROR = "https://binaries.openttd.org/bananas"

def send(s, ptype, payload):
    s.sendall(struct.pack("<HB", len(payload) + 3, ptype) + payload)

def recv_exact(s, n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c: raise EOFError
        b += c
    return b

def cstr(buf, i):
    j = buf.index(b"\0", i)
    return buf[i:j].decode("utf-8", "replace"), j + 1

def list_content(ctype, filt=""):
    s = socket.create_connection((HOST, PORT), timeout=30)
    payload = struct.pack("<BIB", ctype, 0xFFFFFFFF, 1) + b"vanilla\0" + b"15.3\0"
    send(s, 0, payload)
    out = []
    try:
        while True:
            size, ptype = struct.unpack("<HB", recv_exact(s, 3))
            body = recv_exact(s, size - 3)
            if ptype != 4: continue
            t, cid, fsize = struct.unpack_from("<BII", body, 0)
            i = 9
            name, i = cstr(body, i); ver, i = cstr(body, i); url, i = cstr(body, i); desc, i = cstr(body, i)
            uid, = struct.unpack_from("<I", body, i)
            if filt.lower() in name.lower():
                out.append((cid, name, ver, fsize, "%08x" % uid))
    except (socket.timeout, EOFError):
        pass
    return out

def get(outdir, ids):
    os.makedirs(outdir, exist_ok=True)
    req = urllib.request.Request(MIRROR, data="".join("%d\n" % i for i in ids).encode(), method="POST",
                                 headers={"User-Agent": "OpenTTD/15.3"})
    lines = urllib.request.urlopen(req, timeout=60).read().decode().splitlines()
    for line in lines:
        if not line.strip(): continue
        cid, ctype, size, url = line.split(",", 3)
        if url.startswith("ottd"): continue
        fn = os.path.join(outdir, url.rsplit("/", 1)[-1])
        print("download", cid, url, "->", fn)
        open(fn, "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "OpenTTD/15.3"}), timeout=120).read())

if __name__ == "__main__":
    if sys.argv[1] == "list":
        for row in list_content(int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else ""):
            print(*row, sep="\t")
    else:
        get(sys.argv[2], [int(x) for x in sys.argv[3:]])
