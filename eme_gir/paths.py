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

# Prompt / grammar artifacts (checked into the repo, not generated).
GRAMMAR_DOC = PROMPT_DIR / "SUMERIAN_GRAMMAR.md"
MEADOW_GRAMMAR_DOC = PROMPT_DIR / "MEADOW_GRAMMAR.md"
AGENT_PROMPT_DOC = PROMPT_DIR / "AGENT_PROMPT.md"
