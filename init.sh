#!/usr/bin/env bash
#
# init.sh — one-shot data initialization for the eme-gir stack.
#
# Invoked by the `init` service in docker-compose.yml. The web and mcp
# services declare `depends_on: init: condition: service_completed_successfully`,
# so they don't start until this script exits 0. After init completes,
# both servers boot in parallel — neither pays the multi-minute setup
# cost in its own healthcheck window.
#
# Trust model: the sentinel file /app/data/.initialized is the SOLE
# source of truth for "data/ is consistent with the current code". If
# missing or version-stale, every SQLite index in /app/data is
# considered defunct (could be from a different / incompatible build of
# the stack) and gets WIPED before rebuild. corpus/ is left intact —
# download_corpus.py is resume-safe and never produces an incompatible
# artifact, so re-downloading 3.1 GB is wasteful.
#
# Lifecycle:
#   - Fresh host: data/ is empty → wipe is a no-op → full rebuild.
#   - Container restart mid-init: sentinel still missing → re-wipe and
#     restart from scratch. Worst-case recovery ~10 min (glossary
#     rebuild dominates). Predictable.
#   - Re-running on a healthy stack: sentinel present + version-current
#     → fast-path exit 0 in ~50 ms.
#   - Pre-built host data you want to REUSE: drop the sentinel manually
#     on the host BEFORE `docker compose up`:
#         echo "init_version=2" > data/.initialized
#     The container will skip init and trust your existing files.
#   - Forcing re-init after an upgrade: bump INIT_VERSION below; the
#     sentinel becomes stale and init re-runs (with wipe).

set -euo pipefail

INIT_FILE="/app/data/.initialized"
INIT_VERSION="4"

# Optional builds — toggle off via env to skip. Defaults are ON because
# the MCP server's tool surface is incomplete without them
# (find_collocations degrades gracefully; the four etcsl_* tools error
# if etcsl.sqlite is absent; find_phrase_pattern errors on v2/v3 syntax
# when inflected_collocations.sqlite is absent; lookup_artifact /
# find_artifacts AND the CDLI enrichment on see_examples / find_verb_form
# error / degrade if cdli.sqlite is absent).
: "${EME_GIR_BUILD_COLLOCATIONS:=1}"
: "${EME_GIR_BUILD_INFLECTED_COLLOCATIONS:=1}"
: "${EME_GIR_BUILD_ETCSL:=1}"
: "${EME_GIR_BUILD_CDLI:=1}"

log() { printf '[init %s] %s\n' "$(date -u +%H:%M:%S)" "$*" >&2; }

# Sentinel check: if present and version matches, we're done immediately.
if [[ -f "$INIT_FILE" ]]; then
    sentinel_version=$(grep -E '^init_version=' "$INIT_FILE" | cut -d= -f2 || echo "")
    if [[ "$sentinel_version" == "$INIT_VERSION" ]]; then
        log "sentinel v${sentinel_version} present; data/ is current — exiting cleanly"
        exit 0
    else
        log "sentinel v${sentinel_version:-unknown} is stale (current schema: v$INIT_VERSION); re-initializing"
    fi
fi

log "==== first-boot data initialization ===="
log "this can take 5-15 minutes on a clean host depending on bandwidth"
log "data persists via the /app/data and /app/corpus bind mounts"

# Wipe data/ — sentinel missing or stale, contents are untrusted.
# corpus/ is untouched (download_corpus.py is resume-safe).
log "wiping /app/data — contents are untrusted without a current sentinel"
find /app/data -mindepth 1 -delete 2>/dev/null || true

# 1. Corpus zips (~3.1 GB across 208 zips). The presence of epsd2.zip
#    is a good cheap proxy for "this directory has been populated";
#    download_corpus.py itself is resume-safe and only fetches what's
#    missing or wrong-sized.
if [[ -e /app/corpus/epsd2.zip ]]; then
    log "[1/6] corpus: epsd2.zip present, assuming corpus directory populated"
else
    log "[1/6] corpus: downloading Oracc JSON archives (~3.1 GB)"
    python3 /app/download_corpus.py
fi

# 2. Text-location index (~10 MB). Required by see_examples and the
#    period filter; cheap to rebuild (~2s).
log "[2/6] text_index.sqlite: building (~2 s)"
python3 /app/build_text_index.py

# 3. Glossary (~3.4 GB). The big one — required by every MCP tool and
#    every web route. ~3.5 minutes on a fast machine.
log "[3/6] glossary.sqlite: building (~3.5 minutes)"
python3 /app/build_glossary_db.py

# 4. Collocations (~22 MB). Optional — find_collocations MCP tool
#    returns a structured error if absent. Also used by find_phrase_pattern
#    as a fallback when the case-aware inflected index is absent.
if [[ "$EME_GIR_BUILD_COLLOCATIONS" != "1" ]]; then
    log "[4/7] collocations.sqlite: skipped (EME_GIR_BUILD_COLLOCATIONS=$EME_GIR_BUILD_COLLOCATIONS)"
else
    log "[4/7] collocations.sqlite: building (~5 minutes)"
    python3 /app/build_collocations.py
fi

# 5. Inflected collocations (~150 MB). Optional — find_phrase_pattern's
#    case/sense-aware syntax errors out when this is absent, falling back
#    to the legacy cf-only collocations.sqlite for v1 patterns.
if [[ "$EME_GIR_BUILD_INFLECTED_COLLOCATIONS" != "1" ]]; then
    log "[5/7] inflected_collocations.sqlite: skipped (EME_GIR_BUILD_INFLECTED_COLLOCATIONS=$EME_GIR_BUILD_INFLECTED_COLLOCATIONS)"
else
    log "[5/7] inflected_collocations.sqlite: building (~25-40 minutes — case+sense aware)"
    python3 /app/build_inflected_collocations.py
fi

# 6. ETCSL (~31 MB). Optional but cheap — etcsl_* MCP tools require it.
if [[ "$EME_GIR_BUILD_ETCSL" != "1" ]]; then
    log "[6/8] etcsl.sqlite: skipped (EME_GIR_BUILD_ETCSL=$EME_GIR_BUILD_ETCSL)"
else
    log "[6/8] etcsl.sqlite: building (~10 s, downloads 4.9 MB from OTA)"
    python3 /app/build_etcsl_db.py
fi

# 7. CDLI catalogue (~157 MB). Optional but high-value — lookup_artifact
#    and find_artifacts require it; see_examples / find_verb_form
#    silently skip the CDLI URL enrichment when absent.
if [[ "$EME_GIR_BUILD_CDLI" != "1" ]]; then
    log "[7/8] cdli.sqlite: skipped (EME_GIR_BUILD_CDLI=$EME_GIR_BUILD_CDLI)"
else
    log "[7/8] cdli.sqlite: building (~30s, downloads 147 MB from GitHub LFS)"
    python3 /app/build_cdli_db.py
fi

# 8. Pre-warm the Flask sort + casefold migrations on glossary.sqlite.
#    Both are version-gated and run idempotently inside Flask's
#    create_app() during gunicorn's worker boot, but doing them HERE
#    means the MCP server's startup check (which requires
#    meta.casefold_version) passes immediately when mcp boots in
#    parallel with web. Without this pre-warm, the MCP server would
#    race gunicorn's first worker for the migration lock.
log "[8/8] pre-warming Flask SQLite migrations (sort + casefold columns)"
python3 -c "
import sqlite3
from paths import GLOSSARY_DB
from app import ensure_sort_columns, ensure_casefold_columns
con = sqlite3.connect(GLOSSARY_DB)
ensure_sort_columns(con)
ensure_casefold_columns(con)
con.close()
"

# Write the sentinel. Its contents document what ran, when, and which
# optional builds were performed so future debugging has context.
cat > "$INIT_FILE" <<SENTINEL
init_version=$INIT_VERSION
initialized_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
hostname=$(hostname)
collocations=$EME_GIR_BUILD_COLLOCATIONS
inflected_collocations=$EME_GIR_BUILD_INFLECTED_COLLOCATIONS
etcsl=$EME_GIR_BUILD_ETCSL
cdli=$EME_GIR_BUILD_CDLI
SENTINEL
log "==== initialization complete; sentinel written to $INIT_FILE ===="
