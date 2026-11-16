#!/usr/bin/env python3
"""Fetch and verify a task's media assets from its assets.manifest.json.

Usage:
    python3 scripts/fetch_assets.py tasks/dev/trackA/a2/a2-0001-mariner4 [--verify-only] [--rendition large|orig]

Media never lives in git. This script downloads every asset that has a URL
into <task>/assets/, verifies its sha256 against the manifest, fetches
sidecars, and regenerates benchmark-generated assets (those with a
`generate` command). Assets with `status: pending` are reported and skipped.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

UA = "DocuBench-fetch/0.1"
CHUNK = 1 << 20


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req, timeout=120) as r, tmp.open("wb") as out:
        shutil.copyfileobj(r, out, CHUNK)
    tmp.replace(dest)


def check(dest: Path, expected: str | None, label: str, problems: list) -> None:
    if not dest.exists():
        problems.append(f"{label}: missing")
        print(f"  MISSING  {label}")
        return
    actual = sha256_of(dest)
    if expected is None:
        print(f"  NOSUM    {label}  sha256={actual[:16]}… (manifest has no checksum)")
    elif actual == expected:
        print(f"  OK       {label}")
    else:
        problems.append(f"{label}: checksum mismatch")
        print(f"  MISMATCH {label}\n           expected {expected}\n           actual   {actual}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_dir")
    ap.add_argument("--verify-only", action="store_true", help="do not download; only verify what is present")
    ap.add_argument("--rendition", default="large", help="which rendition to fetch for assets that list several")
    args = ap.parse_args()

    task = Path(args.task_dir)
    manifest = json.loads((task / "assets.manifest.json").read_text(encoding="utf-8"))
    assets_dir = task / "assets"
    assets_dir.mkdir(exist_ok=True)
    problems: list = []
    pending: list = []

    for a in manifest["assets"]:
        aid = a["asset_id"]
        if a.get("status", "").startswith("pending"):
            pending.append(f"{aid}: {a['status']}")
            continue

        # Benchmark-generated asset
        if a.get("generate"):
            dest = assets_dir / a["filename"]
            if not dest.exists() and not args.verify_only:
                print(f"  GEN      {aid} {a['filename']}")
                cmd = a["generate"].replace(a["filename"], str(dest))
                subprocess.run(cmd, shell=True, check=True)
            check(dest, None, f"{aid} {a['filename']}", problems)
            continue

        # Multi-rendition video
        if a.get("renditions"):
            rend = a["renditions"].get(args.rendition) or next(iter(a["renditions"].values()))
            dest = assets_dir / a["filename"] if args.rendition in a["filename"] else assets_dir / Path(rend["url"]).name
            if not dest.exists() and not args.verify_only:
                print(f"  GET      {aid} {dest.name} ({rend.get('bytes', '?')} bytes)")
                download(rend["url"], dest)
            check(dest, rend.get("sha256"), f"{aid} {dest.name}", problems)
            for name, sc in (a.get("sidecars") or {}).items():
                if not sc.get("url"):
                    continue
                sdest = assets_dir / Path(sc["url"]).name
                if not sdest.exists() and not args.verify_only:
                    print(f"  GET      {aid} sidecar {name}")
                    download(sc["url"], sdest)
                if sc.get("sha256") or sdest.exists():
                    check(sdest, sc.get("sha256"), f"{aid} sidecar {sdest.name}", problems)
            continue

        # Plain single-file asset
        if a.get("url"):
            dest = assets_dir / a["filename"]
            if not dest.exists() and not args.verify_only:
                print(f"  GET      {aid} {a['filename']}")
                download(a["url"], dest)
            check(dest, a.get("sha256"), f"{aid} {a['filename']}", problems)

    if pending:
        print("\nPending (not fetchable yet):")
        for p in pending:
            print(f"  - {p}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nAll present assets verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
