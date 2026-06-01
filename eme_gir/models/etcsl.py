"""Response models for the ETCSL (Oxford literary corpus) MCP tools.

The ETCSL corpus ships English translations alongside Sumerian lines, so
every hit shape carries both. Every response model also includes an
`attribution` field with the canonical citation string — required under
the CC BY 3.0 UK license. Pass it through to the user verbatim.
"""

from __future__ import annotations

from pydantic import Field

from .common import _Permissive


class ETCSLLine(_Permissive):
    """One line within an ETCSL composition (etcsl_search_english,
    etcsl_lookup_text)."""

    line_id: str | None = Field(None, description="Globally-unique line identifier within the text.")
    line: str | None = Field(None, description="Display label, e.g. '1' or 'A.5'.")
    transliteration: str = Field(..., description="The Sumerian transliteration.")


class ETCSLBlock(_Permissive):
    """One bilingual translation block (etcsl_lookup_text)."""

    paragraph_id: str | None = None
    translation: str | None = Field(None, description="English translation paragraph (None for sections without translation).")
    lines: list[ETCSLLine] = Field(default_factory=list, description="Sumerian lines covered by this paragraph.")


class ETCSLEnglishHit(_Permissive):
    """One hit from etcsl_search_english."""

    text_id: str = Field(..., description="ETCSL composition ID, e.g. 'c.1.4.1'.")
    title: str = Field(..., description="Composition title.")
    line_range: str | None = Field(None, description="Line range covered by this paragraph, e.g. '1-3' or 'B.1-B.5'.")
    translation: str = Field(..., description="The English translation paragraph that matched.")
    sumerian_lines: list[ETCSLLine] = Field(
        default_factory=list, description="The Sumerian lines this paragraph covers."
    )


class ETCSLLemmaHit(_Permissive):
    """One hit from etcsl_lines_with_lemma or etcsl_search_sumerian."""

    text_id: str = Field(..., description="ETCSL composition ID.")
    title: str = Field(..., description="Composition title.")
    line: str = Field(..., description="Display label of the matching line.")
    transliteration: str = Field(..., description="The Sumerian transliteration of this line.")
    translation_paragraph: str | None = Field(
        None, description="The English translation paragraph this line belongs to (None if no translation)."
    )


class ETCSLSearchEnglishResponse(_Permissive):
    """Response shape for etcsl_search_english."""

    query: str
    total_matches: int = Field(0, description="Total paragraphs matching the FTS5 query (may exceed `len(results)` if `limit` clipped).")
    offset: int = Field(0, description="Echo of the request `offset` so the caller knows its place in the result set.")
    next_offset: int | None = Field(
        None,
        description="Pass this back as `offset` on the next call to walk to the next page. `None` means the result set is exhausted.",
    )
    results: list[ETCSLEnglishHit]
    attribution: str = Field(
        ..., description="REQUIRED to display: ETCSL CC BY 3.0 UK attribution string."
    )


class ETCSLLinesWithLemmaResponse(_Permissive):
    """Response shape for etcsl_lines_with_lemma."""

    lemma: str
    total_matches: int = Field(0, description="Total literary lines containing this lemma (may exceed `len(results)` if `limit` clipped).")
    offset: int = Field(0, description="Echo of the request `offset` so the caller knows its place in the result set.")
    next_offset: int | None = Field(
        None,
        description="Pass this back as `offset` on the next call to walk to the next page. `None` means the result set is exhausted.",
    )
    results: list[ETCSLLemmaHit]
    attribution: str = Field(
        ..., description="REQUIRED to display: ETCSL CC BY 3.0 UK attribution string."
    )


class ETCSLLookupTextResponse(_Permissive):
    """Response shape for etcsl_lookup_text."""

    text_id: str
    title: str
    total_lines: int
    returned_lines: int
    start: int = Field(..., description="The 1-based ord the caller requested.")
    last_ord: int | None = Field(None, description="Highest ord in this page (None if no lines returned).")
    next_start: int | None = Field(
        None,
        description="Pass as `start` to fetch the next page (None when at the end of the text).",
    )
    has_translation: bool = Field(..., description="Whether this composition has English translations.")
    blocks: list[ETCSLBlock] = Field(
        ..., description="Bilingual blocks: each translation paragraph + the Sumerian lines it covers."
    )
    attribution: str = Field(
        ..., description="REQUIRED to display: ETCSL CC BY 3.0 UK attribution string."
    )


class ETCSLSearchSumerianResponse(_Permissive):
    """Response shape for etcsl_search_sumerian."""

    query: str
    total_matches: int = Field(0, description="Total Sumerian lines matching the FTS5 query (may exceed `len(results)` if `limit` clipped).")
    offset: int = Field(0, description="Echo of the request `offset` so the caller knows its place in the result set.")
    next_offset: int | None = Field(
        None,
        description="Pass this back as `offset` on the next call to walk to the next page. `None` means the result set is exhausted.",
    )
    results: list[ETCSLLemmaHit]
    attribution: str = Field(
        ..., description="REQUIRED to display: ETCSL CC BY 3.0 UK attribution string."
    )
