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

ROOT = Path(__file__).resolve().parent
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
ETCSL_DB = DATA_DIR / "etcsl.sqlite"

# ETCSL bulk corpus — fetched from Oxford Text Archive.
ETCSL_ZIP = DATA_DIR / "etcsl.zip"
ETCSL_ZIP_URL = (
    "https://ota.bodleian.ox.ac.uk/repository/xmlui/bitstream/handle/"
    "20.500.12024/2518/etcsl.zip?sequence=11&isAllowed=y"
)

# Logs.
MCP_SERVER_LOG = LOG_DIR / "mcp_server.log"

# Reference data shipped with corpus/.
OGSL_ZIP = CORPUS_DIR / "ogsl.zip"

# Prompt / grammar artifacts (checked into the repo, not generated).
GRAMMAR_DOC = PROMPT_DIR / "SUMERIAN_GRAMMAR.md"
AGENT_PROMPT_DOC = PROMPT_DIR / "AGENT_PROMPT.md"
