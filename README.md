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

Auto-detecting the latest version from MikroTik's own update-check endpoint is coming soon — for
now, pass it manually with `--latest`.

## License

MIT — see [LICENSE](LICENSE).
