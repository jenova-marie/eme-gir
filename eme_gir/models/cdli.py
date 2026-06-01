"""Response models for the CDLI (Cuneiform Digital Library Initiative)
artifact-catalogue MCP tools: lookup_artifact, find_artifacts.

CDLI's catalogue is CC0 — attribution isn't legally required, but the
attribution string is still passed through for consistency with the
ETCSL pattern and because crediting CDLI is good practice.

All image URLs (`photo_url`, `lineart_url`, plus thumbnails) point
directly to cdli.earth — we host no imagery ourselves. The same fields
are also auto-splatted onto `AttestationLine` in `common.py` by the
ePSD2 see_examples / find_verb_form pipelines.
"""

from __future__ import annotations

from pydantic import Field

from .common import _Permissive


class CDLIArtifact(_Permissive):
    """One artifact's full CDLI catalogue record + computed image links.

    Returned by lookup_artifact (one record) and find_artifacts (a list).
    Most fields are nullable because CDLI's catalogue is sparse — only
    well-published artifacts have every column populated.
    """

    p_id: str = Field(..., description="Canonical P-id, e.g. 'P347156'. Use as the key for cross-references with Oracc texts.")
    cdli_id: int = Field(..., description="Bare integer id used in cdli.earth URL paths.")
    cdli_url: str = Field(..., description="Browser-facing CDLI artifact page (always present).")
    photo_url: str | None = Field(None, description="High-res photograph (None when CDLI has no photo for this artifact).")
    photo_thumb_url: str | None = Field(None, description="Photograph thumbnail for inline display.")
    lineart_url: str | None = Field(None, description="High-res line drawing (None when CDLI has none).")
    lineart_thumb_url: str | None = Field(None, description="Line drawing thumbnail.")
    has_photo: bool = Field(..., description="Whether CDLI has a photograph available.")
    has_lineart: bool = Field(..., description="Whether CDLI has a line drawing available.")

    # Citation / publication
    designation: str | None = Field(None, description="Bibliographic shorthand, e.g. 'YOS 14, 341'.")
    primary_publication: str | None = Field(None, description="Where the text was first published.")
    publication_history: str | None = Field(None, description="Full publication chronology.")
    citation: str | None = Field(None, description="CDLI's recommended citation string.")
    composite_id: str | None = Field(None, description="Q-id reference if part of a composite reconstruction.")

    # Period + dating
    period: str | None = Field(None, description="Historical period with dates, e.g. 'Ur III (ca. 2100-2000 BC)'.")
    period_remarks: str | None = Field(None, description="Caveats or refinements on the period assignment.")
    accounting_period: str | None = Field(None, description="For Ur III administrative texts: the year-name period.")
    dates_referenced: str | None = Field(None, description="Specific dates mentioned in the text (Šulgi yr X, etc.).")

    # Provenience (find context)
    provenience: str | None = Field(None, description="Find spot, e.g. 'Drehem (mod. Puzriš-Dagan)'.")
    provenience_remarks: str | None = Field(None, description="Notes on certainty / circumstances of the find.")
    findspot_remarks: str | None = Field(None, description="Excavator's notes on the immediate find context.")
    findspot_square: str | None = Field(None, description="Excavation grid reference.")
    excavation_no: str | None = Field(None, description="Excavator's field number, e.g. 'W 06435,a'.")

    # Custody (museum)
    museum_collection: str | None = Field(None, description="Holding institution, e.g. 'British Museum, London, UK'.")
    museum_no: str | None = Field(None, description="Museum catalog number, e.g. 'BM 103437'.")
    accession_no: str | None = Field(None, description="Museum accession number.")

    # Classification
    genre: str | None = Field(None, description="Text genre, e.g. 'Administrative', 'Lexical', 'Literary'.")
    subgenre: str | None = Field(None, description="Finer classification within the genre.")
    language: str | None = Field(None, description="Sumerian / Akkadian / Hittite / undetermined / etc.")
    material: str | None = Field(None, description="Physical material, e.g. 'clay', 'stone'.")
    object_type: str | None = Field(None, description="Tablet / cone / cylinder / brick / etc.")

    # Physical
    height: str | None = Field(None, description="Height (free-form string; CDLI uses mm but format varies).")
    width: str | None = Field(None, description="Width.")
    thickness: str | None = Field(None, description="Thickness.")
    condition_description: str | None = Field(None, description="Physical condition / preservation notes.")
    object_remarks: str | None = Field(None, description="Free-text remarks about the artifact.")


class LookupArtifactResponse(_Permissive):
    """Response shape for lookup_artifact (one P-id → one record)."""

    artifact: CDLIArtifact
    attribution: str = Field(
        ...,
        description=(
            "Source attribution for the catalogue data. CDLI publishes its "
            "catalogue as CC0 (no attribution legally required), but it's "
            "good practice to credit them anyway."
        ),
    )


class FindArtifactsResponse(_Permissive):
    """Response shape for find_artifacts (filtered list)."""

    filter_spec: dict = Field(..., description="Echo of the filter the caller supplied.")
    total_matches: int = Field(..., description="Total artifacts matching the filter (may exceed `len(results)` if `limit` clipped).")
    offset: int = Field(0, description="Echo of the request `offset` so the caller knows its place in the result set.")
    next_offset: int | None = Field(
        None,
        description="Pass this back as `offset` on the next call to walk to the next page. `None` means the result set is exhausted.",
    )
    results: list[CDLIArtifact]
    attribution: str = Field(..., description="CC0 catalogue attribution for CDLI.")
