#!/usr/bin/env python3
"""Check installed RouterOS versions across a fleet against a known-latest version.

Usage:
    python checker.py inventory.json --latest 7.15.3
"""
import argparse
import json
import re
import socket
import sys

import paramiko

VERSION_RE = re.compile(r"version:\s*([\d.]+)")
DEFAULT_TIMEOUT = 10


def load_inventory(path: str) -> list:
    with open(path) as f:
        return json.load(f)["routers"]


def fetch_installed_version(router: dict, timeout: int = DEFAULT_TIMEOUT) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            router["host"],
            port=router.get("port", 22),
            username=router["username"],
            password=router["password"],
            timeout=timeout,
        )
        stdin, stdout, stderr = client.exec_command("/system resource print", timeout=timeout)
        output = stdout.read().decode(errors="replace")
    except (paramiko.ssh_exception.SSHException, socket.timeout, socket.error, OSError) as e:
        raise RuntimeError(str(e))
    finally:
        client.close()

    match = VERSION_RE.search(output)
    if not match:
        raise RuntimeError("could not parse version from /system resource print output")
    return match.group(1)


def compare_versions(a: str, b: str) -> int:
    """Return -1/0/1 comparing dotted version strings a vs b, numerically per segment."""
    a_parts = [int(p) for p in a.split(".")]
    b_parts = [int(p) for p in b.split(".")]
    length = max(len(a_parts), len(b_parts))
    a_parts += [0] * (length - len(a_parts))
    b_parts += [0] * (length - len(b_parts))
    return (a_parts > b_parts) - (a_parts < b_parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory_file", help="Path to an inventory.json file")
    parser.add_argument("--latest", required=True, help="Known-latest RouterOS version to compare against")
    args = parser.parse_args()

    routers = load_inventory(args.inventory_file)
    outdated = 0

    print(f"Latest known version: {args.latest}\n")
    for router in routers:
        name = router.get("name", router["host"])
        try:
            installed = fetch_installed_version(router)
        except RuntimeError as e:
            print(f"{name:<20} ERROR: {e}")
            outdated += 1
            continue

        if compare_versions(installed, args.latest) < 0:
            print(f"{name:<20} {installed:<12} OUTDATED (latest: {args.latest})")
            outdated += 1
        else:
            print(f"{name:<20} {installed:<12} up to date")

    sys.exit(1 if outdated else 0)


if __name__ == "__main__":
    main()
