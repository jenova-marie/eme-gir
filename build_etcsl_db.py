#!/usr/bin/env python3
"""Download (if needed) and ingest the ETCSL corpus into data/etcsl.sqlite.

ETCSL (Electronic Text Corpus of Sumerian Literature, Black et al. 2006)
is a 4.9 MB TEI/XML bundle of ~400 Sumerian literary texts with English
prose translations and per-word lemmatization. Hosted at the Oxford
Text Archive under CC BY 3.0 UK.

Output schema:
    texts         (text_id, title, has_translation)
    lines         (text_id, line_n, line_id, transliteration, paragraph_id)
    words         (text_id, line_n, word_pos, form, lemma, pos, label, type, det)
    paragraphs    (text_id, para_id, line_range, translation)
    paragraphs_fts(translation)        FTS5 over translation text
    lines_fts     (transliteration)    FTS5 over transliteration

Citation per ETCSL terms:
    Black, J.A., Cunningham, G., Ebeling, J., Flückiger-Hawker, E.,
    Robson, E., Taylor, J., and Zólyomi, G., The Electronic Text Corpus
    of Sumerian Literature (http://etcsl.orinst.ox.ac.uk/), Oxford
    1998-2006. CC BY 3.0 UK.
"""

from __future__ import annotations

import argparse
import html
import re
import sqlite3
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

# Reuse the SSL setup that already handles Oracc's chain. ETCSL/OTA serve
# their own valid chain so it works either way, but importing keeps us
# consistent with the rest of the project.
from download_corpus import _SSL_CTX, USER_AGENT
from paths import ETCSL_DB, ETCSL_ZIP, ETCSL_ZIP_URL


# -----------------------------------------------------------------------------
# Entity table — substituted into the raw XML before parsing because ETCSL's
# files have no DOCTYPE and stdlib's xml.etree refuses to resolve unknown
# entity refs. Maps ETCSL XML entities + the standard HTML-Latin set we see
# in author bibliography.
# -----------------------------------------------------------------------------

ETCSL_ENTITIES: dict[str, str] = {
    # Sumerian letters. Lowercase/uppercase pairs. Normalize to the Eme-gir /
    # Oracc convention (ŋ over ĝ; emphatic s/t over digit-suffixed forms).
    "c": "š", "C": "Š",           # shin
    "g": "ŋ", "G": "Ŋ",           # velar nasal — Eme-gir calls it ŋ; ETCSL writes ĝ via &g;
    "h": "ḫ", "H": "Ḫ",           # h with breve below
    "hr": "ḫ",                    # rare variant
    "s": "š",                     # bare &s; — sometimes used for š in non-form contexts
    "s1": "s₁", "s2": "ś", "s3": "ṣ", "s4": "ŝ",  # numbered s variants
    "s5": "s₅", "s6": "s₆", "s7": "s₇", "s8": "s₈", "s9": "s₉",
    "t": "ṭ",                     # emphatic t
    "aleph": "ʾ",                 # glottal stop
    # Determinatives — ETCSL writes these as standalone entities; we render
    # them in standard {brace} form so cuneify.py and Oracc-trained agents
    # both understand them.
    "d": "{d}",       # divine
    "dug": "{dug}",   # ceramic vessel
    "f": "{f}",       # female PN marker
    "gi": "{gi}",     # reed
    "id2": "{id₂}",   # river/canal
    "im": "{im}",     # clay (or storm-god)
    "jic": "{ŋeš}",   # wood (ETCSL: 'jic' = ŋeš)
    "ki": "{ki}",     # place (post-determinative)
    "ku6": "{ku₆}",   # fish (post-determinative)
    "kuc": "{kuš}",   # leather
    "lu2": "{lu₂}",   # person-class profession
    "m": "{m}",       # male PN marker
    "mu": "{mu}",     # year/name marker
    "mucen": "{mušen}",  # bird
    "mul": "{mul}",   # star
    "zabar": "{zabar}",  # bronze
    "na4": "{na₄}",   # stone
    "sar": "{sar}",   # plant
    "tug2": "{tug₂}", # textile
    "u2": "{u₂}",     # plant
    "udu": "{udu}",   # sheep
    "urud": "{urud}", # copper
    "uzu": "{uzu}",   # meat / body part
    "ance": "{anše}", # donkey / equid
    "cah2": "{šaḫ₂}", # pig
    "e2": "{e₂}",     # house
    "gud": "{gud}",   # bull
    "iku": "{iku}",   # area measure
    "kac": "{kaš}",   # beer
    "kur": "{kur}",   # mountain / foreign land
    "ninda": "{ninda}",  # bread
    "sa": "{sa}",     # sinew
    "tum9": "{tum₉}", # wind
    # Punctuation / utility
    "qryb": "«", "qrye": "»",     # quotation marks (in editorial notes)
    # Damaged / supplied brackets — must NOT use ASCII []<> here because
    # these entities appear inside XML attribute values (e.g.
    # <corr sic="&damb;en-ki&dame;">) and ASCII <> would break XML parsing.
    # Use Sumerology-standard half-brackets (⸢⸣) and Unicode angle brackets
    # (⟨⟩) which round-trip cleanly through any subsequent XML processing.
    "damb": "⸢", "dame": "⸣",     # damaged-text begin / end (Sumerological convention)
    "suppb": "⟨", "suppe": "⟩",   # editorially-supplied begin / end
    "times": "×", "commat": "@", "plus": "+", "sect": "§",
    "X": "X",                     # placeholder/unknown
    # HTML / Latin-with-macrons (Akkadian normalizations + author names)
    "amacr": "ā", "Amacr": "Ā", "emacr": "ē", "Emacr": "Ē",
    "imacr": "ī", "Imacr": "Ī", "omacr": "ō", "Omacr": "Ō",
    "umacr": "ū", "Umacr": "Ū",
    "euml": "ë", "iuml": "ï", "Iuml": "Ï",
    # HTML Latin-1 — author bibliography names
    "aacute": "á", "eacute": "é", "iacute": "í", "oacute": "ó", "uacute": "ú",
    "Aacute": "Á", "Eacute": "É", "Iacute": "Í", "Oacute": "Ó", "Uacute": "Ú",
    "ouml": "ö", "auml": "ä", "uuml": "ü", "Ouml": "Ö", "Auml": "Ä", "Uuml": "Ü",
    "ccedil": "ç", "Ccedil": "Ç",
    "ntilde": "ñ", "Ntilde": "Ñ",
    "agrave": "à", "egrave": "è", "igrave": "ì", "ograve": "ò", "ugrave": "ù",
    "acirc": "â", "ecirc": "ê", "icirc": "î", "ocirc": "ô", "ucirc": "û",
    "szlig": "ß",
    "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'",
    "nbsp": " ",
}

_ENTITY_RE = re.compile(r"&([A-Za-z][A-Za-z0-9_]*);")


def expand_entities(xml_text: str) -> str:
    """Replace every &name; with its Unicode equivalent. Unknown entities
    pass through unchanged so the parser's own error tells us what we missed.
    """
    return _ENTITY_RE.sub(
        lambda m: ETCSL_ENTITIES.get(m.group(1), m.group(0)),
        xml_text,
    )


# -----------------------------------------------------------------------------
# Transliteration normalizer — convert ETCSL's ASCII-friendly conventions
# (j=ŋ, c=š, digit-after-letter → subscript) to standard Unicode that matches
# Oracc/Eme-gir spelling. Applied to attribute values like form= and lemma=.
# -----------------------------------------------------------------------------

_DIGIT_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_ASCII_SUMERIAN = str.maketrans({"j": "ŋ", "J": "Ŋ", "c": "š", "C": "Š"})
# Subscript any run of digits that immediately follows an alphabetic char,
# e.g. "gal-ce3" → "gal-še₃", "ju10" → "ŋu₁₀". Don't touch standalone digits
# (line numbers, dates, etc.).
_SUBSCRIPT_RE = re.compile(r"(?<=[A-Za-zŋŠšḫṣṭŊḪṢṬ])(\d+)")


def normalize_translit(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.translate(_ASCII_SUMERIAN)
    s = _SUBSCRIPT_RE.sub(lambda m: m.group(1).translate(_DIGIT_SUB), s)
    return s


# -----------------------------------------------------------------------------
# Schema
# -----------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE texts (
    text_id          TEXT PRIMARY KEY,    -- e.g. "c.1.4.1"
    title            TEXT,                -- e.g. "Inana's descent to the nether world"
    has_translation  INTEGER NOT NULL     -- 0/1
);

CREATE TABLE lines (
    text_id          TEXT NOT NULL,
    line_id          TEXT NOT NULL,       -- e.g. "c141.1" or "c24216.A.5" (ETCSL's globally-unique xref id within text)
    ord              INTEGER NOT NULL,    -- sequential position 1..N for paging (sections concatenated in source order)
    line_label       TEXT NOT NULL,       -- displayable label: "1" for single-section, "A.5" for multi-section
    transliteration  TEXT NOT NULL,
    paragraph_id     TEXT,                -- corresp -> translation paragraph
    UNIQUE (text_id, line_id),
    UNIQUE (text_id, ord)
);
-- Not WITHOUT ROWID because lines_fts (FTS5) needs a real rowid to back
-- its content='lines' contentless-index pattern. Storage cost is modest.

CREATE TABLE words (
    text_id   TEXT NOT NULL,
    line_id   TEXT NOT NULL,              -- joins to lines.line_id (sections preserved)
    word_pos  INTEGER NOT NULL,           -- 0-based position within the line
    form      TEXT NOT NULL,              -- normalized inflected spelling
    lemma     TEXT,                       -- citation form
    pos       TEXT,                       -- ETCSL POS code
    label     TEXT,                       -- short English gloss
    type      TEXT,                       -- e.g. "DN" (divine name), "TN" (temple), "SN" (settlement)
    PRIMARY KEY (text_id, line_id, word_pos)
) WITHOUT ROWID;

CREATE TABLE paragraphs (
    text_id      TEXT NOT NULL,
    para_id      TEXT NOT NULL,           -- e.g. "t141.p1"
    line_range   TEXT,                    -- e.g. "1-5" — the n= attr from <p>
    line_start   INTEGER,                 -- parsed first line number for ranking
    translation  TEXT NOT NULL,           -- markup-stripped English prose
    UNIQUE (text_id, para_id)
);
-- Not WITHOUT ROWID because paragraphs_fts needs a backing rowid.
"""

INDEXES = [
    "CREATE INDEX idx_lines_paragraph   ON lines(paragraph_id)",
    "CREATE INDEX idx_words_lemma       ON words(lemma)",
    "CREATE INDEX idx_words_form        ON words(form)",
    "CREATE INDEX idx_words_type        ON words(type)",
    "CREATE INDEX idx_paragraphs_range  ON paragraphs(text_id, line_start)",
]

FTS_TABLES = [
    # FTS5 indexes for free-text search on Sumerian and English. Use porter
    # stemmer for English (so "kingships" matches "kingship"), unicode61
    # default for Sumerian.
    ("paragraphs_fts", "translation", "paragraphs", "porter unicode61"),
    ("lines_fts",      "transliteration", "lines",  "unicode61"),
]


# -----------------------------------------------------------------------------
# Download
# -----------------------------------------------------------------------------

def ensure_zip(zip_path: Path) -> None:
    if zip_path.exists() and zip_path.stat().st_size > 1_000_000:
        return
    print(f"Downloading ETCSL bulk zip ({ETCSL_ZIP_URL.split('?')[0]}) ...")
    req = urllib.request.Request(ETCSL_ZIP_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as r, open(zip_path, "wb") as f:
        while chunk := r.read(1024 * 256):
            f.write(chunk)
    print(f"  -> {zip_path} ({zip_path.stat().st_size / 1024 / 1024:,.1f} MB)")


# -----------------------------------------------------------------------------
# Parsing
# -----------------------------------------------------------------------------

def _strip_text(elem: ET.Element) -> str:
    """Flatten an element's text content (across all descendants) into a
    single whitespace-collapsed string. Markup like <w type="DN">Inana</w>
    contributes its inner text 'Inana'.
    """
    return re.sub(r"\s+", " ", "".join(elem.itertext())).strip()


_LINE_ID_RE = re.compile(r"^c\d+(?:\.([A-Z]))?\.(\d+)$")


def line_label(line_id: str, n_attr: str) -> str:
    """Derive a displayable line label from the XML id.

      c141.1        -> "1"        (single-section)
      c24216.A.5    -> "A.5"      (multi-section, section A)
      c24216.B.10   -> "B.10"     (multi-section, section B)

    Falls back to the raw <l n="…"> attribute if the id doesn't match the
    expected shape.
    """
    m = _LINE_ID_RE.match(line_id or "")
    if not m:
        return n_attr or "?"
    section, num = m.groups()
    return f"{section}.{num}" if section else num


def parse_translit(xml_bytes: bytes, text_id: str):
    """Yield (line_dict, [word_dict, ...]) tuples for one transliteration file.

    `ord` is assigned in document order so multi-section texts (where each
    section restarts numbering at 1) still have a unique sequential index
    for paging.
    """
    expanded = expand_entities(xml_bytes.decode("utf-8", errors="replace"))
    root = ET.fromstring(expanded)
    body = root.find(".//body")
    if body is None:
        return
    ord_counter = 0
    for l in body.iter("l"):
        line_id = l.get("id", "")
        if not line_id:
            continue
        n_attr = l.get("n", "")
        label = line_label(line_id, n_attr)
        paragraph_id = l.get("corresp")
        words: list[tuple[int, dict]] = []
        for pos, w in enumerate(l.iter("w")):
            form = normalize_translit(w.get("form"))
            if not form:
                continue
            words.append((pos, {
                "text_id": text_id,
                "line_id": line_id,
                "word_pos": pos,
                "form": form,
                "lemma": normalize_translit(w.get("lemma")),
                "pos": w.get("pos"),
                "label": w.get("label"),
                "type": w.get("type"),
            }))
        translit = " ".join(wd["form"] for _, wd in words)
        if not translit:
            continue
        ord_counter += 1
        yield (
            {
                "text_id": text_id,
                "line_id": line_id,
                "ord": ord_counter,
                "line_label": label,
                "transliteration": translit,
                "paragraph_id": paragraph_id,
            },
            [wd for _, wd in words],
        )


def parse_translation(xml_bytes: bytes, text_id: str):
    """Yield paragraph dicts for one translation file."""
    expanded = expand_entities(xml_bytes.decode("utf-8", errors="replace"))
    root = ET.fromstring(expanded)
    body = root.find(".//body")
    if body is None:
        return
    for p in body.iter("p"):
        para_id = p.get("id")
        if not para_id:
            continue
        line_range = p.get("n", "")
        line_start = None
        if line_range:
            m = re.match(r"^(\d+)", line_range)
            if m:
                line_start = int(m.group(1))
        text = _strip_text(p)
        # html.unescape catches anything we missed in entity expansion (e.g.
        # numeric refs like &#x2014;); idempotent on already-decoded content.
        text = html.unescape(text)
        if text:
            yield {
                "text_id": text_id,
                "para_id": para_id,
                "line_range": line_range,
                "line_start": line_start,
                "translation": text,
            }


def parse_title(xml_bytes: bytes) -> str | None:
    expanded = expand_entities(xml_bytes.decode("utf-8", errors="replace"))
    try:
        root = ET.fromstring(expanded)
    except ET.ParseError:
        return None
    title_el = root.find(".//titleStmt/title")
    if title_el is None:
        return None
    return html.unescape(_strip_text(title_el)) or None


# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(ETCSL_DB), help="output SQLite path")
    ap.add_argument("--zip", default=str(ETCSL_ZIP), help="path to (or destination for) etcsl.zip")
    ap.add_argument("--limit", type=int, default=None,
                    help="for testing: stop after processing N transliterations")
    args = ap.parse_args()

    zip_path = Path(args.zip)
    db_path = Path(args.db)

    ensure_zip(zip_path)

    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")
    con.executescript(SCHEMA)

    print(f"\nIngesting {zip_path} → {db_path} ...")
    t0 = time.monotonic()
    n_texts = n_lines = n_words = n_paragraphs = 0
    parse_errors: list[str] = []

    with zipfile.ZipFile(zip_path) as z:
        # Index members by id for fast pairing
        translit_files = [
            n for n in z.namelist()
            if n.startswith("etcsl/transliterations/c.") and n.endswith(".xml")
        ]
        translation_files = {
            n.rsplit("/", 1)[1].removeprefix("t.").removesuffix(".xml"): n
            for n in z.namelist()
            if n.startswith("etcsl/translations/t.") and n.endswith(".xml")
        }
        translit_files.sort()
        if args.limit:
            translit_files = translit_files[: args.limit]

        for member in translit_files:
            text_id = member.rsplit("/", 1)[1].removeprefix("c.").removesuffix(".xml")
            text_id = "c." + text_id
            translit_bytes = z.read(member)
            try:
                title = parse_title(translit_bytes)
            except Exception as e:
                parse_errors.append(f"{text_id} (title): {e}")
                title = None

            try:
                line_rows: list[dict] = []
                word_rows: list[dict] = []
                for line, words in parse_translit(translit_bytes, text_id):
                    line_rows.append(line)
                    word_rows.extend(words)
            except ET.ParseError as e:
                parse_errors.append(f"{text_id} (translit): {e}")
                continue

            # Find the matching translation (id stripped of c.)
            stripped = text_id.removeprefix("c.")
            t_member = translation_files.get(stripped)
            para_rows: list[dict] = []
            has_translation = False
            if t_member:
                try:
                    para_rows = list(parse_translation(z.read(t_member), text_id))
                    has_translation = bool(para_rows)
                except ET.ParseError as e:
                    parse_errors.append(f"{text_id} (translation): {e}")

            con.execute(
                "INSERT INTO texts VALUES (?,?,?)",
                (text_id, title, int(has_translation)),
            )
            # OR IGNORE keeps the first hit per PK — necessary because ETCSL
            # texts often include variant manuscript readings as alternate
            # <l> elements sharing the same line_n. The primary reading
            # always appears first in document order so we keep it.
            if line_rows:
                con.executemany(
                    "INSERT OR IGNORE INTO lines VALUES "
                    "(:text_id, :line_id, :ord, :line_label, :transliteration, :paragraph_id)",
                    line_rows,
                )
            if word_rows:
                con.executemany(
                    "INSERT OR IGNORE INTO words VALUES "
                    "(:text_id, :line_id, :word_pos, :form, :lemma, :pos, :label, :type)",
                    word_rows,
                )
            if para_rows:
                con.executemany(
                    "INSERT OR IGNORE INTO paragraphs VALUES (:text_id, :para_id, :line_range, :line_start, :translation)",
                    para_rows,
                )
            n_texts += 1
            n_lines += len(line_rows)
            n_words += len(word_rows)
            n_paragraphs += len(para_rows)
            if n_texts % 50 == 0:
                con.commit()
                print(f"  {n_texts:>4} texts ingested ({n_lines:,} lines, {n_words:,} words)", flush=True)

    con.commit()
    print(f"\nIngest complete: {n_texts} texts, {n_lines:,} lines, "
          f"{n_words:,} words, {n_paragraphs:,} paragraphs in "
          f"{time.monotonic() - t0:.1f}s")
    if parse_errors:
        print(f"  {len(parse_errors)} parse errors (first 5):")
        for e in parse_errors[:5]:
            print(f"    {e}")

    print("\nBuilding indexes ...")
    t1 = time.monotonic()
    for stmt in INDEXES:
        con.execute(stmt)

    print("Building FTS5 indexes ...")
    for fts_name, col, base, tokenize in FTS_TABLES:
        con.execute(
            f"CREATE VIRTUAL TABLE {fts_name} USING fts5("
            f"  {col}, content='{base}', tokenize='{tokenize}'"
            ")"
        )
        con.execute(f"INSERT INTO {fts_name}(rowid, {col}) "
                    f"SELECT rowid, {col} FROM {base}")
    con.commit()
    print(f"  -> indexes + FTS done in {time.monotonic() - t1:.1f}s")

    con.executemany("INSERT OR REPLACE INTO meta VALUES (?,?)", [
        ("source", "ETCSL bulk corpus, Oxford Text Archive (ota.bodleian.ox.ac.uk handle 20.500.12024/2518)"),
        ("citation", "Black, J.A., et al., The Electronic Text Corpus of Sumerian Literature, Oxford 1998-2006."),
        ("license", "CC BY 3.0 UK"),
        ("texts", str(n_texts)),
        ("lines", str(n_lines)),
        ("words", str(n_words)),
        ("paragraphs", str(n_paragraphs)),
        ("ingested_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    ])
    con.commit()

    print("Optimizing ...")
    con.executescript("PRAGMA journal_mode=WAL; ANALYZE; VACUUM;")
    con.close()

    final_mb = db_path.stat().st_size / 1024 / 1024
    print(f"\n✨ {db_path} built: {final_mb:,.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
