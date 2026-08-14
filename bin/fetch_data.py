#!/usr/bin/env python3

"""Fetch the EHT First M87 Results (Apr 2019) calibrated uvfits data.

Downloads the official EHT data tarball, verifies SHA-256 checksums against
the expected values recorded in data/checksums.txt, and extracts the uvfits
files into the job working directory.

This is a REQUIRED data source: on unrecoverable failure the script still
writes every declared output file (empty) and then exits non-zero, so the
failure surfaces in the fetch job instead of a stage-out HOLD.
"""

import argparse
import hashlib
import os
import sys
import tarfile
import time
import urllib.request

DEFAULT_URL = (
    "https://github.com/eventhorizontelescope/2019-D01-01/raw/master/"
    "EHTC_FirstM87Results_Apr2019_uvfits.tgz"
)

RETRY_DELAYS = [5, 15, 45]


def sha256sum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_expected(path):
    expected = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            digest, name = line.split(None, 1)
            expected[name.strip()] = digest
    return expected


def download(url, dest):
    last_err = None
    for attempt, delay in enumerate([0] + RETRY_DELAYS):
        if delay:
            print(f"Retrying in {delay}s (attempt {attempt + 1})...")
            time.sleep(delay)
        try:
            print(f"Downloading {url}")
            with urllib.request.urlopen(url, timeout=120) as resp, open(dest, "wb") as out:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
            return
        except Exception as e:  # noqa: BLE001 - retry any transient failure
            last_err = e
            print(f"ERROR: download failed: {e}", file=sys.stderr)
    raise RuntimeError(f"download failed after retries: {last_err}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="Tarball URL")
    parser.add_argument("--expected-checksums", default=None,
                        help="File with 'sha256  filename' lines to verify against")
    parser.add_argument("--uvfits", nargs="+", required=True,
                        help="uvfits file names expected out of the tarball")
    parser.add_argument("--manifest", required=True,
                        help="Output manifest of computed checksums")
    args = parser.parse_args()

    try:
        tarball = os.path.basename(args.url)
        download(args.url, tarball)

        expected = {}
        if args.expected_checksums and os.path.exists(args.expected_checksums):
            expected = load_expected(args.expected_checksums)

        records = []
        mismatches = []

        digest = sha256sum(tarball)
        records.append((digest, tarball))
        if tarball in expected and expected[tarball] != digest:
            mismatches.append(tarball)

        with tarfile.open(tarball) as tar:
            members = {os.path.basename(m.name): m for m in tar.getmembers() if m.isfile()}
            for name in args.uvfits:
                if name not in members:
                    raise RuntimeError(f"{name} not found in tarball")
                with tar.extractfile(members[name]) as src, open(name, "wb") as dst:
                    dst.write(src.read())
                digest = sha256sum(name)
                records.append((digest, name))
                if name in expected and expected[name] != digest:
                    mismatches.append(name)

        with open(args.manifest, "w") as f:
            f.write(f"# Computed SHA-256 checksums, source: {args.url}\n")
            for digest, name in records:
                f.write(f"{digest}  {name}\n")

        if mismatches:
            raise RuntimeError(f"checksum mismatch for: {', '.join(mismatches)}")

        print(f"Fetched and verified {len(args.uvfits)} uvfits files")

    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        # Required source: write declared outputs so stage-out does not HOLD,
        # then fail loud.
        for name in args.uvfits + [args.manifest]:
            if not os.path.exists(name):
                open(name, "w").close()
        sys.exit(1)


if __name__ == "__main__":
    main()
