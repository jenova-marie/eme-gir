"""Response models for the ETCSL (Oxford literary corpus) MCP tools.

The ETCSL corpus ships English translations alongside Sumerian lines, so
every hit shape carries both. Every response model also includes an
`attribution` field with the canonical citation string. ETCSL is NOT
released under any Creative Commons license — it carries traditional
academic copyright (© Black, Cunningham, Robson, Zólyomi 1998-2006) with a
required citation. Pass the attribution through to the user verbatim.
"""

from __future__ import annotations

from pydantic import Field

from ..attribution import ETCSL_CITATION_SHORT, ETCSL_PRESENTATION
from .common import _Permissive

_ETCSL_ATTRIBUTION_DESC = (
    "REQUIRED to display: ETCSL citation string. ETCSL is NOT under any "
    "Creative Commons license; the citation is a condition of use."
)

_ETCSL_DISPLAY_DESC = (
    "Pre-composed bilingual block with the ETCSL citation fused in; relay "
    "verbatim to the user."
)


class _ETCSLResponse(_Permissive):
    """Base for every ETCSL tool response — carries the always-present
    short citation + point-of-use presentation imperative (defaults baked
    in) so the citation survives synthesis in generic chat clients."""

    citation_short: str = Field(default=ETCSL_CITATION_SHORT, description="Short ETCSL citation; reproduce verbatim in a Sources section.")
    presentation: str = Field(default=ETCSL_PRESENTATION, description="Point-of-use attribution instruction; ETCSL's display condition.")


class ETCSLLine(_Permissive):
    """One line within an ETCSL composition (etcsl_search_english,
    etcsl_lookup_text)."""

    line_id: str | None = Field(None, description="Globally-unique line identifier within the text.")
    line: str | None = Field(None, description="Display label, e.g. '1' or 'A.5'.")
    transliteration: str = Field(..., description="The Sumerian transliteration.")
    display_markdown: str | None = Field(None, description=_ETCSL_DISPLAY_DESC)


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
    display_markdown: str | None = Field(None, description=_ETCSL_DISPLAY_DESC)


class ETCSLLemmaHit(_Permissive):
    """One hit from etcsl_lines_with_lemma or etcsl_search_sumerian."""

    text_id: str = Field(..., description="ETCSL composition ID.")
    title: str = Field(..., description="Composition title.")
    line: str = Field(..., description="Display label of the matching line.")
    transliteration: str = Field(..., description="The Sumerian transliteration of this line.")
    translation_paragraph: str | None = Field(
        None, description="The English translation paragraph this line belongs to (None if no translation)."
    )
    display_markdown: str | None = Field(None, description=_ETCSL_DISPLAY_DESC)


class ETCSLSearchEnglishResponse(_ETCSLResponse):
    """Response shape for etcsl_search_english."""

    query: str
    total_matches: int = Field(0, description="Total paragraphs matching the FTS5 query (may exceed `len(results)` if `limit` clipped).")
    offset: int = Field(0, description="Echo of the request `offset` so the caller knows its place in the result set.")
    next_offset: int | None = Field(
        None,
        description="Pass this back as `offset` on the next call to walk to the next page. `None` means the result set is exhausted.",
    )
    results: list[ETCSLEnglishHit]
    attribution: str = Field(..., description=_ETCSL_ATTRIBUTION_DESC)


class ETCSLLinesWithLemmaResponse(_ETCSLResponse):
    """Response shape for etcsl_lines_with_lemma."""

    lemma: str
    total_matches: int = Field(0, description="Total literary lines containing this lemma (may exceed `len(results)` if `limit` clipped).")
    offset: int = Field(0, description="Echo of the request `offset` so the caller knows its place in the result set.")
    next_offset: int | None = Field(
        None,
        description="Pass this back as `offset` on the next call to walk to the next page. `None` means the result set is exhausted.",
    )
    results: list[ETCSLLemmaHit]
    attribution: str = Field(..., description=_ETCSL_ATTRIBUTION_DESC)


class ETCSLLookupTextResponse(_ETCSLResponse):
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
    attribution: str = Field(..., description=_ETCSL_ATTRIBUTION_DESC)


class ETCSLSearchSumerianResponse(_ETCSLResponse):
    """Response shape for etcsl_search_sumerian."""

    query: str
    total_matches: int = Field(0, description="Total Sumerian lines matching the FTS5 query (may exceed `len(results)` if `limit` clipped).")
    offset: int = Field(0, description="Echo of the request `offset` so the caller knows its place in the result set.")
    next_offset: int | None = Field(
        None,
        description="Pass this back as `offset` on the next call to walk to the next page. `None` means the result set is exhausted.",
    )
    results: list[ETCSLLemmaHit]
    attribution: str = Field(..., description=_ETCSL_ATTRIBUTION_DESC)
