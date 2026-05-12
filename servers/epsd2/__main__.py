"""ePSD2 (Eme-gir dictionary + corpus) MCP server.

Eleven tools for English ↔ Sumerian translation grounded in attested
forms over the Oracc / Eme-gir dataset (15,940 lemmas, 35.5 M
attestations, 178K phrasal collocations, 138K corpusjson texts).

Translation:
  translate_english, translate_sumerian, lookup_entry, see_examples,
  find_compound, get_inflections, analyze_form

Phrase parsing & collocations:
  parse_phrase, find_collocations, find_phrase_pattern

Verb morphology:
  find_verb_form

Run:
    python -m servers.epsd2                          # stdio (Claude Code)
    python -m servers.epsd2 --transport http         # HTTP on :5052
"""

from __future__ import annotations

from eme_gir.log import init_logging
from eme_gir.paths import GLOSSARY_DB, TEXT_INDEX_DB
from eme_gir.server import READ_ONLY_ANNOTATIONS, make_server, run_server
from eme_gir.tools.epsd2 import (
    analyze_form,
    find_collocations,
    find_compound,
    find_phrase_pattern,
    find_verb_form,
    get_inflections,
    lookup_entry,
    parse_phrase,
    see_examples,
    translate_english,
    translate_sumerian,
)

log = init_logging("eme-gir-epsd2")

mcp = make_server(
    name="eme-gir-epsd2",
    instructions=(
        "Local Eme-gir (electronic Pennsylvania Sumerian Dictionary) "
        "tools for English ↔ Sumerian translation grounded in attested "
        "usage. 15,940 headwords, 35.5 M attestations, 178K phrasal "
        "collocations, 138K corpusjson texts. All data CC0; no network.\n\n"
        "ENGLISH → SUMERIAN:\n"
        "  • translate_english(query) → rank Sumerian candidates with "
        "sense_count + sense_pct so 'the word for X' beats 'X as a "
        "fringe meaning'.\n"
        "  • find_compound(phrase) → fixed multi-word expressions first.\n"
        "  • find_collocations(cf) / find_phrase_pattern(pattern) → "
        "phrasal idioms + structural skeletons attested in the corpus.\n"
        "  • lookup_entry(oid) → full lemma view (senses, spellings, "
        "periods, compounds).\n"
        "  • get_inflections(oid) / find_verb_form(cf, pos, ...) → real "
        "attested morphology; don't synthesize from rules.\n"
        "  • see_examples(oid, period='Early Dynastic') → cite primary-"
        "source lines (ED IIIa/IIIb is the default period).\n\n"
        "SUMERIAN → ENGLISH:\n"
        "  • translate_sumerian(transliteration) → per-token glosses with "
        "detected case/possessive/plural suffixes.\n"
        "  • parse_phrase(transliteration) → case-aware grammatical "
        "pre-annotation (role labels: subject_ergative, oblique_dative, "
        "etc.) + compact bracket skeleton.\n"
        "  • analyze_form(spelling) → decompose a single attested word.\n\n"
        "For artifact provenience and cuneiform rendering use the "
        "companion CDLI and Signs servers. For literary corpus (with "
        "English translations) use the ETCSL server."
    ),
)

mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(translate_english)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(lookup_entry)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(see_examples)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(find_compound)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(get_inflections)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(analyze_form)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(translate_sumerian)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(parse_phrase)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(find_collocations)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(find_phrase_pattern)
mcp.tool(annotations=READ_ONLY_ANNOTATIONS)(find_verb_form)


if __name__ == "__main__":
    run_server(
        mcp, log,
        default_port=5052,
        required_dbs=[
            (GLOSSARY_DB, "build_glossary_db.py"),
            (TEXT_INDEX_DB, "build_text_index.py"),
        ],
    )
