"""MCP tools for cuneiform sign rendering (OGSL domain).

Two tool functions:
- `lookup_sign(query, limit)` — sign name ↔ phonetic value ↔ Unicode glyph
- `cuneify(spelling)` — render an Oracc transliteration as Unicode glyphs

Both wrap the underlying shared library `eme_gir.cuneify` (the OGSL
loader + transliteration-to-glyph renderer used internally by every
MCP server that needs to surface Unicode cuneiform alongside lemma
spellings, attestation lines, etc.).

Importing the renderer as a library is the cross-server bridge —
ePSD2's lookup_entry can pre-cuneify its top spellings without needing
to call this MCP server over the wire. This module is just the
agent-callable wrapper.
"""

from __future__ import annotations

import json
import zipfile
from typing import Any

from .. import cuneify as _cuneify
from ..log import log_call
from ..models.common import ErrorResponse
from ..models.ogsl import CuneifyResponse, LookupSignResponse
from ..paths import OGSL_PROMPT_DOC
from ..prompts import load_prompt

# OGSL stores sign names and phonetic values with Unicode subscript
# digits (E₂, gu₇, lu₂). Users commonly type the ASCII-digit form
# (E2, gu7, lu2) carried over from older transliteration conventions.
# Translate the query to OGSL convention before searching so both
# spellings find their sign.
_ASCII_TO_SUBSCRIPT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


@log_call
def lookup_sign(query: str, limit: int = 10) -> LookupSignResponse | ErrorResponse:
    """Look up a cuneiform sign by name (e.g. 'LUGAL', 'E₂') or phonetic
    value (e.g. 'lugal', 'lu₂', 'gal', 'gu₇'), returning the Unicode
    glyph, sign name, Unicode metadata, and all phonetic values that
    map to that sign.

    **Subscript normalization:** ASCII-digit forms like `E2`, `gu7`,
    `lu2` are auto-converted to OGSL's Unicode-subscript convention
    (`E₂`, `gu₇`, `lu₂`) before lookup, so both spellings find their
    sign. The `matched_by` field reflects OGSL's canonical form, not
    the input convention.

    Useful for: verifying which sign a transliteration syllable
    corresponds to; finding all phonetic readings of a logographic
    spelling; looking up a glyph the agent sees in attested text.

    Args:
        query: sign name (uppercase, e.g. 'LUGAL', 'E2') or phonetic
               value (lowercase, e.g. 'lugal', 'e2'). ASCII or Unicode
               subscript digits both work.
        limit: max matches (default 10, cap 30)
    """
    limit = max(1, min(30, int(limit)))
    # The cuneify module caches its lookup dict; warming it here keeps
    # the lookup_sign call fast even on the first invocation.
    _cuneify._load_lookup()

    if not _cuneify.OGSL_ZIP.exists():
        return ErrorResponse(error="OGSL data missing — corpus/ogsl.zip not present")
    with zipfile.ZipFile(_cuneify.OGSL_ZIP) as z, z.open(_cuneify.OGSL_MEMBER) as f:
        signs = json.load(f).get("signs", {})

    # Normalize ASCII digits → Unicode subscripts so users can type
    # 'E2', 'gu7', 'lu2' and still match OGSL's 'E₂', 'gu₇', 'lu₂'.
    needle = query.strip().translate(_ASCII_TO_SUBSCRIPT)
    needle_lower = needle.casefold()
    results: list[dict[str, Any]] = []

    # Direct sign-name match (uppercase keys in signs dict)
    if needle in signs:
        s = signs[needle]
        results.append({
            "sign_name": needle,
            "glyph": s.get("utf8"),
            "uname": s.get("uname"),
            "hex": s.get("hex"),
            "values": s.get("values") or [],
            "matched_by": "sign_name",
        })

    # Value match (search all signs' values)
    for sign_name, s in signs.items():
        if len(results) >= limit:
            break
        for v in s.get("values") or ():
            if v == needle or v.casefold() == needle_lower:
                results.append({
                    "sign_name": sign_name,
                    "glyph": s.get("utf8"),
                    "uname": s.get("uname"),
                    "hex": s.get("hex"),
                    "values": s.get("values") or [],
                    "matched_by": f"value:{v}",
                })
                break

    # Dedupe (a name match might re-appear as a value match)
    seen = set()
    deduped = []
    for r in results:
        key = r["sign_name"]
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return LookupSignResponse(
        query=query,
        results=deduped[:limit],
    )


@log_call
def cuneify(spelling: str) -> CuneifyResponse:
    """Convert an Oracc-style Sumerian transliteration into Unicode cuneiform.

    Handles every spelling pattern in the corpus:
      - hyphen-joined sign sequences:  'lu₂-gal'         -> 𒇽𒃲
      - sign-list dot compounds:        'AB.GAR'
      - braced determinatives:          '{d}lugal'        -> 𒀭𒈗
                                        'lugal{mušen}'    -> 𒈗𒄷
      - whitespace-separated words:     'gu₃ mu-un-de₂'   -> 𒅗 𒈬𒌦…
      - morphology tails (\\X dropped): 'lugal-bi\\a'      -> 𒈗𒁉
      - compound graphemes:             'muₓ(|KA×GAN₂@t|)'-> uses the | … | inner

    Unknown signs render as □ (U+25A1) so the agent sees explicitly which
    parts didn't resolve. Use this as the final step after composing a
    translation, to render it in the script the original would have used.

    Args:
        spelling: transliteration like 'lugal-e e₂ mu-un-du₃'
    """
    glyphs = _cuneify.cuneify(spelling)
    has_placeholder = "□" in glyphs
    return CuneifyResponse(
        spelling=spelling,
        cuneiform=glyphs,
        complete=not has_placeholder,
        placeholder_count=glyphs.count("□"),
    )


@log_call
def start_here() -> str:
    """⭐ CALL THIS FIRST, BEFORE ANY OTHER TOOL ON THIS SERVER.

    Returns the bootstrap prompt for the `eme-gir-ogsl` MCP server.
    Read the returned markdown in full and keep it in working memory
    for the rest of this session — without it, your `cuneify` and
    `lookup_sign` calls will rely on guesswork about Oracc's
    transliteration conventions (which subscripts disambiguate which
    sign, how compound graphemes are written, how determinatives are
    bracketed) and you will misread placeholder squares (□) in
    `cuneify` output as bugs rather than as the documented missing-
    sign signal.

    The prompt covers:
      • The two tools this server exposes (`cuneify`, `lookup_sign`)
        and when each is appropriate.
      • Oracc transliteration conventions handled by `cuneify`:
        hyphen-joined sign sequences (`lu₂-gal`), braced
        determinatives (`{d}inana`, `lugal{mušen}`), morphology
        tails after backslash (`lugal-bi\\a` drops `\\a`), compound
        graphemes with pipes (`muₓ(|KA×GAN₂@t|)`).
      • The subscript-normalization behavior of `lookup_sign`:
        ASCII `gu7` and Unicode `gu₇` both find the sign.
      • Placeholder-square semantics: `□` in `cuneify` output means
        the sign is missing from OGSL — not a bug, but a gap to
        disclose in your reply rather than silently render.
      • This server is reusable beyond Sumerian — OGSL covers
        cuneiform across Akkadian, Hittite, Hurrian, and Elamite.

    Re-call this tool any time your working context drifts and you
    want to re-anchor on this server's guidance.
    """
    return load_prompt(OGSL_PROMPT_DOC)
