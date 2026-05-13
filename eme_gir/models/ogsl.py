"""Response models for the Signs / OGSL MCP tools: cuneify, lookup_sign.

This is the cuneiform rendering surface — sign name ↔ phonetic value ↔
Unicode glyph. Backed by the OGSL (Oracc Global Sign List) which ships
inside `corpus/ogsl.zip`. The underlying renderer in
`eme_gir.cuneify.cuneify()` is also used internally by every server
that needs to surface Unicode glyphs alongside transliterations, so the
library import is the cross-server bridge; this MCP just wraps the
renderer as agent-callable tools.
"""

from __future__ import annotations

from pydantic import Field

from .common import _Permissive


class SignInfo(_Permissive):
    """A cuneiform sign description (lookup_sign)."""

    sign_name: str = Field(..., description="OGSL sign name, e.g. 'LUGAL'.")
    glyph: str | None = Field(None, description="Unicode cuneiform glyph (may be None for unsigned).")
    uname: str | None = Field(None, description="Unicode character name.")
    hex: str | None = Field(None, description="Unicode codepoint in hex.")
    values: list[str] = Field(default_factory=list, description="Phonetic readings, e.g. ['lugal','šarru'].")
    matched_by: str = Field(..., description="What kind of match triggered this hit, e.g. 'sign_name', 'value:lugal'.")


class LookupSignResponse(_Permissive):
    """Response shape for lookup_sign."""

    query: str
    results: list[SignInfo]
    attribution: str = Field(
        ...,
        description=(
            "REQUIRED to display: Oracc CC BY-SA 3.0 attribution string for OGSL "
            "data. The ShareAlike clause propagates to substantial reuses."
        ),
    )


class CuneifyResponse(_Permissive):
    """Response shape for cuneify."""

    spelling: str
    cuneiform: str = Field(..., description="Unicode cuneiform glyphs.")
    complete: bool = Field(
        ...,
        description="True iff every grapheme rendered (no '□' placeholders).",
    )
    placeholder_count: int = Field(
        ..., description="Count of '□' (PLACEHOLDER) characters in the output."
    )
    attribution: str = Field(
        ...,
        description=(
            "REQUIRED to display: Oracc CC BY-SA 3.0 attribution string for OGSL "
            "data. The ShareAlike clause propagates to substantial reuses."
        ),
    )
