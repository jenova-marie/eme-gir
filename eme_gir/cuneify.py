"""Convert Oracc Sumerian transliteration into Unicode cuneiform glyphs.

Loads the Oracc Global Sign List (OGSL) once on first use, builds a
value/name -> glyph lookup, and exposes a Jinja-filter-friendly
`cuneify(spelling)` function.

Tokenization handles:
- compound graphemes via hyphen joiners: 'lu₂-gal' -> ['lu₂', 'gal']
- braced determinatives: '{d}lugal', 'lugal{mušen}', '{id₂}ti'
- multi-word spellings split on whitespace
- morphology tails like 'lugal-bi\\a' (drop after backslash)
- pipe-form compounds: 'muₓ(|KA×GAN₂@t|)' -> use the | ... | inner
- damage / unknown markers: 'x' renders as a placeholder
"""

from __future__ import annotations

import functools
import json
import re
import zipfile

from .paths import OGSL_ZIP

OGSL_MEMBER = "ogsl/ogsl-sl.json"

PLACEHOLDER = "□"          # substituted for unknown signs ('x', missing values)
DET_OPEN, DET_CLOSE = "{", "}"


@functools.lru_cache(maxsize=1)
def _load_lookup() -> dict[str, str]:
    """value-or-sign-name -> first matching utf8 glyph.

    Lowercase keys are phonetic readings (e.g., 'lugal'); uppercase keys are
    sign names (e.g., 'LUGAL'). When a value maps to multiple signs (5.5% of
    cases), the first one wins — accurate enough for visual rendering.
    """
    if not OGSL_ZIP.exists():
        return {}
    with zipfile.ZipFile(OGSL_ZIP) as z, z.open(OGSL_MEMBER) as f:
        doc = json.load(f)
    lookup: dict[str, str] = {}
    for sign_name, sign in doc.get("signs", {}).items():
        glyph = sign.get("utf8")
        if not glyph:
            continue
        lookup.setdefault(sign_name, glyph)               # by sign name (UPPERCASE)
        for value in sign.get("values") or ():            # by phonetic value (lowercase)
            lookup.setdefault(value, glyph)
    return lookup


def _strip_morph_tail(token: str) -> str:
    """'lugal-bi\\a' style: keep what's before the backslash."""
    return token.split("\\", 1)[0]


def _normalize_compound(token: str) -> str:
    """'muₓ(|KA×GAN₂@t|)' -> '|KA×GAN₂@t|' so we look up the explicit form."""
    if "(" in token and token.endswith(")"):
        inner = token[token.index("(") + 1 : -1]
        if inner:
            return inner
    return token


def _lookup_one(token: str) -> str:
    """Resolve a single sign token to a glyph (or PLACEHOLDER)."""
    if not token or token in {"x", "X", "*", "...", "[...]"}:
        return PLACEHOLDER
    token = _strip_morph_tail(token)
    token = _normalize_compound(token)
    lookup = _load_lookup()
    if token in lookup:
        return lookup[token]
    # Try without trailing punctuation (e.g. 'lugal!' -> 'lugal')
    stripped = token.rstrip("?!*")
    if stripped != token and stripped in lookup:
        return lookup[stripped]
    return PLACEHOLDER


# Splits on hyphen-joiners and the dot used for sign-list compounds, but
# preserves whitespace and braces as separators so we can re-tokenize them.
_SIGN_SPLIT = re.compile(r"[-.]")


def _cuneify_word(word: str) -> str:
    """Render one whitespace-delimited segment of a spelling.

    A word can interleave determinatives in braces with sign tokens:
      '{geš}dih₃' -> det 'geš' + token 'dih₃'
      'lugal{mušen}' -> token 'lugal' + det 'mušen'
    We treat each chunk (det or non-det) the same way: split on -/. and look up.
    """
    out: list[str] = []
    i = 0
    while i < len(word):
        ch = word[i]
        if ch == DET_OPEN:
            close = word.find(DET_CLOSE, i + 1)
            if close == -1:
                # malformed brace — render literal placeholder
                out.append(PLACEHOLDER)
                break
            inner = word[i + 1 : close]
            for tok in _SIGN_SPLIT.split(inner):
                if tok:
                    out.append(_lookup_one(tok))
            i = close + 1
        else:
            # Read until next brace
            nxt = word.find(DET_OPEN, i)
            chunk = word[i : nxt if nxt != -1 else len(word)]
            for tok in _SIGN_SPLIT.split(chunk):
                if tok:
                    out.append(_lookup_one(tok))
            i = nxt if nxt != -1 else len(word)
    return "".join(out)


def cuneify(spelling: str | None) -> str:
    """Render a transliteration string as a Unicode cuneiform string.

    Examples:
        cuneify('lugal')              -> '𒈗'
        cuneify('lu₂-gal')            -> '𒇽𒃲'
        cuneify('{d}lugal')           -> '𒀭𒈗'
        cuneify('lugal{mušen}')       -> '𒈗𒄷'
        cuneify('gu₃ mu-un-de₂')      -> '𒅗 𒈬𒌦𒌤'   (space-separated words)
        cuneify('peš₁₀-peš₁₀-e\\l')   -> '𒁁𒁁𒂊'      (drops the \\l morph tail)
    """
    if not spelling:
        return ""
    return " ".join(_cuneify_word(w) for w in spelling.split() if w)
