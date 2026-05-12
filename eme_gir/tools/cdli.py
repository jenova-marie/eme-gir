"""MCP tools for the CDLI artifact catalogue.

Two tool functions:
- `lookup_artifact(p_id)` — one P-id → one full CDLIArtifact record
- `find_artifacts(...)` — filtered catalogue query

Plus the `_build_cdli_artifact` row → Pydantic adapter and the
`CDLI_ATTRIBUTION` constant for response footers.

Connection + cross-domain enrichment helpers live in `eme_gir.cdli`
(used by the ePSD2 see_examples / find_verb_form pipelines too).
"""

from __future__ import annotations

import sqlite3

from ..cdli import connect
from ..log import log_call
from ..models.cdli import (
    CDLIArtifact,
    FindArtifactsResponse,
    LookupArtifactResponse,
)
from ..models.common import ErrorResponse
from ..paths import (
    CDLI_ARTIFACT_URL,
    CDLI_DB,
    CDLI_LINEART_THUMB_URL,
    CDLI_LINEART_URL,
    CDLI_PHOTO_THUMB_URL,
    CDLI_PHOTO_URL,
)

CDLI_ATTRIBUTION = (
    "CDLI: Cuneiform Digital Library Initiative (cdli.earth), "
    "catalogue data CC0 / public domain. Hosted by Max Planck Institute "
    "for the History of Science (Berlin) since 2022."
)


def _build_cdli_artifact(row: sqlite3.Row) -> CDLIArtifact:
    """Convert a cdli.artifacts SQLite row into the response model,
    computing image + page URLs from the p_id + has_photo / has_lineart
    flags. URL fields are None when the corresponding flag is false so
    agents can tell whether the link will actually return an image
    (vs. a 404 because CDLI never had the imagery for that artifact)."""
    p_id = row["p_id"]
    cdli_id = row["cdli_id"]
    has_photo = bool(row["has_photo"])
    has_lineart = bool(row["has_lineart"])
    return CDLIArtifact(
        p_id=p_id,
        cdli_id=cdli_id,
        cdli_url=CDLI_ARTIFACT_URL.format(cdli_id=cdli_id),
        photo_url=CDLI_PHOTO_URL.format(p_id=p_id) if has_photo else None,
        photo_thumb_url=CDLI_PHOTO_THUMB_URL.format(p_id=p_id) if has_photo else None,
        lineart_url=CDLI_LINEART_URL.format(p_id=p_id) if has_lineart else None,
        lineart_thumb_url=CDLI_LINEART_THUMB_URL.format(p_id=p_id) if has_lineart else None,
        has_photo=has_photo,
        has_lineart=has_lineart,
        designation=row["designation"],
        primary_publication=row["primary_publication"],
        publication_history=row["publication_history"],
        citation=row["citation"],
        composite_id=row["composite_id"],
        period=row["period"],
        period_remarks=row["period_remarks"],
        accounting_period=row["accounting_period"],
        dates_referenced=row["dates_referenced"],
        provenience=row["provenience"],
        provenience_remarks=row["provenience_remarks"],
        findspot_remarks=row["findspot_remarks"],
        findspot_square=row["findspot_square"],
        excavation_no=row["excavation_no"],
        museum_collection=row["museum_collection"],
        museum_no=row["museum_no"],
        accession_no=row["accession_no"],
        genre=row["genre"],
        subgenre=row["subgenre"],
        language=row["language"],
        material=row["material"],
        object_type=row["object_type"],
        height=row["height"],
        width=row["width"],
        thickness=row["thickness"],
        condition_description=row["condition_description"],
        object_remarks=row["object_remarks"],
    )


@log_call
def lookup_artifact(p_id: str) -> LookupArtifactResponse | ErrorResponse:
    """Look up the full CDLI catalogue record for a single cuneiform
    artifact by its P-id (P-number).

    Returns provenience (find spot), period, museum custody, dimensions,
    citations, AND links to CDLI's hosted photographs / line drawings
    when available. Use this to ground an attested line in its
    archaeological + custodial context — "this tablet is from Drehem,
    Ur III period (~2050 BCE), now at the British Museum (BM 103437),
    photographed at <link>".

    Args:
        p_id: P-id like 'P347156' or just '347156' (numeric form OK,
              we normalize). Returned by see_examples / find_verb_form
              as `text_id`.

    Returns LookupArtifactResponse on hit, ErrorResponse when:
      - cdli.sqlite hasn't been built (run build_cdli_db.py)
      - the P-id isn't in CDLI's catalogue (rare — CDLI is comprehensive)

    The image URLs in the response are None when CDLI doesn't have the
    corresponding asset, so you can tell up front whether a "see the
    actual tablet" link will work without making a wasted HTTP request.
    """
    # Normalize the P-id — accept '347156', 'P347156', 'p347156', etc.
    s = (p_id or "").strip().lstrip("Pp")
    if not s.isdigit():
        return ErrorResponse(
            error=f"p_id must be 'P{{nnnnnn}}' or a bare integer (got {p_id!r})",
            hint="Try the text_id from a see_examples result, e.g. 'P347156'.",
        )
    canonical = f"P{int(s):06d}"

    con = connect()
    if con is None:
        return ErrorResponse(
            error=f"cdli.sqlite missing at {CDLI_DB}",
            hint="Run `python3 build_cdli_db.py` to build it (~15s after a 147 MB download).",
        )
    try:
        row = con.execute(
            "SELECT * FROM artifacts WHERE p_id=?", (canonical,)
        ).fetchone()
    finally:
        con.close()
    if not row:
        return ErrorResponse(
            error=f"no CDLI artifact with p_id={canonical!r}",
            hint=(
                "CDLI's catalogue covers ~353K artifacts but the August "
                "2022 snapshot we ingested may not include very recent "
                "additions. Verify at https://cdli.earth/search."
            ),
        )
    return LookupArtifactResponse(
        artifact=_build_cdli_artifact(row),
        attribution=CDLI_ATTRIBUTION,
    )


@log_call
def find_artifacts(
    provenience: str | None = None,
    period: str | None = None,
    museum_collection: str | None = None,
    genre: str | None = None,
    language: str | None = None,
    limit: int = 20,
) -> FindArtifactsResponse | ErrorResponse:
    """Filter the CDLI catalogue by archaeological / curatorial criteria.

    Use this for "show me every artifact matching X" questions that
    Oracc's lemma-centric tools don't answer:
      - "Every Ur III tablet from Drehem in the British Museum"
      - "Every Old Babylonian literary tablet from Nippur"
      - "Every Akkadian text in the Yale Babylonian Collection"

    Each filter argument is matched as a case-insensitive SUBSTRING
    against the corresponding catalogue column, so partial values work:
      - provenience='Drehem'      matches 'Drehem (mod. Puzriš-Dagan)'
      - period='Ur III'           matches 'Ur III (ca. 2100-2000 BC)'
      - museum_collection='Berlin' matches 'Vorderasiatisches Museum, Berlin, Germany'

    All filter arguments are optional — pass none to get an unfiltered
    sample (useful for browsing what CDLI looks like). Filters AND
    together when multiple are supplied.

    Args:
        provenience: find-spot substring, e.g. 'Drehem', 'Nippur', 'Uruk'.
        period: historical period substring, e.g. 'Ur III', 'Old Babylonian'.
        museum_collection: holding institution substring, e.g. 'British
                          Museum', 'Yale', 'Berlin'.
        genre: text genre substring, e.g. 'Administrative', 'Literary',
               'Lexical', 'Royal Inscription'.
        language: language substring, e.g. 'Sumerian', 'Akkadian', 'Hittite'.
        limit: max artifacts to return (default 20, cap 200).

    Each result carries the same image / page URLs as lookup_artifact,
    so the agent can offer "see the actual tablet" links for any item
    in the list without a follow-up call.
    """
    limit = max(1, min(200, int(limit)))

    con = connect()
    if con is None:
        return ErrorResponse(
            error=f"cdli.sqlite missing at {CDLI_DB}",
            hint="Run `python3 build_cdli_db.py` to build it (~15s after a 147 MB download).",
        )

    where: list[str] = []
    params: list[str] = []
    for col, needle in (
        ("provenience", provenience),
        ("period", period),
        ("museum_collection", museum_collection),
        ("genre", genre),
        ("language", language),
    ):
        if needle and needle.strip():
            where.append(f"{col} LIKE ?")
            params.append(f"%{needle.strip()}%")

    sql_where = ("WHERE " + " AND ".join(where)) if where else ""
    filter_spec = {
        "provenience": provenience,
        "period": period,
        "museum_collection": museum_collection,
        "genre": genre,
        "language": language,
    }

    try:
        total = con.execute(
            f"SELECT COUNT(*) FROM artifacts {sql_where}", params
        ).fetchone()[0]
        rows = con.execute(
            f"SELECT * FROM artifacts {sql_where} "
            "ORDER BY p_id LIMIT ?",
            (*params, limit),
        ).fetchall()
    finally:
        con.close()

    return FindArtifactsResponse(
        filter_spec=filter_spec,
        total_matches=total,
        results=[_build_cdli_artifact(r) for r in rows],
        attribution=CDLI_ATTRIBUTION,
    )
