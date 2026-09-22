#!/usr/bin/env python3
"""Check installed RouterOS versions across a fleet against a known-latest version.

Usage:
    python checker.py inventory.json --latest 7.15.3
    python checker.py inventory.json --auto-latest
"""
import argparse
import json
import re
import socket
import sys
from urllib import error, request

import paramiko

VERSION_RE = re.compile(r"version:\s*([\d.]+)")
DEFAULT_TIMEOUT = 10
UPGRADE_CHECK_URL = "https://upgrade.mikrotik.com/routeros/NEWEST{major}.{channel}"


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


def fetch_latest_version(major: int = 7, channel: str = "stable") -> str:
    """Best-effort: ask MikroTik's own update-check endpoint what the latest version is.

    This isn't officially documented as a public API — it's the same endpoint RouterOS itself
    polls for "Check For Updates". Treat it as best-effort; pass --latest to override if it's
    ever unavailable or its format changes.
    """
    url = UPGRADE_CHECK_URL.format(major=major, channel=channel)
    try:
        with request.urlopen(url, timeout=10) as resp:
            body = resp.read().decode().strip()
    except error.URLError as e:
        raise RuntimeError(f"Could not reach {url}: {e}")

    if not body:
        raise RuntimeError(f"{url} returned an empty response")
    return body.split()[0]


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
    parser.add_argument("--latest", help="Known-latest RouterOS version to compare against")
    parser.add_argument("--auto-latest", action="store_true",
                         help="Fetch the latest version from upgrade.mikrotik.com (best effort)")
    parser.add_argument("--channel", default="stable", choices=["stable", "long-term", "testing"])
    parser.add_argument("--major", type=int, default=7)
    args = parser.parse_args()

    if args.auto_latest:
        try:
            latest = fetch_latest_version(args.major, args.channel)
        except RuntimeError as e:
            print(f"Could not auto-detect latest version: {e}", file=sys.stderr)
            print("Pass --latest X.Y.Z to compare manually.", file=sys.stderr)
            sys.exit(2)
    elif args.latest:
        latest = args.latest
    else:
        parser.error("Specify --latest X.Y.Z or --auto-latest")

    routers = load_inventory(args.inventory_file)
    outdated = 0

    print(f"Latest known version: {latest}\n")
    for router in routers:
        name = router.get("name", router["host"])
        try:
            installed = fetch_installed_version(router)
        except RuntimeError as e:
            print(f"{name:<20} ERROR: {e}")
            outdated += 1
            continue

        if compare_versions(installed, latest) < 0:
            print(f"{name:<20} {installed:<12} OUTDATED (latest: {latest})")
            outdated += 1
        else:
            print(f"{name:<20} {installed:<12} up to date")

    sys.exit(1 if outdated else 0)


if __name__ == "__main__":
    main()
