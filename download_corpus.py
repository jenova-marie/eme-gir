#!/usr/bin/env python3
"""Batch-download every .zip listed at https://oracc.museum.upenn.edu/json/ into ./corpus/."""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

INDEX_URL = "https://oracc.museum.upenn.edu/json/"
USER_AGENT = "eme-gir-corpus-fetch/1.0 (+contact: jenova@recoverysky.org)"
HREF_RE = re.compile(r'href="(/json/[^"]+\.zip)"', re.IGNORECASE)

# Oracc's server omits the InCommon intermediate from its TLS chain, so most
# CA bundles can't verify it on their own. Fetch the intermediate (the leaf
# cert advertises its plain-HTTP URL via AIA) once and cache it locally.
INTERMEDIATE_URL = "http://crt.sectigo.com/InCommonRSAServerCA2.crt"
INTERMEDIATE_CACHE = Path(__file__).resolve().parent / ".incommon_intermediate.pem"


def _load_intermediate() -> str:
    if not INTERMEDIATE_CACHE.exists():
        req = urllib.request.Request(INTERMEDIATE_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            der = r.read()
        pem = ssl.DER_cert_to_PEM_cert(der)
        INTERMEDIATE_CACHE.write_text(pem)
    return INTERMEDIATE_CACHE.read_text()


def _build_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if cafile := os.environ.get("SSL_CERT_FILE"):
        ctx.load_verify_locations(cafile=cafile)
    else:
        try:
            import certifi
            ctx.load_verify_locations(cafile=certifi.where())
        except ImportError:
            pass
    try:
        ctx.load_verify_locations(cadata=_load_intermediate())
    except Exception as e:
        print(f"warning: could not load InCommon intermediate ({e})", file=sys.stderr)
    return ctx


_SSL_CTX = _build_ssl_context()


def fetch(url: str, headers: dict | None = None, timeout: int = 60):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX)


def list_zips() -> list[str]:
    with fetch(INDEX_URL) as r:
        html = r.read().decode("utf-8", errors="replace")
    seen, out = set(), []
    for path in HREF_RE.findall(html):
        url = urljoin(INDEX_URL, path)
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def remote_size(url: str) -> int | None:
    try:
        with fetch(url, headers={"Accept-Encoding": "identity"}) as r:
            cl = r.headers.get("Content-Length")
            return int(cl) if cl else None
    except Exception:
        return None


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def download_one(url: str, dest_dir: Path, retries: int = 3) -> tuple[str, str]:
    name = url.rsplit("/", 1)[-1]
    final = dest_dir / name
    part = dest_dir / (name + ".part")

    expected = remote_size(url)
    if final.exists() and expected is not None and final.stat().st_size == expected:
        return name, f"skip ({human(expected)} already present)"

    for attempt in range(1, retries + 1):
        try:
            have = part.stat().st_size if part.exists() else 0
            headers = {"Accept-Encoding": "identity"}
            mode = "wb"
            if have and expected and have < expected:
                headers["Range"] = f"bytes={have}-"
                mode = "ab"
            elif have and expected and have >= expected:
                part.rename(final)
                return name, f"recovered ({human(have)})"

            with fetch(url, headers=headers, timeout=120) as r, open(part, mode) as f:
                while chunk := r.read(1024 * 256):
                    f.write(chunk)

            if expected is not None and part.stat().st_size != expected:
                raise IOError(f"size mismatch: got {part.stat().st_size}, expected {expected}")

            part.rename(final)
            return name, f"ok ({human(final.stat().st_size)})"

        except (urllib.error.URLError, IOError, TimeoutError) as e:
            if attempt == retries:
                return name, f"FAIL after {retries} tries: {e}"
            time.sleep(2 * attempt)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", default="corpus", help="output directory (default: corpus)")
    ap.add_argument("--workers", type=int, default=4, help="parallel downloads (default: 4)")
    ap.add_argument("--list-only", action="store_true", help="just print URLs and exit")
    args = ap.parse_args()

    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    print(f"Indexing {INDEX_URL} ...", flush=True)
    urls = list_zips()
    print(f"Found {len(urls)} zip files.", flush=True)

    if args.list_only:
        print("\n".join(urls))
        return 0

    print(f"Downloading to {dest}/ with {args.workers} workers.\n", flush=True)
    done = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download_one, u, dest): u for u in urls}
        for fut in cf.as_completed(futures):
            done += 1
            name, status = fut.result()
            print(f"[{done:>3}/{len(urls)}] {name}: {status}", flush=True)

    failed = [p for p in dest.glob("*.zip.part")]
    if failed:
        print(f"\n{len(failed)} incomplete .part files left in {dest}/", file=sys.stderr)
        return 1
    print("\nAll done. ✨")
    return 0


if __name__ == "__main__":
    sys.exit(main())
