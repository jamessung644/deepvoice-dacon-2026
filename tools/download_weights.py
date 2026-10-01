#!/usr/bin/env python3
"""Fetch only explicitly released weights; verify bytes before committing a file."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def download_weight(row, destination, *, opener=urlopen):
    release = row.get("release")
    if not release:
        raise ValueError("Weight has not been approved for this public release")
    filename, url = release["filename"], release["url"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.=-]*", filename):
        raise ValueError("Unsafe release filename")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Download URL must be HTTPS without credentials")
    expected_size, expected_hash = row["bytes"], row["sha256"]
    if not isinstance(expected_size, int) or expected_size <= 0 or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError("Invalid size or SHA-256 metadata")
    directory = Path(destination)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / filename
    if target.is_symlink():
        raise ValueError("Existing target is a symlink")
    if target.exists():
        digest = hashlib.sha256()
        if not target.is_file() or target.stat().st_size != expected_size:
            raise ValueError("Existing file differs; move it aside explicitly before retrying")
        with target.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected_hash:
            raise ValueError("Existing file SHA-256 differs; no overwrite performed")
        return target
    descriptor, name = tempfile.mkstemp(prefix=filename + ".", suffix=".part", dir=directory)
    partial = Path(name)
    try:
        digest, received = hashlib.sha256(), 0
        with os.fdopen(descriptor, "wb") as output:
            request = Request(url, headers={"User-Agent": "DeepVoice-weight-downloader/1"})
            with opener(request, timeout=60) as response:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    received += len(chunk)
                    if received > expected_size:
                        raise ValueError("Downloaded size exceeds inventory")
                    output.write(chunk)
                    digest.update(chunk)
        if received != expected_size:
            raise ValueError("Downloaded size does not match inventory")
        if digest.hexdigest() != expected_hash:
            raise ValueError("Downloaded SHA-256 does not match inventory")
        # A hard link is an atomic no-overwrite commit even if a target appears meanwhile.
        os.link(partial, target)
    finally:
        partial.unlink(missing_ok=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("weight", help="Released weight ID, or 'all'")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/weights"))
    args = parser.parse_args()
    inventory = json.loads((ROOT / "results/model_inventory.json").read_text())
    rows = [row for row in inventory["weights"] if row.get("release") and (args.weight == "all" or row["id"] == args.weight)]
    if not rows:
        parser.error("No matching released weight; unpublished weights cannot be downloaded by this tool")
    for row in rows:
        print(f"{row['id']}: downloading/verifying {row['bytes']:,} bytes", flush=True)
        print(f"Verified: {download_weight(row, args.output_dir)}", flush=True)


if __name__ == "__main__":
    main()
