#!/usr/bin/env python3
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.request

BASE = "http://10.4.89.246"
PROJECT_NAME = "K-13-MODUL-1"
USERNAME = "K-13"
PASSWORD = "K-13@GNS3"

CLIENTS = {
    "Alice":   "10.70.1.2",
    "Mika":    "10.70.1.3",
    "Chisa":   "10.70.2.2",
    "Knights": "10.70.3.2",
    "Eiri":    "10.70.3.3",
}

PROMPT_RE = re.compile(rb"root@[\w.-]+:.*[#] $")
CONSOLE_HOST = "10.4.89.246"


def req(method, path, body=None, token=None, timeout=20):
    r = urllib.request.Request(BASE + path, method=method)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(r, data, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def console_cmd(host, port, command, settle=1.0, read_timeout=4.0):
    """Connect to a GNS3 telnet console, run one command, return its output."""
    s = socket.create_connection((host, port), timeout=10)
    s.settimeout(read_timeout)
    try:
        time.sleep(settle)
        s.sendall(b"\n")
        time.sleep(0.3)
        try:
            s.recv(4096)
        except socket.timeout:
            pass
        s.sendall(command.encode() + b"\n")
        out = b""
        deadline = time.time() + read_timeout
        while time.time() < deadline:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                out += chunk
                if PROMPT_RE.search(out):
                    break
            except socket.timeout:
                break
        return out.decode(errors="replace")
    finally:
        s.close()


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", text)


def wait_node_ready(port, expected_ip, tries=15, delay=4):
    """Poll a node console until eth0 has its expected IP (container fully booted)."""
    for i in range(tries):
        try:
            out = strip_ansi(console_cmd(CONSOLE_HOST, port, "ip -br a"))
            if expected_ip in out:
                return True
            print(f"    ... attempt {i+1}/{tries}: {expected_ip} not up yet")
        except Exception as e:
            print(f"    ... attempt {i+1}/{tries}: console error: {e!r}")
        time.sleep(delay)
    return False


def main():
    st, r = req("POST", "/v3/access/users/authenticate",
                {"username": USERNAME, "password": PASSWORD})
    if st != 200:
        sys.exit(f"Authentication failed ({st}): {r}")
    token = r["access_token"]
    print("[+] Authenticated")

    st, projects = req("GET", "/v3/projects", token=token)
    pid = next((p["project_id"] for p in projects if p["name"] == PROJECT_NAME), None)
    if not pid:
        sys.exit(f"Project '{PROJECT_NAME}' not found")
    print(f"[+] Project: {PROJECT_NAME} ({pid})")

    st, ns = req("GET", f"/v3/projects/{pid}/nodes", token=token)
    nodes = {n["name"]: n for n in ns}

    stopped = [n for n in CLIENTS if n not in nodes or nodes[n]["status"] != "started"]
    for name in stopped:
        nid = nodes[name]["node_id"]
        print(f"[*] Starting {name}...")
        req("POST", f"/v3/projects/{pid}/nodes/{nid}/start", token=token)
        time.sleep(4)

    console_host = CONSOLE_HOST
    for name, ip in CLIENTS.items():
        port = nodes[name].get("console")
        if not port:
            sys.exit(f"[!] {name}: no console port")
        if not wait_node_ready(port, ip):
            sys.exit(f"[!] {name}: eth0 never got {ip} — node not ready, check console")
        print(f"[+] {name}: ready ({ip})")

    results = {}
    for src in CLIENTS:
        node = nodes[src]
        port = node.get("console")
        if not port:
            print(f"[!] {src}: no console port")
            continue
        for dst_name, dst_ip in CLIENTS.items():
            if dst_name == src:
                continue
            same_subnet = CLIENTS[src].rsplit(".", 1)[0] == dst_ip.rsplit(".", 1)[0]
            label = "same-subnet" if same_subnet else "cross-subnet"
            try:
                raw = console_cmd(console_host, port, f"ping -c 2 -W 2 {dst_ip}")
                clean = strip_ansi(raw)
                passed = "2 received" in clean or "2/2" in clean or " 0% packet loss" in clean
                # "0% packet loss" can wrap; check for both phrasings
                if not passed:
                    passed = "0% packet loss" in clean.replace("\r\n", " ")
            except Exception as e:
                clean, passed = f"ERROR: {e}", False
            results[(src, dst_name)] = passed
            mark = "PASS" if passed else "FAIL"
            print(f"[{'+' if passed else '!'}] {src:8s} -> {dst_name:8s} ({dst_ip}, {label}): {mark}")

    print("\n=== CONNECTIVITY MATRIX (Soal 3: cross-subnet) ===")
    hdr = "source\\dest " + "".join(f"{d:>10s}" for d in CLIENTS)
    print(hdr)
    for src in CLIENTS:
        row = f"{src:12s}"
        for dst in CLIENTS:
            if dst == src:
                row += f"{'---':>10s}"
            else:
                row += f"{'PASS' if results.get((src, dst)) else 'FAIL':>10s}"
        print(row)

    cross_fail = [(s, d) for (s, d), ok in results.items() if not ok
                  and CLIENTS[s].rsplit(".", 1)[0] != CLIENTS[d].rsplit(".", 1)[0]]
    if cross_fail:
        print(f"\n[!] {len(cross_fail)} cross-subnet test(s) FAILED.")
        sys.exit(1)
    print("\n[+] Semua client dapat saling berkomunikasi antar-subnet.")


if __name__ == "__main__":
    main()
