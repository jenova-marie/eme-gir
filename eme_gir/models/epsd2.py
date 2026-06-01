"""Response models for the ePSD2 (Eme-gir dictionary + corpus) MCP tools.

Tools whose response shapes live here:
- translate_english, translate_sumerian, parse_phrase
- lookup_entry, see_examples, find_compound
- find_collocations, find_phrase_pattern
- get_inflections, analyze_form, find_verb_form

Cross-domain references go through `eme_gir.models.common`:
- `EntryHeader` for shared entry-level fields
- `AttestationLine` for cited corpus lines (also carries CDLI enrichment)
- `Suffix` for the suffix-peeler output (shared with parse_phrase)
"""

from __future__ import annotations

from pydantic import Field

from .common import _Permissive, AttestationLine, EntryHeader, Suffix


# ──────────────────────────────────────────────────────────────────
# Sub-shapes
# ──────────────────────────────────────────────────────────────────


class LemmaCandidate(EntryHeader):
    """A ranked candidate returned by translate_english."""

    sense: str = Field(..., description="Matching sense / meaning text.")
    sense_count: int = Field(..., description="How often this exact sense is attested.")
    sense_pct: int = Field(..., description="Percentage of the entry's total uses in this sense (0-100).")
    entry_total: int = Field(..., description="Total attestations of the lemma across all senses.")


class Sense(_Permissive):
    """One sense of a polysemous entry (lookup_entry)."""

    # Oracc sense IDs are TEXT in the source data (e.g. 'sux.x00459199'),
    # NOT integers. The earlier int typing here rejected entries like
    # 'dilibad' with a Pydantic ValidationError mid-tool-call.
    id: str | None = None
    # ~6% of senses (1,111/19,066) have NULL meaning — typically
    # proper-noun-only entries where the sense exists but the gloss
    # is empty in Oracc's source data.
    meaning: str | None = None
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
    gw: str | None = None
    pos: str | None = None
    matched_text: str = Field(..., description="The literal text from the matched row.")
    count: int
    pct: int
    xis: str | None = None


class TokenAnalysis(_Permissive):
    """One token's per-candidate breakdown from translate_sumerian.

    `match_kind` signals HOW the lookup resolved:
      - "whole"          : the input token was found as-is in forms / morphology
                            / entries.cf — this is the lexicographer-blessed
                            reading and the agent should prefer it.
      - "split_fallback" : the whole token had no match, so the parser fell
                            back to splitting on hyphens/dots; this entry
                            represents one PIECE of that split. `from_word`
                            names the original hyphenated token so the agent
                            can re-assemble context.
      - "unmatched"      : neither whole nor any split piece resolved (no
                            candidates returned).

    `base` and `suffixes` are produced by the suffix-peeling pass. They're
    omitted when no suffix was detected (the token is its own base, like
    'e₂' or 'lugal'). When present, `base` is the head morpheme (which the
    `candidates` list now reflects) and `suffixes` is the LEFT-TO-RIGHT
    chain of attached grammatical morphemes, e.g. for 'lugal-ŋu₁₀-ra':
        base='lugal', suffixes=[1sg_possessive, dative].
    """

    token: str = Field(..., description="The transliteration token analyzed (e.g. 'lugal' or 'mu-un-du₃').")
    candidates: list[EntryHeader] = Field(
        default_factory=list,
        description="Candidate lemmas for this token, ranked by entry total. Each carries oid/cf/gw/pos plus entry_total.",
    )
    match_kind: str = Field(
        default="whole",
        description="How this entry was resolved: 'whole' (token matched as-is), 'split_fallback' (whole-token lookup failed; this is a hyphen-split piece), or 'unmatched' (no candidates anywhere).",
    )
    from_word: str | None = Field(
        default=None,
        description="When match_kind='split_fallback', the original hyphenated word this piece came from. None otherwise.",
    )
    base: str | None = Field(
        default=None,
        description="The base morpheme after stripping any detected case/possessive/plural suffixes. None when no suffix was detected (the token IS its own base).",
    )
    suffixes: list[Suffix] = Field(
        default_factory=list,
        description="Left-to-right chain of grammatical morphemes peeled off the token's right edge. Empty when no suffixes detected.",
    )


class CaseChunk(_Permissive):
    """One token chunked by the case-aware phrase parser (parse_phrase).

    Goes beyond TokenAnalysis by classifying the token's syntactic role
    in a phrase: noun (potentially case-bearing) vs adjective (modifier
    of preceding head) vs verb form (with prefix chain, clause-closing).
    This isn't a true syntactic parse — it's a morphology-driven
    pre-annotation that gives the LLM clear anchor points for the actual
    parsing reasoning.
    """

    token: str = Field(..., description="The transliteration token as it appeared in the input (e.g. 'lugal-e').")
    base: str | None = Field(None, description="Base morpheme after suffix-peeling. None when no suffix was detected.")
    suffixes: list[Suffix] = Field(
        default_factory=list,
        description="Detected suffix chain, left-to-right. Empty when no suffixes detected (e.g. an absolutive noun or a bare verb).",
    )
    candidates: list[EntryHeader] = Field(
        default_factory=list,
        description="Lemma candidates for the base, ranked by entry total.",
    )
    pos_head: str | None = Field(
        None,
        description="POS of the top-ranked candidate, e.g. 'N', 'V/t', 'AJ'. Drives phrase-boundary inference.",
    )
    is_verb_form: bool = Field(
        default=False,
        description="True when the top candidate is a verb (V/t, V/i, V) — signals this token is a verbal head, not a nominal phrase, and case-suffix peeling was skipped.",
    )
    verbal_prefixes: str | None = Field(
        None,
        description="When is_verb_form=True, the prefix chain detected before the verb root (e.g. 'mu-na' in 'mu-na-du₃'). None otherwise.",
    )
    role: str = Field(
        ...,
        description="Inferred phrase role: 'subject_ergative', 'object_absolutive', 'oblique_dative', 'oblique_locative', 'oblique_comitative', 'oblique_ablative', 'oblique_terminative', 'comparison_equative', 'genitive_modifier', 'adjective_modifier', 'verb_head', 'noun_head_unmarked', or 'unknown'.",
    )
    phrase_boundary_after: bool = Field(
        ...,
        description="Heuristic flag: a case-bearing noun, an absolutive object, or a verb head typically closes a phrase. The agent uses this to chunk the input into clause/phrase units.",
    )


# Re-use EntryHeader and add entry_total for translate_sumerian candidates
class TokenCandidate(EntryHeader):
    entry_total: int = Field(..., description="Total attestations across all senses of this candidate.")


class CollocationHit(_Permissive):
    """One n-gram collocation row (find_collocations)."""

    n: int = Field(..., description="N-gram length: 2, 3, or 4.")
    ngram: str = Field(..., description="Space-joined citation forms forming the n-gram.")
    count: int = Field(..., description="Times the n-gram appeared in the corpus.")


class PatternToken(_Permissive):
    """One annotated token within a corpus-attested phrase pattern match.

    Returned as part of `PhrasePatternHit.tokens` — gives the agent each
    n-gram slot's citation form alongside the entry-level POS + gloss
    + (when the inflected-collocations index is in use) the detected case
    marker, so the structural fit of the pattern is visible at a glance.
    """

    cf: str = Field(..., description="The citation form at this slot in the matched n-gram.")
    pos: str | None = Field(None, description="Part of speech of the matching lemma, e.g. 'N', 'V/t', 'RN'.")
    gw: str | None = Field(None, description="English guide-word / gloss of the matching lemma.")
    case: str | None = Field(
        None,
        description=(
            "Detected outermost case suffix role from the inflected-"
            "collocations index, e.g. 'ergative', 'dative', 'locative', "
            "'equative'. None means zero-marked (absolutive — no overt "
            "case suffix on the visible spelling). All rows in one "
            "response come from the same index, so a null `case` within "
            "a response is NOT a signal that the legacy cf-only index was "
            "used as fallback — that fallback only kicks in when the "
            "entire inflected-collocations DB is absent, in which case "
            "the WHOLE response carries null cases."
        ),
    )


class PhrasePatternHit(_Permissive):
    """One attested n-gram match from find_phrase_pattern."""

    ngram: str = Field(..., description="Space-joined citation forms forming the n-gram, e.g. 'Šusuen lugal'.")
    count: int = Field(..., description="Times this exact n-gram was attested in the corpus.")
    tokens: list[PatternToken] = Field(
        ..., description="Per-slot annotation matching the input pattern positionally."
    )


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
    # None when the synthesized spelling doesn't match a forms-table row
    # exactly — common, because Sumerian phonology fills in vowels that
    # the morph-token concatenation can't synthesize (e.g. `mu.n:~` for
    # `du₃` synthesizes `mu-n-du₃` but the attested form is `mu-un-du₃`).
    # The `count` field is authoritative regardless; `forms_table_count`
    # is just the optional secondary-confirmation signal from forms.n.
    forms_table_count: int | None = Field(
        None,
        description=(
            "Attestation count from the matching forms-table row; "
            "None when the synthesized spelling doesn't exactly match a "
            "forms-table row (common, because the morph synthesis doesn't "
            "fill in vowels that Sumerian phonology requires)."
        ),
    )
    cuneiform: str = Field(..., description="Unicode cuneiform glyphs for the spelling.")
    example: AttestationLine | None = Field(
        None, description="One cited corpus line showing this form in real use."
    )


# ──────────────────────────────────────────────────────────────────
# Tool response models
# ──────────────────────────────────────────────────────────────────


# Shared description for the `attribution` field added to every ePSD2
# response. Oracc data (including ePSD2 and OGSL) is licensed CC BY-SA 3.0
# Unported, so attribution is REQUIRED on every quotation and the
# ShareAlike clause propagates to substantial reuses. The tool layer
# sets this via EPSD2_ATTRIBUTION; agents must pass it through verbatim.
_ATTRIBUTION_DESC = (
    "REQUIRED to display: Oracc CC BY-SA 3.0 attribution string for ePSD2 "
    "data. The ShareAlike clause propagates to substantial reuses."
)


class TranslateEnglishResponse(_Permissive):
    """Response shape for translate_english."""

    query: str
    total_matches: int = Field(..., description="Total entries that matched (may exceed `len(results)` if `limit` clipped).")
    offset: int = Field(0, description="Echo of the request `offset` so the caller knows its place in the result set.")
    next_offset: int | None = Field(
        None,
        description="Pass this back as `offset` on the next call to walk to the next page. `None` means the result set is exhausted.",
    )
    results: list[LemmaCandidate]
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


class LookupEntryResponse(_Permissive):
    """Response shape for lookup_entry."""

    oid: str
    cf: str
    gw: str | None = None
    pos: str | None = None
    headword: str = Field(..., description="Full headword string, e.g. 'lugal[king]N'.")
    total_count: int = Field(..., description="Total attestations of this lemma across all senses.")
    senses: list[Sense]
    spellings: list[Spelling] = Field(..., description="Top spellings ranked by attestation count (capped at 25).")
    periods: list[Period]
    compounds: list[Compound] = Field(
        ..., description="See-compounds: idiomatic compounds containing this word."
    )
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


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
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


class FindCompoundResponse(_Permissive):
    """Response shape for find_compound."""

    query: str
    total_matches: int
    results: list[dict] = Field(
        ...,
        description="Compound-entry rows. Each row carries: id, headword, cf, gw, pos, icount, ipct, plus internal indexing columns.",
    )
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


class GetInflectionsResponse(_Permissive):
    """Response shape for get_inflections."""

    oid: str
    cf: str
    gw: str | None = None
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
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


class AnalyzeFormResponse(_Permissive):
    """Response shape for analyze_form."""

    spelling: str
    matches: list[AnalyzeMatch] = Field(
        ..., description="Candidate decompositions, ranked by attestation count."
    )
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


class TranslateSumerianResponse(_Permissive):
    """Response shape for translate_sumerian."""

    transliteration: str
    tokens: list[TokenAnalysis] = Field(
        ..., description="Per-token candidate analyses, in input order."
    )
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


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
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


class FindPhrasePatternResponse(_Permissive):
    """Response shape for find_phrase_pattern.

    Filters the corpus-mined collocation index by a structural template
    where each slot is either a specific citation form, a POS code (e.g.
    'N', 'V/t', 'V*' for any verb), or '*' for any cf. Results are
    attested n-grams that match positionally, ranked by corpus frequency.

    Caveat: the underlying index is keyed by CITATION FORM, not by
    inflected form, so this tool cannot filter by case marker (e.g.
    'N-locative + V'). For that level of structural detail use
    parse_phrase on a specific input phrase instead.
    """

    pattern: list[str] = Field(..., description="The pattern the caller supplied, echoed back.")
    n: int = Field(..., description="Length of the pattern: 2, 3, or 4.")
    total_matches: int = Field(
        ..., description="Total n-grams in the index that matched the pattern (may exceed len(results) if limit clipped)."
    )
    offset: int = Field(0, description="Echo of the request `offset` so the caller knows its place in the result set.")
    next_offset: int | None = Field(
        None,
        description="Pass this back as `offset` on the next call to walk to the next page. `None` means the result set is exhausted.",
    )
    results: list[PhrasePatternHit] = Field(
        ..., description="Attested n-grams matching the pattern, ranked by corpus frequency."
    )
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


class FindVerbFormResponse(_Permissive):
    """Response shape for find_verb_form."""

    cf: str
    pos: str
    gw: str | None = None
    entry_oid: str
    base: str | None = Field(None, description="The base morpheme used in the morph rows.")
    total_attestations_for_entry: int
    candidates_scanned: int = Field(..., description="How many morph rows were considered before filtering.")
    filter_spec: VerbFormFilterSpec = Field(..., description="Echo of the filter spec the caller supplied.")
    matches: list[VerbFormMatch]
    warnings: list[str] = Field(default_factory=list, description="Free-text caveats about the result.")
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)


class ParsePhraseResponse(_Permissive):
    """Response shape for parse_phrase.

    Provides a case-aware, morphology-driven pre-annotation of a Sumerian
    phrase so the LLM can do final syntactic reasoning with explicit anchor
    points instead of inferring everything from raw token glosses. NOT a
    true parser — it does not produce a constituency or dependency tree
    and makes no claim about phrase-attachment. It surfaces the grammatical
    role-markers that ARE in the morphology and lets the agent build the
    parse on top.
    """

    transliteration: str = Field(..., description="The input phrase, echoed back.")
    chunks: list[CaseChunk] = Field(..., description="Per-token chunks in input order.")
    skeleton: str = Field(
        ...,
        description="Compact bracket notation summarizing the phrase, e.g. '[NP lugal-ERG] [NP e₂-ABS] [V du₃ (mu-na-)]'. Read this first for an at-a-glance structural overview.",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Heuristic remarks the parser noticed, e.g. 'ergative subject + absolutive object + transitive verb → transitive clause'. Empty when no patterns matched.",
    )
    attribution: str = Field(..., description=_ATTRIBUTION_DESC)
