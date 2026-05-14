"""Shared Pydantic building blocks for the MCP tool response models.

These types are referenced across multiple per-domain submodules:
- `_Permissive` is the base class for every response model in the package.
- `ErrorResponse` is the canonical error shape every tool may return as
  part of its `success_model | ErrorResponse` Union.
- `EntryHeader`, `AttestationLine`, `Suffix` are shapes that span at least
  two domains (ePSD2 + CDLI enrichment on attestations; ePSD2's translate
  vs parse_phrase sharing the Suffix shape).

Conventions:
- Fields use the same NAMES + TYPES as the legacy dict literals in
  mcp_server.py so the models serialize identically to the pre-refactor
  output.
- `ConfigDict(extra="allow")` is set on every response model so future
  additions to the dict shape don't break in-flight upgrades.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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
    """Common Eme-gir entry-level fields surfaced across many tool responses."""

    oid: str = Field(..., description="Entry OID, e.g. 'o0033341'. Use with lookup_entry/see_examples/get_inflections.")
    cf: str = Field(..., description="Citation form (Sumerian headword), e.g. 'lugal'.")
    # NULL for ~7% of entries (1,123/15,940) — typically proper-noun-only
    # entries (DN, PN, GN) where Oracc has no English gloss to give.
    gw: str | None = Field(None, description="Guide-word / English gloss, e.g. 'king'. None for proper nouns and other entries with no gloss.")
    pos: str | None = Field(None, description="Part of speech, e.g. 'N' (noun), 'V/t' (transitive verb).")


class AttestationLine(_Permissive):
    """A real Sumerian line cited from the corpus (see_examples,
    find_verb_form examples).

    Lives in `common` rather than `epsd2` because CDLI enrichment fields
    (cdli_url, photo_url, lineart_url, museum_*, etc.) are auto-populated
    onto every cited line by the resolver, so this is the cross-domain
    bridge between the ePSD2 attestation pipeline and the CDLI catalogue.
    """

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
    # CDLI enrichment — populated when the artifact appears in our
    # cdli.sqlite catalogue. Lets the agent offer "see the actual tablet"
    # links to the user. None when CDLI doesn't know the artifact OR the
    # corresponding image flag is false in CDLI's catalogue.
    cdli_url: str | None = Field(
        None,
        description="CDLI artifact page URL (always set when CDLI knows the P-id).",
    )
    photo_url: str | None = Field(
        None, description="High-res photograph (None if CDLI has no photo)."
    )
    photo_thumb_url: str | None = Field(
        None, description="Thumbnail photograph for inline display."
    )
    lineart_url: str | None = Field(
        None, description="High-res line drawing (None if CDLI has none)."
    )
    lineart_thumb_url: str | None = Field(
        None, description="Thumbnail line drawing."
    )
    museum_collection: str | None = Field(
        None, description="Holding institution per CDLI, e.g. 'British Museum, London, UK'."
    )
    museum_no: str | None = Field(
        None, description="Museum catalog number, e.g. 'BM 103437'."
    )


class Suffix(_Permissive):
    """One detected grammatical suffix on a Sumerian token.

    Shared sub-shape used by both translate_sumerian (per-token annotation)
    and parse_phrase (per-chunk role labeling). The suffix table that
    produces these is documented in eme_gir/sumerian_morphology.py
    SUMERIAN_SUFFIX_TABLE and mirrors §3 + §5.2 of
    lessons/JAGERSMA_GRAMMAR.md.

    Some suffixes are AMBIGUOUS by surface form alone — most famously `-e`
    (ergative on a noun OR directive case OR 3sg ergative verbal agreement)
    and `-a` (locative on a noun OR nominalizer on a verb). The `role` field
    reports the lexicographically most-likely interpretation given the head
    POS, and `ambiguous_with` lists the other plausible readings the agent
    should consider before committing.
    """

    spelling: str = Field(..., description="The surface form of the suffix, e.g. '-e', '-ra', '-gin₇'.")
    role: str = Field(..., description="Grammatical role: 'ergative', 'dative', 'locative', 'comitative', 'ablative_instrumental', 'terminative', 'directive', 'equative', 'genitive', 'plural', '1sg_possessive', '3sg_h_possessive', '3sg_nh_possessive_or_anaphoric', etc.")
    kind: str = Field(..., description="Suffix family: 'case', 'possessive', 'plural', or 'verbal_agreement'.")
    ambiguous_with: list[str] = Field(
        default_factory=list,
        description="Other roles this surface form could carry. Empty for unambiguous suffixes.",
    )
