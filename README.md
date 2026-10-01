# mikrotik-upgrade-checker

Cross-reference the installed RouterOS version on every router in your fleet against a known-latest
version, and see who's behind at a glance.

## Installation

```sh
pip install -r requirements.txt
```

## Usage

```sh
cp inventory.example.json inventory.json   # fill in your routers
python checker.py inventory.json --latest 7.15.3
```

```
Latest known version: 7.15.3

branch-office        7.14.2       OUTDATED (latest: 7.15.3)
core                  7.15.3       up to date
```

Exits `1` if any router is outdated or unreachable, `0` if the whole fleet is current.

### Auto-detecting the latest version

```sh
python checker.py inventory.json --auto-latest
python checker.py inventory.json --auto-latest --channel long-term
```

This queries the same endpoint RouterOS itself uses for its "Check For Updates" button
(`upgrade.mikrotik.com`). It isn't an officially documented public API, so treat it as best-effort:
if it's ever unreachable or its response format changes, the tool reports that clearly and you can
fall back to `--latest X.Y.Z` with a version you looked up manually.

## Running the tests

```sh
python -m unittest discover -s tests
```

Tests mock both the SSH layer and the HTTP fetch, so they run without any real routers or network
access.

## License

MIT — see [LICENSE](LICENSE).

## About

Maintained by [Onasis Tech](https://onasis.tech), a Kenyan team building software for ISPs and network operators. If you manage MikroTik routers behind CGNAT or Starlink, [Onasis Tech Connect](https://connect.onasis.tech) gives each one a permanent remote access address, no public IP needed.
