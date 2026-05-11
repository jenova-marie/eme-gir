"""Pydantic response models for the MCP tools.

Each model documents the actual JSON shape a tool returns, so FastMCP can
emit an outputSchema in tools/list. Without these, every tool's schema
defaults to a generic `{result: dict[str, Any]}` wrapper that's useless
for LLM reasoning and triggers the "OUTPUT SCHEMA RECOMMENDED" warning
in MCP client UIs.

Conventions:
- Fields use the same NAMES + TYPES as the current dict literals in
  mcp_server.py — these are the source of truth, and the models must
  serialize identically to the legacy dicts so existing clients see no
  change in tool output.
- Each tool may return either its success-shape model OR ErrorResponse
  (e.g., when the requested oid doesn't exist). FastMCP serializes
  Union return types as JSON Schema `anyOf`.
- `ConfigDict(extra="allow")` is set on response models so future
  additions to the dict shape don't immediately break model validation
  for in-flight upgrades.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# ──────────────────────────────────────────────────────────────────
# Shared building blocks
# ──────────────────────────────────────────────────────────────────


class _Permissive(BaseModel):
    """Base for response models — allows extra fields for forward-compat."""

    model_config = ConfigDict(extra="allow")


class ErrorResponse(_Permissive):
    """Standard shape returned by tools when input is invalid or no
    match found. Always check `error` first; success-shape fields will
    be absent."""

    error: str = Field(..., description="Human-readable error message.")
    hint: str | None = Field(
        None,
        description="Optional follow-up suggestion (e.g. 'try translate_english to find the right cf').",
    )


class EntryHeader(_Permissive):
    """Common ePSD2 entry-level fields surfaced across many tool responses."""

    oid: str = Field(..., description="Entry OID, e.g. 'o0033341'. Use with lookup_entry/see_examples/get_inflections.")
    cf: str = Field(..., description="Citation form (Sumerian headword), e.g. 'lugal'.")
    gw: str = Field(..., description="Guide-word / English gloss, e.g. 'king'.")
    pos: str | None = Field(None, description="Part of speech, e.g. 'N' (noun), 'V/t' (transitive verb).")


class LemmaCandidate(EntryHeader):
    """A ranked candidate returned by translate_english."""

    sense: str = Field(..., description="Matching sense / meaning text.")
    sense_count: int = Field(..., description="How often this exact sense is attested.")
    sense_pct: int = Field(..., description="Percentage of the entry's total uses in this sense (0-100).")
    entry_total: int = Field(..., description="Total attestations of the lemma across all senses.")


class Sense(_Permissive):
    """One sense of a polysemous entry (lookup_entry)."""

    id: int | None = None
    meaning: str
    pos: str | None = None
    count: int | None = None
    pct: int | None = None


class Spelling(_Permissive):
    """A spelling variant of a lemma (lookup_entry)."""

    spelling: str = Field(..., description="Transliteration, e.g. 'lugal-e'.")
    count: int = Field(..., description="Attestation count for this spelling.")
    pct: int = Field(..., description="Share of the lemma's total uses (0-100).")
    cuneiform: str = Field(..., description="Unicode cuneiform glyphs.")


class Period(_Permissive):
    """Per-period attestation breakdown (lookup_entry)."""

    period: str = Field(..., description="Historical period, e.g. 'Old Babylonian', 'Ur III'.")
    count: int
    pct: int


class Compound(_Permissive):
    """A see-compound cross-reference (lookup_entry)."""

    compound: str = Field(..., description="The compound expression, e.g. 'a aŋ'.")
    oid: str | None = Field(None, description="OID of the compound's entry, if internally referenced.")


class AttestationLine(_Permissive):
    """A real Sumerian line cited from the corpus (see_examples,
    find_verb_form examples)."""

    text_id: str = Field(..., description="P-id of the cuneiform text, e.g. 'P347156'.")
    project: str = Field(..., description="Oracc project that contains the text.")
    line_label: str = Field(..., description="Display label for the line, e.g. 'o 34'.")
    designation: str | None = Field(None, description="Bibliographic shorthand, e.g. 'YOS 14, 341'.")
    period: str | None = Field(None, description="Historical period of the text.")
    transliteration: str = Field(..., description="The transliterated Sumerian line.")
    target: str | None = Field(None, description="The target word as it appears in this line.")
    target_position: int | None = Field(
        None, description="Zero-indexed position of the target word in the line."
    )


class MorphRow(_Permissive):
    """One morphological breakdown row (get_inflections)."""

    n: str = Field(..., description="The morpheme pattern, e.g. 'mu.na:~' or '~,bi.a'.")
    count: int
    pct: int
    xis: str | None = None


class AnalyzeMatch(_Permissive):
    """One candidate decomposition for a Sumerian spelling (analyze_form)."""

    matched_in: str = Field(..., description="Which table/index hit, e.g. 'forms', 'morphology.base'.")
    oid: str
    cf: str
    gw: str
    pos: str | None = None
    matched_text: str = Field(..., description="The literal text from the matched row.")
    count: int
    pct: int
    xis: str | None = None


class TokenAnalysis(_Permissive):
    """One token's per-candidate breakdown from translate_sumerian."""

    token: str = Field(..., description="The transliteration token analyzed (e.g. 'lugal').")
    candidates: list[EntryHeader] = Field(
        default_factory=list,
        description="Candidate lemmas for this token, ranked by entry total. Each carries oid/cf/gw/pos plus entry_total.",
    )


# Re-use EntryHeader and add entry_total for translate_sumerian candidates
class TokenCandidate(EntryHeader):
    entry_total: int = Field(..., description="Total attestations across all senses of this candidate.")


class CollocationHit(_Permissive):
    """One n-gram collocation row (find_collocations)."""

    n: int = Field(..., description="N-gram length: 2, 3, or 4.")
    ngram: str = Field(..., description="Space-joined citation forms forming the n-gram.")
    count: int = Field(..., description="Times the n-gram appeared in the corpus.")


class SignInfo(_Permissive):
    """A cuneiform sign description (lookup_sign)."""

    sign_name: str = Field(..., description="OGSL sign name, e.g. 'LUGAL'.")
    glyph: str | None = Field(None, description="Unicode cuneiform glyph (may be None for unsigned).")
    uname: str | None = Field(None, description="Unicode character name.")
    hex: str | None = Field(None, description="Unicode codepoint in hex.")
    values: list[str] = Field(default_factory=list, description="Phonetic readings, e.g. ['lugal','šarru'].")
    matched_by: str = Field(..., description="What kind of match triggered this hit, e.g. 'sign_name', 'value:lugal'.")


class VerbFormFilterSpec(_Permissive):
    """Echo of the filter the caller supplied to find_verb_form."""

    prefix: str | None = None
    polarity: str | None = None
    object_person: str | None = None
    dimensional: list[str] = Field(default_factory=list)
    aspect: str | None = None
    suffix_a: bool | None = None
    reduplicated: bool | None = None


class VerbFormMatch(_Permissive):
    """One attested verb form returned by find_verb_form."""

    morph: str = Field(..., description="Morpheme pattern from the morphology table.")
    spelling: str = Field(..., description="Best surface spelling (real if attested, else synthesized).")
    synthesized_spelling: str = Field(..., description="The mechanically-built spelling from morpheme tokens.")
    verified_in_forms: bool = Field(
        ..., description="True iff the synthesized spelling matches a row in the forms table."
    )
    count: int = Field(..., description="Attestation count for this morph row.")
    share_pct: float = Field(..., description="Share of the entry's total attestations (0-100).")
    forms_table_count: int = Field(..., description="Attestation count from the matching forms-table row.")
    cuneiform: str = Field(..., description="Unicode cuneiform glyphs for the spelling.")
    example: AttestationLine | None = Field(
        None, description="One cited corpus line showing this form in real use."
    )


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


# ──────────────────────────────────────────────────────────────────
# Tool response models
# ──────────────────────────────────────────────────────────────────


class TranslateEnglishResponse(_Permissive):
    """Response shape for translate_english."""

    query: str
    total_matches: int = Field(..., description="Total entries that matched (may exceed `len(results)` if `limit` clipped).")
    results: list[LemmaCandidate]


class LookupEntryResponse(_Permissive):
    """Response shape for lookup_entry."""

    oid: str
    cf: str
    gw: str
    pos: str | None = None
    headword: str = Field(..., description="Full headword string, e.g. 'lugal[king]N'.")
    total_count: int = Field(..., description="Total attestations of this lemma across all senses.")
    senses: list[Sense]
    spellings: list[Spelling] = Field(..., description="Top spellings ranked by attestation count (capped at 25).")
    periods: list[Period]
    compounds: list[Compound] = Field(
        ..., description="See-compounds: idiomatic compounds containing this word."
    )


class SeeExamplesResponse(_Permissive):
    """Response shape for see_examples."""

    oid: str
    cf: str | None = None
    gw: str | None = None
    period_filter: str | None = None
    lines: list[AttestationLine] = Field(
        ..., description="Real attested lines with the target word marked."
    )
    note: str | None = None
    diagnostic: str | None = None


class FindCompoundResponse(_Permissive):
    """Response shape for find_compound."""

    query: str
    total_matches: int
    results: list[dict] = Field(
        ...,
        description="Compound-entry rows. Each row carries: id, headword, cf, gw, pos, icount, ipct, plus internal indexing columns.",
    )


class GetInflectionsResponse(_Permissive):
    """Response shape for get_inflections."""

    oid: str
    cf: str
    gw: str
    pos: str | None = None
    morphology: dict[str, list[MorphRow]] = Field(
        ...,
        description="Morphological breakdowns keyed by kind: 'base', 'morph', 'morph2', 'stem', 'prefix', 'form-sans'.",
    )
    kinds: list[str] = Field(..., description="Sorted list of populated morphology kinds.")
    truncated: dict[str, str] = Field(
        ...,
        description="Per-kind truncation note, only present where filtering removed rows.",
    )
    filters: dict = Field(..., description="Echo of {min_count, limit_per_kind} the caller used.")


class AnalyzeFormResponse(_Permissive):
    """Response shape for analyze_form."""

    spelling: str
    matches: list[AnalyzeMatch] = Field(
        ..., description="Candidate decompositions, ranked by attestation count."
    )


class TranslateSumerianResponse(_Permissive):
    """Response shape for translate_sumerian."""

    transliteration: str
    tokens: list[TokenAnalysis] = Field(
        ..., description="Per-token candidate analyses, in input order."
    )


class FindCollocationsResponse(_Permissive):
    """Response shape for find_collocations."""

    word: str = Field(..., description="The word looked up (after any cf-resolution).")
    word_unigram_count: int = Field(..., description="Unigram count for `word` in the corpus.")
    results: list[CollocationHit]
    resolved_from: str | None = Field(
        None, description="If the input was a spelling resolved to a citation form, the original input."
    )
    note: str | None = Field(
        None, description="Diagnostic note (only present when resolved_from is set)."
    )


class LookupSignResponse(_Permissive):
    """Response shape for lookup_sign."""

    query: str
    results: list[SignInfo]


class FindVerbFormResponse(_Permissive):
    """Response shape for find_verb_form."""

    cf: str
    pos: str
    gw: str
    entry_oid: str
    base: str | None = Field(None, description="The base morpheme used in the morph rows.")
    total_attestations_for_entry: int
    candidates_scanned: int = Field(..., description="How many morph rows were considered before filtering.")
    filter_spec: VerbFormFilterSpec = Field(..., description="Echo of the filter spec the caller supplied.")
    matches: list[VerbFormMatch]
    warnings: list[str] = Field(default_factory=list, description="Free-text caveats about the result.")


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


class ETCSLSearchEnglishResponse(_Permissive):
    """Response shape for etcsl_search_english."""

    query: str
    results: list[ETCSLEnglishHit]
    attribution: str = Field(
        ..., description="REQUIRED to display: ETCSL CC BY 3.0 UK attribution string."
    )


class ETCSLLinesWithLemmaResponse(_Permissive):
    """Response shape for etcsl_lines_with_lemma."""

    lemma: str
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
    results: list[ETCSLLemmaHit]
    attribution: str = Field(
        ..., description="REQUIRED to display: ETCSL CC BY 3.0 UK attribution string."
    )
