"""Validate the package-facing Happy Coder contract before LPK creation."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    with (ROOT / name).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main():
    package = load("package.yml")
    manifest = load("lzc-manifest.yml")
    action = load("lazycat-action.yml")
    if package["package"] != "cloud.lazycat.app.happycoder":
        raise SystemExit("unexpected package id")
    if manifest["application"]["subdomain"] != "happyweb":
        raise SystemExit("unexpected web subdomain")
    if manifest["application"]["secondary_domains"] != ["happyserver"]:
        raise SystemExit("unexpected server domain")
    if list(manifest["services"]) != ["happycoder"]:
        raise SystemExit("Happy Coder must use the happycoder service name")
    if manifest["services"]["happycoder"]["binds"] != ["/lzcapp/var/data:/data"]:
        raise SystemExit("unexpected persistent data bind")
    if action["source"]["url"] != "https://github.com/slopus/happy.git":
        raise SystemExit("unexpected upstream source")
    if action["build"]["prepare"]["mode"] != "command":
        raise SystemExit("Happy Coder must use the combined-image build")
    image = manifest["services"]["happycoder"]["image"]
    if not (
        image.startswith("ttl.sh/lazycat-happycoder-")
        or image.startswith("registry.lazycat.cloud/")
    ):
        raise SystemExit("manifest image must be the configured staging or official LazyCat image")
    print("Happy Coder package contract: OK")


if __name__ == "__main__":
    main()
