"""Entrypoint that copies entry.png to MAKEFUN_OUTPUT_DIR and verifies SHA-256."""

import hashlib
import os
from pathlib import Path
import shutil
import sys


def _sha256_file(path):
    """Compute SHA-256 hex digest of a file in 65536-byte chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def main():
    """Copy entry.png to MAKEFUN_OUTPUT_DIR (default /output) and verify SHA-256."""
    src = Path(__file__).resolve().parent / "entry.png"
    if not src.is_file():
        print(f"Error: source file not found: {src}", file=sys.stderr)
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / "entry.png"

    shutil.copyfile(src, dst)

    src_hash = _sha256_file(src)
    dst_hash = _sha256_file(dst)
    if src_hash != dst_hash:
        print(
            f"Error: SHA-256 mismatch after copy ({src_hash} != {dst_hash})",
            file=sys.stderr,
        )
        return 1

    size_bytes = dst.stat().st_size
    print(f"Copied {dst} ({size_bytes} bytes, sha256={dst_hash})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
