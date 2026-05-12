#!/usr/bin/env python3
"""Probe oracc.museum.upenn.edu for project zips that aren't on the public
/json/ download index, and report which ones we don't have locally.

Strategy:
  1. Fetch /projectlist.json — the canonical list of all public Oracc
     projects with pathnames (e.g., "eme-gir/admin/ur3").
  2. For each project, try TWO candidate download URLs:
       a) /json/{pathname-flattened-with-dashes}.zip   (the public index)
       b) /{pathname-with-slashes}/json.zip            (per-project alt)
     The (a) URLs are what download_corpus.py already pulled. The (b)
     URLs sometimes work for sub-projects that aren't listed on (a) —
     this is what we're hunting for.
  3. HEAD each candidate (polite, throttled).
  4. Compare findings against what's in corpus/ and report.

This is a READ-ONLY probe. It downloads nothing — only the project list
and HEAD responses. Use it to plan what to fetch with download_corpus.py
or a follow-up extension.

Output goes to stdout as a structured report, plus optionally a JSON
file for programmatic follow-up.

Usage:
    python3 find_missing_corpora.py
    python3 find_missing_corpora.py --json missing.json --workers 4
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Reuse the SSL/TLS setup + downloader that download_corpus.py already
# worked out (Oracc serves a valid cert but omits the InCommon intermediate,
# so the default Python SSL context fails). Importing keeps the AIA-fetch +
# cache + resume-safe download logic in one place.
from download_corpus import (  # noqa: E402
    _SSL_CTX,
    USER_AGENT,
    download_one,
    fetch as _fetch,
    human as _human,
)

from eme_gir.paths import CORPUS_DIR, ROOT

ORACC_HOST = "https://oracc.museum.upenn.edu"
# /projects.json is the canonical simple list (just pathnames). The richer
# /projectlist.json exists too (with name/abbrev/blurb) but currently has a
# literal-newline bug inside a string that breaks strict JSON parsing.
PROJECTS_URL = f"{ORACC_HOST}/projects.json"
PROJECTLIST_URL = f"{ORACC_HOST}/projectlist.json"


def head(url: str, timeout: int = 30) -> tuple[int, int | None]:
    """Return (status_code, content_length_bytes_or_None).

    HEAD failures (network error, timeout, etc.) yield (0, None).
    """
    req = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as r:
            cl = r.headers.get("Content-Length")
            return r.status, int(cl) if cl else None
    except urllib.error.HTTPError as e:
        return e.code, None
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, None


def project_index_url(pathname: str) -> str:
    """The flattened-with-dashes URL on /json/ that download_corpus.py uses."""
    flat = pathname.replace("/", "-")
    return f"{ORACC_HOST}/json/{flat}.zip"


def project_alt_url(pathname: str) -> str:
    """The per-project /<path>/json.zip URL that's sometimes available even
    when /json/<flat>.zip isn't on the public index."""
    return f"{ORACC_HOST}/{pathname}/json.zip"


def have_locally(pathname: str) -> Path | None:
    """Return the local zip path if we have it, or None."""
    flat = pathname.replace("/", "-")
    p = CORPUS_DIR / f"{flat}.zip"
    return p if p.exists() else None


def human(n: int | None) -> str:
    if n is None:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def probe_project(p: dict | str) -> dict:
    # Accept either a rich dict (from projectlist.json) or a bare pathname
    # string (from projects.json).
    if isinstance(p, str):
        pathname, name, abbrev = p, "", ""
    else:
        pathname = p.get("pathname", "")
        name = p.get("name", "")
        abbrev = p.get("abbrev", "")

    local = have_locally(pathname)
    idx_url = project_index_url(pathname)
    alt_url = project_alt_url(pathname)
    idx_status, idx_size = head(idx_url)
    # Only check alt URL if index URL isn't 200 (saves a polite request)
    if idx_status == 200:
        alt_status, alt_size = (None, None)
    else:
        alt_status, alt_size = head(alt_url)

    return {
        "pathname": pathname,
        "name": name,
        "abbrev": abbrev,
        "local": str(local.relative_to(ROOT)) if local else None,
        "local_size": local.stat().st_size if local else None,
        "index_url": idx_url,
        "index_status": idx_status,
        "index_size": idx_size,
        "alt_url": alt_url,
        "alt_status": alt_status,
        "alt_size": alt_size,
    }


def categorize(rows: list[dict]) -> dict[str, list[dict]]:
    """Bucket the probe results by what action (if any) the user could take."""
    have = []
    missing_indexed = []      # downloadable from /json/ index but we don't have it
    missing_alt_only = []     # only reachable via /<path>/json.zip
    missing_unreachable = []  # listed in projectlist.json but no working URL

    for r in rows:
        if r["local"]:
            have.append(r)
        elif r["index_status"] == 200:
            missing_indexed.append(r)
        elif r["alt_status"] == 200:
            missing_alt_only.append(r)
        else:
            missing_unreachable.append(r)
    return {
        "have": have,
        "missing_indexed": missing_indexed,
        "missing_alt_only": missing_alt_only,
        "missing_unreachable": missing_unreachable,
    }


def print_report(buckets: dict[str, list[dict]]) -> None:
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    h = buckets["have"]
    mi = buckets["missing_indexed"]
    ma = buckets["missing_alt_only"]
    mu = buckets["missing_unreachable"]
    print(f"  have locally:                  {len(h):>4}")
    print(f"  missing, on /json/ index:      {len(mi):>4}")
    print(f"  missing, only at alt URL:      {len(ma):>4}  ← worth fetching")
    print(f"  missing, no working URL:       {len(mu):>4}  ← need external source (ETCSL etc.)")

    if mi:
        print()
        print("--- MISSING but downloadable from /json/ index ---")
        print("(these should already be in corpus/; running download_corpus.py would fix)")
        for r in sorted(mi, key=lambda x: x["pathname"]):
            print(f"  {r['pathname']:<32}  {human(r['index_size']):>8}  {r['name'][:60]}")

    if ma:
        print()
        print("--- MISSING, reachable only via /<project>/json.zip ---")
        print("(NEW finds — not on the public /json/ download page)")
        for r in sorted(ma, key=lambda x: -(x["alt_size"] or 0)):
            print(f"  {r['pathname']:<32}  {human(r['alt_size']):>8}  {r['name'][:60]}")
            print(f"    -> {r['alt_url']}")

    if mu:
        print()
        print(f"--- MISSING, no Oracc URL works ({len(mu)} projects) ---")
        print("(content lives elsewhere — Oxford ETCSL, CDLI, Eme-gir staging, etc.)")
        for r in sorted(mu, key=lambda x: x["pathname"])[:20]:
            print(f"  {r['pathname']:<32}  {r['name'][:60]}")
        if len(mu) > 20:
            print(f"  ... and {len(mu) - 20} more")


ZIP_MAGIC = b"PK\x03\x04"  # local file header signature; every real zip starts with this


def _looks_like_zip(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(4) == ZIP_MAGIC
    except OSError:
        return False


def fetch_alt(url: str, target_name: str, dest_dir: Path) -> tuple[str, str]:
    """Download a /<project>/json.zip URL into corpus/<flat-name>.zip.

    Different from download_corpus.download_one() because we have to
    override the destination filename (alt-URL last segment is always
    `json.zip`, not the flattened project name). Resume-safe via .part
    file and Content-Length comparison.

    Validates the response is actually a zip — Oracc occasionally returns
    a 200 with an HTML error page (its p4error.xml template) when a
    project's archive isn't built yet. Such bogus responses are deleted
    so they can't poison the corpus.
    """
    final = dest_dir / target_name
    part = dest_dir / (target_name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120, context=_SSL_CTX) as r:
            expected = int(r.headers.get("Content-Length") or 0)
            if final.exists() and expected and final.stat().st_size == expected:
                return target_name, f"skip ({_human(expected)} already present)"
            with open(part, "wb") as f:
                while chunk := r.read(1024 * 256):
                    f.write(chunk)
        if expected and part.stat().st_size != expected:
            raise IOError(f"size mismatch: {part.stat().st_size} != {expected}")
        if not _looks_like_zip(part):
            part.unlink(missing_ok=True)
            return target_name, "FAIL: server returned non-zip content (likely an HTML error page — project may not have a built archive yet)"
        part.rename(final)
        return target_name, f"ok ({_human(final.stat().st_size)})"
    except (urllib.error.URLError, IOError, TimeoutError) as e:
        return target_name, f"FAIL: {e}"


def fetch_missing(buckets: dict[str, list[dict]]) -> int:
    to_fetch = buckets["missing_indexed"] + buckets["missing_alt_only"]
    if not to_fetch:
        print("\nNothing missing to fetch.")
        return 0

    print(f"\nFetching {len(to_fetch)} missing zips into {CORPUS_DIR}/ ...\n")
    failures = 0
    for r in to_fetch:
        target = r["pathname"].replace("/", "-") + ".zip"
        if r["index_status"] == 200:
            url = r["index_url"]
            _, status = download_one(url, CORPUS_DIR)
        else:
            url = r["alt_url"]
            _, status = fetch_alt(url, target, CORPUS_DIR)
        marker = "FAIL" in status
        if marker:
            failures += 1
        print(f"  {'✗' if marker else '✓'} {target:<32}  {status}")

    print(f"\nDone. {len(to_fetch) - failures} fetched, {failures} failed.")
    if failures == 0 and to_fetch:
        print(
            "\nNew corpus content available. Rebuild the indexes to pick it up:\n"
            "  python3 build_text_index.py\n"
            "  python3 build_collocations.py    # optional, only if you use find_collocations\n"
        )
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", help="optional: write the full structured report to this JSON file")
    ap.add_argument("--workers", type=int, default=4,
                    help="parallel HEAD probes (default 4; be polite)")
    ap.add_argument("--fetch", action="store_true",
                    help="after probing, download all reachable-but-missing zips into corpus/")
    args = ap.parse_args()

    if not CORPUS_DIR.is_dir():
        print(f"corpus/ not found at {CORPUS_DIR}", file=sys.stderr)
        return 1

    print(f"Fetching {PROJECTS_URL} ...", flush=True)
    with _fetch(PROJECTS_URL) as r:
        doc = json.loads(r.read())
    projects = doc.get("public", [])
    print(f"  {len(projects)} public projects listed", flush=True)

    print(f"\nProbing each project (HEAD-only, {args.workers} workers) ...", flush=True)
    t0 = time.monotonic()
    rows: list[dict] = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for done, row in enumerate(
            pool.map(probe_project, projects), start=1
        ):
            rows.append(row)
            if done % 25 == 0 or done == len(projects):
                rate = done / (time.monotonic() - t0)
                print(f"  {done:>3}/{len(projects)}  ({rate:,.1f}/s)", flush=True)

    buckets = categorize(rows)
    print_report(buckets)

    if args.json:
        out = Path(args.json)
        out.write_text(json.dumps({
            "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_projects": len(projects),
            "buckets": {k: len(v) for k, v in buckets.items()},
            "rows": rows,
        }, indent=2))
        print(f"\nFull report written to {out}")

    if args.fetch:
        return fetch_missing(buckets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
