"""Resolve glossary word_refs (e.g. "epsd2/admin/ur3:P113959.10.3") into
the actual line of Sumerian text in context, by lazily reading the
right corpusjson/{P-id}.json from inside its project zip.

Reads from text_index.sqlite (built by build_text_index.py).
"""

from __future__ import annotations

import functools
import json
import sqlite3
import zipfile
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parent
TEXT_INDEX_DB = ROOT / "text_index.sqlite"


def parse_word_ref(word_ref: str) -> tuple[str, str, str, str | None] | None:
    """'epsd2/admin/ur3:P113959.10.3' -> (project, text_id, line_n, word_n).

    word_n may be None if the ref points at a whole line.
    Returns None if the ref shape is unrecognized.
    """
    if ":" not in word_ref:
        return None
    project, ref = word_ref.split(":", 1)
    parts = ref.split(".")
    if len(parts) < 2 or not parts[0]:
        return None
    text_id = parts[0]
    line_n = parts[1]
    word_n = parts[2] if len(parts) > 2 else None
    return project, text_id, line_n, word_n


@functools.lru_cache(maxsize=8)
def _load_text_index() -> dict[tuple[str, str], tuple[str, str]]:
    """Lazy connect; the SQLite file is small enough to query per call cheaply,
    but we cache the connection-yielding helper instead."""
    raise NotImplementedError("use _lookup() — this is a placeholder")


def _lookup(project: str, text_id: str) -> tuple[str, str] | None:
    """Return (zip_path, member_path) for a (project, text_id), or None."""
    if not TEXT_INDEX_DB.exists():
        return None
    con = sqlite3.connect(TEXT_INDEX_DB)
    try:
        row = con.execute(
            "SELECT zip_path, member_path FROM text_locations "
            "WHERE project=? AND text_id=?",
            (project, text_id),
        ).fetchone()
    finally:
        con.close()
    return tuple(row) if row else None


@functools.lru_cache(maxsize=512)
def _load_corpusjson(project: str, text_id: str) -> dict | None:
    """Load and parse the corpusjson for a given (project, text_id).

    Cached so repeated word_refs into the same text don't re-open the zip.
    Each text JSON is small (a few KB to a few hundred KB). Returns None on
    any I/O / parse failure (some corpusjson files are empty placeholders).
    """
    loc = _lookup(project, text_id)
    if loc is None:
        return None
    zip_path, member = loc
    try:
        with zipfile.ZipFile(zip_path) as z, z.open(member) as f:
            return json.load(f)
    except (json.JSONDecodeError, zipfile.BadZipFile, KeyError, OSError):
        return None


def _walk_cdl(node: Any) -> Iterator[dict]:
    """Depth-first walk yielding every dict child node in cdl order."""
    if not isinstance(node, dict):
        return
    yield node
    for child in node.get("cdl") or ():
        yield from _walk_cdl(child)


def _line_label_from_words(words: list[dict], fallback_line_n: str) -> str:
    """If we couldn't find a line-start d-node, build a reasonable label."""
    return fallback_line_n


def resolve_word_ref(word_ref: str) -> dict | None:
    """Resolve a single word_ref to its line context.

    Returns:
        {
          "raw_ref": str,
          "project": str,
          "text_id": str,
          "line_label": str,                # e.g. "o 3" or "obv. 10"
          "line_n": str,
          "target_ref": str | None,         # the word ref we were asked about
          "words": [
            {"frag": str, "ref": str, "is_target": bool, "f": dict | None,
             "node": "l" | "d", "type": str | None},
            ...
          ],
        }
        or None if the text isn't in our corpus.
    """
    parsed = parse_word_ref(word_ref)
    if parsed is None:
        return None
    project, text_id, line_n, word_n = parsed
    line_ref = f"{text_id}.{line_n}"
    target_ref = f"{line_ref}.{word_n}" if word_n else None

    doc = _load_corpusjson(project, text_id)
    if doc is None:
        return None

    line_label = None
    line_words: list[dict] = []

    for node in _walk_cdl(doc):
        n_type = node.get("node")
        ref = node.get("ref", "")
        if n_type == "d" and node.get("type") == "line-start" and ref == line_ref:
            line_label = node.get("label") or node.get("n") or line_n
        elif ref.startswith(f"{line_ref}.") and n_type in ("l", "d"):
            # words and inline punctuation belonging to this line
            frag = node.get("frag")
            if frag is None:
                continue
            line_words.append({
                "frag": frag,
                "ref": ref,
                "is_target": ref == target_ref,
                "f": node.get("f"),
                "node": n_type,
                "type": node.get("type"),
            })

    if not line_words and not line_label:
        return None  # nothing matched — likely a stale ref

    return {
        "raw_ref": word_ref,
        "project": project,
        "text_id": text_id,
        "line_label": line_label or line_n,
        "line_n": line_n,
        "target_ref": target_ref,
        "words": line_words,
    }


def resolve_many(word_refs: list[str], limit: int | None = None) -> list[dict]:
    """Resolve multiple word_refs, batched-friendly.

    Skips unparseable refs and duplicates within the same (text, line). When
    the same line is referenced multiple times we want to show it once with
    the *first* target marked.
    """
    seen_lines: dict[tuple[str, str, str], dict] = {}
    for ref in word_refs:
        if limit and len(seen_lines) >= limit:
            break
        resolved = resolve_word_ref(ref)
        if resolved is None:
            continue
        key = (resolved["project"], resolved["text_id"], resolved["line_n"])
        if key not in seen_lines:
            seen_lines[key] = resolved
    return list(seen_lines.values())
