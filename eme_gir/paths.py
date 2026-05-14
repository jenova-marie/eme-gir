"""Single source of truth for project file locations.

All Python modules in this project import their canonical SQLite paths,
log paths, and corpus location from here so there's exactly one place
to change if the layout ever moves.

Layout:
    <root>/                       — project root (the dir this file lives in)
        corpus/                   — downloaded Oracc project zips (~3.1 GB)
        data/                     — generated SQLite indexes
        log/                      — generated server logs
        ogsl.zip path             — corpus/ogsl.zip (loaded by cuneify.py)
"""

from __future__ import annotations

from pathlib import Path

# `paths.py` lives at `eme_gir/paths.py`; the repo root is one level up
# so we can resolve `data/`, `corpus/`, `log/`, `prompt/` relative to it
# regardless of CWD or which entry-point script imported us.
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "log"
CORPUS_DIR = ROOT / "corpus"
PROMPT_DIR = ROOT / "prompt"

# Auto-create the writable dirs so first-run scripts can drop files in.
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# SQLite indexes — all generated, all gitignored via *.sqlite*.
GLOSSARY_DB = DATA_DIR / "glossary.sqlite"
GLOSSARY_AKK_DB = DATA_DIR / "glossary_akk.sqlite"
TEXT_INDEX_DB = DATA_DIR / "text_index.sqlite"
COLLOCATIONS_DB = DATA_DIR / "collocations.sqlite"
INFLECTED_COLLOCATIONS_DB = DATA_DIR / "inflected_collocations.sqlite"
ETCSL_DB = DATA_DIR / "etcsl.sqlite"
CDLI_DB = DATA_DIR / "cdli.sqlite"

# ETCSL bulk corpus — fetched from Oxford Text Archive.
ETCSL_ZIP = DATA_DIR / "etcsl.zip"
ETCSL_ZIP_URL = (
    "https://ota.bodleian.ox.ac.uk/repository/xmlui/bitstream/handle/"
    "20.500.12024/2518/etcsl.zip?sequence=11&isAllowed=y"
)

# CDLI bulk catalogue — fetched from the cdli-gh GitHub mirror.
# The repo file at cdli-gh/data/cdli_cat.csv is a Git LFS pointer; the
# actual blob lives on media.githubusercontent.com (no auth, no git-lfs
# install required). Last meaningful data update was Aug 2022 — stale
# but acceptable for catalogue metadata (provenience, museum, period
# don't change once an artifact is excavated and accessioned).
CDLI_CSV = DATA_DIR / "cdli_cat.csv"
CDLI_CSV_URL = (
    "https://media.githubusercontent.com/media/cdli-gh/data/master/cdli_cat.csv"
)
# Public-facing image + artifact-page URL templates. CDLI moved hosting
# from cdli.ucla.edu → cdli.mpiwg-berlin.mpg.de → cdli.earth.
# Artifact page uses the BARE numeric id (no 'P' prefix); image paths
# use the zero-padded 'P{nnnnnn}' form.
CDLI_ARTIFACT_URL = "https://cdli.earth/artifacts/{cdli_id}"
CDLI_PHOTO_URL = "https://cdli.earth/dl/photo/{p_id}.jpg"
CDLI_PHOTO_THUMB_URL = "https://cdli.earth/dl/tn_photo/{p_id}.jpg"
CDLI_LINEART_URL = "https://cdli.earth/dl/lineart/{p_id}_l.jpg"
CDLI_LINEART_THUMB_URL = "https://cdli.earth/dl/tn_lineart/{p_id}_l.jpg"

# Logs.
MCP_SERVER_LOG = LOG_DIR / "mcp_server.log"

# Reference data shipped with corpus/.
OGSL_ZIP = CORPUS_DIR / "ogsl.zip"

# Per-server start_here prompts — each data-MCP server has its own
# scoped bootstrap document. Files are created on demand; the loader
# at `eme_gir.prompts.load_prompt` falls back to a placeholder when
# they're missing.
EPSD2_PROMPT_DOC = PROMPT_DIR / "EPSD2_PROMPT.md"
ETCSL_PROMPT_DOC = PROMPT_DIR / "ETCSL_PROMPT.md"
CDLI_PROMPT_DOC = PROMPT_DIR / "CDLI_PROMPT.md"
OGSL_PROMPT_DOC = PROMPT_DIR / "OGSL_PROMPT.md"
# Ummia persona prompt — lives in prompt/ alongside the other
# per-server bootstrap docs (it IS a bootstrap prompt). The lesson
# markdown files + dual-register grammar references it cycles through
# live in `lessons/` (see the LESSONS_DIR block below) — semantically
# all curriculum / teaching content.
# Ummia (𒌝𒈪𒀀 um-mi-a) is the canonical Sumerian word for the master
# teacher of the e₂-dub-ba — 453× attested across ED, Ur III, and OB,
# used by the Schooldays compositions when a student addresses their
# teacher. Server name: eme-gir-ummia (port 5058).
UMMIA_PROMPT_DOC = PROMPT_DIR / "UMMIA_PROMPT.md"

# Curriculum content — Sumerian 101 lesson prompts + dual-register
# grammar references + their Jagersma source-trail companion docs.
# All owned by the eme-gir-ummia server (see eme_gir/tools/ummia.py).
LESSONS_DIR = ROOT / "lessons"
LESSON_101_1_DOC = LESSONS_DIR / "lesson-101-1.md"
LESSON_101_2_DOC = LESSONS_DIR / "lesson-101-2.md"
LESSON_101_3_DOC = LESSONS_DIR / "lesson-101-3.md"
LESSON_101_4_DOC = LESSONS_DIR / "lesson-101-4.md"
LESSON_101_5_DOC = LESSONS_DIR / "lesson-101-5.md"
# The Jagersma reference is normative for reading attested texts; the
# Meadow companion is normative for composing in temple register.
# Their three Jagersma source-trail companions (CONVENTIONS, NOTES,
# PRONOUNCIATION) sit alongside them in lessons/ but aren't loaded by
# any code path — they're audit-trail documentation cross-linked from
# inside the two grammar files.
GRAMMAR_DOC = LESSONS_DIR / "JAGERSMA_GRAMMAR.md"
MEADOW_GRAMMAR_DOC = LESSONS_DIR / "MEADOW_GRAMMAR.md"
